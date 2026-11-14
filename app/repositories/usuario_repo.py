"""Repositorio SQLAlchemy para acceso a datos de usuarios."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import Rol, TipoDocumento, TipoParticipante
from app.models.usuario import Usuario


def obtener_por_id(db: Session, usuario_id: int) -> Usuario | None:
    """Obtiene un usuario por su identificador primario o None si no existe."""
    return db.execute(select(Usuario).where(Usuario.id == usuario_id)).scalar_one_or_none()


def obtener_por_documento(
    db: Session,
    tipo_documento: TipoDocumento | str,
    numero_documento: str,
) -> Usuario | None:
    """Busca un usuario por el par único (tipo_documento, numero_documento)."""
    tipo = tipo_documento.value if isinstance(tipo_documento, TipoDocumento) else tipo_documento
    return db.execute(
        select(Usuario).where(
            Usuario.tipo_documento == tipo,
            Usuario.numero_documento == numero_documento,
        )
    ).scalar_one_or_none()


def crear(
    db: Session,
    *,
    tipo_documento: TipoDocumento,
    numero_documento: str,
    nombre: str,
    correo: str,
    tipo_participante: TipoParticipante | None,
    hash_password: str,
    rol: Rol,
    activo: bool = True,
) -> Usuario:
    """Persiste un nuevo usuario en la base de datos asegurando rollback ante conflicto."""
    usuario = Usuario(
        tipo_documento=tipo_documento.value,
        numero_documento=numero_documento,
        nombre=nombre,
        correo=correo,
        tipo_participante=tipo_participante.value if tipo_participante is not None else None,
        hash_password=hash_password,
        rol=rol.value,
        activo=activo,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(usuario)
    return usuario
