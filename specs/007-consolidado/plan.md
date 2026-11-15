# Plan de Implementación: Consolidado para Coordinación Académica

**Rama:** `007-consolidado` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](spec.md)
**Entrada:** Especificación en `specs/007-consolidado/spec.md`.

---

## 1. Resumen y decisiones técnicas

- **Capa Repositorio (`app/repositories/reporte_repo.py`):**
  - Implementación de `obtener_consolidado_eventos(db, filtros)`.
  - Sentencia SQL agregada utilizando `func.count()`, `func.sum()` y expresiones condicionales `case()`:
    - `inscritos_activos`: conteo con condición `inscripciones.estado == 'activa'`.
    - `cancelaciones`: conteo con condición `inscripciones.estado == 'cancelada'`.
    - `presentes`: conteo donde `asistencias.estado == 'presente'`.
    - `ausentes`: conteo donde `asistencias.estado == 'ausente'`.
  - Agrupación por `Evento.id`.
- **Capa Servicio (`app/services/reporte_service.py`):**
  - Validación de rol del usuario solicitante (`coordinacion`).
  - Cálculo en memoria de tasas porcentuales y protección contra división por cero:
    - `ocupacion_pct = round((activos / cupo_maximo) * 100, 2)`
    - `asistencia_pct = round((presentes / activos) * 100, 2) if activos > 0 else 0.0`
  - Generación de fila resumen `totales`.
  - Módulo de generación CSV con sanitización anti-fórmulas.
- **Capa API (`app/api/v1/reportes.py`):**
  - `GET /reportes/consolidado`: Retorna métricas en JSON con soporte de filtros query.
  - `GET /reportes/consolidado/csv`: Genera stream de descarga CSV con cabeceras `Content-Disposition`.
- **Capa Web Jinja2 y Módulo JS:**
  - `app/templates/reportes/consolidado.html`: Vista del panel analítico.
  - `app/static/js/reportes.js`: Interfaz interactiva de filtros y renderizado seguro de tablas.

---

## 2. Contexto técnico

- **Lenguaje:** Python 3.11+
- **Base de Datos:** SQLite con SQLAlchemy 2.x
- **Dependencias:** FastAPI, Pydantic v2, Jinja2
- **Pruebas:** `pytest`, `pytest-asyncio`

---

## 3. Verificación contra la constitución

- [x] **I. La spec manda:** Spec aprobada previa a código.
- [x] **II. Capas estrictas:** Repositorios ejecutan consultas; servicios calculan métricas y totales.
- [x] **V. Mínimo privilegio:** Restringido exclusivamente al rol `coordinacion` (403 para otros).
- [x] **VI. Errores uniformes:** Respuestas estandarizadas.
- [x] **VII. Privacidad:** Enmascaramiento y neutralización CSV.
- [x] **VIII. Commits atómicos:** Conventional Commits en español.

---

## 4. Estructura de archivos por capa (Propiedad del Integrante A)

```text
app/
├── api/v1/
│   └── reportes.py
├── repositories/
│   └── reporte_repo.py
├── schemas/
│   └── reporte.py
├── services/
│   └── reporte_service.py
├── static/js/
│   └── reportes.js
├── templates/reportes/
│   └── consolidado.html
tests/
└── test_reportes.py
specs/007-consolidado/
├── spec.md
├── plan.md
└── tasks.md
```
