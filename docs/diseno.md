# Diseño técnico y contrato compartido (PF-04)

> **Estado:** Documento completo (**E1** contrato compartido + **E9-A** arquitectura, modelo de datos, especificación de API, justificación tecnológica y prototipos).

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

---

## 3. Diagrama de Componentes y Flujo de Solicitud

```mermaid
flowchart LR
    subgraph Cliente["Navegador Web (HTTPS)"]
        UI["Plantillas Jinja2 (esqueleto HTML)"]
        JS["Módulos JS ES6 (api.js + por página)"]
    end

    subgraph FastAPI["Backend FastAPI (uvicorn TLS)"]
        WEB["app/web/* (rutas HTML + require_web_roles)"]
        API["app/api/v1/* (routers REST + Pydantic v2)"]
        DEPS["app/api/deps.py (JWT HttpOnly + CSRF Origin/Referer)"]
        SVC["app/services/* (reglas de negocio RN-01..RN-21)"]
        REPO["app/repositories/* (consultas SQLAlchemy + BEGIN IMMEDIATE)"]
    end

    DB[("SQLite WAL\nFK=ON · busy_timeout=5000")]

    UI -->|"Carga inicial SSR mínima"| WEB
    JS -->|"fetch /api/v1/* (JSON + cookie)"| API
    WEB --> DEPS
    API --> DEPS
    API --> SVC
    SVC --> REPO
    REPO --> DB
```

---

## 4. Modelo de Datos y Reglas de Integridad (SQLite + Alembic)

El esquema relacional se gestiona con migraciones versionadas en `migrations/` y modelos ORM en `app/models/`. Cada conexión habilita `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` y `PRAGMA journal_mode=WAL`. Todas las fechas se almacenan normalizadas en **UTC** mediante `UTCDateTime`.

```mermaid
erDiagram
    USUARIOS ||--o{ EVENTOS : "organiza (organizador_id)"
    USUARIOS ||--o{ INSCRIPCIONES : "se inscribe (participante_id)"
    EVENTOS ||--o{ INSCRIPCIONES : "recibe (evento_id)"
    INSCRIPCIONES ||--o| ASISTENCIAS : "registra (inscripcion_id)"
    USUARIOS ||--o{ ASISTENCIAS : "audita (registrado_por_id)"

    USUARIOS {
        int id PK
        string tipo_documento
        string numero_documento
        string nombre
        string correo
        string tipo_participante
        string hash_password
        string rol
        bool activo
        datetime creado_en
    }

    EVENTOS {
        int id PK
        string titulo
        text descripcion
        string tipo
        datetime fecha_inicio
        datetime fecha_fin
        datetime fecha_limite_inscripcion
        string lugar
        string modalidad
        string publico_objetivo
        string ponente
        text requisitos
        string responsable_nombre
        string responsable_correo
        int cupo_maximo
        string estado
        text motivo_cancelacion
        int organizador_id FK
        datetime creado_en
        datetime actualizado_en
    }

    INSCRIPCIONES {
        int id PK
        int evento_id FK
        int participante_id FK
        string estado
        datetime creado_en
        datetime cancelada_en
    }

    ASISTENCIAS {
        int id PK
        int inscripcion_id FK
        string estado
        int registrado_por_id FK
        datetime registrado_en
        datetime actualizado_en
    }
```

### Restricciones e índices críticos en base de datos

