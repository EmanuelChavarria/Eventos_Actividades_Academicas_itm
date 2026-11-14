"""Endpoints REST públicos del catálogo y detalle de eventos (E4)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalogo import (
    CatalogoEventoDetalle,
    CatalogoFiltros,
    CatalogoPaginadoSalida,
)
from app.services import catalogo_service

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get(
    "/eventos",
    response_model=CatalogoPaginadoSalida,
    summary="Listar catálogo público de eventos publicados",
)
def listar_catalogo(
    filtros: Annotated[CatalogoFiltros, Query()],
    db: Session = Depends(get_db),
) -> CatalogoPaginadoSalida:
    """Devuelve eventos publicados paginados con filtros y disponibilidad real."""
    return catalogo_service.listar_catalogo(db, filtros)


@router.get(
    "/eventos/{evento_id}",
    response_model=CatalogoEventoDetalle,
    summary="Consultar detalle público de un evento publicado",
)
def obtener_detalle_catalogo(
    evento_id: int,
    db: Session = Depends(get_db),
) -> CatalogoEventoDetalle:
    """Devuelve detalle y cupos disponibles en tiempo real o 404 si no es público."""
    return catalogo_service.obtener_detalle_catalogo(db, evento_id)
