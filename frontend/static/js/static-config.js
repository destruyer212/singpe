(() => {
  fetch("/api/admin/config")
    .then((r) => (r.ok ? r.json() : null))
    .then((config) => {
      if (!config) return;
      document.querySelectorAll(".evento-nombre").forEach((el) => {
        el.textContent = config.nombre_evento || "SingPe Karaoke";
      });
    })
    .catch(() => {});
})();
