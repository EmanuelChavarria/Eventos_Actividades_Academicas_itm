"""Dependencias compartidas de autenticación, autorización por rol y defensa CSRF."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import NoAutenticado, NoAutorizado, RequiereLoginWeb
from app.core.security import NOMBRE_COOKIE_SESION, es_origen_confiable
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.services import auth_service

_METODOS_MUTADORES = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _normalizar_roles(roles: tuple[Rol, ...]) -> set[str]:
    return {rol.value if isinstance(rol, Rol) else str(rol) for rol in roles}


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Retorna el usuario autenticado y activo desde cookie JWT o None."""
    token = request.cookies.get(NOMBRE_COOKIE_SESION)
    return auth_service.obtener_usuario_activo(db, token)


def get_current_user(
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Usuario:
    """Exige una sesión autenticada con usuario activo (401 si falta)."""
    if usuario is None or not usuario.activo:
        raise NoAutenticado()
    return usuario


def require_roles(*roles: Rol) -> Callable[[Usuario], Usuario]:
    """Genera una dependencia que exige uno de los roles permitidos (403 si no cumple)."""
    roles_permitidos = _normalizar_roles(roles)

    def _verificar_rol(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise NoAutorizado()
        return usuario

    return _verificar_rol


def require_web_user(
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Usuario:
    """Exige usuario activo en vistas web protegidas o redirige a /login."""
    if usuario is None or not usuario.activo:
        raise RequiereLoginWeb()
    return usuario


def require_web_roles(*roles: Rol) -> Callable[[Usuario], Usuario]:
    """Genera dependencia web: redirige 303 sin sesión y devuelve 403 si el rol no aplica."""
    roles_permitidos = _normalizar_roles(roles)

    def _verificar_rol_web(usuario: Usuario = Depends(require_web_user)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise NoAutorizado()
        return usuario

    return _verificar_rol_web


def verificar_csrf(request: Request) -> None:
    """Exige Origin (o respaldo Referer) válido en mutaciones autenticadas por cookie."""
    if request.method not in _METODOS_MUTADORES:
        return
    if NOMBRE_COOKIE_SESION not in request.cookies:
        return

    settings = get_settings()
    origen_solicitud = f"{request.url.scheme}://{request.url.netloc}"
    valido = es_origen_confiable(
        origin=request.headers.get("origin"),
        referer=request.headers.get("referer"),
        origen_solicitud=origen_solicitud,
        origenes_permitidos=settings.ALLOWED_ORIGINS,
    )
    if not valido:
        raise NoAutorizado(mensaje="Origen de solicitud no permitido.")
