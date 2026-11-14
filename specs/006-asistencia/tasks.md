# Tareas: Registro y Consulta de Asistencia

- **Rama:** `006-asistencia` · **Responsable:** Integrante B
- **Entradas:** `specs/006-asistencia/spec.md`, `specs/006-asistencia/plan.md`
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** Para la ventana de 48 h y permisos de organizador, las pruebas pytest se redactan rojo → verde.

---

## Tareas de Implementación

### Fase 1: Capa de Datos y Schemas (US1, US2)
- [ ] **T-006-01** [US1, US2] Schemas Pydantic para registro y consulta de asistencia en `app/schemas/asistencia.py` · Commit: `feat(asistencia): agrega schemas de asistencia` · Terminado cuando: los schemas validan estados `presente`/`ausente` y formatean fechas con zona horaria.
- [ ] **T-006-02** [US1, US2] Repositorio de asistencia con UPSERT idempotente en `app/repositories/asistencia_repo.py` · Commit: `feat(asistencia): agrega repositorio con upsert por inscripcion` · Terminado cuando: registra o actualiza la asistencia de una inscripción sin duplicar filas.

### Fase 2: Lógica de Negocio y Reglas Críticas (US1, US2, US3)
- [ ] **T-006-03** [US1, US2, US3] Servicio de asistencia con validación de ventana temporal (RN-08) y propiedad (RN-11) en `app/services/asistencia_service.py` · Commit: `feat(asistencia): implementa reglas de registro y correccion` · Terminado cuando: rechaza operaciones fuera de la ventana de 48 h tras fin y restringe mutaciones al organizador.

### Fase 3: Endpoints API REST (US1, US2, US3)
- [ ] **T-006-04** [US1, US2] Endpoint `PUT /api/v1/eventos/{id}/inscripciones/{insc_id}/asistencia` · Commit: `feat(asistencia): expone endpoint para registrar y corregir asistencia` · Terminado cuando: permite registrar o corregir el estado de asistencia respondiendo 200 o 409 tipado.
- [ ] **T-006-05** [US3] Endpoint `GET /api/v1/eventos/{id}/asistencia` con enmascaramiento diferencial · Commit: `feat(asistencia): expone lista de participantes con asistencia` · Terminado cuando: muestra documento completo a organizador y enmascarado (`••••1234`) a coordinación.

### Fase 4: Vistas Web Jinja2 y Módulos JS (US4)
- [ ] **T-006-06** [US4] Pantalla y controles interactivos de asistencia en `app/templates/asistencia/registro.html` y `app/static/js/asistencia.js` · Commit: `feat(web): agrega pantalla de registro de asistencia` · Terminado cuando: permite registrar asistencia interactivamente con DOM seguro.

### Fase 5: Pruebas Automatizadas y Evidencias Funcionales (US1, US2, US3)
- [ ] **T-006-07** [US1, US2, US3] Pruebas unitarias y de integración en `tests/test_asistencia.py` · Commit: `test(asistencia): agrega pruebas de permisos y regla de inicio` · Terminado cuando: las pruebas verifican la ventana de 48 h, el rechazo previo a inicio y permisos de organizador.
- [ ] **T-006-08** [US1..US3] Documentación de prueba funcional PF-10 en `docs/pruebas/PF-10.md` con evidencias · Commit: `docs(pruebas): documenta pf-10 con evidencias` · Terminado cuando: se registran pasos, capturas y resultado de PF-10.
