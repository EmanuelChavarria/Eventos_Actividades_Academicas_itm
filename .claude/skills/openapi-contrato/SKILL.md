---
name: openapi-contrato
description: Regenera y verifica el contrato OpenAPI (specs/contrato/openapi.json) con scripts/export_openapi.py. Úsala cuando un cambio altere endpoints o schemas, o ante conflictos en ese archivo.
---

# openapi-contrato

El contrato `specs/contrato/openapi.json` se **genera desde el código**; nunca se edita a mano (`AGENTS.md` §4).

## Cuándo
- Cambiaste endpoints, schemas, códigos de respuesta o ejemplos.
- El CI falló por `export_openapi.py --check`.
- Hay conflicto de fusión en el archivo.

## Pasos
```bash
python scripts/export_openapi.py           # regenera (serializa app.openapi() ordenado)
python scripts/export_openapi.py --check   # verifica; falla si hay desvío
git add specs/contrato/openapi.json
git commit -m "docs(specs): regenera contrato OpenAPI"
```

## Conflictos
No edites el JSON: acepta cualquier versión, regenera con el script y commitea `docs(specs): regenera contrato OpenAPI`. Hazlo tras cada `rebase`.

## Reglas
- Un cambio de contrato compartido requiere acuerdo de ambos integrantes y la spec actualizada antes.
- Los endpoints documentados deben coincidir con la tabla de API de `docs/01_analisis_y_especificaciones.md` (incluye errores `409 DOCUMENTO_DUPLICADO`, etc.).
- `scripts/export_openapi.py` es de B (E10); mientras no exista, avisa al humano en lugar de crearlo fuera de su épica.
