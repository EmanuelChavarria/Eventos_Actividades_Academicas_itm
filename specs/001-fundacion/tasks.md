---
description: "Tareas atómicas para implementar E1 — Fundación y plataforma"
---

# Tareas: Fundación y plataforma (E1)

- **Rama:** `001-fundacion` · **Responsable:** Integrante A
- **Entradas:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/spec.md), [plan.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/plan.md), [data-model.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/data-model.md)
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** para reglas críticas de seguridad, fechas UTC, integridad de BD y manejo de errores sin filtrar datos sensibles, escribe primero la prueba `pytest` que falla y después la implementación (rojo → verde).

## Convención de formato

`- [ ] T-001-XX [P?] [US?] Descripción concreta con ruta exacta · Commit: \`tipo(alcance): descripción\` · Terminado cuando: [criterio verificable]`

---

## Fase 1: Preparación (Setup)

- [x] T-001-01 Crear estructura de carpetas en capas (`app/core`, `app/models`, `app/schemas`, `app/repositories`, `app/services`, `app/api/v1`, `app/web`, `app/templates`, `app/static`, `migrations`, `scripts`, `tests`) con `app = FastAPI(...)` mínimo en `app/main.py` y stubs por épica · Commit: `chore(repo): crea estructura de capas y archivos base por epica` · Terminado cuando: todos los paquetes y `app.main:app` existen e importan sin errores de sintaxis
- [x] T-001-02 [P] Verificar exclusiones de `.gitignore` (`.env`, `*.db`, `.venv/`, `certs/`, `*.pem`, `*.key`, `*.crt`) y crear `.gitattributes` con finales de línea LF/CRLF explícitos · Commit: `chore(repo): verifica .gitignore y agrega .gitattributes` · Terminado cuando: `git status --ignored` confirma secretos/certificados ignorados
- [x] T-001-03 [P] Fijar dependencias de producción en `requirements.txt` (`fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic`, `pydantic-settings`, `email-validator`, `jinja2`, `python-multipart`, `argon2-cffi`, `PyJWT`, `tzdata`) · Commit: `chore(deps): fija dependencias base de FastAPI, SQLAlchemy y Jinja2` · Terminado cuando: `pip install -r requirements.txt` instala sin conflictos en entorno virtual limpio
- [x] T-001-04 [P] Fijar dependencias de desarrollo en `requirements-dev.txt` (`pytest`, `httpx`, `ruff`, `pre-commit`) · Commit: `chore(deps): agrega requirements-dev.txt con pytest, httpx y ruff` · Terminado cuando: `pip install -r requirements-dev.txt` instala todas las herramientas de prueba y lint
- [x] T-001-05 [P] Configurar `ruff.toml` (reglas `E, F, I, B, UP`, `target-version = "py311"`, longitud de línea consistente) · Commit: `chore(lint): configura ruff para lint y formato` · Terminado cuando: `ruff check .` se ejecuta sin errores de configuración
- [x] T-001-06 [P] Crear `scripts/generar_certificados.ps1` y `scripts/generar_certificados.sh` (`mkcert` con alternativa `openssl`) para emitir `certs/localhost.pem` y `certs/localhost-key.pem` · Commit: `chore(repo): agrega scripts de certificados locales HTTPS con mkcert` · Terminado cuando: los scripts validan/generan certificados en `certs/` y quedan ignorados por Git

---

## Fase 2: Pruebas primero para reglas críticas de fundación

- [x] T-001-07 [US1] [US2] Crear `tests/conftest.py` (BD temporal en archivo por prueba, `TestClient(base_url="https://testserver")`, fábricas por rol) y pruebas iniciales rojo en `tests/test_seguridad_fechas_bd.py` para configuración fail-fast (`SECRET_KEY`, `COOKIE_SECURE`), fechas UTC/422/48 h, errores sin `input` y restricciones SQLite · Commit: `test(core): agrega conftest HTTPS y pruebas rojo de reglas base` · Terminado cuando: `pytest` falla por ausencia/incompleto de la implementación esperada (rojo verificado)

---

## Fase 3: Base bloqueante y contrato compartido (US1 + US2)

**Objetivo:** Entregar configuración segura, SQLite con integridad, modelos, migración inicial y utilidades compartidas que ponen en verde las pruebas de US1 y US2.
**Prueba independiente:** `alembic upgrade head` en BD limpia y `pytest tests/test_seguridad_fechas_bd.py` en verde.

