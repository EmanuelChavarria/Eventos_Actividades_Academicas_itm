# Plan de Implementación: Inscripciones y Control Atómico de Cupos

**Rama:** `005-inscripciones-cupos` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](spec.md)
**Entrada:** Especificación en `specs/005-inscripciones-cupos/spec.md`.

---

## 1. Resumen y decisiones técnicas

- **Capa Repositorio (`app/repositories/inscripcion_repo.py`):**
  - Implementación de método `inscribir_con_cupo_atomico(db, evento_id, usuario_id)`.
  - Ejecución con `BEGIN IMMEDIATE` para adquirir bloqueo de escritura exclusivo en SQLite.
  - Consulta condicional `INSERT INTO inscripciones ... SELECT ... WHERE activas < cupo_maximo`.
  - Captura de `sqlite3.IntegrityError` diferenciando violación de índice parcial (`uq_inscripcion_activa`) de violación de FK.
- **Capa Servicio (`app/services/inscripcion_service.py`):**
  - Orquestación de validaciones de precondición: existencia del evento, estado `publicado`, vigencia de `fecha_limite_inscripcion` (comparada en UTC), compatibilidad de `publico_objetivo`.
  - Invocación de repositorio y mapeo a errores de dominio tipados (`CupoAgotadoError`, `InscripcionDuplicadaError`, `InscripcionesCerradasError`, etc.).
  - Método `cancelar_inscripcion(db, inscripcion_id, usuario_id)` con validación de propiedad y verificación `ahora_utc < evento.fecha_inicio`.
  - Consulta de inscritos con enmascaramiento condicional de `numero_documento` según rol (`organizador` vs `coordinacion`).
- **Capa API (`app/api/v1/inscripciones.py`):**
  - `POST /eventos/{id}/inscripciones`: Registro de inscripción.
  - `PATCH /inscripciones/{id}/cancelar`: Cancelación de inscripción.
  - `GET /inscripciones/mias`: Lista de inscripciones del usuario en sesión.
  - `GET /eventos/{id}/inscripciones`: Lista de inscritos para organizador dueño o coordinación.
- **Capa Web / Interfaz Jinja2:**
  - `app/templates/inscripciones/mias.html`: Plantilla de "Mis inscripciones".
  - `app/static/js/inscripciones.js`: Módulo JS que consume la API con `fetch` seguro (`textContent`).

---

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.11+
- **Almacenamiento:** SQLite con `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000`, WAL y fechas UTC.
- **Dependencias:** FastAPI, SQLAlchemy 2.x, Pydantic v2, Jinja2.
- **Pruebas:** `pytest`, `pytest-asyncio`, concurrencia con `concurrent.futures`.

---

## 3. Verificación contra la constitución

- [x] **I. La spec manda:** Spec aprobada previa a la codificación.
- [x] **II. Capas estrictas:** `api` → `services` → `repositories` → `models`. Lógica de negocio 100% en `services/`.
- [x] **III. Validación servidor y BD:** Pydantic v2 + índice único parcial e inserción condicional.
- [x] **IV. Cupo nunca se excede:** `BEGIN IMMEDIATE` + inserción condicional. Cupo calculado, nunca persistido.
- [x] **V. Mínimo privilegio:** Validación por rol y propietario en endpoints y páginas web.
- [x] **VI. Errores uniformes:** `{"error": {"codigo", "mensaje", "detalles"}}` con códigos HTTP 401/403/404/409/422.
- [x] **VIII. Commits atómicos:** 1 tarea = 1 commit con Conventional Commits.

---

## 4. Estructura de archivos por capa (Propiedad del Integrante B)

```text
app/
├── api/v1/
│   └── inscripciones.py
├── repositories/
│   └── inscripcion_repo.py
├── schemas/
│   └── inscripcion.py
├── services/
│   └── inscripcion_service.py
├── static/js/
│   └── inscripciones.js
├── templates/inscripciones/
│   └── mias.html
tests/
└── test_inscripciones.py
specs/005-inscripciones-cupos/
├── spec.md
├── plan.md
└── tasks.md
```
