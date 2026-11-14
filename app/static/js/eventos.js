/**
 * Lógica de vistas web del organizador (/organizador/eventos/*) mediante DOM seguro.
 */

import {
  aIsoBogota,
  crearNodo,
  formatearFechaBogota,
  mostrarAlerta,
  ocultarAlerta,
  requestApi,
} from "/static/js/api.js";

const alertaGlobal = document.getElementById("alerta-global");
const panelMisEventos = document.getElementById("panel-mis-eventos");
const panelCancelar = document.getElementById("panel-cancelar");
const textoEventoCancelar = document.getElementById("texto-evento-cancelar");
const formCancelar = document.getElementById("form-cancelar-evento");
const inputMotivoCancelar = document.getElementById("cancelar-motivo");
const btnCerrarCancelar = document.getElementById("btn-cerrar-cancelar");
const contenedorForm = document.getElementById("contenedor-form-evento");
const formEvento = document.getElementById("form-evento");

let eventoEnCancelacion = null;

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

function aInputBogotaLocal(isoFecha) {
  if (!isoFecha) {
    return "";
  }
  const fecha = new Date(isoFecha);
  if (Number.isNaN(fecha.getTime())) {
    return "";
  }
  const partes = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(fecha);

  const mapa = {};
  for (const parte of partes) {
    mapa[parte.type] = parte.value;
  }
  return `${mapa.year}-${mapa.month}-${mapa.day}T${mapa.hour}:${mapa.minute}`;
}

function crearEnlaceBoton(texto, href, clase) {
  const enlace = crearNodo("a", { texto, clase });
  enlace.href = href;
  return enlace;
}

function abrirPanelCancelacion(evento) {
  eventoEnCancelacion = evento;
  if (textoEventoCancelar) {
    textoEventoCancelar.textContent = `Vas a cancelar el evento "${evento.titulo}".`;
  }
  if (inputMotivoCancelar) {
    inputMotivoCancelar.value = "";
  }
  panelCancelar?.classList.remove("oculto");
  inputMotivoCancelar?.focus();
}

function cerrarPanelCancelacion() {
  eventoEnCancelacion = null;
  panelCancelar?.classList.add("oculto");
  if (inputMotivoCancelar) {
    inputMotivoCancelar.value = "";
  }
}

async function publicarEventoDesdeListado(evento, boton) {
  ocultarAlerta(alertaGlobal);
  boton.disabled = true;
  try {
    await requestApi(`/eventos/${evento.id}/publicar`, { method: "POST" });
    mostrarAlerta(alertaGlobal, `El evento "${evento.titulo}" fue publicado.`, "exito");
    await cargarMisEventos();
  } catch (error) {
    mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
    boton.disabled = false;
  }
}

function renderizarTarjetaEvento(ev) {
  const tarjeta = crearNodo("article", { clase: "tarjeta-evento" });
  const encabezado = crearNodo("div", { clase: "encabezado-tarjeta-evento" });
  encabezado.appendChild(crearNodo("h2", { texto: ev.titulo }));
  encabezado.appendChild(
    crearNodo("span", {
      texto: ev.estado_efectivo,
      clase: `insignia insignia-${ev.estado_efectivo}`,
    }),
  );
  tarjeta.appendChild(encabezado);

  tarjeta.appendChild(crearNodo("p", { texto: ev.descripcion }));

  const detalles = crearNodo("ul", { clase: "lista-datos-evento" });
  detalles.appendChild(
    crearNodo("li", {
      texto: `Tipo y modalidad: ${ev.tipo} · ${ev.modalidad} (Público: ${ev.publico_objetivo})`,
    }),
  );
  detalles.appendChild(
    crearNodo("li", {
      texto: `Inicio: ${formatearFechaBogota(ev.fecha_inicio)} · Fin: ${formatearFechaBogota(ev.fecha_fin)}`,
    }),
  );
  detalles.appendChild(
    crearNodo("li", {
      texto: `Límite de inscripción: ${formatearFechaBogota(ev.fecha_limite_inscripcion)}`,
    }),
  );
  detalles.appendChild(
    crearNodo("li", {
      texto: `Lugar: ${ev.lugar} · Cupos: ${ev.inscripciones_activas}/${ev.cupo_maximo} (${ev.cupos_disponibles} disponibles)`,
    }),
  );
  if (ev.motivo_cancelacion) {
    detalles.appendChild(
      crearNodo("li", { texto: `Motivo de cancelación: ${ev.motivo_cancelacion}` }),
    );
  }
  tarjeta.appendChild(detalles);

  const acciones = crearNodo("div", { clase: "acciones-hero" });
  if (ev.estado_efectivo === "borrador" || ev.estado_efectivo === "publicado") {
    acciones.appendChild(
      crearEnlaceBoton("Editar", `/organizador/eventos/${ev.id}/editar`, "btn-secundario"),
    );
  }
  if (ev.estado_efectivo === "borrador") {
    const btnPublicar = crearNodo("button", { texto: "Publicar", clase: "btn-primario" });
    btnPublicar.type = "button";
    btnPublicar.addEventListener("click", () => publicarEventoDesdeListado(ev, btnPublicar));
    acciones.appendChild(btnPublicar);
  }
  if (ev.estado_efectivo === "publicado") {
    const btnCancelar = crearNodo("button", {
      texto: "Cancelar evento",
      clase: "btn-peligro",
    });
    btnCancelar.type = "button";
    btnCancelar.addEventListener("click", () => abrirPanelCancelacion(ev));
    acciones.appendChild(btnCancelar);
  }
  if (acciones.childElementCount > 0) {
    tarjeta.appendChild(acciones);
  }
  return tarjeta;
}

