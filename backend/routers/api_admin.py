from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend import crud
from backend.database import get_db
from backend.library import escanear_biblioteca, registrar_cancion_subida
from backend.models import Cancion, ConfiguracionSistema, Mesa
from backend.qr import generar_qr_mesa
from backend.ws_manager import manager

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/mesas")
def listar_mesas(db: Session = Depends(get_db)):
    return [
        {
            "id": m.id,
            "numero": m.numero,
            "nombre": m.nombre,
            "activo": m.activo,
            "puntos": m.puntos,
            "qr": f"/static/qr/mesa_{m.numero}.png",
        }
        for m in crud.listar_mesas(db)
    ]


class GenerarMesasIn(BaseModel):
    cantidad: int = 10


@router.post("/mesas/generar")
def generar_mesas(payload: GenerarMesasIn, db: Session = Depends(get_db)):
    creadas = []
    for numero in range(1, payload.cantidad + 1):
        mesa = crud.get_or_create_mesa(db, numero)
        generar_qr_mesa(numero)
        creadas.append(mesa.numero)
    return {"ok": True, "mesas": creadas}


class MesaActivaIn(BaseModel):
    activo: bool


@router.post("/mesas/{numero}/activo")
def cambiar_activo_mesa(numero: int, payload: MesaActivaIn, db: Session = Depends(get_db)):
    mesa = crud.get_or_create_mesa(db, numero)
    mesa.activo = payload.activo
    db.commit()
    return {"ok": True}


@router.get("/canciones")
def listar_canciones(db: Session = Depends(get_db)):
    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "artista": c.artista,
            "genero": c.genero,
            "activo": c.activo,
            "tiene_voz_guia": c.tiene_voz_guia,
            "archivo_video": c.archivo_video,
            "archivo_lyrics": c.archivo_lyrics,
        }
        for c in db.query(Cancion).order_by(Cancion.artista, Cancion.titulo).all()
    ]


AUDIO_EXTS = {"mp3", "wav", "ogg", "m4a"}
VIDEO_EXTS = {"mp4", "webm"}
COVER_EXTS = {"jpg", "jpeg", "png"}


def _extension(nombre_archivo: str, permitidas: set[str]) -> str | None:
    if not nombre_archivo or "." not in nombre_archivo:
        return None
    ext = nombre_archivo.rsplit(".", 1)[-1].lower()
    return ext if ext in permitidas else None


@router.post("/canciones")
async def crear_cancion(
    titulo: str = Form(...),
    artista: str = Form(...),
    genero: str = Form(""),
    tiene_voz_guia: bool = Form(False),
    audio: UploadFile = File(...),
    video: UploadFile | None = File(None),
    lyrics: UploadFile | None = File(None),
    cover: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    audio_ext = _extension(audio.filename, AUDIO_EXTS)
    if not audio_ext:
        return {"ok": False, "error": "El audio debe ser .mp3, .wav, .ogg o .m4a"}
    audio_bytes = await audio.read()

    video_bytes = video_ext = None
    if video and video.filename:
        video_ext = _extension(video.filename, VIDEO_EXTS)
        if video_ext:
            video_bytes = await video.read()

    lyrics_text = None
    if lyrics and lyrics.filename:
        raw = await lyrics.read()
        lyrics_text = raw.decode("utf-8", errors="ignore")

    cover_bytes = cover_ext = None
    if cover and cover.filename:
        cover_ext = _extension(cover.filename, COVER_EXTS)
        if cover_ext:
            cover_bytes = await cover.read()

    cancion = registrar_cancion_subida(
        db,
        titulo=titulo,
        artista=artista,
        genero=genero or None,
        tiene_voz_guia=tiene_voz_guia,
        audio_bytes=audio_bytes,
        audio_ext=audio_ext,
        video_bytes=video_bytes,
        video_ext=video_ext,
        lyrics_text=lyrics_text,
        cover_bytes=cover_bytes,
        cover_ext=cover_ext,
    )
    await manager.broadcast("biblioteca_actualizada")
    return {"ok": True, "id": cancion.id}


class CancionActivaIn(BaseModel):
    activo: bool


@router.post("/canciones/{cancion_id}/activo")
async def cambiar_activo_cancion(cancion_id: int, payload: CancionActivaIn, db: Session = Depends(get_db)):
    cancion = db.query(Cancion).filter(Cancion.id == cancion_id).first()
    if not cancion:
        return {"ok": False, "error": "Canción no encontrada"}
    cancion.activo = payload.activo
    db.commit()
    await manager.broadcast("biblioteca_actualizada")
    return {"ok": True}


@router.post("/biblioteca/escanear")
async def escanear(db: Session = Depends(get_db)):
    resultado = escanear_biblioteca(db)
    await manager.broadcast("biblioteca_actualizada")
    return resultado


@router.get("/config")
def ver_config(db: Session = Depends(get_db)):
    c = crud.get_config(db)
    return {
        "nombre_evento": c.nombre_evento,
        "segundos_entre_pedidos": c.segundos_entre_pedidos,
        "max_pendientes_por_mesa": c.max_pendientes_por_mesa,
        "puntos_por_cancion": c.puntos_por_cancion,
    }


class ConfigIn(BaseModel):
    nombre_evento: str
    segundos_entre_pedidos: int
    max_pendientes_por_mesa: int
    puntos_por_cancion: int


@router.post("/config")
def actualizar_config(payload: ConfigIn, db: Session = Depends(get_db)):
    c = crud.get_config(db)
    c.nombre_evento = payload.nombre_evento
    c.segundos_entre_pedidos = payload.segundos_entre_pedidos
    c.max_pendientes_por_mesa = payload.max_pendientes_por_mesa
    c.puntos_por_cancion = payload.puntos_por_cancion
    db.commit()
    return {"ok": True}
