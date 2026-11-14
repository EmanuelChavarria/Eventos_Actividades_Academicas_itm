---
name: pytest-reglas-criticas
description: Cómo escribir (primero rojo, luego verde) las pruebas pytest de cupo, duplicados, permisos, ventana de asistencia y fechas. Úsala al probar reglas críticas.
---

# pytest-reglas-criticas

## Método
1. Escribe la prueba y **verifica que falla** por la razón correcta.
2. Implementa lo mínimo en `services/`/`repositories/`.
3. Verifica verde con `pytest -q` y refactoriza con `ruff check . && ruff format .`.

## Infraestructura (`tests/conftest.py`)
BD SQLite temporal desde los modelos, `get_db` sobrescrito, `TestClient`, fábricas de usuarios por rol / eventos publicados / inscripciones y un auxiliar de login (documento + contraseña) que reutiliza la cookie. Solo datos ficticios.

## Casos mínimos
| Archivo | Caso | Esperado |
|---|---|---|
| `test_permisos.py` | Sin sesión crea evento | 401 |
| | Participante o coordinación crea/publica | 403 `SIN_PERMISO` |
| | Organizador ajeno edita/publica | 403 |
| `test_auth.py` | Documento repetido | 409 `DOCUMENTO_DUPLICADO` |
| | Mismo número, otro `tipo_documento` | 201 |
| | Correo repetido | 201 |
| `test_inscripciones.py` | Inscripción válida | 201; cupo disponible −1 |
| | Cupo agotado | 409 `CUPO_AGOTADO`; conteo intacto |
| | Segunda inscripción activa | 409 `INSCRIPCION_DUPLICADA` |
| | Cancelar y reinscribir | cupo liberado; registro nuevo, historial conservado |
| | Hilos simultáneos, cupo 1 | exactamente 1 éxito |
| | Después de `fecha_limite_inscripcion` | 409 `INSCRIPCIONES_CERRADAS` |
| `test_asistencia.py` | Organizador ajeno o participante | 403 |
| | Antes del inicio o después de `fecha_fin + 48 h` | 409 `ASISTENCIA_NO_PERMITIDA` |
| `test_reportes.py` | No coordinación | 403 |
| | Totales | igual a la suma del detalle |

## Simultaneidad
Usa `ThreadPoolExecutor` con N solicitudes a un evento de cupo 1 y afirma `éxitos == 1`, el resto 409 y `COUNT(activas) == 1`.

## Fechas
Fija el «ahora» (inyectable) y prueba los bordes en UTC; la zona `America/Bogota` solo se prueba en presentación.
