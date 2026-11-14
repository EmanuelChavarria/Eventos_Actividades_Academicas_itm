---
name: pr-workflow
description: Flujo de Pull Request del proyecto: borrador desde G2, verificaciones previas, plantilla de descripción, CI y revisión del compañero. Úsala al abrir, actualizar o cerrar un PR.
---

# pr-workflow

## Ciclo
1. **Borrador desde G2:** al aprobarse plan y tareas, abre el PR en borrador hacia `main` desde la rama `NNN-slug` para que el compañero lea la spec. Nunca se trabaja ni se hace push directo a `main`.
2. Implementa tarea por tarea (un commit por tarea). Sube la rama tras cada tarea.
3. Sincroniza a diario: `git fetch origin && git rebase origin/main`; si rebasaste, `git push --force-with-lease` solo en tu propia rama. Si hay conflicto en `specs/contrato/openapi.json`, regenéralo con el script (no a mano).

## Antes de marcar «listo» (obligatorio)
```bash
ruff check . && ruff format --check .
pytest -q
python scripts/export_openapi.py --check
```
Además: la app arranca (con o sin Docker) y los endpoints de la épica funcionan en `/docs`. **El CI debe estar verde** (`calidad`, `pruebas`, `docker`); no se desactivan checks ni se usa `--no-verify`.

## Descripción del PR
- **Propósito**
- **Spec asociada** (`specs/NNN-slug/`)
- **Cambios realizados**
- **Pruebas efectuadas** (PF-XX y pytest)
- **Requisitos asociados** (RF/RNF/CA)
- **Notas para el revisor** (archivos del otro integrante o contrato compartido tocados)

## Revisión y fusión
- Revisor = el otro integrante, con comentarios reales en GitHub (G5).
- Método de fusión: **merge commit** (no squash), para conservar los aportes individuales.
- Tras el merge: `git switch main && git pull --rebase origin main` y elimina la rama.
- Actualiza `docs/trazabilidad.md` (componente, PR, prueba).
