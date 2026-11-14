---
name: commits-convencionales
description: Redacta y valida commits atómicos en Conventional Commits en español, con alcance y pie Refs/Spec. Úsala al hacer cada commit de una tarea.
---

# commits-convencionales

## Formato
`tipo(alcance): descripción` — presente, minúscula inicial, sin punto final, **≤ 72 caracteres**. Cuerpo opcional para el porqué. Pie opcional:

```
Refs: RF-05, RN-02, CA-01
Spec: specs/003-gestion-eventos
```

- **Tipos:** `feat fix docs test refactor style chore perf ci build`.
- **Alcances:** `specs docker ci devops repo core bd auth eventos catalogo inscripciones asistencia reportes web docs pruebas`.
- Regex: `^(feat|fix|docs|test|refactor|style|chore|perf|ci|build)(\([a-z0-9-]+\))?: .{1,72}$`.

## Reglas
1. **Una tarea de `tasks.md` = un commit atómico**; marca la tarea hecha en el mismo commit. Si el mensaje necesita «y», son dos commits.
2. Cada commit deja la app ejecutable. Antes: `ruff check . && ruff format .`.
3. `git add` con **archivos explícitos**, nunca `git add .`.
4. Prohibido: `--no-verify`, mensajes como «cambios», «update», «fix», «wip», y commitear `.env`, `*.db`, `.venv/`, `__pycache__/`.
5. Cambios de comportamiento: primero `docs(specs): ...` y después el commit de código.
6. Nunca commitear en `main`.

## Ejemplos
```
feat(inscripciones): rechaza inscripción cuando el cupo está agotado
fix(catalogo): corrige conteo de cupos con inscripciones canceladas
docs(specs): agrega spec, plan y tareas de E3
test(auth): agrega prueba de documento duplicado con 409
```

Tras el commit reporta: qué hiciste, hash, qué probaste y qué sigue.
