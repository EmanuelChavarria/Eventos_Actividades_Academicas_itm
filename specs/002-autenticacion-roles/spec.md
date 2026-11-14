# Especificación de Feature: Autenticación, roles y autorización

- **Épica:** E2 · **Condiciones:** Transversal (`CA-01`, `CA-03`, `CA-05`, `CA-06`) · **Requisitos:** RF-01, RF-02, RF-03, RF-04 (complemento), RN-13, RN-14, RN-21, RNF-05, RNF-06, RNF-07, RNF-08, RNF-12, RNF-15
- **Rama de feature:** `002-autenticacion-roles` · **Creada:** 2026-11-14
- **Estado:** aprobada · **Responsable:** Integrante A
- **Entrada:** Descripción del usuario: `"E2 Autenticación, roles y autorización: registro de participantes, login con documento y cookie JWT segura, logout, /auth/yo, rate limit, CSRF Origin/Referer, dependencias get_current_user/require_roles y vistas /login y /registro"`

## 1. Objetivo y alcance

Identificar de forma segura a los usuarios mediante documento y contraseña, mantener su sesión con cookie `HttpOnly` firmada (JWT `HS256` sobre HTTPS obligatorio) y proteger cada endpoint de la API (`/api/v1`) y vista web según autenticación, estado activo y rol (`participante`, `organizador`, `coordinacion`).

Incluye dentro del alcance de E2:
- Utilidades de seguridad en `app/core/security.py`: hash y verificación en tiempo constante con `argon2id`, emisión y validación de JWT `HS256` (`sub = usuario.id`), validación CSRF por `Origin`/`Referer` para mutaciones con cookie y limitador de intentos fallidos de inicio de sesión.
- Normalización y validación compartida de documento (`tipo_documento` + `numero_documento`) reutilizable entre API y scripts.
- Schemas Pydantic v2 de entrada/salida de autenticación (`app/schemas/auth.py`), repositorio de usuarios (`app/repositories/usuario_repo.py`) y servicio de autenticación (`app/services/auth_service.py`).
- Endpoints bajo `/api/v1/auth`: `POST /registro`, `POST /login`, `POST /logout` y `GET /yo`.
- Implementación completa de las dependencias compartidas en `app/api/deps.py`: `get_current_user_optional`, `get_current_user`, `require_roles` y dependencia de protección CSRF para mutaciones con cookie, además de helpers para rutas web protegidas.
- Vistas web públicas `/login` y `/registro` (esqueleto Jinja2 + módulo `app/static/js/auth.js` con `fetch` y `textContent`), navegación condicional por rol en `app/templates/base.html` y acción del botón «Cerrar sesión» en `app/static/js/api.js`.
- Pruebas automatizadas en `tests/test_auth.py` y `tests/test_permisos.py`.

## 2. Fuera de alcance

- Recuperación o restablecimiento de contraseña por correo o token (decisión aprobada: fuera de alcance).
- Auto-registro público de cuentas `organizador` o `coordinacion` (solo mediante `scripts/crear_usuario.py` y `scripts/seed.py`).
- Gestión administrativa de cuentas (activar/desactivar usuarios, cambio de rol o perfil avanzado).
- Autenticación externa (OAuth2, SSO institucional), doble factor (MFA) o lectura de QR.
- Endpoints y lógica de negocio de eventos (E3), catálogo completo (E4), inscripciones (E5), asistencia (E6) y consolidado (E7).

## 3. Historias de usuario y criterios de aceptación *(obligatorio)*

### Historia de Usuario 1 - Registro público de participantes (Prioridad: P1)

Como participante (estudiante o docente), quiero registrarme ingresando mi tipo y número de documento, nombre, correo de contacto, tipo de participante y contraseña para poder autenticarse posteriormente e inscribirse en actividades.

