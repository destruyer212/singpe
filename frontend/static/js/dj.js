(() => {
  const ahoraSonando = document.getElementById("ahora-sonando");
  const colaEl = document.getElementById("cola");

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
    <div class="glass rounded-2xl p-5 border border-neon-pink/40">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-xs text-neon-pink flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-neon-pink pulse-dot"></span> EN VIVO · Mesa ${s.mesa.numero}
            <span class="text-white/40">· 🔥 ${s.votos_fuego || 0}</span>
          </div>
          <div class="text-xl font-bold mt-1">${s.cancion_titulo}</div>
          <div class="text-white/50 text-sm">${s.cancion_artista || ""}${s.cancion_artista ? " · " : ""}canta ${nombresCantantes(s)}</div>
          <div class="text-xs mt-1">${origenBadge(s)}</div>
          ${retoBadge(s)}
          ${s.mensaje ? `<div class="text-xs text-white/40 mt-1">💬 "${s.mensaje}"</div>` : ""}
        </div>
        <div class="flex gap-2">
          <button data-accion="finalizar" data-id="${s.id}" class="px-3 py-2 rounded-xl bg-green-600/70 hover:bg-green-600 text-sm">✅ Finalizar</button>
        </div>
      </div>
    </div>`;
  }

  function tarjetaCola(s, index) {
    return `
    <div class="glass rounded-xl p-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">${index + 1}</div>
        <div>
          <div class="font-semibold">${s.cancion_titulo} <span class="text-white/40 font-normal">${s.cancion_artista ? "· " + s.cancion_artista : ""}</span></div>
          <div class="text-xs text-white/50">Mesa ${s.mesa.numero} · canta ${nombresCantantes(s)} · ${s.modo === "voz_guia" ? "con voz guía" : "karaoke"}</div>
          <div class="text-xs mt-0.5">${origenBadge(s)}</div>
          ${retoBadge(s)}
        </div>
      </div>
      <div class="flex gap-1">
        <button data-accion="arriba" data-id="${s.id}" title="Subir" class="px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs">▲</button>
        <button data-accion="abajo" data-id="${s.id}" title="Bajar" class="px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs">▼</button>
        <button data-accion="iniciar" data-id="${s.id}" class="px-3 py-1.5 rounded-lg bg-neon-purple/70 hover:bg-neon-purple text-xs font-bold">▶ Iniciar</button>
        <button data-accion="cancelar" data-id="${s.id}" class="px-2 py-1.5 rounded-lg bg-red-600/50 hover:bg-red-600/80 text-xs">✕</button>
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

  const wsProtocolo = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsProtocolo}://${location.host}/ws`);
  ws.onmessage = () => cargar();

  cargar();
  setInterval(cargar, 8000);
})();
