"""Esquemas Pydantic v2 para filtros, listado paginado y detalle del catálogo público (E4)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.fechas import FechaConZona
from app.models.enums import Modalidad, PublicoObjetivo, TipoEvento


class CatalogoFiltros(BaseModel):
    """Parámetros validados de búsqueda y paginación para el catálogo público (RF-11)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tipo: TipoEvento | None = None
    modalidad: Modalidad | None = None
    fecha_desde: FechaConZona | None = None
    fecha_hasta: FechaConZona | None = None
    texto: str | None = Field(default=None, max_length=120)
    incluir_finalizados: bool = False
    pagina: int = Field(default=1, ge=1)
    tamano: int = Field(default=10, ge=1, le=50)

    @field_validator("texto", mode="before")
    @classmethod
    def _normalizar_texto(cls, valor: object) -> object:
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @model_validator(mode="after")
    def _validar_rango_fechas(self) -> CatalogoFiltros:
        if (
            self.fecha_desde is not None
            and self.fecha_hasta is not None
            and self.fecha_hasta < self.fecha_desde
        ):
            raise ValueError("`fecha_hasta` no puede ser anterior a `fecha_desde`.")
        return self


class CatalogoEventoResumen(BaseModel):
    """Resumen público de un evento en el catálogo con disponibilidad calculada."""

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
    cupo_maximo: int
    inscripciones_activas: int
    cupos_disponibles: int
    inscripciones_abiertas: bool
    estado_efectivo: str


class CatalogoEventoDetalle(CatalogoEventoResumen):
    """Detalle completo de un evento publicado expuesto en el catálogo público (RF-12)."""

    requisitos: str | None
    responsable_nombre: str
    responsable_correo: str


class CatalogoPaginadoSalida(BaseModel):
    """Respuesta paginada del catálogo público de eventos."""

    items: list[CatalogoEventoResumen]
    total: int
    pagina: int
    tamano: int
    total_paginas: int
