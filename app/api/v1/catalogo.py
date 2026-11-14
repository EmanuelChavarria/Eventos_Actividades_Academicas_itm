"""Router v1 del catálogo público (stub E1, implementación completa en E4)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get("/eventos", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def listar_catalogo_stub() -> None:
    """Stub E1 para catálogo público de eventos (implementación en E4)."""
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="El catálogo público se implementa en E4.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
