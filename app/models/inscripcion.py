"""Modelo ORM para inscripciones de participantes a eventos."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.fechas import UTCDateTime, ahora_utc
from app.models.enums import EstadoInscripcion

if TYPE_CHECKING:
    from app.models.asistencia import Asistencia
    from app.models.evento import Evento
    from app.models.usuario import Usuario


class Inscripcion(Base):
    """Inscripción de un participante a un evento académico."""

    __tablename__ = "inscripciones"
    __table_args__ = (
        CheckConstraint("estado IN ('activa', 'cancelada')", name="ck_inscripciones_estado"),
        Index(
            "ux_inscripciones_activa",
            "evento_id",
            "participante_id",
            unique=True,
            sqlite_where=text("estado = 'activa'"),
        ),
        Index("ix_inscripciones_evento", "evento_id"),
        Index("ix_inscripciones_participante", "participante_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evento_id: Mapped[int] = mapped_column(
        ForeignKey("eventos.id", ondelete="RESTRICT"),
        nullable=False,
    )
    participante_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoInscripcion.ACTIVA.value,
    )
    creado_en: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=ahora_utc)
    cancelada_en: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    evento: Mapped[Evento] = relationship(back_populates="inscripciones")
    participante: Mapped[Usuario] = relationship(
        back_populates="inscripciones",
        foreign_keys=[participante_id],
    )
    asistencia: Mapped[Asistencia | None] = relationship(
        back_populates="inscripcion",
        uselist=False,
    )
