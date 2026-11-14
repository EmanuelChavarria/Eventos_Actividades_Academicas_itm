"""Vistas web del catálogo público (base en E1, vista completa en E4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.api.deps import get_current_user_optional
from app.models.usuario import Usuario
from app.web import templates

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def pagina_inicio(
    request: Request,
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> HTMLResponse:
    """Renderiza el esqueleto inicial Jinja2 sin lógica ni datos de negocio."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"usuario": usuario},
    )
