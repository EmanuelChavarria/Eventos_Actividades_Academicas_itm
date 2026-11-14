"""Repositorio de inscripciones: conteos de cupo compartido en E1 y flujo E5."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import EstadoInscripcion
from app.models.inscripcion import Inscripcion


def contar_activas(db: Session, evento_id: int) -> int:
    """Retorna el número de inscripciones activas de un evento."""
    consulta = select(func.count(Inscripcion.id)).where(
        Inscripcion.evento_id == evento_id,
        Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
    )
    resultado = db.execute(consulta).scalar_one()
    return int(resultado)


def contar_activas_por_eventos(db: Session, ids: Sequence[int]) -> dict[int, int]:
    """Retorna un mapa {evento_id: inscripciones_activas} en una sola consulta."""
    ids_unicos = list(dict.fromkeys(ids))
    if not ids_unicos:
        return {}

    consulta = (
        select(Inscripcion.evento_id, func.count(Inscripcion.id))
        .where(
            Inscripcion.evento_id.in_(ids_unicos),
            Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
        )
        .group_by(Inscripcion.evento_id)
    )
    filas = db.execute(consulta).all()
    conteos = {int(evento_id): int(total) for evento_id, total in filas}
    return {evento_id: conteos.get(evento_id, 0) for evento_id in ids_unicos}
