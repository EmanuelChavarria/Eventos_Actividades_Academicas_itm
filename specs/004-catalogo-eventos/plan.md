# Plan de Implementación: Catálogo y consulta de eventos (E4)

**Rama:** `004-catalogo-eventos` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/004-catalogo-eventos/spec.md)
**Entrada:** Especificación aprobada en G1 en `specs/004-catalogo-eventos/spec.md` (sin `[PENDIENTE]` bloqueantes).

## 1. Resumen y decisiones técnicas

El objetivo de E4 es exponer el catálogo público paginado de eventos publicados (`/api/v1/catalogo/eventos` y `/`) y su detalle en tiempo real (`/api/v1/catalogo/eventos/{evento_id}` y `/eventos/{evento_id}`), garantizando disponibilidad real calculada sin N+1, escape seguro de filtros `LIKE`, fechas UTC ↔ `America/Bogota`, manejo `404` controlado y preparación limpia de la vista de detalle para que E5 conecte la inscripción.

Decisiones principales y alternativas descartadas:
- **Reutilización de `calcular_estado_efectivo` desde `evento_service.py`:** evitar duplicar la lógica de `finalizado` e `inscripciones_abiertas` entre E3 y E4 invocando un helper único de dominio desde `catalogo_service.py`. *Descartado:* reescribir comparaciones de fecha duplicadas.
- **Conteo agregado único con `contar_activas_por_eventos`:** en el listado paginado se consultan primero los eventos de la página y el `total`, y luego en una sola consulta `GROUP BY` se obtienen las inscripciones activas de esos IDs. *Descartado:* contar por fila en bucle o almacenar un contador en BD (`CA-02`).
- **Escape explícito de `%`, `_` y `\` en filtros `texto` (`RNF-08`):** normalizar el término de búsqueda con `escape="\\"` en SQLAlchemy (`ilike`) para que búsquedas literales con `%` o `_` no actúen como comodines SQL arbitrarios.
- **Vista web `/eventos/{evento_id}` con verificación previa en servicio:** el router web llama a `catalogo_service.existe_evento_publicado(db, evento_id)` (respetando capas `web → service → repo`); si no existe o no está publicado responde HTTP **404** con `catalogo/no_encontrado.html`; si existe responde **200** con `catalogo/detalle.html` y `catalogo.js` carga el detalle actualizado vía `fetch` (dejando un contenedor `#zona-inscripcion` con `data-evento-id` listo para E5).
- **Schema público separado de `EventoSalida` de gestión:** `CatalogoEventoResumen` y `CatalogoEventoDetalle` no exponen `organizador_id`, `motivo_cancelacion` ni estados internos (`borrador`/`cancelado`).

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.12 (`target-version = "py311"`).
- **Dependencias:** FastAPI, SQLAlchemy 2.x, Pydantic v2, Jinja2 y utilidades existentes (`fechas.py`, `errors.py`, `inscripcion_repo.py`, `api.js`). Sin dependencias nuevas ni migraciones.
- **Almacenamiento:** lectura sobre `eventos` (índice `ix_eventos_estado_inicio`) e `inscripciones`.
- **Pruebas:** `pytest` + `TestClient(base_url="https://testserver")` con BD SQLite temporal.

## 3. Verificación contra la constitución *(puerta obligatoria)*

Revisión frente a `.specify/memory/constitution.md` (v2.0.2):
- [x] I. La spec manda (`specs/004-catalogo-eventos/spec.md` aprobada en G1, sin `[PENDIENTE]`)
- [x] II. Capas estrictas (`api/v1/catalogo.py` y `web/catalogo.py` → `services/catalogo_service.py` → `repositories/evento_repo.py` / `inscripcion_repo.py`; `catalogo_service.py` sin FastAPI)
- [x] III. Validación en servidor (Pydantic v2 / Query params, `FechaConZona`, `fecha_hasta >= fecha_desde`, escape `LIKE`)
- [x] IV. Cupos calculados dinámicamente (`cupo_maximo - inscripciones_activas`) sin N+1
- [x] V. Acceso público estricto solo a `estado == "publicado"`; `404` controlado para borradores/cancelados
- [x] VI. Errores uniformes (`404 EVENTO_NO_ENCONTRADO`, `422 ERROR_VALIDACION`/`REGLA_NEGOCIO`) sin `input` ni fugas
- [x] VII. Sin secretos ni datos reales
- [x] VIII. Commits atómicos en español en rama `004-catalogo-eventos`; PR en borrador en G2
- [x] IX. `ruff` y `pytest` en verde antes de G4
- [x] X. Compatible con arranque HTTPS local y Docker sin pasos nuevos
- [x] XI. Contrato compartido respetado sin modificar modelos, errores ni `inscripcion_repo.py`
- [x] XII. Clarificaciones resueltas con el humano en G1

