# Especificación de Requisitos — Proyecto PF-04

**Proyecto:** Organización de eventos y actividades académicas  
**Asignatura:** Aplicaciones y Servicios Web · Tecnología en Desarrollo de Software  
**Versión:** 1.0 (E9-A · consolidado con aclaraciones del cliente y specs SDD aprobadas)

---

## 1. Método de levantamiento de requisitos

El levantamiento de requisitos se realizó mediante tres actividades complementarias:

1. **Análisis documental de la guía base (PF-04 v001):** extracción inicial de actores, flujo funcional obligatorio, restricciones técnicas, criterios de evaluación y condiciones de aceptación (`CA-01` a `CA-06`).
2. **Entrevista estructurada al cliente/docente (14 preguntas):** validación de ambigüedades operativas sobre público objetivo, ciclo de vida de eventos, duplicidad de inscripciones, cancelación, registro de asistencia, indicadores de consolidado, tecnología de vistas y escala del sistema (ver §6).
3. **Refinamiento bajo Spec-Driven Development (SDD):** formalización de cada épica en `specs/NNN-slug/{spec.md, plan.md, tasks.md}` bajo los principios de [.specify/memory/constitution.md](../.specify/memory/constitution.md) antes de la implementación.

---

## 2. Alcance del sistema y exclusiones

### 2.1 Dentro del alcance
- Registro público de participantes (`participante`) y autenticación segura basada en documento de identidad y contraseña.
- Gestión de eventos académicos (`borrador`, `publicado`, `cancelado`, más estado calculado `finalizado`) exclusiva del organizador propietario.
- Catálogo público paginado y filtrable con consulta de disponibilidad de cupos en tiempo real.
- Inscripción atómica de participantes con control estricto de cupo, prevención de duplicados activos y cancelación anticipada con liberación de cupo.
- Registro y corrección de asistencia dentro de la ventana temporal válida (`fecha_inicio` hasta 48 horas después de `fecha_fin`) y privacidad diferencial del documento.
- Panel consolidado para coordinación con métricas por evento, totales globales coherentes, filtros combinables y exportación opcional a CSV sanitizado.

### 2.2 Fuera del alcance
- Pasarelas de pago o manejo financiero (actividades académicas gratuitas).
- Salas de videoconferencia, notificaciones por SMS/WhatsApp o envío automático de correos SMTP.
- Certificados digitales firmados criptográficamente o lectura presencial por códigos QR.
- Integración con sistemas institucionales externos (SIA/LDAP).
- Lista de espera, flujo de aprobación previo a la publicación de eventos, validación de traslape de horarios y recuperación automática de contraseñas (excluidos por decisión aprobada del equipo).

---

## 3. Condiciones de Aceptación Obligatorias (CA)

| ID | Condición de aceptación | Cobertura principal |
|---|---|---|
| **CA-01** | El personal autorizado crea y publica actividades académicas; quedan persistidas en SQLite y aparecen de inmediato en el catálogo de eventos publicados. | E3 (`003-gestion-eventos`), PF-01, PF-02 |
| **CA-02** | Los visitantes y participantes consultan eventos publicados y su disponibilidad real, coherente con las inscripciones activas almacenadas. | E4 (`004-catalogo-eventos`), PF-03, PF-04 |
| **CA-03** | Un participante autenticado se inscribe en un evento válido; la inscripción queda persistida y es consultable en su historial. | E5 (`005-inscripciones-cupos`), PF-05 |
| **CA-04** | El sistema administra cupos de forma atómica y rechaza inscripciones que excedan el cupo o incumplan reglas aprobadas sin dejar registros parciales ni alterar cupos. | E5 (`005-inscripciones-cupos`), PF-06, PF-07, PF-08 |
| **CA-05** | El organizador propietario registra y corrige asistencia dentro de la ventana habilitada, y los roles autorizados consultan la nómina (relación evento–inscripción–asistencia). | E6 (`006-asistencia`), PF-10 |
| **CA-06** | Coordinación consulta información consolidada de eventos, inscripciones, cancelaciones, asistencia y porcentajes, con totales globales exactos y filtros combinables. | E7 (`007-consolidado`), PF-11 |

---

## 4. Requisitos Funcionales y No Funcionales

Prioridad adoptada (MoSCoW): **M** = Obligatorio (*Must*), **S** = Recomendado (*Should*), **C** = Opcional (*Could*).

