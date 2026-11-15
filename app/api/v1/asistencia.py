"""Router v1 de asistencia: registro, corrección y consulta con privacidad (E6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles, verificar_csrf
from app.core.database import get_db
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.schemas.asistencia import (
    AsistenciaRegistroEntrada,
    AsistenciaSalida,
    ParticipanteAsistenciaSalida,
)
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


@router.get(
    "/eventos/{evento_id}/asistencia",
    response_model=list[ParticipanteAsistenciaSalida],
    summary="Listar nómina de participantes con asistencia y privacidad diferencial",
)
def listar_asistencia(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[ParticipanteAsistenciaSalida]:
    """Organizador dueño ve documento completo; coordinación lo ve enmascarado."""
    return asistencia_service.listar_asistencia_evento(db, evento_id, usuario)
