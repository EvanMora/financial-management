/*
 * Diálogo "Nuevo movimiento" / "Editar movimiento" (está en todas las secciones).
 * - Abre con el botón de la barra lateral (o cualquier [data-nuevo-movimiento]) y desde las filas
 *   de Movimientos con window.dialogoMovimiento.abrir(movimiento).
 * - Guarda con la API JSON (/api/v1/movimientos) y muestra los errores por campo, como el login.
 * - Después de guardar o eliminar recarga la sección y deja un aviso para la página siguiente.
 */
(() => {
  const dialog = document.querySelector("[data-dialogo-movimiento]");
  if (!dialog) return;

  const API = "/api/v1/movimientos";
  const AVISO = "aviso";
  const form = dialog.querySelector("[data-form-movimiento]");
  const confirmar = dialog.querySelector("[data-confirmar]");
  const titulo = dialog.querySelector("[data-titulo]");
  const alerta = dialog.querySelector("[data-form-alert]");
  const alertaConfirmar = dialog.querySelector("[data-confirmar-alert]");
  const guardar = form.querySelector("[data-guardar]");
  const eliminar = form.querySelector("[data-eliminar]");
  const botonEliminar = confirmar.querySelector("[data-confirmar-eliminar]");
  const campos = {
    monto: form.elements.monto,
    categoria_id: form.elements.categoria_id,
    cuenta_id: form.elements.cuenta_id,
    fecha: form.elements.fecha,
    descripcion: form.elements.descripcion,
  };
  const hoy = campos.fecha.max;

  let actual = null; // movimiento en edición, o null si es nuevo
  let ocupado = false;

  // ---------- Formato ----------
  const miles = (digitos) => digitos.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  // Lo escrito en el campo ("184.300"): solo los dígitos.
  const digitosCampo = (texto) => String(texto).replace(/\D/g, "").replace(/^0+(?=\d)/, "");
  // Un monto de la API ("62000" o "62000.00"): la parte entera.
  const digitosMonto = (monto) => digitosCampo(String(monto).split(".")[0]);
  const dinero = (monto, tipo) => `${tipo === "ingreso" ? "+" : "−"}$${miles(digitosMonto(monto))}`;

  campos.monto.addEventListener("input", () => {
    const digitos = digitosCampo(campos.monto.value).slice(0, 12);
    campos.monto.value = digitos ? miles(digitos) : "";
  });

  // ---------- Tipo: la categoría solo ofrece las del tipo elegido ----------
  const tipoElegido = () => form.elements.tipo.value;

  function filtrarCategorias() {
    const tipo = tipoElegido();
    for (const opcion of campos.categoria_id.options) {
      if (!opcion.dataset.tipo) continue;
      const otra = opcion.dataset.tipo !== tipo;
      opcion.hidden = otra;
      opcion.disabled = otra;
    }
    if (campos.categoria_id.selectedOptions[0]?.disabled) campos.categoria_id.value = "";
  }

  for (const radio of form.elements.tipo) radio.addEventListener("change", filtrarCategorias);

  // ---------- Errores (mismo comportamiento que el login) ----------
  function errorDeCampo(nombre, mensaje) {
    const input = campos[nombre];
    const p = document.getElementById(`${nombre}-error`);
    if (!input || !p) return false;
    p.textContent = mensaje || "";
    p.hidden = !mensaje;
    if (mensaje) input.setAttribute("aria-invalid", "true");
    else input.removeAttribute("aria-invalid");
    return true;
  }

  function mostrarAlerta(caja, mensaje) {
    caja.textContent = mensaje || "";
    caja.hidden = !mensaje;
  }

  function limpiarErrores() {
    for (const nombre of Object.keys(campos)) errorDeCampo(nombre, null);
    mostrarAlerta(alerta, null);
    mostrarAlerta(alertaConfirmar, null);
  }

  for (const [nombre, input] of Object.entries(campos)) {
    input.addEventListener(input.tagName === "SELECT" ? "change" : "input", () => {
      if (input.hasAttribute("aria-invalid")) errorDeCampo(nombre, null);
    });
  }

  function validar() {
    const errores = {};
    if (!(Number(digitosCampo(campos.monto.value)) > 0)) errores.monto = "Escribe un monto mayor que 0.";
    if (!campos.categoria_id.value) errores.categoria_id = "Elige una categoría.";
    if (!campos.cuenta_id.value) errores.cuenta_id = "Elige una cuenta.";
    if (!campos.fecha.value) errores.fecha = "Escribe una fecha válida.";
    else if (campos.fecha.value > hoy) errores.fecha = "La fecha no puede ser futura.";
    return errores;
  }

  function mostrarErrores(errores) {
    let primero = null;
    for (const [nombre, mensaje] of Object.entries(errores)) {
      if (errorDeCampo(nombre, mensaje)) primero ??= campos[nombre];
      else mostrarAlerta(alerta, mensaje);
    }
    primero?.focus();
  }

  // ---------- Abrir y cerrar ----------
  function abrir(movimiento = null) {
    actual = movimiento;
    form.reset();
    limpiarErrores();
    guardar.classList.remove("is-loading", "is-success");
    form.hidden = false;
    confirmar.hidden = true;

    titulo.textContent = movimiento ? "Editar movimiento" : "Nuevo movimiento";
    eliminar.hidden = !movimiento;
    form.elements.tipo.value = movimiento?.tipo ?? "gasto";
    filtrarCategorias();
    campos.monto.value = movimiento ? miles(digitosMonto(movimiento.monto)) : "";
    campos.categoria_id.value = movimiento?.categoria_id ?? "";
    campos.cuenta_id.value = movimiento?.cuenta_id ?? "";
    campos.fecha.value = movimiento?.fecha ?? hoy;
    campos.descripcion.value = movimiento?.descripcion ?? "";

    // En el celular, si el cajón de la barra estaba abierto, se cierra.
    document.querySelector("[data-shell].is-open [data-scrim]")?.click();
    if (!dialog.open) dialog.showModal();
    campos.monto.focus();
  }

  function cerrar() {
    if (!ocupado) dialog.close();
  }

  dialog.querySelector("[data-cerrar]").addEventListener("click", cerrar);
  dialog.addEventListener("cancel", (event) => {
    if (ocupado) event.preventDefault();
  });
  // Clic en el fondo oscuro, fuera de la tarjeta. Tienen que caer fuera tanto el pointerdown como
  // el click: así no cierra al tocar el espacio libre del diálogo a pantalla completa (celular) ni
  // al soltar sobre el fondo una selección de texto que empezó en un campo.
  const fueraDeLaTarjeta = (event) => {
    const r = dialog.getBoundingClientRect();
    return event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom;
  };
  let pulsoFuera = false;
  dialog.addEventListener("pointerdown", (event) => {
    pulsoFuera = event.target === dialog && fueraDeLaTarjeta(event);
  });
  dialog.addEventListener("click", (event) => {
    if (pulsoFuera && event.target === dialog && fueraDeLaTarjeta(event)) cerrar();
    pulsoFuera = false;
  });

  for (const enlace of document.querySelectorAll("[data-nuevo-movimiento]")) {
    enlace.addEventListener("click", (event) => {
      event.preventDefault();
      abrir(null);
    });
  }

  // ---------- Después de guardar o eliminar ----------
  function irDespues(texto, movimiento) {
    sessionStorage.setItem(AVISO, texto);
    const url = new URL(location.href);
    url.searchParams.delete("nuevo");
    url.searchParams.delete("guardado");
    if (url.pathname === "/movimientos" && movimiento) {
      const [anio, mes] = movimiento.fecha.split("-").map(Number);
      const mesActual = url.searchParams.get("anio") ? [Number(url.searchParams.get("anio")), Number(url.searchParams.get("mes"))] : null;
      const hoyPartes = hoy.split("-").map(Number);
      const vista = mesActual ?? [hoyPartes[0], hoyPartes[1]];
      if (vista[0] !== anio || vista[1] !== mes) {
        // Otro mes: se va a ese mes, sin filtros.
        url.search = "";
        url.searchParams.set("anio", anio);
        url.searchParams.set("mes", mes);
      }
      url.searchParams.set("guardado", movimiento.id);
    }
    location.assign(url);
  }

  function ocupar(boton, si) {
    ocupado = si;
    boton.classList.toggle("is-loading", si);
    boton.disabled = si;
  }

  async function pedir(url, opciones) {
    return fetch(url, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      ...opciones,
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (ocupado) return;
    limpiarErrores();
    const errores = validar();
    if (Object.keys(errores).length) {
      mostrarErrores(errores);
      return;
    }

    const cuerpo = {
      tipo: tipoElegido(),
      monto: digitosCampo(campos.monto.value),
      categoria_id: Number(campos.categoria_id.value),
      cuenta_id: Number(campos.cuenta_id.value),
      fecha: campos.fecha.value,
      descripcion: campos.descripcion.value.trim(),
    };

    ocupar(guardar, true);
    try {
      const respuesta = await pedir(actual ? `${API}/${actual.id}` : API, {
        method: actual ? "PUT" : "POST",
        body: JSON.stringify(cuerpo),
      });
      const datos = await respuesta.json().catch(() => ({}));
      if (respuesta.ok) {
        guardar.classList.remove("is-loading");
        guardar.classList.add("is-success");
        setTimeout(() => irDespues("Movimiento guardado", datos), 450);
        return;
      }
      ocupar(guardar, false);
      if (respuesta.status === 422 && datos.errores) mostrarErrores(datos.errores);
      else if (respuesta.status === 404) mostrarAlerta(alerta, "Este movimiento ya no existe. Cierra y recarga la página.");
      else mostrarAlerta(alerta, "No se pudo guardar. Inténtalo de nuevo.");
    } catch {
      ocupar(guardar, false);
      mostrarAlerta(alerta, "No se pudo guardar. Revisa tu conexión e inténtalo de nuevo.");
    }
  });

  // ---------- Eliminar (con confirmación dentro del mismo diálogo) ----------
  eliminar.addEventListener("click", () => {
    if (!actual) return;
    const texto = confirmar.querySelector("[data-confirmar-texto]");
    const nombre = document.createElement("strong");
    nombre.textContent = actual.nombre;
    texto.replaceChildren("¿Eliminar ", nombre, ` por ${dinero(actual.monto, actual.tipo)}? No se puede deshacer.`);
    mostrarAlerta(alertaConfirmar, null);
    form.hidden = true;
    confirmar.hidden = false;
    confirmar.querySelector("[data-cancelar]").focus();
  });

  confirmar.querySelector("[data-cancelar]").addEventListener("click", () => {
    confirmar.hidden = true;
    form.hidden = false;
    eliminar.focus();
  });

  botonEliminar.addEventListener("click", async () => {
    if (!actual || ocupado) return;
    ocupar(botonEliminar, true);
    try {
      const respuesta = await pedir(`${API}/${actual.id}`, { method: "DELETE" });
      if (respuesta.ok || respuesta.status === 404) {
        irDespues("Movimiento eliminado", null);
        return;
      }
      ocupar(botonEliminar, false);
      mostrarAlerta(alertaConfirmar, "No se pudo eliminar. Inténtalo de nuevo.");
    } catch {
      ocupar(botonEliminar, false);
      mostrarAlerta(alertaConfirmar, "No se pudo eliminar. Revisa tu conexión e inténtalo de nuevo.");
    }
  });

  // ---------- Aviso que viene de la página anterior ----------
  const toast = document.querySelector("[data-toast]");
  const pendiente = sessionStorage.getItem(AVISO);
  if (toast && pendiente) {
    sessionStorage.removeItem(AVISO);
    toast.textContent = pendiente;
    toast.hidden = false;
    setTimeout(() => {
      toast.hidden = true;
    }, 4000);
  }

  // Al volver con Atrás, el navegador puede restaurar la página tal como quedó (bfcache): con el
  // diálogo abierto, ocupado y con el check de éxito. Se deja cerrado y listo.
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    ocupado = false;
    for (const boton of [guardar, botonEliminar]) {
      boton.classList.remove("is-loading", "is-success");
      boton.disabled = false;
    }
    if (dialog.open) dialog.close();
  });

  window.dialogoMovimiento = { abrir };
})();
