from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.models import (
    CanalBloqueado,
    Cancion,
    ConfiguracionSistema,
    EstadoSolicitud,
    Mesa,
    Solicitud,
    VideoBloqueado,
)

ESTADOS_ACTIVOS = (
    EstadoSolicitud.pendiente,
    EstadoSolicitud.preparando,
    EstadoSolicitud.cantando,
)


class ReglaRechazada(Exception):
    """Se lanza cuando una solicitud viola una regla de negocio (anti-spam, etc.)."""

    def __init__(self, motivo: str, segundos_restantes: int | None = None):
        self.motivo = motivo
        self.segundos_restantes = segundos_restantes
        super().__init__(motivo)


# ---------- Configuración ----------
def get_config(db: Session) -> ConfiguracionSistema:
    config = db.query(ConfiguracionSistema).first()
    if not config:
        config = ConfiguracionSistema()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# ---------- Mesas ----------
def get_or_create_mesa(db: Session, numero: int) -> Mesa:
    mesa = db.query(Mesa).filter(Mesa.numero == numero).first()
    if not mesa:
        mesa = Mesa(numero=numero, nombre=f"Mesa {numero}")
        db.add(mesa)
        db.commit()
        db.refresh(mesa)
    return mesa


def listar_mesas(db: Session) -> list[Mesa]:
    return db.query(Mesa).order_by(Mesa.numero).all()


# ---------- Canciones ----------
def buscar_canciones(db: Session, q: str | None, limit: int = 30) -> list[Cancion]:
    query = db.query(Cancion).filter(Cancion.activo.is_(True))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Cancion.titulo.ilike(like), Cancion.artista.ilike(like)))
    return query.order_by(Cancion.artista, Cancion.titulo).limit(limit).all()


def listar_canciones(db: Session) -> list[Cancion]:
    return db.query(Cancion).order_by(Cancion.artista, Cancion.titulo).all()


# ---------- Cola / Solicitudes ----------
def obtener_cola(db: Session) -> list[Solicitud]:
    return (
        db.query(Solicitud)
        .filter(Solicitud.estado.in_(ESTADOS_ACTIVOS))
        .order_by(Solicitud.orden)
        .all()
    )


def obtener_cantando(db: Session) -> Solicitud | None:
    return (
        db.query(Solicitud)
        .filter(Solicitud.estado == EstadoSolicitud.cantando)
        .order_by(Solicitud.orden)
        .first()
    )


def historial(db: Session, limit: int = 50) -> list[Solicitud]:
    return (
        db.query(Solicitud)
        .filter(Solicitud.estado.in_((EstadoSolicitud.finalizada, EstadoSolicitud.cancelada)))
        .order_by(Solicitud.creado_en.desc())
        .limit(limit)
        .all()
    )


def _normalizar_cantantes(cantantes: list[str] | None) -> list[str] | None:
    limpios = [c.strip()[:40] for c in (cantantes or []) if c and c.strip()]
    return limpios[:6] or None