### 4.1 Requisitos Funcionales (`RF-01` a `RF-30`)

| ID | Descripción del requisito | Prioridad | CA asociado | Épica |
|---|---|:---:|---|:-:|
| **RF-01** | Registrar participantes (`estudiante` o `docente`) con `tipo_documento` (`CC`, `CE`, `TI`, `PAS`), `numero_documento`, nombre, correo de contacto (no único), tipo de participante y contraseña. | M | CA-03 | E2 |
| **RF-02** | Iniciar y cerrar sesión con documento (`tipo_documento` + `numero_documento`) y contraseña mediante cookie JWT segura. | M | Transversal | E2 |
| **RF-03** | Gestionar tres roles (`participante`, `organizador`, `coordinacion`), validando rol y propiedad en cada endpoint REST y vista web. | M | CA-01 / 05 / 06 | E2 |
| **RF-04** | Crear cuentas de `organizador` y `coordinacion` mediante seed reproducible o script administrativo (`scripts/crear_usuario.py`), sin auto-registro público. | M | CA-01 | E1 / E2 |
| **RF-05** | Crear evento en estado `borrador` con título, descripción, tipo, inicio, fin, lugar, modalidad, fecha límite de inscripción, responsable (nombre y correo) y cupo máximo; opcionales: ponente, requisitos y público objetivo. | M | CA-01 | E3 |
| **RF-06** | Editar evento propio; permitir aumentar el cupo en eventos activos y reducirlo solo hasta la cantidad de inscripciones activas; impedir edición en eventos cancelados o finalizados. | M | CA-01 / CA-04 | E3 |
| **RF-07** | Publicar evento propio (`borrador` → `publicado`) sin flujo de aprobación, verificando datos completos, `fecha_fin > fecha_inicio`, `fecha_limite_inscripcion <= fecha_inicio`, inicio futuro y `cupo_maximo >= 1`. | M | CA-01 | E3 |
| **RF-08** | Cancelar evento propio publicado (`publicado` → `cancelado`) registrando motivo obligatorio. | S | CA-01 | E3 |
| **RF-09** | Calcular en tiempo de ejecución el estado efectivo `finalizado` cuando un evento `publicado` supera su `fecha_fin` en UTC (sin almacenarlo en BD). | S | CA-06 | E3 |
| **RF-10** | Permitir al organizador listar y consultar sus propios eventos en cualquier estado (`borrador`, `publicado`, `finalizado`, `cancelado`). | M | CA-01 | E3 |
| **RF-11** | Exponer catálogo público de eventos publicados con filtros combinables (texto, tipo, modalidad, rango de fechas e inclusión de finalizados) y paginación. | M | CA-02 | E4 |
| **RF-12** | Consultar detalle público de un evento con cupo máximo, inscritos activos y cupos disponibles calculados dinámicamente desde la BD. | M | CA-02 | E4 |
| **RF-13** | Responder HTTP `404` controlado (`EVENTO_NO_ENCONTRADO`) en API y vista amigable ante eventos inexistentes o no publicados para visitantes. | M | CA-02 | E4 |
| **RF-14** | Permitir a un participante autenticado inscribirse en un evento publicado que cumpla todas las condiciones. | M | CA-03 | E5 |
| **RF-15** | Validar todas las reglas de inscripción en el servidor: rol participante, evento publicado, plazo vigente (`ahora < fecha_limite_inscripcion`), cupo disponible, ausencia de inscripción activa previa y compatibilidad de `publico_objetivo`. | M | CA-04 | E5 |
| **RF-16** | Garantizar rechazo atómico: ninguna inscripción rechazada deja registros parciales ni modifica el conteo de cupos, incluso bajo solicitudes concurrentes. | M | CA-04 | E5 |
| **RF-17** | Permitir al participante consultar su historial cronológico de inscripciones (activas y canceladas). | M | CA-03 | E5 |
| **RF-18** | Permitir al participante cancelar su inscripción activa hasta antes de `fecha_inicio`, liberando el cupo (reutilizable si sigue abierta la inscripción) y conservando historial. | S | CA-04 | E5 |
| **RF-19** | Permitir al organizador propietario consultar inscritos de sus eventos con documento completo, y a coordinación en solo lectura con documento enmascarado. | M | CA-05 | E5 |
| **RF-20** | Registrar asistencia (`presente` / `ausente`) sobre inscripciones activas de un evento propio. | M | CA-05 | E6 |
| **RF-21** | Corregir un registro de asistencia existente dentro de la ventana temporal, actualizando el usuario responsable (`registrado_por_id`) y marca temporal (`actualizado_en`). | S | CA-05 | E6 |
| **RF-22** | Consultar la nómina de participantes con su estado de asistencia diferenciando visibilidad de documento entre organizador y coordinación. | M | CA-05 | E6 |
| **RF-23** | Restringir el registro y corrección de asistencia estrictamente al intervalo `[fecha_inicio, fecha_fin + 48h]` en UTC y únicamente para inscripciones activas. | M | CA-05 | E6 |
| **RF-24** | Generar reporte consolidado por evento para coordinación con cupo, inscritos activos, disponibles, ocupación %, cancelaciones, presentes, ausentes, sin registrar, asistencia % y estado efectivo. | M | CA-06 | E7 |
| **RF-25** | Filtrar el reporte consolidado por rango de fechas, tipo, modalidad, estado efectivo, organizador y búsqueda textual segura. | S | CA-06 | E7 |
| **RF-26** | Garantizar coherencia aritmética exacta entre los totales globales del consolidado y la suma de las filas filtradas, evitando división por cero. | M | CA-06 | E7 |
| **RF-27** | Proveer interfaz web en español con Jinja2 como esqueleto HTML y módulos JS que consumen `/api/v1` mediante `fetch`. | M | CA-01..06 | E1–E7 |
| **RF-28** | Publicar documentación OpenAPI interactiva en `/docs` y `/redoc` con contrato versionado en `specs/contrato/openapi.json`. | M | Documentación | Todas |
| **RF-29** | Proveer script idempotente (`scripts/seed.py`) con datos ficticios reproducibles para pruebas y demostraciones. | M | Pruebas | E1 |
| **RF-30** | Permitir a coordinación exportar el reporte consolidado filtrado a archivo CSV con neutralización de fórmulas peligrosas y protección de documentos. | C | CA-06 | E7 |

