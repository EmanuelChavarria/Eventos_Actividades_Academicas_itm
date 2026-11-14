#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="${SCRIPT_DIR}/../certs"
CERT_FILE="${CERTS_DIR}/localhost.pem"
KEY_FILE="${CERTS_DIR}/localhost-key.pem"
FORCE="${1:-}"

mkdir -p "${CERTS_DIR}"

if [[ -f "${CERT_FILE}" && -f "${KEY_FILE}" && "${FORCE}" != "--force" ]]; then
  echo "Los certificados ya existen en certs/. Usa --force para regenerarlos."
  exit 0
fi

if command -v mkcert >/dev/null 2>&1; then
  echo "Generando certificados locales confiables con mkcert..."
  mkcert -install
  mkcert -key-file "${KEY_FILE}" -cert-file "${CERT_FILE}" localhost 127.0.0.1 ::1
  echo "Certificados listos en certs/localhost.pem y certs/localhost-key.pem"
  exit 0
fi

if command -v openssl >/dev/null 2>&1; then
  echo "mkcert no encontrado; generando certificado autofirmado con openssl..."
  openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    -keyout "${KEY_FILE}" \
    -out "${CERT_FILE}"
  echo "Certificados autofirmados listos en certs/ (el navegador pedirá aceptar la excepción)."
  exit 0
fi

echo "Error: no se encontró 'mkcert' ni 'openssl'. Instala mkcert y vuelve a intentarlo." >&2
exit 1
