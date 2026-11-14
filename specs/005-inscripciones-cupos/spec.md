# Especificación de Feature: Inscripciones y Control Atómico de Cupos

- **Épica:** E5 · **Condiciones:** CA-03, CA-04 · **Requisitos:** RF-14..RF-19, RN-04..RN-07, RN-11, RNF-03, RNF-04, RNF-06, RNF-08
- **Rama de feature:** `005-inscripciones-cupos` · **Creada:** 2026-11-14
- **Estado:** borrador · **Responsable:** Integrante B
- **Entrada:** Gestión integral del ciclo de inscripción, control atómico estricto de cupo sin sobrecupo bajo concurrencia, cancelación anticipada y consulta con privacidad diferencial.

---

## 1. Objetivo y alcance

Permitir a los participantes autenticados inscribirse en eventos académicos publicados y cancelar inscripciones activas antes del inicio del evento, garantizando de manera matemática y transaccional que el cupo nunca se exceda, preservando el historial de estados (`activa`, `cancelada`) y ofreciendo vistas diferenciadas de inscritos según el rol del usuario (organizador con documento visible, coordinación con documento enmascarado).

---

## 2. Fuera de alcance

- Pagos o cobros por inscripción (actividades gratuitas).
- Lista de espera automática al agotarse el cupo (descartada explícitamente en la constitución).
- Notificaciones externas por correo electrónico, SMS o WhatsApp.

---

## 3. Historias de usuario y criterios de aceptación

### Historia de Usuario 1 - Inscripción exitosa con reserva atómica de cupo (Prioridad: P1)

Como participante autenticado quiero inscribirme en un evento publicado que tiene cupo disponible, para asegurar mi participación en la actividad académica.

- **Por qué esta prioridad:** Núcleo de valor del sistema y condición CA-03.
- **Prueba independiente:** Realizar petición `POST /api/v1/eventos/{id}/inscripciones` con token de participante sobre evento publicado con cupo y verificar estado 201 y cupo calculado disminuido en 1.
- **Escenarios de aceptación:**
  1. **Dado** un evento en estado `publicado`, con cupo disponible (`activas < cupo_maximo`), fecha actual anterior a `fecha_limite_inscripcion` y un participante sin inscripción activa previa que cumple el público objetivo, **Cuando** solicita la inscripción, **Entonces** el sistema responde `201 Created` con el detalle de la inscripción en estado `activa`, persiste la fecha en UTC y el cupo disponible se reduce en 1.
  2. **Dado** un participante con una inscripción previa en estado `cancelada` para un evento que aún tiene cupo y plazo abierto, **Cuando** solicita inscribirse nuevamente, **Entonces** el sistema genera un **nuevo registro** en estado `activa` preservando el historial anterior (`201 Created`).

---

### Historia de Usuario 2 - Rechazo estricto de inscripciones inválidas y prevención de sobrecupo (Prioridad: P1)

Como sistema quiero rechazar de manera determinista cualquier intento de inscripción que viole las reglas de negocio, sin alterar datos ni generar registros parciales huérfanos.

- **Por qué esta prioridad:** Integridad transaccional y cumplimiento de CA-04 y Principio IV.
- **Prueba independiente:** Enviar peticiones concurrentes o con condiciones inválidas y verificar códigos 409 tipados sin mutación de BD.
- **Escenarios de aceptación:**
  1. **Dado** un evento cuyo cupo máximo ha sido alcanzado, **Cuando** un usuario intenta inscribirse, **Entonces** el sistema responde `409 Conflict` con código de dominio `CUPO_AGOTADO` y no inserta ningún registro.
  2. **Dado** un participante que ya cuenta con una inscripción en estado `activa` para el evento, **Cuando** intenta inscribirse de nuevo, **Entonces** el sistema responde `409 Conflict` con código `INSCRIPCION_DUPLICADA`.
  3. **Dado** un evento cuya `fecha_limite_inscripcion` ya transcurrió en UTC, **Cuando** se intenta una inscripción, **Entonces** responde `409 Conflict` con código `INSCRIPCIONES_CERRADAS`.
  4. **Dado** un evento en estado `borrador` o `cancelado`, **Cuando** se solicita inscripción, **Entonces** responde `409 Conflict` con código `EVENTO_NO_PUBLICADO`.
  5. **Dado** un participante cuyo rol no coincide con el `publico_objetivo` del evento, **Cuando** solicita inscripción, **Entonces** responde `409 Conflict` con código `PUBLICO_NO_PERMITIDO`.
  6. **Dado** un evento inexistente en la BD, **Cuando** se solicita inscripción, **Entonces** responde `404 Not Found` con código `EVENTO_NO_ENCONTRADO`.

