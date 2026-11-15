"""Consultas agregadas en SQLite para el reporte consolidado de coordinación (E7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.core.fechas import asegurar_utc
from app.models.asistencia import Asistencia
from app.models.enums import EstadoAsistencia, EstadoEvento, EstadoInscripcion, Rol
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.repositories.evento_repo import escapar_like
from app.schemas.reporte import ConsolidadoFiltros


@dataclass(frozen=True)
class FilaConsolidadoEvento:
    """Proyección agregada por evento devuelta por la consulta SQL consolidada."""

    evento_id: int
    titulo: str
    tipo: str
    modalidad: str
    estado_almacenado: str
    fecha_inicio: datetime
    fecha_fin: datetime
    organizador_id: int
    organizador_nombre: str
    cupo_maximo: int
    inscritos_activos: int
    cancelaciones: int
    presentes: int
    ausentes: int


def obtener_consolidado_eventos(
    db: Session,
    filtros: ConsolidadoFiltros,
    ahora: datetime,
) -> list[FilaConsolidadoEvento]:
    """Obtiene métricas de inscripción y asistencia agregadas por evento en una sola consulta."""
    ahora_utc = asegurar_utc(ahora)
    condiciones = []

    if filtros.fecha_desde is not None:
        condiciones.append(Evento.fecha_inicio >= asegurar_utc(filtros.fecha_desde))
    if filtros.fecha_hasta is not None:
        condiciones.append(Evento.fecha_inicio <= asegurar_utc(filtros.fecha_hasta))
    if filtros.tipo is not None:
        condiciones.append(Evento.tipo == filtros.tipo.value)
    if filtros.modalidad is not None:
        condiciones.append(Evento.modalidad == filtros.modalidad.value)
    if filtros.organizador_id is not None:
        condiciones.append(Evento.organizador_id == filtros.organizador_id)
    if filtros.estado is not None:
        if filtros.estado == "finalizado":
            condiciones.extend(
                [
                    Evento.estado == EstadoEvento.PUBLICADO.value,
                    Evento.fecha_fin < ahora_utc,
                ]
            )
        elif filtros.estado == "publicado":
            condiciones.extend(
                [
                    Evento.estado == EstadoEvento.PUBLICADO.value,
                    Evento.fecha_fin >= ahora_utc,
                ]
            )
        else:
            condiciones.append(Evento.estado == filtros.estado)
    if filtros.texto is not None:
        patron = f"%{escapar_like(filtros.texto)}%"
        condiciones.append(
            or_(
                Evento.titulo.ilike(patron, escape="\\"),
                Evento.descripcion.ilike(patron, escape="\\"),
                Usuario.nombre.ilike(patron, escape="\\"),
            )
        )

    inscritos_activos = func.coalesce(
        func.sum(case((Inscripcion.estado == EstadoInscripcion.ACTIVA.value, 1), else_=0)),
        0,
    ).label("inscritos_activos")
    cancelaciones = func.coalesce(
        func.sum(case((Inscripcion.estado == EstadoInscripcion.CANCELADA.value, 1), else_=0)),
        0,
    ).label("cancelaciones")
    presentes = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
                        Asistencia.estado == EstadoAsistencia.PRESENTE.value,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    ).label("presentes")
    ausentes = func.coalesce(
        func.sum(
            case(
                (
                    and_(
                        Inscripcion.estado == EstadoInscripcion.ACTIVA.value,
                        Asistencia.estado == EstadoAsistencia.AUSENTE.value,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        0,
    ).label("ausentes")

    consulta = (
        select(
            Evento.id.label("evento_id"),
            Evento.titulo.label("titulo"),
            Evento.tipo.label("tipo"),
            Evento.modalidad.label("modalidad"),
            Evento.estado.label("estado_almacenado"),
            Evento.fecha_inicio.label("fecha_inicio"),
            Evento.fecha_fin.label("fecha_fin"),
            Evento.organizador_id.label("organizador_id"),
            Usuario.nombre.label("organizador_nombre"),
            Evento.cupo_maximo.label("cupo_maximo"),
            inscritos_activos,
            cancelaciones,
            presentes,
            ausentes,
        )
        .join(Usuario, Usuario.id == Evento.organizador_id)
        .outerjoin(Inscripcion, Inscripcion.evento_id == Evento.id)
        .outerjoin(Asistencia, Asistencia.inscripcion_id == Inscripcion.id)
        .where(*condiciones)
        .group_by(Evento.id, Usuario.nombre)
        .order_by(Evento.fecha_inicio.asc(), Evento.id.asc())
    )

    filas = db.execute(consulta).all()
    return [
        FilaConsolidadoEvento(
            evento_id=fila.evento_id,
            titulo=fila.titulo,
            tipo=fila.tipo,
            modalidad=fila.modalidad,
            estado_almacenado=fila.estado_almacenado,
            fecha_inicio=asegurar_utc(fila.fecha_inicio),
            fecha_fin=asegurar_utc(fila.fecha_fin),
            organizador_id=fila.organizador_id,
            organizador_nombre=fila.organizador_nombre,
            cupo_maximo=int(fila.cupo_maximo),
            inscritos_activos=int(fila.inscritos_activos),
            cancelaciones=int(fila.cancelaciones),
            presentes=int(fila.presentes),
            ausentes=int(fila.ausentes),
        )
        for fila in filas
    ]


def listar_organizadores(db: Session) -> list[tuple[int, str]]:
    """Devuelve pares (id, nombre) de organizadores ordenados alfabéticamente."""
    consulta = (
        select(Usuario.id, Usuario.nombre)
        .where(Usuario.rol == Rol.ORGANIZADOR.value)
        .order_by(Usuario.nombre.asc(), Usuario.id.asc())
    )
    return [(int(row.id), str(row.nombre)) for row in db.execute(consulta).all()]
