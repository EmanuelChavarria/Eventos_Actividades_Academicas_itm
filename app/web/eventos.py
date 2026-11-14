"""Vistas web de gestión de eventos para organizadores (E3)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from app.api.deps import require_web_roles
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


def _render_vista(
    request: Request,
    usuario: Usuario,
    plantilla: str,
    **extra: Any,
) -> Response:
    """Renderiza una plantilla HTML inyectando el usuario autenticado en sesión."""
    contexto = {"usuario": usuario, **extra}
    return templates.TemplateResponse(request=request, name=plantilla, context=contexto)


@router.get("/organizador/eventos", response_class=HTMLResponse)
def pagina_mis_eventos(
    request: Request,
    usuario: Usuario = Depends(require_web_roles(Rol.ORGANIZADOR)),
) -> Response:
    """Vista web de listado y acciones rápidas de eventos del organizador."""
    return _render_vista(request, usuario, "eventos/mis_eventos.html")


@router.get("/organizador/eventos/nuevo", response_class=HTMLResponse)
def pagina_nuevo_evento(
    request: Request,
    usuario: Usuario = Depends(require_web_roles(Rol.ORGANIZADOR)),
) -> Response:
    """Vista web para crear un nuevo evento en borrador."""
    return _render_vista(
        request,
        usuario,
        "eventos/formulario.html",
        modo="crear",
        evento_id=None,
    )


@router.get("/organizador/eventos/{evento_id}/editar", response_class=HTMLResponse)
def pagina_editar_evento(
    request: Request,
    evento_id: int,
    usuario: Usuario = Depends(require_web_roles(Rol.ORGANIZADOR)),
) -> Response:
    """Vista web para editar un evento existente del organizador."""
    return _render_vista(
        request,
        usuario,
        "eventos/formulario.html",
        modo="editar",
        evento_id=evento_id,
    )
