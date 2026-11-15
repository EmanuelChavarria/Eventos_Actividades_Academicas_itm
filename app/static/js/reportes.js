/**
 * Módulo JS del panel consolidado de coordinación (E7).
 * Consume GET /api/v1/reportes/consolidado usando DOM seguro (crearNodo y textContent).
 */

import {
  crearNodo,
  formatearFechaBogota,
  mostrarAlerta,
  ocultarAlerta,
  requestApi,
} from "/static/js/api.js";

const formFiltros = document.getElementById("form-filtros-consolidado");
const btnLimpiar = document.getElementById("btn-limpiar");
const btnExportarCsv = document.getElementById("btn-exportar-csv");
const alerta = document.getElementById("alerta-consolidado");
const selectOrganizador = document.getElementById("filtro-organizador");
const cuerpoTabla = document.getElementById("cuerpo-consolidado");

const elementosTotales = {
  total_eventos: document.getElementById("total-eventos"),
  cupo_total: document.getElementById("total-cupo"),
  inscritos_activos: document.getElementById("total-inscritos"),
  disponibles: document.getElementById("total-disponibles"),
  ocupacion_pct: document.getElementById("total-ocupacion"),
  cancelaciones: document.getElementById("total-cancelaciones"),
  presentes: document.getElementById("total-presentes"),
  ausentes: document.getElementById("total-ausentes"),
  sin_registrar: document.getElementById("total-sin-registrar"),
  asistencia_pct: document.getElementById("total-asistencia"),
};

const organizadoresConocidos = new Map();

function extraerMensajeError(error) {
  if (Array.isArray(error?.detalles) && error.detalles.length > 0) {
    const textos = error.detalles
      .map((item) => item?.mensaje)
      .filter((msg) => typeof msg === "string" && msg.length > 0);
    if (textos.length > 0) {
      return textos.join(" ");
    }
  }
  return error?.message || "No se pudo cargar el reporte consolidado.";
}

function construirParametrosFiltros() {
  const params = new URLSearchParams();
  if (!formFiltros) {
    return params;
  }
  const datos = new FormData(formFiltros);
  const fechaDesde = String(datos.get("fecha_desde") || "").trim();
  const fechaHasta = String(datos.get("fecha_hasta") || "").trim();
  if (fechaDesde) {
    params.set("fecha_desde", `${fechaDesde}T00:00:00-05:00`);
  }
  if (fechaHasta) {
    params.set("fecha_hasta", `${fechaHasta}T23:59:59-05:00`);
  }

  for (const campo of ["tipo", "modalidad", "estado", "organizador_id", "texto"]) {
    const valor = String(datos.get(campo) || "").trim();
    if (valor) {
      params.set(campo, valor);
    }
  }
  return params;
}

function actualizarEnlaceCsv(params) {
  if (!btnExportarCsv) {
    return;
  }
  const query = params.toString();
  btnExportarCsv.href = query
    ? `/api/v1/reportes/consolidado/csv?${query}`
    : "/api/v1/reportes/consolidado/csv";
}

function actualizarSelectOrganizadores(eventos) {
  if (!selectOrganizador || !Array.isArray(eventos)) {
    return;
  }
  let cambio = false;
  for (const evento of eventos) {
    if (
      evento?.organizador_id &&
      evento?.organizador_nombre &&
      !organizadoresConocidos.has(String(evento.organizador_id))
    ) {
      organizadoresConocidos.set(String(evento.organizador_id), evento.organizador_nombre);
      cambio = true;
    }
  }
  if (!cambio) {
    return;
  }

  const seleccionActual = selectOrganizador.value;
  const opciones = [crearNodo("option", { texto: "Todos", atributos: { value: "" } })];
  const ordenados = [...organizadoresConocidos.entries()].sort((a, b) =>
    a[1].localeCompare(b[1], "es"),
  );
  for (const [id, nombre] of ordenados) {
    opciones.push(crearNodo("option", { texto: nombre, atributos: { value: id } }));
  }
  selectOrganizador.replaceChildren(...opciones);
  selectOrganizador.value = seleccionActual;
}

