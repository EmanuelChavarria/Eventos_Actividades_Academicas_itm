/**
 * Módulo JS de la pantalla de registro y consulta de asistencia (E6).
 * Consume GET /api/v1/eventos/{id}/asistencia y
 * PUT /api/v1/eventos/{id}/inscripciones/{insc_id}/asistencia con DOM seguro.
 */

import {
  crearNodo,
  mostrarAlerta,
  ocultarAlerta,
  requestApi,
} from "/static/js/api.js";

const panelAsistencia = document.getElementById("panel-asistencia");
const cuerpoTabla = document.getElementById("cuerpo-asistencia");
const alerta = document.getElementById("alerta-asistencia");

function extraerMensajeError(error) {
  if (Array.isArray(error?.detalles) && error.detalles.length > 0) {
    const textos = error.detalles
      .map((item) => item?.mensaje)
      .filter((msg) => typeof msg === "string" && msg.length > 0);
    if (textos.length > 0) {
      return textos.join(" ");
    }
  }
  return error?.message || "No se pudo completar la operación.";
}

function renderizarMensajeTabla(texto, clase = "") {
  if (!cuerpoTabla) {
    return;
  }
  const fila = crearNodo("tr", {});
  const celda = crearNodo("td", { texto, clase });
  celda.colSpan = 6;
  fila.appendChild(celda);
  cuerpoTabla.replaceChildren(fila);
}

function crearBotonEstado(eventoId, item, estadoObjetivo, etiqueta, esActivo) {
  const clase = esActivo ? "btn-primario btn-compacto" : "btn-secundario btn-compacto";
  const btn = crearNodo("button", { texto: etiqueta, clase });
  btn.type = "button";
  btn.dataset.inscripcionId = String(item.inscripcion_id);
  btn.dataset.estadoObjetivo = estadoObjetivo;
  btn.disabled = esActivo;
  btn.addEventListener("click", () =>
    marcarAsistencia(eventoId, item.inscripcion_id, estadoObjetivo),
  );
  return btn;
}

function renderizarNomina(eventoId, rolUsuario, items) {
  if (!cuerpoTabla) {
    return;
  }
  if (!Array.isArray(items) || items.length === 0) {
    renderizarMensajeTabla("Este evento aún no tiene participantes inscritos.");
    return;
  }

  const filas = items.map((item) => {
    const fila = crearNodo("tr", {});
    fila.dataset.inscripcionId = String(item.inscripcion_id);

    const columnas = [
      item.nombre,
      `${item.tipo_documento} ${item.numero_documento}`,
      item.correo,
      item.estado_inscripcion,
      item.estado_asistencia,
    ];
    for (const texto of columnas) {
      fila.appendChild(crearNodo("td", { texto }));
    }

    const celdaAccion = crearNodo("td", { clase: "col-acciones" });
    const puedeMarcar =
      rolUsuario === "organizador" && item.estado_inscripcion === "activa";
    if (puedeMarcar) {
      const grupo = crearNodo("div", { clase: "acciones-tabla" });
      grupo.appendChild(
        crearBotonEstado(
          eventoId,
          item,
          "presente",
          "Presente",
          item.estado_asistencia === "presente",
        ),
      );
      grupo.appendChild(
        crearBotonEstado(
          eventoId,
          item,
          "ausente",
          "Ausente",
          item.estado_asistencia === "ausente",
        ),
      );
      celdaAccion.appendChild(grupo);
    } else {
      celdaAccion.appendChild(crearNodo("span", { texto: "Solo lectura" }));
    }
    fila.appendChild(celdaAccion);
    return fila;
  });

  cuerpoTabla.replaceChildren(...filas);
}

async function cargarNomina({ limpiarAlerta = true } = {}) {
  if (!panelAsistencia || !cuerpoTabla) {
    return;
  }
  const eventoId = panelAsistencia.dataset.eventoId;
  const rolUsuario = panelAsistencia.dataset.usuarioRol || "";
  if (!eventoId) {
    return;
  }
  if (limpiarAlerta) {
    ocultarAlerta(alerta);
  }
  try {
    const items = await requestApi(`/eventos/${eventoId}/asistencia`, {
      redireccion401: true,
    });
    renderizarNomina(eventoId, rolUsuario, items);
  } catch (error) {
    renderizarMensajeTabla(
      "No fue posible cargar la nómina de asistencia.",
      "texto-error",
    );
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
  }
}

async function marcarAsistencia(eventoId, inscripcionId, estado) {
  ocultarAlerta(alerta);
  const botones = document.querySelectorAll(
    `button[data-inscripcion-id="${inscripcionId}"]`,
  );
  for (const btn of botones) {
    btn.disabled = true;
  }
  try {
    await requestApi(
      `/eventos/${eventoId}/inscripciones/${inscripcionId}/asistencia`,
      {
        method: "PUT",
        body: { estado },
      },
    );
    mostrarAlerta(
      alerta,
      `Asistencia actualizada a "${estado}".`,
      "exito",
    );
    await cargarNomina({ limpiarAlerta: false });
  } catch (error) {
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
    await cargarNomina({ limpiarAlerta: false });
  }
}

if (panelAsistencia) {
  cargarNomina();
}