### 4.2 Requisitos No Funcionales (`RNF-01` a `RNF-23`)

| ID | Descripción del requisito | Mecanismo de verificación |
|---|---|---|
| **RNF-01** | Arquitectura en 4 capas estrictas: `api/v1` → `services` → `repositories` → `models` (routers sin reglas ni SQL; services sin importar FastAPI). | Revisión de código y pruebas de arquitectura |
| **RNF-02** | Validación estricta en servidor mediante Pydantic v2 (`extra="forbid"`) respaldada por restricciones de esquema en BD. | `tests/`, PF-02, PF-06 |
| **RNF-03** | Integridad referencial y de dominio: PK/FK (`PRAGMA foreign_keys=ON`, `busy_timeout=5000`), `UNIQUE`, `CHECK`, índice parcial `ux_inscripciones_activa` y escape en `LIKE`. | Migración Alembic inicial + `pytest` |
| **RNF-04** | Control de concurrencia sin sobrecupo mediante transacción `BEGIN IMMEDIATE`, `INSERT ... SELECT` condicional verificando `rowcount` e índice único parcial. | Prueba multihilo en `tests/test_inscripciones.py` y PF-07 |
| **RNF-05** | Seguridad integral: contraseñas con **argon2id**, verificación en tiempo constante, rate limit de 10 intentos fallidos (`429`), JWT `HS256` (`sub=id`), cookie `HttpOnly` + `SameSite=Lax` + `Secure`, HTTPS en todos los entornos, defensa CSRF por `Origin`/`Referer` y secretos solo en `.env`. | `tests/test_auth.py`, `tests/test_permisos.py` |
| **RNF-06** | Autorización de mínimo privilegio por rol y propietario de recurso (prevención de IDOR). | PF-09 y `tests/test_permisos.py` |
| **RNF-07** | Respuestas de error uniformes `{"error": {"codigo", "mensaje", "detalles"}}`, omitiendo `input` en errores 422 y sin trazas ni datos sensibles. | Manejadores globales en `app/core/errors.py` |
| **RNF-08** | Uso semántico correcto de códigos HTTP (`200`, `201`, `204`, `400`, `401`, `403`, `404`, `409`, `422`, `429`). | Contrato OpenAPI y suite `pytest` |
| **RNF-09** | Documentación técnica completa (`README.md`, `docs/requisitos.md`, `docs/diseno.md`, `docs/trazabilidad.md`, `docs/devops.md`, `/docs`). | Revisión documental (E9) |
| **RNF-10** | Reproducibilidad con y sin Docker, con dependencias fijadas en `requirements*.txt` y migraciones Alembic. | Instalación limpia y CI Docker |
| **RNF-11** | Mantenibilidad: PEP 8, type hints, docstrings, nombres de dominio en español/`snake_case`, validación con `ruff check` y `ruff format`. | Job `calidad` en CI |
| **RNF-12** | Usabilidad y accesibilidad básica: interfaz en español, etiquetas asociadas, alertas claras y diseño adaptable básico. | Validación manual en PF-01..PF-12 |
| **RNF-13** | Rendimiento: catálogo paginado, consulta única agregada con `GROUP BY` para consolidado e índices en columnas de filtro/FK. | Inspección de queries y repositorios |
| **RNF-14** | Trazabilidad Git: ramas por épica, Conventional Commits en español validados por hook y CI, Pull Requests revisados. | `scripts/check_commits.py` |
| **RNF-15** | Privacidad: datos exclusivamente ficticios en repo/seed, documento enmascarado (`••••1234`) para coordinación y excluido de logs/errores. | Revisión de logs y pruebas E6/E7 |
| **RNF-16** | Manejo consistente de tiempo: almacenamiento UTC (`UTCDateTime`), API ISO-8601 con zona (`-05:00`), rechazo 422 a fechas *naive* y presentación en `America/Bogota` (`Intl`). | `tests/` y `app/core/fechas.py` |
| **RNF-17** | Portabilidad entre Windows, macOS y Linux con Python 3.11+. | Scripts `.ps1` y `.sh`, `README.md` |
| **RNF-18** | Ejecución y documentación obligatoria de las 12 pruebas funcionales (`PF-01`..`PF-12`) con evidencias. | `docs/pruebas/` y `evidencias/` |
| **RNF-19** | Metodología SDD estricta: ninguna épica se codifica sin `spec.md`, `plan.md` y `tasks.md` aprobados. | Directorio `specs/` |
| **RNF-20** | Integración continua automatizada en GitHub Actions (`calidad`, `pruebas`, `docker`) sobre ramas protegidas. | `.github/workflows/ci.yml` |
| **RNF-21** | Contenerización reproducible con usuario sin privilegios (`appuser` UID 1000), volumen nombrado para SQLite y healthcheck TLS. | `Dockerfile`, `docker-compose.yml` |
| **RNF-22** | Endpoint `GET /health` y logging estructurado de solicitudes HTTP sin cuerpos ni cabeceras sensibles. | `app/core/logging.py`, `app/main.py` |
| **RNF-23** | Suite automatizada `pytest` ejecutable sobre bases SQLite temporales aisladas. | `tests/conftest.py` y job `pruebas` |

