# Plan de Implementación: [FEATURE]

**Rama:** `[NNN-slug]` | **Fecha:** [FECHA] | **Spec:** [enlace a `spec.md`]
**Entrada:** Especificación en `specs/[NNN-slug]/spec.md` (aprobada en G1 y sin `[PENDIENTE]` bloqueantes).

## 1. Resumen y decisiones técnicas

[Resumen del enfoque técnico y decisiones tomadas junto con las alternativas descartadas.]

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.11+
- **Dependencias principales:** FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, Jinja2, argon2-cffi, PyJWT, `tzdata`
- **Almacenamiento:** SQLite (`PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`, WAL, UTC en fechas)
- **Pruebas y calidad:** `pytest`, `httpx`, `ruff`
- **Plataforma objetivo:** Local (Windows/macOS/Linux) y Docker (`python:3.12-slim`)
- **Restricciones:** Sin bundler ni SPA; sin lista de espera ni aprobación de eventos; propiedad estricta de archivos por integrante

## 3. Verificación contra la constitución *(puerta obligatoria)*

Revisión frente a `.specify/memory/constitution.md`:
- [ ] I. La spec manda (aprobada en G1, sin `[PENDIENTE]`)
- [ ] II. Capas estrictas (`api` → `services` → `repositories` → `models`; `services/` sin FastAPI; solo `repositories/` escribe SQL)
- [ ] III. Validación en servidor (Pydantic v2) y en BD (`PK`, `FK`, `UNIQUE`, `CHECK`, índice parcial)
- [ ] IV. Cupo atómico calculado (`BEGIN IMMEDIATE` + sentencia condicional + índice único parcial)
- [ ] V. Mínimo privilegio (rol + propietario en API y páginas web)
- [ ] VI. Errores uniformes sin trazas ni datos sensibles (422 sin `input`)
- [ ] VII. Sin secretos ni datos reales (`.env` fuera de Git, documentos ficticios)
- [ ] VIII. Commits atómicos en español, rama `NNN-slug`, PR en borrador en G2
- [ ] IX. `ruff` y `pytest` en verde (y `export_openapi.py --check` + CI cuando E10 esté integrado)
- [ ] X. Reproducible con y sin Docker
- [ ] XI. Respeta contrato compartido y propiedad de archivos (acuerdo previo si se toca algo compartido)
- [ ] XII. Dudas resueltas con el humano

## 4. Estructura y archivos por capa

```text
specs/[NNN-slug]/
├── plan.md
├── research.md          # si aplica
├── data-model.md        # si aplica
├── quickstart.md        # si aplica
├── contracts/           # si aplica
└── tasks.md             # generado con /speckit-tasks
```

| Capa | Archivos a crear o modificar | Responsable |
|---|---|:-:|
| Modelos / Migraciones | `app/models/...`, `migrations/...` | A |
| Core / Seguridad / Fechas | `app/core/...` | A |
| Schemas (entrada/salida) | `app/schemas/...` | A \| B |
| Repositorios (solo SQL) | `app/repositories/...` | A \| B |
| Servicios (reglas RN) | `app/services/...` | A \| B |
| API REST (`/api/v1`) | `app/api/v1/...` | A \| B |
| Web (esqueleto Jinja2) | `app/web/...`, `app/templates/...` | A \| B |
| Frontend JS (`fetch`) | `app/static/js/...` | A \| B |
| Pruebas (`pytest`) | `tests/...` | A \| B |

## 5. Contrato de API, modelo de datos y seguridad

- **Endpoints:** [Método, ruta, rol, éxito, errores HTTP + código de dominio]
- **Schemas:** [Entrada y salida separados; nunca exponer `hash_password`]
- **Cambios en BD / SQLite:** [Tablas, restricciones, índices, manejo de fechas UTC y `BEGIN IMMEDIATE` si aplica]
- **Seguridad y privacidad:** [argon2id / JWT `sub=id` / cookie `Secure` + HTTPS en todos los entornos / `Origin` CSRF / rate limit login / XSS `textContent` / enmascarado de documento / logs sin datos sensibles]

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| [Riesgo técnico o de integración] | [Mitigación] |

## 7. Registro de complejidad (solo si hay excepciones)

| Excepción | Por qué es necesaria | Alternativa más simple descartada |
|---|---|---|
| — | — | — |
