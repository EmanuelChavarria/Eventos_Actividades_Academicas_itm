"""Configuración tipada por entorno con validación estricta al arranque."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VALOR_EJEMPLO_SECRET_KEY = "CAMBIA-ESTA-CLAVE-POR-UNA-SECRETA-DE-AL-MENOS-32-CARACTERES"
MIN_SECRET_KEY_LEN = 32


class Settings(BaseSettings):
    """Parámetros de entorno requeridos para ejecutar la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Eventos y Actividades Académicas"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./eventos.db"
    SECRET_KEY: str
    COOKIE_SECURE: bool = True
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    ALLOWED_ORIGINS: list[str] = [
        "https://localhost:8000",
        "https://127.0.0.1:8000",
    ]
    LOG_LEVEL: str = "INFO"

    @field_validator("SECRET_KEY")
    @classmethod
    def validar_secret_key(cls, valor: str) -> str:
        """Exige una SECRET_KEY robusta y distinta al valor de ejemplo."""
        limpio = valor.strip()
        if not limpio:
            raise ValueError("SECRET_KEY no puede estar vacía.")
        if limpio == VALOR_EJEMPLO_SECRET_KEY:
            raise ValueError("SECRET_KEY no puede ser igual al valor de .env.example.")
        if len(limpio) < MIN_SECRET_KEY_LEN:
            raise ValueError(f"SECRET_KEY debe tener al menos {MIN_SECRET_KEY_LEN} caracteres.")
        return limpio

    @field_validator("COOKIE_SECURE")
    @classmethod
    def validar_cookie_secure(cls, valor: bool) -> bool:
        """Exige COOKIE_SECURE=true porque la app opera solo por HTTPS."""
        if valor is not True:
            raise ValueError(
                "COOKIE_SECURE debe ser true; HTTPS es obligatorio en todos los entornos."
            )
        return valor


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración validada en caché."""
    return Settings()
