"""Utilidades de seguridad: argon2id, JWT, documento, CSRF y limitador de login."""

from __future__ import annotations

import re
import threading
from collections import defaultdict, deque
from collections.abc import Sequence
from datetime import datetime, timedelta
from urllib.parse import urlsplit

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings, get_settings
from app.core.errors import DemasiadosIntentos
from app.core.fechas import ahora_utc
from app.models.enums import TipoDocumento

NOMBRE_COOKIE_SESION = "pf04_session"
MAX_INTENTOS_LOGIN = 10
VENTANA_INTENTOS_SEGUNDOS = 900

_PATRON_DIGITOS = re.compile(r"^\d{5,12}$")
_PATRON_PAS = re.compile(r"^[A-Z0-9]{5,15}$")

_hasher = PasswordHasher()
HASH_FICTICIO_TIMING: str = _hasher.hash("clave-ficticia-para-tiempo-constante-pf04")


def hashear_password(password: str) -> str:
    """Genera el hash argon2id de una contraseña en texto plano."""
    return _hasher.hash(password)


def verificar_password(password: str, hash_almacenado: str) -> bool:
    """Verifica de forma segura una contraseña contra su hash argon2id."""
    try:
        return _hasher.verify(hash_almacenado, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verificar_en_tiempo_constante(password: str, hash_almacenado: str | None) -> bool:
    """Ejecuta verificación argon2id incluso cuando no existe hash para evitar timing attacks."""
    if not hash_almacenado:
        verificar_password(password, HASH_FICTICIO_TIMING)
        return False
    return verificar_password(password, hash_almacenado)


def crear_token_acceso(usuario_id: int, settings: Settings | None = None) -> str:
    """Emite un JWT HS256 conteniendo únicamente sub=id, iat y exp."""
    cfg = settings or get_settings()
    ahora = ahora_utc()
    expiracion = ahora + timedelta(seconds=cfg.ACCESS_TOKEN_EXPIRE_SECONDS)
    carga = {
        "sub": str(usuario_id),
        "iat": int(ahora.timestamp()),
        "exp": int(expiracion.timestamp()),
    }
    return jwt.encode(carga, cfg.SECRET_KEY, algorithm=cfg.JWT_ALGORITHM)


def decodificar_token_acceso(token: str, settings: Settings | None = None) -> int | None:
    """Valida firma y expiración de un JWT y retorna el usuario_id entero o None."""
    if not token:
        return None
    cfg = settings or get_settings()
    try:
        carga = jwt.decode(
            token,
            cfg.SECRET_KEY,
            algorithms=[cfg.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
        sub = carga.get("sub")
        usuario_id = int(sub)
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None
    return usuario_id if usuario_id > 0 else None


def normalizar_y_validar_documento(
    tipo_documento: TipoDocumento | str,
    numero_documento: str,
) -> str:
    """Normaliza sin espacios/puntos y valida el formato según tipo de documento (RN-14)."""
    tipo = (
        tipo_documento
        if isinstance(tipo_documento, TipoDocumento)
        else TipoDocumento(str(tipo_documento).strip().upper())
    )
    limpio = numero_documento.strip().replace(" ", "").replace(".", "")
    if tipo == TipoDocumento.PAS:
        limpio = limpio.upper()
        if not _PATRON_PAS.match(limpio):
            raise ValueError("El pasaporte debe tener entre 5 y 15 caracteres alfanuméricos.")
        return limpio

    if not _PATRON_DIGITOS.match(limpio):
        raise ValueError("El documento CC/CE/TI debe contener solo entre 5 y 12 dígitos.")
    return limpio


def extraer_origen(cabecera: str | None) -> str | None:
    """Extrae esquema://host[:puerto] normalizado desde una cabecera Origin o Referer."""
    if not cabecera:
        return None
    partes = urlsplit(cabecera.strip())
    if not partes.scheme or not partes.netloc:
        return None
    return f"{partes.scheme.lower()}://{partes.netloc.lower()}"


def es_origen_confiable(
    *,
    origin: str | None,
    referer: str | None,
    origen_solicitud: str,
    origenes_permitidos: Sequence[str],
) -> bool:
    """Valida Origin (o Referer como respaldo) frente a los orígenes HTTPS confiables."""
    candidato = origin or referer
    origen_normalizado = extraer_origen(candidato)
    if origen_normalizado is None:
        return False

    permitidos = {
        origen
        for valor in (*origenes_permitidos, origen_solicitud)
        if (origen := extraer_origen(valor)) is not None
    }
    return origen_normalizado in permitidos


class ControlIntentosLogin:
    """Limitador en memoria por (ip, tipo_documento, numero_documento) con ventana móvil."""

    def __init__(
        self,
        *,
        max_intentos: int = MAX_INTENTOS_LOGIN,
        ventana_segundos: int = VENTANA_INTENTOS_SEGUNDOS,
    ) -> None:
        self._max_intentos = max_intentos
        self._ventana = timedelta(seconds=ventana_segundos)
        self._fallos: dict[tuple[str, str, str], deque[datetime]] = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _clave(ip_cliente: str, tipo_documento: str, numero_documento: str) -> tuple[str, str, str]:
        return (ip_cliente or "desconocida", tipo_documento, numero_documento)

    def _podar(self, cola: deque[datetime], ahora: datetime) -> None:
        limite = ahora - self._ventana
        while cola and cola[0] < limite:
            cola.popleft()

    def verificar_no_bloqueado(
        self,
        ip_cliente: str,
        tipo_documento: str,
        numero_documento: str,
        *,
        ahora: datetime | None = None,
    ) -> None:
        """Lanza 429 DEMASIADOS_INTENTOS si la clave alcanzó el máximo dentro de la ventana."""
        instante = ahora or ahora_utc()
        clave = self._clave(ip_cliente, tipo_documento, numero_documento)
        with self._lock:
            cola = self._fallos.get(clave)
            if not cola:
                return
            self._podar(cola, instante)
            if not cola:
                self._fallos.pop(clave, None)
                return
            if len(cola) >= self._max_intentos:
                raise DemasiadosIntentos()

    def registrar_fallo(
        self,
        ip_cliente: str,
        tipo_documento: str,
        numero_documento: str,
        *,
        ahora: datetime | None = None,
    ) -> None:
        """Registra un intento fallido dentro de la ventana actual."""
        instante = ahora or ahora_utc()
        clave = self._clave(ip_cliente, tipo_documento, numero_documento)
        with self._lock:
            cola = self._fallos[clave]
            self._podar(cola, instante)
            cola.append(instante)

    def reiniciar(self, ip_cliente: str, tipo_documento: str, numero_documento: str) -> None:
        """Elimina el historial de fallos de la clave tras un inicio de sesión exitoso."""
        clave = self._clave(ip_cliente, tipo_documento, numero_documento)
        with self._lock:
            self._fallos.pop(clave, None)

    def reiniciar_todo(self) -> None:
        """Limpia todos los contadores en memoria (uso en pruebas automatizadas)."""
        with self._lock:
            self._fallos.clear()


control_intentos_login = ControlIntentosLogin()
