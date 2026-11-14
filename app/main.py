"""Punto de entrada principal de la aplicación FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import registrar_manejadores_errores
from app.web import web_router

DIRECTORIO_STATIC = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Valida la configuración obligatoria de seguridad al arrancar."""
    get_settings()
    yield


def crear_app() -> FastAPI:
    """Construye y configura la instancia FastAPI con routers y manejadores."""
    settings = get_settings()
    aplicacion = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Plataforma para organización de eventos y actividades académicas.",
        lifespan=lifespan,
    )
    registrar_manejadores_errores(aplicacion)
    aplicacion.mount("/static", StaticFiles(directory=str(DIRECTORIO_STATIC)), name="static")
    aplicacion.include_router(api_router)
    aplicacion.include_router(web_router)
    return aplicacion


app = crear_app()
