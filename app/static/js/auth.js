/**
 * Lógica de formularios /login y /registro consumiendo /api/v1/auth/*.
 */

import { mostrarAlerta, ocultarAlerta, requestApi } from "/static/js/api.js";

const alertaGlobal = document.getElementById("alerta-global");
const formLogin = document.getElementById("form-login");
const formRegistro = document.getElementById("form-registro");

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

function conectarFormularioAuth(formulario, botonId, rutaApi, construirCuerpo, rutaDestino) {
  if (!formulario) {
    return;
  }
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    ocultarAlerta(alertaGlobal);

    if (!formulario.checkValidity()) {
      formulario.reportValidity();
      return;
    }

    const boton = document.getElementById(botonId);
    const cuerpo = construirCuerpo(new FormData(formulario));

    if (boton) {
      boton.disabled = true;
    }
    try {
      await requestApi(rutaApi, {
        method: "POST",
        body: cuerpo,
        redireccion401: false,
      });
      window.location.assign(rutaDestino);
    } catch (error) {
      mostrarAlerta(alertaGlobal, extraerMensajeError(error), "error");
    } finally {
      if (boton) {
        boton.disabled = false;
      }
    }
  });
}

if (formLogin) {
  const params = new URLSearchParams(window.location.search);
  if (params.get("registrado") === "1") {
    mostrarAlerta(alertaGlobal, "Cuenta creada correctamente. Ya puedes iniciar sesión.", "exito");
  }
}

conectarFormularioAuth(
  formLogin,
  "btn-login-enviar",
  "/auth/login",
  (datos) => ({
    tipo_documento: String(datos.get("tipo_documento") || ""),
    numero_documento: String(datos.get("numero_documento") || ""),
    password: String(datos.get("password") || ""),
  }),
  "/",
);

conectarFormularioAuth(
  formRegistro,
  "btn-registro-enviar",
  "/auth/registro",
  (datos) => ({
    tipo_documento: String(datos.get("tipo_documento") || ""),
    numero_documento: String(datos.get("numero_documento") || ""),
    nombre: String(datos.get("nombre") || ""),
    correo: String(datos.get("correo") || ""),
    tipo_participante: String(datos.get("tipo_participante") || ""),
    password: String(datos.get("password") || ""),
  }),
  "/login?registrado=1",
);
