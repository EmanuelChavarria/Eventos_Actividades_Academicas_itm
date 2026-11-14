"""Repositorio SQLAlchemy para acceso a datos de eventos académicos."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evento import Evento


def obtener_por_id(db: Session, evento_id: int) -> Evento | None:
    """Obtiene un evento por su identificador primario o `None` si no existe."""
    return db.execute(select(Evento).where(Evento.id == evento_id)).scalar_one_or_none()


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
