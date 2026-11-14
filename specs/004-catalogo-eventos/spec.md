# Especificación de Feature: Catálogo y consulta de eventos

- **Épica:** E4 · **Condiciones:** `CA-02` · **Requisitos:** RF-11, RF-12, RF-13, RF-27, RN-01, RN-12, RN-18, RNF-01, RNF-02, RNF-07, RNF-08, RNF-12, RNF-13
- **Rama de feature:** `004-catalogo-eventos` · **Creada:** 2026-11-14
- **Estado:** aprobada · **Responsable:** Integrante A
- **Entrada:** Descripción del usuario: `"E4 Catalogo y consulta publica de eventos publicados con filtros, paginacion, detalle con cupos disponibles en tiempo real y manejo 404"`

## 1. Objetivo y alcance

Permitir que cualquier visitante (anónimo o autenticado con cualquier rol) consulte el catálogo público paginado de eventos publicados, filtre por tipo, rango de fechas y texto, y acceda al detalle completo de cada actividad con cupo máximo, inscritos activos, cupos disponibles en tiempo real e indicador de inscripciones abiertas, respondiendo `404` controlado ante eventos inexistentes o no publicados.

Incluye dentro del alcance de E4:
- Schemas Pydantic v2 del catálogo (`app/schemas/catalogo.py`): `CatalogoEventoResumen`, `CatalogoEventoDetalle`, `CatalogoPaginadoSalida` (metadatos de paginación e ítems).
- Ampliación de `app/repositories/evento_repo.py` con consulta paginada de eventos `publicado` filtrable (escapando `%` y `_` en `LIKE` con `escape="\\"`) y orden estable (`fecha_inicio ASC`, `id ASC`).
- Servicio de catálogo (`app/services/catalogo_service.py`, sin importar FastAPI) para listar eventos publicados evitando consultas N+1 mediante `inscripcion_repo.contar_activas_por_eventos(db, ids)` y obtener detalle con `inscripcion_repo.contar_activas(db, evento_id)` + cálculo en tiempo real de `cupos_disponibles`, `estado_efectivo` e `inscripciones_abiertas`.
- Endpoints REST públicos (`/api/v1`, servidos sobre HTTPS):
  - `GET /api/v1/catalogo/eventos`
  - `GET /api/v1/catalogo/eventos/{evento_id}`
- Vistas web públicas (`app/web/catalogo.py`, `app/templates/index.html`, `app/templates/catalogo/detalle.html`, `app/templates/catalogo/no_encontrado.html`, `app/static/js/catalogo.js`, `app/static/css/styles.css`):
  - `GET /`: catálogo interactivo con filtros, paginación, fechas en `America/Bogota` y DOM seguro con `textContent`/`crearNodo` (cero `innerHTML`).
  - `GET /eventos/{evento_id}`: detalle con disponibilidad en tiempo real, botón/enlace de inscripción preparado para que E5 lo conecte y página HTML amigable `404` ante evento inexistente o no publicado.
- Pruebas automatizadas en `tests/test_catalogo.py`, actualización de stub `501` en `tests/test_scripts_web.py` y documentación funcional en `docs/pruebas/PF-03.md` y `docs/pruebas/PF-04.md`.

## 2. Fuera de alcance

- Creación, edición, publicación o cancelación de eventos por organizadores (E3, ya completado).
- Registro de inscripción (`POST /api/v1/eventos/{id}/inscripciones`), cancelación de inscripción propia y conexión del botón «Inscribirse» (E5, Integrante B).
- Registro y consulta de asistencia (E6) y consolidado de coordinación (E7).

## 3. Historias de usuario y criterios de aceptación *(obligatorio)*

### Historia de Usuario 1 - Consultar catálogo público paginado con filtros (Prioridad: P1)

Como visitante, quiero consultar el catálogo de eventos publicados filtrando por tipo, rango de fechas y texto con paginación para descubrir actividades académicas de interés.

