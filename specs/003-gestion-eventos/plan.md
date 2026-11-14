# Plan de Implementación: Gestión de eventos (E3)

**Rama:** `003-gestion-eventos` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/003-gestion-eventos/spec.md)
**Entrada:** Especificación aprobada en G1 en `specs/003-gestion-eventos/spec.md` (sin `[PENDIENTE]` bloqueantes).

## 1. Resumen y decisiones técnicas

El objetivo de E3 es implementar el ciclo completo de gestión de actividades por parte del organizador sobre **HTTPS obligatorio**: crear borradores, consultar eventos propios con ocupación y estado calculado `finalizado`, leer detalle individual para edición, editar validando cupo mínimo frente a inscritos activos, publicar directamente sin aprobación y cancelar con motivo preservando inscripciones.

Decisiones principales y alternativas descartadas:
- **Reutilización única de validación de fechas (`validar_coherencia_fechas`):** extraer la regla `fecha_fin > fecha_inicio` y `fecha_limite_inscripcion <= fecha_inicio` en un validador compartido en `app/schemas/evento.py` para aplicarla tanto en `EventoCrear` como en `evento_service.actualizar_evento` tras combinar campos parciales de `PATCH` con los valores persistidos en BD. *Descartado:* duplicar condiciones en cada schema y servicio o validar `PATCH` sin el contexto del registro actual.
- **Separación explícita de `estado` persistido vs `estado_efectivo` calculado (`RN-12`):** `EventoSalida` conserva `estado` (`borrador`/`publicado`/`cancelado`) y añade `estado_efectivo` (`finalizado` cuando `estado == "publicado"` y `fecha_fin < ahora_utc()`), `inscripciones_abiertas`, `inscripciones_activas` y `cupos_disponibles`. *Descartado:* sobreescribir `estado` en BD por cron o mezclar estado guardado y calculado.
- **Verificación de existencia (404) antes de propietario (403) en `_obtener_evento_del_organizador`:** evita errores ambiguos y garantiza `404 EVENTO_NO_ENCONTRADO` para IDs inexistentes y `403 SIN_PERMISO` cuando pertenece a otro organizador (`RN-10`) sin filtrar sus datos. *Descartado:* devolver `404` a otro organizador, porque PF-09 y HU-E3-02 exigen explícitamente `403 SIN_PERMISO`.
- **Conteo sin N+1 en listado del organizador:** `listar_eventos_organizador` usa `inscripcion_repo.contar_activas_por_eventos(db, ids)` en una sola consulta agrupada. *Descartado:* ejecutar `contar_activas` por cada fila en bucle.
- **Segundo subrouter en `app/api/v1/eventos.py` para `/organizador/eventos`:** exportar `router` (`/eventos`) y `organizador_router` (`/organizador`) e incluir ambos en `app/api/router.py` manteniendo la URL oficial `/api/v1/organizador/eventos` sin crear archivos no asignados a E3.
- **Plantillas web compartidas para crear y editar:** usar `eventos/mis_eventos.html` y `eventos/formulario.html` (reutilizada para `/nuevo` y `/{evento_id}/editar`) manejadas desde `app/static/js/eventos.js` con `fetch`, `aIsoBogota`, `formatearFechaBogota`, `crearNodo` y cero `innerHTML`.

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.12 (`target-version = "py311"`).
- **Dependencias:** FastAPI, SQLAlchemy 2.x, Pydantic v2, Jinja2 y utilidades E1/E2 ya instaladas (`fechas.py`, `errors.py`, `deps.py`, `inscripcion_repo.py`). No requiere nuevas librerías.
- **Almacenamiento:** tabla existente `eventos` (`ck_eventos_cupo`, `ck_eventos_fechas`, `ck_eventos_limite`, `ix_eventos_organizador`) y lectura agregada de `inscripciones`. Sin nuevas migraciones Alembic.
- **Pruebas:** `pytest` + `TestClient(base_url="https://testserver")` con archivo SQLite temporal y cabecera `Origin: https://testserver` en mutaciones autenticadas por cookie (`verificar_csrf`).

## 3. Verificación contra la constitución *(puerta obligatoria)*

Revisión frente a `.specify/memory/constitution.md` (v2.0.2):
- [x] I. La spec manda (`specs/003-gestion-eventos/spec.md` aprobada en G1, sin `[PENDIENTE]`)
- [x] II. Capas estrictas (`api/v1/eventos.py` → `services/evento_service.py` → `repositories/evento_repo.py` → `models/evento.py`; `evento_service.py` sin FastAPI)
- [x] III. Validación en servidor (Pydantic v2 `extra="forbid"`, `FechaConZona`) y BD (`CHECK` de cupo y fechas, FK `organizador_id`)
- [x] IV. Cupos calculados dinámicamente (`cupo_maximo - inscripciones_activas`) vía `inscripcion_repo` sin almacenar disponibles
- [x] V. Mínimo privilegio (`require_roles(Rol.ORGANIZADOR)`, `require_web_roles(Rol.ORGANIZADOR)`, propiedad `organizador_id == usuario.id` en cada operación)
- [x] VI. Errores uniformes (`401`, `403`, `404`, `409`, `422` sin `input` ni trazas sensibles)
- [x] VII. Sin secretos ni datos reales (documentos ficticios y fechas de prueba en `UTC`/`-05:00`)
- [x] VIII. Commits atómicos en español en rama `003-gestion-eventos`; PR en borrador en G2
- [x] IX. `ruff` y `pytest` en verde antes de G4 (y `export_openapi.py --check` si E10 ya está en `main`)
- [x] X. Compatible con arranque HTTPS local y Docker sin pasos ni paquetes nuevos
- [x] XI. Respeta el contrato compartido sin modificar modelos ni `inscripcion_repo.py`
- [x] XII. Clarificaciones cerradas con el humano en G1 (`422` en publicación con fecha pasada, cancelación solo `publicado` con motivo ≥ 5 chars, `estado_efectivo`, `GET /eventos/{id}` para propietario)