| Tabla | Restricciones e índices verificados en ORM (`app/models/`) |
|---|---|
| `usuarios` | PK `id`; `UNIQUE(tipo_documento, numero_documento)` (`uq_usuarios_documento`); `CHECK` de longitud de documento (5..15), `tipo_documento` (`CC`, `CE`, `TI`, `PAS`), `rol` (`participante`, `organizador`, `coordinacion`) y `tipo_participante` (`estudiante`, `docente` o `NULL`). |
| `eventos` | PK `id`; FK `organizador_id → usuarios.id` (`RESTRICT`); `CHECK` `cupo_maximo >= 1`, `fecha_fin > fecha_inicio`, `fecha_limite_inscripcion <= fecha_inicio`, `estado` (`borrador`, `publicado`, `cancelado`), `tipo`, `modalidad` y `publico_objetivo`; índices `ix_eventos_estado_inicio` y `ix_eventos_organizador`. |
| `inscripciones` | PK `id`; FKs `evento_id → eventos.id` y `participante_id → usuarios.id` (`RESTRICT`); `CHECK` `estado IN ('activa', 'cancelada')`; **índice único parcial** `ux_inscripciones_activa` sobre `(evento_id, participante_id)` `WHERE estado = 'activa'` (permite reinscripción tras cancelar pero impide dos inscripciones activas simultáneas). |
| `asistencias` | PK `id`; FK `inscripcion_id → inscripciones.id` (`RESTRICT`) con `UNIQUE(inscripcion_id)` (`uq_asistencias_inscripcion`); FK `registrado_por_id → usuarios.id` (`RESTRICT`); `CHECK` `estado IN ('presente', 'ausente')`. |

**Control atómico de cupos (`RNF-04`):** la inscripción abre transacción inmediata con `BEGIN IMMEDIATE` en SQLite y ejecuta una inserción condicional `INSERT INTO inscripciones ... SELECT ... WHERE (SELECT COUNT(*) FROM inscripciones WHERE evento_id = :id AND estado = 'activa') < :cupo_maximo`, verificando `rowcount == 1`. Si otro hilo consume el último cupo antes de confirmar, devuelve `409 CUPO_AGOTADO` sin dejar registros parciales.

---

## 5. Especificación de API REST (`/api/v1`) y Vistas Web

El contrato formal generado desde la aplicación se encuentra versionado en [specs/contrato/openapi.json](../specs/contrato/openapi.json) y disponible interactivamente en `https://localhost:8000/docs`.

### 5.1 Endpoints REST principales

| Módulo | Método y ruta | Rol / Seguridad | Respuestas principales |
|---|---|---|---|
| **Salud** | `GET /health` | Público | `200` estado del servicio y BD |
| **Auth** | `POST /api/v1/auth/registro`, `POST /api/v1/auth/login` | Público (rate limit 10 fallos → `429`) | `201`/`200`, `401`, `409`, `422`, `429` |
| **Auth** | `POST /api/v1/auth/logout`, `GET /api/v1/auth/yo` | Autenticado + CSRF (`POST`) | `200`/`204`, `401`, `403` |
| **Eventos** | `GET /api/v1/organizador/eventos`, `POST /api/v1/eventos`, `GET\|PUT\|PATCH /api/v1/eventos/{evento_id}`, `POST /api/v1/eventos/{evento_id}/publicar`, `POST /api/v1/eventos/{evento_id}/cancelar` | `organizador` propietario + CSRF en mutaciones | `200`/`201`, `401`, `403`, `404`, `409`, `422` |
| **Catálogo** | `GET /api/v1/catalogo/eventos`, `GET /api/v1/catalogo/eventos/{evento_id}` | Público (solo publicados) | `200`, `404` (`EVENTO_NO_ENCONTRADO`), `422` |
| **Inscripciones** | `POST /api/v1/eventos/{evento_id}/inscripciones`, `GET /api/v1/inscripciones/mias`, `PATCH /api/v1/inscripciones/{inscripcion_id}/cancelar` | `participante` propietario + CSRF en mutaciones | `201`/`200`, `401`, `403`, `404`, `409` (`CUPO_AGOTADO`, `INSCRIPCION_DUPLICADA`, etc.) |
| **Inscripciones** | `GET /api/v1/eventos/{evento_id}/inscripciones` | `organizador` dueño o `coordinacion` (enmascarado) | `200`, `401`, `403`, `404` |
| **Asistencia** | `PUT /api/v1/eventos/{evento_id}/inscripciones/{inscripcion_id}/asistencia` | `organizador` dueño en ventana `[inicio, fin+48h]` + CSRF | `200`, `401`, `403`, `404`, `409` (`ASISTENCIA_NO_PERMITIDA`) |
| **Asistencia** | `GET /api/v1/eventos/{evento_id}/asistencia` | `organizador` dueño o `coordinacion` (enmascarado) | `200`, `401`, `403`, `404` |
| **Reportes** | `GET /api/v1/reportes/consolidado`, `GET /api/v1/reportes/consolidado/csv` | `coordinacion` solo lectura | `200` (JSON / `text/csv` sanitizado), `401`, `403`, `422` |

