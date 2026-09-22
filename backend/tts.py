"""Anuncios de voz natural y gratis usando edge-tts (voces neuronales de
Microsoft, las mismas del "Leer en voz alta" de Edge). Sin costo, sin API key.

Cada texto se genera una sola vez y se guarda en caché en disco
(frontend/static/tts_cache/), así que anuncios repetidos ("Mesa 4, sigues...")
no vuelven a llamar a Microsoft.
"""
import hashlib

import edge_tts

from backend.config import STATIC_DIR

VOZ_POR_DEFECTO = "es-PE-AlexNeural"  # cambiar por es-PE-CamilaNeural, es-MX-DaliaNeural, etc.
# Un toque de energía tipo animador de fiesta: más rápido y un poco más agudo
# que la voz plana por defecto, para que suene "retador" y no monótono.
RITMO_POR_DEFECTO = "+12%"
TONO_POR_DEFECTO = "+4Hz"
CACHE_DIR = STATIC_DIR / "tts_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def generar_audio(
    texto: str,
    voz: str = VOZ_POR_DEFECTO,
    ritmo: str = RITMO_POR_DEFECTO,
    tono: str = TONO_POR_DEFECTO,
) -> str:
    """Devuelve la ruta pública (/static/tts_cache/...) del MP3 con el texto leído."""
    texto = (texto or "").strip()[:300]
    if not texto:
        raise ValueError("Texto vacío")

    clave = hashlib.md5(f"{voz}:{ritmo}:{tono}:{texto}".encode("utf-8")).hexdigest()
    nombre_archivo = f"{clave}.mp3"
    ruta_local = CACHE_DIR / nombre_archivo

    if not ruta_local.exists():
        comunicador = edge_tts.Communicate(texto, voz, rate=ritmo, pitch=tono)
        await comunicador.save(str(ruta_local))

    return f"/static/tts_cache/{nombre_archivo}"