---

## 5. Reglas de Negocio (`RN-01` a `RN-21`)

| ID | Regla de negocio |
|---|---|
| **RN-01** | Solo los eventos en estado almacenado `publicado` son visibles en el catálogo público. |
| **RN-02** | `cupo_maximo` debe ser un entero `>= 1`. |
| **RN-03** | Siempre debe cumplirse `fecha_fin > fecha_inicio` y `fecha_limite_inscripcion <= fecha_inicio`; además, al publicar, `fecha_inicio` debe ser futura en UTC. |
| **RN-04** | Un participante solo puede tener una inscripción `activa` simultánea por evento (duplicado → `409 INSCRIPCION_DUPLICADA`). |
| **RN-05** | No se admiten inscripciones cuando `inscripciones_activas >= cupo_maximo` (`409 CUPO_AGOTADO`); no hay sobrecupo ni lista de espera. |
| **RN-06** | Solo se acepta inscripción si el evento está `publicado`, `ahora < fecha_limite_inscripcion`, hay cupo disponible y el `tipo_participante` coincide con `publico_objetivo`. |
| **RN-07** | Un participante puede cancelar su inscripción activa hasta antes de `fecha_inicio`; la inscripción pasa a `cancelada`, conserva historial y libera el cupo. |
| **RN-08** | La asistencia solo se registra sobre inscripciones `activa`s dentro del rango `[fecha_inicio, fecha_fin + 48h]` en UTC. |
| **RN-09** | El organizador puede aumentar `cupo_maximo` siempre, pero solo puede reducirlo hasta igualar las inscripciones activas; eventos `cancelado` o `finalizado` no permiten editar cupo. |
| **RN-10** | Un organizador solo gestiona sus propios eventos; coordinación tiene acceso exclusivamente de lectura global; un participante solo opera sobre sus propias inscripciones. |
| **RN-11** | Cancelar un evento publicado exige motivo, conserva las inscripciones históricas y bloquea nuevas inscripciones y registros de asistencia. |
| **RN-12** | El estado guardado sigue el flujo unidireccional `borrador → publicado → cancelado` (también `borrador → cancelado`); `finalizado` e «inscripciones cerradas» se calculan dinámicamente. |
| **RN-13** | Identificación única por `(tipo_documento, numero_documento)` (`409 DOCUMENTO_DUPLICADO`). El correo electrónico es obligatorio como contacto y no es único. |
| **RN-14** | Formato estricto de documento sin espacios ni puntos: `CC`/`CE`/`TI` solo dígitos (5–12); `PAS` alfanumérico en mayúsculas (5–15). |
| **RN-15** | El cierre ordinario de inscripciones ocurre al alcanzarse `fecha_limite_inscripcion` (`<= fecha_inicio`). |
| **RN-16** | Tras cancelar una inscripción, el participante puede reinscribirse si cumple todas las reglas vigentes; la reinscripción crea una fila nueva conservando la `cancelada`. |
| **RN-17** | Las correcciones de asistencia solo proceden dentro de la ventana de 48 h y actualizan quién corrigió y la fecha/hora de actualización. |
| **RN-18** | Todas las fechas se almacenan en UTC, se validan con zona horaria en la API, se comparan en UTC y se presentan en `America/Bogota`. |
| **RN-19** | Privacidad de documento: completo para el organizador propietario, enmascarado (`••••1234`) para coordinación, omitido en logs/errores y neutralización CSV (`=`, `+`, `-`, `@`, tabuladores) en exportaciones. |
| **RN-20** | No existe lista de espera ni flujo de aprobación administrativa previa para publicar eventos. |
| **RN-21** | El registro web público únicamente crea cuentas con rol `participante`; organizadores y coordinación se aprovisionan mediante seed/script administrativo. |

