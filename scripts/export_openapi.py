#!/usr/bin/env python3
"""Exportador y verificador del contrato OpenAPI.

Uso:
  1. Exportar contrato actualizado:
     python scripts/export_openapi.py
  2. Verificar si el contrato versionado coincide con la API (CI):
     python scripts/export_openapi.py --check
"""

import argparse
import json
import sys
from pathlib import Path

CONTRATO_PATH = Path("specs/contrato/openapi.json")


def obtener_openapi_actual() -> str:
    """Importa la aplicación FastAPI y obtiene el esquema OpenAPI serializado en JSON."""
    try:
        from app.main import app
    except ImportError as e:
        print(f"Error al importar la aplicación FastAPI (app.main): {e}", file=sys.stderr)
        sys.exit(1)

    esquema = app.openapi()
    return json.dumps(esquema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def exportar_contrato() -> int:
    """Exporta el esquema OpenAPI a specs/contrato/openapi.json."""
    CONTRATO_PATH.parent.mkdir(parents=True, exist_ok=True)
    contenido = obtener_openapi_actual()
    CONTRATO_PATH.write_text(contenido, encoding="utf-8")
    print(f"Contrato OpenAPI exportado exitosamente en {CONTRATO_PATH}")
    return 0


def verificar_contrato() -> int:
    """Compara el esquema OpenAPI actual con el archivo versionado en specs/contrato/openapi.json."""
    if not CONTRATO_PATH.exists():
        print(
            f"Error: No existe el archivo de contrato {CONTRATO_PATH}.\n"
            "Ejecuta 'python scripts/export_openapi.py' para generarlo.",
            file=sys.stderr,
        )
        return 1

    contenido_actual = obtener_openapi_actual()
    contenido_guardado = CONTRATO_PATH.read_text(encoding="utf-8")

    if contenido_actual != contenido_guardado:
        print(
            f"Error: El contrato OpenAPI en {CONTRATO_PATH} no coincide con el esquema actual de la API.\n"
            "Ejecuta 'python scripts/export_openapi.py' para actualizar el contrato y commitea los cambios.",
            file=sys.stderr,
        )
        return 1

    print("El contrato OpenAPI versionado coincide exactamente con la API.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta o verifica el contrato OpenAPI.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica si el contrato en disco coincide con la API sin modificarlo.",
    )
    args = parser.parse_args()

    if args.check:
        return verificar_contrato()
    return exportar_contrato()


if __name__ == "__main__":
    sys.exit(main())
