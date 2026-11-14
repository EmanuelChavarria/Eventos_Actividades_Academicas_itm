---
description: "Tareas atómicas para implementar E3 — Gestión de eventos"
---

# Tareas: Gestión de eventos (E3)

- **Rama:** `003-gestion-eventos` · **Responsable:** Integrante A
- **Entradas:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/003-gestion-eventos/spec.md), [plan.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/003-gestion-eventos/plan.md)
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** para permisos/propiedad (`RN-10`), reglas de fechas (`RN-03`), cupo mínimo frente a inscritos (`RN-09`), bloqueo en `cancelado`/`finalizado` y publicación directa, redacta primero las pruebas `pytest` en rojo y luego la implementación (rojo → verde).

## Convención de formato

`- [ ] T-003-XX [P?] [US?] Descripción concreta con ruta exacta · Commit: \`tipo(alcance): descripción\` · Terminado cuando: [criterio verificable]`

---

## Fase 1: Pruebas primero para reglas críticas de eventos y propiedad (Rojo)

- [x] T-003-01 [US1] [US2] [US3] [US4] [US5] Crear pruebas iniciales rojo en `tests/test_eventos.py` (creación `201` en `borrador`, `422` sin persistir por cupo/fechas/zona horaria, publicación `borrador → publicado`, `409` en no borrador, `422` en inicio pasado, edición parcial y subida/bajada de cupo respetando `inscripciones_activas`, `409` al bajar debajo de activas o editar `cancelado`/`finalizado`, cancelación con motivo `≥ 5` chars preservando inscripciones y `422` motivo corto, listado `GET /api/v1/organizador/eventos` con cálculo `finalizado` y `GET /api/v1/eventos/{id}`) · Commit: `test(eventos): agrega pruebas rojo de ciclo de vida y reglas` · Terminado cuando: las pruebas existen en `tests/test_eventos.py` y fallan por ausencia de implementación E3
- [x] T-003-02 [P] [US1] [US2] [US3] [US4] [US5] Ampliar `tests/test_permisos.py` con pruebas rojo de autorización y propiedad de eventos (`401` sin sesión, `403` para participante/coordinación y `403 SIN_PERMISO` cuando un organizador intenta leer, editar, publicar o cancelar eventos de otro organizador según `RN-10`) · Commit: `test(eventos): agrega pruebas rojo de permisos y propiedad` · Terminado cuando: las pruebas existen y fallan antes de implementar endpoints y servicio

---

## Fase 2: Schemas, repositorio y servicio de dominio (US1..US5)

**Objetivo:** Implementar validación Pydantic v2 (`FechaConZona`, `extra="forbid"`), persistencia en repositorio y todas las reglas de negocio en `services/evento_service.py` sin importar FastAPI.
**Prueba independiente:** Al conectar el router en Fase 3, todas las pruebas unitarias e integración de `test_eventos.py` y `test_permisos.py` pasan en verde.

- [x] T-003-03 [US1] [US3] [US4] [US5] Implementar schemas `EventoCrear`, `EventoActualizar`, `EventoCancelar`, `EventoSalida` (con `estado_efectivo`, `inscripciones_abiertas`, `inscripciones_activas`, `cupos_disponibles`) y helper `validar_coherencia_fechas` en `app/schemas/evento.py` · Commit: `feat(eventos): agrega schemas de evento con validaciones de entrada` · Terminado cuando: los schemas validan fechas con zona, rangos, `extra="forbid"` y salida calculada
- [x] T-003-04 [P] [US1] [US5] Implementar `app/repositories/evento_repo.py` (`obtener_por_id`, `listar_por_organizador`, `crear`, `guardar`) con SQLAlchemy 2.x · Commit: `feat(eventos): implementa repositorio de eventos` · Terminado cuando: toda operación SQL sobre `eventos` está encapsulada en el repositorio
- [x] T-003-05 [US1] [US2] [US3] [US4] [US5] Implementar `app/services/evento_service.py` (`crear_evento`, `obtener_evento_propio`, `listar_eventos_organizador` con `contar_activas_por_eventos`, `actualizar_evento` con `RN-03`/`RN-09`, `publicar_evento` con `RN-03`/`RN-12`, `cancelar_evento` preservando inscripciones, propiedad `RN-10` y cálculo `finalizado`) sin importar FastAPI · Commit: `feat(eventos): implementa servicio de gestion y reglas de eventos` · Terminado cuando: todas las reglas RN-02, RN-03, RN-09, RN-10, RN-12, RN-18 y RN-20 residen en `services/`

---

## Fase 3: Endpoints REST y verificación en verde (US1..US5)

**Objetivo:** Exponer `/api/v1/eventos/*` y `/api/v1/organizador/eventos` con control de rol/CSRF y poner en verde `test_eventos.py` y `test_permisos.py`.
**Prueba independiente:** `pytest -q` 100 % en verde con todos los casos de API de E3 y permisos.

- [ ] T-003-06 [US1] [US2] [US3] [US4] [US5] Implementar en `app/api/v1/eventos.py` los routers `router` (`/eventos`: `POST /`, `GET /{evento_id}`, `PATCH /{evento_id}`, `POST /{evento_id}/publicar`, `POST /{evento_id}/cancelar`) y `organizador_router` (`/organizador/eventos`), registrar `organizador_router` en `app/api/router.py` y actualizar la lista de stubs `501` en `tests/test_scripts_web.py` · Commit: `feat(eventos): expone endpoints rest de gestion de eventos` · Terminado cuando: toda la suite de API en `tests/test_eventos.py`, `tests/test_permisos.py` y `tests/test_scripts_web.py` pasa en verde

