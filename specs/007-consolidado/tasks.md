# Tareas: Consolidado para Coordinación Académica

- **Rama:** `007-consolidado` · **Responsable:** Integrante A
- **Entradas:** `specs/007-consolidado/spec.md`, `specs/007-consolidado/plan.md`
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** Para la coherencia de totales y la protección contra división por cero, las pruebas se redactan rojo → verde.

---

## Tareas de Implementación

### Fase 1: Capa de Datos y Schemas (US1, US3)
- [x] **T-007-01** [US1, US3] Schemas Pydantic para métricas por evento y totales globales en `app/schemas/reporte.py` · Commit: `feat(reportes): agrega schemas de consolidado y totales` · Terminado cuando: los schemas definen métricas, porcentajes y totales.
- [x] **T-007-02** [US1, US2] Consulta agregada optimizada con `GROUP BY` y `case()` en `app/repositories/reporte_repo.py` · Commit: `feat(reportes): implementa consulta agregada de eventos` · Terminado cuando: consolida eventos, inscritos activos, cancelaciones y asistencia en una sola consulta.

### Fase 2: Lógica de Negocio y Métricas Analíticas (US1, US2, US3, US4)
- [x] **T-007-03** [US1, US3] Servicio con cálculo de porcentajes, protección de división por cero y totales en `app/services/reporte_service.py` · Commit: `feat(reportes): calcula porcentaje de asistencia y totales globales` · Terminado cuando: calcula ocupación %, asistencia % y objeto `totales`.
- [x] **T-007-04** [US4] Generación de archivo CSV sanitizado contra inyecciones de fórmulas en `app/services/reporte_service.py` · Commit: `feat(reportes): agrega exportacion del consolidado a csv` · Terminado cuando: neutraliza caracteres `=`, `+`, `-`, `@` y enmascara identificaciones.

### Fase 3: Endpoints API REST (US1, US2, US3, US4)
- [x] **T-007-05** [US1, US2, US3] Endpoint `GET /api/v1/reportes/consolidado` exclusivo para coordinación en `app/api/v1/reportes.py` · Commit: `feat(reportes): expone get consolidado para coordinacion` · Terminado cuando: responde 200 con el consolidado a coordinación y 403 a otros roles.

### Fase 4: Vistas Web Jinja2 y Módulos JS (US1, US2, US3, US4)
- [ ] **T-007-06** [US1, US2, US3] Vista web del panel consolidado con filtros y totales en `app/templates/reportes/consolidado.html` y `app/static/js/reportes.js` · Commit: `feat(web): agrega panel consolidado para coordinacion` · Terminado cuando: renderiza la tabla analítica con filtros dinámicos y totales.

### Fase 5: Pruebas Automatizadas y Evidencias Funcionales (US1, US2, US3)
- [ ] **T-007-07** [US1, US3] Pruebas unitarias y de integración en `tests/test_reportes.py` · Commit: `test(reportes): agrega pruebas de acceso y coherencia de totales` · Terminado cuando: valida permiso 403, coherencia de sumas y cero inscritos.
- [ ] **T-007-08** [US1..US3] Documentación de la prueba funcional PF-11 en `docs/pruebas/PF-11.md` con evidencias · Commit: `docs(pruebas): documenta pf-11 con verificacion de totales` · Terminado cuando: se documentan pasos y evidencias de PF-11.
