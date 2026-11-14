"""Enumeraciones oficiales del dominio (contrato compartido)."""

from __future__ import annotations

from enum import StrEnum


class Rol(StrEnum):
    """Roles de autorización en el sistema."""

    PARTICIPANTE = "participante"
    ORGANIZADOR = "organizador"
    COORDINACION = "coordinacion"


class TipoDocumento(StrEnum):
    """Tipos de documento aceptados para identificación única."""

    CC = "CC"
    CE = "CE"
    TI = "TI"
    PAS = "PAS"


class TipoParticipante(StrEnum):
    """Clasificación académica del participante."""

    ESTUDIANTE = "estudiante"
    DOCENTE = "docente"


class TipoEvento(StrEnum):
    """Categorías permitidas de eventos académicos."""

    CONFERENCIA = "conferencia"
    TALLER = "taller"
    SEMINARIO = "seminario"
    CAPACITACION = "capacitacion"


class Modalidad(StrEnum):
    """Modalidad de realización del evento."""

    PRESENCIAL = "presencial"
    VIRTUAL = "virtual"
    HIBRIDA = "hibrida"


class PublicoObjetivo(StrEnum):
    """Público habilitado para inscribirse en el evento."""

    TODOS = "todos"
    ESTUDIANTES = "estudiantes"
    DOCENTES = "docentes"


class EstadoEvento(StrEnum):
    """Estados persistidos del ciclo de vida de un evento."""

    BORRADOR = "borrador"
    PUBLICADO = "publicado"
    CANCELADO = "cancelado"


class EstadoInscripcion(StrEnum):
    """Estados posibles de una inscripción."""

    ACTIVA = "activa"
    CANCELADA = "cancelada"


class EstadoAsistencia(StrEnum):
    """Estados registrables de asistencia (sin registro = pendiente)."""

    PRESENTE = "presente"
    AUSENTE = "ausente"
