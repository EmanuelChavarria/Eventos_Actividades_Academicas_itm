# Especificación de Feature: DevOps, CI/CD y Contenedorización

- **Épica:** E10 · **Condiciones:** — · **Requisitos:** RNF-10, RNF-20, RNF-21, RNF-22, RNF-23
- **Rama de feature:** `010-devops-ci-docker` · **Creada:** 2026-11-14
- **Estado:** borrador · **Responsable:** Integrante B
- **Entrada:** Configuración de DevOps, integración continua, dockerización, hooks de calidad y gobierno del contrato OpenAPI para el proyecto PF-04.

---

## 1. Objetivo y alcance

Establecer la infraestructura de integración continua (CI) en GitHub Actions, la estandarización del entorno de ejecución mediante Docker y `docker-compose`, el control automatizado del formato de commits y código mediante hooks, y el mecanismo de verificación del contrato OpenAPI (`specs/contrato/openapi.json`), garantizando reproducibilidad y calidad antes de fusionar cualquier cambio a `main`.

---

## 2. Fuera de alcance

- Despliegue en la nube o clusters Kubernetes (producción no exigida por guía docente).
- Registry remoto privado de contenedores (Docker Hub / GHCR con publicación automática).
- Renovación automática de certificados SSL comerciales (se usan certificados locales `mkcert` y autofirmados en CI/Docker).

---

## 3. Historias de usuario y criterios de aceptación

### Historia de Usuario 1 - Levantamiento homogéneo con Docker (Prioridad: P1)

Como desarrollador o evaluador quiero levantar la aplicación y su base de datos con un único comando Docker, para ejecutar el sistema en un entorno idéntico sin dependencias locales previas.

- **Por qué esta prioridad:** Garantiza el principio X de la constitución (reproducibilidad).
- **Prueba independiente:** Ejecutar `docker compose up --build` en un entorno limpio sin Python instalado y comprobar que `/health` y `/docs` responden en HTTPS.
- **Escenarios de aceptación:**
  1. **Dado** un entorno con Docker instalado, **Cuando** se ejecuta `docker compose up --build`, **Entonces** se construye la imagen sobre `python:3.12-slim`, se ejecutan las migraciones pendientes vía `entrypoint.sh` y el servidor queda disponible en el puerto expuesto.
  2. **Dado** un contenedor en ejecución con datos registrados, **Cuando** se detiene y reinicia el contenedor (`docker compose down && docker compose up`), **Entonces** los datos en SQLite persisten íntegros gracias al volumen nombrado asignado.

---

### Historia de Usuario 2 - Validación automática de PRs en CI (Prioridad: P1)

Como equipo de desarrollo queremos que cada Pull Request y push a `main` se valide de forma autónoma en GitHub Actions, para impedir la integración de código con fallos de estilo, pruebas rotas o imágenes Docker incompatibles.

- **Por qué esta prioridad:** Constituye la puerta de calidad G4 (CI verde obligatorio antes de merge).
- **Prueba independiente:** Abrir un PR con un error sintáctico o prueba rota y comprobar que el workflow bloquea la fusión.
- **Escenarios de aceptación:**
  1. **Dado** un PR hacia `main`, **Cuando** se dispara el pipeline de CI, **Entonces** se ejecutan en paralelo o etapas los jobs de `calidad` (`ruff check .`, `ruff format --check .`), `pruebas` (`pytest -q` con certificados de prueba) y `docker` (`docker build`), requiriendo éxito total (código de salida 0) para autorizar la integración.
  2. **Dado** un cambio en routers o esquemas de la API sin actualizar el contrato, **Cuando** corre el paso de verificación de contrato, **Entonces** `python scripts/export_openapi.py --check` falla con código 1 alertando la discrepancia.

---

### Historia de Usuario 3 - Validación de Conventional Commits y Plantilla de PR (Prioridad: P2)

Como equipo queremos garantizar la trazabilidad del historial Git mediante Conventional Commits en español y estructurar la información de cada PR con una plantilla estándar.

- **Por qué esta prioridad:** Cumple el principio VIII de la constitución y RNF-21/RNF-23.
- **Prueba independiente:** Intentar realizar un commit con mensaje informal (ej. "arreglos") y verificar su rechazo por el script validador.
- **Escenarios de aceptación:**
  1. **Dado** un mensaje de commit, **Cuando** se procesa por `scripts/check_commits.py`, **Entonces** valida que siga el patrón `tipo(alcance): descripción` en minúscula inicial, tiempo presente, sin punto final, con longitud ≤ 72 caracteres y tipo válido (`feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`, `perf`, `ci`, `build`).
  2. **Dado** un desarrollador abriendo un PR en GitHub, **Cuando** se crea la solicitud, **Entonces** se precarga `.github/pull_request_template.md` exigiendo tipo de cambio, tareas asociadas, pruebas efectuadas y verificación de checklist.

