---
description: "Plantilla de tareas atómicas para implementar una feature en Spec Kit"
---

# Tareas: [NOMBRE DE LA FEATURE]

- **Rama:** `[NNN-slug]` · **Responsable:** Integrante A | B
- **Entradas:** `specs/[NNN-slug]/spec.md`, `specs/[NNN-slug]/plan.md` (y `data-model.md`, `contracts/` si existen)
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** para cupo, duplicados, permisos, ventana de fechas y seguridad, **escribe primero la prueba `pytest` que falla** y después la implementación (rojo → verde).

## Convención de formato

`- [ ] T-NNN-01 [P?] [US?] Descripción concreta con ruta exacta de archivo · Commit: \`tipo(alcance): descripción\` · Terminado cuando: [criterio verificable]`

- **[P]:** ejecutable en paralelo (archivos distintos, sin dependencia pendiente).
- **[USX]:** historia de usuario a la que pertenece (`spec.md`).

---

## Fase 1: Preparación (Setup)

- [ ] T-NNN-01 [Descripción con rutas exactas] · Commit: `chore(...): ...` · Terminado cuando: [criterio]

---

## Fase 2: Base bloqueante (Foundational)

- [ ] T-NNN-02 [Descripción con rutas exactas] · Commit: `feat(...): ...` · Terminado cuando: [criterio]

---

## Fase 3: Historia de Usuario 1 - [Título] (Prioridad: P1)

**Objetivo:** [Qué entrega esta historia]
**Prueba independiente:** [Cómo verificarla sola]

### Pruebas primero (rojo → verde)

- [ ] T-NNN-03 [P] [US1] Escribir pruebas que fallan en `tests/test_....py` · Commit: `test(...): ...` · Terminado cuando: las pruebas fallan por la regla esperada

### Implementación

- [ ] T-NNN-04 [P] [US1] Schemas en `app/schemas/....py` · Commit: `feat(...): ...` · Terminado cuando: validación Pydantic completa
- [ ] T-NNN-05 [US1] Repositorio en `app/repositories/....py` · Commit: `feat(...): ...` · Terminado cuando: consultas e integridad en BD probadas
- [ ] T-NNN-06 [US1] Servicio en `app/services/....py` · Commit: `feat(...): ...` · Terminado cuando: reglas de negocio y pruebas en verde
- [ ] T-NNN-07 [US1] Router en `app/api/v1/....py` · Commit: `feat(...): ...` · Terminado cuando: endpoint responde en `/docs` con errores uniformes
- [ ] T-NNN-08 [US1] Vista Jinja2 + módulo JS en `app/web/...`, `app/templates/...`, `app/static/js/...` · Commit: `feat(web): ...` · Terminado cuando: interfaz consume `/api/v1` vía `fetch` sin `innerHTML` inseguro

---

## Fase 4: Verificación y cierre (Puertas G3–G4)

- [ ] T-NNN-09 Documentar pruebas funcionales `PF-XX` en `docs/pruebas/PF-XX.md` y `evidencias/PF-XX/` · Commit: `docs(pruebas): ...` · Terminado cuando: evidencia completa sin datos reales
- [ ] T-NNN-10 Ejecutar `ruff check . && ruff format --check .`, `pytest -q` (y `python scripts/export_openapi.py --check` si E10 ya existe) y verificar arranque de la app · Commit: `docs(specs): regenera contrato OpenAPI` (si aplica) · Terminado cuando: todo en verde

---

## Tabla resumen de trazabilidad

| ID | Tarea | Depende de | Archivos | Commit sugerido | Terminado cuando | Estado |
|---|---|---|---|---|---|:-:|
| T-NNN-01 | ... | — | `...` | `chore(...): ...` | ... | [ ] |
