"""Genera los efectos de sonido del soundboard del DJ (frontend/static/sfx/).
100% sintéticos con la librería estándar de Python (sin descargas externas,
así nunca dependen de un link roto ni de licencias de terceros).

Ejecutar: python scripts/make_efectos.py
"""
import math
import random
import struct
import wave
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DESTINO = BASE_DIR / "frontend" / "static" / "sfx"
MUESTREO = 44100


def _escribir(nombre: str, muestras: list[float]):
    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / f"{nombre}.wav"
    with wave.open(str(ruta), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(MUESTREO)
        frames = bytearray()
        for m in muestras:
            valor = max(-1.0, min(1.0, m))
            frames += struct.pack("<h", int(valor * 32000))
        wav.writeframes(bytes(frames))
    print(f"  {nombre}.wav ({len(muestras) / MUESTREO:.2f}s)")


def _envolvente(t, duracion, ataque=0.02, caida=0.3):
    if t < ataque:
        return t / ataque
    return max(0.0, 1.0 - (t - ataque) / (duracion - ataque)) ** caida * 1.2


def aire():
    """Bocina de estadio (air horn): dos tonos graves sostenidos con vibra."""
    duracion = 1.4
    n = int(MUESTREO * duracion)
    muestras = []
    for i in range(n):
        t = i / MUESTREO
        vibra = 1 + 0.01 * math.sin(2 * math.pi * 6 * t)
        onda = 0.6 * math.sin(2 * math.pi * 233 * vibra * t) + 0.4 * math.sin(2 * math.pi * 116 * vibra * t)
        env = min(1.0, t / 0.05) * min(1.0, (duracion - t) / 0.15)
        muestras.append(onda * env * 0.9)
    _escribir("aire", muestras)


def campana():
    """Ding de campana brillante (para 'bien ahí')."""
    duracion = 1.2
    n = int(MUESTREO * duracion)
    muestras = []
    for i in range(n):
        t = i / MUESTREO
        onda = (
            math.sin(2 * math.pi * 1046 * t) * 0.5
            + math.sin(2 * math.pi * 1568 * t) * 0.3
            + math.sin(2 * math.pi * 2093 * t) * 0.2
        )
        env = math.exp(-t * 4.5)
        muestras.append(onda * env)
    _escribir("campana", muestras)


def redoble():
    """Redoble de tambor creciente + platillazo final (para crear suspenso)."""
    duracion = 2.0
    n = int(MUESTREO * duracion)
    muestras = []
    random.seed(7)
    for i in range(n):
        t = i / MUESTREO
        progreso = t / duracion
        # golpes de ruido cada vez más rápidos
        frecuencia_golpe = 8 + progreso * 40
        fase_golpe = (t * frecuencia_golpe) % 1.0
        pulso = 1.0 if fase_golpe < 0.25 else 0.0
        ruido = (random.random() * 2 - 1) * pulso
        muestras.append(ruido * (0.3 + progreso * 0.6))
    # platillazo final: ruido con caída larga
    cola_n = int(MUESTREO * 1.0)
    for i in range(cola_n):
        t = i / MUESTREO
        ruido = random.random() * 2 - 1
        env = math.exp(-t * 3)
        muestras.append(ruido * env * 0.8)
    _escribir("redoble", muestras)


def sirena():
    """Sirena tipo alarma (para 'alerta desafinado')."""
    duracion = 1.6
    n = int(MUESTREO * duracion)
    muestras = []
    fase = 0.0
    for i in range(n):
        t = i / MUESTREO
        freq = 500 + 300 * math.sin(2 * math.pi * 2.2 * t)
        fase += freq / MUESTREO
        onda = math.sin(2 * math.pi * fase)
        env = min(1.0, t / 0.05) * min(1.0, (duracion - t) / 0.1)
        muestras.append(onda * env * 0.75)
    _escribir("sirena", muestras)


def error():
    """'Womp womp' descendente (broma cuando alguien desafina)."""
    duracion = 1.0
    n = int(MUESTREO * duracion)
    muestras = []
    fase = 0.0
    for i in range(n):
        t = i / MUESTREO
        freq = 220 - t * 140
        fase += freq / MUESTREO
        onda = math.copysign(1.0, math.sin(2 * math.pi * fase)) * 0.35  # onda cuadrada, sonido "de juego"
        env = min(1.0, t / 0.02) * math.exp(-max(0, t - 0.3) * 3)
        muestras.append(onda * env)
    _escribir("error", muestras)


def fanfarria():
    """Mini fanfarria de victoria (arpegio ascendente)."""
    notas = [523, 659, 784, 1046]  # Do-Mi-Sol-Do (mayor, triunfal)
    muestras = []
    for nota in notas:
        dur = 0.22
        n = int(MUESTREO * dur)
        for i in range(n):
            t = i / MUESTREO
            onda = math.sin(2 * math.pi * nota * t) * 0.6 + math.sin(2 * math.pi * nota * 2 * t) * 0.2
            env = min(1.0, t / 0.01) * math.exp(-t * 2)
            muestras.append(onda * env)
    # nota final sostenida
    dur = 0.6
    n = int(MUESTREO * dur)
    for i in range(n):
        t = i / MUESTREO
        onda = math.sin(2 * math.pi * 1046 * t) * 0.6 + math.sin(2 * math.pi * 1568 * t) * 0.3
        env = min(1.0, t / 0.01) * math.exp(-t * 2.5)
        muestras.append(onda * env)
    _escribir("fanfarria", muestras)


def aplausos():
    """Aplausos (ráfagas de ruido filtrado, imitando textura de aplauso)."""
    duracion = 2.2
    n = int(MUESTREO * duracion)
    muestras = [0.0] * n
    random.seed(3)
    # muchos "golpes" cortos de ruido superpuestos, aleatorios en el tiempo
    n_palmas = 260
    for _ in range(n_palmas):
        inicio = random.random() * (duracion - 0.05)
        idx0 = int(inicio * MUESTREO)
        dur_palma = 0.02 + random.random() * 0.02
        n_palma = int(MUESTREO * dur_palma)
        vol = 0.15 + random.random() * 0.25
        for j in range(n_palma):
            if idx0 + j >= n:
                break
            env = math.exp(-j / (MUESTREO * 0.008))
            muestras[idx0 + j] += (random.random() * 2 - 1) * env * vol
    # envolvente general: sube y baja (como una ovación)
    for i in range(n):
        t = i / duracion / MUESTREO
        progreso = i / n
        forma = math.sin(math.pi * progreso) ** 0.5
        muestras[i] *= forma
    _escribir("aplausos", muestras)


def main():
    print("Generando efectos de sonido en frontend/static/sfx/ ...")
    aire()
    campana()
    redoble()
    sirena()
    error()
    fanfarria()
    aplausos()
    print("Listo.")


if __name__ == "__main__":
    main()
