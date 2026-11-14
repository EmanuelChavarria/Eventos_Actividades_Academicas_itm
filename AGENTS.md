# AGENTS.md — Reglas obligatorias del proyecto PF-04

**Proyecto:** Organización de eventos y actividades académicas · Python · FastAPI · SQLite · Jinja2 · SDD con Spec Kit.
**Fuente única de verdad** para cualquier agente (Claude, Gemini u otro). `CLAUDE.md` y `GEMINI.md` la importan y solo añaden instrucciones propias de cada herramienta. Si algo aquí contradice otro archivo, gana este y la constitución.

## Documentos de referencia (léelos antes de actuar)

| Documento | Para qué |
|---|---|
| `.specify/memory/constitution.md` | 12 principios y reglas finales de dominio (prevalece sobre todo) |
| `docs/01_analisis_y_especificaciones.md` | Requisitos RF/RNF/RN, épicas, modelo de datos, API, pruebas PF |
| `docs/02_agente_integrante_A.md`, `docs/03_agente_integrante_B.md` | Épicas y propiedad de archivos de cada integrante |
| `docs_base/` | Material original (solo lectura; no se edita) |

## 1. Reglas generales de conducta

1. **Ante cualquier duda, pregunta al humano** antes de continuar. No rellenes vacíos ni inventes respuestas del cliente; lo no confirmado se rotula `[SUPUESTO S-XX]` o `[PENDIENTE: ...]`.
2. Trabaja **solo en las épicas y archivos de tu integrante** (ver propiedad de archivos en `docs/`). Para cambiar archivos ajenos o el contrato compartido, pide al humano que lo coordine.
3. Responde y documenta **en español**. Código de dominio en español y `snake_case` (`evento`, `inscripcion`); términos técnicos en inglés (`service`, `repository`).
4. Al terminar cada tarea reporta: qué hiciste, hash del commit, qué probaste y qué sigue.

## 2. SDD estricto: sin spec aprobada no hay código

- Ciclo obligatorio por feature: `specify → clarify → plan → tasks → analyze → implement` (`constitution` ya está hecho; `checklist` es opcional). En Claude Code los skills se invocan con `/speckit-<paso>` y en Gemini CLI con `/speckit.<paso>`.
- **Puertas:** G1 el humano aprueba la spec · G2 el humano aprueba plan y tareas, `analyze` sin hallazgos críticos y PR en borrador · G3 cada tarea cumple su criterio · G4 CI verde · G5 aprobación del compañero.
- `clarify` es obligatorio antes de `plan`; `analyze` antes de `implement`. **Nunca ejecutes `implement` ni escribas código sin spec aprobada y sin `[PENDIENTE]` bloqueantes.**
- **La spec manda:** si el comportamiento cambia, primero se actualiza la spec (commit `docs(specs): ...`) y después el código, en commits separados.
- Cada spec enlaza sus RF/RN/CA y define errores esperados (HTTP + código de dominio) y verificación (PF-XX y pytest).

## 3. Git: ramas, commits y PR

- **Nunca se trabaja en `main`.** Una rama por feature con el esquema de Spec Kit **`NNN-slug`**, creada pasando `-Number N` explícito a `create-new-feature.ps1` (para evitar colisiones entre A y B). Épica ↔ feature: E1 `001-fundacion` · E2 `002-autenticacion-roles` · E3 `003-gestion-eventos` · E4 `004-catalogo-eventos` · E5 `005-inscripciones-cupos` · E6 `006-asistencia` · E7 `007-consolidado` · E10 `010-devops-ci-docker`. Otras ramas: `docs/E0-sdd-constitucion`, `test/E8a-...`, `docs/E9a-...`.
- **Conventional Commits en español:** `tipo(alcance): descripción` en presente, minúscula inicial, sin punto final, ≤ 72 caracteres. Tipos: `feat fix docs test refactor style chore perf ci build`. Pie opcional `Refs: RF-.., CA-..` y `Spec: specs/NNN-slug`.
- **Una tarea de `tasks.md` = un commit atómico**; marca la tarea hecha en el mismo commit. Cada commit deja la app ejecutable.
- Archivos explícitos en `git add` (nunca `git add .`). Prohibido: `--no-verify`, `push --force` (solo `--force-with-lease` en tu propia rama), mensajes como «cambios», «update», «wip», y commitear `.env`, `*.db`, `.venv/`, `__pycache__/`.
- **PR** hacia `main` revisado por el compañero, en borrador desde G2, con propósito, spec asociada, cambios, pruebas efectuadas y requisitos RF/RNF/CA. Fusión con **merge commit** (no squash).

