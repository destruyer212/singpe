import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class ModoCancion(str, enum.Enum):
    karaoke = "karaoke"          # sin voz, 100% instrumental
    voz_guia = "voz_guia"        # con voz guía de referencia


class EstadoSolicitud(str, enum.Enum):
    pendiente = "pendiente"
    preparando = "preparando"
    cantando = "cantando"
    finalizada = "finalizada"
    cancelada = "cancelada"


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    puntos = Column(Integer, default=0)

    solicitudes = relationship("Solicitud", back_populates="mesa")


class Cancion(Base):
    __tablename__ = "canciones"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False, index=True)
    artista = Column(String, nullable=False, index=True)
    genero = Column(String, nullable=True)
    duracion_seg = Column(Integer, nullable=True)

    # Rutas relativas dentro de karaoke_library/
    carpeta = Column(String, nullable=False)
    archivo_audio = Column(String, nullable=False)
    archivo_video = Column(String, nullable=True)
    archivo_lyrics = Column(String, nullable=True)
    archivo_cover = Column(String, nullable=True)

    tiene_voz_guia = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

    solicitudes = relationship("Solicitud", back_populates="cancion")


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=False)

    # Si el cliente eligió una canción de la biblioteca (vía el buscador) queda
    # enlazada aquí y se puede reproducir automáticamente. Si el cliente
    # escribió libremente un título que no está en la biblioteca, cancion_id
    # queda en None y el DJ debe reproducirla por su cuenta (equipo externo).
    cancion_id = Column(Integer, ForeignKey("canciones.id"), nullable=True)
    cancion_titulo = Column(String, nullable=False)
    cancion_artista = Column(String, nullable=True)

    # Si el cliente la eligió del buscador de YouTube, queda el video_id
    # para reproducirlo embebido automáticamente en la pantalla TV.
    youtube_video_id = Column(String, nullable=True)
    # Otros videos de la misma búsqueda (misma canción, subida por otro canal)
    # para probar automáticamente si el principal está bloqueado para embeber.
    youtube_alternativas = Column(JSON, nullable=True)

    nombre_cantante = Column(String, nullable=True)
    # Si cantan en grupo, aquí van todos los nombres (["Ana", "Luis"]).
    # nombre_cantante sigue siendo el principal, para no romper lo que ya lo usa.
    cantantes = Column(JSON, nullable=True)
    mensaje = Column(String, nullable=True)  # se anuncia/lee al empezar la canción

    votos_fuego = Column(Integer, default=0)  # votos 🔥 del público mientras canta
    mesa_retada_numero = Column(Integer, nullable=True)  # reto: número de la otra mesa
    avisada = Column(Boolean, default=False)  # ya se le avisó por voz "sigues pronto"

    modo = Column(Enum(ModoCancion), default=ModoCancion.karaoke)
    estado = Column(Enum(EstadoSolicitud), default=EstadoSolicitud.pendiente, index=True)

    orden = Column(Integer, nullable=False, index=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    iniciado_en = Column(DateTime, nullable=True)
    finalizado_en = Column(DateTime, nullable=True)

    puntos_otorgados = Column(Integer, default=0)

    mesa = relationship("Mesa", back_populates="solicitudes")
    cancion = relationship("Cancion", back_populates="solicitudes")


class ConfiguracionSistema(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, index=True)
    nombre_evento = Column(String, default="Karaoke Night")
    segundos_entre_pedidos = Column(Integer, default=60)
    max_pendientes_por_mesa = Column(Integer, default=3)
    puntos_por_cancion = Column(Integer, default=10)
