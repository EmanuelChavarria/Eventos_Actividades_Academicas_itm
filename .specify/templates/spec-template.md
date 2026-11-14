# Especificación de Feature: [NOMBRE DE LA FEATURE]

- **Épica:** EXX · **Condiciones:** CA-0X · **Requisitos:** RF-.., RN-.., RNF-..
- **Rama de feature:** `[NNN-slug]` · **Creada:** [FECHA]
- **Estado:** borrador | aprobada · **Responsable:** Integrante A | B
- **Entrada:** Descripción del usuario: `"$ARGUMENTS"`

## 1. Objetivo y alcance

[Qué problema resuelve esta feature y qué entregas incluye dentro del alcance del proyecto PF-04.]

## 2. Fuera de alcance

[Qué queda explícitamente excluido en esta feature.]

## 3. Historias de usuario y criterios de aceptación *(obligatorio)*

<!--
  Las historias deben ordenarse por prioridad (P1, P2, P3...) y poder probarse
  de forma independiente. Cada escenario usa Dado / Cuando / Entonces e indica
  código HTTP, persistencia y cambio de estado cuando aplique.
-->

### Historia de Usuario 1 - [Título breve] (Prioridad: P1)

[Descripción del flujo en lenguaje claro.]

- **Por qué esta prioridad:** [Valor principal]
- **Prueba independiente:** [Cómo verificarla de forma aislada]
- **Escenarios de aceptación:**
  1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado, código HTTP y estado en BD].
  2. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado, código HTTP y estado en BD].

---

### Historia de Usuario 2 - [Título breve] (Prioridad: P2)

[Descripción del flujo.]

- **Por qué esta prioridad:** [Valor]
- **Prueba independiente:** [Cómo verificarla de forma aislada]
- **Escenarios de aceptación:**
  1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado].

---

## 4. Reglas de negocio y validaciones

- **RN-XX:** [Regla aplicable y dónde se valida: servicio y restricción de BD]
- **Validaciones de entrada (Pydantic v2):** [Campos, tipos, normalización y rangos; fechas en ISO-8601 con zona]
- **Entidades clave afectadas:** [Tablas/columnas y restricciones `UNIQUE`, `CHECK`, `FK`, índice parcial]

## 5. Errores esperados *(obligatorio)*

Formato uniforme de respuesta: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre | Notas de seguridad |
|---|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` / no autenticado | [Si aplica] | Sin indicar qué campo falló |
| 403 | `SIN_PERMISO` | [Rol insuficiente o recurso ajeno] | — |
| 404 | `...` | [Recurso inexistente o no publicado] | — |
| 409 | `...` | [Conflicto de estado, duplicado o cupo] | — |
| 422 | Validación | [Datos inválidos o regla de entrada] | Sin campo `input` con datos sensibles |

## 6. Seguridad, privacidad y zona horaria aplicables

- **Autorización y mínimo privilegio:** [Roles permitidos y verificación de propietario]
- **Privacidad y logs:** [Tratamiento de `numero_documento`, enmascarado si aplica, prohibido en logs/errores]
- **Seguridad web/API:** [Cookie/JWT, `Origin` en mutaciones, `textContent` sin `innerHTML` si hay vista JS]
- **Fechas:** [Almacenamiento y comparación en UTC; presentación en `America/Bogota`]

## 7. Casos límite

- [Condición límite 1: concurrencia, bordes de fecha UTC, cupo en 0, etc.]
- [Condición límite 2]

## 8. Supuestos y pendientes

- `[SUPUESTO S-XX]`: [Supuesto aplicable ya resuelto o confirmado]
- `[PENDIENTE: pregunta]`: [Duda bloqueante para preguntar al humano en `/speckit-clarify` antes de `/speckit-plan`]

## 9. Criterios de éxito y verificación *(obligatorio)*

- **Criterios medibles (SC-00X):** [Resultados verificables]
- **Pruebas funcionales (PF):** [PF-XX que cubren esta feature]
- **Pruebas automatizadas (`pytest`):** [Casos obligatorios, redactados rojo → verde antes de implementar reglas críticas]
