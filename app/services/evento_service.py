"""Servicio de dominio para creación, edición, publicación, cancelación y consulta de eventos."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.core import fechas
from app.core.errors import CodigosError, Conflicto, NoAutorizado, NoEncontrado, ReglaNegocio
from app.models.enums import EstadoEvento
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.repositories import evento_repo, inscripcion_repo
from app.schemas.evento import (
    EventoActualizar,
    EventoCancelar,
    EventoCrear,
    EventoSalida,
    validar_coherencia_fechas,
)


def calcular_estado_efectivo(evento: Evento, ahora: datetime | None = None) -> str:
    """Devuelve `finalizado` si un evento publicado ya superó su `fecha_fin` en UTC."""
    referencia = fechas.asegurar_utc(ahora) if ahora is not None else fechas.ahora_utc()
    if (
        evento.estado == EstadoEvento.PUBLICADO.value
        and fechas.asegurar_utc(evento.fecha_fin) < referencia
    ):
        return "finalizado"
    return evento.estado


def _construir_salida(
    evento: Evento,
    inscripciones_activas: int,
    *,
    ahora: datetime | None = None,
) -> EventoSalida:
    """Ensambla `EventoSalida` con estado efectivo e indicadores de cupo calculados."""
    referencia = fechas.asegurar_utc(ahora) if ahora is not None else fechas.ahora_utc()
    estado_efectivo = calcular_estado_efectivo(evento, referencia)
    cupos_disponibles = max(evento.cupo_maximo - inscripciones_activas, 0)
    inscripciones_abiertas = (
        estado_efectivo == EstadoEvento.PUBLICADO.value
        and fechas.asegurar_utc(evento.fecha_limite_inscripcion) > referencia
        and cupos_disponibles > 0
    )
    datos = {columna.name: getattr(evento, columna.name) for columna in Evento.__table__.columns}
    datos.update(
        {
            "estado_efectivo": estado_efectivo,
            "inscripciones_abiertas": inscripciones_abiertas,
            "inscripciones_activas": inscripciones_activas,
            "cupos_disponibles": cupos_disponibles,
        }
    )
    return EventoSalida.model_validate(datos)


def _obtener_evento_del_organizador(db: Session, evento_id: int, usuario: Usuario) -> Evento:
    """Obtiene un evento y exige propiedad estricta del organizador autenticado (RN-10)."""
    evento = evento_repo.obtener_por_id(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            CodigosError.EVENTO_NO_ENCONTRADO,
            "El evento solicitado no existe.",
        )
    if evento.organizador_id != usuario.id:
        raise NoAutorizado(
            CodigosError.SIN_PERMISO,
            "No tienes permiso para gestionar este evento.",
        )
    return evento


def _serializar_campos(modelo_pydantic: EventoCrear | EventoActualizar, *, parcial: bool) -> dict:
    """Extrae campos validados convirtiendo enums a su valor persistible."""
    bruto = modelo_pydantic.model_dump(exclude_unset=parcial)
    return {
        clave: (valor.value if isinstance(valor, Enum) else valor) for clave, valor in bruto.items()
    }


def crear_evento(db: Session, usuario: Usuario, datos: EventoCrear) -> EventoSalida:
    """Crea un evento en estado `borrador` asignado al organizador autenticado (RF-05)."""
    campos = _serializar_campos(datos, parcial=False)
    evento = Evento(
        **campos,
        estado=EstadoEvento.BORRADOR.value,
        organizador_id=usuario.id,
    )
    creado = evento_repo.crear(db, evento)
    return _construir_salida(creado, 0)


def obtener_evento_propio(db: Session, usuario: Usuario, evento_id: int) -> EventoSalida:
    """Devuelve el detalle de gestión de un evento perteneciente al organizador."""
    evento = _obtener_evento_del_organizador(db, evento_id, usuario)
    activas = inscripcion_repo.contar_activas(db, evento.id)
    return _construir_salida(evento, activas)


def listar_eventos_organizador(db: Session, usuario: Usuario) -> list[EventoSalida]:
    """Lista los eventos propios del organizador con conteo agregado de inscripciones."""
    eventos = evento_repo.listar_por_organizador(db, usuario.id)
    if not eventos:
        return []
    ahora = fechas.ahora_utc()
    conteos = inscripcion_repo.contar_activas_por_eventos(db, [ev.id for ev in eventos])
    return [_construir_salida(ev, conteos.get(ev.id, 0), ahora=ahora) for ev in eventos]


def actualizar_evento(
    db: Session,
    usuario: Usuario,
    evento_id: int,
    datos: EventoActualizar,
) -> EventoSalida:
    """Edita campos de un evento activo validando fechas combinadas y cupo mínimo (RN-09)."""
    evento = _obtener_evento_del_organizador(db, evento_id, usuario)
    ahora = fechas.ahora_utc()
    estado_efectivo = calcular_estado_efectivo(evento, ahora)
    if estado_efectivo in {EstadoEvento.CANCELADO.value, "finalizado"}:
        raise Conflicto(
            CodigosError.REGLA_NEGOCIO,
            "No se puede editar un evento cancelado o finalizado.",
        )

    cambios = _serializar_campos(datos, parcial=True)
    for clave, valor in cambios.items():
        if clave not in {"ponente", "requisitos"} and valor is None:
            raise ReglaNegocio(
                CodigosError.ERROR_VALIDACION,
                f"El campo '{clave}' no puede enviarse nulo.",
            )

    fecha_inicio = cambios.get("fecha_inicio", evento.fecha_inicio)
    fecha_fin = cambios.get("fecha_fin", evento.fecha_fin)
    fecha_limite = cambios.get("fecha_limite_inscripcion", evento.fecha_limite_inscripcion)
    try:
        validar_coherencia_fechas(fecha_inicio, fecha_fin, fecha_limite)
    except ValueError as exc:
        raise ReglaNegocio(CodigosError.REGLA_NEGOCIO, str(exc)) from exc

    activas = inscripcion_repo.contar_activas(db, evento.id)
    nuevo_cupo = cambios.get("cupo_maximo")
    if nuevo_cupo is not None and nuevo_cupo < activas:
        raise Conflicto(
            CodigosError.REGLA_NEGOCIO,
            f"El cupo máximo no puede ser inferior a las inscripciones activas ({activas}).",
        )

    for clave, valor in cambios.items():
        setattr(evento, clave, valor)

    actualizado = evento_repo.guardar(db, evento)
    return _construir_salida(actualizado, activas, ahora=ahora)


def publicar_evento(db: Session, usuario: Usuario, evento_id: int) -> EventoSalida:
    """Publica directamente un evento en `borrador` sin flujo de aprobación previo (RN-20)."""
    evento = _obtener_evento_del_organizador(db, evento_id, usuario)
    if evento.estado != EstadoEvento.BORRADOR.value:
        raise Conflicto(
            CodigosError.REGLA_NEGOCIO,
            "Solo se pueden publicar eventos en estado borrador.",
        )

    ahora = fechas.ahora_utc()
    if evento.cupo_maximo < 1:
        raise ReglaNegocio(
            CodigosError.REGLA_NEGOCIO,
            "El cupo máximo debe ser al menos 1 para publicar el evento.",
        )
    try:
        validar_coherencia_fechas(
            evento.fecha_inicio,
            evento.fecha_fin,
            evento.fecha_limite_inscripcion,
        )
    except ValueError as exc:
        raise ReglaNegocio(CodigosError.REGLA_NEGOCIO, str(exc)) from exc

    if fechas.asegurar_utc(evento.fecha_inicio) <= ahora:
        raise ReglaNegocio(
            CodigosError.REGLA_NEGOCIO,
            "La fecha de inicio debe ser futura para publicar el evento.",
        )

    evento.estado = EstadoEvento.PUBLICADO.value
    publicado = evento_repo.guardar(db, evento)
    activas = inscripcion_repo.contar_activas(db, publicado.id)
    return _construir_salida(publicado, activas, ahora=ahora)


def cancelar_evento(
    db: Session,
    usuario: Usuario,
    evento_id: int,
    datos: EventoCancelar,
) -> EventoSalida:
    """Cancela un evento publicado no finalizado guardando motivo y conservando inscripciones."""
    evento = _obtener_evento_del_organizador(db, evento_id, usuario)
    ahora = fechas.ahora_utc()
    if calcular_estado_efectivo(evento, ahora) != EstadoEvento.PUBLICADO.value:
        raise Conflicto(
            CodigosError.CANCELACION_NO_PERMITIDA,
            "Solo se pueden cancelar eventos publicados que no hayan finalizado.",
        )

    evento.estado = EstadoEvento.CANCELADO.value
    evento.motivo_cancelacion = datos.motivo
    cancelado = evento_repo.guardar(db, evento)
    activas = inscripcion_repo.contar_activas(db, cancelado.id)
    return _construir_salida(cancelado, activas, ahora=ahora)
