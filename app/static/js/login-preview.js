/*
 * Vista previa decorativa del login: cifra del saldo que cuenta hacia arriba, reflejo del
 * vidrio que sigue al cursor y una leve profundidad (parallax). Nada de esto se ejecuta si
 * el sistema pide reducir el movimiento.
 */
(() => {
  const stage = document.querySelector("[data-preview-stage]");
  const preview = stage && stage.querySelector(".preview");
  if (!preview || getComputedStyle(preview).display === "none") return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const counter = preview.querySelector("[data-count-to]");
  if (counter) {
    const target = Number(counter.dataset.countTo);
    const format = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
    const duration = 900;
    const delay = 300;
    let start;
    const tick = (now) => {
      start ??= now;
      const t = Math.min(Math.max(now - start - delay, 0) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      counter.textContent = `$${format.format(Math.round(target * eased))}`;
      if (t < 1) requestAnimationFrame(tick);
    };
    counter.textContent = "$0";
    requestAnimationFrame(tick);
  }

  if (!window.matchMedia("(pointer: fine)").matches) return;

  const panels = [...preview.querySelectorAll(".glass")];
  let frame = 0;

  stage.addEventListener("pointermove", (event) => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const box = stage.getBoundingClientRect();
      stage.style.setProperty("--px", ((event.clientX - box.left) / box.width - 0.5).toFixed(3));
      stage.style.setProperty("--py", ((event.clientY - box.top) / box.height - 0.5).toFixed(3));
      for (const panel of panels) {
        const rect = panel.getBoundingClientRect();
        panel.style.setProperty("--glare-x", `${event.clientX - rect.left}px`);
        panel.style.setProperty("--glare-y", `${event.clientY - rect.top}px`);
      }
    });
  });

  stage.addEventListener("pointerleave", () => {
    cancelAnimationFrame(frame);
    stage.style.removeProperty("--px");
    stage.style.removeProperty("--py");
    for (const panel of panels) {
      panel.style.removeProperty("--glare-x");
      panel.style.removeProperty("--glare-y");
    }
  });
})();
