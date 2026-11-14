# Especificación de Feature: Gestión de eventos

- **Épica:** E3 · **Condiciones:** `CA-01`, `CA-04` (cupo mínimo al editar) · **Requisitos:** RF-05, RF-06, RF-07, RF-08, RF-09, RF-10, RF-27, RN-01, RN-02, RN-03, RN-09, RN-10, RN-12, RN-18, RN-20, RNF-01, RNF-02, RNF-03, RNF-05 (CSRF), RNF-06, RNF-07, RNF-08, RNF-12, RNF-16
- **Rama de feature:** `003-gestion-eventos` · **Creada:** 2026-11-14
- **Estado:** aprobada · **Responsable:** Integrante A
- **Entrada:** Descripción del usuario: `"E3 Gestion de eventos: crear en borrador, editar con control de cupo minimo, publicar sin aprobacion, cancelar con motivo, estado calculado finalizado, listado de organizador, propiedad por organizador y vistas web de gestion"`

## 1. Objetivo y alcance

Permitir que el usuario con rol `organizador` cree actividades académicas en estado `borrador`, las edite respetando la ocupación actual, las publique directamente sin aprobación previa, las cancele indicando un motivo y consulte todos sus eventos propios con estado efectivo y ocupación real, garantizando autorización estricta por rol y por propietario (`RN-10`) tanto en API (`/api/v1`) como en la interfaz web.

Incluye dentro del alcance de E3:
- Schemas Pydantic v2 de evento (`EventoCrear`, `EventoActualizar`, `EventoCancelar`, `EventoSalida`) con validación de fechas ISO-8601 con zona (`FechaConZona`), rangos y longitudes (`app/schemas/evento.py`).
- Repositorio de eventos (`app/repositories/evento_repo.py`) para creación, obtención por ID, listado por organizador con orden estable y actualización.
- Servicio de eventos (`app/services/evento_service.py`) sin importar FastAPI, encapsulando `RN-02`, `RN-03`, `RN-09`, `RN-10`, `RN-12`, `RN-18`, `RN-20` y cálculo de `finalizado` e `inscripciones_abiertas` + `cupos_disponibles` mediante `inscripcion_repo.contar_activas` / `contar_activas_por_eventos`.
- Endpoints REST (`/api/v1`, servidos siempre sobre HTTPS):
  - `POST /api/v1/eventos` (crear borrador)
  - `GET /api/v1/eventos/{evento_id}` (lectura de evento propio para gestión/edición)
  - `PATCH /api/v1/eventos/{evento_id}` (editar evento propio)
  - `POST /api/v1/eventos/{evento_id}/publicar` (publicar sin aprobación)
  - `POST /api/v1/eventos/{evento_id}/cancelar` (cancelar con motivo)
  - `GET /api/v1/organizador/eventos` (listar todos los eventos propios del organizador)
- Vistas web (`app/web/eventos.py`, `app/templates/eventos/*.html`, `app/static/js/eventos.js`): «Mis eventos» (`/organizador/eventos`), creación (`/organizador/eventos/nuevo`) y edición (`/organizador/eventos/{evento_id}/editar`), protegidas por `require_web_roles(Rol.ORGANIZADOR)` y consumiendo `/api/v1` mediante `fetch` y `textContent`.
- Pruebas automatizadas en `tests/test_eventos.py` y ampliación de `tests/test_permisos.py` (propiedad por organizador `RN-10`), más ampliación de `docs/pruebas/PF-09.md` y documentación `PF-01`, `PF-02`.

## 2. Fuera de alcance

- Catálogo público paginado con filtros de búsqueda (`GET /api/v1/catalogo/eventos`) y detalle público (E4).
- Inscripción de participantes, cancelación de inscripción y control atómico de concurrencia al inscribirse (E5).
- Flujo de aprobación previa de eventos por coordinación o terceros (`RN-20`: prohibido por acuerdo).
- Lista de espera (`RN-20`).
- Registro y consulta de asistencia (E6) y consolidado global de coordinación (E7).

## 3. Historias de usuario y criterios de aceptación *(obligatorio)*

### Historia de Usuario 1 - Crear evento en borrador (Prioridad: P1)