- [x] T-001-08 [US1] Implementar `app/core/config.py` (`pydantic-settings` validando `SECRET_KEY` no vacía/≥32/distinta de ejemplo y `COOKIE_SECURE == True` al arrancar) y `.env.example` · Commit: `feat(core): agrega configuracion segura por entorno y .env.example` · Terminado cuando: las pruebas de arranque inseguro en `pytest` pasan en verde
- [x] T-001-09 [P] [US2] Implementar `app/core/fechas.py` (`UTCDateTime`, rechazo 422 a fechas sin zona horaria, conversión UTC ↔ `America/Bogota`, ventana `fecha_inicio .. fecha_fin + 48h` y reloj inyectable) · Commit: `feat(core): agrega utilidades de fechas UTC y ventana de asistencia` · Terminado cuando: pruebas unitarias de fechas en `pytest` pasan en verde
- [x] T-001-10 [US2] Implementar `app/core/database.py` (`Base`, `engine`, `SessionLocal`, `get_db()`, listener por conexión con `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`, `WAL`) · Commit: `feat(bd): configura SQLite con claves foraneas y sesion por solicitud` · Terminado cuando: pruebas de `PRAGMA foreign_keys=1` y `busy_timeout=5000` pasan en verde
- [x] T-001-11 [P] [US2] Definir enumeraciones del dominio en `app/models/enums.py` (`Rol`, `TipoDocumento`, `TipoParticipante`, `TipoEvento`, `Modalidad`, `PublicoObjetivo`, `EstadoEvento`, `EstadoInscripcion`, `EstadoAsistencia`) · Commit: `feat(bd): define enumeraciones de rol, documento, tipo y estados` · Terminado cuando: todas las enumeraciones del contrato compartido son importables y usadas por modelos
- [x] T-001-12 [US2] Implementar modelos ORM `app/models/{usuario,evento,inscripcion,asistencia}.py` y `app/models/__init__.py` con `PK`, `FK`, `UNIQUE`, `CHECK`, índice único parcial y `UTCDateTime` · Commit: `feat(bd): define modelos con restricciones CHECK, FK e indices` · Terminado cuando: `Base.metadata` refleja fielmente [data-model.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/data-model.md)
- [x] T-001-13 [US2] Configurar Alembic (`alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`) y crear `migrations/versions/0001_esquema_inicial.py` (incluyendo índice único parcial `WHERE estado = 'activa'`) · Commit: `feat(bd): agrega migracion inicial del esquema en Alembic` · Terminado cuando: `alembic upgrade head` crea las 4 tablas y pasan las pruebas de integridad SQLite en `pytest`
- [x] T-001-14 [US2] Implementar `app/core/errors.py` (`ErrorDominio`, `NoEncontrado`, `NoAutorizado`, `Conflicto`, `ReglaNegocio`, códigos de dominio de constitución y manejadores globales para `ErrorDominio`, `RequestValidationError` omitiendo `input`, `HTTPException` y `Exception`) · Commit: `feat(core): agrega errores de dominio y manejadores globales uniformes` · Terminado cuando: pruebas de formato uniforme sin `input` pasan en verde
- [ ] T-001-15 [P] [US2] Definir en `app/api/deps.py` las firmas `get_current_user` (lanza `401 CREDENCIALES_INVALIDAS` en E1), `get_current_user_optional` (`None` en E1) y `require_roles(*roles)` · Commit: `feat(api): define interfaz de dependencias de autenticacion y roles` · Terminado cuando: las firmas coinciden con el contrato compartido y rechazan acceso no autenticado
- [ ] T-001-16 [P] [US2] Implementar `contar_activas(db, evento_id)` y `contar_activas_por_eventos(db, ids)` en `app/repositories/inscripcion_repo.py` · Commit: `feat(bd): agrega conteo de inscripciones activas por evento` · Terminado cuando: pruebas unitarias verifican conteo solo de inscripciones con `estado='activa'`

---

## Fase 4: Plataforma API, observabilidad y esqueleto web (US1 + US4)

**Objetivo:** Exponer la aplicación FastAPI ejecutable por HTTPS con `/docs`, `/health`, logging seguro, *stubs* `501` por épica y esqueleto Jinja2 + `static/js/api.js`.
**Prueba independiente:** Levantar `uvicorn app.main:app` por HTTPS y comprobar `/`, `/docs` y `/health` en `200`, y endpoints *stub* `/api/v1/*` en `501`.

- [ ] T-001-17 [US1] Implementar `app/api/router.py`, stubs `/api/v1/{auth,eventos,catalogo,inscripciones,asistencia,reportes}.py` (`501 NO_IMPLEMENTADO`), rutas web stub en `app/web/` y ensamblar `app/main.py` con manejadores globales y `/docs` · Commit: `feat(api): crea app FastAPI, router v1 y stubs por epica` · Terminado cuando: `GET /docs` y `GET /openapi.json` responden `200`
- [ ] T-001-18 [US1] Implementar logging seguro por solicitud (`app/core/logging.py`, sin cuerpos, `Cookie`, `Authorization` ni documentos) y endpoint `GET /health` (`SELECT 1` + `PRAGMA foreign_keys`) · Commit: `feat(core): agrega endpoint GET /health y logging seguro por solicitud` · Terminado cuando: `GET /health` responde `200 {"status": "ok", "database": "ok"}` y el log omite datos sensibles
- [ ] T-001-19 [US4] Crear `app/templates/base.html` (Jinja2 con autoescape y navegación por rol), `app/templates/index.html`, `app/static/css/styles.css` y `app/static/js/api.js` (`fetch` a `/api/v1`, errores y fechas `America/Bogota` con `textContent`) · Commit: `feat(web): agrega esqueleto Jinja2, navegacion y cliente fetch comun` · Terminado cuando: `GET /` responde HTML `200` y `api.js` no contiene `innerHTML`

