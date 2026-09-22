from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.models import EstadoSolicitud, ModoCancion


# ---------- Cancion ----------
class CancionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    artista: str
    genero: Optional[str] = None
    duracion_seg: Optional[int] = None
    carpeta: str
    archivo_audio: str
    archivo_video: Optional[str] = None
    archivo_lyrics: Optional[str] = None
    archivo_cover: Optional[str] = None
    tiene_voz_guia: bool


# ---------- Mesa ----------
class MesaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    nombre: Optional[str] = None
    activo: bool
    puntos: int


# ---------- Solicitud ----------
class SolicitudCreate(BaseModel):
    cancion_titulo: str
    cancion_artista: Optional[str] = None
    cancion_id: Optional[int] = None  # se envía solo si el cliente eligió de la biblioteca propia
    youtube_video_id: Optional[str] = None  # se envía si el cliente eligió de la búsqueda de YouTube
    youtube_alternativas: Optional[list[str]] = None  # otras versiones del mismo tema, por si la principal está bloqueada
    nombre_cantante: Optional[str] = ""
    cantantes: Optional[list[str]] = None  # si cantan en grupo, todos los nombres
    mensaje: Optional[str] = None
    mesa_retada_numero: Optional[int] = None  # reto a otra mesa
    modo: ModoCancion = ModoCancion.karaoke


class SolicitudOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mesa_id: int
    cancion_id: Optional[int] = None
    cancion_titulo: str
    cancion_artista: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_alternativas: Optional[list[str]] = None
    nombre_cantante: Optional[str] = None
    cantantes: Optional[list[str]] = None
    mensaje: Optional[str] = None
    votos_fuego: int = 0
    mesa_retada_numero: Optional[int] = None
    avisada: bool = False
    modo: ModoCancion
    estado: EstadoSolicitud
    orden: int
    creado_en: datetime
    puntos_otorgados: int

    mesa: MesaOut
    cancion: Optional[CancionOut] = None


class SolicitudRechazada(BaseModel):
    ok: bool = False
    motivo: str
    segundos_restantes: Optional[int] = None