Como organizador, quiero crear un evento en estado `borrador` con sus datos completos, fechas con zona horaria, responsable y cupo máximo para prepararlo antes de publicarlo.

- **Por qué esta prioridad:** Da inicio al flujo `CA-01` y fija la propiedad (`organizador_id = usuario.id`) desde la creación.
- **Prueba independiente:** Invocar `POST /api/v1/eventos` autenticado como organizador con datos válidos e inválidos sobre BD temporal y verificar código HTTP, respuesta y persistencia.
- **Escenarios de aceptación:**
  1. **Dado** un organizador autenticado con cabecera CSRF válida, **Cuando** envía `POST /api/v1/eventos` con `titulo`, `descripcion`, `tipo`, `fecha_inicio`, `fecha_fin`, `fecha_limite_inscripcion` (ISO-8601 con zona `-05:00` o UTC), `lugar`, `modalidad`, `responsable_nombre`, `responsable_correo`, `cupo_maximo >= 1` y opcionales (`publico_objetivo`, `ponente`, `requisitos`), **Entonces** retorna **201 Created** con `estado="borrador"`, `organizador_id=usuario.id`, `inscripciones_activas=0`, `cupos_disponibles=cupo_maximo`, persiste fechas en UTC en la tabla `eventos` y el evento no aparece aún en el catálogo público.
  2. **Dado** datos inválidos (título vacío, `cupo_maximo < 1`, fecha sin zona horaria, `fecha_fin <= fecha_inicio`, `fecha_limite_inscripcion > fecha_inicio`, correo inválido o campos extra), **Cuando** envía `POST /api/v1/eventos`, **Entonces** retorna **422** sin persistir ningún registro en BD.
  3. **Dado** una petición sin sesión o con rol `participante`/`coordinacion`, **Cuando** envía `POST /api/v1/eventos`, **Entonces** retorna **401** o **403 `SIN_PERMISO`** respectivamente.

---

### Historia de Usuario 2 - Publicar evento propio sin aprobación previa (Prioridad: P1)

Como organizador propietario, quiero publicar mi evento desde `borrador` sin flujo de aprobación previo para habilitarlo en el catálogo cuando cumpla las condiciones obligatorias.

- **Por qué esta prioridad:** Completa el criterio `CA-01` («publica actividades; quedan persistidas y aparecen en el catálogo de publicados»).
- **Prueba independiente:** Publicar un evento propio en `borrador` con inicio futuro y verificar cambio a `publicado`, rechazo a otro organizador (`403`) y rechazo si ya estaba `publicado` (`409`) o con fecha pasada.
- **Escenarios de aceptación:**
  1. **Dado** un evento en estado `borrador` cuyo propietario es el organizador autenticado, con datos completos, `cupo_maximo >= 1`, `fecha_fin > fecha_inicio`, `fecha_limite_inscripcion <= fecha_inicio` y `fecha_inicio > ahora_utc()`, **Cuando** envía `POST /api/v1/eventos/{id}/publicar`, **Entonces** retorna **200 OK** con `estado="publicado"` y el evento queda visible para el catálogo (`RN-01`).
  2. **Dado** un evento cuyo propietario es otro organizador, **Cuando** un organizador distinto intenta publicarlo, **Entonces** retorna **403 `SIN_PERMISO`** sin cambiar el estado.
  3. **Dado** un evento que no existe, **Cuando** se intenta publicar, **Entonces** retorna **404 `EVENTO_NO_ENCONTRADO`**.
  4. **Dado** un evento cuyo estado ya es `publicado` o `cancelado`, **Cuando** se intenta publicar, **Entonces** retorna **409** sin alterar su estado.
  5. **Dado** un evento en `borrador` cuya `fecha_inicio <= ahora_utc()` (inicio no futuro), **Cuando** se intenta publicar, **Entonces** permanece en `borrador` y retorna **422 `REGLA_NEGOCIO`**.

---

### Historia de Usuario 3 - Editar evento propio respetando cupo mínimo y estado (Prioridad: P1)

Como organizador propietario, quiero editar los datos y el cupo de mi evento en `borrador` o `publicado` sin poder bajar el cupo por debajo de los inscritos activos ni modificar eventos cancelados o finalizados.

