"""Repositorio de inscripciones: conteos de cupo compartido en E1 y flujo E5."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload

from app.core.errors import CodigosError, Conflicto, NoEncontrado
from app.core.fechas import ahora_utc
from app.models.enums import EstadoInscripcion
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario


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


def insertar_atomica(
    db: Session,
    evento_id: int,
    participante_id: int,
    ahora: datetime | None = None,
) -> Inscripcion:
    """Inserta una inscripción activa con BEGIN IMMEDIATE + inserción condicional.

    Garantiza cero sobrecupos: si el cupo está lleno (rowcount == 0) lanza
    Conflicto(CUPO_AGOTADO). La unicidad activa la garantiza el índice parcial.
    """
    ts = (ahora or ahora_utc()).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Iniciamos transacción exclusiva para evitar condición de carrera en SQLite
    db.execute(text("BEGIN IMMEDIATE"))

    sql = text(
        """
        INSERT INTO inscripciones (evento_id, participante_id, estado, creado_en)
        SELECT :evento_id, :participante_id, 'activa', :ts
        WHERE (
            SELECT COUNT(*) FROM inscripciones
            WHERE evento_id = :evento_id AND estado = 'activa'
        ) < (
            SELECT cupo_maximo FROM eventos WHERE id = :evento_id
        )
        """
    )
    resultado = db.execute(
        sql,
        {"evento_id": evento_id, "participante_id": participante_id, "ts": ts},
    )

    if resultado.rowcount == 0:
        db.rollback()
        raise Conflicto(
            codigo=CodigosError.CUPO_AGOTADO,
            mensaje="El evento ha alcanzado su capacidad máxima de inscripciones.",
        )

    # Recuperamos el registro recién creado (lastrowid disponible en SQLite)
    nueva_id = resultado.lastrowid
    db.commit()

    inscripcion = db.get(Inscripcion, nueva_id)
    if inscripcion is None:  # pragma: no cover — no debería ocurrir
        raise NoEncontrado(
            codigo="INSCRIPCION_NO_ENCONTRADA",
            mensaje="No se pudo recuperar la inscripción recién creada.",
        )
    return inscripcion


def cancelar(
    db: Session,
    inscripcion: Inscripcion,
    ahora: datetime | None = None,
) -> Inscripcion:
    """Actualiza la inscripción a 'cancelada' sin eliminar el registro (historial)."""
    ts = ahora or ahora_utc()
    inscripcion.estado = EstadoInscripcion.CANCELADA.value
    inscripcion.cancelada_en = ts
    db.commit()
    db.refresh(inscripcion)
    return inscripcion


def obtener_por_id(db: Session, inscripcion_id: int) -> Inscripcion | None:
    """Retorna una inscripción por su ID o None si no existe."""
    return db.get(Inscripcion, inscripcion_id)


def listar_de_participante(db: Session, participante_id: int) -> list[Inscripcion]:
    """Retorna todas las inscripciones de un participante, más recientes primero."""
    consulta = (
        select(Inscripcion)
        .options(joinedload(Inscripcion.evento))
        .where(Inscripcion.participante_id == participante_id)
        .order_by(Inscripcion.creado_en.desc())
    )
    return list(db.execute(consulta).scalars().all())


def listar_de_evento(db: Session, evento_id: int) -> list[Inscripcion]:
    """Retorna todas las inscripciones de un evento con sus participantes cargados."""
    consulta = (
        select(Inscripcion)
        .where(Inscripcion.evento_id == evento_id)
        .order_by(Inscripcion.creado_en.asc())
    )
    return list(db.execute(consulta).scalars().all())


def tiene_inscripcion_activa(db: Session, evento_id: int, participante_id: int) -> bool:
    """Verifica si el participante ya tiene una inscripción activa en el evento."""
    consulta = select(func.count(Inscripcion.id)).where(
        Inscripcion.evento_id == evento_id,
        Inscripcion.participante_id == participante_id,
        Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
    )
    return int(db.execute(consulta).scalar_one()) > 0


def obtener_evento(db: Session, evento_id: int) -> Evento | None:
    """Retorna el evento por ID o None."""
    return db.get(Evento, evento_id)


def obtener_participante(db: Session, participante_id: int) -> Usuario | None:
    """Retorna el usuario por ID o None."""
    return db.get(Usuario, participante_id)
