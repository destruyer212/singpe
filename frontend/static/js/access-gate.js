(() => {
  const requiredRole = document.currentScript.dataset.role || "admin";
  const expectedPin = String(window.SINGPE_ACCESS_PIN || "1234");
  const storageKey = `singpe_access_${requiredRole}`;

  if (sessionStorage.getItem(storageKey) === "1") return;

  document.documentElement.classList.add("overflow-hidden");

  const overlay = document.createElement("div");
  overlay.className = "fixed inset-0 z-[9999] bg-[#0b0620] flex items-center justify-center px-5";
  overlay.innerHTML = `
    <div class="w-full max-w-sm rounded-[1.5rem] border border-white/10 bg-white/10 p-6 shadow-2xl shadow-black/40 backdrop-blur">
      <img src="/static/img/singpe-app-icon-white.png" alt="SingPe" class="mx-auto mb-4 h-24 w-24 rounded-3xl bg-white object-contain" />
      <h1 class="text-center text-2xl font-extrabold">Acceso ${requiredRole.toUpperCase()}</h1>
      <p class="mt-2 text-center text-sm text-white/50">Ingresa el PIN del encargado para continuar.</p>
      <input id="singpe-pin-input" inputmode="numeric" autocomplete="one-time-code" type="password" maxlength="12"
        class="mt-5 w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-center text-xl font-bold tracking-[0.35em] outline-none focus:border-neon-pink" />
      <button id="singpe-pin-button" class="mt-4 w-full rounded-xl bg-gradient-to-r from-neon-pink to-neon-purple py-3 font-bold">
        Entrar
      </button>
      <div id="singpe-pin-error" class="mt-3 hidden text-center text-sm text-red-300">PIN incorrecto</div>
      <a href="/" class="mt-5 block text-center text-xs text-white/40 hover:text-white/70">Volver a elegir mesa</a>
    </div>`;

  document.body.appendChild(overlay);

  const input = overlay.querySelector("#singpe-pin-input");
  const button = overlay.querySelector("#singpe-pin-button");
  const error = overlay.querySelector("#singpe-pin-error");

  function unlock() {
    if (input.value.trim() === expectedPin) {
      sessionStorage.setItem(storageKey, "1");
      overlay.remove();
      document.documentElement.classList.remove("overflow-hidden");
      return;
    }
    error.classList.remove("hidden");
    input.select();
  }

  button.addEventListener("click", unlock);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") unlock();
  });
  setTimeout(() => input.focus(), 50);
})();
