"""Registro de rutas web y reexportación del motor de plantillas Jinja2."""

from fastapi import APIRouter

from app.web import (
    asistencia,
    auth,
    catalogo,
    eventos,
    inscripciones,
    reportes,
)
from app.web.plantillas import templates

web_router = APIRouter(include_in_schema=False)
web_router.include_router(catalogo.router)
web_router.include_router(auth.router)
web_router.include_router(eventos.router)
web_router.include_router(inscripciones.router)
web_router.include_router(asistencia.router)
web_router.include_router(reportes.router)

__all__ = ["templates", "web_router"]