- **Por qué esta prioridad:** Es el punto de entrada de nuevos participantes (`RF-01`) y garantiza desde el origen las reglas de identificación única (`RN-13`, `RN-14`) y rol restringido (`RN-21`).
- **Prueba independiente:** Invocar `POST /api/v1/auth/registro` con datos válidos, duplicados e inválidos contra una BD temporal y verificar código HTTP, respuesta JSON y fila creada en `usuarios`.
- **Escenarios de aceptación:**
  1. **Dado** que no existe un usuario con `(tipo_documento='CC', numero_documento='1001234567')`, **Cuando** se envía `POST /api/v1/auth/registro` con `tipo_documento="CC"`, `numero_documento="1.001 234.567"`, `nombre`, `correo`, `tipo_participante="estudiante"` y `password` de al menos 8 caracteres, **Entonces** retorna **201 Created** con el usuario público (`rol="participante"`, `activo=True`, `numero_documento="1001234567"` normalizado y sin `hash_password`), y queda persistido en `usuarios` con contraseña cifrada en `argon2id`.
  2. **Dado** que ya existe un usuario con `('CC', '1001234567')`, **Cuando** se intenta registrar otro participante con `('CC', '1001234567')` (incluso enviándolo con puntos o espacios), **Entonces** retorna **409 Conflict** con código `DOCUMENTO_DUPLICADO` y no crea ningún registro adicional.
  3. **Dado** que ya existe un usuario con `('CC', '1001234567')` y correo `ana@example.edu`, **Cuando** se registra otro participante con `('CE', '1001234567')` o con el mismo correo `ana@example.edu` y otro documento distinto, **Entonces** retorna **201 Created** y persiste la nueva cuenta (el documento identifica por par `(tipo, numero)` y el correo no es único).
  4. **Dado** datos inválidos (contraseña < 8 caracteres, correo con formato inválido, `CC/CE/TI` con letras o longitud fuera de 5–12, `PAS` fuera de 5–15 alfanuméricos o `tipo_participante` inválido), **Cuando** se envía `POST /api/v1/auth/registro`, **Entonces** retorna **422 Unprocessable Entity** con formato uniforme de error sin campo `input` ni creación en BD.

---

### Historia de Usuario 2 - Inicio, consulta y cierre de sesión con cookie segura (Prioridad: P1)

Como usuario registrado (participante, organizador o coordinación), quiero iniciar sesión con mi documento y contraseña para obtener una cookie de sesión segura, consultar mi identidad actual en `/api/v1/auth/yo` y cerrar sesión cuando termine.

- **Por qué esta prioridad:** Habilita la autenticación transversal (`RF-02`) requerida por E3–E7 y garantiza pruebas manuales en `/docs` (Swagger) usando la cookie de sesión.
- **Prueba independiente:** Ejecutar flujo completo `login -> GET /auth/yo -> logout -> GET /auth/yo` en cliente HTTPS verificando cabecera `Set-Cookie`, firma JWT, bloqueo tras 10 fallos e invalidación al cerrar sesión.
- **Escenarios de aceptación:**
  1. **Dado** un usuario activo existente, **Cuando** envía `POST /api/v1/auth/login` con `tipo_documento`, `numero_documento` (se normaliza igual que en registro) y contraseña correcta, **Entonces** retorna **200 OK** con los datos públicos del usuario (`UsuarioSalida`) y fija la cookie de sesión JWT (`HS256`, `sub=str(usuario.id)`) con atributos `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600` y `Secure`.
  2. **Dado** un documento inexistente, un usuario con `activo=False` o una contraseña incorrecta, **Cuando** envía `POST /api/v1/auth/login`, **Entonces** ejecuta verificación en tiempo constante (incluyendo hash ficticio cuando el documento no existe) y retorna **401 Unauthorized** con código `CREDENCIALES_INVALIDAS` sin indicar si falló el documento, el estado o la contraseña.
  3. **Dado** 10 intentos fallidos consecutivos por `(ip_cliente, tipo_documento, numero_documento)` dentro de una ventana de 15 minutos (900 s), **Cuando** se realiza el intento número 11, **Entonces** retorna **429 Too Many Requests** con código `DEMASIADOS_INTENTOS` sin permitir autenticar durante el periodo de bloqueo (el contador se reinicia tras un login exitoso).
  4. **Dado** un cliente con cookie de sesión válida y activa, **Cuando** consulta `GET /api/v1/auth/yo`, **Entonces** retorna **200 OK** con la información pública del usuario autenticado; si la cookie falta, expiró, está alterada o el usuario está inactivo, retorna **401 Unauthorized** (`CREDENCIALES_INVALIDAS`).
  5. **Dado** un cliente autenticado con origen permitido, **Cuando** envía `POST /api/v1/auth/logout`, **Entonces** elimina la cookie de sesión (`Max-Age=0` / expirada con los mismos atributos de ruta y seguridad), retorna **204 No Content** y una consulta posterior a `GET /api/v1/auth/yo` retorna **401 Unauthorized**.

