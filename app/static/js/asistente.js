/*
 * Asistente de la barra superior (botón "Asistente ▾").
 * - El botón despliega el panel; se cierra con Escape, con clic fuera o al volver a pulsar el botón.
 * - Los ejemplos llenan la frase. "Completar" la manda a Gemini (window.dialogoMovimiento.interpretar)
 *   y, si sale bien, cierra el panel y abre "Nuevo movimiento" ya lleno para revisar y guardar.
 */
(() => {
  const raiz = document.querySelector("[data-asistente]");
  if (!raiz) return;

  const boton = raiz.querySelector("[data-asistente-abrir]");
  const panel = raiz.querySelector("[data-asistente-panel]");
  const form = raiz.querySelector("[data-asistente-form]");
  const texto = raiz.querySelector("[data-asistente-texto]");
  const completar = raiz.querySelector("[data-asistente-completar]");
  const mensaje = raiz.querySelector("[data-asistente-mensaje]");
  let peticion = 0; // si se cierra el panel mientras Gemini responde, esa respuesta se ignora

  function mostrarMensaje(contenido, error = false) {
    mensaje.textContent = contenido || "";
    mensaje.hidden = !contenido;
    mensaje.classList.toggle("field__message--error", error);
    if (error) texto.setAttribute("aria-invalid", "true");
    else texto.removeAttribute("aria-invalid");
  }

  function ocupar(si) {
    completar.classList.toggle("is-loading", si);
    completar.disabled = si;
  }

  const abierto = () => !panel.hidden;

  function abrir() {
    panel.hidden = false;
    boton.setAttribute("aria-expanded", "true");
    texto.focus();
  }

  function cerrar({ devolverFoco = false } = {}) {
    if (!abierto()) return;
    peticion += 1;
    ocupar(false);
    mostrarMensaje(null);
    panel.hidden = true;
    boton.setAttribute("aria-expanded", "false");
    if (devolverFoco) boton.focus();
  }

  boton.addEventListener("click", () => (abierto() ? cerrar() : abrir()));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && abierto()) cerrar({ devolverFoco: true });
  });
  document.addEventListener("pointerdown", (event) => {
    if (abierto() && !raiz.contains(event.target)) cerrar();
  });

  for (const ejemplo of raiz.querySelectorAll("[data-ejemplo]")) {
    ejemplo.addEventListener("click", () => {
      texto.value = ejemplo.textContent.trim();
      mostrarMensaje(null);
      texto.focus();
    });
  }

  texto.addEventListener("input", () => {
    if (texto.hasAttribute("aria-invalid")) mostrarMensaje(null);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (completar.disabled) return;
    const frase = texto.value.trim();
    if (!frase) {
      mostrarMensaje("Escribe qué gastaste o recibiste.", true);
      texto.focus();
      return;
    }
    const dialogo = window.dialogoMovimiento;
    if (!dialogo?.interpretar) return;

    const esta = ++peticion;
    mostrarMensaje(null);
    ocupar(true);
    const { sugerencia, error } = await dialogo.interpretar(frase);
    if (esta !== peticion) return;
    ocupar(false);
    if (error) {
      mostrarMensaje(error, true);
      texto.focus();
      return;
    }
    cerrar();
    texto.value = "";
    dialogo.abrirConSugerencia(frase, sugerencia);
  });

  // Al volver con Atrás (bfcache) el panel queda cerrado y listo.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) cerrar();
  });
})();
