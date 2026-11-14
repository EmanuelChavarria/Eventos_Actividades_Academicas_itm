"""Router v1 de gestión de eventos (stub E1, implementación completa en E3)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def crear_evento_stub() -> None:
    """Stub E1 para creación de eventos (implementación en E3)."""
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="La gestión de eventos se implementa en E3.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
