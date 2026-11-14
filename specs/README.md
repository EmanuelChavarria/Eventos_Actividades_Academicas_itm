# Especificaciones del Proyecto (Spec-Driven Development)

Este directorio centraliza las especificaciones técnicas, planes de arquitectura y tareas atómicas para el desarrollo guiado por especificación (SDD) con **Spec Kit**.

---

## 1. Mapeo de Épicas a Features (Spec Kit)

Las ramas de desarrollo de cada feature siguen la convención `NNN-slug` pasando el parámetro `-Number N` explícito a `create-new-feature.ps1` o `/speckit.specify`.

| Épica | Feature / Carpeta | Nombre | Responsable | Rama |
|---|---|---|:---:|---|
| **E0** | *(Transversal)* | Cimientos de SDD (constitución y plantillas) | **B** | `docs/E0-sdd-constitucion` |
| **E1** | `001-fundacion` | Fundación y plataforma base | **A** | `001-fundacion` |
| **E2** | `002-autenticacion-roles` | Autenticación, roles y autorización | **A** | `002-autenticacion-roles` |
| **E3** | `003-gestion-eventos` | Gestión de eventos (creación/edición) | **A** | `003-gestion-eventos` |
| **E4** | `004-catalogo-eventos` | Catálogo y consulta de eventos | **A** | `004-catalogo-eventos` |
| **E5** | `005-inscripciones-cupos` | Inscripciones y control atómico de cupos | **B** | `005-inscripciones-cupos` |
| **E6** | `006-asistencia` | Registro y consulta de asistencia | **B** | `006-asistencia` |
| **E7** | `007-consolidado` | Consolidado para coordinación | **B** | `007-consolidado` |
| **E8** | *(Pruebas)* | Pruebas funcionales PF-01…PF-12 | **A y B** | `test/E8a-…` / `test/E8b-…` |
| **E9** | *(Docs)* | Documentación, diseño y trazabilidad | **A y B** | `docs/E9a-…` / `docs/E9b-…` |
| **E10** | `010-devops-ci-docker` | DevOps: CI, Docker, hooks y contrato | **B** | `010-devops-ci-docker` |

---

## 2. Ciclo de Trabajo SDD y Puertas de Control (G1 a G5)

El flujo estricto de desarrollo por feature comprende los siguientes pasos:

$$\text{specify} \longrightarrow \text{clarify} \overset{\mathbf{G1}}{\longrightarrow} \text{plan} \longrightarrow \text{tasks} \longrightarrow \text{analyze} \overset{\mathbf{G2}}{\longrightarrow} \text{implement} \overset{\mathbf{G3}}{\longrightarrow} \text{verificar} \overset{\mathbf{G4}}{\longrightarrow} \text{cerrar} \overset{\mathbf{G5}}{\longrightarrow} \text{merge}$$

| Paso | Comando / Acción | Artefacto Generado | Puerta de Control |
|---|---|---|---|
| **1. Especificar** | `/speckit.specify` | `specs/NNN-slug/spec.md` | — |
| **2. Clarificar** | `/speckit.clarify` | Spec sin ambigüedades (`[SUPUESTO S-XX]`) | **G1: Aprobación humana de la spec.** Sin spec aprobada no hay plan ni código. |
| **3. Planificar** | `/speckit.plan` | `specs/NNN-slug/plan.md` | — |
| **4. Tareas** | `/speckit.tasks` | `specs/NNN-slug/tasks.md` | — |
| **5. Analizar** | `/speckit.analyze` | Informe de consistencia | **G2: Aprobación humana de plan y tareas.** Apertura de **PR en borrador** para visibilidad del compañero. |
| **6. Implementar** | `/speckit.implement` | Código en `app/` y pruebas en `tests/` | **G3: Cumplimiento de criterio por tarea.** Un commit por tarea con tests en verde. |
| **7. Verificar** | Checklist, pytest, ruff, `export_openapi.py --check` | Evidencias y validaciones | **G4: CI en verde.** Pipelines de calidad, pruebas y contrato sin fallos. |
| **8. Cerrar** | Revisión de código entre integrantes | PR listo para fusión | **G5: Aprobación del compañero.** Merge commit hacia `main`. |

---

## 3. Gobernanza y Gestión de Cambios

1. **La Spec Manda:** Cualquier cambio de diseño o comportamiento requiere actualizar primero la especificación (`docs(specs): ...`) antes de modificar el código.
2. **Contrato de API Compartido:** El archivo `specs/contrato/openapi.json` representa la fuente de verdad pública. Se regenera exclusivamente con `python scripts/export_openapi.py`.
3. **Propiedad y Coordinación:** Cada integrante implementa sus épicas. Modificaciones al contrato compartido o a capas base (`app/core/`, `app/models/`, `app/api/deps.py`) requieren acuerdo mutuo previo.