async function cargarMisEventos() {
  if (!panelMisEventos) {
    return;
  }
  panelMisEventos.replaceChildren(crearNodo("p", { texto: "Cargando eventos..." }));
  try {
    const eventos = await requestApi("/organizador/eventos");
    if (!Array.isArray(eventos) || eventos.length === 0) {
      panelMisEventos.replaceChildren(
        crearNodo("p", { texto: "Aún no tienes eventos registrados." }),
      );
      return;
    }
    const nodos = eventos.map(renderizarTarjetaEvento);
    panelMisEventos.replaceChildren(...nodos);
  } catch (error) {
    panelMisEventos.replaceChildren();
    mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
  }
}

function conectarCancelacion() {
  btnCerrarCancelar?.addEventListener("click", cerrarPanelCancelacion);
  formCancelar?.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    ocultarAlerta(alertaGlobal);
    if (!eventoEnCancelacion) {
      return;
    }
    if (!formCancelar.checkValidity()) {
      formCancelar.reportValidity();
      return;
    }
    const btn = document.getElementById("btn-confirmar-cancelar");
    if (btn) {
      btn.disabled = true;
    }
    try {
      await requestApi(`/eventos/${eventoEnCancelacion.id}/cancelar`, {
        method: "POST",
        body: { motivo: String(inputMotivoCancelar?.value || "").trim() },
      });
      cerrarPanelCancelacion();
      mostrarAlerta(alertaGlobal, "El evento fue cancelado correctamente.", "exito");
      await cargarMisEventos();
    } catch (error) {
      mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
    } finally {
      if (btn) {
        btn.disabled = false;
      }
    }
  });
}

function poblarFormularioEdicion(ev) {
  const asignaciones = {
    "ev-titulo": ev.titulo,
    "ev-descripcion": ev.descripcion,
    "ev-tipo": ev.tipo,
    "ev-modalidad": ev.modalidad,
    "ev-publico": ev.publico_objetivo,
    "ev-inicio": aInputBogotaLocal(ev.fecha_inicio),
    "ev-fin": aInputBogotaLocal(ev.fecha_fin),
    "ev-limite": aInputBogotaLocal(ev.fecha_limite_inscripcion),
    "ev-lugar": ev.lugar,
    "ev-cupo": String(ev.cupo_maximo),
    "ev-ponente": ev.ponente || "",
    "ev-resp-nombre": ev.responsable_nombre,
    "ev-resp-correo": ev.responsable_correo,
    "ev-requisitos": ev.requisitos || "",
  };
  for (const [idCampo, valor] of Object.entries(asignaciones)) {
    const el = document.getElementById(idCampo);
    if (el) {
      el.value = valor;
    }
  }
  if (ev.estado_efectivo === "cancelado" || ev.estado_efectivo === "finalizado") {
    for (const elemento of formEvento?.elements || []) {
      if (elemento.tagName !== "A") {
        elemento.disabled = true;
      }
    }
    mostrarAlerta(
      alertaGlobal,
      `Este evento está en estado ${ev.estado_efectivo} y no admite modificaciones.`,
      "error",
    );
  }
}

function construirPayloadFormulario(datos) {
  const ponente = String(datos.get("ponente") || "").trim();
  const requisitos = String(datos.get("requisitos") || "").trim();
  return {
    titulo: String(datos.get("titulo") || "").trim(),
    descripcion: String(datos.get("descripcion") || "").trim(),
    tipo: String(datos.get("tipo") || ""),
    modalidad: String(datos.get("modalidad") || ""),
    publico_objetivo: String(datos.get("publico_objetivo") || "todos"),
    fecha_inicio: aIsoBogota(String(datos.get("fecha_inicio") || "")),
    fecha_fin: aIsoBogota(String(datos.get("fecha_fin") || "")),
    fecha_limite_inscripcion: aIsoBogota(String(datos.get("fecha_limite_inscripcion") || "")),
    lugar: String(datos.get("lugar") || "").trim(),
    cupo_maximo: Number(datos.get("cupo_maximo") || 0),
    ponente: ponente || null,
    responsable_nombre: String(datos.get("responsable_nombre") || "").trim(),
    responsable_correo: String(datos.get("responsable_correo") || "").trim(),
    requisitos: requisitos || null,
  };
}

async function inicializarFormulario() {
  if (!formEvento || !contenedorForm) {
    return;
  }
  const modo = contenedorForm.dataset.modo || "crear";
  const eventoId = contenedorForm.dataset.eventoId || "";

  if (modo === "editar" && eventoId) {
    try {
      const evento = await requestApi(`/eventos/${eventoId}`);
      poblarFormularioEdicion(evento);
    } catch (error) {
      mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
    }
  }

  formEvento.addEventListener("submit", async (e) => {
    e.preventDefault();
    ocultarAlerta(alertaGlobal);
    if (!formEvento.checkValidity()) {
      formEvento.reportValidity();
      return;
    }
    const boton = document.getElementById("btn-guardar-evento");
    if (boton) {
      boton.disabled = true;
    }
    try {
      const cuerpo = construirPayloadFormulario(new FormData(formEvento));
      if (modo === "editar" && eventoId) {
        await requestApi(`/eventos/${eventoId}`, { method: "PATCH", body: cuerpo });
      } else {
        await requestApi("/eventos", { method: "POST", body: cuerpo });
      }
      window.location.assign("/organizador/eventos");
    } catch (error) {
      mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
    } finally {
      if (boton) {
        boton.disabled = false;
      }
    }
  });
}

if (panelMisEventos) {
  conectarCancelacion();
  cargarMisEventos();
}
if (formEvento) {
  inicializarFormulario();
}
