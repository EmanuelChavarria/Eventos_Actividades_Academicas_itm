"""Schemas Pydantic v2 para filtros, métricas por evento y totales globales (E7)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.fechas import FechaConZona
from app.models.enums import Modalidad, TipoEvento

EstadoConsolidado = Literal["borrador", "publicado", "finalizado", "cancelado"]


class ConsolidadoFiltros(BaseModel):
    """Filtros combinables para el reporte consolidado de coordinación (RF-25)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    fecha_desde: FechaConZona | None = None
    fecha_hasta: FechaConZona | None = None
    tipo: TipoEvento | None = None
    modalidad: Modalidad | None = None
    estado: EstadoConsolidado | None = None
    organizador_id: int | None = Field(default=None, ge=1)
    texto: str | None = Field(default=None, max_length=120)

    @field_validator("texto", mode="before")
    @classmethod
    def _normalizar_texto(cls, valor: object) -> object:
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @model_validator(mode="after")
    def _validar_rango_fechas(self) -> ConsolidadoFiltros:
        if (
            self.fecha_desde is not None
            and self.fecha_hasta is not None
            and self.fecha_hasta < self.fecha_desde
        ):
            raise ValueError("`fecha_hasta` no puede ser anterior a `fecha_desde`.")
        return self


class EventoConsolidadoItem(BaseModel):
    """Métricas agregadas de inscripción y asistencia para un evento."""

    evento_id: int
    titulo: str
    tipo: str
    modalidad: str
    estado: str
    fecha_inicio: datetime
    fecha_fin: datetime
    organizador_id: int
    organizador_nombre: str
    cupo_maximo: int
    inscritos_activos: int
    disponibles: int
    ocupacion_pct: float
    cancelaciones: int
    presentes: int
    ausentes: int
    sin_registrar: int
    asistencia_pct: float


class ConsolidadoTotales(BaseModel):
    """Totales globales coherentes con las filas del consolidado (RF-26)."""

    total_eventos: int
    cupo_total: int
    inscritos_activos: int
    disponibles: int
    ocupacion_pct: float
    cancelaciones: int
    presentes: int
    ausentes: int
    sin_registrar: int
    asistencia_pct: float


class ConsolidadoSalida(BaseModel):
    """Respuesta completa del panel consolidado con detalle y totales."""

    eventos: list[EventoConsolidadoItem]
    totales: ConsolidadoTotales
