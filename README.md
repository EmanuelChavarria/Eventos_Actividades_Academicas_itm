# PF-04 — Organización de Eventos y Actividades Académicas

Plataforma web y API REST en Python (**FastAPI**, **SQLite**, **SQLAlchemy**, **Alembic** y **Jinja2 + JavaScript modular**) para gestionar eventos académicos, catálogo público, inscripciones con cupo atómico, asistencia y reportes consolidados.

## Descripción y arquitectura

El sistema resuelve el ciclo completo de actividades académicas institucionales bajo separación estricta en **4 capas** (`app/api/v1` + `app/web` → `app/services` → `app/repositories` → `app/models`), con autenticación segura basada en documento de identidad, fechas normalizadas en UTC con presentación en `America/Bogota`, control atómico de cupos en SQLite (`BEGIN IMMEDIATE`) y consumo de `/api/v1` vía `fetch` desde el navegador.

- **Roles soportados:** `participante` (estudiante/docente), `organizador` (gestión exclusiva de sus eventos y asistencia) y `coordinacion` (consulta consolidada y exportación CSV en solo lectura).
- **Documentación detallada de análisis y diseño:** [docs/requisitos.md](docs/requisitos.md) (requisitos RF/RNF/RN y entrevista al cliente) · [docs/diseno.md](docs/diseno.md) (arquitectura, modelo de datos, API y justificación tecnológica).

## Requisitos previos

- **Python 3.11 o superior** (desarrollado con Python 3.12).
- **Git**.
- **`mkcert`** (recomendado para certificados TLS locales confiables en `https://localhost:8000`) o `openssl` como alternativa.
- Opcional: **`uv`** para crear el entorno virtual e instalar dependencias más rápido, y **Docker / Docker Compose** si se opta por ejecución en contenedores (ver [docs/devops.md](docs/devops.md)).

---

## 1. Clonar y crear el entorno virtual

```bash
git clone https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm.git
cd Eventos_Actividades_Academicas_itm
```

### Opción A: con `venv` estándar de Python

- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(Si PowerShell bloquea scripts locales, ejecuta antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)*
- **Windows (CMD):**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Opción B: con `uv`

- **Windows (PowerShell):**
  ```powershell
  uv venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  uv venv .venv
  source .venv/bin/activate
  ```

---

## 2. Instalar dependencias

Con el entorno virtual `.venv` activado:

```bash
# Con pip (si usaste python -m venv):
pip install -r requirements.txt -r requirements-dev.txt

# O con uv:
uv pip install -r requirements.txt -r requirements-dev.txt
```

Para salir del entorno virtual cuando termines de trabajar: `deactivate`.

---

## 3. Configurar variables de entorno (`.env`)

1. Copia `.env.example` a `.env`:
   - **Windows (PowerShell):** `Copy-Item .env.example .env`
   - **Linux / macOS:** `cp .env.example .env`
2. Genera una clave aleatoria para `SECRET_KEY` (mínimo 32 caracteres y distinta al ejemplo):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
3. Reemplaza `SECRET_KEY=...` dentro de `.env` y mantén **`COOKIE_SECURE=true`** (la aplicación falla al arrancar si `COOKIE_SECURE` no es `true` o si `SECRET_KEY` es insegura).

---

## 4. Generar certificados HTTPS locales (`certs/`)

La aplicación funciona exclusivamente sobre **HTTPS** en todos los entornos. La carpeta `certs/` está ignorada por Git.

- **Windows (PowerShell):**
  ```powershell
  # Instalar mkcert una sola vez (requiere reiniciar la terminal si acaba de instalarse):
  winget install FiloSottile.mkcert

  .\scripts\generar_certificados.ps1
  ```
- **Linux / macOS:**
  ```bash
  chmod +x scripts/generar_certificados.sh
  ./scripts/generar_certificados.sh
  ```

Si no tienes `mkcert` instalado pero sí `openssl`, los scripts generan un certificado autofirmado en `certs/localhost.pem` y `certs/localhost-key.pem` (en ese caso el navegador pedirá aceptar la excepción).

---

## 5. Migrar base de datos y poblar datos ficticios

```bash
alembic upgrade head
python scripts/seed.py
```

`seed.py` es idempotente y crea datos ficticios (1 usuario de coordinación, 2 organizadores, 6 participantes y 5 eventos en distintos estados). La contraseña ficticia de demostración definida en `scripts/seed.py` es `DemoFicticia123!`.

Para crear cuentas administrativas adicionales (`organizador` o `coordinacion`):

```bash
python scripts/crear_usuario.py
```

---

## Puesta en marcha y ejecución

### Opción A: Ejecución local por HTTPS (bare-metal)

```bash
uvicorn app.main:app --reload --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost.pem
```

### Opción B: Ejecución con Docker Compose