---

### Historia de Usuario 4 - Hooks locales de pre-commit (Prioridad: P2)

Como desarrollador quiero advertencias y correcciones locales automáticas antes de enviar commits, reduciendo ciclos de retroalimentación fallidos en el CI.

- **Por qué esta prioridad:** Previene errores triviales de formato y commits no conformes antes de llegar a GitHub.
- **Prueba independiente:** Ejecutar `pre-commit run --all-files` en local.
- **Escenarios de aceptación:**
  1. **Dado** un archivo modificado con desalineación de formato o espacios en blanco residuales, **Cuando** se intenta commitear, **Entonces** pre-commit formatea con `ruff format` y valida con `ruff check` antes de confirmar el commit.

---

## 4. Reglas técnicas y restricciones

- **RNF-10 (Docker):** Contenedor multi-stage o optimizado con usuario no-root por seguridad, variables de entorno inyectables y almacenamiento en `/data` montado en volumen Docker.
- **RNF-20 (CI):** GitHub Actions configurado en `.github/workflows/ci.yml`. Python 3.12, cache de dependencias con `pip`/`uv`, matriz limpia.
- **RNF-21 (Commits):** Validador en `scripts/check_commits.py` compatible con ejecución local (hook `commit-msg`) y CI.
- **RNF-22 (Contrato OpenAPI):** Script `scripts/export_openapi.py` exporta el esquema JSON a `specs/contrato/openapi.json`. La opción `--check` realiza comparación determinista sin modificar el archivo en disco.
- **RNF-23 (Git / PR):** Rama `010-devops-ci-docker`, commits atómicos en español, plantilla `.github/pull_request_template.md`.

---

## 5. Errores esperados y códigos de salida

| Herramienta / Script | Condición de fallo | Código de salida | Comportamiento |
|---|---|---|---|
| `scripts/check_commits.py` | Mensaje no cumple Conventional Commits o supera 72 caracteres | `1` | Muestra mensaje explicativo con la regla incumplida y aborta el commit. |
| `scripts/export_openapi.py --check` | `openapi.json` desincronizado con la API en memoria | `1` | Imprime diff o mensaje de error indicando ejecutar `python scripts/export_openapi.py`. |
| `ruff check .` | Errores de linting o imports no utilizados | `1` | Detalla archivo y línea infractora. |
| `ruff format --check .` | Código no formateado según estándar | `1` | Lista archivos que requieren reformateo. |
| `pytest` | Pruebas unitarias o de integración fallidas | `1` | Detalla aserción fallida y traza de test. |

---

## 6. Seguridad y variables de entorno

- **Secretos:** Prohibido incluir credenciales, contraseñas o `.env` en imágenes Docker o en el repositorio Git (`.dockerignore` debe excluir `.env`, `*.db`, `.git`, `.venv`).
- **Usuario no privilegiado:** El contenedor debe ejecutar la aplicación bajo un usuario de sistema dedicado (`appuser`, UID 10001), no como `root`.
- **Certificados SSL:** El Dockerfile y CI deben generar o configurar certificados autofirmados si no se proporcionan certificados externos, asegurando que `COOKIE_SECURE=true` y HTTPS se cumplan siempre.

---

## 7. Casos límite

- Verificación de OpenAPI cuando la aplicación aún no tiene todas las rutas de negocio (debe funcionar limpiamente con los endpoints base existentes como `/health`).
- Manejo de finales de línea CRLF vs LF en scripts shell (`scripts/entrypoint.sh` debe forzar LF en `.gitattributes` para no fallar en entornos Linux/Docker).
- Persistencia de base de datos SQLite en volumen nombrado con permisos adecuados para el usuario `appuser`.

---

## 8. Supuestos y pendientes

- `[SUPUESTO S-01]`: Las pruebas en CI se ejecutan con certificado autofirmado generado dinámicamente o mockeado mediante `httpx.AsyncClient(base_url="https://testserver")`.
- `[SUPUESTO S-02]`: En la Fase 0, los jobs de CI que requieren código de aplicación (`pytest`, `export_openapi.py`) se configurarán de forma robusta para ejecutarse una vez que E1 esté presente en `main`.

---

## 9. Criterios de éxito y verificación

- **SC-E10-01:** `python scripts/check_commits.py` valida mensajes válidos y rechaza inválidos.
- **SC-E10-02:** `python scripts/export_openapi.py --check` retorna 0 si no hay cambios y 1 si difiere.
- **SC-E10-03:** Workflow `.github/workflows/ci.yml` sintácticamente válido y estructurado.
- **SC-E10-04:** `docker compose build` genera la imagen sin errores.
