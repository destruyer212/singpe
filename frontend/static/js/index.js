(() => {
  const eventoNombre = document.getElementById("evento-nombre");
  const mesasLista = document.getElementById("mesas-lista");
  const mesasVacias = document.getElementById("mesas-vacias");

  async function cargar() {
    try {
      const [config, mesas] = await Promise.all([
        fetch("/api/admin/config").then((r) => r.json()),
        fetch("/api/admin/mesas").then((r) => r.json()).catch(() => []),
      ]);

      if (eventoNombre) eventoNombre.textContent = config.nombre_evento || "SingPe Karaoke";

      const activas = (mesas || []).filter((m) => m.activo !== false);
      if (!mesasLista) return;
      if (!activas.length) {
        mesasLista.classList.add("hidden");
        mesasVacias?.classList.remove("hidden");
        return;
      }
      mesasVacias?.classList.add("hidden");
      mesasLista.classList.remove("hidden");
      mesasLista.innerHTML = activas
        .map((m) => `<a href="/mesa/${m.numero}" class="px-4 py-2 rounded-full glass hover:bg-white/10 text-sm">Mesa ${m.numero}</a>`)
        .join("");
    } catch (e) {
      if (eventoNombre) eventoNombre.textContent = "SingPe Karaoke";
    }
  }

  cargar();
})();
