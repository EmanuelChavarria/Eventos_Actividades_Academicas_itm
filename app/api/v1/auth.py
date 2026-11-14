"""Router v1 de autenticación, registro público y gestión de sesión por cookie."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import NOMBRE_COOKIE_SESION
from app.models.usuario import Usuario
from app.schemas.auth import LoginEntrada, RegistroEntrada, UsuarioSalida
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _obtener_ip_cliente(request: Request) -> str:
    """Obtiene la IP directa de conexión sin confiar en cabeceras no validadas."""
    return request.client.host if request.client and request.client.host else "desconocida"


@router.post(
    "/registro",
    response_model=UsuarioSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar participante",
)
def registrar_participante(
    datos: RegistroEntrada,
    db: Session = Depends(get_db),
) -> UsuarioSalida:
    """Registra públicamente un nuevo participante (estudiante o docente)."""
    usuario = auth_service.registrar_participante(db, datos)
    return UsuarioSalida.model_validate(usuario)


@router.post(
    "/login",
    response_model=UsuarioSalida,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
def iniciar_sesion(
    datos: LoginEntrada,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> UsuarioSalida:
    """Autentica con documento y contraseña y entrega cookie JWT segura."""
    settings = get_settings()
    usuario, token = auth_service.autenticar_usuario(
        db,
        datos,
        ip_cliente=_obtener_ip_cliente(request),
    )
    response.set_cookie(
        key=NOMBRE_COOKIE_SESION,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return UsuarioSalida.model_validate(usuario)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
def cerrar_sesion(response: Response) -> None:
    """Elimina la cookie de sesión del navegador."""
    settings = get_settings()
    response.delete_cookie(
        key=NOMBRE_COOKIE_SESION,
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.get(
    "/yo",
    response_model=UsuarioSalida,
    status_code=status.HTTP_200_OK,
    summary="Consultar usuario autenticado",
)
def obtener_usuario_actual(
    usuario: Usuario = Depends(get_current_user),
) -> UsuarioSalida:
    """Retorna la información pública del usuario autenticado y activo."""
    return UsuarioSalida.model_validate(usuario)
