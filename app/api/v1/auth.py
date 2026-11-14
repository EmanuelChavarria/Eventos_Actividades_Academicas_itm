"""Router v1 de autenticación y registro (stub E1, implementación completa en E2)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.get("/yo", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def obtener_usuario_actual_stub() -> None:
    """Stub E1 para consulta de sesión actual (implementación en E2)."""
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="El módulo de autenticación se implementa en E2.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
