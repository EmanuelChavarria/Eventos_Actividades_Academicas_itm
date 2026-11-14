---
name: pf-evidencias
description: Documenta las pruebas funcionales PF-01 a PF-12 con evidencia en docs/pruebas/ y evidencias/. Úsala al ejecutar o registrar una prueba funcional.
---

# pf-evidencias

## Estructura
- Detalle: `docs/pruebas/PF-XX.md`. Evidencia (capturas, respuestas, consultas): `evidencias/PF-XX/`. Índice: `docs/pruebas.md` (B).
- Reparto: A → PF-01, 02, 03, 04, 09 · B → PF-05, 06, 07, 08, 10, 11 · ambos → PF-12.

## Contenido de cada `PF-XX.md`
Identificador · requisito asociado (RF/RN/CA) · condiciones iniciales · pasos · datos de entrada (ficticios) · resultado esperado · resultado obtenido · estado (aprobada/fallida) · evidencia (ruta) · método y código HTTP.

## Pruebas
| ID | Prueba | Esperado |
|---|---|---|
| PF-01 | Registro y publicación válida | 201 y visible en catálogo |
| PF-02 | Evento con datos inválidos | 422, nada persistido |
| PF-03 | Catálogo y detalle | 200 con cupos reales |
| PF-04 | Evento inexistente | 404 con formato de error |
| PF-05 | Inscripción válida | 201, persistida y consultable |
| PF-06 | Inscripción inválida | 422 controlado |
| PF-07 | Cupo agotado | 409 `CUPO_AGOTADO`, cupo intacto |
| PF-08 | Inscripción duplicada | 409 `INSCRIPCION_DUPLICADA` |
| PF-09 | Sin autorización | 401/403 |
| PF-10 | Asistencia | persistida y asociada a evento y participante |
| PF-11 | Consolidado | totales coherentes con el detalle |
| PF-12 | Flujo interfaz–API–BD | crear → publicar → inscribir → asistencia → consolidado, con **capturas de la pestaña Red** (llamadas `fetch` a `/api/v1`) y consulta de la BD |

## Reglas
- Usa Swagger (`/docs`) o un cliente HTTP, consulta directa a SQLite y capturas de la interfaz.
- **Privacidad:** datos ficticios; en capturas y consultas oculta o enmascara documentos; sin contraseñas ni tokens.
- Si una prueba falla: rama `fix` sobre la feature afectada, commit `fix(...)`, repite la prueba y registra ambos resultados.
- Commits: `docs(pruebas): registra resultados y evidencias de PF-0X`.