- **Por qué esta prioridad:** Es el punto de entrada principal del sistema (`/` y `GET /api/v1/catalogo/eventos`) y materializa `RF-11` y `CA-02`.
- **Prueba independiente:** Poblar eventos en estados `borrador`, `publicado` y `cancelado`, consultar `GET /api/v1/catalogo/eventos` con distintas combinaciones de filtros y paginación sin sesión y verificar respuesta `200`, orden por `fecha_inicio ASC`, exclusión de no publicados y conteo exacto de cupos.
- **Escenarios de aceptación:**
  1. **Dado** eventos en estados `borrador`, `publicado` (vigentes y ya finalizados) y `cancelado` en BD, **Cuando** un visitante consulta `GET /api/v1/catalogo/eventos` sin autenticación ni parámetros extra, **Entonces** recibe **200 OK** únicamente con eventos `publicado` aún no finalizados (`fecha_fin >= ahora_utc()`, salvo si se envía `incluir_finalizados=true`), ordenados por `fecha_inicio` ascendente (desempate por `id`), incluyendo `total`, `pagina`, `tamano`, `total_paginas` y para cada evento `inscripciones_activas`, `cupos_disponibles`, `inscripciones_abiertas` y `estado_efectivo`.
  2. **Dado** múltiples eventos publicados de distinto `tipo`, `modalidad`, título/descripción y fechas, **Cuando** se filtra por `tipo`, `modalidad`, `incluir_finalizados`, rango `fecha_desde`/`fecha_hasta` (ISO-8601 con zona) o `texto` (incluidos caracteres `%` o `_`), **Entonces** devuelve únicamente las coincidencias ordenadas y paginadas sin interpretar comodines SQL arbitrarios.
  3. **Dado** filtros inválidos (`pagina < 1`, `tamano < 1` o `> 50`, `tipo` desconocido, fechas sin zona horaria o `fecha_hasta < fecha_desde`), **Cuando** se consulta `GET /api/v1/catalogo/eventos`, **Entonces** retorna **422**.

---

### Historia de Usuario 2 - Ver detalle de evento y cupos disponibles en tiempo real (Prioridad: P1)

Como visitante, quiero ver el detalle completo de un evento publicado con su cupo máximo, inscritos activos, cupos disponibles e indicador de inscripciones abiertas en horario `America/Bogota`.

- **Por qué esta prioridad:** Completa `CA-02` (`RF-12`) y prepara la vista donde el participante podrá inscribirse en E5.
- **Prueba independiente:** Consultar `GET /api/v1/catalogo/eventos/{id}` con inscripciones `activa` y `cancelada` en BD, comprobando que `cupos_disponibles = max(cupo_maximo - activas, 0)` y que `inscripciones_abiertas` refleja estado, límite horario y cupo disponible.
- **Escenarios de aceptación:**
  1. **Dado** un evento `publicado` con `cupo_maximo = 20`, 4 inscripciones `activa` y 2 `cancelada`, **Cuando** un visitante consulta `GET /api/v1/catalogo/eventos/{id}`, **Entonces** recibe **200 OK** con todos los atributos públicos del evento (`titulo`, `descripcion`, `tipo`, `fecha_inicio`, `fecha_fin`, `fecha_limite_inscripcion`, `lugar`, `modalidad`, `publico_objetivo`, `ponente`, `requisitos`, `responsable_nombre`, `cupo_maximo`), `inscripciones_activas = 4`, `cupos_disponibles = 16`, `estado_efectivo` e `inscripciones_abiertas`.
  2. **Dado** que se inserta o cancela una inscripción activa en BD, **Cuando** se vuelve a consultar `GET /api/v1/catalogo/eventos/{id}`, **Entonces** `cupos_disponibles` refleja el cambio en tiempo real.
  3. **Dado** la vista web `/eventos/{id}`, **Cuando** un visitante la abre en el navegador, **Entonces** `catalogo.js` obtiene los datos mediante `fetch` a `/api/v1/catalogo/eventos/{id}`, muestra las fechas en `America/Bogota` y renderiza el DOM con `textContent` sin `innerHTML`.

---

### Historia de Usuario 3 - Manejo controlado `404` ante evento inexistente o no publicado (Prioridad: P1)

Como visitante, si consulto un evento que no existe o no está publicado, quiero recibir un error `404` uniforme en la API y una página amigable en la web sin filtrar información interna.