---

### Historia de Usuario 3 - Autorización por rol, estado activo y protección CSRF (Prioridad: P1)

Como sistema, quiero exponer dependencias reutilizables de autenticación, autorización por rol y validación CSRF por origen para que todos los endpoints protegidos y páginas restringidas apliquen mínimo privilegio de forma uniforme.

- **Por qué esta prioridad:** Protege todas las operaciones de negocio (`RF-03`, `RNF-05`, `RNF-06`) y desbloquea los routers de E3–E7 manteniendo el contrato de `app/api/deps.py`.
- **Prueba independiente:** Probar rutas protegidas (y/o endpoints de verificación con `get_current_user` y `require_roles`) con sesión ausente, usuario inactivo, rol insuficiente, rol permitido y mutación con cookie desde origen no autorizado.
- **Escenarios de aceptación:**
  1. **Dado** una petición sin cookie o con cookie JWT expirada/inválida/de usuario inactivo hacia un endpoint protegido por `get_current_user` o `require_roles`, **Cuando** se procesa la solicitud, **Entonces** retorna **401 Unauthorized** con código `CREDENCIALES_INVALIDAS`.
  2. **Dado** un usuario autenticado cuyo rol no pertenece al conjunto autorizado en `require_roles(...)`, **Cuando** invoca un endpoint restringido a otro rol, **Entonces** retorna **403 Forbidden** con código `SIN_PERMISO`.
  3. **Dado** un usuario autenticado cuyo rol sí está autorizado y `activo=True`, **Cuando** invoca el endpoint permitido, **Entonces** la dependencia entrega la instancia `Usuario` y permite continuar.
  4. **Dado** una petición mutadora (`POST`, `PUT`, `PATCH`, `DELETE`) hacia `/api/v1` con cookie de sesión activa cuyo encabezado `Origin` (o `Referer` como respaldo cuando `Origin` esté ausente) falte o no coincida con los orígenes confiables configurados o el origen HTTPS efectivo de la solicitud, **Cuando** se evalúa la defensa CSRF, **Entonces** rechaza la operación con **403 Forbidden** (`SIN_PERMISO`).

---

### Historia de Usuario 4 - Vistas web de login, registro y navegación por rol (Prioridad: P2)

Como usuario del sistema, quiero acceder a páginas `/login` y `/registro` claras y seguras, ver en la barra superior las opciones acordes a mi rol y cerrar sesión desde el botón de la interfaz.

- **Por qué esta prioridad:** Completa la experiencia web sobre el esqueleto Jinja2 + `fetch` a `/api/v1` definido en `RF-27` y `RNF-12` manteniendo `textContent` estricto.
- **Prueba independiente:** Renderizar `GET /login` y `GET /registro`, verificar redirección si ya hay sesión activa, comprobar atributos de accesibilidad de los formularios, presencia de scripts JS (`auth.js`, `api.js`) y navegación diferenciada por rol en `base.html`.
- **Escenarios de aceptación:**
  1. **Dado** un visitante sin sesión, **Cuando** abre `GET /login` o `GET /registro`, **Entonces** recibe **200 OK** con HTML válido que extiende `base.html` y carga `auth.js` sin renderizar lógica ni mensajes sensibles desde el servidor.
  2. **Dado** un usuario ya autenticado, **Cuando** solicita `GET /login` o `GET /registro`, **Entonces** es redirigido (**303 See Other**) a `/`.
  3. **Dado** la navegación en `base.html` para cada rol autenticado (`participante`, `organizador`, `coordinacion`), **Cuando** carga cualquier página web, **Entonces** solo observa los enlaces permitidos para su rol, su nombre y rol visibles y el botón «Cerrar sesión» conectado a `POST /api/v1/auth/logout`.
  4. **Dado** el envío de formulario en `/login` o `/registro` desde el navegador, **Cuando** la API responde error (401, 409, 422 o 429), **Entonces** el módulo JS muestra el mensaje en `#alerta-global` mediante `mostrarAlerta` (`textContent`, nunca `innerHTML`) sin redirigir en bucle ante 401 durante el login.

