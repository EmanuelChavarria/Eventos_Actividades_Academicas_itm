---
paths:
  - "specs/**/*.md"
  - ".specify/**/*.md"
---

# Reglas para specs (Spec Kit)

- **Sin spec aprobada no hay código.** Ciclo: `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`. Detente en G1 (spec) y G2 (plan, tareas y `analyze` sin críticos).
- **Numeración:** pasar siempre `-Number N` explícito a `create-new-feature.ps1` (según la tabla épica ↔ feature en `AGENTS.md` §3) para evitar colisiones entre A y B.
- **Ubicación:** `specs/NNN-slug/{spec,plan,tasks}.md` en la rama `NNN-slug`. El contrato vive en `specs/contrato/openapi.json` y se regenera con `python scripts/export_openapi.py`, nunca a mano.
- **Contenido mínimo de `spec.md`:** épica, condiciones CA-0X y requisitos RF/RN/RNF trazables; historias con Dado/Cuando/Entonces; **errores esperados** (HTTP + código de dominio); seguridad y privacidad; casos límite; fuera de alcance; supuestos y pendientes; **verificación** (PF-XX y pytest).
- **Pendientes:** lo no confirmado se rotula `[SUPUESTO S-XX]` o `[PENDIENTE: pregunta]`. Un `[PENDIENTE]` bloqueante impide pasar a `plan`. Nunca inventes respuestas del cliente.
- **`tasks.md`:** una tarea = un commit atómico, con ID `T-NNN-01`, dependencias, archivos, commit sugerido (Conventional Commits en español), criterio de terminado y estado.
- **La spec manda:** si cambia el comportamiento, commit `docs(specs): ...` antes del commit de código.
- **Coherencia con la constitución y las reglas finales:** documento único `tipo_documento` + `numero_documento` (`DOCUMENTO_DUPLICADO` 409), correo solo contacto, UTC/`America/Bogota`, sin lista de espera ni aprobación de eventos, ventana de asistencia de 48 h, y controles de seguridad de la constitución v2.0.1.
- **Constitución y plantillas** (`.specify/memory/constitution.md`, `.specify/templates/`): solo cambian con acuerdo de ambos integrantes.
