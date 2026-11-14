# Tareas: DevOps, CI/CD y Contenedorización

- **Rama:** `010-devops-ci-docker` · **Responsable:** Integrante B
- **Entradas:** `specs/010-devops-ci-docker/spec.md`, `specs/010-devops-ci-docker/plan.md`
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.

---

## Tareas de Implementación

### Fase 1: Docker y Contenedorización (US1)
- [ ] **T-010-01** [US1] Crear `.dockerignore`, `.gitattributes`, `Dockerfile` y `scripts/entrypoint.sh` · Commit: `build(docker): agrega imagen de la aplicacion con entrypoint de migracion` · Terminado cuando: los archivos están configurados con usuario no-root y finales de línea LF para scripts shell.
- [ ] **T-010-02** [US1] Crear `docker-compose.yml` con servicio web y volumen persistente para SQLite · Commit: `build(docker): agrega docker-compose con volumen persistente para sqlite` · Terminado cuando: `docker-compose.yml` está correctamente estructurado con volumen nombrado y variables de entorno.

### Fase 2: Automatización de Calidad y Commits (US3, US4)
- [ ] **T-010-03** [US3] Crear script `scripts/check_commits.py` para validar Conventional Commits en español · Commit: `ci(commits): agrega validador de conventional commits` · Terminado cuando: el script valida tipos permitidos, longitud ≤ 72 y formato sin dependencias externas.
- [ ] **T-010-04** [US4] Configurar `.pre-commit-config.yaml` y `.github/pull_request_template.md` · Commit: `chore(ci): agrega hooks de pre-commit y plantilla de pull request` · Terminado cuando: los hooks de ruff/commits y la plantilla de PR quedan configurados.

### Fase 3: Gobernanza del Contrato OpenAPI (US2)
- [ ] **T-010-05** [US2] Crear `scripts/export_openapi.py` para exportar y verificar `specs/contrato/openapi.json` con flag `--check` · Commit: `ci(specs): agrega script de exportacion y verificacion de contrato openapi` · Terminado cuando: el script soporta exportar e inspeccionar el esquema deterministamente.

### Fase 4: Pipeline de Integración Continua (US2)
- [ ] **T-010-06** [US2] Crear workflow de GitHub Actions en `.github/workflows/ci.yml` · Commit: `ci(workflows): agrega pipeline de calidad pruebas contrato y docker` · Terminado cuando: el workflow incluye jobs de calidad, pruebas, openapi y build docker.
