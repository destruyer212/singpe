(() => {
  const cfgNombre = document.getElementById("cfg-nombre");
  const cfgSegundos = document.getElementById("cfg-segundos");
  const cfgMax = document.getElementById("cfg-max");
  const cfgPuntos = document.getElementById("cfg-puntos");
  const cfgMsg = document.getElementById("cfg-msg");
  const mesasGrid = document.getElementById("mesas-grid");
  const cancionesTabla = document.getElementById("canciones-tabla");
  const escaneoMsg = document.getElementById("escaneo-msg");
  const ytUsoNumero = document.getElementById("yt-uso-numero");
  const ytUsoBarra = document.getElementById("yt-uso-barra");
  const ytUsoDetalle = document.getElementById("yt-uso-detalle");

  async function cargarUsoYoutube() {
    const u = await fetch("/api/admin/youtube-uso").then((r) => r.json());
    if (!u.disponible) {
      ytUsoNumero.textContent = "–";
      ytUsoDetalle.textContent = "No hay API key configurada (búsqueda de YouTube desactivada).";
      ytUsoBarra.style.width = "0%";
      return;
    }
    const pct = Math.min(100, Math.round((u.busquedas / u.limite_estimado) * 100));
    ytUsoNumero.textContent = u.busquedas;
    ytUsoDetalle.textContent = `Hoy (${u.fecha}) · se resetea a medianoche hora de California`;
    ytUsoBarra.style.width = `${pct}%`;
    ytUsoBarra.className = "h-full rounded-full transition-all " + (pct >= 90 ? "bg-red-500" : pct >= 60 ? "bg-yellow-400" : "bg-neon-cyan");
  }

  async function cargarConfig() {
    const c = await fetch("/api/admin/config").then((r) => r.json());
    cfgNombre.value = c.nombre_evento;
    cfgSegundos.value = c.segundos_entre_pedidos;
    cfgMax.value = c.max_pendientes_por_mesa;
    cfgPuntos.value = c.puntos_por_cancion;
  }

  document.getElementById("btn-guardar-cfg").addEventListener("click", async () => {
    await fetch("/api/admin/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre_evento: cfgNombre.value,
        segundos_entre_pedidos: parseInt(cfgSegundos.value, 10),
        max_pendientes_por_mesa: parseInt(cfgMax.value, 10),
        puntos_por_cancion: parseInt(cfgPuntos.value, 10),
      }),
    });
    cfgMsg.textContent = "Guardado ✓";
    setTimeout(() => (cfgMsg.textContent = ""), 2000);
  });

  async function cargarMesas() {
    const mesas = await fetch("/api/admin/mesas").then((r) => r.json());
    mesasGrid.innerHTML = mesas
      .map(
        (m) => `
      <div class="glass rounded-xl p-3 text-center ${m.activo ? "" : "opacity-50"}">
        <img src="${m.qr}" class="w-full aspect-square object-contain bg-white rounded-lg mb-2" onerror="this.style.display='none'" />
        <div class="font-bold">Mesa ${m.numero}</div>
        <div class="text-xs text-white/40">${m.puntos} pts</div>
        <div class="flex items-center justify-center gap-1 mt-1 text-xs text-white/50">
          👥 <input type="number" min="1" value="${m.capacidad}" data-numero="${m.numero}"
            class="input-capacidad w-12 bg-black/30 border border-white/10 rounded-lg px-1 py-0.5 text-center" />
        </div>
        <button data-numero="${m.numero}" data-activo="${m.activo}"
          class="btn-toggle-activo mt-2 w-full text-xs py-1.5 rounded-lg font-semibold ${m.activo ? "bg-green-600/30 text-green-300 hover:bg-red-600/30 hover:text-red-300" : "bg-red-600/30 text-red-300 hover:bg-green-600/30 hover:text-green-300"}">
          ${m.activo ? "✓ Activa" : "✕ Inactiva"}
        </button>
        <a href="${m.qr}" download class="block mt-1 text-xs underline text-neon-cyan">Descargar QR</a>
      </div>`
      )
      .join("");
  }

  mesasGrid.addEventListener("click", async (e) => {
    const btn = e.target.closest(".btn-toggle-activo");
    if (!btn) return;
    const activoActual = btn.dataset.activo === "true";
    await fetch(`/api/admin/mesas/${btn.dataset.numero}/activo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activo: !activoActual }),
    });
    cargarMesas();
  });

  mesasGrid.addEventListener("change", async (e) => {
    const input = e.target.closest(".input-capacidad");
    if (!input) return;
    const capacidad = parseInt(input.value, 10) || 1;
    await fetch(`/api/admin/mesas/${input.dataset.numero}/capacidad`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capacidad }),
    });
  });

  document.getElementById("btn-generar-mesas").addEventListener("click", async () => {
    const cantidad = parseInt(document.getElementById("cantidad-mesas").value, 10) || 1;
    await fetch("/api/admin/mesas/generar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cantidad }),
    });
    cargarMesas();
  });

  async function cargarCanciones() {
    const canciones = await fetch("/api/admin/canciones").then((r) => r.json());
    if (canciones.length === 0) {
      cancionesTabla.innerHTML = `<div class="text-white/30 text-center py-4">Aún no hay canciones registradas</div>`;
      return;
    }
    cancionesTabla.innerHTML = canciones
      .map(
        (c) => `
      <div class="flex items-center justify-between border-b border-white/5 py-1.5">
        <span>${c.titulo} <span class="text-white/40">· ${c.artista}</span></span>
        <span class="text-xs ${c.activo ? "text-green-400" : "text-red-400"}">${c.activo ? "activa" : "inactiva"}</span>
      </div>`
      )
      .join("");
  }

  document.getElementById("btn-escanear").addEventListener("click", async () => {
    const r = await fetch("/api/admin/biblioteca/escanear", { method: "POST" }).then((r) => r.json());
    escaneoMsg.textContent = `Nuevas: ${r.nuevas} · Actualizadas: ${r.actualizadas} · Desactivadas: ${r.desactivadas}`;
    cargarCanciones();
  });

  cargarConfig();
  cargarMesas();
  cargarCanciones();
  cargarUsoYoutube();
  setInterval(cargarUsoYoutube, 30000);
})();
