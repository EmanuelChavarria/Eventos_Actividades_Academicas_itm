"""Repositorio de asistencia con UPSERT idempotente por inscripción (E6)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.asistencia import Asistencia
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario


def obtener_evento(db: Session, evento_id: int) -> Evento | None:
    """Retorna el evento por su ID o None si no existe."""
    return db.get(Evento, evento_id)


def obtener_inscripcion_de_evento(
    db: Session,
    evento_id: int,
    inscripcion_id: int,
) -> Inscripcion | None:
    """Retorna la inscripción indicada verificando que pertenezca al evento."""
    consulta = select(Inscripcion).where(
        Inscripcion.id == inscripcion_id,
        Inscripcion.evento_id == evento_id,
    )
    return db.execute(consulta).scalar_one_or_none()


def obtener_por_inscripcion(db: Session, inscripcion_id: int) -> Asistencia | None:
    """Retorna el registro de asistencia asociado a la inscripción o None."""
    consulta = select(Asistencia).where(Asistencia.inscripcion_id == inscripcion_id)
    return db.execute(consulta).scalar_one_or_none()


def registrar_o_actualizar(
    db: Session,
    *,
    inscripcion_id: int,
    estado: str,
    usuario_id: int,
    ahora: datetime,
) -> Asistencia:
    """Inserta o actualiza idempotente la asistencia de una inscripción (UPSERT)."""
    stmt = (
        sqlite_insert(Asistencia)
        .values(
            inscripcion_id=inscripcion_id,
            estado=estado,
            registrado_por_id=usuario_id,
            registrado_en=ahora,
            actualizado_en=ahora,
        )
        .on_conflict_do_update(
            index_elements=["inscripcion_id"],
            set_={
                "estado": estado,
                "registrado_por_id": usuario_id,
                "actualizado_en": ahora,
            },
        )
    )
    db.execute(stmt)
    db.commit()

    asistencia = obtener_por_inscripcion(db, inscripcion_id)
    if asistencia is None:  # pragma: no cover - invariante tras commit
        raise RuntimeError("No se pudo recuperar el registro de asistencia tras UPSERT.")
    db.refresh(asistencia)
    return asistencia


def listar_nomina_con_asistencia(
    db: Session,
    evento_id: int,
) -> list[tuple[Inscripcion, Usuario, Asistencia | None]]:
    """Lista las inscripciones del evento con su participante y asistencia (LEFT JOIN)."""
    consulta = (
        select(Inscripcion, Usuario, Asistencia)
        .join(Usuario, Inscripcion.participante_id == Usuario.id)
        .outerjoin(Asistencia, Asistencia.inscripcion_id == Inscripcion.id)
        .where(Inscripcion.evento_id == evento_id)
        .order_by(Usuario.nombre.asc(), Inscripcion.creado_en.asc())
    )
    return [(insc, usuario, asist) for insc, usuario, asist in db.execute(consulta).all()]
