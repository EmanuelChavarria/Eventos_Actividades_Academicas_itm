#!/usr/bin/env python3
"""Validador de mensajes de commit bajo la convención Conventional Commits en español.

Uso:
  1. Como hook de commit-msg:
     python scripts/check_commits.py .git/COMMIT_EDITMSG
  2. En CI sobre un rango de commits:
     python scripts/check_commits.py "origin/main..HEAD"
"""

import os
import re
import subprocess
import sys

PATTERN = re.compile(
    r"^(feat|fix|docs|test|refactor|style|chore|perf|ci|build)"
    r"(\([a-z0-9_-]+\))?: "
    r".+$"
)

MAX_LENGTH = 72


def validar_mensaje(mensaje: str) -> tuple[bool, str]:
    """Valida la primera línea de un mensaje de commit."""
    lineas = [l for l in mensaje.strip().splitlines() if l.strip()]
    if not lineas:
        return False, "El mensaje de commit está vacío."

    primera_linea = lineas[0].strip()

    # Ignorar commits automáticos de merge
    if primera_linea.startswith("Merge ") or primera_linea.startswith("Revert "):
        return True, ""

    if len(primera_linea) > MAX_LENGTH:
        return (
            False,
            f"La primera línea excede {MAX_LENGTH} caracteres (longitud actual: {len(primera_linea)}).\n"
            f"Línea: {primera_linea}",
        )

    if primera_linea.endswith("."):
        return (
            False,
            f"La primera línea no debe terminar con punto final.\nLínea: {primera_linea}",
        )

    if not PATTERN.match(primera_linea):
        return (
            False,
            "El formato no coincide con: tipo(alcance): descripción\n"
            "Tipos permitidos: feat, fix, docs, test, refactor, style, chore, perf, ci, build\n"
            f"Línea recibida: {primera_linea}",
        )

    return True, ""


def validar_archivo(ruta_archivo: str) -> int:
    """Valida el mensaje contenido en un archivo (hook commit-msg)."""
    if not os.path.isfile(ruta_archivo):
        print(f"Error: no se encontró el archivo {ruta_archivo}", file=sys.stderr)
        return 1

    with open(ruta_archivo, "r", encoding="utf-8", errors="replace") as f:
        contenido = f.read()

    valido, razon = validar_mensaje(contenido)
    if not valido:
        print(f"\n[ERROR COMMIT] Mensaje de commit rechazado:\n{razon}\n", file=sys.stderr)
        return 1

    return 0


def validar_rango(rango: str) -> int:
    """Valida todos los commits dentro de un rango git (CI)."""
    cmd = ["git", "log", rango, "--no-merges", "--format=%H %s"]
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar git log: {e.stderr}", file=sys.stderr)
        return 1

    lineas = [l for l in resultado.stdout.strip().splitlines() if l.strip()]
    if not lineas:
        return 0

    fallos = 0
    for linea in lineas:
        partes = linea.split(" ", 1)
        if len(partes) < 2:
            continue
        sha, mensaje = partes[0], partes[1]
        valido, razon = validar_mensaje(mensaje)
        if not valido:
            print(f"[ERROR COMMIT {sha[:7]}] {razon}\n", file=sys.stderr)
            fallos += 1

    if fallos > 0:
        print(f"Total de commits inválidos en rango {rango}: {fallos}", file=sys.stderr)
        return 1

    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python check_commits.py <archivo_o_rango_git>", file=sys.stderr)
        return 1

    arg = sys.argv[1]
    if os.path.isfile(arg):
        return validar_archivo(arg)
    return validar_rango(arg)


if __name__ == "__main__":
    sys.exit(main())
