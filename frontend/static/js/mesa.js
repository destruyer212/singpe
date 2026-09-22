(() => {
  const numero = document.currentScript.dataset.numero;
  const esperaSegundos = parseInt(document.currentScript.dataset.espera || "60", 10);

  const cancionInput = document.getElementById("cancion");
  const artistaInput = document.getElementById("artista");
  const resultados = document.getElementById("resultados");
  const ytMsg = document.getElementById("yt-msg");
  const seleccion = document.getElementById("seleccion");
  const selThumb = document.getElementById("sel-thumb");
  const selTitulo = document.getElementById("sel-titulo");
  const selCanal = document.getElementById("sel-canal");
  const btnQuitarSeleccion = document.getElementById("btn-quitar-seleccion");
  const nombreInput = document.getElementById("nombre");
  const mensajeInput = document.getElementById("mensaje");
  const mensajeContador = document.getElementById("mensaje-contador");
  const btnEnviar = document.getElementById("btn-enviar");
  const mensajeEstado = document.getElementById("mensaje-estado");
  const miCola = document.getElementById("mi-cola");
  const gaugeDots = document.getElementById("gauge-dots");
  const gaugeTexto = document.getElementById("gauge-texto");
  const badgeEspera = document.getElementById("badge-espera");
  const badgeEsperaSeg = document.getElementById("badge-espera-seg");
  const tituloForm = document.getElementById("titulo-form");
  const bannerEdicion = document.getElementById("banner-edicion");
  const btnCancelarEdicion = document.getElementById("btn-cancelar-edicion");
  const btnEnviarTexto = document.getElementById("btn-enviar-texto");
  const cantantesLista = document.getElementById("cantantes-lista");
  const btnAgregarCantante = document.getElementById("btn-agregar-cantante");
  const btnToggleReto = document.getElementById("btn-toggle-reto");
  const retoCaja = document.getElementById("reto-caja");
  const mesaRetadaInput = document.getElementById("mesa-retada");

  const MAX_CANTANTES = 4;

  let modo = "karaoke";
  let youtubeVideoId = null;
  let youtubeAlternativas = [];
  let ultimosResultados = [];
  let bloqueadoHasta = 0;
  let editandoId = null;

  const ICONOS_ESTADO = {
    pendiente: "⏳ En cola",
    preparando: "🎬 Preparando",
    cantando: "🎤 ¡Cantando ahora!",
    finalizada: "✅ Cantada",
    cancelada: "❌ Cancelada",
  };

  document.querySelectorAll(".modo-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      modo = btn.dataset.modo;
      document.querySelectorAll(".modo-btn").forEach((b) => {
        b.classList.remove("bg-gradient-to-r", "from-neon-purple", "to-neon-pink");
        b.classList.add("bg-white/5", "border", "border-white/10");
      });
      btn.classList.remove("bg-white/5", "border", "border-white/10");
      btn.classList.add("bg-gradient-to-r", "from-neon-purple", "to-neon-pink");
      limpiarSeleccion();
      dispararBusqueda();
    });
  });

  mensajeInput.addEventListener("input", () => {
    mensajeContador.textContent = mensajeInput.value.length;
  });

  function agregarCampoCantante(valor = "") {
    const actuales = cantantesLista.querySelectorAll("input").length;
    if (actuales >= MAX_CANTANTES) return;
    const fila = document.createElement("div");
    fila.className = "flex gap-2";
    fila.innerHTML = `
      <input type="text" maxlength="40" placeholder="Otro cantante..." value="${valor.replace(/"/g, "&quot;")}"
        class="cantante-extra flex-1 bg-black/30 border border-white/10 rounded-xl px-4 py-3 outline-none focus:border-neon-pink" />
      <button type="button" class="btn-quitar-cantante w-11 rounded-xl bg-white/10 hover:bg-white/20 text-white/60">✕</button>`;
    fila.querySelector(".btn-quitar-cantante").addEventListener("click", () => fila.remove());
    cantantesLista.appendChild(fila);
  }

  btnAgregarCantante.addEventListener("click", () => agregarCampoCantante());

  function limpiarCantantesExtra() {
    cantantesLista.querySelectorAll(".cantante-extra").forEach((el) => el.closest("div").remove());
  }

  function obtenerCantantes() {
    const nombres = [nombreInput.value.trim()];
    cantantesLista.querySelectorAll(".cantante-extra").forEach((el) => {
      if (el.value.trim()) nombres.push(el.value.trim());
    });
    return nombres.filter(Boolean);
  }

  function establecerCantantes(lista) {
    limpiarCantantesExtra();
    const nombres = (lista || []).filter(Boolean);
    nombreInput.value = nombres[0] || "";
    nombres.slice(1).forEach((n) => agregarCampoCantante(n));
  }

  btnToggleReto.addEventListener("click", () => {
    retoCaja.classList.toggle("hidden");
  });

  function limpiarSeleccion() {
    youtubeVideoId = null;
    youtubeAlternativas = [];
    seleccion.classList.add("hidden");
  }

  function limpiarFormulario() {
    cancionInput.value = "";
    artistaInput.value = "";
    mensajeInput.value = "";
    mensajeContador.textContent = "0";
    limpiarSeleccion();
    limpiarCantantesExtra();
    nombreInput.value = "";
    retoCaja.classList.add("hidden");
    mesaRetadaInput.value = "";
    resultados.innerHTML = "";
    ytMsg.textContent = "";
  }

  function entrarModoEdicion(s) {
    editandoId = s.id;
    cancionInput.value = s.cancion_titulo || "";
    artistaInput.value = s.cancion_artista || "";
    establecerCantantes(s.cantantes && s.cantantes.length ? s.cantantes : [s.nombre_cantante]);
    mensajeInput.value = s.mensaje || "";
    mensajeContador.textContent = (s.mensaje || "").length;
    if (s.mesa_retada_numero) {
      retoCaja.classList.remove("hidden");
      mesaRetadaInput.value = s.mesa_retada_numero;
    } else {
      retoCaja.classList.add("hidden");
      mesaRetadaInput.value = "";
    }
    youtubeVideoId = s.youtube_video_id || null;
    youtubeAlternativas = s.youtube_alternativas || [];
    if (youtubeVideoId) {
      selThumb.src = `https://img.youtube.com/vi/${youtubeVideoId}/mqdefault.jpg`;
      selTitulo.textContent = s.cancion_titulo;
      selCanal.textContent = s.cancion_artista || "";
      seleccion.classList.remove("hidden");
    } else {
      seleccion.classList.add("hidden");
    }
    modo = s.modo;
    document.querySelectorAll(".modo-btn").forEach((b) => {
      const activo = b.dataset.modo === modo;
      b.classList.toggle("bg-gradient-to-r", activo);
      b.classList.toggle("from-neon-purple", activo);
      b.classList.toggle("to-neon-pink", activo);
      b.classList.toggle("bg-white/5", !activo);
      b.classList.toggle("border", !activo);
      b.classList.toggle("border-white/10", !activo);
    });
    tituloForm.textContent = "✏️ Editando tu pedido";
    bannerEdicion.classList.remove("hidden");
    btnEnviarTexto.textContent = "Guardar cambios ✏️";
    mensajeEstado.textContent = "";
    resultados.innerHTML = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function salirModoEdicion() {
    editandoId = null;
    tituloForm.textContent = "🚩 Nueva solicitud";
    bannerEdicion.classList.add("hidden");
    btnEnviarTexto.textContent = "Enviar a la cola 🎤";
    limpiarFormulario();
  }

  btnCancelarEdicion.addEventListener("click", salirModoEdicion);

  function elegirResultado(video) {
    youtubeVideoId = video.video_id;
    // Otras versiones del mismo tema (mismo resultado de búsqueda, distinto canal):
    // si la principal queda bloqueada, la pantalla TV prueba estas solas.
    youtubeAlternativas = ultimosResultados.filter((id) => id !== video.video_id);
    cancionInput.value = video.titulo;
    artistaInput.value = video.canal;
    selThumb.src = video.miniatura || "";
    selTitulo.textContent = video.titulo;
    selCanal.textContent = video.canal;
    seleccion.classList.remove("hidden");
    resultados.innerHTML = "";
  }

  btnQuitarSeleccion.addEventListener("click", limpiarSeleccion);

  async function buscarYoutube(q) {
    if (!q) {
      resultados.innerHTML = "";
      ytMsg.textContent = "";
      return;
    }
    ytMsg.textContent = "Buscando en YouTube...";
    const res = await fetch(`/api/mesas/youtube?q=${encodeURIComponent(q)}&modo=${encodeURIComponent(modo)}`);
    const data = await res.json();
    resultados.innerHTML = "";

    if (!data.disponible) {
      ytMsg.textContent = "Búsqueda no disponible por ahora — igual puedes escribir la canción arriba.";
      return;
    }
    if (data.resultados.length === 0) {
      ytMsg.textContent = "Sin resultados. Prueba con otro nombre.";
      return;
    }
    ytMsg.textContent = "";
    ultimosResultados = data.resultados.map((v) => v.video_id);
    data.resultados.forEach((video) => {
      const div = document.createElement("button");
      div.type = "button";
      div.className = "w-full text-left glass rounded-xl p-2 flex items-center gap-3 hover:bg-white/10";
      div.innerHTML = `
        <img src="${video.miniatura || ""}" class="w-16 h-10 object-cover rounded-lg bg-white/10" />
        <div class="min-w-0">
          <div class="text-sm font-semibold truncate">${video.titulo}</div>
          <div class="text-xs text-white/40 truncate">${video.canal}</div>
        </div>`;
      div.onclick = () => elegirResultado(video);
      resultados.appendChild(div);
    });
  }

  function construirConsulta() {
    const cancion = cancionInput.value.trim();
    const artista = artistaInput.value.trim();
    if (cancion.length < 2) return "";
    return artista ? `${cancion} ${artista}` : cancion;
  }

  let debounce;
  function dispararBusqueda() {
    clearTimeout(debounce);
    debounce = setTimeout(() => buscarYoutube(construirConsulta()), 350);
  }
  cancionInput.addEventListener("input", dispararBusqueda);
  artistaInput.addEventListener("input", dispararBusqueda);

  function actualizarBadgeEspera() {
    const restante = Math.ceil((bloqueadoHasta - Date.now()) / 1000);
    if (restante > 0) {
      btnEnviar.disabled = true;
      badgeEspera.classList.remove("hidden");
      badgeEsperaSeg.textContent = restante;
      setTimeout(actualizarBadgeEspera, 1000);
    } else {
      btnEnviar.disabled = false;
      badgeEspera.classList.add("hidden");
    }
  }

  function iniciarEspera(segundos) {
    bloqueadoHasta = Date.now() + segundos * 1000;
    actualizarBadgeEspera();
  }

  btnEnviar.addEventListener("click", async () => {
    const titulo = cancionInput.value.trim();
    if (!titulo) {
      mensajeEstado.className = "text-sm text-center text-red-400";
      mensajeEstado.textContent = "Escribe el nombre de la canción";
      cancionInput.focus();
      return;
    }
    btnEnviar.disabled = true;

    const editando = editandoId !== null;
    const url = editando
      ? `/api/mesas/${numero}/solicitudes/${editandoId}/editar`
      : `/api/mesas/${numero}/solicitudes`;

    const cantantes = obtenerCantantes();
    const mesaRetada = parseInt(mesaRetadaInput.value, 10);

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cancion_titulo: titulo,
        cancion_artista: artistaInput.value.trim() || null,
        youtube_video_id: youtubeVideoId,
        youtube_alternativas: youtubeAlternativas,
        nombre_cantante: cantantes[0] || "",
        cantantes: cantantes.length > 1 ? cantantes : null,
        mensaje: mensajeInput.value.trim() || null,
        mesa_retada_numero: Number.isInteger(mesaRetada) && mesaRetada > 0 ? mesaRetada : null,
        modo,
      }),
    });

    if (res.ok) {
      if (editando) {
        editandoId = null;
        tituloForm.textContent = "🚩 Nueva solicitud";
        bannerEdicion.classList.add("hidden");
        btnEnviarTexto.textContent = "Enviar a la cola 🎤";
        mensajeEstado.className = "text-sm text-center text-green-400";
        mensajeEstado.textContent = "¡Cambios guardados, sigues en tu lugar en la cola! ✅";
        limpiarFormulario();
        btnEnviar.disabled = false;
      } else {
        mensajeEstado.className = "text-sm text-center text-green-400";
        mensajeEstado.textContent = "¡Canción agregada a la cola! 🎉";
        limpiarFormulario();
        // El botón vuelve a habilitarse solo cuando termine la espera anti-spam.
        iniciarEspera(esperaSegundos);
      }
      cargarMiCola();
      actualizarGauge();
    } else {
      const err = await res.json();
      const detalle = err.detail || {};
      mensajeEstado.className = "text-sm text-center text-red-400";
      mensajeEstado.textContent = detalle.motivo || "No se pudo agregar la canción";
      if (detalle.segundos_restantes) {
        iniciarEspera(detalle.segundos_restantes);
      } else {
        btnEnviar.disabled = false;
      }
    }
  });

  let ultimaColaPropia = [];

  async function cargarMiCola() {
    const res = await fetch(`/api/mesas/${numero}/cola`);
    const data = await res.json();
    ultimaColaPropia = data;
    if (data.length === 0) {
      miCola.innerHTML = `<div class="text-white/30 text-center py-3">Aún no has pedido canciones</div>`;
      return;
    }
    miCola.innerHTML = data
      .map((s) => {
        const editable = s.estado === "pendiente";
        const cantantesTexto = s.cantantes && s.cantantes.length ? s.cantantes.join(" & ") : s.nombre_cantante || "";
        const retoTexto = s.mesa_retada_numero ? ` · ⚔️ vs Mesa ${s.mesa_retada_numero}` : "";
        return `
      <div class="glass rounded-xl p-3 flex items-center justify-between gap-2">
        <div class="min-w-0">
          <div class="font-semibold truncate">${s.cancion_titulo}</div>
          <div class="text-xs text-white/50 truncate">${s.cancion_artista || ""}${s.cancion_artista ? " · " : ""}${cantantesTexto}${retoTexto}</div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-xs">${ICONOS_ESTADO[s.estado] || s.estado}</span>
          ${
            editable
              ? `<button data-accion="editar" data-id="${s.id}" title="Corregir" class="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center">✏️</button>
                 <button data-accion="eliminar" data-id="${s.id}" title="Quitar de la cola" class="w-7 h-7 rounded-lg bg-red-600/30 hover:bg-red-600/60 flex items-center justify-center">🗑️</button>`
              : ""
          }
        </div>
      </div>`;
      })
      .join("");
  }

  miCola.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-accion]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.accion === "editar") {
      const s = ultimaColaPropia.find((x) => x.id === id);
      if (s) entrarModoEdicion(s);
      return;
    }

    if (btn.dataset.accion === "eliminar") {
      if (!confirm("¿Quitar esta canción de tu cola?")) return;
      const res = await fetch(`/api/mesas/${numero}/solicitudes/${id}/eliminar`, { method: "POST" });
      if (res.ok) {
        if (editandoId === id) salirModoEdicion();
        cargarMiCola();
        actualizarGauge();
      }
    }
  });

  const MAX_DOTS = 8;
  const btnVotoFuego = document.getElementById("btn-voto-fuego");
  const votoFuegoContador = document.getElementById("voto-fuego-contador");

  async function actualizarGauge() {
    const data = await fetch("/api/mesas/estado").then((r) => r.json());
    const n = data.en_cola || 0;
    const llenos = Math.min(n, MAX_DOTS);
    gaugeDots.innerHTML = Array.from({ length: MAX_DOTS }, (_, i) =>
      `<span class="w-1.5 h-1.5 rounded-full ${i < llenos ? "bg-neon-pink" : "bg-white/15"}"></span>`
    ).join("");
    gaugeTexto.textContent = `${n}/${MAX_DOTS}`;

    // El botón de voto 🔥 solo aparece si OTRA mesa está cantando ahora.
    const hayShowAjeno = data.cantando_mesa && data.cantando_mesa !== parseInt(numero, 10);
    btnVotoFuego.classList.toggle("hidden", !hayShowAjeno);
    if (hayShowAjeno) votoFuegoContador.textContent = data.cantando_votos || 0;
  }

  btnVotoFuego.addEventListener("click", async () => {
    btnVotoFuego.classList.add("scale-110");
    setTimeout(() => btnVotoFuego.classList.remove("scale-110"), 150);
    const res = await fetch("/api/dj/actual/votar", { method: "POST" });
    if (res.ok) {
      const s = await res.json();
      votoFuegoContador.textContent = s.votos_fuego;
    }
  });

  const wsProtocolo = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsProtocolo}://${location.host}/ws`);
  ws.onmessage = () => {
    cargarMiCola();
    actualizarGauge();
  };

  cargarMiCola();
  actualizarGauge();
})();
