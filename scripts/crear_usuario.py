"""Script administrativo para crear cuentas de organizador o coordinación."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

if __name__ == "__main__":
    raiz_real = Path(__file__).resolve().parent.parent
    if str(raiz_real) not in sys.path:
        sys.path.insert(0, str(raiz_real))

from app.core.database import SessionLocal
from app.core.errors import CodigosError, Conflicto, ReglaNegocio
from app.core.security import (
    hashear_password,
)
from app.core.security import (
    normalizar_y_validar_documento as _normalizar_documento_core,
)
from app.models.enums import Rol, TipoDocumento
from app.models.usuario import Usuario

_ROLES_PERSONAL = {Rol.ORGANIZADOR, Rol.COORDINACION}


def normalizar_y_validar_documento(
    tipo_documento: TipoDocumento,
    numero_documento: str,
) -> str:
    """Normaliza sin espacios ni puntos y valida el formato según tipo de documento."""
    try:
        return _normalizar_documento_core(tipo_documento, numero_documento)
    except ValueError as exc:
        raise ReglaNegocio(mensaje=str(exc)) from exc


def crear_personal(
    db: Session,
    *,
    rol: Rol,
    tipo_documento: TipoDocumento,
    numero_documento: str,
    nombre: str,
    correo: str,
    password: str,
) -> Usuario:
    """Crea una cuenta administrativa (organizador o coordinación) validando documento único."""
    if rol not in _ROLES_PERSONAL:
        raise ReglaNegocio(mensaje="Este script solo crea cuentas de organizador o coordinación.")

    doc_normalizado = normalizar_y_validar_documento(tipo_documento, numero_documento)
    nombre_limpio = nombre.strip()
    if len(nombre_limpio) < 2:
        raise ReglaNegocio(mensaje="El nombre debe tener al menos 2 caracteres.")

    try:
        correo_validado = validate_email(correo.strip(), check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ReglaNegocio(mensaje="El formato del correo electrónico no es válido.") from exc

    if len(password) < 8:
        raise ReglaNegocio(mensaje="La contraseña debe tener al menos 8 caracteres.")

    existente = db.execute(
        select(Usuario).where(
            Usuario.tipo_documento == tipo_documento.value,
            Usuario.numero_documento == doc_normalizado,
        )
    ).scalar_one_or_none()
    if existente is not None:
        raise Conflicto(
            codigo=CodigosError.DOCUMENTO_DUPLICADO,
            mensaje="Ya existe una cuenta registrada con ese tipo y número de documento.",
        )

    usuario = Usuario(
        tipo_documento=tipo_documento.value,
        numero_documento=doc_normalizado,
        nombre=nombre_limpio,
        correo=correo_validado,
        tipo_participante=None,
        hash_password=hashear_password(password),
        rol=rol.value,
        activo=True,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflicto(
            codigo=CodigosError.DOCUMENTO_DUPLICADO,
            mensaje="Ya existe una cuenta registrada con ese tipo y número de documento.",
        ) from exc

    db.refresh(usuario)
    return usuario


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crea cuentas administrativas de organizador o coordinación.",
    )
    parser.add_argument("--rol", choices=["organizador", "coordinacion"])
    parser.add_argument("--tipo-documento", choices=["CC", "CE", "TI", "PAS"])
    parser.add_argument("--numero-documento")
    parser.add_argument("--nombre")
    parser.add_argument("--correo")
    parser.add_argument("--password", help="Opcional; si se omite se solicita sin eco.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Interfaz CLI interactiva/parametrizada para crear personal autorizado."""
    args = _parsear_argumentos(argv)
    rol_str = args.rol or input("Rol (organizador/coordinacion): ").strip().lower()
    tipo_str = args.tipo_documento or input("Tipo de documento (CC/CE/TI/PAS): ").strip().upper()
    numero_doc = args.numero_documento or input("Número de documento: ").strip()
    nombre = args.nombre or input("Nombre completo: ").strip()
    correo = args.correo or input("Correo de contacto: ").strip()
    password = args.password or getpass.getpass("Contraseña (mínimo 8 caracteres): ")

    try:
        rol = Rol(rol_str)
        tipo_doc = TipoDocumento(tipo_str)
        with SessionLocal() as db:
            creado = crear_personal(
                db,
                rol=rol,
                tipo_documento=tipo_doc,
                numero_documento=numero_doc,
                nombre=nombre,
                correo=correo,
                password=password,
            )
    except (ValueError, Conflicto, ReglaNegocio) as exc:
        print(f"Error al crear usuario: {exc}", file=sys.stderr)
        return 1

    print(f"Usuario administrativo creado: id={creado.id}, rol={creado.rol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
