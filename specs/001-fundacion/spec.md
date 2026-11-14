# Especificación de Feature: Fundación y plataforma (E1)

- **Épica:** E1 · **Condiciones:** CA-01 (base cuentas personal), base transversal (CA-02..CA-06) · **Requisitos:** RF-04, RF-27 (base), RF-28, RF-29; RNF-01, RNF-03, RNF-05 (configuración y HTTPS), RNF-07, RNF-10, RNF-11, RNF-15, RNF-16 (base UTC/`tzdata`), RNF-17, RNF-22, RNF-23 (base fixtures)
- **Rama de feature:** `001-fundacion` · **Creada:** 2026-11-14
- **Estado:** aprobada · **Responsable:** Integrante A
- **Entrada:** Descripción del usuario: `"E1 Fundación y plataforma: esqueleto ejecutable, configuración HTTPS, base de datos SQLite con migraciones, contrato compartido, layout web base y datos de prueba ficticios"`

## 1. Objetivo y alcance

Establecer la base ejecutable y el contrato compartido del proyecto **PF-04 — Organización de eventos y actividades académicas** para desbloquear el desarrollo paralelo de las épicas E2–E7 (Integrantes A y B).

Incluye dentro del alcance:
- Estructura modular en capas (`api` → `services` → `repositories` → `models`) con archivos *stub* por épica para evitar conflictos de fusión.
- Configuración tipada por entorno y `.env.example`, con validación estricta al arranque (`SECRET_KEY` y `COOKIE_SECURE=true`), dependencias fijadas (`requirements.txt` y `requirements-dev.txt`) y reglas de calidad (`ruff.toml`, `.gitignore`).
- Motor SQLite con `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000` por conexión, enumeraciones del dominio, modelos ORM (`Usuario`, `Evento`, `Inscripcion`, `Asistencia`) con restricciones de integridad y migración inicial de Alembic (incluyendo índice único parcial).
- Contrato compartido inicial: `app/core/database.py`, `app/core/fechas.py` (UTC ↔ `America/Bogota`, ventana de asistencia de 48 h y reloj inyectable), `app/models/enums.py`, `app/core/errors.py` (jerarquía `ErrorDominio` y manejadores globales uniformes), `app/api/deps.py` (firmas de dependencias de autenticación/roles) y `app/repositories/inscripcion_repo.py` (`contar_activas` y `contar_activas_por_eventos`).
- Enrutador versionado (`/api/v1`), documentación interactiva `/docs`, endpoint `GET /health` y middleware de logging seguro por solicitud.
- Esqueleto web Jinja2 (`base.html` con autoescape y navegación por rol), estilos CSS base y cliente JS común (`static/js/api.js`) con `fetch` a `/api/v1`, manejo de errores y formateo de fechas en `America/Bogota`.
- Scripts reproducibles: `scripts/seed.py` (idempotente, con documentos obviamente ficticios), `scripts/crear_usuario.py` (creación administrativa de organizadores y coordinación pidiendo tipo y número de documento) y `scripts/generar_certificados.ps1` / `.sh` (`mkcert`, alternativa `openssl`) para servir todo entorno por **HTTPS**.
- Base de pruebas (`tests/conftest.py` con BD SQLite en archivo temporal, cliente HTTPS `base_url="https://testserver"` y fábricas por rol), sección inicial de **Contrato compartido** en `docs/diseno.md` (que E9-A completará) y guía de instalación/entorno virtual (`venv`/`uv` en Windows/Linux/macOS) e inicio por HTTPS en `README.md`.

## 2. Fuera de alcance

