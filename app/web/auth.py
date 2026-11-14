"""Vistas web de autenticación (/login y /registro)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.api.deps import get_current_user_optional
from app.models.usuario import Usuario
from app.web.plantillas import templates

router = APIRouter(include_in_schema=False)


def _render_o_redirigir(
    request: Request,
    usuario: Usuario | None,
    plantilla: str,
) -> Response:
    """Redirige a inicio si ya hay sesión activa; de lo contrario renderiza la vista."""
    if usuario is not None:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name=plantilla,
        context={"usuario": None},
    )


@router.get("/login", response_class=HTMLResponse)
def pagina_login(
    request: Request,
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Response:
    """Renderiza el formulario de inicio de sesión o redirige si ya hay sesión."""
    return _render_o_redirigir(request, usuario, "auth/login.html")


@router.get("/registro", response_class=HTMLResponse)
def pagina_registro(
    request: Request,
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Response:
    """Renderiza el formulario de registro de participante o redirige si ya hay sesión."""
    return _render_o_redirigir(request, usuario, "auth/registro.html")
