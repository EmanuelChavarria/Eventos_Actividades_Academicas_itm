"""Modelo ORM para eventos y actividades académicas."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.fechas import UTCDateTime, ahora_utc
from app.models.enums import EstadoEvento, PublicoObjetivo

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion
    from app.models.usuario import Usuario


class Evento(Base):
    """Evento o actividad académica creada por un organizador."""

    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint("cupo_maximo >= 1", name="ck_eventos_cupo"),
        CheckConstraint("fecha_fin > fecha_inicio", name="ck_eventos_fechas"),
        CheckConstraint("fecha_limite_inscripcion <= fecha_inicio", name="ck_eventos_limite"),
        CheckConstraint(
            "estado IN ('borrador', 'publicado', 'cancelado')",
            name="ck_eventos_estado",
        ),
        CheckConstraint(
            "tipo IN ('conferencia', 'taller', 'seminario', 'capacitacion')",
            name="ck_eventos_tipo",
        ),
        CheckConstraint(
            "modalidad IN ('presencial', 'virtual', 'hibrida')",
            name="ck_eventos_modalidad",
        ),
        CheckConstraint(
            "publico_objetivo IN ('todos', 'estudiantes', 'docentes')",
            name="ck_eventos_publico",
        ),
        Index("ix_eventos_estado_inicio", "estado", "fecha_inicio"),
        Index("ix_eventos_organizador", "organizador_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    fecha_limite_inscripcion: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    lugar: Mapped[str] = mapped_column(String(200), nullable=False)
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    publico_objetivo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PublicoObjetivo.TODOS.value,
    )
    ponente: Mapped[str | None] = mapped_column(String(150), nullable=True)
    requisitos: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    responsable_correo: Mapped[str] = mapped_column(String(150), nullable=False)
    cupo_maximo: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoEvento.BORRADOR.value,
    )
    motivo_cancelacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    organizador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    creado_en: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=ahora_utc)
    actualizado_en: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=ahora_utc,
        onupdate=ahora_utc,
    )

    organizador: Mapped[Usuario] = relationship(
        back_populates="eventos_organizados",
        foreign_keys=[organizador_id],
    )
    inscripciones: Mapped[list[Inscripcion]] = relationship(back_populates="evento")
