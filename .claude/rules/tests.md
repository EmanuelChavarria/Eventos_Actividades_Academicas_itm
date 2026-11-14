---
paths:
  - "tests/**/*.py"
---

# Reglas para `tests/` (pytest)

- **Primero la prueba:** para cupo, duplicados, permisos y seguridad escribe la prueba que falla y luego la implementación (rojo → verde).
- **Aislamiento:** BD SQLite en **archivo temporal** (`tmp_path`, no `:memory:` para soportar hilos reales), creada desde los modelos con `PRAGMA foreign_keys=ON`, `get_db` sobrescrito y `TestClient`; nunca la BD de desarrollo ni datos reales. Fábricas por rol (participante, organizador, coordinación) en `tests/conftest.py` (dueño: A).
- **Datos ficticios:** documentos obviamente falsos; nada de contraseñas reales.
- **Qué debe existir (mínimo):**
  - `test_permisos.py` (A): 401 sin sesión o usuario inactivo, 403 por rol, propietario ajeno, rechazo CSRF por `Origin` externo en mutación con cookie, 422 sin `input` sensible.
  - `test_auth.py` (A): `DOCUMENTO_DUPLICADO` 409, mismo número con otro tipo permitido, correo repetido permitido, login con documento, rechazo de fecha sin zona (422), límite de 10 intentos fallidos en login (429 `DEMASIADOS_INTENTOS`).
  - `test_inscripciones.py` (B): válida, cupo agotado 409 `CUPO_AGOTADO`, duplicado 409 `INSCRIPCION_DUPLICADA`, cancelar y reinscribir, solicitudes simultáneas con hilos (`BEGIN IMMEDIATE`) y cupo 1 → exactamente 1 éxito.
  - `test_asistencia.py` (B): permisos y ventana (antes del inicio o después de 48 h de `fecha_fin` → 409).
  - `test_reportes.py` (B): solo coordinación; totales = suma del detalle; documento enmascarado.
- **Fechas:** inyectar el reloj («ahora») y probar los límites en UTC (fecha límite, inicio, ventana de 48 h).
- **Nombres:** `test_<regla>_<resultado_esperado>`, en español `snake_case`. Cada prueba referencia su RF/RN en el docstring.
- **Ejecución:** `pytest -q`; un PR no se fusiona con pruebas en rojo.
