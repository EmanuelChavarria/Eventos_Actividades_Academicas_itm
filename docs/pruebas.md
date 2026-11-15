# Índice de Pruebas Funcionales — Proyecto PF-04

**Proyecto:** Organización de eventos y actividades académicas (Python · FastAPI · SQLite · Jinja2 · SDD)  
**Asignatura:** Aplicaciones y Servicios Web · Tecnología en Desarrollo de Software  
**Fuente de verdad:** `docs/01_analisis_y_especificaciones.md`, `.specify/memory/constitution.md`

Este documento consolida la matriz y el estado de ejecución de las **12 pruebas funcionales obligatorias (PF-01 a PF-12)** definidas en la guía del proyecto (Actividad 6) y en la especificación del sistema, verificando el cumplimiento de todas las Condiciones de Aceptación (`CA-01` a `CA-06`) y los Requisitos Funcionales (`RF-01` a `RF-30`).

---

## 1. Matriz general de pruebas funcionales

| ID | Nombre de la prueba | Épica | Condición | Requisitos | Responsable | Estado | Automatización (pytest) |
|---|---|:---:|:---:|---|:---:|:---:|---|
| **PF-01** | [Registro y publicación de actividad válida](pruebas/PF-01.md) | E3 | CA-01 | RF-05, RF-06, RF-07, RN-02, RN-03, RN-12, RN-20 | A | **Aprobada** | `tests/test_eventos.py` |
| **PF-02** | [Creación de actividad con datos inválidos](pruebas/PF-02.md) | E3 | CA-01 | RF-05, RNF-02, RNF-08, RN-02, RN-03, RN-18 | A | **Aprobada** | `tests/test_eventos.py` |
| **PF-03** | [Publicación de actividad con restricciones de fechas](pruebas/PF-03.md) | E3 | CA-01 | RF-07, RN-03, RN-12, RN-15, RN-18 | A | **Aprobada** | `tests/test_eventos.py` |
| **PF-04** | [Consulta y filtrado en catálogo de actividades](pruebas/PF-04.md) | E4 | CA-02 | RF-11, RF-12, RF-13, RN-01, RN-18 | A | **Aprobada** | `tests/test_catalogo.py` |
| **PF-05** | [Inscripción válida a un evento con cupo disponible](pruebas/PF-05.md) | E5 | CA-03 | RF-14, RN-04, RN-06, RN-18 | **B** | **Aprobada** | `tests/test_inscripciones.py` |
| **PF-06** | [Rechazo de inscripción por reglas de negocio](pruebas/PF-06.md) | E5 | CA-04 | RF-15, RF-16, RN-04..07, RN-11, RN-15 | **B** | **Aprobada** | `tests/test_inscripciones.py` |
| **PF-07** | [Control atómico de cupo bajo concurrencia simultánea](pruebas/PF-07.md) | E5 | CA-04 | RF-16, RNF-04, RN-04, RN-05 | **B** | **Aprobada** | `tests/test_inscripciones.py` |
| **PF-08** | [Cancelación de inscripción y liberación de cupo](pruebas/PF-08.md) | E5 | CA-04 | RF-18, RN-06, RN-07, RN-18 | **B** | **Aprobada** | `tests/test_inscripciones.py` |
| **PF-09** | [Control de acceso por rol y propiedad (mínimo privilegio)](pruebas/PF-09.md) | E2/E3 | Transv. | RF-02, RF-03, RNF-05, RNF-06, RN-10 | A | **Aprobada** | `tests/test_permisos.py` |
| **PF-10** | [Registro y corrección de asistencia en ventana de 48 h](pruebas/PF-10.md) | E6 | CA-05 | RF-20, RF-21, RF-22, RF-23, RN-08, RN-10 | **B** | **Aprobada** | `tests/test_asistencia.py` |
| **PF-11** | [Consulta consolidada para coordinación y totales globales](pruebas/PF-11.md) | E7 | CA-06 | RF-24, RF-25, RF-26, RF-30, RN-10, RN-19 | **B** | **Aprobada** | `tests/test_reportes.py` |
| **PF-12** | [Flujo integral completo interfaz–API–BD](pruebas/PF-12.md) | Transv. | CA-01..06 | RF-27, RNF-01..05, RNF-16 | **A y B** | **Aprobada** | `tests/test_scripts_web.py` + Suite |

---

## 2. Cobertura de Condiciones de Aceptación (CA)

- **CA-01 (Creación y publicación persistida de actividades):** Verificada en **PF-01**, **PF-02** y **PF-03**. Los organizadores crean eventos en `borrador`, validan datos en servidor (Pydantic v2 + SQLite CHECK) y publican directamente si cumplen las condiciones (fechas futuras coherentes y cupo ≥ 1).
- **CA-02 (Consulta en catálogo y disponibilidad coherente):** Verificada en **PF-04**. Solo los eventos en estado `publicado` son visibles en el catálogo público; el cupo disponible se calcula en tiempo real (`cupo_maximo - inscripciones_activas`).
- **CA-03 (Inscripción persistida y consultable):** Verificada en **PF-05**. Participantes autenticados aseguran su cupo, persistiendo la inscripción en UTC y consultándola en `/mis-inscripciones`.
- **CA-04 (Administración estricta de cupos sin sobrecupo):** Verificada en **PF-06**, **PF-07** y **PF-08**. Operación atómica con `BEGIN IMMEDIATE` + inserción condicional en SQLite e índice único parcial. Solicitudes concurrentes con hilos garantizan cero sobrecupos.
- **CA-05 (Registro de asistencia y control de nómina):** Verificada en **PF-10**. El organizador dueño registra y corrige asistencia (`presente`/`ausente`) exclusivamente dentro de la ventana oficial (`fecha_inicio` hasta 48 horas tras `fecha_fin`). Coordinación ve la lista con documento enmascarado.
- **CA-06 (Información consolidada para coordinación):** Verificada en **PF-11**. Vista agregada con métricas de ocupación, cancelaciones, asistencia porcentual y totales matemáticamente coherentes con los eventos individuales.

---

## 3. Resumen de ejecución y reproducibilidad

Todas las pruebas cuentan con respaldo de doble verificación:
1. **Pruebas automatizadas (pytest):** Suite completa de 77 pruebas ejecutables en entorno local con `pytest -q` y en contenedor Docker con `docker compose exec web pytest -q`.
2. **Validación interactiva en interfaz web y API:** Vistas Jinja2 con consumo asíncrono seguro vía `fetch` a `/api/v1` (`api.js`), verificadas sobre HTTPS en `https://localhost:8000` y `/docs`.