function renderizarTotales(totales) {
  if (!totales) {
    return;
  }
  if (elementosTotales.total_eventos) {
    elementosTotales.total_eventos.textContent = String(totales.total_eventos ?? 0);
  }
  if (elementosTotales.cupo_total) {
    elementosTotales.cupo_total.textContent = String(totales.cupo_total ?? 0);
  }
  if (elementosTotales.inscritos_activos) {
    elementosTotales.inscritos_activos.textContent = String(totales.inscritos_activos ?? 0);
  }
  if (elementosTotales.disponibles) {
    elementosTotales.disponibles.textContent = String(totales.disponibles ?? 0);
  }
  if (elementosTotales.ocupacion_pct) {
    elementosTotales.ocupacion_pct.textContent = `${Number(totales.ocupacion_pct ?? 0).toFixed(2)}%`;
  }
  if (elementosTotales.cancelaciones) {
    elementosTotales.cancelaciones.textContent = String(totales.cancelaciones ?? 0);
  }
  if (elementosTotales.presentes) {
    elementosTotales.presentes.textContent = String(totales.presentes ?? 0);
  }
  if (elementosTotales.ausentes) {
    elementosTotales.ausentes.textContent = String(totales.ausentes ?? 0);
  }
  if (elementosTotales.sin_registrar) {
    elementosTotales.sin_registrar.textContent = String(totales.sin_registrar ?? 0);
  }
  if (elementosTotales.asistencia_pct) {
    elementosTotales.asistencia_pct.textContent = `${Number(totales.asistencia_pct ?? 0).toFixed(2)}%`;
  }
}

function renderizarMensajeTabla(texto, clase = "") {
  if (!cuerpoTabla) {
    return;
  }
  const fila = crearNodo("tr", {});
  const celda = crearNodo("td", { texto, clase });
  celda.colSpan = 15;
  fila.appendChild(celda);
  cuerpoTabla.replaceChildren(fila);
}

function renderizarEventos(eventos) {
  if (!cuerpoTabla) {
    return;
  }
  if (!Array.isArray(eventos) || eventos.length === 0) {
    renderizarMensajeTabla("No se encontraron eventos para los filtros seleccionados.");
    return;
  }

  const filas = eventos.map((item) => {
    const fila = crearNodo("tr", {});

    fila.appendChild(crearNodo("td", { texto: item.titulo, clase: "col-titulo" }));
    fila.appendChild(crearNodo("td", { texto: `${item.tipo} / ${item.modalidad}` }));

    const celdaEstado = crearNodo("td", {});
    celdaEstado.appendChild(
      crearNodo("span", {
        texto: item.estado,
        clase: `insignia insignia-${item.estado}`,
      }),
    );
    fila.appendChild(celdaEstado);

    fila.appendChild(
      crearNodo("td", {
        texto: formatearFechaBogota(item.fecha_inicio),
        clase: "col-fecha",
      }),
    );
    fila.appendChild(
      crearNodo("td", {
        texto: item.organizador_nombre,
        clase: "col-organizador",
      }),
    );

    const metricas = [
      String(item.cupo_maximo),
      String(item.inscritos_activos),
      String(item.disponibles),
      `${Number(item.ocupacion_pct).toFixed(2)}%`,
      String(item.cancelaciones),
      String(item.presentes),
      String(item.ausentes),
      String(item.sin_registrar),
      `${Number(item.asistencia_pct).toFixed(2)}%`,
    ];
    for (const texto of metricas) {
      fila.appendChild(crearNodo("td", { texto, clase: "col-numerica" }));
    }

    const celdaAccion = crearNodo("td", { clase: "col-acciones" });
    const enlace = crearNodo("a", {
      texto: "Ver asistencia",
      clase: "btn-secundario btn-compacto",
      atributos: { href: `/eventos/${item.evento_id}/asistencia` },
    });
    celdaAccion.appendChild(enlace);
    fila.appendChild(celdaAccion);
    return fila;
  });

  cuerpoTabla.replaceChildren(...filas);
}

async function cargarConsolidado() {
  ocultarAlerta(alerta);
  const params = construirParametrosFiltros();
  actualizarEnlaceCsv(params);
  const query = params.toString();
  const ruta = query ? `/reportes/consolidado?${query}` : "/reportes/consolidado";

  try {
    const datos = await requestApi(ruta);
    actualizarSelectOrganizadores(datos.eventos);
    renderizarTotales(datos.totales);
    renderizarEventos(datos.eventos);
  } catch (error) {
    renderizarMensajeTabla("Error al cargar el reporte consolidado.", "texto-error");
    mostrarAlerta(alerta, extraerMensajeError(error), "error");
  }
}

if (formFiltros) {
  formFiltros.addEventListener("submit", (event) => {
    event.preventDefault();
    cargarConsolidado();
  });
  formFiltros.addEventListener("change", () => {
    actualizarEnlaceCsv(construirParametrosFiltros());
  });
}

if (btnLimpiar) {
  btnLimpiar.addEventListener("click", () => {
    formFiltros?.reset();
    if (selectOrganizador) {
      selectOrganizador.value = "";
    }
    cargarConsolidado();
  });
}

cargarConsolidado();