### 5.2 Vistas Web (`app/web/`)

- **Públicas:** `/` (catálogo), `/eventos/{evento_id}` (detalle y `404` amigable), `/login`, `/registro`.
- **Participante:** `/mis-inscripciones`.
- **Organizador:** `/organizador/eventos`, `/organizador/eventos/nuevo`, `/organizador/eventos/{evento_id}/editar`.
- **Organizador / Coordinación:** `/eventos/{evento_id}/asistencia`.
- **Coordinación:** `/coordinacion/consolidado`.

---

## 6. Enlaces a Especificaciones SDD (Spec Kit)

- Constitución del proyecto: [.specify/memory/constitution.md](../.specify/memory/constitution.md)
- Índice y puertas G1–G5: [specs/README.md](../specs/README.md)
- **E1 — Fundación:** [specs/001-fundacion/](../specs/001-fundacion/spec.md)
- **E2 — Autenticación y roles:** [specs/002-autenticacion-roles/](../specs/002-autenticacion-roles/spec.md)
- **E3 — Gestión de eventos:** [specs/003-gestion-eventos/](../specs/003-gestion-eventos/spec.md)
- **E4 — Catálogo y consulta:** [specs/004-catalogo-eventos/](../specs/004-catalogo-eventos/spec.md)
- **E5 — Inscripciones y cupos:** [specs/005-inscripciones-cupos/](../specs/005-inscripciones-cupos/spec.md)
- **E6 — Asistencia:** [specs/006-asistencia/](../specs/006-asistencia/spec.md)
- **E7 — Consolidado:** [specs/007-consolidado/](../specs/007-consolidado/spec.md)
- **E10 — DevOps, CI y Docker:** [specs/010-devops-ci-docker/](../specs/010-devops-ci-docker/spec.md)

---

## 7. Justificación de Tecnologías y Elección de Frontend

| Componente | Tecnología elegida | Justificación técnica y de alcance |
|---|---|---|
| **Lenguaje y Web API** | Python 3.12 + FastAPI | Tipado estático nativo, inyección de dependencias limpia para autenticación/autorización (`deps.py`), generación automática del contrato OpenAPI (`/docs`) y alto rendimiento. |
| **Validación** | Pydantic v2 | Validación declarativa estricta (`extra="forbid"`, validación de formatos de documento y zonas horarias `FechaConZona`) con serialización uniforme de errores. |
| **Persistencia y migraciones** | SQLite + SQLAlchemy 2.x + Alembic | Aprobada por el cliente para escala académica; garantiza integridad estricta con `PRAGMA foreign_keys=ON`, `WAL`, `CHECK`, índice único parcial y control atómico de cupos (`BEGIN IMMEDIATE`) sin requerir servidor de BD externo. |
| **Seguridad** | `argon2-cffi`, PyJWT (`HS256`), TLS obligatorio | Hashing resistente a fuerza bruta (`argon2id`), cookies `HttpOnly` + `SameSite=Lax` + `Secure` siempre activas sobre HTTPS y validación `Origin`/`Referer` contra CSRF. |
| **Calidad y pruebas** | `pytest`, `ruff`, GitHub Actions, Docker | Verificación continua de reglas críticas (cupo concurrente en 20 hilos, permisos, fechas UTC) y entorno reproducible con y sin contenedores. |

### 7.1 Justificación de Jinja2 como esqueleto + JavaScript modular (`fetch` a `/api/v1`)

En la entrevista inicial (pregunta 14), el cliente permitió usar **Jinja2** siempre que se justificara técnicamente por qué se elige frente a un framework SPA tradicional (como React o Vue) y se demostrara el consumo real de la API REST mediante JavaScript:

