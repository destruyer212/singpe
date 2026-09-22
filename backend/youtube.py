"""Búsqueda de videos karaoke en YouTube (catálogo de millones de canciones,
en vez de depender de una biblioteca propia y limitada).

Requiere una YOUTUBE_API_KEY (ver app/config.py). Sin la clave, la búsqueda
simplemente devuelve una lista vacía y el cliente puede seguir escribiendo
el nombre de la canción a mano.
"""
import json
import urllib.parse
import urllib.request

from backend.config import YOUTUBE_API_KEY

BUSQUEDA_URL = "https://www.googleapis.com/youtube/v3/search"


def buscar_karaoke(q: str, limite: int = 8, modo: str = "karaoke") -> list[dict]:
    q = (q or "").strip()
    if not YOUTUBE_API_KEY or not q:
        return []

    # "karaoke" (sin voz) busca la pista instrumental pura; "voz_guia" (con
    # letra) busca la canción normal/original, con la voz del cantante.
    if modo == "voz_guia":
        consulta = q
    else:
        consulta = f"{q} karaoke sin voz instrumental"

    params = {
        "part": "snippet",
        "q": consulta,
        "type": "video",
        "videoEmbeddable": "true",
        "maxResults": str(limite),
        "safeSearch": "moderate",
        "key": YOUTUBE_API_KEY,
    }
    url = f"{BUSQUEDA_URL}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    resultados = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        miniaturas = snippet.get("thumbnails", {})
        miniatura = (
            miniaturas.get("medium", {}).get("url")
            or miniaturas.get("default", {}).get("url")
        )
        resultados.append(
            {
                "video_id": video_id,
                "titulo": snippet.get("title", ""),
                "canal": snippet.get("channelTitle", ""),
                "miniatura": miniatura,
            }
        )
    return resultados


def obtener_titulo_actual(video_id: str) -> dict | None:
    """A veces la búsqueda de YouTube devuelve un título viejo/en caché que ya
    no coincide con el video real. Esto consulta el título ACTUAL vía oEmbed
    (endpoint público de YouTube, sin necesitar la API key) justo cuando el
    cliente elige un resultado, para no guardar un nombre desactualizado."""
    video_id = (video_id or "").strip()
    if not video_id:
        return None
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return {"titulo": data.get("title", ""), "canal": data.get("author_name", "")}
