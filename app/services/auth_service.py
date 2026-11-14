"""Lógica de negocio de autenticación, registro público y gestión de credenciales."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import CodigosError, Conflicto, NoAutenticado
from app.core.security import (
    control_intentos_login,
    crear_token_acceso,
    decodificar_token_acceso,
    hashear_password,
    verificar_en_tiempo_constante,
)
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories import usuario_repo
from app.schemas.auth import LoginEntrada, RegistroEntrada


def registrar_participante(db: Session, datos: RegistroEntrada) -> Usuario:
    """Registra públicamente a un participante validando documento único (RN-13, RN-21)."""
    existente = usuario_repo.obtener_por_documento(
        db,
        datos.tipo_documento,
        datos.numero_documento,
    )
    if existente is not None:
        raise Conflicto(
            codigo=CodigosError.DOCUMENTO_DUPLICADO,
            mensaje="Ya existe una cuenta registrada con ese tipo y número de documento.",
        )

    hash_pw = hashear_password(datos.password)
    try:
        return usuario_repo.crear(
            db,
            tipo_documento=datos.tipo_documento,
            numero_documento=datos.numero_documento,
            nombre=datos.nombre,
            correo=str(datos.correo),
            tipo_participante=datos.tipo_participante,
            hash_password=hash_pw,
            rol=Rol.PARTICIPANTE,
            activo=True,
        )
    except IntegrityError as exc:
        raise Conflicto(
            codigo=CodigosError.DOCUMENTO_DUPLICADO,
            mensaje="Ya existe una cuenta registrada con ese tipo y número de documento.",
        ) from exc


def autenticar_usuario(
    db: Session,
    datos: LoginEntrada,
    *,
    ip_cliente: str,
) -> tuple[Usuario, str]:
    """Autentica con tiempo constante, verifica cuenta activa y emite JWT HS256."""
    tipo = datos.tipo_documento.value
    control_intentos_login.verificar_no_bloqueado(ip_cliente, tipo, datos.numero_documento)

    usuario = usuario_repo.obtener_por_documento(
        db,
        datos.tipo_documento,
        datos.numero_documento,
    )
    hash_objetivo = usuario.hash_password if usuario is not None else None
    clave_valida = verificar_en_tiempo_constante(datos.password, hash_objetivo)

    if usuario is None or not usuario.activo or not clave_valida:
        control_intentos_login.registrar_fallo(ip_cliente, tipo, datos.numero_documento)
        raise NoAutenticado()

    control_intentos_login.reiniciar(ip_cliente, tipo, datos.numero_documento)
    token = crear_token_acceso(usuario.id)
    return usuario, token


def obtener_usuario_activo(db: Session, token: str | None) -> Usuario | None:
    """Resuelve el usuario autenticado y activo a partir del JWT de sesión o retorna None."""
    if not token:
        return None
    usuario_id = decodificar_token_acceso(token)
    if usuario_id is None:
        return None
    usuario = usuario_repo.obtener_por_id(db, usuario_id)
    if usuario is None or not usuario.activo:
        return None
    return usuario
