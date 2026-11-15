"""Router v1 de asistencia: registro, corrección y consulta con privacidad (E6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles, verificar_csrf
from app.core.database import get_db
from app.core.errors import CodigosError, ErrorDominio
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.schemas.asistencia import AsistenciaRegistroEntrada, AsistenciaSalida
from app.services import asistencia_service

router = APIRouter(tags=["Asistencia"])


@router.put(
    "/eventos/{evento_id}/inscripciones/{inscripcion_id}/asistencia",
    response_model=AsistenciaSalida,
    summary="Registrar o corregir asistencia de una inscripción activa",
)
def registrar_o_corregir_asistencia(
    evento_id: int,
    inscripcion_id: int,
    datos: AsistenciaRegistroEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
    _csrf: None = Depends(verificar_csrf),
) -> AsistenciaSalida:
    """Registra o corrige asistencia dentro de la ventana válida (inicio hasta +48 h)."""
    asistencia = asistencia_service.registrar_asistencia(
        db,
        evento_id,
        inscripcion_id,
        datos.estado,
        usuario,
    )
    return AsistenciaSalida.model_validate(asistencia)


@router.get("/eventos/{evento_id}/asistencia", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def listar_asistencia_stub(evento_id: int) -> None:
    """Stub E1 para consulta de asistencia (implementación en T-006-05)."""
    _ = evento_id
    raise ErrorDominio(
        codigo=CodigosError.NO_IMPLEMENTADO,
        mensaje="La consulta de asistencia se implementa en T-006-05.",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
