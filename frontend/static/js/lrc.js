// Parser sencillo de letras sincronizadas en formato .lrc
// Devuelve una lista ordenada de { time: segundos, text: "línea" }
function parseLRC(texto) {
  const lineas = [];
  const regexTiempo = /\[(\d{2}):(\d{2})(?:[.:](\d{1,3}))?\]/g;

  texto.split(/\r?\n/).forEach((linea) => {
    const tiempos = [...linea.matchAll(regexTiempo)];
    if (tiempos.length === 0) return;
    const contenido = linea.replace(regexTiempo, "").trim();
    tiempos.forEach((m) => {
      const min = parseInt(m[1], 10);
      const seg = parseInt(m[2], 10);
      const ms = m[3] ? parseInt(m[3].padEnd(3, "0"), 10) : 0;
      lineas.push({ time: min * 60 + seg + ms / 1000, text: contenido });
    });
  });

  return lineas.sort((a, b) => a.time - b.time);
}

// Devuelve el índice de la línea activa según el tiempo actual de reproducción.
function indiceLineaActual(lineas, tiempoActual) {
  let idx = -1;
  for (let i = 0; i < lineas.length; i++) {
    if (lineas[i].time <= tiempoActual) idx = i;
    else break;
  }
  return idx;
}
