"""Dependencias compartidas de autenticación y control de acceso por rol."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NoAutenticado, NoAutorizado
from app.models.enums import Rol
from app.models.usuario import Usuario


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Retorna el usuario autenticado si existe sesión válida o None en caso contrario.

    Nota: la decodificación de cookie JWT se completa en E2; en E1 retorna None
    para que ninguna ruta protegida quede accesible sin autenticación.
    """
    _ = (request, db)
    return None


def get_current_user(
    usuario: Usuario | None = Depends(get_current_user_optional),
) -> Usuario:
    """Exige una sesión autenticada con usuario activo (401 si falta)."""
    if usuario is None or not usuario.activo:
        raise NoAutenticado()
    return usuario


def require_roles(*roles: Rol) -> Callable[[Usuario], Usuario]:
    """Genera una dependencia que exige uno de los roles permitidos (403 si no cumple)."""
    roles_permitidos = {rol.value if isinstance(rol, Rol) else str(rol) for rol in roles}

    def _verificar_rol(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise NoAutorizado()
        return usuario

    return _verificar_rol
