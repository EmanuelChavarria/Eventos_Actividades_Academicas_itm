# Plan de Implementación: Autenticación, roles y autorización (E2)

**Rama:** `002-autenticacion-roles` | **Fecha:** 2026-11-14 | **Spec:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/002-autenticacion-roles/spec.md)
**Entrada:** Especificación aprobada en G1 en `specs/002-autenticacion-roles/spec.md` (sin `[PENDIENTE]` bloqueantes).

## 1. Resumen y decisiones técnicas

El objetivo de E2 es habilitar registro público de participantes, inicio/cierre de sesión con cookie JWT segura sobre HTTPS, verificación de identidad actual (`GET /api/v1/auth/yo`), autorización por rol y estado activo en API/web, protección CSRF y vistas web `/login` y `/registro`.

Decisiones principales y alternativas descartadas:
- **Cookie `HttpOnly` exclusiva (sin devolver JWT en el cuerpo JSON):** `POST /api/v1/auth/login` retorna `UsuarioSalida` en JSON (`200`) y entrega el JWT `HS256` únicamente mediante la cookie `pf04_session` (`httponly=True`, `samesite="lax"`, `path="/"`, `max_age=3600`, `secure=True`). *Descartado:* devolver `access_token` en el JSON y guardarlo en `localStorage`, por exposición a XSS y porque Swagger (`/docs`) en el mismo origen HTTPS envía la cookie automáticamente.
- **Defensa CSRF centralizada en `api_router` (`Origin` + respaldo `Referer`):** la dependencia `verificar_csrf` evalúa peticiones mutadoras (`POST`, `PUT`, `PATCH`, `DELETE`) cuando existe la cookie `pf04_session`, exigiendo `Origin` válido (o `Referer` como respaldo) contra `settings.ALLOWED_ORIGINS` y el origen HTTPS efectivo de la solicitud; ante ausencia de ambos o origen distinto responde `403 SIN_PERMISO`. *Descartado:* repetir comprobaciones CSRF manuales en cada router de E2–E7.
- **Limitador de intentos fallidos en memoria por `(ip_cliente, tipo_documento, numero_documento)`:** clase `ControlIntentosLogin` con `threading.Lock`, ventana de 900 s (15 min), máximo 10 fallos usando `ahora_utc()` inyectable y reinicio al autenticar con éxito. *Descartado:* bloquear solo por IP (afectaría redes universitarias detrás de NAT) o crear migración de BD innecesaria en E2.
- **Verificación en tiempo constante con hash ficticio (`HASH_FICTICIO_TIMING`):** cuando el documento no existe o `usuario.activo` es `False`, el servicio ejecuta igualmente `verificar_password` contra un hash `argon2id` precalculado antes de responder `401 CREDENCIALES_INVALIDAS`. *Descartado:* retorno temprano sin verificación, para no filtrar existencia de cuentas por tiempo de respuesta.
- **Normalización única compartida de documento (`normalizar_y_validar_documento`):** ubicar la regla de limpieza/validación de `CC`/`CE`/`TI`/`PAS` en `app/core/security.py` y reutilizarla desde `app/schemas/auth.py` y `scripts/crear_usuario.py` para evitar lógica duplicada. *Descartado:* mantener dos implementaciones paralelas.
- **Redirección web para páginas protegidas (`RequiereLoginWeb`):** definir una excepción dedicada capturada en `app/core/errors.py` para dependencias web (`require_web_user` / `require_web_roles`), de modo que vistas protegidas futuras (E3–E7) redirijan con `303 See Other` hacia `/login` sin sesión y respondan `403` con rol insuficiente. *Descartado:* duplicar condicionales `if not usuario: RedirectResponse` en cada ruta web.

## 2. Contexto técnico

