"""Schemas Pydantic v2 de entrada y salida para inscripciones."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InscripcionSalida(BaseModel):
    """Respuesta pública de una inscripción (sin datos sensibles)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    evento_id: int
    participante_id: int
    estado: str
    creado_en: datetime
    cancelada_en: datetime | None = None


class InscripcionDetalle(InscripcionSalida):
    """Detalle extendido con título del evento para 'Mis inscripciones'."""

    titulo_evento: str
    fecha_inicio_evento: datetime
    estado_evento: str


class InscritoSalida(BaseModel):
    """Inscrito visible para el organizador (documento completo)."""

    model_config = ConfigDict(from_attributes=True)

    inscripcion_id: int
    participante_id: int
    nombre: str
    numero_documento: str
    tipo_documento: str
    estado: str
    creado_en: datetime
    cancelada_en: datetime | None = None


class InscritoEnmascarado(BaseModel):
    """Inscrito visible para coordinación (documento enmascarado)."""

    model_config = ConfigDict(from_attributes=True)

    inscripcion_id: int
    participante_id: int
    nombre: str
    numero_documento: str  # ya viene enmascarado desde el servicio
    estado: str
    creado_en: datetime
    cancelada_en: datetime | None = None