Para la guía completa de contenerización, volúmenes, certificados en contenedor, CI/CD y reglas de protección de ramas, consulta [docs/devops.md](docs/devops.md).

```bash
# Construir y levantar el contenedor en segundo plano:
docker compose up -d --build

# Ver logs del contenedor:
docker compose logs -f web

# Detener el contenedor:
docker compose down
```

Rutas principales de acceso:
- Portada web y catálogo: `https://localhost:8000/`
- Documentación interactiva OpenAPI: `https://localhost:8000/docs`
- Estado del servicio y BD: `https://localhost:8000/health`

---

## 6. Catálogo de Endpoints de la API REST (`/api/v1`)

Todos los endpoints se encuentran documentados interactivamente en `https://localhost:8000/docs`. La comunicación se efectúa bajo HTTPS, las fechas se reciben y entregan en formato ISO-8601 con zona (`-05:00` o `Z`) y los errores siguen una estructura uniforme:

```json
{
  "error": {
    "codigo": "CODIGO_DE_DOMINIO",
    "mensaje": "Descripción legible de la causa",
    "detalles": []
  }
}
```

### Tabla de Endpoints por Módulo

| Módulo | Método | Ruta | Rol requerido | Descripción / Requisito |
|---|:---:|---|:---:|---|
| **Salud** | `GET` | `/health` | Público | Verificación de estado del servidor y SQLite (`RNF-22`). |
| **Auth** | `POST` | `/api/v1/auth/registro` | Público | Registro de participante con identificación única (`RF-01`). |
| **Auth** | `POST` | `/api/v1/auth/login` | Público | Autenticación con documento y password; emite cookie JWT (`RF-02`). |
| **Auth** | `POST` | `/api/v1/auth/logout` | Autenticado | Cierre de sesión y revocación de cookie (`RF-02`). |
| **Auth** | `GET` | `/api/v1/auth/yo` | Autenticado | Consulta del perfil en sesión (`RF-02`). |
| **Eventos** | `GET` | `/api/v1/organizador/eventos` | Organizador | Lista de eventos propios en cualquier estado (`RF-10`). |
| **Eventos** | `POST` | `/api/v1/eventos` | Organizador | Creación de evento en estado `borrador` (`RF-05`). |
| **Eventos** | `GET` | `/api/v1/eventos/{id}` | Organizador | Detalle completo de evento propio (`RF-06`). |
| **Eventos** | `PUT` | `/api/v1/eventos/{id}` | Organizador | Edición completa de evento propio en borrador (`RF-06`). |
| **Eventos** | `PATCH` | `/api/v1/eventos/{id}` | Organizador | Modificación parcial de evento propio (`RF-06`). |
| **Eventos** | `POST` | `/api/v1/eventos/{id}/publicar` | Organizador | Publicación directa sin flujo de aprobación (`RF-07`, `RN-20`). |
| **Eventos** | `POST` | `/api/v1/eventos/{id}/cancelar` | Organizador | Cancelación de evento propio con motivo (`RF-08`). |
| **Catálogo** | `GET` | `/api/v1/catalogo/eventos` | Público | Catálogo con filtros de texto, tipo, fechas y paginación (`RF-11`). |
| **Catálogo** | `GET` | `/api/v1/catalogo/eventos/{id}` | Público | Detalle con cálculo de cupo disponible en tiempo real (`RF-12`). |
| **Inscripciones** | `POST` | `/api/v1/eventos/{id}/inscripciones` | Participante | Inscripción atómica con reserva de cupo sin sobrecupo (`RF-14`, `CA-03`). |
| **Inscripciones** | `PATCH` | `/api/v1/inscripciones/{id}/cancelar` | Participante | Cancelación anticipada de inscripción y liberación de cupo (`RF-18`). |
| **Inscripciones** | `GET` | `/api/v1/inscripciones/mias` | Participante | Historial cronológico de inscripciones del usuario (`RF-17`). |
| **Inscripciones** | `GET` | `/api/v1/eventos/{id}/inscripciones` | Org. / Coord. | Lista de inscritos: visible para creador, enmascarada para coord. (`RF-19`). |
| **Asistencia** | `PUT` | `/api/v1/eventos/{id}/inscripciones/{ins_id}/asistencia` | Organizador | Registro y corrección (UPSERT) en ventana de 48 h (`RF-20`, `RF-21`, `CA-05`). |
| **Asistencia** | `GET` | `/api/v1/eventos/{id}/asistencia` | Org. / Coord. | Nómina con asistencia y privacidad diferencial (`RF-22`). |
| **Reportes** | `GET` | `/api/v1/reportes/consolidado` | Coordinación | Consolidado con filtros, métricas y totales coherentes (`RF-24`, `RF-26`, `CA-06`). |
| **Reportes** | `GET` | `/api/v1/reportes/consolidado/csv` | Coordinación | Exportación a CSV con UTF-8 BOM y neutralización de fórmulas (`RF-30`). |

