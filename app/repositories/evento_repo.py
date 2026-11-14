"""Repositorio SQLAlchemy para acceso a datos de eventos académicos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.fechas import ahora_utc
from app.models.enums import EstadoEvento
from app.models.evento import Evento


def escapar_like(texto: str) -> str:
    """Escapa comodines SQL (`\\`, `%`, `_`) para búsquedas literales seguras con `LIKE`."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def obtener_por_id(db: Session, evento_id: int) -> Evento | None:
    """Obtiene un evento por su identificador primario o `None` si no existe."""
    return db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()


def obtener_publicado_por_id(db: Session, evento_id: int) -> Evento | None:
    """Obtiene un evento solo si su estado persistido es `publicado`."""
    consulta = select(Evento).where(
        Evento.id == evento_id,
        Evento.estado == EstadoEvento.PUBLICADO.value,
    )
    return db.execute(consulta).scalar_one_or_none()


def buscar_publicados_paginado(
    db: Session,
    *,
    tipo: str | None = None,
    modalidad: str | None = None,
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    texto: str | None = None,
    incluir_finalizados: bool = False,
    ahora: datetime | None = None,
    pagina: int = 1,
    tamano: int = 10,
) -> tuple[list[Evento], int]:
    """Consulta eventos publicados con filtros combinables, orden estable y paginación."""
    condiciones = [Evento.estado == EstadoEvento.PUBLICADO.value]
    if not incluir_finalizados:
        condiciones.append(Evento.fecha_fin >= (ahora or ahora_utc()))
    if tipo is not None:
        condiciones.append(Evento.tipo == tipo)
    if modalidad is not None:
        condiciones.append(Evento.modalidad == modalidad)
    if fecha_desde is not None:
        condiciones.append(Evento.fecha_inicio >= fecha_desde)
    if fecha_hasta is not None:
        condiciones.append(Evento.fecha_inicio <= fecha_hasta)
    if texto:
        patron = f"%{escapar_like(texto)}%"
        condiciones.append(
            or_(
                Evento.titulo.ilike(patron, escape="\\"),
                Evento.descripcion.ilike(patron, escape="\\"),
                Evento.lugar.ilike(patron, escape="\\"),
                Evento.ponente.ilike(patron, escape="\\"),
            )
        )

    total = int(db.scalar(select(func.count()).select_from(Evento).where(*condiciones)) or 0)
    offset = (pagina - 1) * tamano
    consulta = (
        select(Evento)
        .where(*condiciones)
        .order_by(Evento.fecha_inicio.asc(), Evento.id.asc())
        .offset(offset)
        .limit(tamano)
    )
    items = list(db.execute(consulta).scalars().all())
    return items, total


def listar_por_organizador(db: Session, organizador_id: int) -> list[Evento]:
    """Lista los eventos de un organizador ordenados del más reciente al más antiguo."""
    consulta = (
        select(Evento)
        .where(Evento.organizador_id == organizador_id)
        .order_by(Evento.fecha_inicio.desc(), Evento.id.desc())
    )
    return list(db.execute(consulta).scalars().all())


def _persistir(db: Session, evento: Evento, *, nuevo: bool) -> Evento:
    """Persiste cambios de un evento garantizando rollback ante conflicto de BD."""
    if nuevo:
        db.add(evento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(evento)
    return evento


def crear(db: Session, evento: Evento) -> Evento:
    """Inserta y devuelve un nuevo evento persistido."""
    return _persistir(db, evento, nuevo=True)


def guardar(db: Session, evento: Evento) -> Evento:
    """Guarda las modificaciones de un evento existente en BD."""
    return _persistir(db, evento, nuevo=False)
