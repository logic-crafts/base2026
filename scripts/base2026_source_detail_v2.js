(() => {
  const copyButton = document.querySelector('[data-copy-source]');
  const status = document.querySelector('[data-copy-status]');
  if (copyButton) copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(window.location.href.split('?')[0]);
      copyButton.textContent = 'Copied';
      if (status) status.textContent = 'Source link copied.';
    } catch (_) {
      if (status) status.textContent = 'Copy unavailable. Use the browser address bar.';
    }
  });
  const back = document.querySelector('[data-back-to-results]');
  if (back && document.referrer && new URL(document.referrer).origin === window.location.origin) {
    back.addEventListener('click', event => {
      if (history.length > 1) { event.preventDefault(); history.back(); }
    });
  }
})();
