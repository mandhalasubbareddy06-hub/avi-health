document.addEventListener("DOMContentLoaded", () => {
  const art = document.getElementById("loginArt");
  const orb = art?.querySelector(".health-orb");
  const ring = art?.querySelector(".orb-ring");
  const cards = art?.querySelectorAll(".floating-card");

  if (!art || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  art.addEventListener("pointermove", (event) => {
    const bounds = art.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - 0.5;
    const y = (event.clientY - bounds.top) / bounds.height - 0.5;

    orb?.style.setProperty("transform", `translate(-50%, -50%) rotateX(${-y * 8}deg) rotateY(${x * 12}deg)`);
    ring?.style.setProperty("transform", `translate(-50%, -50%) rotateX(${68 + y * 8}deg) rotateY(${x * 10}deg) rotateZ(-16deg)`);

    cards.forEach((card, index) => {
      const direction = index === 0 ? 1 : -1;
      card.style.transform = `translate3d(${x * 16 * direction}px, ${y * 12 * direction}px, 0)`;
    });
  });

  art.addEventListener("pointerleave", () => {
    orb?.style.removeProperty("transform");
    ring?.style.removeProperty("transform");
    cards.forEach((card) => card.style.removeProperty("transform"));
  });
});
