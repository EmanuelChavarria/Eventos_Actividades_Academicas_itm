"""Router v1 de reportes y consolidado (stub E1, implementación completa en E7)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/consolidado", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def obtener_consolidado_stub() -> None:
    """Stub E1 para reporte consolidado (implementación en E7)."""
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="El módulo de reportes se implementa en E7.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