- Flujos completos de registro público, login, logout, emisión de JWT/cookies y límite de 10 intentos fallidos (pertenecen a **E2**).
- CRUD y transiciones de estado de eventos (pertenecen a **E3**).
- Catálogo público de eventos con filtros y paginación real (pertenece a **E4**; en E1 `/` solo sirve el esqueleto HTML base).
- Inscripciones, cancelaciones, control atómico con `BEGIN IMMEDIATE`, asistencia y consolidado/CSV (pertenecen a **E5**, **E6** y **E7**).
- `Dockerfile`, `docker-compose.yml` y workflow CI en GitHub Actions (pertenecen a **E10**; en E1 solo se dejan instrucciones locales replicables).

## 3. Historias de usuario y criterios de aceptación *(obligatorio)*

### Historia de Usuario 1 - Arranque seguro por HTTPS y verificación de salud (Prioridad: P1)

Como desarrollador del equipo quiero clonar el repositorio, configurar el entorno virtual y certificados TLS locales, e iniciar la aplicación en pocos comandos para verificar que responde por HTTPS en `/`, `/docs` y `/health`.

- **Por qué esta prioridad:** Sin una aplicación ejecutable, configurada y segura al arranque, ninguna épica posterior puede desarrollarse ni probarse.
- **Prueba independiente:** Siguiendo el `README.md` en un entorno limpio con `.env` válido y certificados en `certs/`, levantar el servidor con Uvicorn HTTPS y consultar `GET /`, `GET /docs` y `GET /health`.
- **Escenarios de aceptación:**
  1. **Dado** un entorno virtual limpio con dependencias instaladas, archivo `.env` válido (`SECRET_KEY` robusta y `COOKIE_SECURE=true`) y certificados locales generados en `certs/`, **Cuando** se ejecuta `uvicorn app.main:app --reload --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost.pem`, **Entonces** la aplicación arranca sin errores y `GET /docs` y `GET /` responden HTTP `200`.
  2. **Dado** un archivo `.env` con `SECRET_KEY` vacía, menor a 32 caracteres o igual al valor de `.env.example`, **Cuando** se intenta iniciar la aplicación, **Entonces** el arranque falla explícitamente con error de configuración antes de aceptar tráfico.
  3. **Dado** un archivo `.env` con `COOKIE_SECURE` distinto de `true`, **Cuando** se intenta iniciar la aplicación, **Entonces** el arranque falla explícitamente rechazando configuración insegura.
  4. **Dado** la aplicación en ejecución con BD migrada, **Cuando** se consulta `GET /health`, **Entonces** responde HTTP `200` verificando conectividad con SQLite (`SELECT 1`) y emite un log de solicitud sin cuerpos, cookies, tokens ni números de documento.

---

### Historia de Usuario 2 - Esquema de base de datos versionado y contrato compartido (Prioridad: P1)

Como integrante del equipo quiero un esquema SQLite versionado con Alembic, restricciones de integridad activas y el contrato compartido implementado para construir sobre él los módulos de E2–E7 sin divergencias.

- **Por qué esta prioridad:** Bloquea directamente al Integrante B (E5, E6, E7) y al propio Integrante A (E2, E3, E4).
- **Prueba independiente:** Ejecutar `alembic upgrade head` sobre una BD nueva, inspeccionar tablas, claves foráneas, restricciones `CHECK`/`UNIQUE` e índice único parcial, y ejecutar pruebas unitarias del contrato (`fechas.py`, `errors.py`, `inscripcion_repo.py`).
- **Escenarios de aceptación:**
  1. **Dado** una base de datos SQLite inexistente o vacía, **Cuando** se ejecuta `alembic upgrade head`, **Entonces** se crean las 4 tablas (`usuarios`, `eventos`, `inscripciones`, `asistencias`) con todas sus PK, FK, `CHECK`, `UNIQUE(tipo_documento, numero_documento)`, `UNIQUE(inscripcion_id)` y el índice único parcial sobre `(evento_id, participante_id) WHERE estado = 'activa'`.
  2. **Dado** cualquier sesión obtenida mediante `get_db()`, **Cuando** se consulta `PRAGMA foreign_keys` y `PRAGMA busy_timeout`, **Entonces** `foreign_keys` es `1` (ON) y `busy_timeout` es `5000`.
  3. **Dado** un endpoint que lanza `ErrorDominio` (o un error de validación `RequestValidationError` / `HTTPException`), **Cuando** FastAPI responde al cliente, **Entonces** retorna exactamente el formato JSON `{"error": {"codigo": "...", "mensaje": "...", "detalles": [...]}}` sin trazas internas ni campo `input`.
  4. **Dado** fechas con zona horaria (`-05:00` o `UTC`) o sin zona horaria (*naive*) enviadas a las utilidades de `app/core/fechas.py`, **Cuando** se procesan, **Entonces** las fechas válidas se almacenan en UTC, la ventana de asistencia valida `[fecha_inicio, fecha_fin + 48h]` en UTC y las fechas sin zona se rechazan con error de validación (HTTP `422`).

