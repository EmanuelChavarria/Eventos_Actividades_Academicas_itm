"""Schemas Pydantic v2 para registro, inicio de sesión y salida pública de usuario."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.security import normalizar_y_validar_documento
from app.models.enums import Rol, TipoDocumento, TipoParticipante


class _DocumentoEntradaBase(BaseModel):
    """Base compartida para validar y normalizar documento sin campos extra."""

    model_config = ConfigDict(extra="forbid")

    tipo_documento: TipoDocumento
    numero_documento: str = Field(min_length=5, max_length=30)

    @model_validator(mode="after")
    def _normalizar_documento(self) -> _DocumentoEntradaBase:
        self.numero_documento = normalizar_y_validar_documento(
            self.tipo_documento,
            self.numero_documento,
        )
        return self


class RegistroEntrada(_DocumentoEntradaBase):
    """Datos requeridos para registrar públicamente a un participante (RF-01, RN-21)."""

    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr = Field(max_length=150)
    tipo_participante: TipoParticipante
    password: str = Field(min_length=8, max_length=128)

    @field_validator("nombre")
    @classmethod
    def _limpiar_nombre(cls, valor: str) -> str:
        limpio = " ".join(valor.split())
        if len(limpio) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        return limpio


class LoginEntrada(_DocumentoEntradaBase):
    """Credenciales de inicio de sesión mediante documento y contraseña (RF-02)."""

    password: str = Field(min_length=1, max_length=128)


class UsuarioSalida(BaseModel):
    """Representación pública segura del usuario sin exponer el hash de contraseña."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_documento: TipoDocumento
    numero_documento: str
    nombre: str
    correo: str
    tipo_participante: TipoParticipante | None = None
    rol: Rol
    activo: bool
    creado_en: datetime
