(() => {
  const body = document.body;
  const button = document.querySelector(".ay-v2-menu-toggle");
  const panel = document.getElementById("ay-v2-mobile-panel");

  const syncCondensedState = () => {
    body.classList.toggle("ay-v2-condensed", window.scrollY > 44);
  };

  const setMenuOpen = (open) => {
    if (!button || !panel) return;
    panel.toggleAttribute("hidden", !open);
    button.setAttribute("aria-expanded", open ? "true" : "false");
    body.classList.toggle("ay-v2-menu-open", open);
  };

  syncCondensedState();
  window.addEventListener("scroll", syncCondensedState, { passive: true });

  if (!button || !panel) return;
  button.addEventListener("click", () => setMenuOpen(panel.hasAttribute("hidden")));
  panel.addEventListener("click", (event) => {
    if (event.target.closest("a")) setMenuOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setMenuOpen(false);
  });
})();
