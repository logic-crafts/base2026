(() => {
  const runtimeScript = document.currentScript;
  const root = document.querySelector('.base2026-search-v1');
  if (!root) return;

  const filterCount = document.querySelector('#desktop-filter-count');
  const filterReset = document.querySelector('#filter-reset');
  const currentRefinements = document.querySelector('#current-refinements');
  const filterPanel = document.querySelector('#mobile-filter-panel');

  function syncDrawerState() {
    if (!filterPanel || !matchMedia('(max-width: 640px)').matches) return;
    const open = document.body.classList.contains('filters-open');
    filterPanel.style.opacity = open ? '1' : '0';
    filterPanel.style.pointerEvents = open ? 'auto' : 'none';
    filterPanel.style.transform = open ? 'translateY(0)' : 'translateY(10px)';
  }

  function syncControls() {
    const submit = document.querySelector('.ais-SearchBox-submit');
    const reset = document.querySelector('.ais-SearchBox-reset');
    if (submit) {
      submit.setAttribute('aria-label', 'Search evidence');
      submit.setAttribute('title', 'Search evidence');
    }
    if (reset) {
      reset.setAttribute('aria-label', 'Clear search');
      reset.setAttribute('title', 'Clear search');
    }

    const active = document.querySelectorAll('.ais-CurrentRefinements-category').length;
    if (filterCount) filterCount.textContent = `${active} selected`;
    if (filterReset) {
      filterReset.disabled = active === 0;
      filterReset.setAttribute('aria-label', active ? `Reset ${active} active filters` : 'No active filters');
    }
  }

  filterReset?.addEventListener('click', () => {
    const removeButtons = [...document.querySelectorAll('.ais-CurrentRefinements-delete')];
    removeButtons.forEach((button) => button.click());
  });

  const contextItems = [...document.querySelectorAll('.research-context__item')];
  contextItems.forEach((item) => {
    item.querySelector('summary')?.addEventListener('click', (event) => {
      event.preventDefault();
      const willOpen = !item.open;
      contextItems.forEach((other) => { other.open = false; });
      item.open = willOpen;
    });
  });

  const observer = new MutationObserver(syncControls);
  if (currentRefinements) observer.observe(currentRefinements, { childList: true, subtree: true });
  observer.observe(document.querySelector('#searchbox') || document.body, { childList: true, subtree: true });
  const drawerObserver = new MutationObserver(syncDrawerState);
  drawerObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  ['#mobile-filter-toggle', '#mobile-filter-close', '#mobile-filter-backdrop'].forEach((selector) => {
    document.querySelector(selector)?.addEventListener('click', syncDrawerState);
  });
  window.addEventListener('resize', syncDrawerState);
  syncControls();
  syncDrawerState();
  if (runtimeScript?.src && !document.querySelector('[data-base2026-solution-journey="runtime"]')) {
    const journey = document.createElement('script');
    journey.src = new URL('./base2026-solution-journey.js', runtimeScript.src).href;
    journey.dataset.base2026SolutionJourney = 'runtime';
    document.head.append(journey);
  }
})();
