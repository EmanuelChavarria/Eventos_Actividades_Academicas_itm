---
name: capas-fastapi
description: Indica dónde va cada cosa en la arquitectura en capas (routers, services, repositories, models, schemas, web, static/js) y cómo traducir errores. Úsala al crear o modificar código en app/.
---

# capas-fastapi

Flujo: `api (routers) → services → repositories → models`. Dependencias solo hacia adentro.

| Capa | Va aquí | NO va aquí |
|---|---|---|
| `app/api/v1/*.py` | Rutas, validación con schemas, `Depends(require_roles(...))`, llamada a un service | Reglas de negocio, SQL, `try/except` repetidos |
| `app/services/*.py` | **Toda** la lógica de negocio (RN-xx), control de la transacción, verificación de propietario, errores de dominio | Imports de FastAPI, SQL directo |
| `app/repositories/*.py` | Consultas SQLAlchemy y escrituras; alta atómica de inscripción | Reglas de negocio |
| `app/models/*.py` | Tablas, enums, restricciones (contrato compartido) | Lógica |
| `app/schemas/*.py` | Schemas Pydantic v2 separados de entrada y salida (nunca `hash_password`) | Acceso a datos |
| `app/core/*.py` | Config, seguridad, errores, logging, fechas (UTC ↔ `America/Bogota`) | Lógica de un dominio concreto |
| `app/web/*.py` + `templates/` | Solo renderizan el esqueleto Jinja2 | Datos del dominio (llegan por `fetch`) |
| `app/static/js/` | `api.js` común + un módulo por página que llama a `/api/v1` | Bundler, SPA |

## Receta para un endpoint nuevo
1. Schemas de entrada y salida.
2. Método en el repositorio (solo SQL).
3. Método en el service con las reglas; lanza `NoEncontrado` (404), `NoAutorizado` (403), `Conflicto` (409) o `ReglaNegocio` (422).
4. Router delgado: valida, autoriza por rol, llama al service. El manejador global arma `{"error": {"codigo","mensaje","detalles"}}`.
5. `python scripts/export_openapi.py` si cambió la API.

Cada épica tiene su propio archivo por capa (evita conflictos); respeta la propiedad de archivos de tu integrante.
