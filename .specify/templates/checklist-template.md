# Checklist de [TIPO]: [NOMBRE DE LA FEATURE]

**Propósito:** [Qué valida esta lista de verificación]
**Creada:** [FECHA]
**Feature:** [Enlace a `spec.md`]

**Nota:** Generado con `/speckit-checklist`. El revisor marca `[x]` solo cuando confirma que el criterio de calidad de requisitos se cumple. `/speckit-implement` lee el estado de estos checkboxes como puerta y no debe modificar los marcadores.

## Trazabilidad y reglas de negocio

- [ ] CHK001 Cada requisito de la spec enlaza a RF/RN/RNF y CA-0X del proyecto
- [ ] CHK002 Están definidos todos los errores esperados (HTTP + código de dominio)
- [ ] CHK003 Las reglas respetan las decisiones finales aprobadas (documento único, correo no único, UTC/`America/Bogota`, sin lista de espera, sin aprobación de eventos, ventana 48 h)

## Seguridad, privacidad e integridad

- [ ] CHK004 Autorización por rol y por propietario definida en cada endpoint y vista
- [ ] CHK005 Privacidad del documento (completo organizador propio, enmascarado coordinación, nunca en logs/errores ni 422 `input`)
- [ ] CHK006 Integridad en BD (PK/FK/UNIQUE/CHECK/índice parcial) y atomicidad/concurrencia cubiertas

## Notas

- Dejar sin marcar `[ ]` cualquier ítem pendiente de aclaración o corrección.
- Enlazar `docs/pruebas/PF-XX.md` y pruebas `pytest` correspondientes cuando aplique.
