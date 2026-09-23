"""Búsqueda de videos karaoke en YouTube (catálogo de millones de canciones,
en vez de depender de una biblioteca propia y limitada).

Requiere una YOUTUBE_API_KEY (ver app/config.py). Sin la clave, la búsqueda
simplemente devuelve una lista vacía y el cliente puede seguir escribiendo
el nombre de la canción a mano.
"""
import json
import re
import urllib.parse
import urllib.request
from html import unescape
from datetime import date

from backend.config import BASE_DIR, YOUTUBE_API_KEY

BUSQUEDA_URL = "https://www.googleapis.com/youtube/v3/search"
BUSQUEDA_WEB_URL = "https://www.youtube.com/results"

# ---------- Videos/canales bloqueados (clickbait: metadata falsa) ----------
# Algunos canales le ponen a sus videos el título de una canción de moda
# ("Myke Towers - Lala") pero el video real es otra cosa completamente
# distinta (ej. un capítulo de "31 minutos"). Ni la búsqueda ni el título
# oficial (oEmbed) delatan esto porque el propio canal mintió en el dato.
# Por eso se guarda una lista de reportes: video_id o nombre de canal que ya
# se comprobó que engaña, para que no vuelvan a aparecer en resultados.
ARCHIVO_BLOQUEADOS = BASE_DIR / "youtube_bloqueados.json"
VIDEOS_BLOQUEADOS_INICIAL = {"vXvRENPpjSI"}  # "Myke Towers - Lala" que en realidad es "31 minutos"
CANALES_BLOQUEADOS_INICIAL = {"karaoke live"}  # canal detectado subiendo videos con título falso


def _cargar_bloqueados() -> dict:
    if ARCHIVO_BLOQUEADOS.exists():
        try:
            datos = json.loads(ARCHIVO_BLOQUEADOS.read_text(encoding="utf-8"))
            return {
                "videos": set(datos.get("videos", [])) | VIDEOS_BLOQUEADOS_INICIAL,
                "canales": set(c.lower() for c in datos.get("canales", [])) | CANALES_BLOQUEADOS_INICIAL,
            }
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return {"videos": set(VIDEOS_BLOQUEADOS_INICIAL), "canales": set(CANALES_BLOQUEADOS_INICIAL)}


def reportar_video_falso(video_id: str, canal: str | None = None) -> None:
    """Un cliente o el DJ reporta que este resultado no era lo que decía ser.
    Queda bloqueado para siempre (video_id, y el canal si lo mandan)."""
    video_id = (video_id or "").strip()
    if not video_id:
        return
    datos = _cargar_bloqueados()
    datos["videos"].add(video_id)
    if canal:
        datos["canales"].add(canal.strip().lower())
    try:
        ARCHIVO_BLOQUEADOS.write_text(
            json.dumps({"videos": sorted(datos["videos"]), "canales": sorted(datos["canales"])}),
            encoding="utf-8",
        )
    except OSError:
        pass


def _filtrar_bloqueados(resultados: list[dict]) -> list[dict]:
    bloqueados = _cargar_bloqueados()
    return [
        r
        for r in resultados
        if r["video_id"] not in bloqueados["videos"] and (r.get("canal") or "").strip().lower() not in bloqueados["canales"]
    ]

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


def _consulta_youtube(q: str, modo: str) -> str:
    # "karaoke" (sin voz) busca la pista instrumental pura; "voz_guia" (con
    # letra) busca la canción normal/original, con la voz del cantante.
    if modo == "voz_guia":
        return q
    return f"{q} karaoke"


def _normalizar_resultados(items: list[dict]) -> list[dict]:
    resultados = []
    vistos = set()
    for item in items:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id or video_id in vistos:
            continue
        vistos.add(video_id)
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


def _buscar_con_api(consulta: str, limite: int) -> list[dict]:
    if not YOUTUBE_API_KEY:
        return []

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
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    return _normalizar_resultados(data.get("items", []))


def _buscar_en_web(consulta: str, limite: int) -> list[dict]:
    params = {"search_query": consulta}
    url = f"{BUSQUEDA_WEB_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    resultados = []
    vistos = set()
    for video_id in re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html):
        if video_id in vistos:
            continue
        vistos.add(video_id)
        pos = html.find(f'"videoId":"{video_id}"')
        tramo = html[pos : pos + 3500]
        titulo = ""
        canal = ""
        title_match = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"', tramo)
        if not title_match:
            title_match = re.search(r'"title":\{"simpleText":"(.*?)"', tramo)
        owner_match = re.search(r'"ownerText":\{"runs":\[\{"text":"(.*?)"', tramo)
        if title_match:
            titulo = unescape(title_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore"))
        if owner_match:
            canal = unescape(owner_match.group(1).encode("utf-8").decode("unicode_escape", errors="ignore"))
        if not titulo:
            continue
        resultados.append(
            {
                "video_id": video_id,
                "titulo": titulo,
                "canal": canal,
                "miniatura": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
            }
        )
        if len(resultados) >= limite:
            break
    return resultados


def buscar_karaoke(q: str, limite: int = 8, modo: str = "karaoke") -> list[dict]:
    q = (q or "").strip()
    if not q:
        return []

    consulta = _consulta_youtube(q, modo)
    variantes = [consulta]
    if modo != "voz_guia":
        variantes.extend([f"{q} karaoke instrumental", f"{q} karaoke sin voz"])

    for variante in variantes:
        resultados = _filtrar_bloqueados(_buscar_con_api(variante, limite))
        if resultados:
            return resultados

    for variante in variantes:
        resultados = _filtrar_bloqueados(_buscar_en_web(variante, limite))
        if resultados:
            return resultados

    return []


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
