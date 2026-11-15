# Plan de Implementación: DevOps, CI/CD y Contenedorización

**Rama:** `010-devops-ci-docker` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](spec.md)
**Entrada:** Especificación en `specs/010-devops-ci-docker/spec.md`.

---

## 1. Resumen y decisiones técnicas

- **Docker:** Imagen base `python:3.12-slim`. Creación de usuario sin privilegios `appuser` (UID/GID 10001). Generación o copia de certificados SSL para servir HTTPS internamente. Inclusión de `entrypoint.sh` para aplicar migraciones con Alembic antes de iniciar Uvicorn.
- **Docker Compose:** Definición de servicio `web` con redirección de puertos, variables de entorno inyectadas y volumen con nombre `sqlite_data` montado en `/data` donde residirá la base de datos `app.db`.
- **Git / Líneas de fin:** Creación de `.gitattributes` para forzar `eol=lf` en scripts `.sh` y `.dockerignore` para excluir artefactos locales (`.venv`, `*.db`, `.env`, cachés).
- **Hooks y Commits:** Script standalone `scripts/check_commits.py` sin dependencias externas (usa librería estándar de Python `re`, `sys`) para validar mensajes tanto en hook de Git como en CI.
- **Contrato OpenAPI:** Script `scripts/export_openapi.py` que importa la app FastAPI (`app.main:app`), extrae el esquema con `app.openapi()`, lo formatea de forma determinista (claves ordenadas, sangría 2) y lo compara o escribe en `specs/contrato/openapi.json`.
- **CI / GitHub Actions:** Workflow `.github/workflows/ci.yml` configurado con jobs de calidad (`ruff`), pruebas (`pytest`), verificación de contrato OpenAPI (`export_openapi.py --check`) y compilación Docker (`docker build`).
- **Gobernanza PR:** Plantilla `.github/pull_request_template.md` para estandarizar revisiones cruzadas.

---

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.12 (CI y Docker) / 3.11+ (local)
- **Dependencias principales:** Docker Engine / Docker Compose, GitHub Actions, `ruff`, `pre-commit`
- **Plataforma objetivo:** Contenedor Linux Debian slim, GitHub Actions `ubuntu-latest`, Windows/macOS local.
- **Restricciones:** Sin secretos en el repositorio; HTTPS obligatorio en todos los entornos; propiedad exclusiva de archivos del Integrante B.

---

## 3. Verificación contra la constitución

Revisión frente a `.specify/memory/constitution.md`:
- [x] **I. La spec manda:** Especificación `spec.md` redactada y versionada previa a la implementación.
- [x] **II. Capas estrictas:** Los scripts y artefactos de CI residen en `scripts/`, `.github/` y raíz, sin invadir capas de aplicación.
- [x] **VII. Sin secretos ni datos reales:** `.dockerignore` y plantillas de configuración excluyen `.env` y llaves privadas.
- [x] **VIII. Commits atómicos en español:** Cumplimiento de Conventional Commits validado por hook y script.
- [x] **IX. CI verde:** Pipeline automático configurado como requisito previo para merge.
- [x] **X. Reproducible con y sin Docker:** Se soporta levantar la app con `docker compose` o directamente en entorno local.
- [x] **XI. Propiedad de archivos:** Los archivos corresponden 100% a la propiedad del Integrante B definida en `docs/03_agente_integrante_B.md`.

---

## 4. Estructura y archivos por capa

```text
.
├── .dockerignore
├── .gitattributes
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── scripts/
│   ├── check_commits.py
│   ├── entrypoint.sh
│   └── export_openapi.py
└── specs/
    ├── contrato/
    │   └── .gitkeep
    └── 010-devops-ci-docker/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```
