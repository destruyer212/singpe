(() => {
  const ahoraSonando = document.getElementById("ahora-sonando");
  const colaEl = document.getElementById("cola");
  const soundboard = document.getElementById("soundboard");
  const anuncioTexto = document.getElementById("anuncio-texto");
  const btnAnuncio = document.getElementById("btn-anuncio");

  async function api(path, method = "POST") {
    const res = await fetch(path, { method });
    return res.ok;
  }

  function origenBadge(s) {
    if (s.youtube_video_id) {
      return `<a href="https://youtube.com/watch?v=${s.youtube_video_id}" target="_blank" class="text-red-400 hover:underline">▶ YouTube ↗</a>`;
    }
    if (s.cancion_id) {
      return `<span class="text-neon-cyan">📀 Biblioteca propia</span>`;
    }
    return `<span class="text-yellow-300">✋ Pedido libre (buscar manualmente)</span>`;
  }

  function nombresCantantes(s) {
    return s.cantantes && s.cantantes.length ? s.cantantes.join(" & ") : s.nombre_cantante || "Anónimo";
  }

  function retoBadge(s) {
    return s.mesa_retada_numero
      ? `<div class="text-xs text-orange-300 mt-0.5">⚔️ Mesa ${s.mesa.numero} reta a Mesa ${s.mesa_retada_numero}</div>`
      : "";
  }

  function tarjetaActual(s) {
    return `
    <div class="glass rounded-2xl p-5 border-2 border-neon-pink/50 shadow-lg shadow-pink-900/20">
      <div class="flex items-center justify-between gap-4">
        <div class="min-w-0">
          <div class="text-xs text-neon-pink flex items-center gap-2 font-bold">
            <span class="w-2 h-2 rounded-full bg-neon-pink pulse-dot"></span> EN VIVO · Mesa ${s.mesa.numero}
            <span class="text-orange-300">🔥 ${s.votos_fuego || 0}</span>
          </div>
          <div class="text-xl font-bold mt-1">${s.cancion_titulo}</div>
          <div class="text-white/50 text-sm">${s.cancion_artista || ""}${s.cancion_artista ? " · " : ""}canta ${nombresCantantes(s)}</div>
          <div class="text-xs mt-1">${origenBadge(s)}</div>
          ${retoBadge(s)}
          ${s.mensaje ? `<div class="text-xs text-white/40 mt-1">💬 "${s.mensaje}"</div>` : ""}
        </div>
        <button data-accion="finalizar" data-id="${s.id}"
          class="shrink-0 px-5 py-3 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 font-bold text-sm shadow-lg shadow-green-900/30 hover:scale-105 active:scale-95 transition-transform">
          ✅ Finalizar
        </button>
      </div>
    </div>`;
  }

  function tarjetaCola(s, index) {
    return `
    <div class="glass rounded-xl p-3 flex items-center justify-between gap-2">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-neon-purple to-neon-pink flex items-center justify-center text-xs font-extrabold">${index + 1}</div>
        <div class="min-w-0">
          <div class="font-semibold truncate">${s.cancion_titulo} <span class="text-white/40 font-normal">${s.cancion_artista ? "· " + s.cancion_artista : ""}</span></div>
          <div class="text-xs text-white/50">Mesa ${s.mesa.numero} · canta ${nombresCantantes(s)} · ${s.modo === "voz_guia" ? "con voz guía" : "karaoke"}</div>
          <div class="text-xs mt-0.5">${origenBadge(s)}</div>
          ${retoBadge(s)}
        </div>
      </div>
      <div class="flex gap-1.5 shrink-0">
        <button data-accion="arriba" data-id="${s.id}" title="Subir" class="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 hover:scale-105 active:scale-95 transition-transform text-sm">▲</button>
        <button data-accion="abajo" data-id="${s.id}" title="Bajar" class="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 hover:scale-105 active:scale-95 transition-transform text-sm">▼</button>
        <button data-accion="iniciar" data-id="${s.id}"
          class="px-4 h-9 rounded-xl bg-gradient-to-r from-neon-purple to-neon-pink hover:opacity-90 hover:scale-105 active:scale-95 transition-transform text-xs font-bold shadow-md shadow-purple-900/30">
          ▶ Iniciar
        </button>
        <button data-accion="cancelar" data-id="${s.id}" title="Quitar" class="w-9 h-9 rounded-xl bg-red-600/40 hover:bg-red-600/70 hover:scale-105 active:scale-95 transition-transform text-sm">✕</button>
      </div>
    </div>`;
  }

  async function cargar() {
    const [colaRes, actualRes] = await Promise.all([
      fetch("/api/dj/cola").then((r) => r.json()),
      fetch("/api/dj/actual").then((r) => r.json()),
    ]);

    ahoraSonando.innerHTML = actualRes
      ? tarjetaActual(actualRes)
      : `<div class="glass rounded-2xl p-5 text-white/40 text-center">Nadie está cantando ahora mismo</div>`;

    const pendientes = colaRes.filter((s) => !actualRes || s.id !== actualRes.id);
    colaEl.innerHTML = pendientes.length
      ? pendientes.map(tarjetaCola).join("")
      : `<div class="glass rounded-xl p-4 text-white/30 text-center text-sm">La cola está vacía</div>`;
  }

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-accion]");
    if (!btn) return;
    const { accion, id } = btn.dataset;
    if (accion === "arriba" || accion === "abajo") {
      await fetch(`/api/dj/solicitudes/${id}/mover?direccion=${accion}`, { method: "POST" });
    } else {
      await api(`/api/dj/solicitudes/${id}/${accion}`);
    }
    cargar();
  });

  // ---------- Soundboard ----------
  const EFECTOS = [
    { sonido: "aplausos", sticker: "🔥", texto: "¡Está que arde!", color: "from-orange-500 to-red-600" },
    { sonido: "fanfarria", sticker: "👑", texto: "¡Rey/Reina del Karaoke!", color: "from-yellow-400 to-amber-600" },
    { sonido: "error", sticker: "😂", texto: "Plot twist", color: "from-slate-500 to-slate-700" },
    { sonido: "redoble", sticker: "🥁", texto: "Redoble de tambor...", color: "from-purple-600 to-indigo-700" },
    { sonido: "sirena", sticker: "🚨", texto: "¡Alerta desafinado!", color: "from-red-600 to-rose-700" },
    { sonido: "campana", sticker: "🔔", texto: "¡Bien ahí!", color: "from-cyan-500 to-blue-600" },
    { sonido: "aire", sticker: "📯", texto: "¡EEEOOO!", color: "from-pink-500 to-fuchsia-600" },
    { sonido: "aplausos", sticker: "👏", texto: "", color: "from-emerald-500 to-teal-600" },
  ];

  soundboard.innerHTML = EFECTOS.map(
    (e, i) => `
    <button data-efecto-i="${i}"
      class="btn-efecto relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br ${e.color} text-left shadow-lg hover:scale-[1.03] active:scale-95 transition-transform">
      <div class="text-3xl mb-1">${e.sticker}</div>
      <div class="text-xs font-bold leading-tight">${e.texto || e.sonido}</div>
    </button>`
  ).join("");

  soundboard.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-efecto-i]");
    if (!btn) return;
    const efecto = EFECTOS[parseInt(btn.dataset.efectoI, 10)];
    btn.classList.add("scale-95");
    setTimeout(() => btn.classList.remove("scale-95"), 150);
    await fetch("/api/dj/efecto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(efecto),
    });
  });

  btnAnuncio.addEventListener("click", async () => {
    const texto = anuncioTexto.value.trim();
    if (!texto) return;
    btnAnuncio.disabled = true;
    await fetch("/api/dj/anuncio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    anuncioTexto.value = "";
    btnAnuncio.disabled = false;
  });
  anuncioTexto.addEventListener("keydown", (e) => {
    if (e.key === "Enter") btnAnuncio.click();
  });

  const ws = new WebSocket(window.singpeWsUrl ? window.singpeWsUrl("/ws") : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.onmessage = () => cargar();

  cargar();
  setInterval(cargar, 8000);
})();
