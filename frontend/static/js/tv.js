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
  const sfxAudio = document.getElementById("sfx-audio");
  const anuncioAudio = document.getElementById("anuncio-audio");
  const stickerOverlay = document.getElementById("sticker-overlay");
  const stickerEmoji = document.getElementById("sticker-emoji");
  const stickerTexto = document.getElementById("sticker-texto");
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
    const path = encodeURI(`/media/${carpeta}/${archivo}`);
    return window.singpeUrl ? window.singpeUrl(path) : path;
  }

  function chip(s) {
    return `<div class="glass rounded-2xl px-6 py-3 text-xl whitespace-nowrap">🎵 <b>${s.cancion_titulo}</b> · Mesa ${s.mesa.numero}</div>`;
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
        <div class="glass rounded-2xl px-6 py-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="text-4xl">${MEDALLAS[i] || "🎖️"}</span>
            <span class="font-bold text-2xl">Mesa ${r.mesa}</span>
            ${insignia ? `<span class="text-base text-neon-yellow">${insignia}</span>` : ""}
          </div>
          <div class="text-xl text-white/60">🎵 ${r.canciones} · 🔥 ${r.votos}</div>
        </div>`;
      })
      .join("");
  }

  function mostrarTextoGrande(emoji, texto, duracionMs = 4000) {
    if (!texto) return;
    stickerEmoji.textContent = emoji;
    stickerTexto.textContent = texto;
    stickerTexto.classList.remove("hidden");
    stickerOverlay.classList.remove("hidden");
    stickerEmoji.classList.remove("sticker-pop");
    void stickerEmoji.offsetWidth; // reinicia la animación si se dispara de nuevo
    stickerEmoji.classList.add("sticker-pop");
    setTimeout(() => stickerOverlay.classList.add("hidden"), duracionMs);
  }

  // ---------- Ducking: baja la música mientras habla la voz, como en radio ----------
  const VOLUMEN_DUCK = 0.22;
  let vecesHablando = 0;

  function bajarMusica() {
    vecesHablando++;
    video.volume = VOLUMEN_DUCK;
    audio.volume = VOLUMEN_DUCK;
    if (ytPlayer && ytListo) {
      try {
        ytPlayer.setVolume(Math.round(VOLUMEN_DUCK * 100));
      } catch (e) {
        /* si el iframe todavía no está listo, no pasa nada */
      }
    }
  }

  function subirMusica() {
    vecesHablando = Math.max(0, vecesHablando - 1);
    if (vecesHablando > 0) return; // sigue hablando otra voz encimada, no restaurar todavía
    video.volume = 1;
    audio.volume = 1;
    if (ytPlayer && ytListo) {
      try {
        ytPlayer.setVolume(100);
      } catch (e) {
        /* nada que hacer */
      }
    }
  }

  // ---------- Motor de audio para voz/efectos que NO le quita el foco al video ----------
  // En TVs y navegadores de TV, arrancar un segundo <audio>/<video> suele
  // PAUSAR automáticamente el que ya estaba sonando (le quitan el "foco" de
  // audio, como cuando una llamada interrumpe la música). Por eso la voz y
  // los efectos ya no se reproducen con un <audio> normal: se decodifican y
  // se tocan como buffers crudos de Web Audio API, que nunca abren una
  // sesión de medios nueva y por lo tanto nunca pueden pausar el video.
  let audioCtx = null;
  function obtenerAudioCtx() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    return audioCtx;
  }

  const cacheBuffers = new Map();

  async function cargarBuffer(url) {
    if (cacheBuffers.has(url)) return cacheBuffers.get(url);
    const ctx = obtenerAudioCtx();
    const resp = await fetch(url);
    const arrayBuffer = await resp.arrayBuffer();
    const buffer = await ctx.decodeAudioData(arrayBuffer);
    cacheBuffers.set(url, buffer);
    return buffer;
  }

  function reproducirBuffer(buffer, ganancia) {
    const ctx = obtenerAudioCtx();
    const fuente = ctx.createBufferSource();
    fuente.buffer = buffer;
    const nodoGanancia = ctx.createGain();
    nodoGanancia.gain.value = ganancia;
    fuente.connect(nodoGanancia).connect(ctx.destination);
    fuente.start();
    return new Promise((resolve) => {
      fuente.onended = resolve;
    });
  }

  async function reproducirEfectoSonido(nombre) {
    try {
      const buffer = await cargarBuffer(`/static/sfx/${nombre}.wav`);
      await reproducirBuffer(buffer, 1.8);
    } catch (e) {
      /* si falla, simplemente no suena el efecto (el sticker igual se ve) */
    }
  }

  async function reproducirVozConDucking(url) {
    bajarMusica();
    try {
      const buffer = await cargarBuffer(url);
      await reproducirBuffer(buffer, 3.0);
    } catch (e) {
      /* si falla la voz, el texto grande ya quedó visible en pantalla */
    } finally {
      subirMusica();
    }
  }

  function mostrarEfecto(data) {
    if (data.sonido) reproducirEfectoSonido(data.sonido);
    if (data.sticker) mostrarTextoGrande(data.sticker, data.texto || "", 2200);
  }

  async function mostrarAnuncio(data) {
    if (!data.texto) return;
    mostrarTextoGrande("📢", data.texto, 4000);
    try {
      const res = await fetch(`/api/dj/tts?texto=${encodeURIComponent(data.texto)}`);
      if (res.ok) {
        const { url } = await res.json();
        await reproducirVozConDucking(window.singpeUrl ? window.singpeUrl(url) : url);
      }
    } catch (e) {
      /* el texto ya quedó visible aunque falle la voz */
    }
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
    await decirMensaje(`Mesa ${siguiente.mesa.numero}, prepárate, ¡sigues pronto!`, "⏰");
    await fetch(`/api/dj/solicitudes/${siguiente.id}/avisar`, { method: "POST" });
    avisando = false;
  }

  async function marcarFinalizada(id) {
    if (finalizando) return;
    finalizando = true;
    if (solicitudActualDatos && solicitudActualDatos.id === id && solicitudActualDatos.mesa_retada_numero) {
      const votos = solicitudActualDatos.votos_fuego || 0;
      await decirMensaje(
        `¡Fin de la batalla! Mesa ${solicitudActualDatos.mesa.numero} sacó ${votos} fuegos. Mesa ${solicitudActualDatos.mesa_retada_numero}, ¡te toca responder!`,
        "🏆"
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

  async function decirMensaje(texto, emoji = "🗣️") {
    if (!texto) return;
    mostrarTextoGrande(emoji, texto, 4000);
    try {
      const res = await fetch(`/api/dj/tts?texto=${encodeURIComponent(texto)}`);
      if (!res.ok) throw new Error("tts no disponible");
      const { url } = await res.json();
      await reproducirVozConDucking(window.singpeUrl ? window.singpeUrl(url) : url);
    } catch (e) {
      // Si falla el servicio de voz, el mensaje igual queda visible en pantalla grande.
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
      decirMensaje(`¡Batalla! Mesa ${s.mesa.numero} reta a la mesa ${s.mesa_retada_numero}. ¡Voten con el botón de fuego!`, "⚔️");
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

    if (!s.mesa_retada_numero) decirMensaje(s.mensaje, "💬");
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

  // ---------- Arranque: un solo toque desbloquea el audio para toda la noche ----------
  const arranque = document.getElementById("arranque");
  const btnArrancar = document.getElementById("btn-arrancar");
  const CLAVE_DESBLOQUEO = "singpe_tv_desbloqueado";

  function iniciarShow() {
    arranque.remove();
    try {
      sessionStorage.setItem(CLAVE_DESBLOQUEO, "1");
    } catch (e) {
      /* si el navegador bloquea sessionStorage, no pasa nada grave */
    }

    // "Desbloquea" el audio del navegador con este gesto real del usuario,
    // para que loadVideoById()/play() con sonido ya no se bloqueen después.
    audio.muted = false;
    video.muted = false;
    [video, audio].forEach((el) => {
      el.play().then(() => el.pause()).catch(() => {});
    });

    // El motor de voz/efectos (Web Audio API) también necesita arrancar
    // dentro de este gesto real del usuario para poder sonar después.
    const ctx = obtenerAudioCtx();
    if (ctx.state === "suspended") ctx.resume().catch(() => {});

    cargarApiYoutube();

    const ws = new WebSocket(window.singpeWsUrl ? window.singpeWsUrl("/ws") : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    ws.onmessage = (e) => {
      let msg;
      try {
        msg = JSON.parse(e.data);
      } catch (err) {
        return;
      }
      if (msg.tipo === "efecto") mostrarEfecto(msg.data || {});
      else if (msg.tipo === "anuncio") mostrarAnuncio(msg.data || {});
      else refrescar();
    };

    refrescar();
    setInterval(refrescar, 10000);
  }

  let yaDesbloqueado = false;
  try {
    yaDesbloqueado = sessionStorage.getItem(CLAVE_DESBLOQUEO) === "1";
  } catch (e) {
    /* si el navegador bloquea sessionStorage, simplemente pedimos el toque otra vez */
  }

  if (yaDesbloqueado) {
    iniciarShow();
  } else {
    btnArrancar.addEventListener("click", iniciarShow, { once: true });
  }
})();
