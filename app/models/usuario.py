"""Modelo ORM para usuarios (participantes, organizadores y coordinación)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.fechas import UTCDateTime, ahora_utc
from app.models.enums import Rol

if TYPE_CHECKING:
    from app.models.evento import Evento
    from app.models.inscripcion import Inscripcion


class Usuario(Base):
    """Representa una persona registrada en el sistema."""

    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_usuarios_documento"),
        CheckConstraint("length(numero_documento) BETWEEN 5 AND 15", name="ck_usuarios_doc_len"),
        CheckConstraint(
            "tipo_documento IN ('CC', 'CE', 'TI', 'PAS')",
            name="ck_usuarios_tipo_doc",
        ),
        CheckConstraint(
            "rol IN ('participante', 'organizador', 'coordinacion')",
            name="ck_usuarios_rol",
        ),
        CheckConstraint(
            "tipo_participante IS NULL OR tipo_participante IN ('estudiante', 'docente')",
            name="ck_usuarios_tipo_participante",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_documento: Mapped[str] = mapped_column(String(4), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(15), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_participante: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hash_password: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default=Rol.PARTICIPANTE.value)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=ahora_utc)

    eventos_organizados: Mapped[list[Evento]] = relationship(
        back_populates="organizador",
        foreign_keys="Evento.organizador_id",
    )
    inscripciones: Mapped[list[Inscripcion]] = relationship(
        back_populates="participante",
        foreign_keys="Inscripcion.participante_id",
    )