---

### Historia de Usuario 3 - Cancelación de inscripción propia antes del evento (Prioridad: P2)

Como participante quiero cancelar mi inscripción activa antes de que inicie el evento, para liberar mi cupo a otros interesados manteniendo el registro de mi acción.

- **Por qué esta prioridad:** Flexibilidad para el usuario y recuperación de cupo disponible.
- **Prueba independiente:** Ejecutar `PATCH /api/v1/inscripciones/{id}/cancelar` antes de `fecha_inicio` y verificar transición a `cancelada` y aumento de cupo disponible.
- **Escenarios de aceptación:**
  1. **Dado** un participante con inscripción `activa` y fecha actual anterior a la `fecha_inicio` del evento, **Cuando** solicita cancelar su inscripción, **Entonces** el sistema responde `200 OK`, actualiza el estado a `cancelada`, registra la marca temporal de cancelación en UTC y libera el cupo inmediatamente.
  2. **Dado** un evento cuya `fecha_inicio` ya ha sido alcanzada o superada, **Cuando** el usuario intenta cancelar su inscripción, **Entonces** el sistema responde `409 Conflict` con código `CANCELACION_NO_PERMITIDA`.
  3. **Dado** un usuario intentando cancelar la inscripción de otro participante, **Cuando** envía la solicitud, **Entonces** el sistema responde `403 Forbidden` (`SIN_PERMISO`).

---

### Historia de Usuario 4 - Consulta de inscritos con privacidad diferencial (Prioridad: P2)

Como organizador del evento o miembro de coordinación académica quiero consultar la lista de inscritos, asegurando que los datos de identificación se revelen únicamente a quien tiene legitimidad.

- **Por qué esta prioridad:** Protección de datos personales y principio de mínimo privilegio.
- **Prueba independiente:** Consultar `GET /api/v1/eventos/{id}/inscripciones` como organizador dueño y como coordinación.
- **Escenarios de aceptación:**
  1. **Dado** el organizador creador del evento autenticado, **Cuando** consulta la lista de inscritos, **Entonces** el sistema retorna la lista de inscripciones con el `numero_documento` completo y visible.
  2. **Dado** un usuario con rol `coordinacion` autenticado, **Cuando** consulta la lista de inscritos del evento, **Entonces** el sistema retorna la lista en modo solo lectura con el documento de identidad enmascarado (`••••1234`).
  3. **Dado** un organizador ajeno intentando consultar los inscritos de un evento que no le pertenece, **Cuando** envía la petición, **Entonces** el sistema responde `403 Forbidden` (`SIN_PERMISO`).

---

### Historia de Usuario 5 - Consulta de inscripciones del participante (Prioridad: P3)

Como participante quiero acceder a la sección "Mis inscripciones", para consultar mis eventos vigentes e históricos y poder cancelar los que correspondan.

- **Por qué esta prioridad:** Usabilidad e interfaz del participante.
- **Prueba independiente:** Consultar `GET /api/v1/inscripciones/mias` y visualizar la página Jinja2 correspondiente.
- **Escenarios de aceptación:**
  1. **Dado** un participante autenticado, **Cuando** ingresa a "Mis inscripciones", **Entonces** visualiza sus inscripciones ordenadas cronológicamente, con el estado actual del evento (`publicado`, `finalizado`, `cancelado`) y la opción interactiva de cancelar aquellas que sigan activas antes del inicio.

---

## 4. Reglas de negocio y modelo de datos

