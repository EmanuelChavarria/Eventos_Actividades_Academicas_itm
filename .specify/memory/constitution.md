<!--
Informe de impacto de sincronización:
- Cambio de versión: 2.0.1 → 2.0.2 (PARCHE: HTTPS obligatorio en todos los entornos, con certificados locales mkcert y cookie Secure obligatoria)
- Versión anterior 2.0.0 → 2.0.1: ajustes de seguridad sobre las reglas establecidas
- Principios ajustados: III (SQLite PRAGMA/UTC), IV (BEGIN IMMEDIATE), V (activo==True), VI (422 sin input y logs sin datos sensibles), VIII (-Number N en Spec Kit), IX (OpenAPI/CI tras E10)
- Reglas y pila ajustadas: argon2id, hash ficticio en login, rate limit de 10 intentos en login, JWT HS256 con sub=id y SECRET_KEY validado, cookie con Path/Secure/Max-Age, CSRF Origin/Referer, XSS textContent, CSV seguro, LIKE escapado
- Plantillas actualizadas: .specify/templates/{spec,plan,tasks,checklist}-template.md
- Pendientes: ninguno
-->
# Constitución del Proyecto Final PF-04 — Organización de eventos y actividades académicas

## Principios fundamentales

### I. La spec manda (NO NEGOCIABLE)
Sin spec aprobada no hay código. Cualquier divergencia de comportamiento se corrige primero en la spec (commit `docs(specs): ...`) y después en el código, en commits separados. El ciclo es `/speckit.constitution → specify → clarify → plan → tasks → analyze → implement`; `clarify` es obligatorio antes de `plan` y `analyze` va antes de `implement`.

### II. Capas estrictas
`api` (routers) → `services` → `repositories` → `models`. Las reglas de negocio viven solo en `services/`; los routers validan entrada, invocan servicios y traducen errores de dominio; solo los repositorios escriben SQL. Los services no importan FastAPI.

### III. Validar en el servidor y en la BD
Toda entrada se valida en el servidor (Pydantic v2) y la integridad se garantiza también en la BD: PK, FK con `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000` por conexión, `UNIQUE`, `CHECK`, índice único parcial de inscripción activa y escape de comodines en filtros `LIKE`.

### IV. El cupo nunca se excede
La inscripción es una operación atómica en una sola transacción iniciada con `BEGIN IMMEDIATE` en SQLite (sentencia condicional + índice único parcial). El cupo disponible se calcula (`cupo_maximo − inscripciones activas`), nunca se almacena. Una inscripción rechazada no deja registros parciales ni altera cupos.

### V. Mínimo privilegio
Autorización por rol y por propietario en cada endpoint y página (prevención de IDOR), verificando además `usuario.activo == True` al autenticar y en cada sesión. Organizador: solo sus eventos. Coordinación: solo lectura global. Participante: solo lo propio.

### VI. Errores uniformes
Formato `{"error": {"codigo", "mensaje", "detalles"}}`, código HTTP correcto (200, 201, 204, 400/422, 401, 403, 404, 409, 429) y sin trazas ni datos sensibles (incluido el documento de identidad) en respuestas ni logs. Los manejadores globales cubren `ErrorDominio`, `RequestValidationError` (omitiendo el campo `input`) y `HTTPException`.

### VII. Sin secretos ni datos reales
Ningún secreto, `.env` ni `*.db` en el repositorio; solo `.env.example`. Configuración por entorno y datos ficticios; los documentos del seed son números obviamente falsos. La aplicación valida `SECRET_KEY` al arrancar y falla si está vacía, es corta o conserva el valor de `.env.example`.

### VIII. Commits atómicos y ramas por feature
Conventional Commits en español (≤ 72 caracteres), un commit por tarea de `tasks.md`. Una rama por feature con el esquema de Spec Kit `NNN-slug` creada con `-Number N` explícito según la tabla épica ↔ feature (p. ej. `003-gestion-eventos`). Nunca se trabaja en `main`; todo llega por Pull Request revisado por el compañero, con merge commit.

### IX. CI verde antes de fusionar
`ruff` y `pytest` deben pasar antes de cada PR; `export_openapi.py --check` y el CI completo aplican desde la integración de E10 en `main`. Ningún check se desactiva, ignora ni se omite (`--no-verify`) para «pasar».

### X. Reproducible con y sin Docker
El README documenta ambas vías con las mismas dependencias fijadas (`tzdata` incluido), migraciones Alembic, seed idempotente y la generación de certificados locales con `mkcert` (alternativa `openssl`). La guía no exige Docker, por lo que la ejecución local debe funcionar sola.

### XI. Contrato compartido
Modelos, errores, dependencias, enums y `specs/contrato/openapi.json` solo se cambian con acuerdo de ambos integrantes. El contrato OpenAPI se regenera con el script, nunca a mano.

### XII. Ante la duda, se pregunta
Cuando hay duda se pregunta al humano (y este al cliente o al docente); no se asume en silencio. Lo no confirmado por el cliente se rotula como supuesto (`S-XX`) y nunca se inventan respuestas del cliente.

## Reglas finales de dominio aprobadas

Estas decisiones, confirmadas por el cliente o aprobadas por el equipo por delegación, son vinculantes para toda spec, plan y tarea:

