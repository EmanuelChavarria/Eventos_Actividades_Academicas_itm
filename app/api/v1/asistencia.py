"""Router v1 de asistencia (stub E1, implementación completa en E6)."""

from fastapi import APIRouter, status

from app.core.errors import CodigosError, ErrorDominio

router = APIRouter(tags=["Asistencia"])


@router.get("/eventos/{evento_id}/asistencia", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def listar_asistencia_stub(evento_id: int) -> None:
    """Stub E1 para consulta de asistencia (implementación en E6)."""
    _ = evento_id
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="El módulo de asistencia se implementa en E6.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
