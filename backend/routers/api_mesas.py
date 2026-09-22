from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import crud
from backend.config import YOUTUBE_API_KEY
from backend.database import get_db
from backend.schemas import CancionOut, SolicitudCreate, SolicitudOut
from backend.ws_manager import manager
from backend.youtube import buscar_karaoke, obtener_titulo_actual

router = APIRouter(prefix="/api/mesas", tags=["mesas"])


@router.get("/canciones", response_model=list[CancionOut])
def buscar_canciones(q: str | None = None, db: Session = Depends(get_db)):
    """Biblioteca propia (curada por el bar) — resultados con audio/letra ya listos."""
    return crud.buscar_canciones(db, q)


@router.get("/youtube")
def buscar_youtube(q: str, modo: str = "karaoke"):
    """Catálogo prácticamente ilimitado: busca videos karaoke en YouTube.
    modo="karaoke" busca instrumental puro; modo="voz_guia" busca con voz de referencia."""
    return {"disponible": bool(YOUTUBE_API_KEY), "resultados": buscar_karaoke(q, modo=modo)}


@router.get("/youtube/titulo")
def titulo_actual_youtube(video_id: str):
    """Título real y actual del video (corrige nombres viejos/en caché de la búsqueda)."""
    return obtener_titulo_actual(video_id) or {}


@router.get("/{numero}/cola", response_model=list[SolicitudOut])
def cola_de_mesa(numero: int, db: Session = Depends(get_db)):
    mesa = crud.get_or_create_mesa(db, numero)
    return [s for s in crud.obtener_cola(db) if s.mesa_id == mesa.id]


@router.get("/estado")
def estado_general(db: Session = Depends(get_db)):
    """Info pública liviana para el gauge de 'personas esperando' y el botón de voto 🔥."""
    actual = crud.obtener_cantando(db)
    return {
        "en_cola": len(crud.obtener_cola(db)),
        "cantando_mesa": actual.mesa.numero if actual else None,
        "cantando_votos": actual.votos_fuego if actual else 0,
    }


@router.post("/{numero}/solicitudes", response_model=SolicitudOut)
async def crear_solicitud(numero: int, payload: SolicitudCreate, db: Session = Depends(get_db)):
    mesa = crud.get_or_create_mesa(db, numero)
    if not mesa.activo:
        raise HTTPException(status_code=403, detail="Esta mesa está inactiva.")
    try:
        solicitud = crud.crear_solicitud(
            db,
            mesa,
            cancion_titulo=payload.cancion_titulo,
            cancion_artista=payload.cancion_artista,
            nombre_cantante=payload.nombre_cantante,
            modo=payload.modo,
            cancion_id=payload.cancion_id,
            youtube_video_id=payload.youtube_video_id,
            youtube_alternativas=payload.youtube_alternativas,
            cantantes=payload.cantantes,
            mensaje=payload.mensaje,
            mesa_retada_numero=payload.mesa_retada_numero,
        )
    except crud.ReglaRechazada as e:
        raise HTTPException(
            status_code=429,
            detail={"motivo": e.motivo, "segundos_restantes": e.segundos_restantes},
        )
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/{numero}/solicitudes/{solicitud_id}/editar", response_model=SolicitudOut)
async def editar_solicitud(numero: int, solicitud_id: int, payload: SolicitudCreate, db: Session = Depends(get_db)):
    """Corrige una canción propia que sigue en espera, sin perder el turno en la cola."""
    mesa = crud.get_or_create_mesa(db, numero)
    try:
        solicitud = crud.editar_solicitud_de_mesa(
            db,
            mesa.id,
            solicitud_id,
            cancion_titulo=payload.cancion_titulo,
            cancion_artista=payload.cancion_artista,
            modo=payload.modo,
            cancion_id=payload.cancion_id,
            youtube_video_id=payload.youtube_video_id,
            youtube_alternativas=payload.youtube_alternativas,
            nombre_cantante=payload.nombre_cantante,
            cantantes=payload.cantantes,
            mensaje=payload.mensaje,
            mesa_retada_numero=payload.mesa_retada_numero,
        )
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=400, detail={"motivo": e.motivo})
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/{numero}/solicitudes/{solicitud_id}/eliminar", response_model=SolicitudOut)
async def eliminar_solicitud(numero: int, solicitud_id: int, db: Session = Depends(get_db)):
    """Borra (cancela) una canción propia que sigue en espera."""
    mesa = crud.get_or_create_mesa(db, numero)
    try:
        solicitud = crud.eliminar_solicitud_de_mesa(db, mesa.id, solicitud_id)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=400, detail={"motivo": e.motivo})
    await manager.broadcast("cola_actualizada")
    return solicitud
