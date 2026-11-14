---
description: "Tareas atómicas para implementar E4 — Catálogo y consulta de eventos"
---

# Tareas: Catálogo y consulta de eventos (E4)

- **Rama:** `004-catalogo-eventos` · **Responsable:** Integrante A
- **Entradas:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/004-catalogo-eventos/spec.md), [plan.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/004-catalogo-eventos/plan.md)
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** redactar primero en rojo las pruebas críticas del catálogo (`RN-01`, filtros, `422`, conteo real de cupos `CA-02`, `404` ante borrador/cancelado/inexistente) antes de implementar los endpoints.

## Convención de formato

`- [ ] T-004-XX [P?] [US?] Descripción concreta con ruta exacta · Commit: \`tipo(alcance): descripción\` · Terminado cuando: [criterio verificable]`

---

## Fase 1: Pruebas primero del catálogo, filtros y 404 (Rojo)

- [ ] T-004-01 [US1] [US2] [US3] Crear pruebas iniciales rojo en `tests/test_catalogo.py` (listado público solo `publicado`, ocultación por defecto de finalizados y opción `incluir_finalizados=true`, orden estable por `fecha_inicio`, paginación, filtros `tipo`/`modalidad`/fechas/`texto` con `%` y `_`, validaciones `422`, detalle con cálculo real `cupos_disponibles` tras inscripción activa y cancelada, y `404 EVENTO_NO_ENCONTRADO` ante inexistente, `borrador` o `cancelado`) · Commit: `test(catalogo): agrega pruebas rojo de catalogo, filtros y 404` · Terminado cuando: las pruebas existen en `tests/test_catalogo.py` y fallan antes de implementar E4

---

## Fase 2: Schemas, repositorio y servicio de dominio (US1..US3)

**Objetivo:** Implementar validación de filtros, consultas SQL filtradas/paginadas seguras y servicio `catalogo_service.py` sin importar FastAPI ni incurrir en N+1.
**Prueba independiente:** Al conectar el router en Fase 3, toda la suite de API en `tests/test_catalogo.py` pasa en verde.