---

### Historia de Usuario 3 - Datos de prueba ficticios y creación de personal administrativo (Prioridad: P2)

Como equipo queremos poblar la base de datos de forma repetible con usuarios y eventos ficticios, y crear cuentas de organizador o coordinación por consola, respetando la identificación única por documento.

- **Por qué esta prioridad:** Permite probar manualmente la interfaz, verificar permisos por rol y alimentar pruebas funcionales desde E1 sin auto-registro de personal.
- **Prueba independiente:** Ejecutar `python scripts/seed.py` dos veces seguidas sobre una BD migrada y ejecutar `python scripts/crear_usuario.py` para crear un organizador y verificar rechazo ante documento duplicado.
- **Escenarios de aceptación:**
  1. **Dado** una BD recién migrada, **Cuando** se ejecuta `python scripts/seed.py`, **Entonces** crea al menos 1 usuario de `coordinacion`, 2 de `organizador`, 6 `participante` (estudiantes y docentes) y 5 `evento` en distintos estados (`borrador`, `publicado`, `cancelado`, incluyendo al menos uno con fecha ya finalizada), todos con documentos obviamente ficticios.
  2. **Dado** una BD ya poblada por `seed.py`, **Cuando** se vuelve a ejecutar `python scripts/seed.py`, **Entonces** finaliza sin error y sin duplicar usuarios ni eventos (idempotencia).
  3. **Dado** un administrador ejecutando `python scripts/crear_usuario.py`, **Cuando** ingresa rol (`organizador` o `coordinacion`), `tipo_documento`, `numero_documento`, nombre, correo y contraseña válida (≥ 8 caracteres), **Entonces** el usuario se crea en BD con hash `argon2id` y documento normalizado.
  4. **Dado** un `tipo_documento` y `numero_documento` ya existentes en BD, **Cuando** se intenta crear otro usuario con esa misma combinación mediante `crear_usuario.py`, **Entonces** la creación es rechazada informando conflicto de documento duplicado sin crear un registro parcial.

---

### Historia de Usuario 4 - Esqueleto web seguro y cliente API común (Prioridad: P2)

Como desarrollador del frontend quiero una plantilla base Jinja2 con navegación adaptada por rol y un cliente JavaScript común para que todas las vistas consuman `/api/v1` de forma segura y consistente.

- **Por qué esta prioridad:** Garantiza uniformidad visual, protección XSS y manejo coherente de zona horaria `America/Bogota` desde la primera página.
- **Prueba independiente:** Abrir `GET /` en navegador (o verificar HTML en `pytest`) comprobando estructura `base.html`, carga de `static/js/api.js` y utilidades de formato de fecha y errores sin usar `innerHTML`.
- **Escenarios de aceptación:**
  1. **Dado** un visitante accediendo a `GET /`, **Cuando** el servidor renderiza la vista, **Entonces** devuelve HTML válido basado en `base.html` con autoescape activo, menú de navegación y enlace a `static/js/api.js`.
  2. **Dado** una llamada desde `static/js/api.js` a un endpoint `/api/v1/...`, **Cuando** ocurre una respuesta de error uniforme `{"error": ...}` o se muestra una fecha ISO-8601 UTC/`-05:00`, **Entonces** el cliente JS expone funciones reutilizables para extraer el mensaje de error y formatear fechas en `America/Bogota` usando exclusivamente APIs seguras del DOM (`textContent`), nunca `innerHTML`.

