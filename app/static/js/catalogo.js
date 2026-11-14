/**
 * Lógica del catálogo público (/) y detalle de evento (/eventos/{id}) con DOM seguro.
 */

import {
  crearNodo,
  formatearFechaBogota,
  mostrarAlerta,
  ocultarAlerta,
  requestApi,
} from "/static/js/api.js";

const alertaGlobal = document.getElementById("alerta-global");
const formFiltros = document.getElementById("form-filtros-catalogo");
const btnLimpiarFiltros = document.getElementById("btn-limpiar-catalogo");
const listaCatalogo = document.getElementById("lista-catalogo");
const paginacionCatalogo = document.getElementById("paginacion-catalogo");
const panelDetalle = document.getElementById("panel-detalle-evento");
const contenidoDetalle = document.getElementById("contenido-detalle-evento");
const zonaInscripcion = document.getElementById("zona-inscripcion");

let paginaActual = 1;

function extraerMensajeError(error) {
  if (Array.isArray(error?.detalles) && error.detalles.length > 0) {
    const textos = error.detalles
      .map((item) => item?.mensaje)
      .filter((msg) => typeof msg === "string" && msg.length > 0);
    if (textos.length > 0) {
      return textos.join(" ");
    }
  }
  return error?.message || "No se pudo consultar el catálogo.";
}

function construirParametrosCatalogo(pagina) {
  const params = new URLSearchParams();
  params.set("pagina", String(pagina));
  params.set("tamano", "6");

  if (!formFiltros) {
    return params;
  }
  const datos = new FormData(formFiltros);
  const texto = String(datos.get("texto") || "").trim();
  const tipo = String(datos.get("tipo") || "");
  const modalidad = String(datos.get("modalidad") || "");
  const fechaDesde = String(datos.get("fecha_desde") || "");
  const fechaHasta = String(datos.get("fecha_hasta") || "");
  const incluirFinalizados = Boolean(
    document.getElementById("filtro-finalizados")?.checked,
  );

  if (texto) {
    params.set("texto", texto);
  }
  if (tipo) {
    params.set("tipo", tipo);
  }
  if (modalidad) {
    params.set("modalidad", modalidad);
  }
  if (fechaDesde) {
    params.set("fecha_desde", `${fechaDesde}T00:00:00-05:00`);
  }
  if (fechaHasta) {
    params.set("fecha_hasta", `${fechaHasta}T23:59:59-05:00`);
  }
  if (incluirFinalizados) {
    params.set("incluir_finalizados", "true");
  }
  return params;
}

function renderizarTarjetaCatalogo(ev) {
  const tarjeta = crearNodo("article", { clase: "tarjeta-evento" });
  const encabezado = crearNodo("div", { clase: "encabezado-tarjeta-evento" });
  encabezado.appendChild(crearNodo("h3", { texto: ev.titulo }));
  encabezado.appendChild(
    crearNodo("span", {
      texto: ev.estado_efectivo,
      clase: `insignia insignia-${ev.estado_efectivo}`,
    }),
  );
  tarjeta.appendChild(encabezado);

  tarjeta.appendChild(crearNodo("p", { texto: ev.descripcion }));

  const listaDatos = crearNodo("ul", { clase: "lista-datos-evento" });
  listaDatos.appendChild(
    crearNodo("li", {
      texto: `Tipo y modalidad: ${ev.tipo} · ${ev.modalidad} (Público: ${ev.publico_objetivo})`,
    }),
  );
  listaDatos.appendChild(
    crearNodo("li", {
      texto: `Inicio: ${formatearFechaBogota(ev.fecha_inicio)} · Fin: ${formatearFechaBogota(ev.fecha_fin)}`,
    }),
  );
  listaDatos.appendChild(
    crearNodo("li", {
      texto: `Lugar: ${ev.lugar} · Cupos disponibles: ${ev.cupos_disponibles} de ${ev.cupo_maximo}`,
    }),
  );
  listaDatos.appendChild(
    crearNodo("li", {
      texto: ev.inscripciones_abiertas
        ? `Inscripciones abiertas hasta ${formatearFechaBogota(ev.fecha_limite_inscripcion)}`
        : "Inscripciones cerradas",
    }),
  );
  tarjeta.appendChild(listaDatos);

  const enlaceDetalle = crearNodo("a", { texto: "Ver detalle", clase: "btn-primario" });
  enlaceDetalle.href = `/eventos/${ev.id}`;
  tarjeta.appendChild(enlaceDetalle);
  return tarjeta;
}

