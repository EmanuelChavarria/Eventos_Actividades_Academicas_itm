## Propósito del Pull Request

<!-- Describe de forma concisa qué problema resuelve o qué feature implementa este PR. -->

## Épica y Especificación Asociada

- **Épica:** E...
- **Spec:** `specs/NNN-slug/`
- **Requisitos cubiertos:** RF-..., RNF-..., RN-..., CA-...

## Cambios Realizados

- 
- 
- 

## Pruebas Efectuadas

- [ ] Pruebas unitarias/integración con `pytest -q`
- [ ] Pruebas funcionales manuales (PF-...)
- [ ] Verificación de endpoints en `/docs`
- [ ] Verificación en contenedor Docker

## Checklist de Puertas de Calidad (G1 a G5)

- [ ] **G1/G2:** Spec, plan y tareas aprobados previamente sin pendientes bloqueantes.
- [ ] **G3:** Commits atómicos en español siguiendo Conventional Commits (≤ 72 caracteres).
- [ ] **G4:** `ruff check .` y `ruff format --check .` en verde sin advertencias.
- [ ] **G4:** `python scripts/export_openapi.py --check` sin discrepancias de contrato.
- [ ] **Seguridad:** Sin `.env`, `*.db`, claves privadas ni datos reales en el diff.
- [ ] **G5:** Revisión cruzada aprobada por el compañero (merge commit, no squash).