- **Lenguaje / Versión:** Python 3.12 (`target-version = "py311"`).
- **Dependencias existentes aprovechadas (`requirements.txt`):** `argon2-cffi`, `PyJWT`, `pydantic` + `email-validator`, `fastapi`, `sqlalchemy`, `jinja2`. No se agregan nuevas dependencias externas.
- **Almacenamiento:** tabla existente `usuarios` en SQLite (`uq_usuarios_documento`, `CHECK` de tipo/longitud/rol/tipo_participante, `creado_en` en `UTCDateTime`). No requiere nuevas migraciones Alembic.
- **Pruebas:** `pytest` + `httpx` (`TestClient(base_url="https://testserver")`) sobre archivo SQLite temporal por prueba.
- **Restricciones:** Sin `innerHTML` en JS (`textContent` estricto); servicios sin importar `fastapi`; prohibido escribir contraseñas, tokens, cookies o `numero_documento` en logs o respuestas de error; mensajes y UI en español.

## 3. Verificación contra la constitución *(puerta obligatoria)*

Revisión frente a `.specify/memory/constitution.md` (v2.0.2):
- [x] I. La spec manda (`specs/002-autenticacion-roles/spec.md` aprobada en G1, sin `[PENDIENTE]`)
- [x] II. Capas estrictas (`api/v1/auth.py` → `services/auth_service.py` → `repositories/usuario_repo.py` → `models/usuario.py`; `auth_service.py` recibe `ip_cliente: str` sin importar FastAPI)
- [x] III. Validación en servidor (`RegistroEntrada`/`LoginEntrada` Pydantic v2 con `extra="forbid"`) y en BD (`uq_usuarios_documento`, `CHECK`)
- [x] IV. No modifica lógica de cupos (sin impacto en inscripciones atómicas)
- [x] V. Mínimo privilegio (`get_current_user` verifica `usuario.activo == True`, `require_roles` verifica rol en cada endpoint, `RN-21` fuerza `Rol.PARTICIPANTE` en registro público)
- [x] VI. Errores uniformes (`401 CREDENCIALES_INVALIDAS`, `403 SIN_PERMISO`, `409 DOCUMENTO_DUPLICADO`, `422 ERROR_VALIDACION` sin `input`, `429 DEMASIADOS_INTENTOS`) y sin documentos/tokens/contraseñas en logs
- [x] VII. Sin secretos ni datos reales (JWT firmado con `settings.SECRET_KEY` validada al arranque; pruebas usan documentos ficticios)
- [x] VIII. Commits atómicos en español en rama `002-autenticacion-roles`; PR en borrador al pasar G2
- [x] IX. `ruff` y `pytest` en verde antes de G4 (y `export_openapi.py` si aplica)
- [x] X. Compatible con ejecución local HTTPS y Docker sin dependencias nuevas ni pasos adicionales
- [x] XI. Respeta las firmas base del contrato compartido (`deps.py` mantiene firma y tipos de `get_current_user_optional`, `get_current_user` y `require_roles`; `scripts/crear_usuario.py` mantiene su interfaz pública)
- [x] XII. Clarificaciones cerradas con el humano antes de planificar (ventana/clave de 10 intentos, `204` en logout, CSRF estricto `Origin`/`Referer`, `extra="forbid"`)

## 4. Estructura y archivos por capa

```text
specs/002-autenticacion-roles/
├── spec.md              # Especificación aprobada (G1)
├── plan.md              # Este documento
├── checklists/
│   └── requirements.md  # Checklist de calidad de spec
└── tasks.md             # Tareas atómicas T-002-XX
```

