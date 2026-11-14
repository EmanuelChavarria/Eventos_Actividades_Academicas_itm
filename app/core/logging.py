"""Logging seguro por solicitud sin cuerpos, cabeceras sensibles ni documentos."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

logger_acceso = logging.getLogger("pf04.acceso")


def configurar_logging(nivel: str = "INFO") -> None:
    """Configura el nivel base de logging de la aplicación."""
    nivel_num = getattr(logging, nivel.upper(), logging.INFO)
    logging.basicConfig(
        level=nivel_num,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger_acceso.setLevel(nivel_num)


def registrar_middleware_logging(app: FastAPI) -> None:
    """Registra middleware que solo anota método, ruta sin query, estado y duración."""

    @app.middleware("http")
    async def _log_solicitud(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        inicio = time.perf_counter()
        response = await call_next(request)
        duracion_ms = (time.perf_counter() - inicio) * 1000
        # Se registra únicamente request.url.path (sin query, cuerpo ni cabeceras Cookie/Auth).
        logger_acceso.info(
            "%s %s -> %d (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duracion_ms,
        )
        return response
