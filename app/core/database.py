"""Configuración de SQLAlchemy, sesión por solicitud y PRAGMAs de SQLite."""

from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import dotenv_values
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM del dominio."""


def configurar_pragmas_sqlite(target_engine: Engine, *, usar_wal: bool = True) -> None:
    """Registra PRAGMAs obligatorios por conexión en SQLite."""

    @event.listens_for(target_engine, "connect")
    def _on_connect(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        if usar_wal:
            cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


def crear_motor(database_url: str) -> Engine:
    """Crea el Engine SQLAlchemy aplicando opciones específicas de SQLite."""
    es_sqlite = database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if es_sqlite else {}
    motor = create_engine(database_url, connect_args=connect_args)
    if es_sqlite:
        configurar_pragmas_sqlite(motor, usar_wal=":memory:" not in database_url)
    return motor


def _obtener_database_url() -> str:
    """Obtiene DATABASE_URL desde entorno o .env sin exigir secretos web en migraciones."""
    url_env = os.getenv("DATABASE_URL")
    if url_env:
        return url_env
    valores_dotenv = dotenv_values(".env")
    if valores_dotenv.get("DATABASE_URL"):
        return str(valores_dotenv["DATABASE_URL"])
    return "sqlite:///./eventos.db"


engine = crear_motor(_obtener_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee una sesión de BD cerrada al finalizar la petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