- **RN-04 (Cupo Atómico):** El cupo disponible nunca se almacena; se calcula en tiempo de ejecución: `cupo_disponible = cupo_maximo - COUNT(inscripciones WHERE estado = 'activa')`.
  - La inserción atómica se ejecuta obligatoriamente bajo transacción `BEGIN IMMEDIATE` con sentencia condicional SQL:
    ```sql
    INSERT INTO inscripciones (id, evento_id, usuario_id, estado, creado_en)
    SELECT ?, ?, ?, 'activa', ?
    WHERE (
        SELECT COUNT(*) FROM inscripciones 
        WHERE evento_id = ? AND estado = 'activa'
    ) < (SELECT cupo_maximo FROM eventos WHERE id = ?);
    ```
  - Si `cursor.rowcount == 0`, se verifica la causa (cupo agotado vs evento no existente/cerrado) y se levanta `ErrorDominio(CUPO_AGOTADO)`.
- **RN-05 (Unicidad Activa):** Índice único parcial en BD:
  `CREATE UNIQUE INDEX uq_inscripcion_activa ON inscripciones (evento_id, usuario_id) WHERE estado = 'activa';`
- **RN-06 (Historial y Reinscripción):** Las cancelaciones nunca hacen `DELETE`; actualizan `estado = 'cancelada'`. Una reinscripción crea un nuevo registro con nuevo UUID.
- **RN-07 (Límite de Cancelación):** Cancelación permitida solo si `ahora_utc < evento.fecha_inicio`.
- **RN-11 (Público Objetivo):** Si `evento.publico_objetivo != 'todos'`, el rol del usuario debe coincidir exactamente.

---

## 5. Errores esperados

Formato uniforme: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre |
|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | Usuario no autenticado o token ausente/inválido. |
| 403 | `SIN_PERMISO` | Intento de cancelar inscripción ajena o ver lista ajena sin ser dueño ni coordinación. |
| 404 | `EVENTO_NO_ENCONTRADO` | `evento_id` no existe en la base de datos. |
| 404 | `INSCRIPCION_NO_ENCONTRADA` | `inscripcion_id` no existe o no pertenece al usuario en cancelación. |
| 409 | `CUPO_AGOTADO` | Evento alcanzó su capacidad máxima de inscripciones activas. |
| 409 | `INSCRIPCION_DUPLICADA` | El participante ya tiene una inscripción activa en el evento. |
| 409 | `INSCRIPCIONES_CERRADAS` | La fecha límite de inscripción ya fue superada. |
| 409 | `EVENTO_NO_PUBLICADO` | El evento está en estado `borrador` o `cancelado`. |
| 409 | `PUBLICO_NO_PERMITIDO` | El rol del participante no cumple con el público objetivo definido. |
| 409 | `CANCELACION_NO_PERMITIDA` | Intento de cancelar después de la fecha de inicio del evento. |
| 422 | `VALIDACION_ERROR` | Parámetros de petición mal formados (sin incluir `input` en respuesta). |

---

## 6. Seguridad y privacidad

- **Mínimo Privilegio:** Autorización basada en rol y propietario (`usuario.id == inscripcion.usuario_id` o `usuario.id == evento.organizador_id`).
- **Enmascaramiento:** Función `enmascarar_documento(num)` retorna `••••` seguido de los últimos 4 dígitos para rol `coordinacion`.
- **Protección de Logs:** El `numero_documento` está prohibido en logs de acceso, trazas y mensajes de error.
- **Transaccionalidad SQLite:** Conexión con `PRAGMA foreign_keys=ON`, `PRAGMA busy_timeout=5000` y `journal_mode=WAL`.

---

## 7. Casos límite

- Dos peticiones simultáneas disputando el último cupo: solo una debe registrar éxito (`201`), la otra debe recibir `409 CUPO_AGOTADO`.
- Intento de cancelación en el segundo exacto de inicio del evento.
- Intento de reinscripción inmediata tras cancelación cuando ya otro usuario ocupó el cupo liberado.

---

## 8. Supuestos

- `[SUPUESTO S-03]`: Para la prueba de simultaneidad (PF-07), se implementará un test con hilos (`concurrent.futures`) usando una base de datos SQLite en archivo temporal con WAL habilitado.

---

## 9. Criterios de éxito y verificación

- **SC-E5-01:** Pruebas unitarias de cupo, duplicados, público objetivo y fechas en verde en `tests/test_inscripciones.py`.
- **SC-E5-02:** Prueba de concurrencia con 20 hilos disputando 5 cupos resulta exactamente en 5 exitosos y 15 rechazados con `CUPO_AGOTADO`.
- **SC-E5-03:** Cobertura de pruebas funcionales PF-05, PF-06, PF-07 y PF-08.
