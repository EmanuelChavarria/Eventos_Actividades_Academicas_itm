"""Vistas web del panel consolidado para coordinación (E7)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from app.api.deps import require_web_roles
from app.models.enums import Modalidad, Rol, TipoEvento
from app.models.usuario import Usuario
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


@router.get("/coordinacion/consolidado", response_class=HTMLResponse)
def pagina_consolidado(
    request: Request,
    usuario: Usuario = Depends(require_web_roles(Rol.COORDINACION)),
) -> Response:
    """Renderiza el esqueleto HTML del panel consolidado de coordinación."""
    return templates.TemplateResponse(
        request=request,
        name="reportes/consolidado.html",
        context={
            "usuario": usuario,
            "tipos": [tipo.value for tipo in TipoEvento],
            "modalidades": [mod.value for mod in Modalidad],
        },
    )
