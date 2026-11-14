"""Modelos ORM registrados en Base.metadata."""

from app.models.asistencia import Asistencia
from app.models.evento import Evento
from app.models.inscripcion import Inscripcion
from app.models.usuario import Usuario

__all__ = ["Asistencia", "Evento", "Inscripcion", "Usuario"]