## 4. Arquitectura, seguridad y reglas de negocio

- **Capas estrictas:** `api` (routers) → `services` → `repositories` → `models`. **La lógica de negocio vive solo en `services/`**; los routers validan, invocan servicios y traducen errores; solo los repositorios escriben SQL; los services no importan FastAPI.
- **Cupo atómico en SQLite:** `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000` por conexión; la inscripción inicia transacción con **`BEGIN IMMEDIATE`** + sentencia condicional (`INSERT ... SELECT ... WHERE activas < cupo_maximo` verificando `rowcount`) + índice único parcial de inscripción activa. El cupo disponible se **calcula**, nunca se almacena. Un rechazo no deja registros parciales.
- **Mínimo privilegio:** autorización por rol **y** por propietario en cada endpoint y página web (validando además `usuario.activo == True`). Organizador: solo sus eventos. Coordinación: solo lectura. Participante: solo lo propio.
- **Validar en servidor y en BD:** Pydantic v2 + PK/FK, `UNIQUE`, `CHECK`, índice único parcial y escape de comodines (`%`, `_`) en filtros `LIKE`. Schemas separados de entrada y salida (nunca exponer `hash_password`).
- **Errores uniformes** `{"error": {"codigo", "mensaje", "detalles"}}` con códigos 200/201/204/400/422/401/403/404/409/429, sin trazas ni datos sensibles. Manejadores globales obligatorios para `ErrorDominio`, `RequestValidationError` (omitiendo `input` para no filtrar contraseñas ni documentos) y `HTTPException`.
- **Códigos de error de dominio:** `DOCUMENTO_DUPLICADO` (409), `INSCRIPCION_DUPLICADA` (409), `CUPO_AGOTADO` (409), `INSCRIPCIONES_CERRADAS` (409), `PUBLICO_NO_PERMITIDO` (409), `CANCELACION_NO_PERMITIDA` (409), `ASISTENCIA_NO_PERMITIDA` (409), `EVENTO_NO_PUBLICADO` (409), `EVENTO_NO_ENCONTRADO` (404), `INSCRIPCION_NO_ENCONTRADA` (404), `SIN_PERMISO` (403), `CREDENCIALES_INVALIDAS` (401), `DEMASIADOS_INTENTOS` (429).
- **Contrato compartido** (modelos, errores, `deps.py`, `fechas.py`, enums, OpenAPI) solo cambia con acuerdo de ambos integrantes; `specs/contrato/openapi.json` se regenera con `python scripts/export_openapi.py`, nunca a mano.

### Reglas finales de dominio (no negociables sin acuerdo del cliente)

