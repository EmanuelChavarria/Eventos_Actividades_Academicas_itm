"""Errores de dominio y manejadores globales uniformes sin fuga de datos."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("pf04.errores")


class CodigosError:
    """Constantes de códigos de error de dominio compartidos."""

    DOCUMENTO_DUPLICADO = "DOCUMENTO_DUPLICADO"
    INSCRIPCION_DUPLICADA = "INSCRIPCION_DUPLICADA"
    CUPO_AGOTADO = "CUPO_AGOTADO"
    INSCRIPCIONES_CERRADAS = "INSCRIPCIONES_CERRADAS"
    PUBLICO_NO_PERMITIDO = "PUBLICO_NO_PERMITIDO"
    CANCELACION_NO_PERMITIDA = "CANCELACION_NO_PERMITIDA"
    ASISTENCIA_NO_PERMITIDA = "ASISTENCIA_NO_PERMITIDA"
    EVENTO_NO_PUBLICADO = "EVENTO_NO_PUBLICADO"
    EVENTO_NO_ENCONTRADO = "EVENTO_NO_ENCONTRADO"
    INSCRIPCION_NO_ENCONTRADA = "INSCRIPCION_NO_ENCONTRADA"
    SIN_PERMISO = "SIN_PERMISO"
    CREDENCIALES_INVALIDAS = "CREDENCIALES_INVALIDAS"
    DEMASIADOS_INTENTOS = "DEMASIADOS_INTENTOS"
    ERROR_VALIDACION = "ERROR_VALIDACION"
    REGLA_NEGOCIO = "REGLA_NEGOCIO"
    NO_IMPLEMENTADO = "NO_IMPLEMENTADO"
    ERROR_INTERNO = "ERROR_INTERNO"


class ErrorDominio(Exception):
    """Excepción base del dominio traducida automáticamente a respuesta JSON uniforme."""

    def __init__(
        self,
        codigo: str,
        mensaje: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        self.codigo = codigo
        self.mensaje = mensaje
        self.status_code = status_code
        self.detalles = detalles if detalles is not None else []
        super().__init__(mensaje)


class NoEncontrado(ErrorDominio):
    """Recurso no encontrado (HTTP 404)."""

    def __init__(
        self,
        codigo: str = "RECURSO_NO_ENCONTRADO",
        mensaje: str = "El recurso solicitado no existe.",
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_404_NOT_FOUND, detalles)


class NoAutorizado(ErrorDominio):
    """Usuario autenticado sin permisos suficientes (HTTP 403)."""

    def __init__(
        self,
        codigo: str = CodigosError.SIN_PERMISO,
        mensaje: str = "No tienes permiso para realizar esta acción.",
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_403_FORBIDDEN, detalles)


class NoAutenticado(ErrorDominio):
    """Credenciales inválidas o sesión ausente (HTTP 401)."""

    def __init__(
        self,
        codigo: str = CodigosError.CREDENCIALES_INVALIDAS,
        mensaje: str = "Autenticación requerida o credenciales inválidas.",
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_401_UNAUTHORIZED, detalles)


class Conflicto(ErrorDominio):
    """Conflicto de estado, duplicado o restricción de cupo/ventana (HTTP 409)."""

    def __init__(
        self,
        codigo: str,
        mensaje: str,
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_409_CONFLICT, detalles)


class ReglaNegocio(ErrorDominio):
    """Incumplimiento de regla de entrada o validación semántica (HTTP 422)."""

    def __init__(
        self,
        codigo: str = CodigosError.REGLA_NEGOCIO,
        mensaje: str = "La operación incumple una regla de negocio.",
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_422_UNPROCESSABLE_CONTENT, detalles)


class DemasiadosIntentos(ErrorDominio):
    """Límite de intentos excedido (HTTP 429)."""

    def __init__(
        self,
        codigo: str = CodigosError.DEMASIADOS_INTENTOS,
        mensaje: str = "Demasiados intentos fallidos. Intenta de nuevo más tarde.",
        detalles: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(codigo, mensaje, status.HTTP_429_TOO_MANY_REQUESTS, detalles)


def _construir_cuerpo(
    codigo: str,
    mensaje: str,
    detalles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": detalles if detalles is not None else [],
        }
    }


def _sanitizar_validacion(errores: tuple[Any, ...] | list[Any]) -> list[dict[str, Any]]:
    """Extrae ubicación y mensaje omitiendo explícitamente el valor enviado (`input`)."""
    detalles: list[dict[str, Any]] = []
    for err in errores:
        loc = [str(parte) for parte in err.get("loc", ())]
        detalles.append(
            {
                "campo": ".".join(loc),
                "mensaje": str(err.get("msg", "Dato inválido")),
                "tipo": str(err.get("type", "value_error")),
            }
        )
    return detalles


_CODIGOS_HTTP = {
    400: "SOLICITUD_INVALIDA",
    401: CodigosError.CREDENCIALES_INVALIDAS,
    403: CodigosError.SIN_PERMISO,
    404: "RECURSO_NO_ENCONTRADO",
    405: "METODO_NO_PERMITIDO",
    409: "CONFLICTO",
    422: CodigosError.ERROR_VALIDACION,
    429: CodigosError.DEMASIADOS_INTENTOS,
    501: CodigosError.NO_IMPLEMENTADO,
}


def registrar_manejadores_errores(app: FastAPI) -> None:
    """Registra los manejadores globales de errores sobre la instancia FastAPI."""

    @app.exception_handler(ErrorDominio)
    async def _handler_error_dominio(_request: Request, exc: ErrorDominio) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_construir_cuerpo(exc.codigo, exc.mensaje, exc.detalles),
        )

    @app.exception_handler(RequestValidationError)
    async def _handler_validacion(_request: Request, exc: RequestValidationError) -> JSONResponse:
        detalles = _sanitizar_validacion(exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_construir_cuerpo(
                CodigosError.ERROR_VALIDACION,
                "Los datos enviados no son válidos.",
                detalles,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handler_http(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codigo = _CODIGOS_HTTP.get(exc.status_code, f"HTTP_{exc.status_code}")
        mensaje = exc.detail if isinstance(exc.detail, str) else "Error en la solicitud."
        return JSONResponse(
            status_code=exc.status_code,
            content=_construir_cuerpo(codigo, mensaje),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _handler_inesperado(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("Error interno no controlado: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_construir_cuerpo(
                CodigosError.ERROR_INTERNO,
                "Ocurrió un error interno inesperado.",
            ),
        )