## 4. Reglas de negocio y validaciones

- **RN-02, RN-03, RN-04, RN-12, RN-13, RN-14, RN-18, RN-21 (aplicadas a esquema, scripts y utilidades en E1):**
  - `usuarios`: `UNIQUE(tipo_documento, numero_documento)`; `correo` obligatorio no único; `tipo_participante` (`estudiante`/`docente`) nulo permitido para `organizador`/`coordinacion`; `CHECK` de longitud de documento (5–15 caracteres tras normalización sin espacios ni puntos, `PAS` en mayúsculas; CC/CE/TI solo dígitos 5–12 validado en Pydantic y en `crear_usuario.py`).
  - `eventos`: `CHECK(cupo_maximo >= 1)`, `CHECK(fecha_fin > fecha_inicio)`, `CHECK(fecha_limite_inscripcion <= fecha_inicio)`, índice `(estado, fecha_inicio)`. Estados permitidos: `borrador`, `publicado`, `cancelado`.
  - `inscripciones`: estados `activa`, `cancelada`; **índice único parcial** `UNIQUE(evento_id, participante_id) WHERE estado = 'activa'`; índices por `evento_id` y `participante_id`. `cupos_disponibles` se calcula dinámicamente con `contar_activas` / `contar_activas_por_eventos`, nunca se almacena.
  - `asistencias`: `UNIQUE(inscripcion_id)`; estados `presente`, `ausente`; FK a `usuarios` en `registrado_por_id`.
- **Validaciones de configuración al arranque (`app/core/config.py`):**
  - `SECRET_KEY`: obligatoria, longitud ≥ 32 caracteres y distinta al valor de ejemplo en `.env.example`.
  - `COOKIE_SECURE`: obligatoria y estrictamente `true` en todos los entornos.
  - `DATABASE_URL`: ruta válida a SQLite (por defecto local en desarrollo/pruebas, ignorada por Git).
- **Validaciones en `app/core/fechas.py`:**
  - Toda fecha recibida debe incluir información de zona horaria (`tzinfo is not None`); de lo contrario se rechaza (HTTP `422`).
  - Conversión interna y almacenamiento en **UTC** mediante tipo ORM `TypeDecorator`; utilidad de ventana de asistencia válida `[fecha_inicio, fecha_fin + 48 horas]` y conversión a `America/Bogota`.

## 5. Errores esperados *(obligatorio)*

Formato uniforme de respuesta: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre | Notas de seguridad |
|---|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | Endpoint que invoque `get_current_user` sin sesión válida (firma base en `deps.py`) | No expone detalles de token ni cabeceras |
| 403 | `SIN_PERMISO` | Rol insuficiente en `require_roles` o acceso no autorizado | No revela estado interno de otros recursos |
| 404 | `EVENTO_NO_ENCONTRADO` / `INSCRIPCION_NO_ENCONTRADA` / `RECURSO_NO_ENCONTRADO` | `NoEncontrado` de dominio o ruta inexistente vía `HTTPException` | Sin rutas físicas ni trazas |
| 409 | `DOCUMENTO_DUPLICADO` / conflictos de dominio | Subclases de `Conflicto` (ej. duplicado de documento al crear usuario) | Sin mostrar documentos de terceros en logs |
| 422 | `ERROR_VALIDACION` / `REGLA_NEGOCIO` | `RequestValidationError` de FastAPI/Pydantic o `ReglaNegocio` (ej. fecha sin zona horaria) | **Omite el campo `input`** para no filtrar contraseñas ni documentos |
| 501 | `NO_IMPLEMENTADO` | Endpoints *stub* de E2–E7 antes de implementar su respectiva épica | Indica épica pendiente sin exponer detalles internos |
| 500 | `ERROR_INTERNO` | Excepción no controlada | Mensaje genérico sin *stacktrace* ni datos de BD |