---

## 6. Resumen de Historias de Usuario por Épica

Cada épica cuenta con sus historias y criterios detallados en `specs/`:

- **E0 (`docs/E0-sdd-constitucion`):** Cimientos SDD, constitución v2.0.2 y plantillas trazables (`HU-E0-01`..`03`).
- **E1 (`specs/001-fundacion/`):** Configuración segura, BD SQLite con WAL/FK, modelo relacional inicial, migraciones, errores uniformes y seed (`HU-E1-01`..`04`).
- **E2 (`specs/002-autenticacion-roles/`):** Registro de participantes con documento único, login/logout con JWT en cookie `HttpOnly Secure`, protección CSRF y control por rol (`HU-E2-01`..`04`).
- **E3 (`specs/003-gestion-eventos/`):** Creación en borrador, edición, publicación directa, cancelación con motivo y listado de eventos propios (`HU-E3-01`..`05`).
- **E4 (`specs/004-catalogo-eventos/`):** Catálogo público paginado con filtros, cálculo dinámico de disponibilidad y página `404` amigable (`HU-E4-01`..`03`).
- **E5 (`specs/005-inscripciones-cupos/`):** Inscripción atómica con `BEGIN IMMEDIATE`, prevención de duplicados, historial, cancelación con liberación de cupo y consulta de inscritos (`HU-E5-01`..`05`).
- **E6 (`specs/006-asistencia/`):** Registro y corrección idempotente de asistencia dentro de ventana de 48 h y privacidad diferencial por rol (`HU-E6-01`..`04`).
- **E7 (`specs/007-consolidado/`):** Panel consolidado para coordinación con métricas, totales exactos, filtros combinables y exportación CSV sanitizada (`HU-E7-01`..`04`).
- **E10 (`specs/010-devops-ci-docker/`):** Contenerización Docker, scripts HTTPS, pipeline CI y verificación automática del contrato OpenAPI.