- **Por qué esta prioridad:** Garantiza consistencia de datos y la regla crítica `RN-09` antes de abrir inscripciones concurrentes (E5).
- **Prueba independiente:** Editar eventos en `borrador`, `publicado` (con inscripciones activas), `cancelado`, `finalizado` (por fecha `fecha_fin < ahora_utc()`) y de otro organizador.
- **Escenarios de aceptación:**
  1. **Dado** un evento propio en `borrador` o `publicado` aún no finalizado con 3 inscripciones activas, **Cuando** su organizador envía `PATCH /api/v1/eventos/{id}` subiendo `cupo_maximo` a 20 o bajándolo a 3 (igual a activas), o ajustando campos válidos cumpliendo `RN-02`/`RN-03`, **Entonces** retorna **200 OK** y persiste los cambios manteniendo `inscripciones_activas=3` y `cupos_disponibles` recalculado.
  2. **Dado** un evento propio con 3 inscripciones activas, **Cuando** el organizador intenta bajar `cupo_maximo` a 2 (`< 3`), **Entonces** retorna **409** sin modificar el cupo en BD.
  3. **Dado** un evento en estado `cancelado` o ya finalizado (`fecha_fin < ahora_utc()`), **Cuando** su organizador intenta editar cualquier campo (incluido `cupo_maximo`), **Entonces** retorna **409** sin persistir cambios.
  4. **Dado** un evento perteneciente a otro organizador, **Cuando** otro organizador envía `PATCH /api/v1/eventos/{id}`, **Entonces** retorna **403 `SIN_PERMISO`**.

---

### Historia de Usuario 4 - Cancelar evento publicado indicando motivo (Prioridad: P2)

Como organizador propietario, quiero cancelar un evento publicado indicando el motivo para detener nuevas inscripciones conservando las ya registradas.

- **Por qué esta prioridad:** Permite reaccionar ante imprevistos (`RF-08`, `RN-11`, `RN-12`) sin destruir historial de inscripciones.
- **Prueba independiente:** Cancelar un evento publicado con inscripciones activas y verificar que pasa a `cancelado`, guarda `motivo_cancelacion`, conserva las inscripciones en BD y bloquea nuevas ediciones o re-cancelación.
- **Escenarios de aceptación:**
  1. **Dado** un evento propio en estado `publicado` no finalizado (con o sin inscripciones), **Cuando** el organizador envía `POST /api/v1/eventos/{id}/cancelar` con `motivo` de al menos 5 caracteres recortados, **Entonces** retorna **200 OK** con `estado="cancelado"`, `estado_efectivo="cancelado"` y `motivo_cancelacion` guardado, conservando intactas todas las filas existentes en `inscripciones`.
  2. **Dado** un evento en estado `borrador`, `cancelado` o `finalizado`, **Cuando** se envía `POST /api/v1/eventos/{id}/cancelar`, **Entonces** retorna **409** sin alterar datos.
  3. **Dado** una solicitud de cancelación sin `motivo` o con `motivo` menor a 5 caracteres recortados, **Cuando** se envía `POST /api/v1/eventos/{id}/cancelar`, **Entonces** retorna **422**.
  4. **Dado** un organizador distinto al propietario, **Cuando** intenta cancelar el evento, **Entonces** retorna **403 `SIN_PERMISO`**.

---

### Historia de Usuario 5 - Consultar eventos propios y cálculo de estado `finalizado` (Prioridad: P1)

Como organizador, quiero ver en la API (`GET /api/v1/organizador/eventos`) y en la vista web `/organizador/eventos` todos mis eventos (borradores, publicados, cancelados y finalizados) con su estado efectivo y ocupación actual.

