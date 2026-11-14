---
paths:
  - "app/**/*.py"
---

# Reglas para `app/` (FastAPI)

Fuente: `AGENTS.md` §4 y constitución (principios II–VII).

- **Capas:** `api` → `services` → `repositories` → `models`. Los routers solo validan (Pydantic), invocan un service y dejan que el manejador global traduzca `ErrorDominio` a HTTP. Sin reglas de negocio ni SQL en routers. Los services **no importan FastAPI**. Solo `repositories/` escribe SQL.
- **SQLite y cupo atómico:** configurar `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000` por conexión. Alta de inscripción dentro de una transacción iniciada con `BEGIN IMMEDIATE` usando una sola sentencia condicionada al cupo (`rowcount`); el índice único parcial cubre el duplicado en carrera. El cupo disponible se calcula, no se guarda.
- **Autorización y sesiones activas:** cada endpoint usa `require_roles(...)` **y** verifica propietario (organizador solo sus eventos; participante solo lo propio; coordinación solo lectura). `app/web/` protege páginas con `get_current_user_optional` redirigiendo a `/login`. Verificar `usuario.activo == True` al autenticar y en `get_current_user`.
- **Autenticación y CSRF:** contraseñas con **argon2id**; login con verificación en tiempo constante (hash ficticio si no existe el documento) y **límite de 10 intentos fallidos** (429 `DEMASIADOS_INTENTOS`). JWT `HS256` con `sub = usuario.id` (nunca documento ni correo), validando `SECRET_KEY` al arrancar (fallar si está vacía, es corta o igual a `.env.example`). Cookie `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600`, `Secure` obligatorio (HTTPS en todos los entornos; la app falla al arrancar si `COOKIE_SECURE` no es `true`). La app se sirve solo por HTTPS en todos los entornos. Validar `Origin`/`Referer` del mismo origen en POST/PUT/PATCH con cookie.
- **Schemas y SQL seguro:** entrada y salida separados; nunca exponer `hash_password`. Escapar comodines (`%`, `_`) en filtros `LIKE`.
- **Errores sin fuga de datos:** `{"error": {"codigo", "mensaje", "detalles"}}`. Manejadores globales para `ErrorDominio`, `RequestValidationError` (omitiendo el campo `input`) y `HTTPException`. Sin trazas ni datos sensibles.
- **Identificación y privacidad:** `tipo_documento` + `numero_documento` normalizados (sin espacios ni puntos; PAS en mayúsculas); duplicado → 409 `DOCUMENTO_DUPLICADO`. El correo no es único. El documento nunca va en logs (tampoco cuerpos de petición ni cabeceras `Cookie`/`Authorization`) ni en errores; coordinación lo ve enmascarado (`••••1234`). En CSV opcional, enmascarar documento y neutralizar fórmulas (`=`, `+`, `-`, `@`).
- **Fechas:** UTC garantizado en BD (`TypeDecorator`); la API rechaza fechas sin zona (422) y usa ISO-8601 con zona; conversión a `America/Bogota` solo en presentación (`app/core/fechas.py`, con `tzdata`). El reloj actual («ahora») debe ser inyectable para pruebas.
- **Frontend:** `app/web/` y `templates/` solo renderizan el esqueleto Jinja2; los datos llegan por `fetch` a `/api/v1` desde `static/js/`.
- **Estilo y propiedad:** nombres de dominio en español `snake_case`, type hints, funciones cortas, `ruff check . && ruff format .` antes de cada commit. Edita solo los archivos de tu integrante.