- **Por qué esta prioridad:** Requisito explícito `RF-13` y prueba funcional `PF-04`.
- **Prueba independiente:** Solicitar por API y web un `evento_id` inexistente, un `borrador` y un `cancelado`, verificando `404 EVENTO_NO_ENCONTRADO` y plantilla HTML amigable.
- **Escenarios de aceptación:**
  1. **Dado** un `evento_id` inexistente o en estado `borrador` / `cancelado`, **Cuando** se envía `GET /api/v1/catalogo/eventos/{evento_id}` (con o sin sesión de cualquier rol), **Entonces** responde **404 Not Found** con `{"error": {"codigo": "EVENTO_NO_ENCONTRADO", "mensaje": "...", "detalles": []}}`.
  2. **Dado** una visita web a `GET /eventos/{evento_id}` para un evento inexistente o no publicado, **Cuando** el navegador carga la ruta, **Entonces** responde HTTP **404 Not Found** renderizando la plantilla amigable `catalogo/no_encontrado.html` con enlace de regreso al catálogo.

---

## 4. Reglas de negocio y validaciones

- **RN-01 (Solo eventos publicados en catálogo):** Ni el listado ni el detalle público exponen eventos en `borrador` o `cancelado` (independientemente del rol que consulte `/api/v1/catalogo/*`); en BD se filtra `estado == 'publicado'` aprovechando el índice `ix_eventos_estado_inicio`. Por defecto el listado público muestra eventos vigentes (`fecha_fin >= ahora_utc()`), salvo `incluir_finalizados=true`; el detalle directo de un `publicado` ya finalizado devuelve `200` con `estado_efectivo == 'finalizado'` e `inscripciones_abiertas == False`.
- **RN-12 y cupo calculado (`CA-02`):** `cupos_disponibles = max(cupo_maximo - inscripciones_activas, 0)` se calcula dinámicamente en lectura vía `inscripcion_repo`; `estado_efectivo` (`publicado` vs `finalizado` si `fecha_fin < ahora_utc()`) e `inscripciones_abiertas` (`estado_efectivo == 'publicado' and fecha_limite_inscripcion > ahora_utc() and cupos_disponibles > 0`) se calculan en UTC.
- **RN-18 (UTC y zona horaria):** Filtros de fecha con zona (`FechaConZona` → `422` si es *naive*), comparación en UTC en SQLite (`UTCDateTime`), respuesta ISO-8601 con zona y renderizado web en `America/Bogota` vía `formatearFechaBogota`.
- **Validaciones de entrada (query params Pydantic / FastAPI):**
  - `pagina`: `int >= 1` (default `1`).
  - `tamano`: `int` con `1 <= tamano <= 50` (default `10`).
  - `tipo`: `TipoEvento | None` (default `None`).
  - `modalidad`: `Modalidad | None` (default `None`).
  - `fecha_desde`: `FechaConZona | None` (default `None`).
  - `fecha_hasta`: `FechaConZona | None` (default `None`; si ambas están presentes y `fecha_hasta < fecha_desde` → `422`).
  - `texto`: `str | None` recortado (`max_length=120`), escapando `%`, `_` y `\` antes de usar `ILIKE`/`LIKE`.
  - `incluir_finalizados`: `bool` (default `False`).
- **Entidades clave afectadas:** Solo lectura sobre `eventos` e `inscripciones` (sin cambios de esquema ni migraciones).

## 5. Errores esperados *(obligatorio)*

Formato uniforme de respuesta: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre | Notas de seguridad |
|---|---|---|---|
| 404 | `EVENTO_NO_ENCONTRADO` | `evento_id` no existe en `eventos` o su estado es `borrador`/`cancelado` | No revelar si el evento existió como borrador o cancelado |
| 422 | `ERROR_VALIDACION` / `REGLA_NEGOCIO` | Parámetros inválidos (`pagina < 1`, `tamano > 50`, `tipo` inválido, fecha sin zona o `fecha_hasta < fecha_desde`) | Manejador global omite `input` en detalles |

## 6. Seguridad, privacidad y zona horaria aplicables

- **Acceso público:** El catálogo y detalle no requieren autenticación ni exponen datos sensibles ni correos personales de inscritos; en el detalle público se muestra `responsable_nombre` y `responsable_correo` institucional de contacto del evento (`RF-05`).
- **Prevención de inyección/comodines en filtros (`RNF-08`):** Consultas parametrizadas SQLAlchemy + escape explícito de `%`, `_` y `\` en búsqueda por texto.
- **Frontend seguro (`RF-27`, `RNF-12`):** Plantillas Jinja2 con autoescape, módulo dedicado `app/static/js/catalogo.js`, formato `America/Bogota` mediante `formatearFechaBogota` y construcción de DOM con `crearNodo`/`textContent` (cero `innerHTML`).

## 7. Casos límite

- Catálogo sin resultados o página fuera de rango (`pagina > total_paginas`): retorna `200` con `items: []`, `total` real y `total_paginas` coherente sin error `500`.
- Búsqueda por texto con `%` o `_` (por ejemplo `"100%"` o `"python_3"`): solo coincide literalmente con esos caracteres y no actúa como comodín SQL.
- Evento con `cupos_disponibles == 0` o `fecha_limite_inscripcion <= ahora_utc()`: sigue apareciendo como publicado según criterio definido en clarificación, pero con `inscripciones_abiertas = False`.

## 8. Supuestos y pendientes

- `[SUPUESTO S-02]` (Confirmado por el cliente): Visitantes consultan catálogo y detalle sin sesión; inscribirse requerirá autenticación como participante en E5.
- `[SUPUESTO S-11]` (Confirmado por el cliente): Horario oficial `America/Bogota` (UTC-5) en UI y UTC en almacenamiento/reglas.
- **Decisiones resueltas en `/speckit.clarify`:**
  - `GET /api/v1/catalogo/eventos` oculta por defecto eventos publicados ya finalizados (`fecha_fin < ahora_utc()`), aceptando `incluir_finalizados: bool = False` (opcional); `GET /api/v1/catalogo/eventos/{id}` sí permite ver un `publicado` ya finalizado con `estado_efectivo: "finalizado"` e `inscripciones_abiertas: false`.
  - `GET /api/v1/catalogo/eventos/{id}` responde siempre **404 `EVENTO_NO_ENCONTRADO`** para eventos en `borrador` o `cancelado` sin importar el rol (la gestión privada usa `GET /api/v1/eventos/{id}` de E3).
  - La vista web `GET /eventos/{evento_id}` verifica si existe el evento publicado y devuelve HTTP **404** con `catalogo/no_encontrado.html` cuando no existe o no está publicado, o `200` con `catalogo/detalle.html` (datos cargados por `fetch`).
  - Filtros habilitados: `tipo`, `modalidad` (opcional), `fecha_desde`, `fecha_hasta`, `texto`, `incluir_finalizados`, `pagina` y `tamano`.
- **Pendientes bloqueantes:** ninguno.

## 9. Criterios de éxito y verificación *(obligatorio)*

- **Criterios medibles:**
  - **SC-001:** `GET /api/v1/catalogo/eventos` devuelve `200` solo con publicados, orden estable, paginación exacta, filtros combinables y conteo agregado sin consultas N+1.
  - **SC-002:** `GET /api/v1/catalogo/eventos/{id}` devuelve `200` con cupos disponibles coherentes en tiempo real ante altas/cancelaciones de inscripciones en BD.
  - **SC-003:** Todo evento inexistente, `borrador` o `cancelado` responde `404 EVENTO_NO_ENCONTRADO` uniforme en API y página amigable en web.
  - **SC-004:** Las vistas `/` y `/eventos/{id}` consumen `/api/v1/catalogo/*` mediante `fetch`, formatean fechas en `America/Bogota` y no usan `innerHTML`.
- **Pruebas funcionales (PF):** **PF-03** (consulta de catálogo y detalle con cupos reales) y **PF-04** (consulta de evento inexistente / no publicado → `404`).
- **Pruebas automatizadas (`pytest`):** `tests/test_catalogo.py` (paginación, orden estable, exclusión de borrador/cancelado, filtros `tipo`/fechas/texto con `%` y `_`, validaciones `422`, detalle y actualización real de cupos tras inscripción/cancelación, `404` uniforme, y vistas `/` y `/eventos/{id}` + ausencia de `innerHTML` en `catalogo.js`).
