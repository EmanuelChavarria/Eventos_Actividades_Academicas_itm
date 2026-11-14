"""Esquemas Pydantic v2 y validadores compartidos para gestión de eventos (E3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.fechas import FechaConZona, asegurar_utc
from app.models.enums import EstadoEvento, Modalidad, PublicoObjetivo, TipoEvento


def validar_coherencia_fechas(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    fecha_limite_inscripcion: datetime,
) -> None:
    """Valida RN-03 en UTC: `fecha_fin > fecha_inicio` y `fecha_limite <= fecha_inicio`."""
    inicio = asegurar_utc(fecha_inicio)
    fin = asegurar_utc(fecha_fin)
    limite = asegurar_utc(fecha_limite_inscripcion)
    if fin <= inicio:
        raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
    if limite > inicio:
        raise ValueError(
            "La fecha límite de inscripción no puede ser posterior al inicio del evento."
        )


def _normalizar_opcional_vacio(valor: object) -> object:
    """Convierte cadenas vacías o solo espacios en `None` para campos opcionales."""
    if isinstance(valor, str) and not valor.strip():
        return None
    return valor


class EventoCrear(BaseModel):
    """Datos requeridos para crear un evento en estado `borrador` (RF-05)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str = Field(min_length=10, max_length=4000)
    tipo: TipoEvento
    fecha_inicio: FechaConZona
    fecha_fin: FechaConZona
    fecha_limite_inscripcion: FechaConZona
    lugar: str = Field(min_length=2, max_length=200)
    modalidad: Modalidad
    publico_objetivo: PublicoObjetivo = PublicoObjetivo.TODOS
    ponente: str | None = Field(default=None, max_length=150)
    requisitos: str | None = Field(default=None, max_length=2000)
    responsable_nombre: str = Field(min_length=2, max_length=120)
    responsable_correo: EmailStr = Field(max_length=150)
    cupo_maximo: int = Field(ge=1)

    _limpiar_opcionales = field_validator("ponente", "requisitos", mode="before")(
        _normalizar_opcional_vacio
    )

    @model_validator(mode="after")
    def _validar_fechas(self) -> EventoCrear:
        validar_coherencia_fechas(
            self.fecha_inicio,
            self.fecha_fin,
            self.fecha_limite_inscripcion,
        )
        return self


class EventoActualizar(BaseModel):
    """Campos editables de un evento existente vía `PATCH` (RF-07, RN-09)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=3, max_length=200)
    descripcion: str | None = Field(default=None, min_length=10, max_length=4000)
    tipo: TipoEvento | None = None
    fecha_inicio: FechaConZona | None = None
    fecha_fin: FechaConZona | None = None
    fecha_limite_inscripcion: FechaConZona | None = None
    lugar: str | None = Field(default=None, min_length=2, max_length=200)
    modalidad: Modalidad | None = None
    publico_objetivo: PublicoObjetivo | None = None
    ponente: str | None = Field(default=None, max_length=150)
    requisitos: str | None = Field(default=None, max_length=2000)
    responsable_nombre: str | None = Field(default=None, min_length=2, max_length=120)
    responsable_correo: EmailStr | None = Field(default=None, max_length=150)
    cupo_maximo: int | None = Field(default=None, ge=1)

    _limpiar_opcionales = field_validator("ponente", "requisitos", mode="before")(
        _normalizar_opcional_vacio
    )


class EventoCancelar(BaseModel):
    """Carga útil para cancelar un evento publicado indicando motivo (RF-08)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    motivo: str = Field(min_length=5, max_length=1000)


class EventoSalida(BaseModel):
    """Representación de gestión del evento con estado efectivo y ocupación calculada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: str
    tipo: TipoEvento
    fecha_inicio: datetime
    fecha_fin: datetime
    fecha_limite_inscripcion: datetime
    lugar: str
    modalidad: Modalidad
    publico_objetivo: PublicoObjetivo
    ponente: str | None
    requisitos: str | None
    responsable_nombre: str
    responsable_correo: str
    cupo_maximo: int
    estado: EstadoEvento
    estado_efectivo: str
    inscripciones_abiertas: bool
    inscripciones_activas: int
    cupos_disponibles: int
    motivo_cancelacion: str | None
    organizador_id: int
    creado_en: datetime
    actualizado_en: datetime
