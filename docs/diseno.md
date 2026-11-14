# Diseño técnico y contrato compartido (PF-04)

> **Estado:** Documento inicial creado en **E1 — Fundación y plataforma** con el **Contrato compartido entre integrantes** para desbloquear E2–E7. En la épica E9-A se ampliará con diagramas y arquitectura completa.

## 1. Arquitectura en capas

El proyecto aplica separación estricta de responsabilidades (`RNF-01`):

```text
app/api/v1/ + app/web/   ──►   app/services/   ──►   app/repositories/   ──►   app/models/
  (HTTP / Pydantic)             (Reglas RN)             (Única capa SQL)        (ORM SQLite)
```

- **Routers (`app/api/v1/`):** validan entrada con Pydantic v2, invocan servicios y delegan excepciones al manejador global. No contienen reglas de negocio ni SQL.
- **Servicios (`app/services/`):** implementan todas las reglas `RN-01..RN-21`. **No importan `fastapi`**.
- **Repositorios (`app/repositories/`):** encapsulan consultas SQLAlchemy.

---

## 2. Contrato compartido entre integrantes (congelado desde E1)

Ninguno de estos módulos ni firmas se modifica sin acuerdo previo de ambos integrantes (`AGENTS.md` §4 y principio XI de la constitución).

### 2.1 Base de datos y sesión (`app/core/database.py`)
- `Base`: clase base declarativa de SQLAlchemy.
- `engine`, `SessionLocal`: motor SQLite configurado con `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` y `PRAGMA journal_mode=WAL` en cada conexión.
- `get_db() -> Generator[Session, None, None]`: dependencia FastAPI de sesión por solicitud.

### 2.2 Fechas y ventana de asistencia (`app/core/fechas.py`)
- `ZONA_BOGOTA = ZoneInfo("America/Bogota")` · `VENTANA_ASISTENCIA_HORAS = 48`.
- `ahora_utc() -> datetime`: proveedor inyectable de hora actual en UTC para pruebas.
- `asegurar_utc(valor: datetime) -> datetime`: exige zona horaria explícita (`ValueError` → HTTP 422 si es *naive*) y normaliza a UTC.
- `FechaConZona`: tipo anotado Pydantic (`Annotated[datetime, AfterValidator(asegurar_utc)]`).
- `a_bogota(valor: datetime) -> datetime`: convierte a `America/Bogota`.
- `esta_en_ventana_asistencia(fecha_inicio, fecha_fin, *, ahora=None) -> bool`: evalúa `[fecha_inicio, fecha_fin + 48h]` en UTC.
- `UTCDateTime(TypeDecorator)`: persiste fechas en formato ISO UTC fijo (`%Y-%m-%dT%H:%M:%S.%fZ`) para que las restricciones `CHECK` en SQLite comparen de forma fiable.

### 2.3 Enumeraciones (`app/models/enums.py`)
- `Rol`: `participante`, `organizador`, `coordinacion`
- `TipoDocumento`: `CC`, `CE`, `TI`, `PAS`
- `TipoParticipante`: `estudiante`, `docente`
- `TipoEvento`: `conferencia`, `taller`, `seminario`, `capacitacion`
- `Modalidad`: `presencial`, `virtual`, `hibrida`
- `PublicoObjetivo`: `todos`, `estudiantes`, `docentes`
- `EstadoEvento`: `borrador`, `publicado`, `cancelado`
- `EstadoInscripcion`: `activa`, `cancelada`
- `EstadoAsistencia`: `presente`, `ausente`

### 2.4 Errores de dominio (`app/core/errors.py`)
Formato JSON uniforme garantizado por `registrar_manejadores_errores(app)`:

```json
{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}
```

- Jerarquía: `ErrorDominio(codigo, mensaje, status_code=400, detalles=None)` con subclases `NoEncontrado` (404), `NoAutorizado` (403), `NoAutenticado` (401), `Conflicto` (409), `ReglaNegocio` (422) y `DemasiadosIntentos` (429).
- `RequestValidationError` devuelve 422 `ERROR_VALIDACION` **omitiendo el campo `input`** para evitar filtrar contraseñas o documentos.
- Códigos oficiales (`CodigosError`):
  - `409`: `DOCUMENTO_DUPLICADO`, `INSCRIPCION_DUPLICADA`, `CUPO_AGOTADO`, `INSCRIPCIONES_CERRADAS`, `PUBLICO_NO_PERMITIDO`, `CANCELACION_NO_PERMITIDA`, `ASISTENCIA_NO_PERMITIDA`, `EVENTO_NO_PUBLICADO`
  - `404`: `EVENTO_NO_ENCONTRADO`, `INSCRIPCION_NO_ENCONTRADA`
  - `403`: `SIN_PERMISO`
  - `401`: `CREDENCIALES_INVALIDAS`
  - `429`: `DEMASIADOS_INTENTOS`

### 2.5 Dependencias de autenticación (`app/api/deps.py`)
- `get_current_user_optional(request, db) -> Usuario | None`: decodifica la cookie JWT `pf04_session` verificando firma, expiración y `usuario.activo`.
- `get_current_user(usuario) -> Usuario`: exige usuario autenticado y activo (`401 CREDENCIALES_INVALIDAS`).
- `require_roles(*roles: Rol) -> Callable[[Usuario], Usuario]`: exige rol autorizado (`403 SIN_PERMISO`).
- `require_web_user` / `require_web_roles(*roles: Rol)`: equivalentes para vistas web; sin sesión redirigen `303` a `/login`, y con rol insuficiente responden `403 SIN_PERMISO`.
- `verificar_csrf(request)`: registrada globalmente en `api_router`; exige `Origin` válido (o `Referer` como respaldo) frente a `ALLOWED_ORIGINS` y origen efectivo en toda mutación (`POST`/`PUT`/`PATCH`/`DELETE`) que envíe cookie de sesión (`403 SIN_PERMISO` si falta o no coincide; en `pytest` enviar `Origin: https://testserver`).

### 2.6 Conteo compartido de inscripciones (`app/repositories/inscripcion_repo.py`)
- `contar_activas(db: Session, evento_id: int) -> int`
- `contar_activas_por_eventos(db: Session, ids: Sequence[int]) -> dict[int, int]`

### 2.7 Cliente frontend común (`app/static/js/api.js`)
- `requestApi(ruta, opciones)`: envuelve `fetch('/api/v1' + ruta, { credentials: 'same-origin' })`, interpreta `{"error": ...}` y redirige a `/login` ante 401.
- `formatearFechaBogota(isoFecha)` y `aIsoBogota(valorLocal)`: presentación y envío explícito en `America/Bogota` (`-05:00`).
- `mostrarAlerta`, `ocultarAlerta`, `crearNodo`: manipulación DOM segura usando exclusivamente `textContent`.
