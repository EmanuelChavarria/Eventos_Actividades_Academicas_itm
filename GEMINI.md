@AGENTS.md

# Instrucciones específicas de Gemini CLI / Antigravity

Las reglas del proyecto están en `AGENTS.md` (importado arriba) y en `.specify/memory/constitution.md`. Este archivo solo añade lo propio de Gemini.

## Identidad del desarrollador
- Gemini no lee `CLAUDE.local.md` automáticamente. Al iniciar sesión **pregunta al humano si es Integrante A o B** y consulta `docs/02_agente_integrante_A.md` o `docs/03_agente_integrante_B.md` para conocer sus épicas y archivos.

## Spec Kit
- Usa los comandos de `.gemini/commands/` (`/speckit.specify`, `clarify`, `plan`, `tasks`, `analyze`, `implement`) en ese orden. Detente a pedir aprobación tras la spec (G1) y tras plan, tareas y `analyze` (G2).
- No hay equivalente garantizado de skills `SKILL.md` en tu versión: aplica estas reglas directamente desde `AGENTS.md`.

## Forma de trabajo
- Sigue el ciclo Research → Strategy → Execution de la constitución y confirma con el humano antes de cambiar el contrato compartido o archivos del otro integrante.
- Cambios pequeños y verificables: un commit por tarea de `tasks.md`, con Conventional Commits en español.
- Antes de proponer un PR ejecuta `ruff`, `pytest` y `python scripts/export_openapi.py --check`.
- No leas ni imprimas `.env`; no uses `git push --force` ni push directo a `main`.
- Responde siempre en español, de forma concisa.
