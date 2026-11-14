"""Vistas web públicas del catálogo y detalle de eventos (E4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.usuario import Usuario
from app.services import catalogo_service
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def pagina_inicio(
    request: Request,
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Response:
    """Renderiza el esqueleto Jinja2 del catálogo público con filtros y paginación."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"usuario": usuario},
    )


@router.get("/eventos/{evento_id}", response_class=HTMLResponse)
def pagina_detalle_evento(
    request: Request,
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Response:
    """Renderiza el detalle de un evento publicado o una página 404 amigable."""
    if not catalogo_service.existe_evento_publicado(db, evento_id):
        return templates.TemplateResponse(
            request=request,
            name="catalogo/no_encontrado.html",
            context={"usuario": usuario, "evento_id": evento_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return templates.TemplateResponse(
        request=request,
        name="catalogo/detalle.html",
        context={"usuario": usuario, "evento_id": evento_id},
    )
