# PF-04 — Organización de Eventos y Actividades Académicas

Plataforma web y API REST en Python (FastAPI, SQLite, SQLAlchemy, Alembic y Jinja2 + JS modular) para gestionar eventos académicos, catálogo público, inscripciones con cupo atómico, asistencia y reportes consolidados.

## Requisitos previos

- **Python 3.11 o superior** (desarrollado con Python 3.12).
- **Git**.
- **`mkcert`** (recomendado para certificados TLS locales confiables en `https://localhost:8000`) o `openssl` como alternativa.
- Opcional: **`uv`** para crear el entorno virtual e instalar dependencias más rápido.

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

## 6. Ejecutar la aplicación por HTTPS

```bash
uvicorn app.main:app --reload --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost.pem
```

Rutas principales:
- Portada web: `https://localhost:8000/`
- Documentación OpenAPI: `https://localhost:8000/docs`
- Estado del servicio y BD: `https://localhost:8000/health`

---

## 7. Verificación de calidad y pruebas

```bash
ruff check . && ruff format --check .
pytest -q
```

---

## Referencias del proyecto

- Reglas obligatorias de desarrollo y SDD: [AGENTS.md](AGENTS.md)
- Constitución del proyecto: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- Contrato compartido inicial: [docs/diseno.md](docs/diseno.md)