---

## 7. Estrategia de Pruebas y Evidencias Funcionales

La calidad del sistema se respalda en una estrategia de doble verificación: pruebas funcionales documentadas de extremo a extremo y pruebas automatizadas continuas con pytest.

### 7.1 Matriz de Pruebas Funcionales Obligatorias (PF-01 a PF-12)

La documentación completa de condiciones, datos, pasos y resultados esperados/obtenidos se encuentra centralizada en [docs/pruebas.md](docs/pruebas.md):

- [PF-01 — Registro y publicación de actividad válida](docs/pruebas/PF-01.md) (`CA-01`)
- [PF-02 — Creación de actividad con datos inválidos](docs/pruebas/PF-02.md) (`CA-01`)
- [PF-03 — Publicación de actividad con restricciones de fechas](docs/pruebas/PF-03.md) (`CA-01`)
- [PF-04 — Consulta y filtrado en catálogo de actividades](docs/pruebas/PF-04.md) (`CA-02`)
- [PF-05 — Inscripción válida a un evento con cupo disponible](docs/pruebas/PF-05.md) (`CA-03`)
- [PF-06 — Rechazo de inscripción por reglas de negocio](docs/pruebas/PF-06.md) (`CA-04`)
- [PF-07 — Control atómico de cupo bajo concurrencia simultánea](docs/pruebas/PF-07.md) (`CA-04`, `RNF-04`)
- [PF-08 — Cancelación de inscripción y liberación de cupo](docs/pruebas/PF-08.md) (`CA-04`)
- [PF-09 — Control de acceso por rol y propiedad de recursos](docs/pruebas/PF-09.md) (`RNF-06`)
- [PF-10 — Registro y corrección de asistencia en ventana de 48 horas](docs/pruebas/PF-10.md) (`CA-05`)
- [PF-11 — Consulta consolidada para coordinación y totales globales](docs/pruebas/PF-11.md) (`CA-06`)
- [PF-12 — Flujo integral completo interfaz–API–BD](docs/pruebas/PF-12.md) (`CA-01..CA-06`)

### 7.2 Pruebas Automatizadas (pytest)

La suite automatizada consta de **77 pruebas** que verifican el cumplimiento estricto de las reglas críticas:

```bash
# Ejecución local:
pytest -q

# Ejecución dentro del contenedor Docker:
docker compose exec web pytest -q
```

Cobertura automatizada por módulo:
- `tests/test_auth.py`: Identificación única por documento, hash argon2id, rate limit y sesión JWT.
- `tests/test_permisos.py`: Mínimo privilegio, validación de roles en API y vistas web, defensa CSRF.
- `tests/test_eventos.py`: Ciclo de vida de eventos, restricciones CHECK, edición y cancelación.
- `tests/test_catalogo.py`: Filtros de catálogo, visibilidad exclusiva de publicados, cupo calculado.
- `tests/test_inscripciones.py`: Inscripción atómica, rechazos tipados 409 y prueba de estrés concurrente con 20 hilos (`ThreadPoolExecutor`) garantizando cero sobrecupos.
- `tests/test_asistencia.py`: Ventana de asistencia de 48 h, UPSERT de corrección y permisos de organizador.
- `tests/test_reportes.py`: Consulta consolidada, cálculo exacto de métricas, coherencia de totales y CSV seguro.
- `tests/test_scripts_web.py`: Integración de scripts administrativos y renderizado de plantillas Jinja2.

---

## 8. Control de Versiones, Ramas y Aportes por Integrante

El proyecto se desarrolló bajo la metodología **Spec-Driven Development (SDD)** con Spec Kit, manteniendo aislamiento estricto de ramas y convención de commits en español.

### 8.1 Reparto oficial de responsabilidades

- **Integrante A (Emanuel Chavarría):**
  - Cimientos de plataforma (`E1`), Autenticación y roles (`E2`).
  - Gestión de eventos (`E3`), Catálogo público (`E4`).
  - Implementación de asistencia (`E6`) y consolidado (`E7`).
  - Pruebas funcionales PF-01..PF-04 y PF-09 (`E8-A`).
- **Integrante B (Santiago Henao):**
  - Cimientos SDD y constitución v2.0.2 (`E0`).
  - Infraestructura DevOps, Dockerfile, docker-compose, CI y contrato OpenAPI (`E10`).
  - Inscripciones, control atómico de cupos y cancelación (`E5`).
  - Pruebas funcionales PF-05..PF-08, PF-10..PF-12 e índice maestro (`E8-B`).
  - Matriz de trazabilidad integral y documentación DevOps (`E9-B`).

### 8.2 Registro de Pull Requests integrados en `main`