---

## Fase 4: Interfaz web segura, documentación PF y cierre E3

**Objetivo:** Entregar las vistas web del organizador (Jinja2 + `eventos.js`), documentar pruebas `PF-01`, `PF-02` y ampliar `PF-09`, y verificar todo el conjunto.
**Prueba independiente:** Vistas web responden `200`/`303`/`403` según sesión/rol, `eventos.js` no usa `innerHTML`, y `ruff` + `pytest -q` + arranque HTTPS pasan sin errores.

- [ ] T-003-07 [US5] Implementar rutas web en `app/web/eventos.py` (`/organizador/eventos`, `/organizador/eventos/nuevo`, `/organizador/eventos/{evento_id}/editar` protegidas con `require_web_roles(Rol.ORGANIZADOR)`), plantillas `app/templates/eventos/mis_eventos.html` y `app/templates/eventos/formulario.html`, estilos auxiliares en `app/static/css/styles.css` y módulo `app/static/js/eventos.js` (`fetch` a `/api/v1`, `aIsoBogota`, `formatearFechaBogota`, `crearNodo`/`textContent`) más pruebas web en `tests/test_eventos.py` · Commit: `feat(web): agrega vistas de gestion de eventos del organizador` · Terminado cuando: las vistas cargan y operan por `fetch` sin `innerHTML` con pruebas web en verde
- [ ] T-003-08 [US1] [US2] Documentar `docs/pruebas/PF-01.md`, `docs/pruebas/PF-02.md` y ampliar `docs/pruebas/PF-09.md` con casos de propiedad entre organizadores · Commit: `docs(pruebas): documenta casos PF-01, PF-02 y ampliacion de PF-09` · Terminado cuando: los tres documentos siguen la estructura de prueba funcional con trazabilidad RF/RN/CA
- [ ] T-003-09 Ejecutar verificación completa de E3 (`ruff check .`, `ruff format --check .`, `pytest -q`, arranque HTTPS sobre `/docs` y vistas `/organizador/eventos`), actualizar estados en `specs/003-gestion-eventos/tasks.md` y regenerar OpenAPI si aplica · Commit: `docs(specs): marca tareas verificadas de E3 tras pruebas en verde` · Terminado cuando: `ruff`, `pytest -q` y verificación HTTPS pasan con 0 fallos

---

## Tabla resumen de trazabilidad

| ID | Tarea | Depende de | Archivos clave | Commit sugerido | Terminado cuando | Estado |
|---|---|---|---|---|---|:-:|
| T-003-01 | Pruebas rojo ciclo de vida y reglas E3 | — | `tests/test_eventos.py` | `test(eventos): agrega pruebas rojo de ciclo de vida y reglas` | Fallan antes del código E3 | [x] |
| T-003-02 | Pruebas rojo permisos y propiedad (`RN-10`) | — | `tests/test_permisos.py` | `test(eventos): agrega pruebas rojo de permisos y propiedad` | Fallan antes de endpoints/servicio | [x] |
| T-003-03 | Schemas y validador fechas en `evento.py` | T-003-01 | `app/schemas/evento.py` | `feat(eventos): agrega schemas de evento con validaciones de entrada` | Validaciones y `EventoSalida` listos | [x] |
| T-003-04 | Repositorio `evento_repo.py` | T-003-01 | `app/repositories/evento_repo.py` | `feat(eventos): implementa repositorio de eventos` | SQL encapsulado en repositorio | [x] |
| T-003-05 | Servicio `evento_service.py` sin FastAPI | T-003-03, T-003-04 | `app/services/evento_service.py` | `feat(eventos): implementa servicio de gestion y reglas de eventos` | RN-02/03/09/10/12/18/20 listas | [x] |
| T-003-06 | Router `/eventos` y `/organizador/eventos` | T-003-05 | `app/api/v1/eventos.py`, `app/api/router.py`, `tests/test_scripts_web.py` | `feat(eventos): expone endpoints rest de gestion de eventos` | `test_eventos.py` y `test_permisos.py` OK | [ ] |
| T-003-07 | Vistas web, templates y `eventos.js` | T-003-06 | `app/web/eventos.py`, `app/templates/eventos/*`, `app/static/js/eventos.js` | `feat(web): agrega vistas de gestion de eventos del organizador` | HTML `200`/`303`/`403` sin `innerHTML` | [ ] |
| T-003-08 | Docs `PF-01`, `PF-02` y `PF-09` | T-003-06 | `docs/pruebas/PF-01.md`, `PF-02.md`, `PF-09.md` | `docs(pruebas): documenta casos PF-01, PF-02 y ampliacion de PF-09` | Casos y trazabilidad documentados | [ ] |
| T-003-09 | Verificación final `ruff`, `pytest`, HTTPS | T-003-07, T-003-08 | `specs/003-gestion-eventos/tasks.md` | `docs(specs): marca tareas verificadas de E3 tras pruebas en verde` | `ruff` y `pytest -q` 100 % verdes | [ ] |
