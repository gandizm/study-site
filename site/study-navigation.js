/* Presentation only: never reads or changes learning records. */
(() => {
  'use strict';
  // Keep the existing read-only QA mode across home and subject navigation.
  // Hash-only controls stay untouched, so lesson routers keep their semantics.
  if (new URLSearchParams(location.search).get('preview') === '1') {
    document.addEventListener('click', event => {
      const anchor = event.target.closest?.('a[href]');
      if (!anchor || anchor.hasAttribute('download') || anchor.getAttribute('href').startsWith('#')) return;
      const url = new URL(anchor.href, location.href);
      if (url.origin === location.origin && url.pathname.startsWith('/study-site/') &&
          (url.pathname.endsWith('.html') || url.pathname === '/study-site/')) {
        url.searchParams.set('preview', '1');
        anchor.href = url.toString();
      }
    }, true);
  }
  const menu = document.querySelector('.study-subject-menu');
  if (!menu) return;
  const narrow = window.matchMedia('(max-width: 820px)');
  const update = () => { menu.open = !narrow.matches; };
  update();
  narrow.addEventListener('change', update);
  menu.addEventListener('keydown', event => {
    if (event.key === 'Escape' && narrow.matches && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
})();