1. **Identificación única:** cada persona se identifica por `tipo_documento` (`CC`, `CE`, `TI`, `PAS`) + `numero_documento`, con `UNIQUE(tipo_documento, numero_documento)`. Un duplicado responde **409 `DOCUMENTO_DUPLICADO`**. El número se guarda como texto sin espacios ni puntos: CC, CE y TI solo dígitos (5 a 12); PAS alfanumérico en mayúsculas (5 a 15).
2. **Correo:** obligatorio y con formato válido, pero **no único**; es solo dato de contacto y no identifica ni sirve para iniciar sesión. El inicio de sesión es documento + contraseña.
3. **Cuentas:** el registro público solo crea participantes (estudiantes o docentes). Organizadores y coordinación se crean con `scripts/crear_usuario.py` (que pide documento) y el seed.
4. **Frontend:** Jinja2 solo como esqueleto (layout y navegación) con autoescape activo. Todos los datos llegan con `fetch` a `/api/v1` desde módulos JS (`api.js` común y un módulo por página) usando `textContent` / DOM seguro (prohibido `innerHTML` con datos de usuario o API). Sin bundler ni SPA; la evidencia se documenta en PF-12 con capturas de la pestaña Red.
5. **Fechas y zona horaria:** interfaz en español, zona `America/Bogota` (UTC-5, sin horario de verano). Almacenamiento en **UTC** garantizado en el ORM; la API rechaza entradas sin zona (422) y recibe/devuelve ISO-8601 con zona (`-05:00`); la presentación convierte explícitamente a `America/Bogota` (`Intl` con `timeZone: 'America/Bogota'`); las reglas de fechas se comparan siempre en UTC.
6. **Sin lista de espera.**
7. **Sin flujo de aprobación de eventos:** el organizador publica directo si cumple las condiciones (datos completos, `fecha_fin > fecha_inicio`, `fecha_limite_inscripcion ≤ fecha_inicio`, inicio futuro y cupo ≥ 1).
8. **Estados del evento:** guardados `borrador`, `publicado`, `cancelado`; `finalizado` e «inscripciones cerradas» se calculan.
9. **Inscripción:** se acepta con participante autenticado, evento publicado, antes de `fecha_limite_inscripcion`, cupo disponible, sin inscripción activa y cumpliendo el público objetivo. Duplicado → 409 `INSCRIPCION_DUPLICADA`. Cancelación hasta el inicio del evento; la reinscripción crea un registro nuevo y conserva el historial.
10. **Asistencia:** la registra el organizador del evento, desde `fecha_inicio` hasta **48 horas** después de `fecha_fin`; estados `presente` y `ausente` (sin registro = pendiente); las correcciones dentro de la ventana guardan quién y cuándo; solo para inscripciones activas.
11. **Privacidad y exportación:** el organizador ve el documento completo de los inscritos de su evento; coordinación lo ve enmascarado (`••••1234`); el documento no se escribe en logs ni en errores (ni en el registro por solicitud). Si se exporta CSV (opcional), el documento va enmascarado y se neutralizan celdas que inicien con `=`, `+`, `-` o `@`.
12. **Cupo:** puede subir siempre; solo baja hasta el número de inscritos activos; no se edita en eventos cancelados ni finalizados.
13. **HTTPS en todos los entornos:** la aplicación se sirve siempre por HTTPS (local, Docker, CI y entrega). En local se usan certificados de `mkcert` en `certs/` (ignorada por Git; nunca se commitean `*.pem`, `*.key` ni `*.crt`); en el CI, un certificado autofirmado con `openssl`. No se agregan por ahora redirección HTTP→HTTPS, HSTS ni cookie con prefijo `__Host-`.

## Pila tecnológica y seguridad
Python 3.11+ · FastAPI · SQLite (SQLAlchemy 2.x + Alembic) · Jinja2 · `tzdata` · pytest · ruff · GitHub Actions · Docker (complemento). Contraseñas con hash **argon2id** (mínimo 8 caracteres); en `POST /auth/login` verificación en tiempo constante (hash ficticio cuando el documento no existe) y **límite de 10 intentos fallidos** (HTTP 429 `DEMASIADOS_INTENTOS`). JWT firmado con `HS256` conteniendo únicamente `sub = usuario.id` (nunca documento ni correo), entregado en cookie `HttpOnly` + `SameSite=Lax` + `Path=/` + `Max-Age=3600` + `Secure` siempre activa (`COOKIE_SECURE=true` obligatorio; la app falla al arrancar si no lo está), sin recuperación de contraseña. La aplicación se sirve solo por HTTPS en todos los entornos. Las operaciones que modifican datos usan POST/PUT/PATCH y validan cabecera `Origin`/`Referer` del mismo origen cuando la sesión usa cookie (defensa CSRF).

## Flujo de desarrollo y puertas de calidad
Puertas G1 (spec aprobada por el humano), G2 (plan y tareas aprobados y `analyze` sin críticos; PR en borrador), G3 (cada tarea cumple su criterio), G4 (CI verde) y G5 (aprobación del compañero). Las pruebas de cupo, duplicados, permisos y seguridad se escriben primero (rojo → verde). Las 12 pruebas funcionales PF-01…PF-12 siguen siendo obligatorias y se documentan con evidencia.

## Gobernanza
Esta constitución prevalece sobre cualquier otra práctica del proyecto. Las enmiendas requieren justificación documentada, acuerdo de ambos integrantes y actualización de las specs afectadas. El cumplimiento se verifica en cada revisión de PR y en la sección de verificación de cada `plan.md`. Los documentos base viven en `docs/`.

**Versión**: 2.0.2 | **Ratificada**: 2026-11-13 | **Última enmienda**: 2026-11-14