| PR # | Rama de feature | Propósito y Requisitos | Autor |
|:---:|---|---|:---:|
| **[#3](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/3)** | `docs/E0-sdd-constitucion` | Constitución del proyecto v2.0.2 y plantillas SDD trazables | Integrante B |
| **[#11](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/11)** | `010-devops-ci-docker` | Contenerización Docker, pipeline CI en GitHub Actions y OpenAPI inicial | Integrante B |
| **[#12](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/12)** | `005-inscripciones-cupos` | Inscripciones, control atómico con `BEGIN IMMEDIATE` y cancelación | Integrante B |
| **[#13](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/13)** | `docs/reasignacion-e6-e7` | Reasignación acordada de épicas E6 y E7 al Integrante A | Integrante A |
| **[#14](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/14)** | `006-asistencia` | Registro y corrección de asistencia en ventana de 48 horas | Integrante A |
| **[#15](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/15)** | `007-consolidado` | Consulta consolidada para coordinación y exportación CSV sanitizada | Integrante A |
| **[#16](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/16)** | `fix/E10-ci-openapi-docker` | Corrección de PYTHONPATH en exportador OpenAPI y permisos de certs Docker | Integrante B |
| **[#17](https://github.com/EmanuelChavarria/Eventos_Actividades_Academicas_itm/pull/17)** | `test/E8b-pruebas-inscripcion-asistencia` | Documentación de pruebas funcionales PF-05 a PF-12 e índice general | Integrante B |

Para consultar la matriz completa de requisitos contra código y pruebas, ver [docs/trazabilidad.md](docs/trazabilidad.md).

---

## 9. Conclusiones, Lecciones Aprendidas y Limitaciones

### 9.1 Conclusiones Técnicas
1. **Separación arquitectónica estricta:** La separación en cuatro capas (`api` → `services` → `repositories` → `models`) garantizó que toda la lógica de negocio resida exclusivamente en `services/`, manteniendo los routers delgados y los repositorios enfocados en la persistencia.
2. **Concurrencia confiable en SQLite:** El uso de transacciones con `BEGIN IMMEDIATE` y sentencias condicionales `INSERT ... SELECT WHERE (SELECT COUNT(*) ...) < cupo_maximo` demostró empíricamente que SQLite puede manejar alta contención con cero sobrecupos bajo pruebas de estrés multihilo.
3. **Seguridad por diseño:** La adopción de HTTPS obligatorio, cookies con banderas `HttpOnly`, `SameSite=Lax` y `Secure`, validación CSRF estricta sobre cabeceras `Origin`/`Referer`, y contraseñas hasheadas con `argon2id` protege el sistema contra vectores comunes de ataque web.
4. **Desarrollo guiado por especificaciones (SDD):** El marco de trabajo con Spec Kit y compuertas de calidad (`G1` a `G5`) evitó divergencias entre requisitos y código, asegurando que ningún cambio se implementara sin una especificación previa aprobada.

### 9.2 Lecciones Aprendidas
- **Zonas horarias y almacenamiento UTC:** Normalizar todas las fechas en UTC a nivel de ORM y manejarlas con zona horaria explícita (`America/Bogota`) evitó desajustes en el cálculo de límites de inscripción y ventanas de asistencia.
- **Permisos de archivos en volúmenes Docker:** Cuando se ejecutan contenedores con usuarios no privilegiados (`appuser`), los volúmenes montados desde el host (como certificados TLS) deben contar con permisos de lectura explícitos (`chmod 644/755`) para evitar errores de permisos.

### 9.3 Limitaciones Conocidas y Alcance Futuro
- **Pagos y transacciones financieras:** El sistema se diseñó para eventos académicos gratuitos. La integración de pasarelas de pago requeriría un módulo transaccional adicional.
- **Notificaciones externas:** No se contemplaron integraciones de mensajería (SMS, WhatsApp o correos automáticos SMTP); las confirmaciones se gestionan a través de la interfaz web.
- **Certificados digitales firmados:** La emisión de constancias de asistencia con firma criptográfica digital o códigos QR institucionales se mantuvo fuera del alcance según los lineamientos de la guía.

---

## 10. Referencias del Proyecto

- **Reglas obligatorias de desarrollo:** [AGENTS.md](AGENTS.md)
- **Constitución del proyecto (v2.0.2):** [.specify/memory/constitution.md](.specify/memory/constitution.md)
- **Matriz de Trazabilidad Integral:** [docs/trazabilidad.md](docs/trazabilidad.md)
- **Índice de Pruebas Funcionales:** [docs/pruebas.md](docs/pruebas.md)
- **Documentación de DevOps:** [docs/devops.md](docs/devops.md)
- **Diseño y arquitectura base:** [docs/diseno.md](docs/diseno.md)
- **Requisitos iniciales:** [docs/01_analisis_y_especificaciones.md](docs/01_analisis_y_especificaciones.md)
