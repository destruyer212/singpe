"""Genera una canción de demostración (tono sintético + letra sincronizada)
para poder probar todo el flujo de SingPe sin necesitar archivos con
derechos de autor. Ejecutar con: python scripts/make_demo_song.py
"""
import json
import math
import struct
import wave
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DESTINO = BASE_DIR / "karaoke_library" / "SingPe_Demo" / "Cancion_de_Prueba"

FRASES = [
    (0.5, "Esto es una canción de prueba"),
    (4.0, "Generada para probar SingPe Karaoke"),
    (7.5, "Las letras se sincronizan con la música"),
    (11.0, "Reemplaza este archivo por tu propio catálogo"),
    (14.5, "Carpeta: karaoke_library / artista / cancion"),
    (18.0, "Gracias por usar SingPe 🎤"),
]
DURACION_TOTAL = 22


def generar_audio(ruta: Path):
    frecuencia_base = 220.0  # La3, un tono agradable y no muy agudo
    muestreo = 44100
    n_muestras = int(muestreo * DURACION_TOTAL)

    with wave.open(str(ruta), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(muestreo)

        frames = bytearray()
        for i in range(n_muestras):
            t = i / muestreo
            # Un pequeño arpegio ascendente/descendente para que no sea un pitido plano.
            paso = int(t / 2) % 4
            frecuencia = frecuencia_base * (1.0 + 0.12 * paso)
            valor = math.sin(2 * math.pi * frecuencia * t)
            envolvente = min(1.0, t, DURACION_TOTAL - t)  # fade in/out
            muestra = int(valor * envolvente * 12000)
            frames += struct.pack("<h", muestra)
        wav.writeframes(bytes(frames))


def generar_lrc(ruta: Path):
    lineas = []
    for segundos, texto in FRASES:
        minutos = int(segundos // 60)
        resto = segundos % 60
        lineas.append(f"[{minutos:02d}:{resto:05.2f}]{texto}")
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    generar_audio(DESTINO / "audio.wav")
    generar_lrc(DESTINO / "lyrics.lrc")
    (DESTINO / "meta.json").write_text(
        json.dumps(
            {
                "titulo": "Canción de Prueba",
                "artista": "SingPe Demo",
                "genero": "Demo",
                "duracion_seg": DURACION_TOTAL,
                "tiene_voz_guia": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Canción demo creada en: {DESTINO}")
    print("Ahora ve a /admin y presiona 'Escanear karaoke_library/' para registrarla.")


if __name__ == "__main__":
    main()
