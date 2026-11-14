# Guía rápida de verificación local (E1)

## 1. Entorno virtual y dependencias

```powershell
# Windows (PowerShell) con venv (o uv venv)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## 2. Variables de entorno y certificados HTTPS

```powershell
Copy-Item .env.example .env
# Editar .env y colocar una SECRET_KEY aleatoria (>= 32 caracteres), manteniendo COOKIE_SECURE=true
.\scripts\generar_certificados.ps1
```

```bash
# Linux / macOS
cp .env.example .env
./scripts/generar_certificados.sh
```

## 3. Migración, seed y arranque HTTPS

```bash
alembic upgrade head
python scripts/seed.py
python scripts/seed.py   # idempotente: no duplica registros
uvicorn app.main:app --reload --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost.pem
```

## 4. Comprobaciones de calidad y pruebas

```bash
ruff check . && ruff format --check .
pytest -q
```

Endpoints iniciales esperados tras arrancar:
- `https://localhost:8000/` → HTTP `200` (esqueleto Jinja2 + `api.js`)
- `https://localhost:8000/docs` → HTTP `200` (OpenAPI)
- `https://localhost:8000/health` → HTTP `200 {"status": "ok", "database": "ok"}`
