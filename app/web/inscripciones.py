"""Vistas web de inscripciones del participante (E5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from app.api.deps import require_web_roles
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


@router.get("/mis-inscripciones", response_class=HTMLResponse)
def pagina_mis_inscripciones(
    request: Request,
    usuario: Usuario = Depends(require_web_roles(Rol.PARTICIPANTE)),
) -> Response:
    """Renderiza la pagina de 'Mis inscripciones' del participante autenticado."""
    return templates.TemplateResponse(
        request=request,
        name="inscripciones/mias.html",
        context={"usuario": usuario},
    )
