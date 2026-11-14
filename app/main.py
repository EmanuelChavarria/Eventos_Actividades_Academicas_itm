"""Punto de entrada principal de la aplicación FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ErrorDominio, registrar_manejadores_errores
from app.core.logging import configurar_logging, registrar_middleware_logging
from app.web import web_router

DIRECTORIO_STATIC = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Valida la configuración obligatoria de seguridad al arrancar."""
    get_settings()
    yield


def crear_app() -> FastAPI:
    """Construye y configura la instancia FastAPI con routers, logging y manejadores."""
    settings = get_settings()
    configurar_logging(settings.LOG_LEVEL)
    aplicacion = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Plataforma para organización de eventos y actividades académicas.",
        lifespan=lifespan,
    )
    registrar_manejadores_errores(aplicacion)
    registrar_middleware_logging(aplicacion)
    aplicacion.mount("/static", StaticFiles(directory=str(DIRECTORIO_STATIC)), name="static")

    @aplicacion.get("/health", tags=["Plataforma"])
    def healthcheck(db: Session = Depends(get_db)) -> dict[str, str]:
        """Verifica disponibilidad de la aplicación y conectividad con SQLite."""
        try:
            db.execute(text("SELECT 1;")).scalar_one()
            fk_activo = db.execute(text("PRAGMA foreign_keys;")).scalar_one()
        except Exception as exc:
            raise ErrorDominio(
                codigo="BD_NO_DISPONIBLE",
                mensaje="La base de datos no está disponible.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        if fk_activo != 1:
            raise ErrorDominio(
                codigo="BD_INTEGRIDAD_INACTIVA",
                mensaje="Las claves foráneas de SQLite no están activas.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return {"status": "ok", "database": "ok"}

    aplicacion.include_router(api_router)
    aplicacion.include_router(web_router)
    return aplicacion


app = crear_app()
