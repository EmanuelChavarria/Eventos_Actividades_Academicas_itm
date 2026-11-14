"""Configuración de entorno de migraciones Alembic para SQLite."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401 - registra todos los modelos en Base.metadata
from app.core.config import get_settings
from app.core.database import Base, configurar_pragmas_sqlite

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def obtener_url_bd() -> str:
    """Obtiene la URL de BD desde Alembic, variable de entorno o Settings."""
    url_config = config.get_main_option("sqlalchemy.url")
    if url_config:
        return url_config
    url_env = os.getenv("DATABASE_URL")
    if url_env:
        return url_env
    return get_settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""
    url = obtener_url_bd()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online con PRAGMAs SQLite activos."""
    seccion = config.get_section(config.config_ini_section, {})
    url = obtener_url_bd()
    seccion["sqlalchemy.url"] = url

    connectable = engine_from_config(
        seccion,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    if url.startswith("sqlite"):
        configurar_pragmas_sqlite(connectable, usar_wal=":memory:" not in url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