function renderizarPaginacion(respuesta) {
  if (!paginacionCatalogo) {
    return;
  }
  paginacionCatalogo.replaceChildren();
  if (respuesta.total_paginas <= 1) {
    return;
  }

  const info = crearNodo("span", {
    texto: `Página ${respuesta.pagina} de ${respuesta.total_paginas} (${respuesta.total} eventos)`,
  });

  const btnAnterior = crearNodo("button", { texto: "Anterior", clase: "btn-secundario" });
  btnAnterior.type = "button";
  btnAnterior.disabled = respuesta.pagina <= 1;
  btnAnterior.addEventListener("click", () => cargarCatalogo(respuesta.pagina - 1));

  const btnSiguiente = crearNodo("button", { texto: "Siguiente", clase: "btn-secundario" });
  btnSiguiente.type = "button";
  btnSiguiente.disabled = respuesta.pagina >= respuesta.total_paginas;
  btnSiguiente.addEventListener("click", () => cargarCatalogo(respuesta.pagina + 1));

  paginacionCatalogo.append(btnAnterior, info, btnSiguiente);
}

async function cargarCatalogo(pagina = 1) {
  if (!listaCatalogo) {
    return;
  }
  ocultarAlerta(alertaGlobal);
  paginaActual = pagina;
  listaCatalogo.replaceChildren(crearNodo("p", { texto: "Cargando eventos publicados..." }));

  try {
    const params = construirParametrosCatalogo(paginaActual);
    const respuesta = await requestApi(`/catalogo/eventos?${params.toString()}`, {
      redireccion401: false,
    });
    if (!Array.isArray(respuesta.items) || respuesta.items.length === 0) {
      listaCatalogo.replaceChildren(
        crearNodo("p", { texto: "No se encontraron eventos publicados con esos criterios." }),
      );
      renderizarPaginacion(respuesta);
      return;
    }
    const tarjetas = respuesta.items.map(renderizarTarjetaCatalogo);
    listaCatalogo.replaceChildren(...tarjetas);
    renderizarPaginacion(respuesta);
  } catch (error) {
    listaCatalogo.replaceChildren();
    paginacionCatalogo?.replaceChildren();
    mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
  }
}

function renderizarDetalleEvento(ev) {
  if (!contenidoDetalle) {
    return;
  }
  const contenedor = crearNodo("div", { clase: "detalle-evento" });
  const encabezado = crearNodo("div", { clase: "encabezado-tarjeta-evento" });
  encabezado.appendChild(crearNodo("h1", { texto: ev.titulo }));
  encabezado.appendChild(
    crearNodo("span", {
      texto: ev.estado_efectivo,
      clase: `insignia insignia-${ev.estado_efectivo}`,
    }),
  );
  contenedor.appendChild(encabezado);
  contenedor.appendChild(crearNodo("p", { texto: ev.descripcion }));

  const ficha = crearNodo("ul", { clase: "lista-datos-evento" });
  const filas = [
    `Tipo: ${ev.tipo} · Modalidad: ${ev.modalidad}`,
    `Público objetivo: ${ev.publico_objetivo}`,
    `Inicio: ${formatearFechaBogota(ev.fecha_inicio)}`,
    `Fin: ${formatearFechaBogota(ev.fecha_fin)}`,
    `Límite de inscripción: ${formatearFechaBogota(ev.fecha_limite_inscripcion)}`,
    `Lugar o enlace: ${ev.lugar}`,
    `Cupos: ${ev.cupos_disponibles} disponibles de ${ev.cupo_maximo} (${ev.inscripciones_activas} inscritos)`,
    `Estado de inscripciones: ${ev.inscripciones_abiertas ? "Abiertas" : "Cerradas"}`,
    `Responsable: ${ev.responsable_nombre} (${ev.responsable_correo})`,
  ];
  if (ev.ponente) {
    filas.push(`Ponente: ${ev.ponente}`);
  }
  if (ev.requisitos) {
    filas.push(`Requisitos: ${ev.requisitos}`);
  }
  for (const linea of filas) {
    ficha.appendChild(crearNodo("li", { texto: linea }));
  }
  contenedor.appendChild(ficha);
  contenidoDetalle.replaceChildren(contenedor);

  if (zonaInscripcion) {
    zonaInscripcion.dataset.inscripcionesAbiertas = String(ev.inscripciones_abiertas);
  }
}

async function cargarDetalleEvento() {
  if (!panelDetalle || !contenidoDetalle) {
    return;
  }
  const eventoId = panelDetalle.dataset.eventoId;
  if (!eventoId) {
    return;
  }
  try {
    const evento = await requestApi(`/catalogo/eventos/${eventoId}`, {
      redireccion401: false,
    });
    renderizarDetalleEvento(evento);
  } catch (error) {
    contenidoDetalle.replaceChildren(
      crearNodo("p", { texto: "No fue posible cargar la actividad solicitada." }),
    );
    mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
  }
}

if (formFiltros) {
  formFiltros.addEventListener("submit", (e) => {
    e.preventDefault();
    cargarCatalogo(1);
  });
}

if (btnLimpiarFiltros && formFiltros) {
  btnLimpiarFiltros.addEventListener("click", () => {
    formFiltros.reset();
    cargarCatalogo(1);
  });
}

if (listaCatalogo) {
  cargarCatalogo(1);
}

if (panelDetalle) {
  cargarDetalleEvento();
}
