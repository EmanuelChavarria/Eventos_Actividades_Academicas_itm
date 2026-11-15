"""Schemas Pydantic v2 para registro y consulta de asistencia (E6)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoAsistencia


class AsistenciaRegistroEntrada(BaseModel):
    """Carga útil para registrar o corregir asistencia de una inscripción."""

    estado: EstadoAsistencia


class AsistenciaSalida(BaseModel):
    """Respuesta pública del registro de asistencia persistido."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    inscripcion_id: int
    estado: str
    registrado_por_id: int
    registrado_en: datetime
    actualizado_en: datetime


class ParticipanteAsistenciaSalida(BaseModel):
    """Elemento de la nómina de asistencia con privacidad diferencial según rol."""

    inscripcion_id: int
    participante_id: int
    nombre: str
    correo: str
    tipo_documento: str
    numero_documento: str
    estado_inscripcion: str
    estado_asistencia: Literal["presente", "ausente", "pendiente"]
    asistencia_id: int | None = None
    registrado_por_id: int | None = None
    registrado_en: datetime | None = None
    actualizado_en: datetime | None = None
