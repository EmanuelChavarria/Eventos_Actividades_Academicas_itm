# Plan de Implementación: Registro y Consulta de Asistencia

**Rama:** `006-asistencia` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](spec.md)
**Entrada:** Especificación en `specs/006-asistencia/spec.md`.

---

## 1. Resumen y decisiones técnicas

- **Capa Repositorio (`app/repositories/asistencia_repo.py`):**
  - Implementación de `registrar_o_actualizar(db, inscripcion_id, estado, usuario_id, ahora)`.
  - Operación UPSERT asegurada por restricción `UNIQUE (inscripcion_id)` en la tabla `asistencias`.
  - Si no existe registro, inserta con `registrado_por_id`, `registrado_en` y `actualizado_en` (UTC).
  - Si ya existe, actualiza `estado`, `registrado_por_id` y `actualizado_en` (UTC).
  - Consulta de participantes con su estado de asistencia asociado mediante `LEFT JOIN`.
- **Capa Servicio (`app/services/asistencia_service.py`):**
  - Validación de ventana temporal (RN-08) mediante `esta_en_ventana_asistencia` (`[fecha_inicio, fecha_fin + 48h]` en UTC). Si no se cumple, lanza `Conflicto(codigo=CodigosError.ASISTENCIA_NO_PERMITIDA)`.
  - Validación de estado: el evento debe estar `publicado` y la inscripción debe estar en estado `activa`.
  - Control de propiedad (RN-11): verifica que `evento.organizador_id == usuario_id`.
  - Enmascaramiento de datos personales en consultas según el rol del solicitante (`organizador` vs `coordinacion`).
- **Capa API (`app/api/v1/asistencia.py`):**
  - `PUT /eventos/{id}/inscripciones/{insc_id}/asistencia`: Registro y corrección idempotente de asistencia.
  - `GET /eventos/{id}/asistencia`: Consulta de nómina con asistencia para organizador y coordinación.
- **Capa Web Jinja2 y Módulo JS:**
  - `app/templates/asistencia/registro.html`: Vista de nómina con controles rápidos.
  - `app/static/js/asistencia.js`: Lógica cliente con llamadas asíncronas `PUT` seguras (DOM seguro, sin `innerHTML`).

---

## 2. Contexto técnico

- **Lenguaje:** Python 3.11+
- **Base de Datos:** SQLite con `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` y almacenamiento de fechas en UTC.
- **Dependencias:** FastAPI, SQLAlchemy 2.x, Pydantic v2, Jinja2.
- **Pruebas:** `pytest`, `pytest-asyncio`.

---

## 3. Verificación contra la constitución

- [x] **I. La spec manda:** Spec aprobada previa a código.
- [x] **II. Capas estrictas:** `api` → `services` → `repositories` → `models`. Lógica de ventana y permisos 100% en `services/`.
- [x] **III. Validación servidor y BD:** Pydantic v2 + índice único en `inscripcion_id`.
- [x] **V. Mínimo privilegio:** Autorización por organizador dueño y lectura para coordinación con documento enmascarado.
- [x] **VI. Errores uniformes:** Respuestas 401/403/404/409 con códigos de dominio (`ASISTENCIA_NO_PERMITIDA`, `SIN_PERMISO`).
- [x] **VIII. Commits atómicos:** Conventional Commits en español.

---

## 4. Estructura de archivos por capa (Propiedad del Integrante A)

```text
app/
├── api/v1/
│   └── asistencia.py
├── repositories/
│   └── asistencia_repo.py
├── schemas/
│   └── asistencia.py
├── services/
│   └── asistencia_service.py
├── static/js/
│   └── asistencia.js
├── templates/asistencia/
│   └── registro.html
tests/
└── test_asistencia.py
specs/006-asistencia/
├── spec.md
├── plan.md
└── tasks.md
```
