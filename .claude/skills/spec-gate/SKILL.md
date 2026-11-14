---
name: spec-gate
description: Verifica que exista spec aprobada y sin [PENDIENTE] bloqueantes antes de escribir código o ejecutar /speckit.implement. Úsala siempre antes de programar una tarea.
---

# spec-gate

Puerta obligatoria antes de cualquier código (`AGENTS.md` §2).

## Pasos
1. Identifica la feature por la rama actual (`NNN-slug`). Si estás en `main` o la rama no sigue el esquema, **detente** y avisa.
2. Comprueba que existan `specs/NNN-slug/spec.md`, `plan.md` y `tasks.md`.
3. Busca `[PENDIENTE` en la spec y el plan; si hay alguno bloqueante, **detente y pregunta al humano**.
4. Confirma con el humano la aprobación G1 (spec) y G2 (plan, tareas, `/speckit.analyze` sin hallazgos críticos, PR en borrador). No asumas aprobación: pídela explícitamente.
5. Verifica que la tarea que vas a hacer esté en `tasks.md` y que pertenezca a tu integrante.
6. Si el comportamiento deseado difiere de la spec, actualiza primero la spec (`docs(specs): ...`) en un commit separado.

## Resultado
- **Aprobado:** responde «spec-gate OK: <NNN-slug>, tarea <T-NNN-XX>» y procede.
- **Bloqueado:** lista qué falta (archivo, pendiente o aprobación) y no escribas código.
