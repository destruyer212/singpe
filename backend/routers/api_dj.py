from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import crud
from backend.database import get_db
from backend.schemas import SolicitudOut
from backend.tts import generar_audio
from backend.ws_manager import manager

router = APIRouter(prefix="/api/dj", tags=["dj"])

SONIDOS_VALIDOS = {"aire", "campana", "redoble", "sirena", "error", "fanfarria", "aplausos"}


class EfectoIn(BaseModel):
    sonido: str
    sticker: str | None = None
    texto: str | None = None


@router.post("/efecto")
async def disparar_efecto(payload: EfectoIn):
    """El DJ dispara un efecto de sonido + sticker que aparece un momento en la pantalla TV."""
    if payload.sonido not in SONIDOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Sonido no válido")
    await manager.broadcast(
        "efecto",
        {"sonido": payload.sonido, "sticker": payload.sticker, "texto": (payload.texto or "")[:60]},
    )
    return {"ok": True}


class AnuncioIn(BaseModel):
    texto: str


@router.post("/anuncio")
async def anuncio_rapido(payload: AnuncioIn):
    """Anuncio de texto+voz instantáneo del DJ, sin pasar por una solicitud."""
    texto = (payload.texto or "").strip()[:120]
    if not texto:
        raise HTTPException(status_code=400, detail="Texto vacío")
    await manager.broadcast("anuncio", {"texto": texto})
    return {"ok": True}


@router.get("/tts")
async def texto_a_voz(texto: str, voz: str | None = None):
    """Genera (o reutiliza del caché) un anuncio en voz natural para la pantalla TV."""
    try:
        url = await generar_audio(texto, voz) if voz else await generar_audio(texto)
    except ValueError:
        raise HTTPException(status_code=400, detail="Texto vacío")
    except Exception:
        raise HTTPException(status_code=502, detail="No se pudo generar el audio de voz")
    return {"url": url}


@router.get("/cola", response_model=list[SolicitudOut])
def ver_cola(db: Session = Depends(get_db)):
    return crud.obtener_cola(db)


@router.get("/actual", response_model=SolicitudOut | None)
def ver_actual(db: Session = Depends(get_db)):
    return crud.obtener_cantando(db)


@router.get("/historial", response_model=list[SolicitudOut])
def ver_historial(db: Session = Depends(get_db)):
    return crud.historial(db)


@router.get("/ranking")
def ver_ranking(db: Session = Depends(get_db)):
    """Ranking de la noche: mesas con más canciones cantadas y más votos 🔥."""
    return crud.ranking_de_la_noche(db)


@router.post("/solicitudes/{solicitud_id}/iniciar", response_model=SolicitudOut)
async def iniciar(solicitud_id: int, db: Session = Depends(get_db)):
    try:
        solicitud = crud.iniciar_solicitud(db, solicitud_id)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=404, detail=e.motivo)
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/solicitudes/{solicitud_id}/finalizar", response_model=SolicitudOut)
async def finalizar(solicitud_id: int, db: Session = Depends(get_db)):
    try:
        solicitud = crud.finalizar_solicitud(db, solicitud_id)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=404, detail=e.motivo)
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/solicitudes/{solicitud_id}/cancelar", response_model=SolicitudOut)
async def cancelar(solicitud_id: int, db: Session = Depends(get_db)):
    try:
        solicitud = crud.cancelar_solicitud(db, solicitud_id)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=404, detail=e.motivo)
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/solicitudes/{solicitud_id}/avisar", response_model=SolicitudOut)
async def avisar(solicitud_id: int, db: Session = Depends(get_db)):
    """Marca que ya se le avisó por voz a la mesa 'sigues pronto' (no repetir)."""
    try:
        solicitud = crud.marcar_avisada(db, solicitud_id)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=404, detail=e.motivo)
    return solicitud


@router.post("/actual/votar", response_model=SolicitudOut)
async def votar_actual(db: Session = Depends(get_db)):
    """El público vota 🔥 por quien está cantando ahora (desde cualquier mesa)."""
    try:
        solicitud = crud.votar_actual(db)
    except crud.ReglaRechazada as e:
        raise HTTPException(status_code=400, detail=e.motivo)
    await manager.broadcast("cola_actualizada")
    return solicitud


@router.post("/solicitudes/{solicitud_id}/mover")
async def mover(solicitud_id: int, direccion: str = Query(pattern="^(arriba|abajo)$"), db: Session = Depends(get_db)):
    crud.mover_solicitud(db, solicitud_id, direccion)
    await manager.broadcast("cola_actualizada")
    return {"ok": True}
