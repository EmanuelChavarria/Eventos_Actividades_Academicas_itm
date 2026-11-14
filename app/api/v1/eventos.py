"""Endpoints REST de gestión de eventos para el rol organizador (E3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.schemas.evento import (
    EventoActualizar,
    EventoCancelar,
    EventoCrear,
    EventoSalida,
)
from app.services import evento_service

router = APIRouter(prefix="/eventos", tags=["eventos"])
organizador_router = APIRouter(prefix="/organizador", tags=["eventos"])


@router.post(
    "",
    response_model=EventoSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un evento en borrador",
)
def crear_evento(
    datos: EventoCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> EventoSalida:
    """Crea una actividad académica en estado `borrador` asignada al organizador actual."""
    return evento_service.crear_evento(db, usuario, datos)


@router.get(
    "/{evento_id}",
    response_model=EventoSalida,
    summary="Obtener detalle de gestión de un evento propio",
)
def obtener_evento_propio(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> EventoSalida:
    """Devuelve el detalle de un evento perteneciente al organizador autenticado."""
    return evento_service.obtener_evento_propio(db, usuario, evento_id)


@router.patch(
    "/{evento_id}",
    response_model=EventoSalida,
    summary="Editar un evento propio",
)
def actualizar_evento(
    evento_id: int,
    datos: EventoActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> EventoSalida:
    """Actualiza datos o cupo de un evento propio no cancelado ni finalizado."""
    return evento_service.actualizar_evento(db, usuario, evento_id, datos)


@router.post(
    "/{evento_id}/publicar",
    response_model=EventoSalida,
    summary="Publicar directamente un evento propio",
)
def publicar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> EventoSalida:
    """Publica un evento en `borrador` sin aprobación previa si cumple fechas y cupo."""
    return evento_service.publicar_evento(db, usuario, evento_id)


@router.post(
    "/{evento_id}/cancelar",
    response_model=EventoSalida,
    summary="Cancelar un evento publicado indicando motivo",
)
def cancelar_evento(
    evento_id: int,
    datos: EventoCancelar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> EventoSalida:
    """Cancela un evento publicado no finalizado conservando sus inscripciones."""
    return evento_service.cancelar_evento(db, usuario, evento_id, datos)


@organizador_router.get(
    "/eventos",
    response_model=list[EventoSalida],
    summary="Listar eventos del organizador autenticado",
)
def listar_eventos_organizador(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles(Rol.ORGANIZADOR)),
) -> list[EventoSalida]:
    """Lista los eventos propios del organizador con estado efectivo y ocupación."""
    return evento_service.listar_eventos_organizador(db, usuario)
