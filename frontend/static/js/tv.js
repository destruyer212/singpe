(() => {
  const idle = document.getElementById("idle");
  const idleProximos = document.getElementById("idle-proximos");
  const reproductor = document.getElementById("reproductor");
  const video = document.getElementById("video");
  const audio = document.getElementById("audio");
  const audioFondo = document.getElementById("audio-fondo");
  const manualFondo = document.getElementById("manual-fondo");
  const ytContenedor = document.getElementById("yt-contenedor");
  const infoMesa = document.getElementById("info-mesa");
  const infoTitulo = document.getElementById("info-titulo");
  const infoArtista = document.getElementById("info-artista");
  const infoCantante = document.getElementById("info-cantante");
  const infoMensaje = document.getElementById("info-mensaje");
  const letras = document.getElementById("letras");
  const lrcAnterior = document.getElementById("lrc-anterior");
  const lrcActual = document.getElementById("lrc-actual");
  const lrcSiguiente = document.getElementById("lrc-siguiente");
  const barraProximos = document.getElementById("barra-proximos");
  const listaProximos = document.getElementById("lista-proximos");
  const ytError = document.getElementById("yt-error");
  const ytErrorLink = document.getElementById("yt-error-link");
  const infoVotos = document.getElementById("info-votos");
  const ranking = document.getElementById("ranking");
  const rankingLista = document.getElementById("ranking-lista");
  const bannerBatalla = document.getElementById("banner-batalla");
  const batallaReta = document.getElementById("batalla-reta");
  const batallaRetada = document.getElementById("batalla-retada");

  let solicitudActualDatos = null;

  let solicitudActualId = null;
  let lineasLrc = [];
  let finalizando = false;
  let manejandoError = false;

  function urlMedia(carpeta, archivo) {
    return encodeURI(`/media/${carpeta}/${archivo}`);
  }

  function chip(s) {
    return `<div class="glass rounded-xl px-4 py-2 text-sm whitespace-nowrap">🎵 <b>${s.cancion_titulo}</b> · Mesa ${s.mesa.numero}</div>`;
  }

  async function avanzarSiguiente() {
    const cola = await fetch("/api/dj/cola").then((r) => r.json());
    const pendientes = cola.filter((s) => s.estado === "pendiente").sort((a, b) => a.orden - b.orden);
    if (pendientes.length > 0) {
      await fetch(`/api/dj/solicitudes/${pendientes[0].id}/iniciar`, { method: "POST" });
    }
  }

  const MEDALLAS = ["🥇", "🥈", "🥉"];

  async function actualizarRanking() {
    const datos = await fetch("/api/dj/ranking").then((r) => r.json());
    if (!datos.length) {
      ranking.classList.add("hidden");
      return;
    }
    ranking.classList.remove("hidden");
    rankingLista.innerHTML = datos
      .slice(0, 3)
      .map((r, i) => {
        const insignia = i === 0 ? "🔥 Más ovacionada" : r.canciones >= 3 ? "🎤 Maratónica" : "";
        return `
        <div class="glass rounded-xl px-4 py-2 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl">${MEDALLAS[i] || "🎖️"}</span>
            <span class="font-bold">Mesa ${r.mesa}</span>
            ${insignia ? `<span class="text-xs text-neon-yellow">${insignia}</span>` : ""}
          </div>
          <div class="text-sm text-white/50">🎵 ${r.canciones} · 🔥 ${r.votos}</div>
        </div>`;
      })
      .join("");
  }

  let avisando = false;

  // A quien sigue justo después del que está cantando (posición 2 de la fila)
  // se le avisa una sola vez por voz: "Mesa X, prepárate, sigues pronto".
  async function avisarSiLeToca(cola, actual) {
    if (avisando) return;
    const pendientes = cola.filter((s) => s.estado === "pendiente" && s.id !== actual.id).sort((a, b) => a.orden - b.orden);
    const siguiente = pendientes[0];
    if (!siguiente || siguiente.avisada) return;

    avisando = true;
    await decirMensaje(`Mesa ${siguiente.mesa.numero}, prepárate, ¡sigues pronto!`);
    await fetch(`/api/dj/solicitudes/${siguiente.id}/avisar`, { method: "POST" });
    avisando = false;
  }

  async function marcarFinalizada(id) {
    if (finalizando) return;
    finalizando = true;
    if (solicitudActualDatos && solicitudActualDatos.id === id && solicitudActualDatos.mesa_retada_numero) {
      const votos = solicitudActualDatos.votos_fuego || 0;
      await decirMensaje(
        `¡Fin de la batalla! Mesa ${solicitudActualDatos.mesa.numero} sacó ${votos} fuegos. Mesa ${solicitudActualDatos.mesa_retada_numero}, ¡te toca responder!`
      );
    }
    await fetch(`/api/dj/solicitudes/${id}/finalizar`, { method: "POST" });
    await avanzarSiguiente();
    finalizando = false;
  }

  async function marcarCancelada(id) {
    if (finalizando) return;
    finalizando = true;
    await fetch(`/api/dj/solicitudes/${id}/cancelar`, { method: "POST" });
    await avanzarSiguiente();
    finalizando = false;
  }

  function mostrarErrorYoutube(videoId) {
    if (manejandoError) return;
    manejandoError = true;
    ytError.dataset.temporal = "0";
    ytError.classList.remove("hidden");
    ytError.classList.add("flex");
    ytErrorLink.classList.remove("hidden");
    document.getElementById("yt-error-titulo").textContent = "Este video está bloqueado para reproducirse aquí";
    document.getElementById("yt-error-sub").textContent = "El sello discográfico no permite incrustarlo en otros sitios. Pasando a la siguiente canción...";
    ytErrorLink.href = `https://youtube.com/watch?v=${videoId}`;
    const idAlMomento = solicitudActualId;
    setTimeout(() => {
      ytError.classList.add("hidden");
      ytError.classList.remove("flex");
      manejandoError = false;
      if (idAlMomento) marcarCancelada(idAlMomento);
    }, 5000);
  }

  function mostrarProbandoOtraVersion() {
    ytError.classList.remove("hidden");
    ytError.classList.add("flex");
    ytError.dataset.temporal = "1";
    document.getElementById("yt-error-titulo").textContent = "Ese video está bloqueado, probando otra versión...";
    document.getElementById("yt-error-sub").textContent = "Misma canción, subida por otro canal.";
    ytErrorLink.classList.add("hidden");
  }

  function ocultarAvisoTemporal() {
    if (ytError.dataset.temporal === "1") {
      ytError.classList.add("hidden");
      ytError.classList.remove("flex");
      ytError.dataset.temporal = "0";
      ytErrorLink.classList.remove("hidden");
      document.getElementById("yt-error-titulo").textContent = "Este video está bloqueado para reproducirse aquí";
      document.getElementById("yt-error-sub").textContent = "El sello discográfico no permite incrustarlo en otros sitios. Pasando a la siguiente canción...";
    }
  }

  const audioAnuncio = new Audio();

  async function decirMensaje(texto) {
    if (!texto) return;
    try {
      const res = await fetch(`/api/dj/tts?texto=${encodeURIComponent(texto)}`);
      if (!res.ok) throw new Error("tts no disponible");
      const { url } = await res.json();
      audioAnuncio.src = url;
      audioAnuncio.play().catch(() => {});
    } catch (e) {
      // Si falla el servicio de voz, el mensaje igual queda visible en pantalla.
    }
  }

  // ---------- YouTube IFrame API ----------
  let ytPlayer = null;
  let ytListo = false;
  let ytPendiente = null;
  let ytUltimoVideoId = null;
  let colaCandidatosYoutube = [];
  let indiceCandidato = 0;

  function cargarApiYoutube() {
    if (window.YT && window.YT.Player) return;
    if (document.getElementById("yt-iframe-api")) return;
    const tag = document.createElement("script");
    tag.id = "yt-iframe-api";
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
  }

  window.onYouTubeIframeAPIReady = () => {
    ytPlayer = new YT.Player("yt-player", {
      height: "100%",
      width: "100%",
      playerVars: { autoplay: 1, controls: 0, rel: 0, modestbranding: 1 },
      events: {
        onReady: () => {
          ytListo = true;
          if (ytPendiente) {
            ytPlayer.loadVideoById(ytPendiente);
            ytPendiente = null;
          }
        },
        onStateChange: (e) => {
          if (e.data === YT.PlayerState.ENDED && solicitudActualId) {
            marcarFinalizada(solicitudActualId);
          }
          if (e.data === YT.PlayerState.PLAYING) {
            ocultarAvisoTemporal();
          }
        },
        onError: () => {
          // 101/150 = el dueño del video bloqueó la reproducción embebida.
          // 100 = no encontrado/privado. 2 = id inválido. 5 = error de HTML5.
          intentarSiguienteCandidato();
        },
      },
    });
  };

  function reproducirYoutube(videoId) {
    ytUltimoVideoId = videoId;
    if (ytListo && ytPlayer) {
      ytPlayer.loadVideoById(videoId);
    } else {
      ytPendiente = videoId;
    }
  }

  function intentarSiguienteCandidato() {
    indiceCandidato += 1;
    if (indiceCandidato < colaCandidatosYoutube.length) {
      mostrarProbandoOtraVersion();
      reproducirYoutube(colaCandidatosYoutube[indiceCandidato]);
    } else {
      // Se probaron todas las versiones disponibles y ninguna se pudo reproducir aquí.
      mostrarErrorYoutube(colaCandidatosYoutube[0] || ytUltimoVideoId);
    }
  }

  cargarApiYoutube();

  // ---------- Carga de una solicitud ----------
  function ocultarTodosLosMedios() {
    video.classList.add("hidden");
    video.pause();
    ytContenedor.classList.add("hidden");
    bannerBatalla.classList.add("hidden");
    audioFondo.classList.add("hidden");
    audioFondo.classList.remove("flex");
    manualFondo.classList.add("hidden");
    manualFondo.classList.remove("flex");
    ytError.classList.add("hidden");
    ytError.classList.remove("flex");
    ytError.dataset.temporal = "0";
    manejandoError = false;
    colaCandidatosYoutube = [];
    indiceCandidato = 0;
    audio.pause();
    audio.removeAttribute("src");
    video.removeAttribute("src");
    letras.classList.add("hidden");
  }

  function cargarCancion(s) {
    solicitudActualId = s.id;
    solicitudActualDatos = s;
    finalizando = false;

    infoMesa.textContent = s.mesa.numero;
    infoTitulo.textContent = s.cancion_titulo;
    infoArtista.textContent = s.cancion_artista || "";
    infoCantante.textContent = s.cantantes && s.cantantes.length ? s.cantantes.join(" & ") : s.nombre_cantante || "Anónimo";
    infoMensaje.textContent = s.mensaje ? `💬 ${s.mensaje}` : "";
    infoVotos.textContent = `🔥 ${s.votos_fuego || 0}`;

    if (s.mesa_retada_numero) {
      bannerBatalla.classList.remove("hidden");
      bannerBatalla.classList.add("block");
      batallaReta.textContent = s.mesa.numero;
      batallaRetada.textContent = s.mesa_retada_numero;
      decirMensaje(`¡Batalla! Mesa ${s.mesa.numero} reta a la mesa ${s.mesa_retada_numero}. ¡Voten con el botón de fuego!`);
    } else {
      bannerBatalla.classList.add("hidden");
      bannerBatalla.classList.remove("block");
    }

    ocultarTodosLosMedios();
    lineasLrc = [];
    lrcAnterior.textContent = "";
    lrcActual.textContent = "🎶";
    lrcSiguiente.textContent = "";

    if (s.youtube_video_id) {
      ytContenedor.classList.remove("hidden");
      colaCandidatosYoutube = [s.youtube_video_id, ...(s.youtube_alternativas || [])];
      indiceCandidato = 0;
      reproducirYoutube(colaCandidatosYoutube[0]);
    } else if (s.cancion) {
      const c = s.cancion;
      if (c.archivo_video) {
        video.classList.remove("hidden");
        video.src = urlMedia(c.carpeta, c.archivo_video);
        video.play().catch(() => {});
      } else {
        audioFondo.classList.remove("hidden");
        audioFondo.classList.add("flex");
        audio.src = urlMedia(c.carpeta, c.archivo_audio);
        audio.play().catch(() => {});
      }
      if (c.archivo_lyrics) {
        letras.classList.remove("hidden");
        fetch(urlMedia(c.carpeta, c.archivo_lyrics))
          .then((r) => (r.ok ? r.text() : ""))
          .then((texto) => {
            if (texto) lineasLrc = parseLRC(texto);
          })
          .catch(() => {});
      }
    } else {
      manualFondo.classList.remove("hidden");
      manualFondo.classList.add("flex");
    }

    if (!s.mesa_retada_numero) decirMensaje(s.mensaje);
  }

  function actualizarLetras(tiempoActual) {
    if (lineasLrc.length === 0) return;
    const idx = indiceLineaActual(lineasLrc, tiempoActual);
    lrcActual.textContent = idx >= 0 ? lineasLrc[idx].text : "🎶";
    lrcAnterior.textContent = idx > 0 ? lineasLrc[idx - 1].text : "";
    lrcSiguiente.textContent = idx >= 0 && idx + 1 < lineasLrc.length ? lineasLrc[idx + 1].text : "";
  }

  video.addEventListener("timeupdate", () => actualizarLetras(video.currentTime));
  audio.addEventListener("timeupdate", () => actualizarLetras(audio.currentTime));
  video.addEventListener("ended", () => solicitudActualId && marcarFinalizada(solicitudActualId));
  audio.addEventListener("ended", () => solicitudActualId && marcarFinalizada(solicitudActualId));

  let arrancandoAutomatico = false;

  async function refrescar() {
    const [actual, cola] = await Promise.all([
      fetch("/api/dj/actual").then((r) => r.json()),
      fetch("/api/dj/cola").then((r) => r.json()),
    ]);

    if (!actual) {
      idle.classList.remove("hidden");
      reproductor.classList.add("hidden");
      barraProximos.classList.add("hidden");
      if (solicitudActualId) ocultarTodosLosMedios();
      solicitudActualId = null;
      solicitudActualDatos = null;
      idleProximos.innerHTML = cola.slice(0, 6).map(chip).join("") ||
        `<div class="text-white/30 text-sm">La cola está vacía por ahora</div>`;
      actualizarRanking();

      // Nadie está cantando pero hay gente esperando: arranca sola la primera.
      const hayPendientes = cola.some((s) => s.estado === "pendiente");
      if (hayPendientes && !arrancandoAutomatico) {
        arrancandoAutomatico = true;
        await avanzarSiguiente();
        arrancandoAutomatico = false;
      }
      return;
    }

    idle.classList.add("hidden");
    reproductor.classList.remove("hidden");

    if (actual.id !== solicitudActualId) cargarCancion(actual);

    if (infoVotos.textContent !== `🔥 ${actual.votos_fuego || 0}`) {
      infoVotos.textContent = `🔥 ${actual.votos_fuego || 0}`;
      infoVotos.classList.add("scale-125");
      setTimeout(() => infoVotos.classList.remove("scale-125"), 200);
    }
    if (solicitudActualDatos && solicitudActualDatos.id === actual.id) {
      solicitudActualDatos.votos_fuego = actual.votos_fuego;
    }

    avisarSiLeToca(cola, actual);

    const proximos = cola.filter((s) => s.id !== actual.id).slice(0, 6);
    if (proximos.length) {
      barraProximos.classList.remove("hidden");
      barraProximos.classList.add("flex");
      listaProximos.innerHTML = proximos.map(chip).join("");
    } else {
      barraProximos.classList.add("hidden");
    }
  }

  const wsProtocolo = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsProtocolo}://${location.host}/ws`);
  ws.onmessage = () => refrescar();

  refrescar();
  setInterval(refrescar, 10000);
})();
