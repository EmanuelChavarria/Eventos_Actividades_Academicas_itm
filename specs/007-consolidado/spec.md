# Especificación de Feature: Consolidado para Coordinación Académica

- **Épica:** E7 · **Condiciones:** CA-06 · **Requisitos:** RF-24..RF-26, RF-30 (opcional), RNF-06, RNF-13
- **Rama de feature:** `007-consolidado` · **Creada:** 2026-11-14
- **Estado:** aprobada · **Responsable:** Integrante A
- **Entrada:** Panel de métricas globales y agregadas por evento, cálculo de tasas de ocupación y asistencia, filtros multidimensionales y exportación segura a CSV.

---

## 1. Objetivo y alcance

Proveer al rol de Coordinación Académica un módulo de analítica y reporte consolidado que centralice las métricas de eventos, inscripciones y asistencia en una sola vista, calculando porcentajes de ocupación y asistencia de forma matemáticamente exacta (previniendo división por cero), con filtros combinados, totales consistentes y exportación opcional a CSV seguro, garantizando acceso restringido exclusivamente a coordinación.

---

## 2. Fuera de alcance

- Reportes gráficos avanzados o dashboards en BI externos (PowerBI, Tableau).
- Generación de reportes en PDF con formato editorial.
- Modificación de eventos o asistencias desde este módulo (módulo de solo lectura).

---

## 3. Historias de usuario y criterios de aceptación

### Historia de Usuario 1 - Métricas consolidadas por evento (Prioridad: P1)

Como personal de coordinación académica quiero visualizar un reporte consolidado por evento con cupo, inscritos activos, cupo disponible, cancelaciones, asistentes presentes, ausentes y tasas de ocupación y asistencia.

- **Por qué esta prioridad:** Cumple la condición CA-06 y la necesidad de supervisión institucional.
- **Prueba independiente:** Invocación de `GET /api/v1/reportes/consolidado` como usuario con rol `coordinacion` y verificar estructura agregada.
- **Escenarios de aceptación:**
  1. **Dado** un usuario con rol `coordinacion` autenticado, **Cuando** consulta el consolidado, **Entonces** el sistema retorna la lista de eventos con: cupo máximo, inscritos activos, cupos disponibles, cancelaciones, asistentes presentes, ausentes, sin registrar, % de ocupación (`(inscritos_activos / cupo_maximo) * 100`) y % de asistencia (`(presentes / inscritos_activos) * 100`).
  2. **Dado** un evento con 0 inscritos activos, **Cuando** se calculan las métricas, **Entonces** el porcentaje de asistencia se reporta como `0.0%` sin generar excepciones de división por cero.
  3. **Dado** un usuario con rol `organizador` o `participante`, **Cuando** intenta acceder al consolidado, **Entonces** el sistema responde `403 Forbidden` (`SIN_PERMISO`).

---

### Historia de Usuario 2 - Filtrado multicriterio del consolidado (Prioridad: P1)

Como coordinación quiero aplicar filtros combinados por rango de fechas (inicio/fin), tipo de evento, estado (`borrador`, `publicado`, `finalizado`, `cancelado`), organizador, modalidad (`presencial`, `virtual`, `hibrida`) y búsqueda de texto.

- **Por qué esta prioridad:** Facilita la auditoría específica de periodos académicos y dependencias.
- **Prueba independiente:** Consultar la API pasando parámetros query `?fecha_desde=...&tipo=...&estado=...` y comprobar que el resultado coincide exactamente con los filtros.
- **Escenarios de aceptación:**
  1. **Dado** un conjunto de eventos en la BD, **Cuando** coordinación envía parámetros de filtro válidos, **Entonces** se retorna únicamente los eventos que cumplen todas las condiciones aplicadas.

---

### Historia de Usuario 3 - Fila de totales globales coherente (Prioridad: P2)

Como coordinación quiero una sección de totales generales que sume de manera exacta los valores individuales de todos los eventos del resultado filtrado.

- **Por qué esta prioridad:** Garantiza la integridad analítica y confiabilidad de los datos.
- **Prueba independiente:** Validar mediante test automatizado que `totales.inscritos_activos == sum(e.inscritos_activos for e in eventos)`.
- **Escenarios de aceptación:**
  1. **Dado** el reporte filtrado, **Cuando** se genera la respuesta, **Entonces** incluye un objeto `totales` donde total de eventos, total inscritos, total presentes, total ausentes y total cupos coinciden exactamente con la suma aritmética de las filas individuales.

---

### Historia de Usuario 4 - Exportación segura a CSV (Prioridad: P3)

Como coordinación quiero descargar el reporte consolidado en formato CSV, asegurando que los datos se exporten protegidos contra inyecciones de fórmulas y con privacidad de identificación.

- **Por qué esta prioridad:** Permite análisis externos sin comprometer seguridad (RF-30).
- **Prueba independiente:** Descargar `GET /api/v1/reportes/consolidado/csv` e inspeccionar el archivo generado.
- **Escenarios de aceptación:**
  1. **Dado** un reporte con datos que inician por `=`, `+`, `-` o `@`, **Cuando** se exporta a CSV, **Entonces** se neutralizan anteponiendo un apóstrofe `'` para prevenir ejecución de macros/fórmulas en hojas de cálculo.
  2. **Dado** que el reporte incluye participantes, **Cuando** se genera el CSV, **Entonces** cualquier documento de identidad se encuentra enmascarado (`••••1234`).

---

## 4. Reglas de negocio y modelo analítico

- **RN-09 (Métricas de Asistencia y Ocupación):**
  - $\text{Cupo disponible} = \text{cupo\_maximo} - \text{inscritos\_activos}$
  - $\text{Ocupación \%} = \frac{\text{inscritos\_activos}}{\text{cupo\_maximo}} \times 100$
  - $\text{Asistencia \%} = \begin{cases} \frac{\text{presentes}}{\text{inscritos\_activos}} \times 100 & \text{si } \text{inscritos\_activos} > 0 \\ 0.0 & \text{si } \text{inscritos\_activos} = 0 \end{cases}$
- **RN-11 (Mínimo Privilegio):** Exclusivo para rol `coordinacion`.
- **Eficiencia:** Consulta única agregada SQL con `LEFT JOIN` hacia `inscripciones` y `asistencias` agrupando por `eventos.id` para garantizar tiempos de respuesta óptimos.

---

## 5. Errores esperados

| HTTP | Código de dominio | Causa |
|---|---|---|
| 401 | `CREDENCIALES_INVALIDAS` | No autenticado. |
| 403 | `SIN_PERMISO` | Rol distinto a `coordinacion` (participantes u organizadores). |
| 422 | `VALIDACION_ERROR` | Parámetros de fecha o filtros con formato inválido. |

---

## 6. Seguridad y privacidad

- **Mínimo Privilegio:** Restricción estricta mediante dependencia `require_roles(Rol.COORDINACION)` (y vista web en `/coordinacion/consolidado`).
- **Prevención de Inyección CSV:** Todo valor textual que inicie con `=`, `+`, `-`, `@` o tabuladores debe ser sanitizado con prefijo `'`.
- **Enmascaramiento:** Documentos de identidad siempre anonimizados en vistas y descargas (`••••1234`).

---

## 7. Criterios de éxito y verificación

- **SC-E7-01:** Pruebas en `tests/test_reportes.py` validando control de acceso (403 a roles no autorizados), coherencia matemática de totales y prevención de división por cero.
- **SC-E7-02:** Documentación y evidencia de la prueba funcional **PF-11** en `docs/pruebas/PF-11.md`.