---

## Fase 5: Datos de prueba, documentación de contrato y verificación final (US3 + G3/G4)

**Objetivo:** Entregar `seed.py` idempotente, `crear_usuario.py`, `docs/diseno.md` inicial, `README.md` y pruebas integradas en verde.
**Prueba independiente:** Ejecutar `seed.py` 2 veces, probar `crear_usuario.py`, correr `ruff check . && ruff format --check .` y `pytest -q`.

- [ ] T-001-20 [US3] Implementar `scripts/seed.py` (idempotente: ≥1 coordinación, ≥2 organizadores, ≥6 participantes, ≥5 eventos en distintos estados con documentos ficticios) y `scripts/crear_usuario.py` (pide tipo/número de documento, valida formato y rechaza duplicado) · Commit: `feat(bd): agrega scripts seed idempotente y crear_usuario` · Terminado cuando: doble ejecución de `seed.py` no duplica registros y `crear_usuario.py` rechaza documento repetido
- [ ] T-001-21 [P] [US1] Redactar `README.md` inicial con guía detallada de entorno virtual (`venv`/`uv` en Windows/Linux/macOS), `.env`, generación de certificados `mkcert`/`openssl`, migraciones, seed y arranque HTTPS · Commit: `docs(repo): agrega README inicial con entorno virtual y arranque HTTPS` · Terminado cuando: todas las instrucciones coinciden con los scripts y rutas reales del repo
- [ ] T-001-22 [P] [US2] Crear `docs/diseno.md` con la sección inicial de **Contrato compartido** (`database.py`, `fechas.py`, `enums.py`, `errors.py`, `deps.py`, `inscripcion_repo.py` y códigos de error) para desbloquear al Integrante B · Commit: `docs(diseno): documenta contrato compartido inicial entre integrantes` · Terminado cuando: firmas, módulos y códigos coinciden exactamente con lo implementado en E1
- [ ] T-001-23 [US1] [US3] [US4] Completar pruebas `tests/test_scripts_web.py` (`/health`, `GET /`, stubs `501`, `get_current_user` `401`, idempotencia de `seed.py`, creación/duplicado en `crear_usuario.py`, ausencia de secretos en logs) · Commit: `test(core): agrega pruebas de health, web base, seed y crear_usuario` · Terminado cuando: toda la suite `pytest -q` pasa en verde sobre BD temporal
- [ ] T-001-24 Ejecutar verificación completa (`ruff check . && ruff format --check .`, `pytest -q`, `alembic upgrade head`, `python scripts/seed.py` y verificación de arranque HTTPS si `mkcert`/`openssl` está disponible) y actualizar checklist · Commit: `docs(specs): marca tareas verificadas de E1 tras pruebas en verde` · Terminado cuando: `ruff` y `pytest -q` pasan con 0 errores y el PR queda listo para revisión G4/G5

---

## Tabla resumen de trazabilidad

