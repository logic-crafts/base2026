(() => {
  const body = document.body;
  const button = document.querySelector('.ay-v2-menu-toggle');
  const panel = document.getElementById('ay-v2-mobile-panel');
  const sync = () => body.classList.toggle('ay-v2-condensed', window.scrollY > 44);
  const setOpen = (open) => {
    panel.toggleAttribute('hidden', !open);
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
    body.classList.toggle('ay-v2-menu-open', open);
  };

  sync();
  window.addEventListener('scroll', sync, { passive: true });
  if (!button || !panel) return;

  button.addEventListener('click', () => setOpen(panel.hasAttribute('hidden')));
  panel.addEventListener('click', (event) => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
  });
})();
