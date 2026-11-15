"""Router v1 de inscripciones: alta atómica, cancelación y consultas con privacidad."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles, verificar_csrf
from app.core.database import get_db
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.schemas.inscripcion import (
    InscripcionDetalle,
    InscripcionSalida,
    InscritoEnmascarado,
    InscritoSalida,
)
from app.services import inscripcion_service

router = APIRouter(tags=["Inscripciones"])


@router.post(
    "/eventos/{evento_id}/inscripciones",
    status_code=status.HTTP_201_CREATED,
    response_model=InscripcionSalida,
    summary="Inscribirse en un evento publicado",
)
def inscribirse(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.PARTICIPANTE)),
    _csrf: None = Depends(verificar_csrf),
) -> InscripcionSalida:
    """Inscribe al participante autenticado en el evento indicado.

    Responde 201 en éxito o 409 con código de dominio específico si falla.
    """
    inscripcion = inscripcion_service.inscribir(db, evento_id, usuario)
    return InscripcionSalida.model_validate(inscripcion)


@router.patch(
    "/inscripciones/{inscripcion_id}/cancelar",
    response_model=InscripcionSalida,
    summary="Cancelar inscripción propia antes del inicio del evento",
)
def cancelar_inscripcion(
    inscripcion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.PARTICIPANTE)),
    _csrf: None = Depends(verificar_csrf),
) -> InscripcionSalida:
    """Cancela la inscripción activa del participante si el evento aún no ha iniciado."""
    inscripcion = inscripcion_service.cancelar_inscripcion(db, inscripcion_id, usuario)
    return InscripcionSalida.model_validate(inscripcion)


@router.get(
    "/inscripciones/mias",
    response_model=list[InscripcionDetalle],
    summary="Listar mis inscripciones",
)
def listar_mis_inscripciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.PARTICIPANTE)),
) -> list[InscripcionDetalle]:
    """Retorna el historial completo de inscripciones del participante autenticado."""
    return inscripcion_service.listar_mis_inscripciones(db, usuario)


@router.get(
    "/eventos/{evento_id}/inscripciones",
    response_model=list[InscritoSalida] | list[InscritoEnmascarado],
    summary="Listar inscritos de un evento con privacidad diferencial",
)
def listar_inscritos(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[InscritoSalida] | list[InscritoEnmascarado]:
    """Organizador dueño ve documento completo; coordinación lo ve enmascarado."""
    return inscripcion_service.listar_inscritos(db, evento_id, usuario)
