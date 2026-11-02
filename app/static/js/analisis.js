/*
 * Análisis del mes en el Resumen (menú "✦ Analizar mes ▾"; abrir y cerrar lo maneja desplegable.js).
 * Al abrirlo por primera vez pide GET /api/v1/ia/analisis-mes y muestra las observaciones y el
 * consejo. Todo el texto de la IA se pone con textContent, nunca como HTML.
 */
(() => {
  const raiz = document.querySelector("[data-analisis]");
  if (!raiz) return;

  const cuerpo = raiz.querySelector("[data-analisis-cuerpo]");
  const { anio, mes, nombreMes } = raiz.dataset;
  let estado = "nuevo"; // nuevo → cargando → listo | error

  const crear = (etiqueta, clase, texto) => {
    const el = document.createElement(etiqueta);
    if (clase) el.className = clase;
    if (texto) el.textContent = texto;
    return el;
  };

  function mostrarCargando() {
    const esqueleto = crear("div", "analisis__esqueleto");
    for (let i = 0; i < 3; i++) esqueleto.append(crear("span"));
    cuerpo.replaceChildren(crear("p", "visually-hidden", "Analizando tus cifras…"), esqueleto);
    cuerpo.setAttribute("aria-busy", "true");
  }

  function mostrarAnalisis(datos) {
    cuerpo.setAttribute("aria-busy", "false");
    if (datos.sin_datos) {
      cuerpo.replaceChildren(crear("p", "asistente__texto", `No hay movimientos en ${nombreMes} para analizar.`));
      return;
    }
    const partes = [];
    if (datos.observaciones.length) {
      const lista = crear("ul", "analisis__lista");
      for (const texto of datos.observaciones) lista.append(crear("li", null, texto));
      partes.push(lista);
    }
    if (datos.consejo) {
      const consejo = crear("p", "analisis__consejo");
      consejo.append(crear("strong", null, "Consejo"), crear("span", null, datos.consejo));
      partes.push(consejo);
    }
    cuerpo.replaceChildren(...partes);
  }

  function mostrarError(mensaje) {
    cuerpo.setAttribute("aria-busy", "false");
    const reintentar = crear("button", "btn btn--outline analisis__reintentar", "Reintentar");
    reintentar.type = "button";
    reintentar.addEventListener("click", cargar);
    cuerpo.replaceChildren(crear("p", "field__message field__message--error", mensaje), reintentar);
  }

  async function cargar() {
    estado = "cargando";
    mostrarCargando();
    try {
      const url = `/api/v1/ia/analisis-mes?anio=${encodeURIComponent(anio)}&mes=${encodeURIComponent(mes)}`;
      const respuesta = await fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } });
      const datos = await respuesta.json().catch(() => ({}));
      if (respuesta.ok) {
        estado = "listo";
        mostrarAnalisis(datos);
        return;
      }
      estado = "error";
      mostrarError(datos.errores?.general ?? "El asistente no respondió. Inténtalo de nuevo en un momento.");
    } catch {
      estado = "error";
      mostrarError("No se pudo contactar al asistente. Revisa tu conexión.");
    }
  }

  // Se pide una sola vez: si se cierra y se vuelve a abrir, se ve lo mismo sin gastar otra consulta.
  raiz.addEventListener("desplegable:abierto", () => {
    if (estado === "nuevo") cargar();
  });
})();