## 6. Seguridad, privacidad y zona horaria aplicables

- **Configuración y HTTPS obligatorio:** Certificados locales con `mkcert` (alternativa `openssl`) generados mediante `scripts/generar_certificados.ps1` / `.sh` dentro de `certs/`. `.gitignore` excluye `.env`, `*.db`, `.venv/`, `__pycache__/`, `certs/`, `*.pem`, `*.key` y `*.crt`. La aplicación rechaza arrancar si `COOKIE_SECURE != true` o `SECRET_KEY` es insegura.
- **Autorización y mínimo privilegio:** `app/api/deps.py` define `get_current_user`, `get_current_user_optional` y `require_roles(*roles)` verificando estado `activo` del usuario cuando E2 complete el flujo; en E1 los *stubs* protegidos no otorgan acceso por defecto (rechazan con `401` o `501` controlado si aún no tienen lógica de negocio).
- **Privacidad y logs:** El middleware de logging registra únicamente método, ruta, código de estado HTTP y duración en ms. Queda prohibido registrar cuerpos de petición/respuesta, cabeceras `Cookie` o `Authorization`, contraseñas o `numero_documento`. Los manejadores de `RequestValidationError` eliminan `input` de cada elemento de `detalles`. Los datos de `scripts/seed.py` usan documentos obviamente ficticios (p. ej. `1000000001`–`1000000009`).
- **Seguridad web:** Plantillas Jinja2 con `autoescape=True`. `static/js/api.js` construye nodos con `textContent` (prohibido `innerHTML` con datos de usuario o API) y prepara envío con `credentials: 'same-origin'`.
- **Fechas:** Almacenamiento en **UTC** en SQLite (garantizado por `TypeDecorator` + `tzdata`); comparaciones de negocio en UTC; presentación de ejemplo y helpers JS en `America/Bogota`.

## 7. Casos límite

- Arranque de la app con `.env` ausente, `SECRET_KEY` igual a `.env.example`, `SECRET_KEY` corta (< 32 caracteres) o `COOKIE_SECURE=false`: debe abortar el arranque sin iniciar servidor.
- Ejecución repetida (≥ 2 veces) de `scripts/seed.py`: no debe fallar por `UNIQUE` ni crear filas repetidas.
- Intento de insertar en SQLite una inscripción con `evento_id` inexistente o `cupo_maximo <= 0` o `fecha_fin <= fecha_inicio` saltándose Pydantic: la propia BD debe rechazar la operación vía `PRAGMA foreign_keys=ON` y restricciones `CHECK`.
- Intento de insertar una segunda inscripción con `estado='activa'` para la misma pareja `(evento_id, participante_id)` en SQLite: el índice único parcial debe impedirlo, mientras que múltiples registros con `estado='cancelada'` + uno `'activa'` sí deben permitirse.
- Envío de cuerpo JSON inválido o campo con contraseña/documento fallando validación Pydantic: la respuesta `422` mantiene el formato `{"error": ...}` y **no** incluye el valor enviado (`input`).
- Dos hilos simultáneos intentando escribir en SQLite: `PRAGMA busy_timeout=5000` evita fallo inmediato por bloqueo corto en pruebas de concurrencia sobre BD temporal en archivo.

## 8. Supuestos y pendientes

