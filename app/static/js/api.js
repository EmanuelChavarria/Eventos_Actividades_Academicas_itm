/**
 * Cliente HTTP común para consumir /api/v1 y utilidades seguras de DOM y fechas.
 * Todas las fechas se presentan explícitamente en America/Bogota (UTC-5).
 */

const BASE_API = "/api/v1";

export class ErrorApi extends Error {
  constructor(status, codigo, mensaje, detalles = []) {
    super(mensaje);
    this.name = "ErrorApi";
    this.status = status;
    this.codigo = codigo;
    this.detalles = detalles;
  }
}

/**
 * Ejecuta una petición fetch hacia /api/v1 con manejo uniforme de errores.
 */
export async function requestApi(ruta, opciones = {}) {
  const {
    method = "GET",
    body = undefined,
    headers = {},
    redireccion401 = true,
  } = opciones;

  const cabeceras = { ...headers };
  let cuerpoFinal = body;

  if (body !== undefined && typeof body !== "string" && !(body instanceof FormData)) {
    cabeceras["Content-Type"] = "application/json";
    cuerpoFinal = JSON.stringify(body);
  }

  const respuesta = await fetch(`${BASE_API}${ruta}`, {
    method,
    credentials: "same-origin",
    headers: cabeceras,
    body: cuerpoFinal,
  });

  if (respuesta.status === 204) {
    return null;
  }

  let datos = null;
  const tipoContenido = respuesta.headers.get("content-type") || "";
  if (tipoContenido.includes("application/json")) {
    datos = await respuesta.json();
  }

  if (!respuesta.ok) {
    const errorInfo = datos && datos.error ? datos.error : null;
    const codigo = errorInfo?.codigo || `HTTP_${respuesta.status}`;
    const mensaje = errorInfo?.mensaje || "No se pudo completar la solicitud.";
    const detalles = Array.isArray(errorInfo?.detalles) ? errorInfo.detalles : [];

    if (respuesta.status === 401 && redireccion401) {
      window.location.assign("/login");
    }
    throw new ErrorApi(respuesta.status, codigo, mensaje, detalles);
  }

  return datos;
}

/**
 * Formatea una fecha ISO-8601 (UTC o con zona) en America/Bogota.
 */
export function formatearFechaBogota(isoFecha) {
  if (!isoFecha) {
    return "—";
  }
  const fecha = new Date(isoFecha);
  if (Number.isNaN(fecha.getTime())) {
    return "Fecha inválida";
  }
  return new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(fecha);
}

/**
 * Convierte un valor de input `datetime-local` a ISO-8601 con zona -05:00.
 */
export function aIsoBogota(valorLocal) {
  if (!valorLocal) {
    return "";
  }
  if (valorLocal.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(valorLocal)) {
    return valorLocal;
  }
  const conSegundos = valorLocal.length === 16 ? `${valorLocal}:00` : valorLocal;
  return `${conSegundos}-05:00`;
}

/**
 * Muestra un mensaje usando exclusivamente textContent (prevención XSS).
 */
export function mostrarAlerta(elemento, mensaje, tipo = "error") {
  if (!elemento) {
    return;
  }
  elemento.classList.remove("oculto", "alerta-error", "alerta-exito");
  elemento.classList.add(tipo === "exito" ? "alerta-exito" : "alerta-error");
  elemento.textContent = mensaje;
}

export function ocultarAlerta(elemento) {
  if (!elemento) {
    return;
  }
  elemento.classList.add("oculto");
  elemento.textContent = "";
}

/**
 * Crea un elemento DOM asignando texto seguro mediante textContent.
 */
export function crearNodo(etiqueta, { texto = "", clase = "" } = {}) {
  const nodo = document.createElement(etiqueta);
  if (clase) {
    nodo.className = clase;
  }
  if (texto) {
    nodo.textContent = texto;
  }
  return nodo;
}

const botonCerrarSesion = document.getElementById("btn-cerrar-sesion");
if (botonCerrarSesion) {
  botonCerrarSesion.addEventListener("click", async () => {
    botonCerrarSesion.disabled = true;
    try {
      await requestApi("/auth/logout", { method: "POST", redireccion401: false });
    } finally {
      window.location.assign("/login");
    }
  });
}