---

## 4. Reglas de negocio y validaciones

- **RN-13 (Identificación única y correo de contacto):**
  - El usuario se identifica únicamente por `(tipo_documento, numero_documento)`, garantizado en servicio (`usuario_repo.obtener_por_documento` + manejo de `IntegrityError`) y en BD (`UNIQUE(tipo_documento, numero_documento)` `uq_usuarios_documento`). Un duplicado produce **409 `DOCUMENTO_DUPLICADO`**.
  - El campo `correo` es obligatorio, con formato válido (`email-validator` / Pydantic `EmailStr`), pero **no es único** ni se usa como credencial de acceso.
- **RN-14 (Normalización y formato del documento):**
  - Se eliminan espacios en blanco y puntos (`.`) antes de validar y guardar.
  - Para `CC`, `CE` y `TI`: solo dígitos (`^\d{5,12}$`, longitud 5–12).
  - Para `PAS`: convertido a mayúsculas, solo alfanumérico (`^[A-Z0-9]{5,15}$`, longitud 5–15).
  - Respaldo en BD: restricciones `CHECK` `ck_usuarios_tipo_doc` y `ck_usuarios_doc_len`. La función de normalización/validación debe ser única y compartida para evitar duplicación con `scripts/crear_usuario.py`.
- **RN-21 (Registro exclusivo de participantes):**
  - `POST /api/v1/auth/registro` crea únicamente usuarios con `rol = Rol.PARTICIPANTE` y exige `tipo_participante` (`estudiante` o `docente`).
  - Las cuentas de `organizador` y `coordinacion` se crean únicamente por `scripts/crear_usuario.py` y `scripts/seed.py`.
- **Validaciones de entrada y salida (Pydantic v2):**
  - `RegistroEntrada` (`extra="forbid"` para rechazar campos no autorizados como `rol` con `422 ERROR_VALIDACION`): `tipo_documento` (`TipoDocumento`), `numero_documento` (`str` normalizado y validado según RN-14), `nombre` (`str` recortado, 2–120 caracteres), `correo` (`EmailStr`, máx. 150 caracteres), `tipo_participante` (`TipoParticipante`), `password` (`str`, mínimo 8 caracteres, máximo 128).
  - `LoginEntrada` (`extra="forbid"`): `tipo_documento` (`TipoDocumento`), `numero_documento` (`str` normalizado y validado según RN-14), `password` (`str`, mínimo 1 carácter).
  - `UsuarioSalida`: `id`, `tipo_documento`, `numero_documento`, `nombre`, `correo`, `tipo_participante`, `rol`, `activo`, `creado_en` (ISO-8601 UTC/con zona). Nunca expone `hash_password`.
- **Entidades clave afectadas:** Tabla existente `usuarios` (no requiere nuevas columnas ni migraciones en E2).

## 5. Errores esperados *(obligatorio)*

Formato uniforme de respuesta: `{"error": {"codigo": "...", "mensaje": "...", "detalles": []}}`.

| HTTP | Código de dominio | Cuándo ocurre | Notas de seguridad |
|---|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | Documento inexistente, contraseña inválida, usuario inactivo, ausencia de sesión o token JWT inválido/expirado | Mensaje genérico; verificación en tiempo constante con hash ficticio; sin indicar qué campo falló |
| 403 | `SIN_PERMISO` | Rol insuficiente en `require_roles` o cabecera `Origin`/`Referer` inválida en mutación con cookie | Sin detalles internos de permisos ni valores sensibles |
| 409 | `DOCUMENTO_DUPLICADO` | Registro con `(tipo_documento, numero_documento)` ya existente | No exponer el documento completo ni datos del usuario existente |
| 422 | `ERROR_VALIDACION` | Error de esquema Pydantic o formato inválido de documento, correo, contraseña o tipo de participante | Manejador global omite campo `input` para no filtrar contraseñas ni documentos |
| 429 | `DEMASIADOS_INTENTOS` | Superar 10 intentos fallidos en `POST /api/v1/auth/login` en la ventana de 15 min | Mensaje uniforme sin revelar si el documento existe |

