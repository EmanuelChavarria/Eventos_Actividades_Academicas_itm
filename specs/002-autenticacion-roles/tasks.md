---
description: "Tareas atómicas para implementar E2 — Autenticación, roles y autorización"
---

# Tareas: Autenticación, roles y autorización (E2)

- **Rama:** `002-autenticacion-roles` · **Responsable:** Integrante A
- **Entradas:** [spec.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/002-autenticacion-roles/spec.md), [plan.md](file:///c:/Users/Chava/Desktop/Proyecto-4/Proyecto_final4/specs/002-autenticacion-roles/plan.md)
- **Regla de oro:** **1 tarea = 1 commit atómico** en Conventional Commits en español (`tipo(alcance): descripción`, ≤ 72 caracteres). Marca la tarea `[x]` en este archivo dentro del mismo commit.
- **Pruebas primero:** para documento duplicado, hash/tiempo constante, bloqueo tras 10 intentos fallidos, JWT, permisos 401/403, usuario inactivo y CSRF, escribe primero las pruebas `pytest` en rojo y luego la implementación (rojo → verde).

## Convención de formato

`- [ ] T-002-XX [P?] [US?] Descripción concreta con ruta exacta · Commit: \`tipo(alcance): descripción\` · Terminado cuando: [criterio verificable]`

---

## Fase 1: Pruebas primero para reglas críticas (Rojo)

- [x] T-002-01 [US1] [US2] Crear pruebas iniciales rojo en `tests/test_auth.py` (registro válido + normalización de documento, 409 `DOCUMENTO_DUPLICADO`, mismo número con distinto tipo, correo repetido permitido, 422 sin `input` y rechazo de campos extra como `rol`, login con cookie `HttpOnly`/`SameSite=lax`/`Secure`/`Max-Age=3600`, 401 uniforme en documento inexistente/clave inválida/inactivo, bloqueo 429 tras 10 fallos y reinicio en login exitoso, `GET /api/v1/auth/yo`, `POST /api/v1/auth/logout` 204) · Commit: `test(auth): agrega pruebas rojo de registro, login, logout y rate limit` · Terminado cuando: las pruebas existen y fallan por falta de implementación en E2
- [x] T-002-02 [P] [US3] Crear pruebas iniciales rojo en `tests/test_permisos.py` (`get_current_user_optional`, `get_current_user` 401 sin cookie / cookie expirada / alterada / usuario inactivo, `require_roles` 403 con rol insuficiente y 200 con rol autorizado, defensa CSRF `Origin`/`Referer` 403 ante origen inválido o ausente con cookie y redirección `303` hacia `/login` en dependencias web protegidas) · Commit: `test(auth): agrega pruebas rojo de sesion, roles y proteccion csrf` · Terminado cuando: las pruebas existen y fallan por ausencia de implementación en `deps.py` y `security.py`

---

## Fase 2: Seguridad base, schemas, repositorio y servicio (US1 + US2)

**Objetivo:** Poner en pie la capa `core/security.py`, validación única de documentos, schemas Pydantic, repositorio SQLAlchemy y servicio de negocio sin importar FastAPI.
**Prueba independiente:** Pruebas de hashing, JWT, rate limit y registro/autenticación en `tests/test_auth.py` pasan en verde al completar endpoints.

- [x] T-002-03 [US1] [US2] Implementar `app/core/security.py` (hash/verificación `argon2id` con `HASH_FICTICIO_TIMING`, `crear_token_acceso`/`decodificar_token_acceso` JWT `HS256`, `ControlIntentosLogin` 10 fallos / 900 s, `es_origen_confiable`, `normalizar_y_validar_documento`, constante `NOMBRE_COOKIE_SESION`) y reutilizar `normalizar_y_validar_documento` en `scripts/crear_usuario.py` sin duplicación · Commit: `feat(auth): agrega utilidades argon2id, jwt, rate limit y documento` · Terminado cuando: todas las funciones de `security.py` y `tests/test_scripts_web.py` funcionan sin duplicar validación de documento
- [x] T-002-04 [P] [US1] [US2] Definir schemas `RegistroEntrada`, `LoginEntrada` (`extra="forbid"`, normalización de documento según RN-14, correo `EmailStr`, contraseña ≥ 8) y `UsuarioSalida` (sin `hash_password`) en `app/schemas/auth.py` · Commit: `feat(auth): agrega schemas de registro, login y usuario publico` · Terminado cuando: entradas válidas se normalizan y entradas inválidas o campos extra lanzan validación Pydantic
- [x] T-002-05 [P] [US1] [US2] Implementar `app/repositories/usuario_repo.py` (`obtener_por_id`, `obtener_por_documento`, `crear`) usando SQLAlchemy 2.x · Commit: `feat(auth): implementa repositorio de usuarios` · Terminado cuando: las consultas e inserciones sobre `usuarios` operan exclusivamente en el repositorio
- [x] T-002-06 [US1] [US2] Implementar `app/services/auth_service.py` (`registrar_participante` forzando `Rol.PARTICIPANTE` y traduciendo duplicado / `IntegrityError` a `409 DOCUMENTO_DUPLICADO`; `autenticar_usuario` con verificación en tiempo constante, control de `activo`, verificación y actualización de `ControlIntentosLogin`; `obtener_usuario_activo`) sin importar FastAPI · Commit: `feat(auth): implementa servicios de registro y autenticacion` · Terminado cuando: las reglas RN-13, RN-14, RN-21 y verificación en tiempo constante están implementadas en `services/`

---

## Fase 3: Endpoints REST y dependencias de autorización/CSRF (US1 + US2 + US3)

**Objetivo:** Conectar `/api/v1/auth/*` y completar `app/api/deps.py`, `app/api/router.py` y `app/core/errors.py` para dejar en verde `test_auth.py` y `test_permisos.py`.
**Prueba independiente:** `pytest tests/test_auth.py tests/test_permisos.py` 100 % en verde.

- [x] T-002-07 [US1] [US2] Implementar en `app/api/v1/auth.py` los endpoints `POST /registro` (`201`), `POST /login` (`200` + cookie `HttpOnly`/`SameSite=lax`/`Path=/`/`Max-Age=3600`/`Secure`), `POST /logout` (`204` borrando cookie) y `GET /yo` (`200`) · Commit: `feat(auth): expone endpoints de registro, login, logout y yo` · Terminado cuando: todos los casos de `tests/test_auth.py` pasan en verde (excepto vistas web de T-002-09)
- [x] T-002-08 [US3] Completar `get_current_user_optional` en `app/api/deps.py`, agregar `verificar_csrf` (exigiendo `Origin` o respaldo `Referer` en mutaciones con cookie) aplicada globalmente en `app/api/router.py`, y añadir `require_web_user`/`require_web_roles` con `RequiereLoginWeb` en `app/core/errors.py` (`303 -> /login`) y actualizar `docs/diseno.md` · Commit: `feat(auth): completa dependencias de sesion, roles y defensa csrf` · Terminado cuando: todos los casos de `tests/test_permisos.py` pasan en verde sin romper rutas públicas ni `GET /health`

---

## Fase 4: Vistas web, navegación y cierre documental (US4 + PF-09)

**Objetivo:** Entregar las páginas `/login` y `/registro` (Jinja2 + `auth.js`), cierre de sesión global en `api.js` / `base.html`, documentación base de PF-09 y verificación integral E2.
**Prueba independiente:** Flujo en navegador sobre HTTPS (`https://localhost:8000/registro` → `/login` → navegación por rol → cerrar sesión) y suite `ruff` + `pytest` en verde.

- [x] T-002-09 [US4] Implementar rutas `GET /login` y `GET /registro` en `app/web/auth.py` (con redirección `303` a `/` si ya existe sesión), plantillas `app/templates/auth/login.html` y `app/templates/auth/registro.html` y módulo `app/static/js/auth.js` (`fetch` a `/api/v1/auth/*` con `redireccion401: false` y alertas con `textContent`) · Commit: `feat(web): agrega vistas de inicio de sesion y registro` · Terminado cuando: `GET /login` y `GET /registro` responden `200` sin sesión, `303` con sesión y envían formularios vía JS seguro
- [x] T-002-10 [US4] Conectar `#btn-cerrar-sesion` en `app/static/js/api.js` (`POST /api/v1/auth/logout` y redirección a `/login`) y verificar/ampliar pruebas web de navegación condicional por rol en `app/templates/base.html` y `tests/test_auth.py` · Commit: `feat(web): conecta cierre de sesion y valida navegacion por rol` · Terminado cuando: cada rol muestra únicamente sus enlaces esperados y cerrar sesión invoca `/api/v1/auth/logout`
- [x] T-002-11 [US3] Documentar casos base de **PF-09** (acceso sin sesión `401`, rol insuficiente `403`, redirección web a `/login` y CSRF) en `docs/pruebas/PF-09.md` · Commit: `docs(pruebas): documenta casos iniciales de autorizacion PF-09` · Terminado cuando: `docs/pruebas/PF-09.md` recoge pasos, datos ficticios, resultados esperados/obtenidos y trazabilidad con `RF-03`/`RNF-06`
- [x] T-002-12 Ejecutar verificación integral de E2 (`ruff check .`, `ruff format --check .`, `pytest -q`, prueba manual HTTPS de `/docs`, `/login` y `/registro`), actualizar estados en `specs/002-autenticacion-roles/tasks.md` y exportar `specs/contrato/openapi.json` si el script ya está disponible · Commit: `docs(specs): marca tareas verificadas de E2 tras pruebas en verde` · Terminado cuando: `ruff` y toda la suite `pytest -q` pasan con 0 errores y el PR queda listo para revisión G4/G5

---

## Tabla resumen de trazabilidad

| ID | Tarea | Depende de | Archivos clave | Commit sugerido | Terminado cuando | Estado |
|---|---|---|---|---|---|:-:|
| T-002-01 | Pruebas rojo auth (`registro`, `login`, `logout`, `yo`, `429`) | — | `tests/test_auth.py` | `test(auth): agrega pruebas rojo de registro, login, logout y rate limit` | Pruebas fallan antes del código | [x] |
| T-002-02 | Pruebas rojo permisos (`401`, `403`, `activo`, CSRF, web) | — | `tests/test_permisos.py` | `test(auth): agrega pruebas rojo de sesion, roles y proteccion csrf` | Pruebas fallan antes del código | [x] |
| T-002-03 | `security.py` + reúso documento en `crear_usuario.py` | T-002-01, T-002-02 | `app/core/security.py`, `scripts/crear_usuario.py` | `feat(auth): agrega utilidades argon2id, jwt, rate limit y documento` | Hashing, JWT, rate limit y doc listos | [x] |
| T-002-04 | Schemas `RegistroEntrada`, `LoginEntrada`, `UsuarioSalida` | T-002-03 | `app/schemas/auth.py` | `feat(auth): agrega schemas de registro, login y usuario publico` | `extra="forbid"` y sin `hash_password` | [x] |
| T-002-05 | Repositorio `usuario_repo.py` | T-002-01 | `app/repositories/usuario_repo.py` | `feat(auth): implementa repositorio de usuarios` | Consultas SQLite encapsuladas | [x] |
| T-002-06 | Servicio `auth_service.py` sin FastAPI | T-002-03, T-002-04, T-002-05 | `app/services/auth_service.py` | `feat(auth): implementa servicios de registro y autenticacion` | RN-13/14/21 y tiempo constante OK | [x] |
| T-002-07 | Router `/api/v1/auth` (`registro`, `login`, `logout`, `yo`) | T-002-06 | `app/api/v1/auth.py` | `feat(auth): expone endpoints de registro, login, logout y yo` | `test_auth.py` API en verde | [x] |
| T-002-08 | `deps.py`, `verificar_csrf` en `router.py`, `errors.py`, `diseno.md` | T-002-03, T-002-05 | `app/api/deps.py`, `app/api/router.py`, `app/core/errors.py`, `docs/diseno.md` | `feat(auth): completa dependencias de sesion, roles y defensa csrf` | `test_permisos.py` en verde | [x] |
| T-002-09 | Vistas `/login`, `/registro`, templates y `auth.js` | T-002-07, T-002-08 | `app/web/auth.py`, `app/templates/auth/*`, `app/static/js/auth.js` | `feat(web): agrega vistas de inicio de sesion y registro` | HTML `200`/`303` y `fetch` sin `innerHTML` | [x] |
| T-002-10 | Logout en `api.js` y verificación navegación por rol | T-002-08, T-002-09 | `app/static/js/api.js`, `tests/test_auth.py` | `feat(web): conecta cierre de sesion y valida navegacion por rol` | Logout UI y menú por rol verificados | [x] |
| T-002-11 | Documentación base `PF-09` | T-002-08 | `docs/pruebas/PF-09.md` | `docs(pruebas): documenta casos iniciales de autorizacion PF-09` | Casos `401`/`403` documentados | [x] |
| T-002-12 | Verificación final `ruff`, `pytest`, `/docs` y `tasks.md` | T-002-10, T-002-11 | `specs/002-autenticacion-roles/tasks.md` | `docs(specs): marca tareas verificadas de E2 tras pruebas en verde` | `ruff` y `pytest -q` 100% verdes | [x] |