## 4. Estructura y archivos por capa

```text
specs/003-gestion-eventos/
├── spec.md              # Especificación aprobada (G1)
├── plan.md              # Este documento
├── checklists/
│   └── requirements.md  # Checklist de calidad de spec
└── tasks.md             # Tareas atómicas T-003-XX
```

| Capa / Ámbito | Archivos creados o modificados en E3 | Responsable |
|---|---|:-:|
| Schemas | `app/schemas/evento.py` (`EventoCrear`, `EventoActualizar`, `EventoCancelar`, `EventoSalida`, `validar_coherencia_fechas`) | A |
| Repositorio | `app/repositories/evento_repo.py` (`obtener_por_id`, `listar_por_organizador`, `crear`, `guardar`) | A |
| Servicio | `app/services/evento_service.py` (`crear_evento`, `obtener_evento_propio`, `listar_eventos_organizador`, `actualizar_evento`, `publicar_evento`, `cancelar_evento`, cálculo `finalizado`) | A |
| API REST | `app/api/v1/eventos.py` (`router` + `organizador_router`), `app/api/router.py` (registrar `organizador_router`) | A |
| Web y Frontend | `app/web/eventos.py`, `app/templates/eventos/mis_eventos.html`, `app/templates/eventos/formulario.html`, `app/static/js/eventos.js`, `app/static/css/styles.css` | A |
| Pruebas y Docs | `tests/test_eventos.py`, `tests/test_permisos.py` (propiedad `RN-10`), `tests/test_scripts_web.py` (actualizar lista 501 tras implementar `POST /eventos`), `docs/pruebas/PF-01.md`, `docs/pruebas/PF-02.md`, `docs/pruebas/PF-09.md` | A |

## 5. Contrato de API, modelo de datos y seguridad

- **Endpoints activos en E3 (`/api/v1`, sobre HTTPS + cookie + `verificar_csrf`):**
  - `POST /api/v1/eventos` → **201** (`EventoSalida`, `estado="borrador"`) | `401`, `403`, `422`
  - `GET /api/v1/eventos/{evento_id}` → **200** (`EventoSalida`, solo propietario) | `401`, `403`, `404`
  - `PATCH /api/v1/eventos/{evento_id}` → **200** (`EventoSalida`) | `401`, `403`, `404`, `409`, `422`
  - `POST /api/v1/eventos/{evento_id}/publicar` → **200** (`EventoSalida`, `estado="publicado"`) | `401`, `403`, `404`, `409`, `422`
  - `POST /api/v1/eventos/{evento_id}/cancelar` → **200** (`EventoSalida`, `estado="cancelado"`) | `401`, `403`, `404`, `409`, `422`
  - `GET /api/v1/organizador/eventos` → **200** (`list[EventoSalida]`) | `401`, `403`
- **Rutas web (`app/web/eventos.py`, protegidas con `require_web_roles(Rol.ORGANIZADOR)`):**
  - `GET /organizador/eventos` → `200` (listado «Mis eventos») / `303 /login` / `403`
  - `GET /organizador/eventos/nuevo` → `200` (crear evento) / `303 /login` / `403`
  - `GET /organizador/eventos/{evento_id}/editar` → `200` (editar evento) / `303 /login` / `403`
- **Modelo de datos:** sin alteraciones a `app/models/evento.py` ni migraciones.

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| `tests/test_scripts_web.py` espera `501` en `POST /api/v1/eventos` (stub E1) | Actualizar `test_stubs_api_v1_responden_501_uniforme` al implementar los endpoints de E3 dejando solo los stubs de E4–E7 |
| Reloj en pruebas del cálculo `finalizado` o publicación de inicio pasado | Inyectar o sustituir `app.core.fechas.ahora_utc` (`monkeypatch`) o usar fechas pasadas en `borrador`/`publicado` en BD temporal sin depender de `sleep` |
| Edición parcial (`PATCH`) rompe `RN-03` contra fechas ya guardadas | Combinar en `evento_service` valores nuevos con existentes y ejecutar `validar_coherencia_fechas` antes de persistir |
| Campos de fecha HTML `datetime-local` sin zona horaria al enviar formularios | Convertir siempre con `aIsoBogota(...)` (`-05:00`) en `app/static/js/eventos.js` antes de enviar por `fetch` |

## 7. Registro de complejidad

No hay excepciones ni violaciones a la constitución en este plan.
