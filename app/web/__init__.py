"""Configuración común de Jinja2 y registro de rutas web."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.web import (
    asistencia,
    auth,
    catalogo,
    eventos,
    inscripciones,
    reportes,
)

DIRECTORIO_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(DIRECTORIO_TEMPLATES)),
    autoescape=select_autoescape(["html", "xml"]),
)
templates = Jinja2Templates(env=_jinja_env)

web_router = APIRouter(include_in_schema=False)
web_router.include_router(catalogo.router)
web_router.include_router(auth.router)
web_router.include_router(eventos.router)
web_router.include_router(inscripciones.router)
web_router.include_router(asistencia.router)
web_router.include_router(reportes.router)