- **Por qué esta prioridad:** Permite gestionar todo el ciclo de vida (`RF-09`, `RF-10`) desde la interfaz y verificar `CA-01` en pruebas funcionales.
- **Prueba independiente:** Consultar `GET /api/v1/organizador/eventos` autenticado con dos organizadores distintos teniendo eventos en distintos estados y fechas pasadas, comprobando aislamiento estricto y cálculo dinámico de `finalizado` y cupos en una sola consulta agregada.
- **Escenarios de aceptación:**
  1. **Dado** que el organizador A tiene eventos en `borrador`, `publicado` futuro, `publicado` con `fecha_fin < ahora_utc()` y `cancelado`, y el organizador B tiene otro evento, **Cuando** el organizador A consulta `GET /api/v1/organizador/eventos`, **Entonces** retorna **200 OK** únicamente con los eventos del organizador A; el evento publicado cuya `fecha_fin` ya pasó conserva `estado="publicado"` en BD pero expone estado calculado `finalizado` (`RF-09`), junto con `inscripciones_activas` y `cupos_disponibles`.
  2. **Dado** un usuario con rol `participante` o `coordinacion`, **Cuando** consulta `GET /api/v1/organizador/eventos`, **Entonces** retorna **403 `SIN_PERMISO`**.
  3. **Dado** un organizador en el navegador abriendo `/organizador/eventos`, `/organizador/eventos/nuevo` o `/organizador/eventos/{id}/editar`, **Cuando** carga y opera las vistas, **Entonces** los datos se consultan/envían por `fetch` hacia `/api/v1` mostrando fechas en `America/Bogota`, utilizando `textContent` sin `innerHTML`; un visitante sin sesión es redirigido `303` a `/login` y otro rol recibe `403`.

---

## 4. Reglas de negocio y validaciones

- **RN-02 (`cupo_maximo >= 1`):** Entero positivo validado en Pydantic y en BD (`ck_eventos_cupo`).
- **RN-03 (Coherencia de fechas):** `fecha_fin > fecha_inicio` y `fecha_limite_inscripcion <= fecha_inicio`; al publicar (`POST /publicar`), además `fecha_inicio > ahora_utc()`. Validado en Pydantic, servicio y BD (`ck_eventos_fechas`, `ck_eventos_limite`).
- **RN-09 (Edición de cupo y bloqueo de edición en cancelados/finalizados):** `cupo_maximo` puede aumentar siempre, puede bajar solo hasta `>= inscripciones_activas`, y no se edita ningún campo cuando el evento está `cancelado` o finalizado (`fecha_fin < ahora_utc()`).
- **RN-10 (Propiedad estricta):** Solo el organizador dueño (`evento.organizador_id == usuario.id`) puede leer detalle de gestión, editar, publicar o cancelar su evento; otro organizador recibe **403 `SIN_PERMISO`**.
- **RN-12 (Máquina de estados sin retrocesos):** Guardados en BD: `borrador → publicado → cancelado`. Sin transición `cancelado → publicado`, `publicado → borrador`, ni `cancelado → borrador`. `finalizado` y `inscripciones_abiertas` se calculan dinámicamente en lectura con `ahora_utc()`.
- **RN-18 (UTC y zona horaria):** Toda fecha de entrada exige zona horaria (`FechaConZona` → 422 si es *naive*); se almacena en UTC vía `UTCDateTime`; comparaciones de reglas en UTC; API devuelve ISO-8601 con zona y frontend muestra en `America/Bogota` mediante `formatearFechaBogota` / `aIsoBogota`.
- **RN-20 (Sin aprobación ni lista de espera):** Publicación directa por el organizador sin intermediarios.
- **Validaciones de entrada (Pydantic v2, `extra="forbid"`):**
  - `EventoCrear`: `titulo` (3–200 chars recortado), `descripcion` (10–4000 chars recortado), `tipo` (`TipoEvento`), `fecha_inicio` (`FechaConZona`), `fecha_fin` (`FechaConZona`), `fecha_limite_inscripcion` (`FechaConZona`), `lugar` (2–200 chars recortado), `modalidad` (`Modalidad`), `publico_objetivo` (`PublicoObjetivo`, default `todos`), `ponente` (opcional, máx. 150), `requisitos` (opcional, máx. 2000), `responsable_nombre` (2–120 chars), `responsable_correo` (`EmailStr`, máx. 150), `cupo_maximo` (`int >= 1`).
  - `EventoActualizar` (`extra="forbid"`): todos los campos de `EventoCrear` opcionales (al menos un campo enviado o sin cambios permitidos manteniendo consistencia combinada con el estado existente en BD para validar `fecha_fin > fecha_inicio` y `fecha_limite_inscripcion <= fecha_inicio` sobre el resultado final).
  - `EventoCancelar` (`extra="forbid"`): `motivo` (`str` recortado, longitud 5–1000 caracteres).
  - `EventoSalida`: incluye todos los atributos del evento (`id`, `titulo`, `descripcion`, `tipo`, `fecha_inicio`, `fecha_fin`, `fecha_limite_inscripcion`, `lugar`, `modalidad`, `publico_objetivo`, `ponente`, `requisitos`, `responsable_nombre`, `responsable_correo`, `cupo_maximo`, `estado`, `motivo_cancelacion`, `organizador_id`, `creado_en`, `actualizado_en`) más campos calculados **`estado_efectivo`** (`borrador`/`publicado`/`cancelado`/`finalizado`), **`inscripciones_abiertas`** (`bool`), **`inscripciones_activas`** (`int`) y **`cupos_disponibles`** (`int`).
