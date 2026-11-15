"""Servicio de asistencia: reglas de ventana 48 h, permisos y privacidad (E6)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import CodigosError, Conflicto, NoAutorizado, NoEncontrado
from app.core.fechas import ProveedorAhora, ahora_utc, esta_en_ventana_asistencia
from app.models.asistencia import Asistencia
from app.models.enums import EstadoAsistencia, EstadoEvento, EstadoInscripcion, Rol
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.repositories import asistencia_repo
from app.schemas.asistencia import ParticipanteAsistenciaSalida


def _enmascarar_documento(numero: str) -> str:
    """Devuelve '••••' seguido de los últimos 4 dígitos del documento."""
    return f"••••{numero[-4:]}" if len(numero) >= 4 else "••••"


def _verificar_organizador_dueno(evento: Evento, usuario: Usuario) -> None:
    """Exige que el usuario sea el organizador propietario del evento."""
    if usuario.rol != Rol.ORGANIZADOR.value or evento.organizador_id != usuario.id:
        raise NoAutorizado(
            codigo=CodigosError.SIN_PERMISO,
            mensaje="Solo el organizador propietario del evento puede registrar asistencia.",
        )


def registrar_asistencia(
    db: Session,
    evento_id: int,
    inscripcion_id: int,
    estado: EstadoAsistencia,
    usuario: Usuario,
    proveedor_ahora: ProveedorAhora = ahora_utc,
) -> Asistencia:
    """Registra o corrige asistencia validando propiedad, estados y ventana de 48 h."""
    evento = asistencia_repo.obtener_evento(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            codigo=CodigosError.EVENTO_NO_ENCONTRADO,
            mensaje="El evento solicitado no existe.",
        )

    _verificar_organizador_dueno(evento, usuario)

    inscripcion = asistencia_repo.obtener_inscripcion_de_evento(db, evento_id, inscripcion_id)
    if inscripcion is None:
        raise NoEncontrado(
            codigo=CodigosError.INSCRIPCION_NO_ENCONTRADA,
            mensaje="La inscripción solicitada no existe en este evento.",
        )

    if evento.estado != EstadoEvento.PUBLICADO.value:
        raise Conflicto(
            codigo=CodigosError.ASISTENCIA_NO_PERMITIDA,
            mensaje="No se puede registrar asistencia en un evento que no está publicado.",
        )

    if inscripcion.estado != EstadoInscripcion.ACTIVA.value:
        raise Conflicto(
            codigo=CodigosError.ASISTENCIA_NO_PERMITIDA,
            mensaje="Solo se puede registrar asistencia para inscripciones activas.",
        )

    ahora = proveedor_ahora()
    if not esta_en_ventana_asistencia(evento.fecha_inicio, evento.fecha_fin, ahora=ahora):
        raise Conflicto(
            codigo=CodigosError.ASISTENCIA_NO_PERMITIDA,
            mensaje=(
                "La asistencia solo puede registrarse desde el inicio del evento "
                "hasta 48 horas después de finalizar."
            ),
        )

    return asistencia_repo.registrar_o_actualizar(
        db,
        inscripcion_id=inscripcion.id,
        estado=estado.value,
        usuario_id=usuario.id,
        ahora=ahora,
    )


def listar_asistencia_evento(
    db: Session,
    evento_id: int,
    solicitante: Usuario,
) -> list[ParticipanteAsistenciaSalida]:
    """Lista la nómina con estado de asistencia y enmascaramiento diferencial por rol."""
    evento = asistencia_repo.obtener_evento(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            codigo=CodigosError.EVENTO_NO_ENCONTRADO,
            mensaje="El evento solicitado no existe.",
        )

    es_dueno = solicitante.rol == Rol.ORGANIZADOR.value and evento.organizador_id == solicitante.id
    es_coordinacion = solicitante.rol == Rol.COORDINACION.value
    if not (es_dueno or es_coordinacion):
        raise NoAutorizado(
            codigo=CodigosError.SIN_PERMISO,
            mensaje="No tienes permiso para consultar la asistencia de este evento.",
        )

    filas = asistencia_repo.listar_nomina_con_asistencia(db, evento_id)
    resultado: list[ParticipanteAsistenciaSalida] = []
    for insc, participante, asist in filas:
        documento = (
            participante.numero_documento
            if es_dueno
            else _enmascarar_documento(participante.numero_documento)
        )
        resultado.append(
            ParticipanteAsistenciaSalida(
                inscripcion_id=insc.id,
                participante_id=participante.id,
                nombre=participante.nombre,
                correo=participante.correo,
                tipo_documento=participante.tipo_documento,
                numero_documento=documento,
                estado_inscripcion=insc.estado,
                estado_asistencia=asist.estado if asist is not None else "pendiente",
                asistencia_id=asist.id if asist is not None else None,
                registrado_por_id=asist.registrado_por_id if asist is not None else None,
                registrado_en=asist.registrado_en if asist is not None else None,
                actualizado_en=asist.actualizado_en if asist is not None else None,
            )
        )
    return resultado
