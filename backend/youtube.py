"""Búsqueda de videos karaoke en YouTube (catálogo de millones de canciones,
en vez de depender de una biblioteca propia y limitada).

Requiere una YOUTUBE_API_KEY (ver app/config.py). Sin la clave, la búsqueda
simplemente devuelve una lista vacía y el cliente puede seguir escribiendo
el nombre de la canción a mano.
"""
import json
import urllib.parse
import urllib.request
from datetime import date

from backend.config import BASE_DIR, YOUTUBE_API_KEY

BUSQUEDA_URL = "https://www.googleapis.com/youtube/v3/search"

# Cuota gratuita de YouTube Data API: 10,000 unidades/día.
# Cada búsqueda (search.list) cuesta 100 unidades -> ~100 búsquedas/día gratis.
COSTO_POR_BUSQUEDA = 100
LIMITE_DIARIO_ESTIMADO = 100  # búsquedas, no unidades
ARCHIVO_USO = BASE_DIR / "youtube_uso.json"


def _leer_uso() -> dict:
    if ARCHIVO_USO.exists():
        try:
            return json.loads(ARCHIVO_USO.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return {"fecha": "", "busquedas": 0}


def _registrar_busqueda() -> None:
    hoy = date.today().isoformat()
    uso = _leer_uso()
    if uso.get("fecha") != hoy:
        uso = {"fecha": hoy, "busquedas": 0}
    uso["busquedas"] += 1
    try:
        ARCHIVO_USO.write_text(json.dumps(uso), encoding="utf-8")
    except OSError:
        pass  # si no se puede escribir, simplemente no se cuenta esta vez


def obtener_uso_hoy() -> dict:
    hoy = date.today().isoformat()
    uso = _leer_uso()
    busquedas = uso["busquedas"] if uso.get("fecha") == hoy else 0
    return {
        "busquedas": busquedas,
        "limite_estimado": LIMITE_DIARIO_ESTIMADO,
        "fecha": hoy,
    }


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
    _registrar_busqueda()

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
