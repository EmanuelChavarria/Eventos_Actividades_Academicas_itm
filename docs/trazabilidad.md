# Matriz de Trazabilidad Integral — Proyecto PF-04

**Proyecto:** Organización de eventos y actividades académicas (Python · FastAPI · SQLite · Jinja2 · SDD)  
**Asignatura:** Aplicaciones y Servicios Web · Tecnología en Desarrollo de Software  
**Responsable (E9-B):** Integrante A (consolidación y cierre sobre base inicial del Integrante B en PR `#18`)  
**Fuente de verdad:** `docs/01_analisis_y_especificaciones.md`, `.specify/memory/constitution.md`

Este documento establece la trazabilidad bidireccional entre las **Condiciones de Aceptación (CA)**, los **Requisitos Funcionales (RF)**, los **Requisitos No Funcionales (RNF)**, las especificaciones de Spec Kit (`specs/`), los componentes de software (rutas, servicios, repositorios, modelos), los Pull Requests (PR) y las pruebas (funcionales PF y automatizadas pytest).

---

## 1. Trazabilidad de Condiciones de Aceptación (CA)

| Condición de Aceptación | Descripción sintética | Requisitos clave | Épica / Spec | Componentes de implementación | Pull Request | Pruebas de verificación |
|---|---|---|:---:|---|:---:|---|
| **CA-01** | El personal autorizado crea y publica actividades; quedan persistidas y aparecen en el catálogo | RF-05, RF-06, RF-07, RF-10 | E3 (`specs/003-gestion-eventos/`) | `app/api/v1/eventos.py`<br>`app/services/evento_service.py`<br>`app/repositories/evento_repo.py`<br>`app/models/evento.py`<br>`app/templates/eventos/` | [#6](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/6), [#19](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/19) | [PF-01](pruebas/PF-01.md)<br>[PF-02](pruebas/PF-02.md)<br>[PF-03](pruebas/PF-03.md)<br>`tests/test_eventos.py` |
| **CA-02** | Los participantes consultan eventos y su disponibilidad, coherente con las inscripciones almacenadas | RF-11, RF-12, RF-13, RN-01 | E4 (`specs/004-catalogo-eventos/`) | `app/api/v1/catalogo.py`<br>`app/services/catalogo_service.py`<br>`app/templates/catalogo/`<br>`app/static/js/catalogo.js` | [#7](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/7), [#19](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/19) | [PF-04](pruebas/PF-04.md)<br>`tests/test_catalogo.py` |
| **CA-03** | Un participante se inscribe; la inscripción queda persistida y es consultable | RF-14, RF-17, RN-06 | E5 (`specs/005-inscripciones-cupos/`) | `app/api/v1/inscripciones.py`<br>`app/services/inscripcion_service.py`<br>`app/repositories/inscripcion_repo.py`<br>`app/models/inscripcion.py`<br>`app/templates/inscripciones/` | [#12](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/12), [#21](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/21), [#22](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/22) | [PF-05](pruebas/PF-05.md)<br>`tests/test_inscripciones.py` |
| **CA-04** | El sistema administra cupos y rechaza inscripciones que excedan el cupo o violen reglas, sin sobrecupo | RF-15, RF-16, RF-18, RNF-04, RN-04, RN-05 | E5 (`specs/005-inscripciones-cupos/`) | `app/repositories/inscripcion_repo.py`<br>`app/services/inscripcion_service.py`<br>`app/api/v1/inscripciones.py`<br>Índice `ux_inscripciones_activa` | [#12](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/12), [#20](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/20), [#21](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/21), [#22](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/22) | [PF-06](pruebas/PF-06.md)<br>[PF-07](pruebas/PF-07.md)<br>[PF-08](pruebas/PF-08.md)<br>`tests/test_inscripciones.py` |
| **CA-05** | El personal autorizado registra asistencia y consulta la lista de participantes (relación evento–inscripción–asistencia) | RF-20, RF-21, RF-22, RF-23, RN-08, RN-10 | E6 (`specs/006-asistencia/`) | `app/api/v1/asistencia.py`<br>`app/services/asistencia_service.py`<br>`app/repositories/asistencia_repo.py`<br>`app/models/asistencia.py`<br>`app/templates/asistencia/` | [#14](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/14), [#20](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/20), [#22](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/22) | [PF-10](pruebas/PF-10.md)<br>`tests/test_asistencia.py` |
| **CA-06** | Coordinación consulta información consolidada de eventos, inscripciones y asistencia | RF-24, RF-25, RF-26, RF-30, RN-10, RN-19 | E7 (`specs/007-consolidado/`) | `app/api/v1/reportes.py`<br>`app/services/reporte_service.py`<br>`app/repositories/reporte_repo.py`<br>`app/templates/reportes/`<br>`app/static/js/reportes.js` | [#15](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/15), [#20](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/20), [#22](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/22) | [PF-11](pruebas/PF-11.md)<br>`tests/test_reportes.py` |

---

## 2. Trazabilidad de Requisitos Funcionales (RF-01 a RF-30)

| Requisito | Descripción | Módulo / Capa API | Capa Service / Repo | Capa Modelo | Verificación |
|---|---|---|---|---|---|
| **RF-01** | Registro público de participantes con documento único | `POST /api/v1/auth/registro` | `auth_service.py`<br>`usuario_repo.py` | `Usuario`<br>`uq_usuarios_documento` | `tests/test_auth.py`<br>Seed inicial |
| **RF-02** | Inicio y cierre de sesión con cookie HttpOnly Secure | `POST /api/v1/auth/login`<br>`POST /api/v1/auth/logout` | `auth_service.py`<br>`security.py` | `Usuario` | `tests/test_auth.py`<br>[PF-09](pruebas/PF-09.md) |
| **RF-03** | Tres roles (`participante`, `organizador`, `coordinacion`) | `app/api/deps.py` (`require_roles`) | `auth_service.py` | `Rol` (enum)<br>`ck_usuarios_rol` | `tests/test_permisos.py`<br>[PF-09](pruebas/PF-09.md) |
| **RF-04** | Creación de personal administrativo mediante seed/script | `scripts/crear_usuario.py`<br>`scripts/seed.py` | `usuario_repo.py` | `Usuario` | `tests/test_scripts_web.py` |
| **RF-05** | Creación de evento en estado `borrador` | `POST /api/v1/eventos` | `evento_service.py`<br>`evento_repo.py` | `Evento`<br>`ck_eventos_cupo` | `tests/test_eventos.py`<br>[PF-01](pruebas/PF-01.md), [PF-02](pruebas/PF-02.md) |
| **RF-06** | Edición de evento propio y ajuste restringido de cupo | `PUT|PATCH /api/v1/eventos/{id}` | `evento_service.py`<br>`evento_repo.py` | `Evento` | `tests/test_eventos.py`<br>[PF-01](pruebas/PF-01.md) |
| **RF-07** | Publicación directa sin flujo de aprobación (RN-20) | `POST /api/v1/eventos/{id}/publicar` | `evento_service.py`<br>`evento_repo.py` | `Evento`<br>`ck_eventos_limite` | `tests/test_eventos.py`<br>[PF-01](pruebas/PF-01.md), [PF-03](pruebas/PF-03.md) |
| **RF-08** | Cancelación de evento con motivo | `POST /api/v1/eventos/{id}/cancelar` | `evento_service.py` | `Evento` | `tests/test_eventos.py` |
| **RF-09** | Estado `finalizado` calculado en tiempo de ejecución | `app/schemas/evento.py`<br>`catalogo_service.py` | `evento_service.py` | `Evento.fecha_fin` | `tests/test_eventos.py`<br>[PF-04](pruebas/PF-04.md) |
| **RF-10** | Organizador consulta sus eventos en cualquier estado | `GET /api/v1/organizador/eventos` | `evento_repo.py` | `Evento` | `tests/test_eventos.py` |
| **RF-11** | Catálogo público con filtros y paginación | `GET /api/v1/catalogo/eventos` | `catalogo_service.py`<br>`evento_repo.py` | `Evento` | `tests/test_catalogo.py`<br>[PF-04](pruebas/PF-04.md) |
| **RF-12** | Detalle de evento con cupo disponible en tiempo real | `GET /api/v1/catalogo/eventos/{id}` | `catalogo_service.py`<br>`inscripcion_repo.py` | `Evento`, `Inscripcion` | `tests/test_catalogo.py`<br>[PF-04](pruebas/PF-04.md) |
| **RF-13** | Respuesta 404 controlada ante evento inexistente | `GET /api/v1/catalogo/eventos/{id}` | `catalogo_service.py` | N/A | `tests/test_catalogo.py`<br>[PF-04](pruebas/PF-04.md) |
| **RF-14** | Inscripción de participante con cupo disponible | `POST /api/v1/eventos/{id}/inscripciones` | `inscripcion_service.py`<br>`inscripcion_repo.py` | `Inscripcion` | `tests/test_inscripciones.py`<br>[PF-05](pruebas/PF-05.md) |
| **RF-15** | Validación de reglas de inscripción (cupo, fechas, rol) | `POST /api/v1/eventos/{id}/inscripciones` | `inscripcion_service.py` | `Inscripcion` | `tests/test_inscripciones.py`<br>[PF-06](pruebas/PF-06.md) |
| **RF-16** | Rechazo atómico de inscripción sin mutación indebida | `POST /api/v1/eventos/{id}/inscripciones` | `inscripcion_repo.py` (`BEGIN IMMEDIATE`) | `ux_inscripciones_activa` | `tests/test_inscripciones.py`<br>[PF-06](pruebas/PF-06.md), [PF-07](pruebas/PF-07.md) |
| **RF-17** | Participante consulta su historial de inscripciones | `GET /api/v1/inscripciones/mias` | `inscripcion_service.py`<br>`inscripcion_repo.py` | `Inscripcion` | `tests/test_inscripciones.py`<br>[PF-05](pruebas/PF-05.md) |
| **RF-18** | Cancelación de inscripción antes del inicio y liberación de cupo | `PATCH /api/v1/inscripciones/{id}/cancelar` | `inscripcion_service.py`<br>`inscripcion_repo.py` | `Inscripcion` | `tests/test_inscripciones.py`<br>[PF-08](pruebas/PF-08.md) |
| **RF-19** | Consulta de inscritos con privacidad diferencial | `GET /api/v1/eventos/{id}/inscripciones` | `inscripcion_service.py` | `Usuario`, `Inscripcion` | `tests/test_inscripciones.py`<br>[PF-10](pruebas/PF-10.md) |
| **RF-20** | Registro de asistencia (`presente`/`ausente`) | `PUT /api/v1/eventos/{id}/inscripciones/{id}/asistencia` | `asistencia_service.py`<br>`asistencia_repo.py` | `Asistencia` | `tests/test_asistencia.py`<br>[PF-10](pruebas/PF-10.md) |
| **RF-21** | Corrección de asistencia (UPSERT) con auditoría | `PUT /api/v1/eventos/{id}/inscripciones/{id}/asistencia` | `asistencia_repo.py` | `Asistencia`<br>`uq_asistencia_inscripcion` | `tests/test_asistencia.py`<br>[PF-10](pruebas/PF-10.md) |
| **RF-22** | Consulta de lista de participantes con asistencia | `GET /api/v1/eventos/{id}/asistencia` | `asistencia_service.py`<br>`asistencia_repo.py` | `Asistencia` | `tests/test_asistencia.py`<br>[PF-10](pruebas/PF-10.md) |
| **RF-23** | Restricción temporal de asistencia (inicio hasta 48 h fin) | `asistencia_service.py` | `app/core/fechas.py` | `Evento`, `Asistencia` | `tests/test_asistencia.py`<br>[PF-10](pruebas/PF-10.md) |
| **RF-24** | Consolidado por evento para coordinación | `GET /api/v1/reportes/consolidado` | `reporte_service.py`<br>`reporte_repo.py` | `Evento`, `Inscripcion`, `Asistencia` | `tests/test_reportes.py`<br>[PF-11](pruebas/PF-11.md) |
| **RF-25** | Filtros avanzados en reporte consolidado | `GET /api/v1/reportes/consolidado` | `reporte_repo.py` | `Evento` | `tests/test_reportes.py`<br>[PF-11](pruebas/PF-11.md) |
| **RF-26** | Coherencia matemática de totales globales | `GET /api/v1/reportes/consolidado` | `reporte_service.py` | Esquema `ConsolidadoTotales` | `tests/test_reportes.py`<br>[PF-11](pruebas/PF-11.md) |
| **RF-27** | Interfaz web segura (Jinja2 + JS Fetch + DOM seguro) | `app/web/*.py`<br>`app/static/js/*.js` | Consumo a `/api/v1` | Plantillas Jinja2 | `tests/test_scripts_web.py`<br>[PF-12](pruebas/PF-12.md) |
| **RF-28** | Documentación interactiva OpenAPI | `/docs` y `/redoc` | FastAPI Schema Generator | `specs/contrato/openapi.json` | `scripts/export_openapi.py --check` |
| **RF-29** | Seed idempotente y reproducible con datos ficticios | `scripts/seed.py` | `usuario_repo.py`<br>`evento_repo.py` | Todos | `tests/test_scripts_web.py` |
| **RF-30** | Exportación del consolidado a CSV con sanitización | `GET /api/v1/reportes/consolidado/csv` | `reporte_service.py` | CSV con BOM y neutralización | `tests/test_reportes.py`<br>[PF-11](pruebas/PF-11.md) |

---

## 3. Trazabilidad de Requisitos No Funcionales (RNF)

| RNF | Descripción y Garantía | Componente / Implementación | Verificación Técnica |
|---|---|---|---|
| **RNF-01** | Arquitectura en 4 capas estrictas sin acoplamiento | `api` → `services` → `repositories` → `models` | Revisión estricta de imports (services no importan FastAPI; routers no escriben SQL). |
| **RNF-02** | Validación en servidor con Pydantic v2 y BD | Schemas Pydantic v2 + SQLite `CHECK` y `UNIQUE` | Pruebas [PF-02](pruebas/PF-02.md), [PF-06](pruebas/PF-06.md) y `pytest`. |
| **RNF-03** | Integridad referencial (`PRAGMA foreign_keys = ON`, `busy_timeout=5000`) | `app/core/database.py` (engine SQLite) | Verificación de migraciones y `PRAGMA foreign_key_check`. |
| **RNF-04** | Concurrencia atómica de cupos sin sobrecupo | `BEGIN IMMEDIATE` + inserción condicional SQL | Prueba de estrés con 20 hilos en [PF-07](pruebas/PF-07.md). |
| **RNF-05** | Seguridad: argon2id, JWT HS256, cookies HttpOnly Secure, CSRF Origin/Referer | `app/core/security.py`, `app/api/deps.py` | Pruebas en `tests/test_auth.py` y `tests/test_permisos.py`. |
| **RNF-06** | Mínimo privilegio por rol y propiedad de recurso | `require_roles`, validación de `organizador_id`/`participante_id` | Pruebas en [PF-09](pruebas/PF-09.md) y `tests/test_permisos.py`. |
| **RNF-07** | Respuestas uniformes de error `{"error": {"codigo", "mensaje", "detalles"}}` | `app/core/errors.py` (manejadores globales) | Validación en todos los endpoints y pruebas de rechazo. |
| **RNF-08** | Códigos HTTP semánticos (200, 201, 204, 400, 401, 403, 404, 409, 422, 429) | Routers y excepciones de dominio | Especificación OpenAPI y suite pytest. |
| **RNF-09** | Documentación técnica completa (`README.md`, `requisitos.md`, `diseno.md`, `trazabilidad.md`, `devops.md`) | `README.md`, `docs/*.md`, `/docs` | Entrega consolidada en E9-A (`#23`) y E9-B (`e9b-trazabilidad`). |
| **RNF-10** | Contenerización Docker con usuario no-root (`appuser` UID 1000) | `Dockerfile`, `docker-compose.yml` | Job `docker` en CI de GitHub Actions. |
| **RNF-11** | Calidad de código: PEP 8, type hints, docstrings y Ruff | `ruff.toml` | `ruff check .` y `ruff format --check .` (0 errores). |
| **RNF-14** | Trazabilidad Git: Conventional Commits en español y ramas por feature | `scripts/check_commits.py` | Job `calidad` en CI validando rango de commits. |
| **RNF-15** | Privacidad de datos personales: documento enmascarado para coordinación | `inscripcion_service.py`, `asistencia_service.py` | Pruebas [PF-10](pruebas/PF-10.md) y logs sin números de documento. |
| **RNF-16** | Fechas normalizadas en UTC en BD y presentación en `America/Bogota` | `app/core/fechas.py` (`UTCDateTime`, `a_bogota`) | Pruebas unitarias en `tests/test_seguridad_fechas_bd.py` y visualización con `Intl`. |
| **RNF-18** | 12 pruebas funcionales obligatorias documentadas con evidencia | `docs/pruebas/PF-01.md`..`PF-12.md`, `evidencias/` | Cobertura PF-01 a PF-12 integrada en `#17`, `#19` y `#22`. |
| **RNF-20** | CI en GitHub Actions con jobs `calidad`, `pruebas` y `docker` | `.github/workflows/ci.yml` | Pipeline 100% en verde en `main` y todos los PRs desde `#16`. |
| **RNF-22** | Contrato OpenAPI versionado y verificado en CI | `scripts/export_openapi.py --check` | `specs/contrato/openapi.json` idéntico a la app. |
| **RNF-23** | Pruebas automatizadas mínimas sobre SQLite temporal | Suite `tests/` (79 pruebas) | Ejecución en CI y local sin afectar BD productiva. |

---

## 4. Registro Completo de Pull Requests del Proyecto

| PR # | Rama | Título / Propósito | Épica | Responsable / Autor | Estado |
|:---:|---|---|:---:|:---:|:---:|
| **[#1](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/1)** | `docs/E0-https` | Regla HTTPS obligatorio en todos los entornos con certificados `mkcert` | E0 | A | **Merged** |
| **[#2](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/2)** | `docs/evidencias-entrevista` | Evidencias visuales de la entrevista con el cliente | E0 / E9-A | A | **Merged** |
| **[#3](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/3)** | `docs/E0-sdd-constitucion` | SDD: constitución v2.0.2, plantillas trazables y `specs/README.md` | E0 | B *(fusionado por A)* | **Merged** |
| **[#4](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/4)** | `001-fundacion` | Fundación, BD SQLite, migraciones, seed, layout y `GET /health` | E1 | A | **Merged** |
| **[#5](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/5)** | `002-autenticacion-roles` | Autenticación segura (argon2id, JWT en cookie HttpOnly Secure), roles y CSRF | E2 | A | **Merged** |
| **[#6](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/6)** | `003-gestion-eventos` | Gestión de eventos académicos (creación, edición, publicación y cancelación) | E3 | A | **Merged** |
| **[#7](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/7)** | `004-catalogo-eventos` | Catálogo público con filtros, paginación y disponibilidad en tiempo real | E4 | A | **Merged** |
| **[#8](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/8)** | `005-inscripciones-cupos` | Spec, plan y tareas SDD de E5 | E5 | A / B | **Merged** |
| **[#9](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/9)** | `006-asistencia` | Spec, plan y tareas SDD de E6 | E6 | A | **Merged** |
| **[#10](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/10)** | `007-consolidado` | Spec, plan y tareas SDD de E7 | E7 | A | **Merged** |
| **[#11](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/11)** | `010-devops-ci-docker` | DevOps: Dockerfile, compose, CI en GitHub Actions, hooks y OpenAPI | E10 | B *(fusionado por A)* | **Merged** |
| **[#12](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/12)** | `005-inscripciones-cupos` | Inscripciones, control atómico de cupos (`BEGIN IMMEDIATE`) y cancelación | E5 | B *(fusionado por A)* | **Merged** |
| **[#13](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/13)** | `docs/reasignacion-e6-e7` | Reasignación de épicas E6 y E7 al Integrante A | Transv. | A | **Merged** |
| **[#14](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/14)** | `006-asistencia` | Registro y consulta de asistencia con ventana de 48 h y privacidad | E6 | A | **Merged** |
| **[#15](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/15)** | `007-consolidado` | Consolidado para coordinación, totales globales y exportación CSV | E7 | A | **Merged** |
| **[#16](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/16)** | `fix/E10-ci-openapi-docker` | Corrección de `PYTHONPATH` en OpenAPI y permisos de certs en Docker | E10 | B (`santyhenao07`) | **Merged** |
| **[#17](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/17)** | `test/E8b-pruebas-inscripcion-asistencia` | Pruebas funcionales PF-05..PF-08, PF-10..PF-12 e índice `docs/pruebas.md` | E8-B | B (`santyhenao07`) | **Merged** |
| **[#18](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/18)** | `docs/E9b-trazabilidad-readme` | Base inicial de matriz de trazabilidad, `docs/devops.md` y README 6–9 | E9-B | B (`santyhenao07`) | **Merged** |
| **[#19](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/19)** | `test/E8a-pruebas-eventos-acceso` | Pruebas funcionales y evidencias PF-01..PF-04 y PF-09 | E8-A | A (`EmanuelChavarria`) | **Merged** |
| **[#20](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/20)** | `fix/visual-consolidado-asistencia-e5` | Estilos responsivos, `crearNodo` con atributos, navegación asistencia y alertas | E5 / E6 / E7 | A (`EmanuelChavarria`) | **Merged** |
| **[#21](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/21)** | `fix/mis-inscripciones-estado-cancelada` | Badges semánticos de estado de evento e inscripción en `/mis-inscripciones` | E5 (UI/UX) | A (`EmanuelChavarria`) | **Merged** |
| **[#22](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/22)** | `test/E8b-evidencias-pf05-pf12` | Evidencias visuales de PF-05..PF-08 y PF-10..PF-12 verificadas | E8-B | B y A | **Merged** |
| **[#23](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/23)** | `docs/E9a-requisitos-diseno` | Requisitos, registro de entrevista, diseño técnico y README 1–5 | E9-A | A (`EmanuelChavarria`) | **Merged** |
| *Pendiente* | `e9b-trazabilidad` | Reasignación y consolidación final de E9-B (trazabilidad completa, errores/ejemplos API, PRs `#1`–`#23` y enlaces de evidencias) | E9-B | A (`EmanuelChavarria`) | **En revisión** |