def crear_solicitud(
    db: Session,
    mesa: Mesa,
    cancion_titulo: str,
    cancion_artista: str | None,
    nombre_cantante: str,
    modo,
    cancion_id: int | None = None,
    youtube_video_id: str | None = None,
    youtube_alternativas: list[str] | None = None,
    cantantes: list[str] | None = None,
    mensaje: str | None = None,
    mesa_retada_numero: int | None = None,
) -> Solicitud:
    config = get_config(db)

    cancion_titulo = (cancion_titulo or "").strip()[:120]
    if not cancion_titulo:
        raise ReglaRechazada("Escribe el nombre de la canción.")

    cancion = None
    if cancion_id is not None:
        cancion = db.query(Cancion).filter(Cancion.id == cancion_id, Cancion.activo.is_(True)).first()
        if not cancion:
            raise ReglaRechazada("La canción seleccionada ya no está disponible.")
        # Si viene enlazada a la biblioteca, el título/artista canónico manda.
        cancion_titulo = cancion.titulo
        cancion_artista = cancion.artista

    # Regla 1: tiempo mínimo entre pedidos de la misma mesa.
    ultima = (
        db.query(Solicitud)
        .filter(Solicitud.mesa_id == mesa.id, Solicitud.estado != EstadoSolicitud.cancelada)
        .order_by(Solicitud.creado_en.desc())
        .first()
    )
    if ultima:
        transcurrido = datetime.utcnow() - ultima.creado_en
        espera = timedelta(seconds=config.segundos_entre_pedidos)
        if transcurrido < espera:
            restante = int((espera - transcurrido).total_seconds()) + 1
            raise ReglaRechazada(
                f"Debes esperar {restante} segundos antes de pedir otra canción.",
                segundos_restantes=restante,
            )

    # Regla 2: máximo de canciones pendientes simultáneas por mesa.
    pendientes = (
        db.query(Solicitud)
        .filter(Solicitud.mesa_id == mesa.id, Solicitud.estado.in_(ESTADOS_ACTIVOS))
        .count()
    )
    if pendientes >= config.max_pendientes_por_mesa:
        raise ReglaRechazada(
            f"Ya tienes {pendientes} canciones en cola. Espera a que se canten antes de pedir más."
        )

    ultimo_orden = db.query(Solicitud).filter(Solicitud.estado.in_(ESTADOS_ACTIVOS)).count()
    max_orden_row = (
        db.query(Solicitud)
        .filter(Solicitud.estado.in_(ESTADOS_ACTIVOS))
        .order_by(Solicitud.orden.desc())
        .first()
    )
    siguiente_orden = (max_orden_row.orden + 1) if max_orden_row else 1

    solicitud = Solicitud(
        mesa_id=mesa.id,
        cancion_id=cancion.id if cancion else None,
        cancion_titulo=cancion_titulo,
        cancion_artista=(cancion_artista or "").strip()[:80] or None,
        youtube_video_id=(youtube_video_id or "").strip()[:20] or None,
        youtube_alternativas=[v.strip()[:20] for v in (youtube_alternativas or []) if v and v.strip()][:6] or None,
        nombre_cantante=(nombre_cantante or "").strip()[:60] or f"Mesa {mesa.numero}",
        cantantes=_normalizar_cantantes(cantantes),
        mensaje=(mensaje or "").strip()[:80] or None,
        mesa_retada_numero=mesa_retada_numero if mesa_retada_numero and mesa_retada_numero != mesa.numero else None,
        modo=modo,
        estado=EstadoSolicitud.pendiente,
        orden=siguiente_orden,
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud


def iniciar_solicitud(db: Session, solicitud_id: int) -> Solicitud:
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise ReglaRechazada("Solicitud no encontrada.")

    # Si ya hay una canción sonando, se finaliza automáticamente antes de iniciar la nueva.
    actual = obtener_cantando(db)
    if actual and actual.id != solicitud.id:
        _finalizar(db, actual)

    solicitud.estado = EstadoSolicitud.cantando
    solicitud.iniciado_en = datetime.utcnow()
    db.commit()
    db.refresh(solicitud)
    return solicitud


def votar_actual(db: Session) -> Solicitud:
    """Suma un voto 🔥 del público a quien está cantando ahora mismo."""
    actual = obtener_cantando(db)
    if not actual:
        raise ReglaRechazada("No hay nadie cantando ahora mismo.")
    actual.votos_fuego = (actual.votos_fuego or 0) + 1
    db.commit()
    db.refresh(actual)
    return actual


def marcar_avisada(db: Session, solicitud_id: int) -> Solicitud:
    """La pantalla TV ya anunció por voz 'sigues pronto' — no repetir el aviso."""
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise ReglaRechazada("Solicitud no encontrada.")
    solicitud.avisada = True
    db.commit()
    db.refresh(solicitud)
    return solicitud


def _finalizar(db: Session, solicitud: Solicitud) -> None:
    config = get_config(db)
    solicitud.estado = EstadoSolicitud.finalizada
    solicitud.finalizado_en = datetime.utcnow()
    solicitud.puntos_otorgados = config.puntos_por_cancion
    mesa = solicitud.mesa
    mesa.puntos = (mesa.puntos or 0) + config.puntos_por_cancion
    db.commit()


def finalizar_solicitud(db: Session, solicitud_id: int) -> Solicitud:
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise ReglaRechazada("Solicitud no encontrada.")
    _finalizar(db, solicitud)
    db.refresh(solicitud)
    return solicitud


def cancelar_solicitud(db: Session, solicitud_id: int) -> Solicitud:
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise ReglaRechazada("Solicitud no encontrada.")
    solicitud.estado = EstadoSolicitud.cancelada
    db.commit()
    db.refresh(solicitud)
    return solicitud


# ---------- Auto-gestión de la mesa sobre su propio pedido ----------
# Mientras una solicitud siga "pendiente" (todavía no empezó a prepararse),
# la mesa que la pidió puede corregirla o borrarla sin perder su lugar en la
# cola (no se toca `orden` ni `creado_en`, así que tampoco reinicia el
# contador anti-spam de 60s).
def _obtener_solicitud_editable_de_mesa(db: Session, mesa_id: int, solicitud_id: int) -> Solicitud:
    solicitud = (
        db.query(Solicitud)
        .filter(Solicitud.id == solicitud_id, Solicitud.mesa_id == mesa_id)
        .first()
    )
    if not solicitud:
        raise ReglaRechazada("Solicitud no encontrada.")
    if solicitud.estado != EstadoSolicitud.pendiente:
        raise ReglaRechazada("Ya no se puede modificar: esta canción ya está en preparación o sonando.")
    return solicitud


def eliminar_solicitud_de_mesa(db: Session, mesa_id: int, solicitud_id: int) -> Solicitud:
    solicitud = _obtener_solicitud_editable_de_mesa(db, mesa_id, solicitud_id)
    solicitud.estado = EstadoSolicitud.cancelada
    db.commit()
    db.refresh(solicitud)
    return solicitud


def editar_solicitud_de_mesa(
    db: Session,
    mesa_id: int,
    solicitud_id: int,
    cancion_titulo: str,
    cancion_artista: str | None,
    modo,
    cancion_id: int | None = None,
    youtube_video_id: str | None = None,
    youtube_alternativas: list[str] | None = None,
    nombre_cantante: str | None = None,
    cantantes: list[str] | None = None,
    mensaje: str | None = None,
    mesa_retada_numero: int | None = None,
) -> Solicitud:
    solicitud = _obtener_solicitud_editable_de_mesa(db, mesa_id, solicitud_id)

    cancion_titulo = (cancion_titulo or "").strip()[:120]
    if not cancion_titulo:
        raise ReglaRechazada("Escribe el nombre de la canción.")

    cancion = None
    if cancion_id is not None:
        cancion = db.query(Cancion).filter(Cancion.id == cancion_id, Cancion.activo.is_(True)).first()
        if not cancion:
            raise ReglaRechazada("La canción seleccionada ya no está disponible.")
        cancion_titulo = cancion.titulo
        cancion_artista = cancion.artista

    solicitud.cancion_id = cancion.id if cancion else None
    solicitud.cancion_titulo = cancion_titulo
    solicitud.cancion_artista = (cancion_artista or "").strip()[:80] or None
    solicitud.youtube_video_id = (youtube_video_id or "").strip()[:20] or None
    solicitud.youtube_alternativas = (
        [v.strip()[:20] for v in (youtube_alternativas or []) if v and v.strip()][:6] or None
    )
    if nombre_cantante:
        solicitud.nombre_cantante = nombre_cantante.strip()[:60] or solicitud.nombre_cantante
    solicitud.cantantes = _normalizar_cantantes(cantantes)
    solicitud.mensaje = (mensaje or "").strip()[:80] or None
    numero_mesa = solicitud.mesa.numero
    solicitud.mesa_retada_numero = (
        mesa_retada_numero if mesa_retada_numero and mesa_retada_numero != numero_mesa else None
    )
    solicitud.modo = modo
    # orden y creado_en no se tocan a propósito.
    db.commit()
    db.refresh(solicitud)
    return solicitud


def mover_solicitud(db: Session, solicitud_id: int, direccion: str) -> None:
    """Reordena la cola moviendo una solicitud 'arriba' o 'abajo' entre las pendientes."""
    cola = (
        db.query(Solicitud)
        .filter(Solicitud.estado == EstadoSolicitud.pendiente)
        .order_by(Solicitud.orden)
        .all()
    )
    idx = next((i for i, s in enumerate(cola) if s.id == solicitud_id), None)
    if idx is None:
        return
    vecino = idx - 1 if direccion == "arriba" else idx + 1
    if vecino < 0 or vecino >= len(cola):
        return
    cola[idx].orden, cola[vecino].orden = cola[vecino].orden, cola[idx].orden
    db.commit()


def ranking_de_la_noche(db: Session) -> list[dict]:
    """Ranking del día en curso: canciones cantadas y votos 🔥 recibidos por mesa."""
    desde = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    filas = (
        db.query(
            Mesa.numero,
            func.count(Solicitud.id).label("canciones"),
            func.coalesce(func.sum(Solicitud.votos_fuego), 0).label("votos"),
        )
        .join(Solicitud, Solicitud.mesa_id == Mesa.id)
        .filter(Solicitud.estado == EstadoSolicitud.finalizada, Solicitud.creado_en >= desde)
        .group_by(Mesa.numero)
        .all()
    )
    ranking = [{"mesa": f.numero, "canciones": f.canciones, "votos": f.votos} for f in filas]
    ranking.sort(key=lambda r: (r["votos"], r["canciones"]), reverse=True)
    return ranking


# ---------- Videos/canales de YouTube reportados como falsos (clickbait) ----------
def bloquear_video_youtube(db: Session, video_id: str, canal: str | None = None) -> None:
    """Un video quedó comprobado como clickbait (título falso). Se bloquea
    para siempre en PostgreSQL, así sobrevive a cualquier redeploy."""
    video_id = (video_id or "").strip()
    if not video_id:
        return
    if not db.query(VideoBloqueado).filter(VideoBloqueado.video_id == video_id).first():
        db.add(VideoBloqueado(video_id=video_id, canal=canal))
    if canal:
        canal_normalizado = canal.strip().lower()
        if canal_normalizado and not db.query(CanalBloqueado).filter(CanalBloqueado.canal == canal_normalizado).first():
            db.add(CanalBloqueado(canal=canal_normalizado))
    db.commit()


def listar_bloqueados_youtube(db: Session) -> dict:
    videos = {v.video_id for v in db.query(VideoBloqueado.video_id).all()}
    canales = {c.canal for c in db.query(CanalBloqueado.canal).all()}
    return {"videos": videos, "canales": canales}
