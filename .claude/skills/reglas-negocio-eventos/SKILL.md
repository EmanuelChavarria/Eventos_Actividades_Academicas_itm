---
name: reglas-negocio-eventos
description: Referencia de estados, reglas de negocio (RN), códigos de error, seguridad y cupo atómico del dominio de eventos, inscripciones y asistencia. Úsala al implementar o revisar cualquier regla de negocio.
---

# reglas-negocio-eventos

## Estados
- **Evento (guardados):** `borrador → publicado → cancelado`. `finalizado` e «inscripciones cerradas» se **calculan**. Sin retrocesos.
- **Inscripción:** `activa` / `cancelada`. **Asistencia:** `presente` / `ausente` (sin registro = pendiente).

## Reglas clave
- **Publicar** (sin aprobación): datos completos, `fecha_fin > fecha_inicio`, `fecha_limite_inscripcion ≤ fecha_inicio`, inicio futuro, cupo ≥ 1.
- **Cupo:** sube siempre; baja hasta las inscripciones activas; no se edita en cancelados ni finalizados. Sin lista de espera. `cupos_disponibles = cupo_maximo − activas` (calculado).
- **Inscribir:** autenticado (`activo == True`), evento publicado, antes de `fecha_limite_inscripcion`, cupo disponible, sin inscripción activa, cumple `publico_objetivo`.
- **Cancelar inscripción:** hasta el inicio; libera cupo; conserva historial. Reinscripción = registro nuevo si cumple todo.
- **Cancelar evento:** conserva inscripciones; bloquea inscripciones y asistencia nuevas.
- **Asistencia:** la registra el organizador del evento, solo inscripciones activas, desde `fecha_inicio` hasta `fecha_fin + 48 h`; correcciones guardan quién y cuándo.
- **Identidad y seguridad:** `UNIQUE(tipo_documento, numero_documento)`; el correo no es único. Hash **argon2id**, verificación en tiempo constante y límite de **10 intentos fallidos** en login. JWT `HS256` con `sub = usuario.id`; validar `Origin`/`Referer` en mutaciones con cookie. Documento completo para el organizador de su evento, enmascarado (`••••1234`) para coordinación, nunca en logs ni errores (tampoco `input` en 422).
- **Fechas:** UTC en BD y comparaciones; API rechaza fechas sin zona (422) y usa ISO-8601 con zona; presentación con `Intl` en `America/Bogota`.

## Códigos de error (HTTP → código)
| HTTP | Código |
|---|---|
| 409 | `DOCUMENTO_DUPLICADO`, `INSCRIPCION_DUPLICADA`, `CUPO_AGOTADO`, `INSCRIPCIONES_CERRADAS`, `PUBLICO_NO_PERMITIDO`, `CANCELACION_NO_PERMITIDA`, `ASISTENCIA_NO_PERMITIDA`, `EVENTO_NO_PUBLICADO` |
| 404 | `EVENTO_NO_ENCONTRADO`, `INSCRIPCION_NO_ENCONTRADA` |
| 403 | `SIN_PERMISO` |
| 401 | `CREDENCIALES_INVALIDAS` (sin indicar si falló documento o contraseña) |
| 429 | `DEMASIADOS_INTENTOS` (tras 10 intentos fallidos en login) |
| 422 | validación (Pydantic / `ReglaNegocio`, sin `input` sensible) |

## Cupo atómico
Transacción iniciada con `BEGIN IMMEDIATE` (con `PRAGMA foreign_keys=ON` y `busy_timeout=5000`), ejecutando una sola sentencia condicional y verificando `rowcount`:

```sql
INSERT INTO inscripciones (evento_id, participante_id, estado, creado_en)
SELECT :e, :p, 'activa', :ahora
WHERE (SELECT COUNT(*) FROM inscripciones WHERE evento_id=:e AND estado='activa')
    < (SELECT cupo_maximo FROM eventos WHERE id=:e);
```
`rowcount == 0` → el service decide `CUPO_AGOTADO`. El índice único parcial `(evento_id, participante_id) WHERE estado='activa'` cubre el duplicado en carrera (→ `INSCRIPCION_DUPLICADA`). Un rechazo no deja registros parciales.
