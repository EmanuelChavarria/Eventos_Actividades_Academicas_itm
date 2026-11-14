@AGENTS.md

# Instrucciones específicas de Claude Code

Las reglas del proyecto están en `AGENTS.md` (importado arriba) y en `.specify/memory/constitution.md`. Este archivo solo añade lo propio de Claude Code.

## Perfil local
- Tu identidad (Integrante A o B) y tus épicas están en `CLAUDE.local.md` (no se sube a Git). Si no existe o está sin completar, **pregunta al humano quién es** antes de actuar.

## Comandos de Spec Kit
- Usa los skills de Spec Kit en `.claude/skills/speckit-*/` en este orden: `/speckit-specify → /speckit-clarify → /speckit-plan → /speckit-tasks → /speckit-analyze → /speckit-implement`. Tras `tasks` y `analyze`, **detente y pide la aprobación** (G1 y G2).
- Al crear una feature con `/speckit-specify` o `create-new-feature.ps1`, pasa `-Number N` explícito según `AGENTS.md` §3.
- No ejecutes `/speckit-implement` sin spec aprobada.

## Forma de trabajar
- Para tareas de varios pasos, propón primero un plan breve y espera confirmación del humano cuando afecte contrato compartido o archivos del otro integrante.
- Usa herramientas de edición sobre archivos concretos; no hagas `git add .` ni `git push --force`.
- Ante ambigüedad usa la pregunta directa al humano en lugar de asumir.
- Responde siempre en español, de forma concisa.

## Permisos y protecciones
- No leas `.env`. Los permisos de `.claude/settings.json` (cuando exista) deniegan `git push --force`, push a `main` y la lectura de `.env`; no intentes eludirlos.
- Las preferencias personales van en `.claude/settings.local.json` (ignorado por Git).
