# Checklist de calidad de especificación: Autenticación, roles y autorización (E2)

**Propósito:** Validar completitud, claridad y cumplimiento de la constitución antes de aprobar la puerta G1 y planificar E2.
**Creada:** 2026-11-14
**Feature:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/002-autenticacion-roles/spec.md)

## Contenido y estructura

- [x] Todas las secciones obligatorias de `.specify/templates/spec-template.md` están completas
- [x] Enfocada en qué necesita el sistema y por qué (alcance estricto de E2, sin invadir E3–E7)
- [x] Trazabilidad explícita a RF-01, RF-02, RF-03, RF-04, RN-13, RN-14, RN-21 y RNF-05, 06, 07, 08, 12, 15

## Completitud y reglas del proyecto

- [x] Marcadores `[PENDIENTE: ...]` resueltos con el humano (`/speckit.clarify`) antes de pasar a `/speckit.plan`
- [x] Supuestos `S-01`, `S-03`, `S-09`, `S-13` y `S-14` documentados explícitamente
- [x] Historias de usuario con escenarios `Dado / Cuando / Entonces` independientes y verificables
- [x] Errores esperados mapeados (`401`, `403`, `409`, `422`, `429`) con notas de seguridad y sin campo `input`
- [x] Casos límite contemplados (normalización de documento, concurrencia `IntegrityError`, usuario inactivo con JWT vigente, token manipulado/expirado, reinicio de límite al login exitoso, origen CSRF inválido)
- [x] Requisitos de seguridad (`argon2id`, verificación en tiempo constante, límite 10 fallos, JWT `HS256` `sub=id`, cookie `HttpOnly`+`SameSite=Lax`+`Secure`+`Max-Age=3600`, defensa `Origin`/`Referer`, `textContent` sin `innerHTML`) alineados con `.specify/memory/constitution.md` v2.0.2

## Preparación para G1 / Planificación

- [x] Criterios de éxito medibles (SC-001..SC-005) y lista de casos `pytest` definidos (`test_auth.py`, `test_permisos.py`)
- [x] Aprobación explícita del humano (**Puerta G1**) antes de ejecutar `/speckit.plan`
