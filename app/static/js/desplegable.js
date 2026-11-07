/*
 * Menús desplegables de la barra superior (asistente de Movimientos, análisis del Resumen).
 * Estructura: [data-desplegable] con un [data-desplegable-boton] y un [data-desplegable-panel].
 * - El botón abre y cierra; Escape cierra y devuelve el foco al botón; un clic fuera cierra.
 * - Avisa con los eventos "desplegable:abierto" y "desplegable:cerrado" en el contenedor.
 * - Otro script puede cerrarlo con contenedor.desplegable.cerrar().
 */
(() => {
  for (const raiz of document.querySelectorAll("[data-desplegable]")) {
    const boton = raiz.querySelector("[data-desplegable-boton]");
    const panel = raiz.querySelector("[data-desplegable-panel]");
    const abierto = () => !panel.hidden;

    function abrir() {
      if (abierto()) return;
      panel.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      raiz.dispatchEvent(new CustomEvent("desplegable:abierto"));
    }

    function cerrar({ devolverFoco = false } = {}) {
      if (!abierto()) return;
      panel.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      raiz.dispatchEvent(new CustomEvent("desplegable:cerrado"));
      if (devolverFoco) boton.focus();
    }

    boton.addEventListener("click", () => (abierto() ? cerrar() : abrir()));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && abierto()) cerrar({ devolverFoco: true });
    });
    document.addEventListener("pointerdown", (event) => {
      if (abierto() && !raiz.contains(event.target)) cerrar();
    });
    // Al volver con Atrás (bfcache) el menú queda cerrado.
    window.addEventListener("pageshow", (event) => {
      if (event.persisted) cerrar();
    });

    raiz.desplegable = { abrir, cerrar, abierto };
  }
})();
