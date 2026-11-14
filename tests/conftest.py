"""Fixtures base de pytest con base de datos temporal y cliente HTTPS."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Asegura configuración de pruebas segura antes de importar la aplicación.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SECRET_KEY",
    "clave-exclusiva-para-pruebas-automatizadas-pf04-debe-ser-larga-1234",
)
os.environ.setdefault("COOKIE_SECURE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_placeholder.db")


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Ruta a un archivo SQLite temporal aislado por prueba."""
    return tmp_path / "pf04_test.db"


@pytest.fixture()
def db_session(db_path: Path) -> Generator[Session, None, None]:
    """Sesión SQLAlchemy sobre SQLite en archivo temporal con claves foráneas activas."""
    import app.models  # noqa: F401 - registra todos los modelos en Base.metadata
    from app.core.database import Base

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _configurar_pragmas(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente de pruebas HTTPS con get_db sobrescrito hacia la BD temporal."""
    from app.core.database import get_db
    from app.main import app

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def crear_usuario_factory(db_session: Session):
    """Fábrica de usuarios ficticios para pruebas por rol."""
    from argon2 import PasswordHasher

    from app.models.enums import Rol, TipoDocumento, TipoParticipante
    from app.models.usuario import Usuario

    hasher = PasswordHasher()
    contador = 0

    def _crear(
        *,
        rol: Rol = Rol.PARTICIPANTE,
        tipo_documento: TipoDocumento = TipoDocumento.CC,
        numero_documento: str | None = None,
        nombre: str = "Usuario Prueba",
        correo: str = "usuario.prueba@example.edu",
        tipo_participante: TipoParticipante | None = TipoParticipante.ESTUDIANTE,
        password: str = "ClaveSegura123!",
        activo: bool = True,
    ) -> Usuario:
        nonlocal contador
        contador += 1
        doc = numero_documento or f"1000099{contador:03d}"
        tipo_part = tipo_participante if rol == Rol.PARTICIPANTE else None
        usuario = Usuario(
            tipo_documento=tipo_documento,
            numero_documento=doc,
            nombre=nombre,
            correo=correo,
            tipo_participante=tipo_part,
            hash_password=hasher.hash(password),
            rol=rol,
            activo=activo,
        )
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        return usuario

    return _crear


@pytest.fixture()
def usuario_participante(crear_usuario_factory):
    """Participante ficticio creado en BD temporal."""
    from app.models.enums import Rol

    return crear_usuario_factory(
        rol=Rol.PARTICIPANTE,
        numero_documento="1000000101",
        nombre="Participante Ficticio",
    )


@pytest.fixture()
def usuario_organizador(crear_usuario_factory):
    """Organizador ficticio creado en BD temporal."""
    from app.models.enums import Rol

    return crear_usuario_factory(
        rol=Rol.ORGANIZADOR,
        numero_documento="1000000102",
        nombre="Organizador Ficticio",
    )


@pytest.fixture()
def usuario_coordinacion(crear_usuario_factory):
    """Usuario de coordinación ficticio creado en BD temporal."""
    from app.models.enums import Rol

    return crear_usuario_factory(
        rol=Rol.COORDINACION,
        numero_documento="1000000103",
        nombre="Coordinacion Ficticia",
    )
