# Especificación de Feature: Registro y Consulta de Asistencia

- **Épica:** E6 · **Condiciones:** CA-05 · **Requisitos:** RF-20..RF-23, RN-08, RN-10, RN-11, RNF-06, RNF-08
- **Rama de feature:** `006-asistencia` · **Creada:** 2026-11-14
- **Estado:** borrador · **Responsable:** Integrante A
- **Entrada:** Control de asistencia a eventos académicos, ventana temporal de registro y corrección, trazabilidad de auditoría y visualización protegida por roles.

---

## 1. Objetivo y alcance

Permitir al organizador responsable de un evento registrar y corregir el estado de asistencia (`presente`, `ausente`) de los participantes formalmente inscritos, restringiendo la operación estrictamente a la ventana temporal de validez (desde `fecha_inicio` hasta 48 horas después de `fecha_fin`), auditando autor y marcas temporales en UTC, y habilitando la consulta diferenciada de asistencia (organizador con documento completo, coordinación académica con documento enmascarado).

---

## 2. Fuera de alcance

- Lectura automatizada de códigos QR o reconocimiento biométrico (excluido en guía docente).
- Emisión o firma digital de certificados de asistencia (excluido en guía docente).
- Registro de asistencia por parte de participantes (solo organizador del evento).

---

## 3. Historias de usuario y criterios de aceptación

### Historia de Usuario 1 - Registro de asistencia por el organizador en ventana válida (Prioridad: P1)

Como organizador del evento quiero marcar la asistencia (`presente` o `ausente`) de cada participante con inscripción activa durante el desarrollo del evento o hasta 48 horas posteriores a su culminación.

- **Por qué esta prioridad:** Cumple la condición CA-05 y la trazabilidad de participación académica.
- **Prueba independiente:** Enviar `PUT /api/v1/eventos/{id}/inscripciones/{inscripcion_id}/asistencia` con estado `presente` durante el rango de fechas válido y verificar respuesta 200 con persistencia en BD.
- **Escenarios de aceptación:**
  1. **Dado** un evento publicado, una inscripción activa y la fecha actual comprendida entre `evento.fecha_inicio` y `evento.fecha_fin + 48 horas` (en UTC), **Cuando** el organizador propietario envía la solicitud de asistencia, **Entonces** el sistema responde `200 OK`, persiste el estado (`presente` o `ausente`), registra `registrado_por` con el ID del organizador y `registrado_en` en UTC.
  2. **Dado** un intento de registro antes de la `fecha_inicio` del evento o posterior a 48 horas de la `fecha_fin`, **Cuando** el organizador intenta registrar asistencia, **Entonces** el sistema responde `409 Conflict` con código `ASISTENCIA_NO_PERMITIDA`.
  3. **Dado** un evento en estado `cancelado` o una inscripción en estado `cancelada`, **Cuando** se intenta registrar asistencia, **Entonces** el sistema responde `409 Conflict` con código `ASISTENCIA_NO_PERMITIDA`.

---

### Historia de Usuario 2 - Corrección de asistencia dentro de la ventana (Prioridad: P1)

Como organizador quiero rectificar el estado de asistencia previamente registrado a un participante dentro del plazo límite, para subsanar errores humanos conservando la auditoría de cambio.

- **Por qué esta prioridad:** Garantiza exactitud en los datos sin duplicar registros de asistencia.
- **Prueba independiente:** Modificar una asistencia de `ausente` a `presente` dentro de la ventana temporal y verificar que se actualiza el mismo registro y se actualizan `actualizado_por` y `actualizado_en`.
- **Escenarios de aceptación:**
  1. **Dado** una asistencia ya registrada previamente, **Cuando** el organizador envía un nuevo estado dentro de la ventana de 48 horas, **Entonces** el sistema responde `200 OK`, actualiza el estado en el registro existente (sin crear filas adicionales), fija `actualizado_por` y `actualizado_en` en UTC.
  2. **Dado** que ya transcurrieron más de 48 horas desde `evento.fecha_fin`, **Cuando** se intenta rectificar una asistencia, **Entonces** el sistema responde `409 Conflict` con código `ASISTENCIA_NO_PERMITIDA`.

---

### Historia de Usuario 3 - Consulta de lista de asistencia con control de privacidad (Prioridad: P2)

Como organizador del evento o personal de coordinación académica quiero consultar la lista consolidada de asistencia de un evento, garantizando el principio de mínimo privilegio sobre los datos del participante.

