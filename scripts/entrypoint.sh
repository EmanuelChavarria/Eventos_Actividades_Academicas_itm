#!/bin/sh
set -e

# Aplicar migraciones si Alembic está configurado
if [ -f "alembic.ini" ]; then
  echo "Aplicando migraciones de base de datos..."
  alembic upgrade head
fi

# Iniciar servidor Uvicorn con HTTPS
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --ssl-keyfile /app/certs/localhost-key.pem --ssl-certfile /app/certs/localhost.pem