## 6. Seguridad, privacidad y zona horaria aplicables

- **Almacenamiento de contraseñas y sesiones (`RNF-05`):**
  - Contraseñas cifradas con `argon2id` (`argon2.PasswordHasher`).
  - Verificación de contraseña ejecutada siempre en `login` usando un hash ficticio precalculado cuando el usuario no existe o está inactivo (tiempo constante).
  - JWT firmado con algoritmo `HS256` usando `settings.SECRET_KEY`; payload mínimo con `sub = str(usuario.id)`, `iat` y `exp` (`ACCESS_TOKEN_EXPIRE_SECONDS = 3600` segundos = 60 min).
  - Cookie de sesión configurada con `httponly=True`, `samesite="lax"`, `path="/"`, `max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS` y `secure=settings.COOKIE_SECURE` (`True` obligatorio). Nunca se devuelve el token en el cuerpo JSON.
- **Autorización y mínimo privilegio (`RNF-06`):**
  - Toda dependencia protegida verifica `usuario is not None and usuario.activo`.
  - En vistas web protegidas (helper reutilizable para E3–E7), si no hay sesión se redirige a `/login` (`303`), y si el rol es insuficiente responde `403`.
- **Defensa CSRF:**
  - Mutaciones (`POST`, `PUT`, `PATCH`, `DELETE`) en `/api/v1` cuando existe cookie de sesión exigen encabezado `Origin` válido (o `Referer` válido como respaldo si `Origin` no viene en la petición) contra los orígenes confiables (`settings.ALLOWED_ORIGINS` y el origen HTTPS efectivo de la solicitud); si faltan ambos o difieren, se rechaza con **403 `SIN_PERMISO`**.
- **Privacidad y logs (`RNF-15`):**
  - Prohibido escribir contraseñas, tokens JWT, cookies o `numero_documento` en logs o respuestas de error.
  - Los esquemas de respuesta públicos nunca incluyen `hash_password`.
- **Frontend seguro (`RF-27`, `RNF-12`):**
  - Formularios `/login` y `/registro` con etiquetas `<label>` accesibles, validación HTML5 complementada por el servidor, módulo JS dedicado `app/static/js/auth.js` y uso exclusivo de `textContent` / `crearNodo` (prohibido `innerHTML` con datos de API o usuario).
- **Fechas:** `creado_en` en `UsuarioSalida` conserva zona UTC almacenada por `UTCDateTime` y se muestra en `America/Bogota` desde JS cuando aplique.

## 7. Casos límite

- Documento ingresado en registro o login con espacios o puntos (ej. `" 1.001 234.567 "` o `" ab12345 "` en `PAS`): se normaliza antes de validar, consultar y persistir.
- Registro concurrente de dos peticiones idénticas con el mismo `(tipo_documento, numero_documento)`: la restricción única `uq_usuarios_documento` en SQLite impide duplicados y el servicio traduce `IntegrityError` a **409 `DOCUMENTO_DUPLICADO`**.
- Usuario desactivado (`activo=False`) con cookie JWT previamente emitida y aún no expirada: `get_current_user_optional` retorna `None` y `get_current_user` responde **401 `CREDENCIALES_INVALIDAS`**.
- Cookie JWT firmada con otra clave, algoritmo distinto (`none`, `HS512`, etc.), `sub` no numérico o expirada: ignorada de forma segura → **401 `CREDENCIALES_INVALIDAS`**.
- Inicio de sesión exitoso antes de alcanzar el límite de 10 fallos: debe reiniciar el contador de intentos fallidos para esa clave `(ip_cliente, tipo_documento, numero_documento)`.
- Mutación con cookie válida enviada desde un origen distinto (ej. `https://evil.example`), sin `Origin` ni `Referer`, o con encabezado `Origin` manipulado: bloqueada con **403 `SIN_PERMISO`**.