- **Identificación única:** `tipo_documento` (`CC`, `CE`, `TI`, `PAS`) + `numero_documento`, `UNIQUE` en BD; duplicado → **409 `DOCUMENTO_DUPLICADO`**. Texto sin espacios ni puntos: CC/CE/TI solo dígitos (5–12), PAS alfanumérico en mayúsculas (5–15).
- **Autenticación segura:** login con documento + contraseña (hash **argon2id**, mín. 8 caracteres; verificación en tiempo constante con hash ficticio si el documento no existe; **límite de 10 intentos fallidos** → 429 `DEMASIADOS_INTENTOS`). JWT `HS256` con `sub = usuario.id` (nunca documento ni correo), validando `SECRET_KEY` al arrancar (fallar si está vacía, es corta o igual al valor de `.env.example`). Cookie `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600`, `Secure` según `COOKIE_SECURE`. Verificación de `Origin`/`Referer` del mismo origen en mutaciones con cookie (CSRF).
- **Correo:** obligatorio, formato válido, **no único**, solo contacto.
- **Cuentas:** el registro público solo crea participantes; organizadores y coordinación con `scripts/crear_usuario.py` y seed.
- **Frontend seguro:** Jinja2 solo como esqueleto con autoescape activo; los datos llegan por `fetch` a `/api/v1` desde módulos JS (`api.js` común + uno por página). Usar siempre `textContent` / DOM seguro (prohibido `innerHTML` con datos de usuario o API). Sin bundler ni SPA.
- **Fechas:** almacenadas en **UTC** (garantizado en ORM; requiere `tzdata`); la API rechaza fechas sin zona (422) y recibe/devuelve ISO-8601 con zona (`-05:00`); presentación con `Intl` y `timeZone: 'America/Bogota'`; reglas de fechas comparadas en UTC.
- **Sin lista de espera. Sin flujo de aprobación de eventos** (publica directo el organizador si cumple las condiciones).
- **Estados guardados:** `borrador`, `publicado`, `cancelado`; `finalizado` e «inscripciones cerradas» se calculan.
- **Inscripción:** autenticado, evento publicado, antes de `fecha_limite_inscripcion`, cupo disponible, sin inscripción activa y cumple el público objetivo. Cancelación hasta el inicio del evento; reinscripción crea registro nuevo y conserva el historial.
- **Asistencia:** la registra el organizador del evento, desde `fecha_inicio` hasta **48 h** después de `fecha_fin`; `presente`/`ausente`; correcciones guardan quién y cuándo.
- **Privacidad y exportación:** el organizador ve el documento completo de los inscritos de su evento; coordinación lo ve enmascarado (`••••1234`); el documento nunca va en logs ni errores (tampoco en logs de acceso ni cuerpos de petición). Si se exporta CSV (opcional), el documento va enmascarado y se neutralizan celdas que inicien con `=`, `+`, `-` o `@`.

## 5. Verificación antes de cada PR (obligatoria)

```bash
ruff check . && ruff format --check .
pytest -q
python scripts/export_openapi.py --check   # obligatorio desde que E10 esté en main
```

- Además: la app arranca (con o sin Docker) y los endpoints de la épica funcionan en `/docs`. **El CI debe estar verde** (`calidad`, `pruebas`, `docker` tras E10); no se abre PR listo con CI en rojo ni se desactivan checks.
- Antes de cada commit: `ruff check . && ruff format .`.
- Pruebas de reglas críticas (cupo, duplicados, permisos, seguridad): escribe primero la prueba que falla y luego la implementación (con BD en archivo temporal cuando haya hilos). Las 12 pruebas funcionales PF-01…PF-12 se documentan con evidencia en `docs/pruebas/` y `evidencias/`.

## 6. Seguridad y datos

- Nunca subas `.env`, `*.db`, secretos ni datos reales; solo `.env.example` y datos **ficticios** (documentos del seed obviamente falsos).
- No leas ni imprimas `.env` ni `*.db`. No escribas contraseñas, tokens, cabeceras `Cookie`/`Authorization` ni documentos en logs.
- Cookies `HttpOnly` + `SameSite=Lax`; operaciones que modifican datos solo con POST/PUT/PATCH y validación `Origin`/`Referer`.

## 7. Estado de la configuración

Existen: constitución (v2.0.1), documentos en `docs/`, estos archivos de reglas, `.specify/templates/` personalizadas, las reglas por ruta (`.claude/rules/`), las skills (`.claude/skills/`) y `.claude/settings.json`. **Aún no existe** código de la app: se crea feature por feature con el ciclo SDD (§2).
