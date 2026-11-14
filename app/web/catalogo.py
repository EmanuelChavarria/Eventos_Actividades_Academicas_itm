"""Vistas web del catálogo público (base en E1, vista completa en E4)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def pagina_inicio(request: Request) -> HTMLResponse:
    """Portada base mientras se integra el esqueleto Jinja2 completo."""
    _ = request
    return HTMLResponse("<!doctype html><html lang='es'><body><h1>PF-04</h1></body></html>")