- `[SUPUESTO S-01]` (aprobado por equipo): Las cuentas de `organizador` y `coordinacion` se crean únicamente mediante `scripts/seed.py` y `scripts/crear_usuario.py` pidiendo tipo y número de documento.
- `[SUPUESTO S-03]` (aprobado por equipo): Identificación única por `(tipo_documento, numero_documento)`; el correo electrónico es obligatorio como contacto y no es único.
- `[SUPUESTO S-11]` (confirmado por cliente): Zona horaria del usuario `America/Bogota` (UTC-5), almacenamiento y comparaciones en UTC.
- `[SUPUESTO S-14]` (confirmado por cliente): Toda la interfaz, mensajes de error y documentación del usuario final en español.
- `[SUPUESTO S-16]` (**confirmado por el humano**): Mientras E2–E7 no implementen su lógica, `get_current_user` en `app/api/deps.py` lanzará `401` (`CREDENCIALES_INVALIDAS`), `get_current_user_optional` devolverá `None` y los endpoints *stub* de E2–E7 responderán `501` (`NO_IMPLEMENTADO`); además, E1 creará `docs/diseno.md` con la sección inicial del **Contrato compartido** (ampliada luego en E9-A).
- `[SUPUESTO S-17]` (decisión técnica por defecto para E1, verificable en G1): `GET /health` responderá `200` `{"status": "ok", "database": "ok"}` validando conexión SQLite y `PRAGMA foreign_keys = 1`.
- *Pendientes bloqueantes:* Ninguno (`[PENDIENTE: ...]` vacío tras aplicar constitución v2.0.2 y decisiones del cliente).

## 9. Criterios de éxito y verificación *(obligatorio)*

- **Criterios medibles:**
  - **SC-001:** En un entorno virtual limpio (`venv` o `uv`) siguiendo `README.md`, `alembic upgrade head`, `python scripts/seed.py` y el arranque de `uvicorn app.main:app` por **HTTPS** completan sin errores y sirven `GET /`, `GET /docs` y `GET /health` con HTTP `200`.
  - **SC-002:** La ejecución repetida de `scripts/seed.py` mantiene exactamente los mismos conteos iniciales (≥ 1 coordinación, ≥ 2 organizadores, ≥ 6 participantes, ≥ 5 eventos) sin duplicados ni errores.
  - **SC-003:** El 100 % de las respuestas de error probadas (`ErrorDominio`, `RequestValidationError`, `HTTPException`) cumplen exactamente `{"error": {"codigo", "mensaje", "detalles"}}` y omiten `input`, contraseñas y documentos.
  - **SC-004:** `ruff check .` y `ruff format --check .` pasan con 0 advertencias/errores tras el último commit.
  - **SC-005:** Todos los archivos del contrato compartido existen con sus firmas documentadas para desbloquear E2–E7 sin tocar archivos fuera de alcance.
- **Pruebas funcionales (PF):** Base requerida para todas las pruebas **PF-01…PF-12** (entorno limpio, HTTPS, migración, seed y layout base).
- **Pruebas automatizadas (`pytest`):** Suite base en `tests/` ejecutándose contra BD temporal en archivo y `TestClient(app, base_url="https://testserver")` cubriendo como mínimo:
  1. Validación de arranque (`SECRET_KEY` vacía/corta/igual a `.env.example` y `COOKIE_SECURE != true` fallan).
  2. `GET /health` responde `200` y `PRAGMA foreign_keys=1` + `PRAGMA busy_timeout=5000` activos por conexión.
  3. Formato uniforme de errores para `ErrorDominio`, `HTTPException` y `RequestValidationError` (verificando ausencia del campo `input` y de datos sensibles en respuesta y logs).
  4. Restricciones de BD: FK activas, `UNIQUE(tipo_documento, numero_documento)`, `CHECK` de cupo y fechas, e índice único parcial de inscripción activa (permitiendo varias `cancelada` y rechazando segunda `activa`).
  5. Utilidades de `app/core/fechas.py`: conversión UTC, rechazo de fecha *naive* (422) y ventana de asistencia de 48 h.
  6. Idempotencia de `scripts/seed.py` y creación/rechazo por duplicado en `scripts/crear_usuario.py`.
