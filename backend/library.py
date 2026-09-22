"""Escaneo de la biblioteca de canciones en disco (karaoke_library/).

Estructura esperada por canción:

    karaoke_library/<artista>/<titulo>/
        audio.mp3 | audio.wav      (obligatorio, instrumental)
        video.mp4                  (opcional, video de fondo)
        lyrics.lrc                 (opcional, letra sincronizada)
        cover.jpg | cover.png      (opcional, portada)
        meta.json                  (opcional: {"genero": "...", "tiene_voz_guia": true})
"""
import json
import re

from sqlalchemy.orm import Session

from backend.config import LIBRARY_DIR
from backend.models import Cancion

AUDIO_NOMBRES = ("audio.mp3", "audio.wav", "audio.ogg", "audio.m4a")
VIDEO_NOMBRES = ("video.mp4", "video.webm")
LYRICS_NOMBRES = ("lyrics.lrc",)
COVER_NOMBRES = ("cover.jpg", "cover.png", "cover.jpeg")


def _buscar(carpeta, nombres) -> str | None:
    for nombre in nombres:
        if (carpeta / nombre).exists():
            return nombre
    return None


def escanear_biblioteca(db: Session) -> dict:
    """Recorre karaoke_library/, registra canciones nuevas y desactiva
    en la base de datos las que ya no tienen carpeta en disco."""
    encontradas: set[str] = set()
    nuevas = 0
    actualizadas = 0

    if not LIBRARY_DIR.exists():
        return {"nuevas": 0, "actualizadas": 0, "desactivadas": 0}

    for carpeta_artista in sorted(p for p in LIBRARY_DIR.iterdir() if p.is_dir()):
        for carpeta_cancion in sorted(p for p in carpeta_artista.iterdir() if p.is_dir()):
            audio = _buscar(carpeta_cancion, AUDIO_NOMBRES)
            if not audio:
                continue  # sin audio no es una canción válida

            ruta_relativa = f"{carpeta_artista.name}/{carpeta_cancion.name}"
            encontradas.add(ruta_relativa)

            meta = {}
            meta_path = carpeta_cancion / "meta.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    meta = {}

            video = _buscar(carpeta_cancion, VIDEO_NOMBRES)
            lyrics = _buscar(carpeta_cancion, LYRICS_NOMBRES)
            cover = _buscar(carpeta_cancion, COVER_NOMBRES)

            cancion = db.query(Cancion).filter(Cancion.carpeta == ruta_relativa).first()
            if not cancion:
                cancion = Cancion(carpeta=ruta_relativa)
                db.add(cancion)
                nuevas += 1
            else:
                actualizadas += 1

            cancion.titulo = meta.get("titulo", carpeta_cancion.name.replace("_", " ").title())
            cancion.artista = meta.get("artista", carpeta_artista.name.replace("_", " ").title())
            cancion.genero = meta.get("genero")
            cancion.duracion_seg = meta.get("duracion_seg")
            cancion.tiene_voz_guia = bool(meta.get("tiene_voz_guia", False))
            cancion.archivo_audio = audio
            cancion.archivo_video = video
            cancion.archivo_lyrics = lyrics
            cancion.archivo_cover = cover
            cancion.activo = True

    desactivadas = 0
    for cancion in db.query(Cancion).filter(Cancion.activo.is_(True)).all():
        if cancion.carpeta not in encontradas:
            cancion.activo = False
            desactivadas += 1

    db.commit()
    return {"nuevas": nuevas, "actualizadas": actualizadas, "desactivadas": desactivadas}


def slugify(texto: str) -> str:
    """Convierte un título/artista en un nombre de carpeta seguro."""
    texto = texto.strip()
    texto = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", "_", texto)
    return texto[:80] or "sin_nombre"


def registrar_cancion_subida(
    db: Session,
    titulo: str,
    artista: str,
    genero: str | None,
    tiene_voz_guia: bool,
    audio_bytes: bytes,
    audio_ext: str,
    video_bytes: bytes | None = None,
    video_ext: str | None = None,
    lyrics_text: str | None = None,
    cover_bytes: bytes | None = None,
    cover_ext: str | None = None,
) -> Cancion:
    """Guarda los archivos subidos desde /admin en karaoke_library/ y
    crea (o actualiza) la canción directamente en la base de datos."""
    carpeta_artista = slugify(artista)
    carpeta_cancion = slugify(titulo)
    ruta_relativa = f"{carpeta_artista}/{carpeta_cancion}"
    carpeta_abs = LIBRARY_DIR / carpeta_artista / carpeta_cancion
    carpeta_abs.mkdir(parents=True, exist_ok=True)

    archivo_audio = f"audio.{audio_ext.lower()}"
    (carpeta_abs / archivo_audio).write_bytes(audio_bytes)

    archivo_video = None
    if video_bytes:
        archivo_video = f"video.{video_ext.lower()}"
        (carpeta_abs / archivo_video).write_bytes(video_bytes)

    archivo_lyrics = None
    if lyrics_text:
        archivo_lyrics = "lyrics.lrc"
        (carpeta_abs / archivo_lyrics).write_text(lyrics_text, encoding="utf-8")

    archivo_cover = None
    if cover_bytes:
        archivo_cover = f"cover.{cover_ext.lower()}"
        (carpeta_abs / archivo_cover).write_bytes(cover_bytes)

    meta = {"titulo": titulo, "artista": artista, "genero": genero, "tiene_voz_guia": tiene_voz_guia}
    (carpeta_abs / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    cancion = db.query(Cancion).filter(Cancion.carpeta == ruta_relativa).first()
    if not cancion:
        cancion = Cancion(carpeta=ruta_relativa)
        db.add(cancion)

    cancion.titulo = titulo
    cancion.artista = artista
    cancion.genero = genero
    cancion.tiene_voz_guia = tiene_voz_guia
    cancion.archivo_audio = archivo_audio
    cancion.archivo_video = archivo_video
    cancion.archivo_lyrics = archivo_lyrics
    cancion.archivo_cover = archivo_cover
    cancion.activo = True

    db.commit()
    db.refresh(cancion)
    return cancion