1. **Separación real entre interfaz y API REST:** Las plantillas Jinja2 (`app/templates/`) actúan exclusivamente como esqueleto HTML con herencia de layout (`base.html`) y autoescape activo, **sin renderizar datos de negocio directamente desde el servidor ni acoplar SQL a las vistas**. Toda la carga, filtrado, creación, edición, inscripción, asistencia y consolidado se ejecuta desde el navegador hacia `/api/v1/*` usando `fetch()` en los módulos `app/static/js/*.js` (verificado en DevTools en [PF-03](../evidencias/PF-03/pf-03-1_catalogo-filtros-red.png) y [PF-12](pruebas/PF-12.md)).
2. **Simplicidad operativa y cero paso de compilación:** Al no introducir Node.js, bundlers (`Vite`/`Webpack`) ni estado duplicado de cliente, ambos integrantes pueden levantar, probar y depurar la aplicación íntegra con un único proceso Python + HTTPS en Windows, macOS, Linux o Docker.
3. **Seguridad XSS por diseño:** El cliente común [app/static/js/api.js](../app/static/js/api.js) centraliza el manejo uniforme de errores, las redirecciones ante `401`, el formateo de fechas en `America/Bogota` mediante `Intl.DateTimeFormat` y la construcción segura del DOM con `crearNodo` y `textContent` (prohibido `innerHTML` con datos de API o usuario).

---

## 8. Prototipos e Interfaces Implementadas

Cada flujo cuenta con su plantilla HTML esqueleto y módulo JavaScript ES6 dedicado:

| Vista web | Plantilla Jinja2 | Módulo JS (`fetch`) | Funcionalidad principal |
|---|---|---|---|
| `/` | `app/templates/index.html` | `app/static/js/catalogo.js` | Catálogo público paginado y filtros |
| `/eventos/{evento_id}` | `app/templates/catalogo/detalle.html` | `app/static/js/catalogo.js`, `inscripciones.js` | Detalle, disponibilidad real e inscripción |
| `/login`, `/registro` | `app/templates/auth/login.html`, `registro.html` | `app/static/js/auth.js` | Autenticación y registro de participantes |
| `/organizador/eventos`, `/nuevo`, `/{id}/editar` | `app/templates/eventos/mis_eventos.html`, `formulario.html` | `app/static/js/eventos.js` | Gestión, publicación y cancelación de eventos |
| `/mis-inscripciones` | `app/templates/inscripciones/mias.html` | `app/static/js/inscripciones.js` | Historial y cancelación de inscripciones |
| `/eventos/{id}/asistencia` | `app/templates/asistencia/registro.html` | `app/static/js/asistencia.js` | Nómina, registro/corrección y privacidad |
| `/coordinacion/consolidado` | `app/templates/reportes/consolidado.html` | `app/static/js/reportes.js` | Consolidado global, filtros y exportación CSV |

### Capturas de las pantallas en ejecución

- **Catálogo público con filtros y llamada `fetch` en DevTools (`/`):**
  ![Catálogo público y pestaña Red](../evidencias/PF-03/pf-03-1_catalogo-filtros-red.png)
- **Detalle público de actividad con cupos en tiempo real (`/eventos/6`):**
  ![Detalle de evento](../evidencias/PF-03/pf-03-3_detalle-evento-cupos.png)
- **Panel de gestión del organizador y publicación directa (`/organizador/eventos`):**
  ![Creación y publicación de evento](../evidencias/PF-01/pf-01-1_creacion-evento-borrador.png)
- **Formulario de creación con validación de servidor visible (`/organizador/eventos/nuevo`):**
  ![Validación en formulario web](../evidencias/PF-02/pf-02-1_ui-rechazo-rango-fechas.png)
- **Vista de recurso inexistente amigable (`/eventos/999999`):**
  ![Vista 404 amigable](../evidencias/PF-04/pf-04-2_ui-404-actividad-no-disponible.png)