- **Por qué esta prioridad:** Permite el seguimiento institucional y previene divulgación no autorizada de identificación.
- **Prueba independiente:** Invocar `GET /api/v1/eventos/{id}/asistencia` con token de organizador dueño y luego con token de coordinación.
- **Escenarios de aceptación:**
  1. **Dado** el organizador del evento autenticado, **Cuando** consulta la lista de asistencia, **Entonces** visualiza nombre completo, correo, `numero_documento` completo, estado de inscripción y estado de asistencia (`presente`, `ausente` o `pendiente`).
  2. **Dado** un usuario con rol `coordinacion` autenticado, **Cuando** consulta la lista de asistencia, **Entonces** visualiza los mismos datos pero con el `numero_documento` enmascarado (`••••1234`).
  3. **Dado** un organizador ajeno al evento o un participante, **Cuando** intenta consultar la lista de asistencia del evento, **Entonces** el sistema responde `403 Forbidden` con código `SIN_PERMISO`.

---

### Historia de Usuario 4 - Interfaz web ágil para registro de asistencia (Prioridad: P3)

Como organizador quiero disponer de una pantalla web con la nómina de inscritos y selectores rápidos de asistencia, para asentar la asistencia en lote de manera intuitiva y segura.

- **Por qué esta prioridad:** Eficiencia operativa del organizador durante y después del evento.
- **Prueba independiente:** Ingresar a `/eventos/{id}/asistencia` en el navegador y marcar asistencia interactiva mediante llamadas JS `fetch` sin recarga.
- **Escenarios de aceptación:**
  1. **Dado** el organizador autenticado en la vista web de asistencia, **Cuando** selecciona `presente` o `ausente` en una fila, **Entonces** el frontend envía la petición `PUT` y muestra confirmación visual de guardado inmediato.

---

## 4. Reglas de negocio y modelo de datos

- **RN-08 (Ventana de Asistencia):** La asistencia solo puede registrarse o corregirse en el intervalo:
  $$\text{evento.fecha\_inicio} \le \text{ahora\_utc} \le (\text{evento.fecha\_fin} + 48\,\text{horas})$$
  Cualquier operación fuera de este intervalo levanta error `409 ASISTENCIA_NO_PERMITIDA`.
- **RN-10 (Unicidad y Auditoría de Asistencia):**
  - Una inscripción solo puede tener a lo sumo un registro de asistencia asociado (`UNIQUE(inscripcion_id)`).
  - Todo cambio persiste `actualizado_por` y `actualizado_en` (UTC).
- **RN-11 (Mínimo Privilegio):** Solo el organizador creador del evento (`evento.organizador_id == usuario.id`) puede registrar o corregir asistencia. Coordinación solo tiene permisos de lectura (`GET`).

---

## 5. Errores esperados

Formato uniforme: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Causa |
|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | No autenticado. |
| 403 | `SIN_PERMISO` | Rol no autorizado o usuario no es organizador del evento. |
| 404 | `EVENTO_NO_ENCONTRADO` | `evento_id` no existe. |
| 404 | `INSCRIPCION_NO_ENCONTRADA` | `inscripcion_id` no existe en el evento especificado. |
| 409 | `ASISTENCIA_NO_PERMITIDA` | Fuera de ventana temporal (antes de inicio o >48h fin), evento cancelado o inscripción cancelada. |
| 422 | `VALIDACION_ERROR` | Estado de asistencia inválido (distinto a `presente` o `ausente`). |

---

## 6. Seguridad y privacidad

- **Privacidad de Documento:** `numero_documento` nunca se muestra a coordinación sin enmascarar (`••••1234`).
- **Logs:** Prohibido registrar documentos o identificaciones en logs y trazas.
- **Validación CSRF / Same-Origin:** Validación de cabecera `Origin` en mutaciones `PUT`.

---

## 7. Casos límite

- Intento de registro en el segundo 0 posterior a las 48 horas de finalización del evento (debe rechazarse con 409).
- Modificación de asistencia de un participante que canceló su inscripción antes del evento (debe rechazarse con 409).

---

## 8. Criterios de éxito y verificación

- **SC-E6-01:** Suite de pruebas en `tests/test_asistencia.py` validando permisos, ventana temporal de 48 h y upsert idempotente.
- **SC-E6-02:** Documentación y evidencia de la prueba funcional **PF-10** en `docs/pruebas/PF-10.md` y `evidencias/PF-10/`.
