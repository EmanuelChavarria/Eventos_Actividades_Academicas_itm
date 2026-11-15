"""Router v1 del reporte consolidado y exportación CSV para coordinación (E7)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.schemas.reporte import ConsolidadoFiltros, ConsolidadoSalida
from app.services import reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get(
    "/consolidado",
    response_model=ConsolidadoSalida,
    summary="Consultar reporte consolidado de eventos y asistencia",
)
def obtener_consolidado(
    filtros: Annotated[ConsolidadoFiltros, Query()],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.COORDINACION)),
) -> ConsolidadoSalida:
    """Devuelve métricas agregadas por evento y totales globales solo para coordinación."""
    return reporte_service.obtener_consolidado(db, filtros, usuario)


@router.get(
    "/consolidado/csv",
    summary="Exportar reporte consolidado en CSV neutralizado",
)
def exportar_consolidado_csv(
    filtros: Annotated[ConsolidadoFiltros, Query()],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.COORDINACION)),
) -> Response:
    """Descarga el reporte consolidado filtrado en CSV protegiendo contra fórmulas peligrosas."""
    contenido = reporte_service.exportar_consolidado_csv(db, filtros, usuario)
    return Response(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="consolidado.csv"'},
    )
