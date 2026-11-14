<#
.SYNOPSIS
Genera certificados TLS locales para servir la aplicación por HTTPS.
.DESCRIPTION
Usa mkcert (recomendado) y, si no está disponible, usa openssl como alternativa.
Los archivos generados quedan en certs/ (directorio ignorado por Git).
#>
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$CertsDir = Join-Path $PSScriptRoot "..\certs"
$CertFile = Join-Path $CertsDir "localhost.pem"
$KeyFile = Join-Path $CertsDir "localhost-key.pem"

New-Item -ItemType Directory -Path $CertsDir -Force | Out-Null

if ((Test-Path $CertFile) -and (Test-Path $KeyFile) -and (-not $Force)) {
    Write-Host "Los certificados ya existen en certs/. Usa -Force para regenerarlos."
    exit 0
}

if (Get-Command mkcert -ErrorAction SilentlyContinue) {
    Write-Host "Generando certificados locales confiables con mkcert..."
    mkcert -install
    mkcert -key-file $KeyFile -cert-file $CertFile localhost 127.0.0.1 ::1
    Write-Host "Certificados listos en certs/localhost.pem y certs/localhost-key.pem"
    exit 0
}

if (Get-Command openssl -ErrorAction SilentlyContinue) {
    Write-Host "mkcert no encontrado; generando certificado autofirmado con openssl..."
    openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 `
        -subj "/CN=localhost" `
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" `
        -keyout $KeyFile `
        -out $CertFile
    Write-Host "Certificados autofirmados listos en certs/ (el navegador pedirá aceptar la excepción)."
    exit 0
}

Write-Error "No se encontró 'mkcert' ni 'openssl'. Instala mkcert (winget install FiloSottile.mkcert) y vuelve a intentarlo."
exit 1
