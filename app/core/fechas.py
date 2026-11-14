"""Utilidades compartidas de fechas UTC, zona America/Bogota y ventana de asistencia."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import AfterValidator
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

ZONA_BOGOTA = ZoneInfo("America/Bogota")
VENTANA_ASISTENCIA_HORAS = 48
_FORMATO_UTC_SQLITE = "%Y-%m-%dT%H:%M:%S.%fZ"

ProveedorAhora = Callable[[], datetime]


def ahora_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC (inyectable para pruebas)."""
    return datetime.now(UTC)


def asegurar_utc(valor: datetime) -> datetime:
    """Valida que una fecha incluya zona horaria y la normaliza a UTC."""
    if valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError("La fecha debe incluir información de zona horaria (ej. -05:00 o Z).")
    return valor.astimezone(UTC)


FechaConZona = Annotated[datetime, AfterValidator(asegurar_utc)]


def a_bogota(valor: datetime) -> datetime:
    """Convierte una fecha con zona horaria (o UTC) a America/Bogota."""
    return asegurar_utc(valor).astimezone(ZONA_BOGOTA)


def esta_en_ventana_asistencia(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    *,
    ahora: datetime | None = None,
) -> bool:
    """Indica si `ahora` está entre `fecha_inicio` y `fecha_fin + 48 horas` en UTC."""
    inicio_utc = asegurar_utc(fecha_inicio)
    fin_utc = asegurar_utc(fecha_fin)
    referencia = asegurar_utc(ahora) if ahora is not None else ahora_utc()
    limite_cierre = fin_utc + timedelta(hours=VENTANA_ASISTENCIA_HORAS)
    return inicio_utc <= referencia <= limite_cierre


class UTCDateTime(TypeDecorator):
    """Tipo ORM que almacena fechas UTC ISO-8601 fijas en SQLite y devuelve datetime UTC."""

    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> str | None:
        if value is None:
            return None
        return asegurar_utc(value).strftime(_FORMATO_UTC_SQLITE)

    def process_result_value(self, value: str | datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value.astimezone(UTC)
        texto = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(texto).astimezone(UTC)