- **Entidades clave afectadas:** Tabla existente `eventos` (sin cambios de esquema ni nuevas migraciones en E3); lectura agregada sobre `inscripciones` vía `inscripcion_repo`.

## 5. Errores esperados *(obligatorio)*

Formato uniforme de respuesta: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre | Notas de seguridad |
|---|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | Solicitud sin sesión activa o cookie inválida/expirada | Sin detalles de sesión |
| 403 | `SIN_PERMISO` | Rol distinto de `organizador`, organizador distinto al propietario (`RN-10`) o fallo CSRF en mutación con cookie | Sin filtrar datos del evento ajeno |
| 404 | `EVENTO_NO_ENCONTRADO` | `evento_id` inexistente en `eventos` | Se verifica existencia antes o de forma consistente con propietario (ver clarificación) |
| 409 | Conflicto de negocio / estado | Publicar evento no `borrador`; bajar cupo `< inscripciones_activas`; editar o cancelar evento `cancelado`/`finalizado` | Operación atómica sin persistencia parcial |
| 422 | `ERROR_VALIDACION` / `REGLA_NEGOCIO` | Validación Pydantic fallida (fechas *naive*, `fecha_fin <= fecha_inicio`, `fecha_limite > inicio`, cupo `< 1`, campos vacíos, `extra="forbid"`) | Manejador omite `input` en errores de validación |

## 6. Seguridad, privacidad y zona horaria aplicables

- **Autorización y mínimo privilegio (`RNF-06`):** Todos los endpoints de E3 exigen `require_roles(Rol.ORGANIZADOR)` y las páginas web exigen `require_web_roles(Rol.ORGANIZADOR)` sobre **HTTPS obligatorio**. La verificación de propietario (`evento.organizador_id == usuario.id`) se ejecuta siempre en `evento_service.py` para evitar IDOR.
- **Defensa CSRF:** Todas las mutaciones (`POST`, `PATCH`) están cubiertas globalmente por `verificar_csrf` registrado en `api_router`.
- **Frontend seguro (`RF-27`, `RNF-12`):** Plantillas Jinja2 con autoescape, módulo JS dedicado `app/static/js/eventos.js`, envío de fechas con `aIsoBogota`, visualización con `formatearFechaBogota` (`America/Bogota`) y creación de DOM exclusivamente con `crearNodo`/`textContent` (cero `innerHTML`).
- **Fechas:** Almacenadas y comparadas en UTC; si `fecha_inicio` ya está en el pasado al publicar o `fecha_fin` ya pasó respecto a `ahora_utc()`, se evalúa usando `app.core.fechas.ahora_utc()`.

## 7. Casos límite

- Edición parcial (`PATCH`) donde solo se envía `fecha_fin` o solo `fecha_inicio`: debe validarse la coherencia `fecha_fin > fecha_inicio` y `fecha_limite_inscripcion <= fecha_inicio` combinando los campos nuevos con los existentes del evento antes de guardar.
- Creación en `borrador` con `fecha_inicio` pasada vs publicación: `HU-E3-02` exige explícitamente `inicio futuro` al publicar (`POST /publicar`), mientras `POST /eventos` en `borrador` exige únicamente `RN-02` y `RN-03` (aunque en UI sea habitual elegir fecha futura, la prueba automatizada puede crear un evento con fecha pasada en borrador o esperar con reloj simulado para verificar el rechazo al publicar).
- Evento `publicado` cuya `fecha_fin` ya pasó (`finalizado` calculado en tiempo real sin tarea cron en BD): debe seguir bloqueado para `PATCH` y `POST /cancelar`, y aparecer marcado como finalizado en `GET /organizador/eventos`.
- Múltiples eventos propios en `GET /organizador/eventos`: usar `contar_activas_por_eventos(db, ids)` en una sola consulta para evitar consultas N+1.
- Cancelar evento publicado que ya tiene inscripciones activas: las filas en `inscripciones` conservan su estado sin borrarse ni alterarse.

