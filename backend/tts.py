"""Anuncios de voz natural y gratis usando edge-tts (voces neuronales de
Microsoft, las mismas del "Leer en voz alta" de Edge). Sin costo, sin API key.

Cada texto se genera una sola vez y se guarda en caché en disco
(frontend/static/tts_cache/), así que anuncios repetidos ("Mesa 4, sigues...")
no vuelven a llamar a Microsoft.
"""
import hashlib

import edge_tts

from backend.config import TTS_CACHE_DIR

VOZ_POR_DEFECTO = "es-PE-AlexNeural"  # cambiar por es-PE-CamilaNeural, es-MX-DaliaNeural, etc.
# Un toque de energía tipo animador de fiesta: más rápido y un poco más agudo
# que la voz plana por defecto, para que suene "retador" y no monótono.
RITMO_POR_DEFECTO = "+12%"
TONO_POR_DEFECTO = "+4Hz"
# edge-tts genera la voz bastante baja por defecto (se pierde contra la
# música/video). +70% es el máximo cómodo antes de que empiece a distorsionar.
VOLUMEN_POR_DEFECTO = "+70%"
CACHE_DIR = TTS_CACHE_DIR
CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def generar_audio(
    texto: str,
    voz: str = VOZ_POR_DEFECTO,
    ritmo: str = RITMO_POR_DEFECTO,
    tono: str = TONO_POR_DEFECTO,
    volumen: str = VOLUMEN_POR_DEFECTO,
) -> str:
    """Devuelve la ruta pública (/static/tts_cache/...) del MP3 con el texto leído."""
    texto = (texto or "").strip()[:300]
    if not texto:
        raise ValueError("Texto vacío")

    clave = hashlib.md5(f"{voz}:{ritmo}:{tono}:{volumen}:{texto}".encode("utf-8")).hexdigest()
    nombre_archivo = f"{clave}.mp3"
    ruta_local = CACHE_DIR / nombre_archivo

    if not ruta_local.exists():
        comunicador = edge_tts.Communicate(texto, voz, rate=ritmo, pitch=tono, volume=volumen)
        await comunicador.save(str(ruta_local))

    return f"/static/tts_cache/{nombre_archivo}"
