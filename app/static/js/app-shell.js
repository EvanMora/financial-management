/*
 * Barra lateral de la app.
 * - Escritorio: contraer / expandir. El estado se guarda en una cookie para que el servidor
 *   pinte la barra ya contraída en la siguiente página (con localStorage parpadearía).
 * - Celular: abre y cierra el cajón con el botón de menú, tocando fuera o con Esc.
 */
(() => {
  const shell = document.querySelector("[data-shell]");
  if (!shell) return;

  const COOKIE = "barra_contraida";
  const toggle = shell.querySelector("[data-collapse]");
  const toggleLabel = shell.querySelector("[data-collapse-label]");
  const menu = shell.querySelector("[data-menu]");
  const scrim = shell.querySelector("[data-scrim]");

  toggle.addEventListener("click", () => {
    const collapsed = shell.classList.toggle("is-collapsed");
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggleLabel.textContent = collapsed ? "Expandir barra" : "Contraer barra";
    document.cookie = `${COOKIE}=${collapsed ? 1 : 0}; path=/; max-age=31536000; SameSite=Lax`;
  });

  function setDrawer(open) {
    shell.classList.toggle("is-open", open);
    menu.setAttribute("aria-expanded", String(open));
    if (open) shell.querySelector(".sb-item[aria-current]")?.focus();
    else if (shell.contains(document.activeElement)) menu.focus();
  }

  menu.addEventListener("click", () => setDrawer(true));
  scrim.addEventListener("click", () => setDrawer(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && shell.classList.contains("is-open")) setDrawer(false);
  });
})();
