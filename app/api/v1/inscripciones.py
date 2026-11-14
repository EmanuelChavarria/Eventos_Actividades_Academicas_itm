"""Router v1 de inscripciones (stub E1, implementación completa en E5)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(tags=["Inscripciones"])


@router.get("/inscripciones/mias", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def listar_mis_inscripciones_stub() -> None:
    """Stub E1 para consulta de inscripciones (implementación en E5)."""
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="El módulo de inscripciones se implementa en E5.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
