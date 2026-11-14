"""Modelo ORM para registro y corrección de asistencia por inscripción."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.fechas import UTCDateTime, ahora_utc

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion
    from app.models.usuario import Usuario


class Asistencia(Base):
    """Registro único de asistencia asociado a una inscripción activa."""

    __tablename__ = "asistencias"
    __table_args__ = (
        UniqueConstraint("inscripcion_id", name="uq_asistencias_inscripcion"),
        CheckConstraint("estado IN ('presente', 'ausente')", name="ck_asistencias_estado"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inscripcion_id: Mapped[int] = mapped_column(
        ForeignKey("inscripciones.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    registrado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    registrado_en: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=ahora_utc,
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=ahora_utc,
        onupdate=ahora_utc,
    )

    inscripcion: Mapped[Inscripcion] = relationship(back_populates="asistencia")
    registrado_por: Mapped[Usuario] = relationship(foreign_keys=[registrado_por_id])
