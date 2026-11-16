/**
 * Módulo JS de la página "Mis inscripciones" (E5).
 * Consume GET /api/v1/inscripciones/mias y PATCH /api/v1/inscripciones/{id}/cancelar
 * usando fetch seguro y DOM sin innerHTML.
 */

import {
  crearNodo,
  formatearFechaBogota,
  mostrarAlerta,
  ocultarAlerta,
  requestApi,
} from "/static/js/api.js";

const tabla = document.getElementById("tabla-mis-inscripciones");
const cuerpo = document.getElementById("cuerpo-mis-inscripciones");
const alerta = document.getElementById("alerta-mis-inscripciones");

const TOTAL_COLUMNAS = 5;

function crearBadgeEstadoEvento(estadoEvento) {
  return crearNodo("span", {
    texto: estadoEvento,
    clase: `insignia insignia-${estadoEvento}`,
  });
}

function crearBadgeEstadoInscripcion(estado) {
  if (estado === "activa") {
    return crearNodo("span", {
      texto: "Inscrito",
      clase: "insignia insignia-publicado",
    });
  }
  if (estado === "cancelada") {
    return crearNodo("span", {
      texto: "Cancelada",
      clase: "insignia insignia-cancelado",
    });
  }
  return crearNodo("span", {
    texto: estado,
    clase: "insignia",
  });
}

function puedeCancelarInscripcion(inscripcion) {
  if (inscripcion.estado !== "activa" || inscripcion.estado_evento !== "publicado") {
    return false;
  }
  const inicioMs = new Date(inscripcion.fecha_inicio_evento).getTime();
  return Number.isNaN(inicioMs) || inicioMs > Date.now();
}

async function cargarMisInscripciones({ limpiarAlerta = true } = {}) {
  if (!cuerpo) {
    return;
  }
  if (limpiarAlerta) {
    ocultarAlerta(alerta);
  }
  try {
    const inscripciones = await requestApi("/inscripciones/mias", {
      redireccion401: true,
    });
    renderizarLista(inscripciones || []);
  } catch (error) {
    cuerpo.replaceChildren(
      crearNodo("tr", {}),
    );
    const celda = crearNodo("td", {
      texto: "No se pudieron cargar tus inscripciones. Intenta de nuevo.",
      clase: "texto-error",
    });
    celda.colSpan = TOTAL_COLUMNAS;
    cuerpo.firstElementChild.appendChild(celda);
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
  }
}

function extraerMensajeError(error) {
  if (Array.isArray(error?.detalles) && error.detalles.length > 0) {
    const textos = error.detalles
      .map((item) => item?.mensaje)
      .filter((msg) => typeof msg === "string" && msg.length > 0);
    if (textos.length > 0) {
      return textos.join(" ");
    }
  }
  return error?.message || "No se pudo completar la solicitud.";
}

function renderizarLista(inscripciones) {
  if (!cuerpo) {
    return;
  }
  cuerpo.replaceChildren();

  if (inscripciones.length === 0) {
    const fila = crearNodo("tr", {});
    const celda = crearNodo("td", {
      texto: "No tienes inscripciones registradas.",
    });
    celda.colSpan = TOTAL_COLUMNAS;
    fila.appendChild(celda);
    cuerpo.appendChild(fila);
    return;
  }

  for (const inscripcion of inscripciones) {
    const fila = crearNodo("tr", {});
    fila.dataset.inscripcionId = String(inscripcion.id);

    fila.appendChild(
      crearNodo("td", {
        texto: inscripcion.titulo_evento,
        clase: "col-titulo",
      }),
    );
    fila.appendChild(
      crearNodo("td", {
        texto: formatearFechaBogota(inscripcion.fecha_inicio_evento),
        clase: "col-fecha",
      }),
    );

    const celdaEstadoEvento = crearNodo("td", {});
    celdaEstadoEvento.appendChild(crearBadgeEstadoEvento(inscripcion.estado_evento));
    fila.appendChild(celdaEstadoEvento);

    const celdaEstadoInscripcion = crearNodo("td", {});
    celdaEstadoInscripcion.appendChild(crearBadgeEstadoInscripcion(inscripcion.estado));
    fila.appendChild(celdaEstadoInscripcion);

    const celdaAccion = crearNodo("td", { clase: "col-acciones" });
    if (puedeCancelarInscripcion(inscripcion)) {
      const btnCancelar = crearNodo("button", {
        texto: "Cancelar inscripción",
        clase: "btn-secundario btn-compacto",
      });
      btnCancelar.type = "button";
      btnCancelar.dataset.inscripcionId = String(inscripcion.id);
      btnCancelar.onclick = () => cancelarInscripcion(inscripcion.id);
      celdaAccion.appendChild(btnCancelar);
    } else if (inscripcion.estado === "cancelada") {
      celdaAccion.appendChild(
        crearNodo("span", {
          texto: "Cancelada por el usuario",
          clase: "texto-tenue",
        }),
      );
    } else {
      celdaAccion.appendChild(
        crearNodo("span", {
          texto: "Sin acciones",
          clase: "texto-tenue",
        }),
      );
    }
    fila.appendChild(celdaAccion);

    cuerpo.appendChild(fila);
  }
}

async function cancelarInscripcion(inscripcionId) {
  const btn = document.querySelector(
    `button[data-inscripcion-id="${inscripcionId}"]`,
  );
  if (!btn) {
    return;
  }
  btn.disabled = true;
  btn.textContent = "Cancelando...";

  try {
    await requestApi(`/inscripciones/${inscripcionId}/cancelar`, {
      method: "PATCH",
    });
    mostrarAlerta(alerta, "Inscripción cancelada correctamente.", "exito");
    await cargarMisInscripciones({ limpiarAlerta: false });
  } catch (error) {
    btn.disabled = false;
    btn.textContent = "Cancelar inscripción";
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
  }
}

if (tabla) {
  cargarMisInscripciones();
}
