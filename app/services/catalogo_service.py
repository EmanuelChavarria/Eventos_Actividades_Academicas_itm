"""Servicio de dominio del catálogo público, filtros, detalle y disponibilidad (E4)."""

from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import TypeVar

from sqlalchemy.orm import Session

from app.core import fechas
from app.core.errors import CodigosError, NoEncontrado
from app.models.enums import EstadoEvento
from app.models.evento import Evento
from app.repositories import evento_repo, inscripcion_repo
from app.schemas.catalogo import (
    CatalogoEventoDetalle,
    CatalogoEventoResumen,
    CatalogoFiltros,
    CatalogoPaginadoSalida,
)
from app.services.evento_service import calcular_estado_efectivo

_TSchemaCatalogo = TypeVar("_TSchemaCatalogo", CatalogoEventoResumen, CatalogoEventoDetalle)


def _construir_item_catalogo(
    evento: Evento,
    inscripciones_activas: int,
    schema_cls: type[_TSchemaCatalogo],
    *,
    ahora: datetime,
) -> _TSchemaCatalogo:
    """Construye la vista pública de evento calculando cupos e indicadores dinámicos."""
    estado_efectivo = calcular_estado_efectivo(evento, ahora)
    cupos_disponibles = max(evento.cupo_maximo - inscripciones_activas, 0)
    inscripciones_abiertas = (
        estado_efectivo == EstadoEvento.PUBLICADO.value
        and fechas.asegurar_utc(evento.fecha_limite_inscripcion) > ahora
        and cupos_disponibles > 0
    )
    datos = {columna.name: getattr(evento, columna.name) for columna in Evento.__table__.columns}
    datos.update(
        {
            "estado_efectivo": estado_efectivo,
            "inscripciones_activas": inscripciones_activas,
            "cupos_disponibles": cupos_disponibles,
            "inscripciones_abiertas": inscripciones_abiertas,
        }
    )
    return schema_cls.model_validate(datos)


def listar_catalogo(db: Session, filtros: CatalogoFiltros) -> CatalogoPaginadoSalida:
    """Lista eventos publicados paginados calculando disponibilidad sin consultas N+1."""
    ahora = fechas.ahora_utc()
    eventos, total = evento_repo.buscar_publicados_paginado(
        db,
        tipo=filtros.tipo.value if filtros.tipo is not None else None,
        modalidad=filtros.modalidad.value if filtros.modalidad is not None else None,
        fecha_desde=filtros.fecha_desde,
        fecha_hasta=filtros.fecha_hasta,
        texto=filtros.texto,
        incluir_finalizados=filtros.incluir_finalizados,
        ahora=ahora,
        pagina=filtros.pagina,
        tamano=filtros.tamano,
    )
    conteos = (
        inscripcion_repo.contar_activas_por_eventos(db, [ev.id for ev in eventos])
        if eventos
        else {}
    )
    items = [
        _construir_item_catalogo(
            ev,
            conteos.get(ev.id, 0),
            CatalogoEventoResumen,
            ahora=ahora,
        )
        for ev in eventos
    ]
    total_paginas = ceil(total / filtros.tamano) if total > 0 else 0
    return CatalogoPaginadoSalida(
        items=items,
        total=total,
        pagina=filtros.pagina,
        tamano=filtros.tamano,
        total_paginas=total_paginas,
    )


def obtener_detalle_catalogo(db: Session, evento_id: int) -> CatalogoEventoDetalle:
    """Devuelve el detalle público de un evento publicado o lanza 404 uniforme."""
    evento = evento_repo.obtener_publicado_por_id(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            CodigosError.EVENTO_NO_ENCONTRADO,
            "El evento solicitado no existe o no está publicado.",
        )
    ahora = fechas.ahora_utc()
    activas = inscripcion_repo.contar_activas(db, evento.id)
    return _construir_item_catalogo(evento, activas, CatalogoEventoDetalle, ahora=ahora)


def existe_evento_publicado(db: Session, evento_id: int) -> bool:
    """Indica si existe un evento en estado `publicado` para renderizado web seguro."""
    return evento_repo.obtener_publicado_por_id(db, evento_id) is not None
