(() => {
  const cfgNombre = document.getElementById("cfg-nombre");
  const cfgSegundos = document.getElementById("cfg-segundos");
  const cfgMax = document.getElementById("cfg-max");
  const cfgPuntos = document.getElementById("cfg-puntos");
  const cfgMsg = document.getElementById("cfg-msg");
  const mesasGrid = document.getElementById("mesas-grid");
  const cancionesTabla = document.getElementById("canciones-tabla");
  const escaneoMsg = document.getElementById("escaneo-msg");

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
      <div class="glass rounded-xl p-3 text-center">
        <img src="${m.qr}" class="w-full aspect-square object-contain bg-white rounded-lg mb-2" onerror="this.style.display='none'" />
        <div class="font-bold">Mesa ${m.numero}</div>
        <div class="text-xs text-white/40">${m.puntos} pts</div>
        <a href="${m.qr}" download class="text-xs underline text-neon-cyan">Descargar QR</a>
      </div>`
      )
      .join("");
  }

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
})();