- [ ] T-004-02 [US1] [US2] Implementar `CatalogoFiltros`, `CatalogoEventoResumen`, `CatalogoEventoDetalle` y `CatalogoPaginadoSalida` en `app/schemas/catalogo.py` · Commit: `feat(catalogo): agrega schemas de catalogo, filtros y paginacion` · Terminado cuando: validan rangos de fechas con zona, `pagina >= 1`, `1 <= tamano <= 50` y salidas sin campos internos
- [ ] T-004-03 [US1] [US2] Ampliar `app/repositories/evento_repo.py` con `obtener_publicado_por_id` y `buscar_publicados_paginado` (filtros combinables, escape de `%`/`_`/`\`, orden por `fecha_inicio ASC, id ASC`) · Commit: `feat(catalogo): agrega consulta paginada y filtrada de publicados` · Terminado cuando: toda consulta SQL del catálogo está encapsulada en `evento_repo.py`
- [ ] T-004-04 [US1] [US2] [US3] Implementar `app/services/catalogo_service.py` (`listar_catalogo`, `obtener_detalle_catalogo`, `existe_evento_publicado`) reutilizando `calcular_estado_efectivo` e `inscripcion_repo` sin N+1 y sin importar FastAPI · Commit: `feat(catalogo): implementa servicio de catalogo y calculo de cupos` · Terminado cuando: `cupos_disponibles`, `inscripciones_abiertas` y `404 EVENTO_NO_ENCONTRADO` se calculan en el servicio

---

## Fase 3: Endpoints REST públicos y verificación en verde (US1..US3)

**Objetivo:** Exponer `/api/v1/catalogo/eventos` y `/api/v1/catalogo/eventos/{evento_id}` y poner en verde `tests/test_catalogo.py` y `tests/test_scripts_web.py`.
**Prueba independiente:** `pytest -q` 100 % en verde con todos los casos de API de E4.

- [ ] T-004-05 [US1] [US2] [US3] Implementar en `app/api/v1/catalogo.py` los endpoints `GET /catalogo/eventos` y `GET /catalogo/eventos/{evento_id}` y retirar el stub `501` de `/api/v1/catalogo/eventos` en `tests/test_scripts_web.py` · Commit: `feat(catalogo): expone endpoints rest del catalogo publico` · Terminado cuando: `tests/test_catalogo.py` y `tests/test_scripts_web.py` pasan en verde

---

## Fase 4: Interfaz web segura, documentación PF y cierre E4

**Objetivo:** Entregar las vistas `/` y `/eventos/{evento_id}` (con página `404` amigable y `catalogo.js` sin `innerHTML`), documentar `PF-03` y `PF-04` y verificar la app completa.
**Prueba independiente:** `/` responde `200`, `/eventos/{id}` responde `200` o `404` amigable, `catalogo.js` no usa `innerHTML`, y `ruff` + `pytest -q` + HTTPS pasan sin errores.

- [ ] T-004-06 [US1] [US2] [US3] Implementar `app/web/catalogo.py` (`/` y `/eventos/{evento_id}` con `404` HTML amigable), actualizar `app/templates/index.html`, crear `app/templates/catalogo/detalle.html` (con `#zona-inscripcion` preparado para E5) y `app/templates/catalogo/no_encontrado.html`, estilos en `app/static/css/styles.css`, módulo `app/static/js/catalogo.js` (sin `innerHTML`) y pruebas web en `tests/test_catalogo.py` · Commit: `feat(web): agrega vistas web de catalogo, detalle y 404` · Terminado cuando: las vistas operan por `fetch` sin `innerHTML` y con pruebas web en verde
- [ ] T-004-07 [US1] [US2] [US3] Documentar `docs/pruebas/PF-03.md` y `docs/pruebas/PF-04.md` siguiendo la estructura funcional con trazabilidad RF/RN/CA · Commit: `docs(pruebas): documenta casos funcionales PF-03 y PF-04` · Terminado cuando: ambos documentos detallan condiciones, pasos, datos y resultados verificados
- [ ] T-004-08 Ejecutar verificación completa de E4 (`ruff check .`, `ruff format --check .`, `pytest -q`, arranque HTTPS sobre `/`, `/eventos/{id}`, `/eventos/999999` y `/docs`) y marcar tareas verificadas en `specs/004-catalogo-eventos/tasks.md` · Commit: `docs(specs): marca tareas verificadas de E4 tras pruebas en verde` · Terminado cuando: `ruff`, `pytest -q` y verificación HTTPS pasan con 0 fallos

---

## Tabla resumen de trazabilidad

| ID | Tarea | Depende de | Archivos clave | Commit sugerido | Terminado cuando | Estado |
|---|---|---|---|---|---|:-:|
| T-004-01 | Pruebas rojo catálogo, filtros y 404 | — | `tests/test_catalogo.py` | `test(catalogo): agrega pruebas rojo de catalogo, filtros y 404` | Fallan antes del código E4 | [ ] |
| T-004-02 | Schemas del catálogo y filtros | T-004-01 | `app/schemas/catalogo.py` | `feat(catalogo): agrega schemas de catalogo, filtros y paginacion` | Schemas y filtros validados | [ ] |
| T-004-03 | Consulta paginada en `evento_repo.py` | T-004-01 | `app/repositories/evento_repo.py` | `feat(catalogo): agrega consulta paginada y filtrada de publicados` | SQL filtrado con escape `LIKE` | [ ] |
| T-004-04 | Servicio `catalogo_service.py` sin FastAPI | T-004-02, T-004-03 | `app/services/catalogo_service.py` | `feat(catalogo): implementa servicio de catalogo y calculo de cupos` | Cupos calculados sin N+1 | [ ] |
| T-004-05 | Router `/catalogo/eventos` y `{id}` | T-004-04 | `app/api/v1/catalogo.py`, `tests/test_scripts_web.py` | `feat(catalogo): expone endpoints rest del catalogo publico` | `test_catalogo.py` y `test_scripts_web.py` OK | [ ] |
| T-004-06 | Vistas `/`, `/eventos/{id}`, 404 y `catalogo.js` | T-004-05 | `app/web/catalogo.py`, `app/templates/index.html`, `app/templates/catalogo/*`, `app/static/js/catalogo.js` | `feat(web): agrega vistas web de catalogo, detalle y 404` | HTML `200`/`404` sin `innerHTML` | [ ] |
| T-004-07 | Docs funcionales `PF-03` y `PF-04` | T-004-05 | `docs/pruebas/PF-03.md`, `docs/pruebas/PF-04.md` | `docs(pruebas): documenta casos funcionales PF-03 y PF-04` | Casos y trazabilidad listos | [ ] |
| T-004-08 | Verificación final `ruff`, `pytest`, HTTPS | T-004-06, T-004-07 | `specs/004-catalogo-eventos/tasks.md` | `docs(specs): marca tareas verificadas de E4 tras pruebas en verde` | `ruff` y `pytest -q` 100 % verdes | [ ] |