| ID | Tarea | Depende de | Archivos clave | Commit sugerido | Terminado cuando | Estado |
|---|---|---|---|---|---|:-:|
| T-001-01 | Estructura y stubs por épica | — | `app/**`, `migrations/`, `scripts/`, `tests/` | `chore(repo): crea estructura de capas y archivos base por epica` | Paquetes y stubs importables | [x] |
| T-001-02 | Verificar `.gitignore` y `.gitattributes` | — | `.gitignore`, `.gitattributes` | `chore(repo): verifica .gitignore y agrega .gitattributes` | Secretos/certs ignorados | [x] |
| T-001-03 | Fijar `requirements.txt` | — | `requirements.txt` | `chore(deps): fija dependencias base de FastAPI, SQLAlchemy y Jinja2` | Instalación limpia OK | [x] |
| T-001-04 | Crear `requirements-dev.txt` | T-001-03 | `requirements-dev.txt` | `chore(deps): agrega requirements-dev.txt con pytest, httpx y ruff` | Herramientas dev OK | [x] |
| T-001-05 | Configurar `ruff.toml` | — | `ruff.toml` | `chore(lint): configura ruff para lint y formato` | `ruff check .` operativo | [x] |
| T-001-06 | Scripts certificados TLS locales | T-001-02 | `scripts/generar_certificados.ps1`, `.sh` | `chore(repo): agrega scripts de certificados locales HTTPS con mkcert` | Genera `certs/` ignorado | [x] |
| T-001-07 | `conftest.py` y pruebas rojo base | T-001-01, T-001-04 | `tests/conftest.py`, `tests/test_seguridad_fechas_bd.py` | `test(core): agrega conftest HTTPS y pruebas rojo de reglas base` | Pruebas fallan antes de código | [x] |
| T-001-08 | `config.py` y `.env.example` | T-001-07 | `app/core/config.py`, `.env.example` | `feat(core): agrega configuracion segura por entorno y .env.example` | Validación arranque en verde | [x] |
| T-001-09 | `fechas.py` UTC y ventana 48 h | T-001-07 | `app/core/fechas.py` | `feat(core): agrega utilidades de fechas UTC y ventana de asistencia` | Pruebas fechas en verde | [x] |
| T-001-10 | `database.py` SQLite + PRAGMAs | T-001-08 | `app/core/database.py` | `feat(bd): configura SQLite con claves foraneas y sesion por solicitud` | `foreign_keys=1` y `busy_timeout=5000` | [x] |
| T-001-11 | Enums del dominio | T-001-01 | `app/models/enums.py` | `feat(bd): define enumeraciones de rol, documento, tipo y estados` | 9 enums del contrato listos | [x] |
| T-001-12 | Modelos ORM con restricciones | T-001-09, T-001-10, T-001-11 | `app/models/*.py` | `feat(bd): define modelos con restricciones CHECK, FK e indices` | `UNIQUE`/`CHECK`/parcial definidos | [x] |
| T-001-13 | Migración inicial Alembic | T-001-12 | `alembic.ini`, `migrations/**` | `feat(bd): agrega migracion inicial del esquema en Alembic` | `alembic upgrade head` + BD tests OK | [x] |
| T-001-14 | Errores de dominio y handlers | T-001-07 | `app/core/errors.py` | `feat(core): agrega errores de dominio y manejadores globales uniformes` | Errores uniformes sin `input` | [x] |
| T-001-15 | Firmas base en `deps.py` | T-001-11, T-001-14 | `app/api/deps.py` | `feat(api): define interfaz de dependencias de autenticacion y roles` | `401`/`None`/`require_roles` listos | [ ] |
| T-001-16 | Conteo activas en `inscripcion_repo.py` | T-001-12 | `app/repositories/inscripcion_repo.py` | `feat(bd): agrega conteo de inscripciones activas por evento` | Conteos filtran `activa` | [ ] |
| T-001-17 | `main.py`, `router.py` y stubs | T-001-14, T-001-15 | `app/main.py`, `app/api/**`, `app/web/**` | `feat(api): crea app FastAPI, router v1 y stubs por epica` | `/docs` `200` y stubs `501` | [ ] |
| T-001-18 | `GET /health` y logging seguro | T-001-10, T-001-17 | `app/core/logging.py`, `app/main.py` | `feat(core): agrega endpoint GET /health y logging seguro por solicitud` | `/health` `200`, logs limpios | [ ] |
| T-001-19 | `base.html`, `index.html`, CSS y `api.js` | T-001-17 | `app/templates/**`, `app/static/**` | `feat(web): agrega esqueleto Jinja2, navegacion y cliente fetch comun` | `GET /` `200`, sin `innerHTML` | [ ] |
| T-001-20 | `seed.py` y `crear_usuario.py` | T-001-13 | `scripts/seed.py`, `scripts/crear_usuario.py` | `feat(bd): agrega scripts seed idempotente y crear_usuario` | Seed idempotente + CLI doc | [ ] |
| T-001-21 | `README.md` inicial + guía venv/HTTPS | T-001-06, T-001-20 | `README.md` | `docs(repo): agrega README inicial con entorno virtual y arranque HTTPS` | Pasos reproducibles claros | [ ] |
| T-001-22 | `docs/diseno.md` Contrato compartido | T-001-16, T-001-18 | `docs/diseno.md` | `docs(diseno): documenta contrato compartido inicial entre integrantes` | Contrato alineado con código | [ ] |
| T-001-23 | Pruebas de integración web/seed/CLI | T-001-18, T-001-19, T-001-20 | `tests/test_scripts_web.py` | `test(core): agrega pruebas de health, web base, seed y crear_usuario` | `pytest -q` todo en verde | [ ] |
| T-001-24 | Verificación final E1 | T-001-05, T-001-21..23 | `specs/001-fundacion/tasks.md` | `docs(specs): marca tareas verificadas de E1 tras pruebas en verde` | `ruff` y `pytest` 100% verdes | [ ] |
