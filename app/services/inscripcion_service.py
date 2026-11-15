"""Servicio de inscripciones: validaciones de dominio y orquestación de flujo."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import CodigosError, Conflicto, NoAutorizado, NoEncontrado
from app.core.fechas import ProveedorAhora, ahora_utc
from app.models.enums import EstadoEvento, EstadoInscripcion, PublicoObjetivo, Rol
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario
from app.repositories import inscripcion_repo
from app.schemas.inscripcion import (
    InscripcionDetalle,
    InscritoEnmascarado,
    InscritoSalida,
)


def _enmascarar_documento(numero: str) -> str:
    """Devuelve '••••' seguido de los últimos 4 dígitos del documento."""
    return f"••••{numero[-4:]}" if len(numero) >= 4 else "••••"


def inscribir(
    db: Session,
    evento_id: int,
    participante: Usuario,
    proveedor_ahora: ProveedorAhora = ahora_utc,
) -> Inscripcion:
    """Inscribe al participante en el evento validando todas las reglas de negocio.

    Reglas validadas:
      - RN-04: cupo atómico (BEGIN IMMEDIATE + inserción condicional)
      - RN-05: duplicado activo (índice único parcial → IntegrityError → 409)
      - RN-07: inscripciones_cerradas (fecha_limite_inscripcion)
      - RN-04/spec: evento publicado
      - RN-11: público objetivo
    """
    ahora = proveedor_ahora()

    # Verificar que el evento existe
    evento = inscripcion_repo.obtener_evento(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            codigo=CodigosError.EVENTO_NO_ENCONTRADO,
            mensaje="El evento solicitado no existe.",
        )

    # RN: evento debe estar publicado
    if evento.estado != EstadoEvento.PUBLICADO.value:
        raise Conflicto(
            codigo=CodigosError.EVENTO_NO_PUBLICADO,
            mensaje="Solo se puede inscribir en eventos publicados.",
        )

    # RN-07: inscripciones cerradas por fecha límite
    fecha_limite = evento.fecha_limite_inscripcion
    if isinstance(fecha_limite, str):
        from app.core.fechas import UTCDateTime  # noqa: PLC0415

        fecha_limite = UTCDateTime().process_result_value(fecha_limite, None)
    if ahora > fecha_limite:
        raise Conflicto(
            codigo=CodigosError.INSCRIPCIONES_CERRADAS,
            mensaje="El plazo de inscripción para este evento ha cerrado.",
        )

    # RN-11: público objetivo
    publico = evento.publico_objetivo
    if publico != PublicoObjetivo.TODOS.value:
        tipo_part = participante.tipo_participante or ""
        permitido = (
            publico == PublicoObjetivo.ESTUDIANTES.value and tipo_part == "estudiante"
        ) or (publico == PublicoObjetivo.DOCENTES.value and tipo_part == "docente")
        if not permitido:
            raise Conflicto(
                codigo=CodigosError.PUBLICO_NO_PERMITIDO,
                mensaje="Tu perfil no corresponde al público objetivo de este evento.",
            )

    # RN-05: duplicado activo (verificación previa para mensaje claro)
    if inscripcion_repo.tiene_inscripcion_activa(db, evento_id, participante.id):
        raise Conflicto(
            codigo=CodigosError.INSCRIPCION_DUPLICADA,
            mensaje="Ya tienes una inscripción activa en este evento.",
        )

    # RN-04: inserción atómica con BEGIN IMMEDIATE (puede lanzar CUPO_AGOTADO)
    try:
        return inscripcion_repo.insertar_atomica(db, evento_id, participante.id, ahora)
    except IntegrityError:
        db.rollback()
        # El índice parcial único disparó → inscripción duplicada concurrente
        raise Conflicto(
            codigo=CodigosError.INSCRIPCION_DUPLICADA,
            mensaje="Ya tienes una inscripción activa en este evento.",
        ) from None


def cancelar_inscripcion(
    db: Session,
    inscripcion_id: int,
    usuario: Usuario,
    proveedor_ahora: ProveedorAhora = ahora_utc,
) -> Inscripcion:
    """Cancela la inscripción propia antes del inicio del evento.

    Reglas validadas:
      - Propietario: inscripcion.participante_id == usuario.id
      - RN-07: cancelación permitida solo antes de fecha_inicio del evento
      - Inscripción debe estar activa
    """
    ahora = proveedor_ahora()

    inscripcion = inscripcion_repo.obtener_por_id(db, inscripcion_id)
    if inscripcion is None:
        raise NoEncontrado(
            codigo=CodigosError.INSCRIPCION_NO_ENCONTRADA,
            mensaje="Inscripción no encontrada.",
        )

    # Solo el propietario puede cancelar su inscripción
    if inscripcion.participante_id != usuario.id:
        raise NoAutorizado(
            codigo=CodigosError.SIN_PERMISO,
            mensaje="No puedes cancelar la inscripción de otro participante.",
        )

    if inscripcion.estado != EstadoInscripcion.ACTIVA.value:
        raise Conflicto(
            codigo=CodigosError.CANCELACION_NO_PERMITIDA,
            mensaje="Solo puedes cancelar inscripciones activas.",
        )

    # RN-07: solo antes de fecha_inicio del evento
    evento = inscripcion.evento
    fecha_inicio = evento.fecha_inicio
    if isinstance(fecha_inicio, str):
        from app.core.fechas import UTCDateTime  # noqa: PLC0415

        fecha_inicio = UTCDateTime().process_result_value(fecha_inicio, None)
    if ahora >= fecha_inicio:
        raise Conflicto(
            codigo=CodigosError.CANCELACION_NO_PERMITIDA,
            mensaje="Solo puedes cancelar antes de que el evento haya iniciado.",
        )

    return inscripcion_repo.cancelar(db, inscripcion, ahora)


def listar_mis_inscripciones(
    db: Session,
    participante: Usuario,
) -> list[InscripcionDetalle]:
    """Retorna todas las inscripciones del participante con detalle del evento.

    Incluye `titulo_evento`, `fecha_inicio_evento` y `estado_evento`
    (calculado: 'finalizado' si fecha_fin < ahora, 'cancelado' si el evento
    está cancelado, o el estado persistido del evento).
    """
    ahora = ahora_utc()
    inscripciones = inscripcion_repo.listar_de_participante(db, participante.id)

    resultado: list[InscripcionDetalle] = []
    for insc in inscripciones:
        evento = insc.evento
        if evento.fecha_fin < ahora:
            estado_evento = "finalizado"
        elif evento.estado == EstadoEvento.CANCELADO.value:
            estado_evento = "cancelado"
        else:
            estado_evento = evento.estado

        resultado.append(
            InscripcionDetalle(
                id=insc.id,
                evento_id=insc.evento_id,
                participante_id=insc.participante_id,
                estado=insc.estado,
                creado_en=insc.creado_en,
                cancelada_en=insc.cancelada_en,
                titulo_evento=evento.titulo,
                fecha_inicio_evento=evento.fecha_inicio,
                estado_evento=estado_evento,
            )
        )
    return resultado


def listar_inscritos(
    db: Session,
    evento_id: int,
    solicitante: Usuario,
) -> list[InscritoSalida | InscritoEnmascarado]:
    """Retorna la lista de inscritos con privacidad diferencial según el rol.

    - Organizador dueño: documento completo (InscritoSalida).
    - Coordinación: documento enmascarado (InscritoEnmascarado).
    - Cualquier otro: 403 SIN_PERMISO.
    """
    evento = inscripcion_repo.obtener_evento(db, evento_id)
    if evento is None:
        raise NoEncontrado(
            codigo=CodigosError.EVENTO_NO_ENCONTRADO,
            mensaje="El evento solicitado no existe.",
        )

    es_organizador_dueno = (
        solicitante.rol == Rol.ORGANIZADOR.value and evento.organizador_id == solicitante.id
    )
    es_coordinacion = solicitante.rol == Rol.COORDINACION.value

    if not (es_organizador_dueno or es_coordinacion):
        raise NoAutorizado(
            codigo=CodigosError.SIN_PERMISO,
            mensaje="No tienes permiso para ver la lista de inscritos.",
        )

    inscripciones = inscripcion_repo.listar_de_evento(db, evento_id)

    resultado: list[InscritoSalida | InscritoEnmascarado] = []
    for insc in inscripciones:
        part = insc.participante
        if es_organizador_dueno:
            resultado.append(
                InscritoSalida(
                    inscripcion_id=insc.id,
                    participante_id=part.id,
                    nombre=part.nombre,
                    numero_documento=part.numero_documento,
                    tipo_documento=part.tipo_documento,
                    estado=insc.estado,
                    creado_en=insc.creado_en,
                    cancelada_en=insc.cancelada_en,
                )
            )
        else:
            resultado.append(
                InscritoEnmascarado(
                    inscripcion_id=insc.id,
                    participante_id=part.id,
                    nombre=part.nombre,
                    numero_documento=_enmascarar_documento(part.numero_documento),
                    estado=insc.estado,
                    creado_en=insc.creado_en,
                    cancelada_en=insc.cancelada_en,
                )
            )
    return resultado


def _parsear_fecha(valor: datetime | str | None) -> datetime | None:
    """Convierte cadena ISO a datetime si es necesario."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    from app.core.fechas import UTCDateTime  # noqa: PLC0415

    return UTCDateTime().process_result_value(valor, None)