| Capa / Ámbito | Archivos creados o modificados en E2 | Responsable |
|---|---|:-:|
| Core / Seguridad | `app/core/security.py`, `app/core/errors.py` (handler `RequiereLoginWeb`) | A |
| Scripts (reúso) | `scripts/crear_usuario.py` (reutiliza `normalizar_y_validar_documento` de `security.py`) | A |
| Schemas | `app/schemas/auth.py` (`RegistroEntrada`, `LoginEntrada`, `UsuarioSalida`) | A |
| Repositorio | `app/repositories/usuario_repo.py` (`obtener_por_id`, `obtener_por_documento`, `crear`) | A |
| Servicio | `app/services/auth_service.py` (`registrar_participante`, `autenticar_usuario`, `obtener_usuario_activo`) | A |
| API / Deps | `app/api/deps.py` (`get_current_user_optional`, `verificar_csrf`, `require_web_user`, `require_web_roles`), `app/api/router.py` (`dependencies=[Depends(verificar_csrf)]`), `app/api/v1/auth.py` | A |
| Web / Templates / JS | `app/web/auth.py` (`/login`, `/registro`), `app/templates/auth/login.html`, `app/templates/auth/registro.html`, `app/static/js/auth.js`, `app/static/js/api.js` (cierre de sesión en `#btn-cerrar-sesion`), `app/templates/base.html` (verificación enlaces/rol) | A |
| Docs | `docs/pruebas/PF-09.md` (documentación base de casos sin sesión/rol insuficiente; evidencias se completan en E3/E8-A) y actualización breve en `docs/diseno.md` si se añade `verificar_csrf` / `require_web_roles` al contrato | A |
| Pruebas | `tests/test_auth.py`, `tests/test_permisos.py` | A |

## 5. Contrato de API, modelo de datos y seguridad

- **Endpoints en `/api/v1/auth`:**
  - `POST /api/v1/auth/registro` → **201 Created** (`UsuarioSalida`) | errores `409 DOCUMENTO_DUPLICADO`, `422 ERROR_VALIDACION`.
  - `POST /api/v1/auth/login` → **200 OK** (`UsuarioSalida`) + `Set-Cookie: pf04_session=<jwt>; HttpOnly; Max-Age=3600; Path=/; SameSite=lax; Secure` | errores `401 CREDENCIALES_INVALIDAS`, `422 ERROR_VALIDACION`, `429 DEMASIADOS_INTENTOS`.
  - `POST /api/v1/auth/logout` → **204 No Content** + `Set-Cookie: pf04_session=""; Max-Age=0; ...` | error `403 SIN_PERMISO` si falla CSRF cuando hay cookie.
  - `GET /api/v1/auth/yo` → **200 OK** (`UsuarioSalida`) | error `401 CREDENCIALES_INVALIDAS` sin sesión válida o usuario inactivo.
- **Vistas web en `app/web/auth.py`:**
  - `GET /login` → `200 text/html` (`auth/login.html`) o `303 -> /` si ya hay usuario activo.
  - `GET /registro` → `200 text/html` (`auth/registro.html`) o `303 -> /` si ya hay usuario activo.
- **Modelo de datos:** sin cambios sobre `app/models/usuario.py` ni `migrations/`.
- **Seguridad y privacidad:**
  - `argon2id` con `PasswordHasher` + `HASH_FICTICIO_TIMING` cuando no exista usuario o esté inactivo.
  - `JWT HS256` con `sub = str(usuario.id)`, `iat`, `exp` (`3600 s`).
  - Límite de 10 fallos en 900 s por `(ip_cliente, tipo_documento, numero_documento)` con limpieza al login exitoso.
  - CSRF por `Origin` / respaldo `Referer` en todas las mutaciones `/api/v1` con cookie de sesión.

## 6. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Pruebas en `TestClient` (propio o futuro de Integrante B) ejecutando mutaciones con cookie sin cabecera `Origin` | Documentar `verificar_csrf` en `docs/diseno.md`; enviar `Origin: https://testserver` en pruebas con cookie y validar ambos escenarios (con origen válido y sin/mal origen) en `test_permisos.py` |
| Estado compartido en memoria del limitador de intentos entre casos `pytest` | Exponer método `control_intentos_login.reiniciar_todo()` y limpiarlo en fixture `autouse` o por prueba en `tests/test_auth.py` |
| Bucle de redirección a `/login` en frontend cuando `login` retorna `401` | Llamar a `requestApi("/auth/login", { method: "POST", body, redireccion401: false })` en `app/static/js/auth.js` |
| Duplicación de validación de documentos entre API y `scripts/crear_usuario.py` | Extraer `normalizar_y_validar_documento` en `app/core/security.py` y delegar desde `scripts/crear_usuario.py` |

## 7. Registro de complejidad

No hay excepciones ni violaciones a la constitución en este plan.
