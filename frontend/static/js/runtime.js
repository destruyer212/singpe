(() => {
  const explicitBase =
    window.SINGPE_API_BASE ||
    document.querySelector('meta[name="singpe-api-base"]')?.content ||
    "";
  const apiBase = explicitBase.replace(/\/$/, "");

  function isBackendPath(path) {
    return (
      path.startsWith("/api/") ||
      path === "/api" ||
      path.startsWith("/media/") ||
      path.startsWith("/static/qr/") ||
      path.startsWith("/static/tts_cache/")
    );
  }

  window.singpeUrl = function singpeUrl(path) {
    if (!path || typeof path !== "string") return path;
    if (/^(https?:|wss?:|data:|blob:)/i.test(path)) return path;
    if (!apiBase || !isBackendPath(path)) return path;
    return `${apiBase}${path}`;
  };

  window.singpeWsUrl = function singpeWsUrl(path = "/ws") {
    const base = apiBase || `${location.protocol}//${location.host}`;
    const url = new URL(path, base);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return url.toString();
  };

  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    if (typeof input === "string") return nativeFetch(window.singpeUrl(input), init);
    return nativeFetch(input, init);
  };
})();
