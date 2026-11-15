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
    celda.colSpan = 4;
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
    celda.colSpan = 4;
    fila.appendChild(celda);
    cuerpo.appendChild(fila);
    return;
  }

  for (const inscripcion of inscripciones) {
    const fila = crearNodo("tr", {});
    fila.dataset.inscripcionId = String(inscripcion.id);

    const esActiva = inscripcion.estado === "activa";

    const celdas = [
      { texto: inscripcion.titulo_evento },
      {
        texto: formatearFechaBogota(inscripcion.fecha_inicio_evento),
      },
      {
        texto: inscripcion.estado_evento,
      },
    ];

    for (const celdaInfo of celdas) {
      fila.appendChild(crearNodo("td", celdaInfo));
    }

    const celdaAccion = crearNodo("td", {});
    if (esActiva) {
      const btnCancelar = crearNodo("button", {
        texto: "Cancelar",
        clase: "btn-secundario btn-compacto",
      });
      btnCancelar.dataset.inscripcionId = String(inscripcion.id);
      btnCancelar.onclick = () => cancelarInscripcion(inscripcion.id);
      celdaAccion.appendChild(btnCancelar);
    } else {
      celdaAccion.appendChild(crearNodo("span", { texto: "—" }));
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
    btn.textContent = "Cancelar";
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
  }
}

if (tabla) {
  cargarMisInscripciones();
}