## 4. Estructura y archivos por capa

```text
specs/004-catalogo-eventos/
├── spec.md              # Especificación aprobada (G1)
├── plan.md              # Este documento
├── checklists/
│   └── requirements.md  # Checklist de calidad de spec
└── tasks.md             # Tareas atómicas T-004-XX
```

| Capa / Ámbito | Archivos creados o modificados en E4 | Responsable |
|---|---|:-:|
| Schemas | `app/schemas/catalogo.py` (`CatalogoFiltros`, `CatalogoEventoResumen`, `CatalogoEventoDetalle`, `CatalogoPaginadoSalida`) | A |
| Repositorio | `app/repositories/evento_repo.py` (`obtener_publicado_por_id`, `buscar_publicados_paginado` con escape `LIKE`) | A |
| Servicio | `app/services/catalogo_service.py` (`listar_catalogo`, `obtener_detalle_catalogo`, `existe_evento_publicado`) | A |
| API REST | `app/api/v1/catalogo.py` (`GET /catalogo/eventos`, `GET /catalogo/eventos/{evento_id}`) | A |
| Web y Frontend | `app/web/catalogo.py`, `app/templates/index.html`, `app/templates/catalogo/detalle.html`, `app/templates/catalogo/no_encontrado.html`, `app/static/js/catalogo.js`, `app/static/css/styles.css` | A |
| Pruebas y Docs | `tests/test_catalogo.py`, `tests/test_scripts_web.py` (retirar stub `501` de `/catalogo/eventos`), `docs/pruebas/PF-03.md`, `docs/pruebas/PF-04.md` | A |

## 5. Contrato de API y rutas web

- **Endpoints públicos en E4 (`/api/v1`, sobre HTTPS, sin sesión requerida):**
  - `GET /api/v1/catalogo/eventos` → **200** (`CatalogoPaginadoSalida`) | `422`
    - Query: `tipo`, `modalidad`, `fecha_desde`, `fecha_hasta`, `texto`, `incluir_finalizados` (`false`), `pagina` (`1`), `tamano` (`10`, máx. `50`).
  - `GET /api/v1/catalogo/eventos/{evento_id}` → **200** (`CatalogoEventoDetalle`) | `404 EVENTO_NO_ENCONTRADO`
- **Rutas web (`app/web/catalogo.py`):**
  - `GET /` → **200** (`index.html`, catálogo público interactivo con `catalogo.js`)
  - `GET /eventos/{evento_id}` → **200** (`catalogo/detalle.html` con `catalogo.js`) o **404** (`catalogo/no_encontrado.html` si no existe o no está publicado)

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| `tests/test_scripts_web.py` espera `501` en `GET /api/v1/catalogo/eventos` (stub E1) | Actualizar `test_stubs_api_v1_responden_501_uniforme` al implementar `T-004-05` dejando solo E5–E7 |
| Comodines `%` o `_` en filtro `texto` interpretados por SQLite `LIKE` | Helper `_escapar_like` con `escape="\\"` sobre `%`, `_` y `\` |
| Consultas N+1 al calcular cupos por página | Llamada única a `inscripcion_repo.contar_activas_por_eventos(db, ids)` |
| Futura integración de botón «Inscribirse» por B en E5 | Incluir `<div id="zona-inscripcion" data-evento-id="...">` bien estructurado en `catalogo/detalle.html` para facilitar un cambio mínimo en E5 |

## 7. Registro de complejidad

No hay excepciones ni violaciones a la constitución en este plan.
