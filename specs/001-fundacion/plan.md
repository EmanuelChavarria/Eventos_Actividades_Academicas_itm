# Plan de Implementación: Fundación y plataforma (E1)

**Rama:** `001-fundacion` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/spec.md)
**Entrada:** Especificación aprobada en G1 en `specs/001-fundacion/spec.md` (sin `[PENDIENTE]` bloqueantes).

## 1. Resumen y decisiones técnicas

El objetivo de E1 es entregar una plataforma ejecutable por **HTTPS** desde el primer día y establecer el **contrato compartido** que desbloquea en paralelo al Integrante B (E5, E6, E7, E10) y las siguientes épicas del Integrante A (E2, E3, E4).

Decisiones principales y alternativas descartadas:
- **Configuración fail-fast al arrancar (`app/core/config.py`):** validar `SECRET_KEY` (no vacía, longitud ≥ 32 y distinta al valor de `.env.example`) y `COOKIE_SECURE == True` al cargar `Settings` en lugar de esperar al primer login en E2. *Descartado:* validar perezosamente en runtime, porque dejaría arrancar entornos inseguros sin aviso.
- **SQLite con PRAGMAs por conexión y migración única inicial:** enganchar un *listener* `connect` en SQLAlchemy (`app/core/database.py`) para ejecutar `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` y `PRAGMA journal_mode=WAL` (excepto si fuera `:memory:`, aunque las pruebas también usan archivo temporal). *Descartado:* configurar PRAGMAs solo en Alembic o en repositorios puntuales.
- **Almacenamiento estricto UTC con `TypeDecorator` (`app/core/fechas.py`):** crear `UTCDateTime(TypeDecorator)` que exige `tzinfo is not None` en Python (o convierte desde SQLite interpretando UTC al leer) y normaliza a UTC antes de persistir, más `tzdata` para conversión `America/Bogota` y reloj inyectable `ahora_utc()`. *Descartado:* `DateTime(timezone=True)` sin adaptador en SQLite, porque SQLite pierde la zona al leer y permite *naive datetimes* silenciosamente.
- **Stubs seguros (`401`/`501`) desde E1:** `app/api/deps.py` define las firmas reales (`get_current_user`, `get_current_user_optional`, `require_roles`), lanzando `401 CREDENCIALES_INVALIDAS` en `get_current_user` mientras E2 implementa JWT/cookies, y los routers *stub* de E2–E7 devuelven `501 NO_IMPLEMENTADO` (confirmado en clarificación G1). *Descartado:* retornar usuarios simulados o `200` vacío, por riesgo de dejar rutas abiertas por omisión.
- **HTTPS local con `mkcert` y alternativa `openssl`:** scripts dedicados `scripts/generar_certificados.ps1` y `scripts/generar_certificados.sh` generando `certs/localhost.pem` y `certs/localhost-key.pem` (carpeta `certs/` ya excluida en `.gitignore`). *Descartado:* arranque por HTTP plano en local.
- **Contrato compartido documentado desde E1:** crear sección inicial en `docs/diseno.md` para que el Integrante B tenga referencia inmediata de tipos, errores y dependencias (confirmado en clarificación G1).

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.12 (compatible 3.11+, `ruff` configurado con `target-version = "py311"`).
- **Dependencias principales (`requirements.txt`):** `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `pydantic`, `pydantic-settings`, `email-validator`, `jinja2`, `python-multipart`, `argon2-cffi`, `PyJWT`, `tzdata` (versiones fijadas `==` al instalar en entorno limpio).
- **Almacenamiento:** SQLite (`PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`, WAL, UTC en fechas).
- **Pruebas y calidad (`requirements-dev.txt`):** `pytest`, `httpx`, `ruff`, `pre-commit`.
- **Plataforma objetivo:** Windows, macOS y Linux (con entorno virtual `venv`/`uv`); preparación compatible con Docker (E10).
- **Restricciones:** Sin bundler ni SPA; sin lista de espera ni aprobación de eventos; propiedad estricta de archivos por integrante; sin `innerHTML` con datos dinámicos; prohibido escribir documentos/tokens/cookies en logs.

## 3. Verificación contra la constitución *(puerta obligatoria)*

Revisión frente a `.specify/memory/constitution.md` (v2.0.2):
- [x] I. La spec manda (`specs/001-fundacion/spec.md` aprobada en G1, sin `[PENDIENTE]` bloqueantes)
- [x] II. Capas estrictas (`api` → `services` → `repositories` → `models`; `services/` sin FastAPI; solo `repositories/` escribe SQL)
- [x] III. Validación en servidor (Pydantic v2 en `config.py`/scripts) y en BD (`PK`, `FK`, `UNIQUE`, `CHECK`, índice parcial `WHERE estado='activa'`)
- [x] IV. Cupo atómico calculado (`contar_activas` y `contar_activas_por_eventos` listos en `inscripcion_repo.py`; no se almacena cupo disponible)
- [x] V. Mínimo privilegio (firmas `get_current_user`/`require_roles` en `deps.py` rechazando con `401` por defecto en E1)
- [x] VI. Errores uniformes sin trazas ni datos sensibles (`ErrorDominio`, `RequestValidationError` omitiendo `input`, `HTTPException`, `Exception`)
- [x] VII. Sin secretos ni datos reales (`.env`, `*.db`, `certs/`, `*.pem`, `*.key`, `*.crt` en `.gitignore`; documentos ficticios en `seed.py`)
- [x] VIII. Commits atómicos en español, rama `001-fundacion`, PR en borrador en G2
- [x] IX. `ruff` y `pytest` en verde antes de G4 (y `export_openapi.py --check` cuando E10 esté en `main`)
- [x] X. Reproducible sin Docker desde E1 (`README.md` con guía detallada de `venv`/`uv` en Windows/Linux/macOS, HTTPS y dependencias fijadas)
- [x] XI. Define el contrato compartido de E1 sin tocar archivos exclusivos de E5–E7 más allá de sus *stubs* iniciales acordados
- [x] XII. Dudas resueltas con el humano en clarificación G1 (`docs/diseno.md` inicial y comportamiento `401`/`501` de *stubs*)

## 4. Estructura y archivos por capa

```text
specs/001-fundacion/
├── spec.md              # Especificación aprobada (G1)
├── plan.md              # Este documento
├── data-model.md        # Esquema SQLite completo, restricciones e índices
├── quickstart.md        # Guía rápida de verificación local HTTPS + migración + seed
├── checklists/
│   └── requirements.md  # Checklist de calidad de spec
└── tasks.md             # Tareas atómicas T-001-XX
```

| Capa / Ámbito | Archivos a crear o verificar en E1 | Responsable |
|---|---|:-:|
| Raíz y calidad | `.gitignore` (verificado), `.gitattributes`, `.env.example`, `requirements.txt`, `requirements-dev.txt`, `ruff.toml`, `alembic.ini`, `README.md` | A |
| Docs contrato | `docs/diseno.md` (sección inicial Contrato compartido) | A |
| Core | `app/core/__init__.py`, `config.py`, `database.py`, `fechas.py`, `errors.py`, `logging.py`, `security.py` (stub para E2) | A |
| Modelos | `app/models/__init__.py`, `enums.py`, `usuario.py`, `evento.py`, `inscripcion.py`, `asistencia.py` | A |
| Migraciones | `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_esquema_inicial.py` | A |
| Schemas | `app/schemas/__init__.py` + stubs `{auth,evento,catalogo,inscripcion,asistencia,reporte}.py` | A |
| Repositorios | `app/repositories/__init__.py`, `inscripcion_repo.py` (`contar_activas`, `contar_activas_por_eventos`) + stubs `{usuario,evento,asistencia,reporte}_repo.py` | A |
| Servicios | `app/services/__init__.py` + stubs `{auth,evento,catalogo,inscripcion,asistencia,reporte}_service.py` | A |
| API REST | `app/main.py`, `app/api/__init__.py`, `deps.py`, `router.py`, `app/api/v1/__init__.py` + stubs `{auth,eventos,catalogo,inscripciones,asistencia,reportes}.py` | A |
| Web y Frontend | `app/web/__init__.py` + rutas base/`index` y stubs `{auth,eventos,catalogo,inscripciones,asistencia,reportes}.py`, `app/templates/base.html`, `app/templates/index.html`, `app/static/css/styles.css`, `app/static/js/api.js` | A |
| Scripts | `scripts/seed.py`, `scripts/crear_usuario.py`, `scripts/generar_certificados.ps1`, `scripts/generar_certificados.sh` | A |
| Pruebas | `tests/__init__.py`, `tests/conftest.py`, `tests/test_config_fechas.py`, `tests/test_bd_errores.py`, `tests/test_scripts_web.py` | A |

## 5. Contrato de API, modelo de datos y seguridad

- **Endpoints activos en E1:**
  - `GET /health` → `200 {"status": "ok", "database": "ok"}` (ejecuta `SELECT 1` y verifica `PRAGMA foreign_keys = 1`; `503` si falla conectividad BD).
  - `GET /` → `200 text/html` (renderiza `base.html` / `index.html` con autoescape y `static/js/api.js`).
  - `GET /docs`, `GET /openapi.json` → `200` (OpenAPI interactivo habilitado).
  - Routers `/api/v1/{auth,eventos,catalogo,inscripciones,asistencia,reportes}` → *stubs* documentados respondiendo `501 NO_IMPLEMENTADO` con formato de error uniforme hasta que cada épica los implemente.
- **Schemas:** `app/schemas/` inicia con paquete y archivos *stub* tipados por épica sin exponer nunca `hash_password`.
- **Cambios en BD / SQLite:** detallado en [data-model.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/data-model.md) (4 tablas `usuarios`, `eventos`, `inscripciones`, `asistencias`, restricciones `PK`, `FK`, `UNIQUE`, `CHECK`, índice único parcial `WHERE estado = 'activa'`, y `UTCDateTime`).
- **Seguridad y privacidad:**
  - Arranque bloqueado si `SECRET_KEY` está vacía, `< 32` chars o igual al placeholder de `.env.example`, o si `COOKIE_SECURE` no es `true`.
  - Certificados TLS generados localmente en `certs/` (`mkcert` / `openssl`) e ignorados por Git.
  - Hashing `argon2id` utilizado ya desde `seed.py` y `crear_usuario.py` (vía `argon2.PasswordHasher`).
  - Middleware de logging en `app/core/logging.py`: registra método, ruta, status y latencia; **nunca** cuerpos, `Cookie`, `Authorization` ni documentos.
  - Manejador `RequestValidationError` en `app/core/errors.py`: elimina el campo `input` en `detalles` para no filtrar contraseñas o documentos.
  - Frontend `static/js/api.js`: envoltorio `fetch` con `credentials: 'same-origin'`, extracción uniforme de errores, formato de fechas `Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', ... })` y helpers DOM seguros (`textContent`, sin `innerHTML`).

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| `sqlite3` pierde información `tzinfo` al leer fechas almacenadas | Implementar `UTCDateTime(TypeDecorator)` en `app/core/fechas.py` que adjunta `timezone.utc` al leer y exige zona horaria al escribir |
| Bloqueos momentáneos en pruebas multi-hilo sobre SQLite | Configurar `PRAGMA busy_timeout=5000` y `WAL` en `app/core/database.py` y usar archivo temporal en `tests/conftest.py` (nunca `:memory:`) |
| `mkcert` aún no instalado en el equipo al ejecutar manualmente HTTPS | Incluir `scripts/generar_certificados.ps1` / `.sh` con soporte `mkcert` y alternativa `openssl`, más guía clara en `README.md` y [quickstart.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/001-fundacion/quickstart.md); pruebas automatizadas usan `TestClient(base_url="https://testserver")` |
| Conflictos futuros entre Integrante A y B en archivos compartidos | Crear todos los archivos *stub* por épica en E1 y congelar la firma del contrato compartido en `docs/diseno.md` |

## 7. Registro de complejidad (solo si hay excepciones)

| Excepción | Por qué es necesaria | Alternativa más simple descartada |
|---|---|---|
| — | Ninguna excepción a la arquitectura o constitución | — |
