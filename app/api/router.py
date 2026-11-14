"""Registro central de routers versionados (/api/v1)."""

from fastapi import APIRouter, Depends

from app.api.deps import verificar_csrf
from app.api.v1 import (
    asistencia,
    auth,
    catalogo,
    eventos,
    inscripciones,
    reportes,
)

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(verificar_csrf)])
api_router.include_router(auth.router)
api_router.include_router(eventos.router)
api_router.include_router(catalogo.router)
api_router.include_router(inscripciones.router)
api_router.include_router(asistencia.router)
api_router.include_router(reportes.router)