## 8. Supuestos y pendientes

- `[SUPUESTO S-01]` (Resuelto por equipo): Cuentas de organizador y coordinación solo mediante `scripts/crear_usuario.py` y `scripts/seed.py`; sin auto-registro de personal.
- `[SUPUESTO S-03]` (Resuelto por equipo): Identidad única mediante `tipo_documento` + `numero_documento`; correo no único y solo de contacto.
- `[SUPUESTO S-09]` (Resuelto por equipo): Autorización de mínimo privilegio por rol y verificación de usuario activo.
- `[SUPUESTO S-13]` (Resuelto por equipo): Autenticación por documento + contraseña, sin recuperación de contraseña.
- `[SUPUESTO S-14]` (Confirmado por cliente): Mensajes de error, etiquetas e interfaz en español.
- **Decisiones resueltas en `/speckit.clarify`:**
  - Límite de **10 intentos fallidos** agrupado por `(ip_cliente, tipo_documento, numero_documento)` con ventana de 15 minutos (900 s) y reinicio al iniciar sesión con éxito (alineado con `constitution.md` v2.0.2).
  - `POST /api/v1/auth/logout` responde **204 No Content** (compatible directamente con `api.js`).
  - Mutaciones con cookie hacia `/api/v1` exigen `Origin` válido (o `Referer` válido como respaldo); si faltan ambos o difieren → **403 `SIN_PERMISO`**.
  - `RegistroEntrada` y `LoginEntrada` usan `extra="forbid"` para rechazar con **422 `ERROR_VALIDACION`** cualquier campo no autorizado (ej. `rol`).
- **Pendientes bloqueantes:** ninguno.

## 9. Criterios de éxito y verificación *(obligatorio)*

- **Criterios medibles:**
  - **SC-001:** El 100 % de registros válidos de participante crean fila con `rol="participante"` y contraseña `argon2id`; duplicados de `(tipo_documento, numero_documento)` devuelven **409 `DOCUMENTO_DUPLICADO`**.
  - **SC-002:** El inicio de sesión válido emite cookie `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600` y `Secure`; los intentos inválidos devuelven **401** uniforme y a partir del intento 11 devuelven **429 `DEMASIADOS_INTENTOS`**.
  - **SC-003:** Swagger (`/docs`) funciona enviando automáticamente la cookie de sesión tras ejecutar `POST /api/v1/auth/login`.
  - **SC-004:** `get_current_user` y `require_roles` rechazan con **401** sin sesión/usuario inactivo y **403** con rol insuficiente, y las mutaciones con cookie desde origen inválido devuelven **403**.
  - **SC-005:** `/login` y `/registro` operan mediante `fetch` hacia `/api/v1/auth/*` sin `innerHTML` y la barra superior muestra las opciones acordes al rol.
- **Pruebas funcionales (PF):** Base directa de **PF-09** (acceso sin sesión → 401 y rol insuficiente → 403) y flujo de entrada para **PF-12**.
- **Pruebas automatizadas (`pytest`):**
  - `tests/test_auth.py`: registro exitoso y normalización de documento, 409 por documento duplicado, aceptación de mismo número con distinto `tipo_documento` y correo repetido, 422 por formatos inválidos y contraseña corta sin exponer `input`, no exposición de `hash_password`, login válido con verificación de atributos de cookie (`HttpOnly`, `SameSite=lax`, `Secure`, `Max-Age=3600`), login inválido/inactivo con 401 uniforme, bloqueo 429 tras 10 fallos, `GET /api/v1/auth/yo` con y sin sesión, `POST /api/v1/auth/logout` borrando cookie y vistas `/login` y `/registro`.
  - `tests/test_permisos.py`: 401 sin sesión, 401 con cookie expirada/alterada/usuario inactivo, 403 por rol insuficiente, acceso permitido al rol autorizado y 403 ante `Origin`/`Referer` inválido en mutaciones con cookie (reglas críticas redactadas primero en rojo → verde).
