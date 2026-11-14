# Tareas: Inscripciones y Control Atómico de Cupos

- **Rama:** `005-inscripciones-cupos` · **Responsable:** Integrante B
- **Entradas:** `specs/005-inscripciones-cupos/spec.md`, `specs/005-inscripciones-cupos/plan.md`
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** Para cupo, duplicados, cancelaciones y concurrencia, las pruebas pytest se redactan y verifican rojo → verde.

---

## Tareas de Implementación

### Fase 1: Capa de Datos y Schemas (US1, US2)
- [ ] **T-005-01** [US1] Schemas de entrada y salida para inscripción en `app/schemas/inscripcion.py` · Commit: `feat(inscripciones): agrega schemas de inscripcion` · Terminado cuando: los schemas Pydantic v2 validan y serializan fechas con zona y estados.
- [ ] **T-005-02** [US1, US2] Repositorio de inscripciones con transacción `BEGIN IMMEDIATE` e inserción condicional en `app/repositories/inscripcion_repo.py` · Commit: `feat(inscripciones): agrega repositorio con alta atomica por cupo` · Terminado cuando: la inserción condicional garantiza cero sobrecupos.

### Fase 2: Lógica de Negocio y Reglas Críticas (US1, US2, US3)
- [ ] **T-005-03** [US1, US2] Servicio de inscripciones con validación de RN-04 a RN-07 y RN-11 en `app/services/inscripcion_service.py` · Commit: `feat(inscripciones): implementa reglas de cupo duplicados y estados` · Terminado cuando: se validan cupo, duplicado activo, fecha límite y público objetivo.
- [ ] **T-005-04** [US3] Cancelación de inscripción propia y liberación de cupo en servicio y repositorio · Commit: `feat(inscripciones): implementa cancelacion con liberacion de cupo` · Terminado cuando: se permite cancelar solo antes de `fecha_inicio` y se actualiza a `cancelada`.

### Fase 3: Endpoints API REST (US1, US2, US3, US4, US5)
- [ ] **T-005-05** [US1, US2] Endpoint `POST /api/v1/eventos/{id}/inscripciones` con manejo de errores tipados 409 · Commit: `feat(inscripciones): expone post de inscripcion a un evento` · Terminado cuando: responde 201 en éxito y 409 con códigos de dominio específicos.
- [ ] **T-005-06** [US3] Endpoint `PATCH /api/v1/inscripciones/{id}/cancelar` con verificación de propietario · Commit: `feat(inscripciones): expone patch de cancelacion de inscripcion` · Terminado cuando: responde 200 liberando el cupo o 409/403 si no procede.
- [ ] **T-005-07** [US5] Endpoint `GET /api/v1/inscripciones/mias` para participante · Commit: `feat(inscripciones): expone listado de inscripciones del participante` · Terminado cuando: retorna historial cronológico con estado del evento.
- [ ] **T-005-08** [US4] Endpoint `GET /api/v1/eventos/{id}/inscripciones` con enmascaramiento diferencial · Commit: `feat(inscripciones): expone inscritos para organizador y coordinacion` · Terminado cuando: organizador ve documento completo y coordinación enmascarado (`••••1234`).

### Fase 4: Vistas Web Jinja2 y Módulos JS (US1, US5)
- [ ] **T-005-09** [US1] Conexión del botón «Inscribirse» en detalle del evento con manejo de errores DOM seguro en `app/static/js/` · Commit: `feat(web): conecta boton de inscripcion con api y muestra errores` · Terminado cuando: la interfaz consume la API con fetch sin recargar página.
- [ ] **T-005-10** [US5] Plantilla y controlador de página «Mis inscripciones» en `app/templates/inscripciones/mias.html` · Commit: `feat(web): agrega pagina de mis inscripciones con cancelacion` · Terminado cuando: permite ver inscripciones y cancelar interactivamente.

### Fase 5: Pruebas Automatizadas y Evidencias Funcionales (US1, US2, US3, US4)
- [ ] **T-005-11** [US1, US2, US3] Pruebas unitarias y de integración en `tests/test_inscripciones.py` · Commit: `test(inscripciones): agrega pruebas de cupo duplicados y concurrencia` · Terminado cuando: suite de pruebas verifica cupo, duplicados, público y simulación concurrente con hilos.
- [ ] **T-005-12** [US1, US2] Evidencia de prueba de concurrencia y simultaneidad para PF-07 · Commit: `docs(pruebas): registra verificacion manual de cupo bajo simultaneidad` · Terminado cuando: se documenta la prueba de estrés de cupo con evidencias.
- [ ] **T-005-13** [US1..US5] Documentación de pruebas funcionales PF-05 a PF-08 en `docs/pruebas/` · Commit: `docs(pruebas): documenta pf-05 a pf-08 con evidencias` · Terminado cuando: los documentos PF-05 a PF-08 quedan completos con pasos y resultados.
