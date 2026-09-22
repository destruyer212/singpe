"""Descarga y recorta los efectos de sonido reales del soundboard del DJ
(frontend/static/sfx/). Requiere ffmpeg instalado y en el PATH.

Fuente: freesoundslibrary.com, licencia CC BY 4.0 (uso libre, con atribución
— ver frontend/static/sfx/CREDITOS.txt).

Ejecutar: python scripts/make_efectos.py
"""
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DESTINO = BASE_DIR / "frontend" / "static" / "sfx"

# nombre_final: (url_del_zip, duracion_segundos, segundo_donde_empieza_el_fade)
EFECTOS = {
    "aire": ("https://www.freesoundslibrary.com/wp-content/uploads/2025/06/mlg-airhorn-sound-effect.zip", 3.8, 3.4),
    "aplausos": ("https://www.freesoundslibrary.com/wp-content/uploads/2023/06/clapping-and-whistling-sound-effect.zip", 4.0, 3.5),
    "campana": ("https://www.freesoundslibrary.com/wp-content/uploads/2021/06/ding-ding-sound-effect.zip", 3.0, 2.6),
    "error": ("https://www.freesoundslibrary.com/wp-content/uploads/2026/02/fail-buzzer-sound-effect.zip", 3.0, 2.6),
    "fanfarria": ("https://www.freesoundslibrary.com/wp-content/uploads/2019/12/reveille-sound-effect.zip", 5.5, 5.0),
    "redoble": ("https://www.freesoundslibrary.com/wp-content/uploads/2020/03/drum-roll-sound-effect.zip", None, 5.7),
    "sirena": ("https://www.freesoundslibrary.com/wp-content/uploads/2026/08/tornado-siren-sound-effect.zip", 4.5, 4.0),
}


def procesar(nombre: str, url: str, duracion: float | None, fade_desde: float):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "s.zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        mp3 = next(tmp.glob("*.mp3"))

        DESTINO.mkdir(parents=True, exist_ok=True)
        salida = DESTINO / f"{nombre}.wav"
        cmd = ["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100"]
        if duracion:
            cmd += ["-t", str(duracion)]
        cmd += ["-af", f"afade=t=out:st={fade_desde}:d=0.5", str(salida)]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  {nombre}.wav")


def main():
    print("Descargando y recortando efectos reales en frontend/static/sfx/ ...")
    for nombre, (url, duracion, fade_desde) in EFECTOS.items():
        procesar(nombre, url, duracion, fade_desde)
    print("Listo.")


if __name__ == "__main__":
    main()
