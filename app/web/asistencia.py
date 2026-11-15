"""Vistas web de registro y consulta de asistencia (E6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from app.api.deps import require_web_roles
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


@router.get("/eventos/{evento_id}/asistencia", response_class=HTMLResponse)
def pagina_registro_asistencia(
    evento_id: int,
    request: Request,
    usuario: Usuario = Depends(require_web_roles(Rol.ORGANIZADOR, Rol.COORDINACION)),
) -> Response:
    """Renderiza la pantalla de registro/consulta de asistencia para un evento."""
    return templates.TemplateResponse(
        request=request,
        name="asistencia/registro.html",
        context={"usuario": usuario, "evento_id": evento_id},
    )
