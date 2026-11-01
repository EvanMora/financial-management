/*
 * Ventana de inicio de sesión: saludo según la hora del usuario y reflejo del vidrio que
 * sigue al cursor. El reflejo no se activa en pantallas táctiles ni con movimiento reducido.
 */
(() => {
  const card = document.querySelector("[data-login-card]");
  if (!card) return;

  // Al terminar la entrada se marca la tarjeta; si el script carga tarde, se marca de una vez.
  card.addEventListener("animationend", (event) => {
    if (event.animationName === "card-in") card.classList.add("is-ready");
  });
  if (!card.getAnimations().some((animation) => animation.animationName === "card-in")) {
    card.classList.add("is-ready");
  }

  const ICONS = {
    sun: '<circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1 1M11.6 11.6l1 1M3.4 12.6l1-1M11.6 4.4l1-1"/>',
    sunset: '<path d="M2 11.5h12M4.5 11.5a3.5 3.5 0 017 0M8 3v2M3.2 6.2l1 1M12.8 6.2l-1 1M5 14h6"/>',
    moon: '<path d="M13 9.5A5.5 5.5 0 116.5 3a4.5 4.5 0 006.5 6.5z"/>',
  };
  const hour = new Date().getHours();
  const [text, icon] = hour >= 5 && hour < 12 ? ["Buenos días", "sun"]
    : hour >= 12 && hour < 19 ? ["Buenas tardes", "sunset"]
    : ["Buenas noches", "moon"];
  card.querySelector("[data-greeting-text]").textContent = text;
  card.querySelector("[data-greeting-icon]").innerHTML = ICONS[icon];

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(pointer: fine)").matches) return;

  let frame = 0;
  document.addEventListener("pointermove", (event) => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty("--glare-x", `${event.clientX - rect.left}px`);
      card.style.setProperty("--glare-y", `${event.clientY - rect.top}px`);
    });
  });
})();