## 8. Supuestos y pendientes

- `[SUPUESTO S-15]` (Resuelto por equipo): Sin flujo de aprobación de eventos; el organizador publica directo si cumple las condiciones de publicación.
- `[SUPUESTO S-11]` (Confirmado por cliente): Horario oficial `America/Bogota` (UTC-5) en presentación y UTC en almacenamiento y comparaciones.
- **Decisiones resueltas en `/speckit.clarify`:**
  - `POST /api/v1/eventos/{id}/publicar` devuelve **409** si el evento no está en `borrador`, y **422 `REGLA_NEGOCIO`** si está en `borrador` pero `fecha_inicio <= ahora_utc()`.
  - `POST /api/v1/eventos/{id}/cancelar` aplica únicamente sobre eventos en estado **`publicado` no finalizados** (`409` en `borrador`, `cancelado` o `finalizado`) y exige `motivo` de al menos **5 caracteres** recortados (`422` si es menor).
  - `EventoSalida` devuelve tanto `estado` (guardado en BD) como `estado_efectivo` (`borrador`/`publicado`/`cancelado`/`finalizado`), `inscripciones_abiertas`, `inscripciones_activas` y `cupos_disponibles`.
  - Se expone `GET /api/v1/eventos/{evento_id}` restringido al organizador propietario (`401`/`403`/`404`) para soportar la carga directa de `/organizador/eventos/{id}/editar`.
- **Pendientes bloqueantes:** ninguno.

## 9. Criterios de éxito y verificación *(obligatorio)*

- **Criterios medibles:**
  - **SC-001:** Un organizador autenticado crea eventos válidos en `borrador` (`201`) y datos inválidos devuelven `422` sin persistir filas en `eventos`.
  - **SC-002:** La publicación directa cambia `borrador → publicado` (`200`), rechaza estado distinto (`409`), rechaza organizador ajeno (`403`) y rechaza inicio no futuro (`422 REGLA_NEGOCIO`).
  - **SC-003:** La edición permite subir cupo, bloquea bajar por debajo de inscripciones activas (`409`) y bloquea edición de eventos cancelados o finalizados (`409`).
  - **SC-004:** La cancelación pasa `publicado → cancelado` guardando `motivo_cancelacion` (`200`), preserva inscripciones existentes y rechaza motivo vacío (`422`).
  - **SC-005:** `GET /api/v1/organizador/eventos` solo lista eventos del organizador autenticado con conteo de cupos sin N+1 y estado `finalizado` calculado dinámicamente; las vistas `/organizador/eventos`, `/nuevo` y `/{id}/editar` operan por `fetch` sin `innerHTML`.
- **Pruebas funcionales (PF):** **PF-01** (registro y publicación válida), **PF-02** (creación inválida `422` sin persistir) y **PF-09** (propiedad de evento entre organizadores y control de rol).
- **Pruebas automatizadas (`pytest`):**
  - `tests/test_eventos.py`: creación válida e inválida (`422` sin persistencia), publicación exitosa, publicación de estado no borrador (`409`) y fecha pasada, edición parcial de fechas combinadas, cupo arriba/abajo (`409` si `< activas`), bloqueo de edición en `cancelado` y `finalizado` (simulado con `fecha_fin` pasada), cancelación con motivo (`200`, inscripciones intactas, motivo vacío `422`), listado `GET /organizador/eventos` aislado por organizador con `estado_efectivo == "finalizado"`, y vistas web `/organizador/eventos`, `/nuevo`, `/{id}/editar` (`200` organizador, `303` anónimo, `403` otro rol).
  - `tests/test_permisos.py`: sin sesión (`401`), participante y coordinación (`403`) en endpoints de eventos, y organizador distinto al propietario (`403 SIN_PERMISO`) en editar/publicar/cancelar (reglas críticas redactadas primero en rojo → verde).
