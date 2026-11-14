---
paths:
  - "app/templates/**"
  - "app/static/**"
---

# Reglas de frontend (`app/templates/` y `app/static/`)

Fuente: `AGENTS.md` §4 y constitución (reglas 4, 5 y 11).

- **Rol de Jinja2:** solo arma el esqueleto HTML (layout base, bloques y navegación). No renderiza listados ni datos de eventos/inscripciones/asistencia desde el servidor; todos los datos llegan por `fetch` a `/api/v1` desde módulos JS (`static/js/api.js` común + un módulo por página). Sin bundler ni SPA.
- **Prevención de XSS:** mantener el autoescape de Jinja2 activo y usar **siempre** `textContent` o creación segura de nodos DOM (`document.createElement`) para insertar texto proveniente de `/api/v1` o del usuario. **Prohibido** `innerHTML` / `insertAdjacentHTML` con datos dinámicos.
- **Fechas y zona horaria (`America/Bogota`):**
  - Formatear todas las fechas en `api.js` usando `Intl.DateTimeFormat('es-CO', { timeZone: 'America/Bogota', ... })` para no depender de la zona del navegador.
  - Al enviar formularios con inputs `datetime-local` (que no incluyen zona horaria), adjuntar explícitamente el desplazamiento `-05:00` en formato ISO-8601 antes de llamar a `/api/v1`.
- **Errores y sesión:** `api.js` interpreta el formato uniforme `{"error": {"codigo", "mensaje", "detalles"}}`, muestra mensajes claros al usuario sin exponer detalles internos y redirige a `/login` ante 401 en rutas privadas.
- **Usabilidad básica (RNF-12):** etiquetas `<label>` accesibles asociadas a cada campo, validación clara en formularios y diseño responsive básico.
- **Propiedad:** `base.html` y `static/*` son de A (excepto módulos por página propios de B en inscripciones/asistencia/reportes; coordinar cambios en `api.js`).
