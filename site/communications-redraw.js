/* Navigation and optional disclosures only. No storage, telemetry, or legacy progress writes. */
(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const units = $$('.comm-unit');
  if (!units.length) return;
  const ids = units.map(unit => unit.id);
  let current = units[0], pass = 'first', showingAll = false, figureOpener = null, contentsOpener = null;
  const contents = $('#contents-dialog');
  const figureDialog = $('#figure-dialog');
  const figureImage = $('#figure-image');
  let figureWidth = 1000;
  let figureScale = 1;

  function applyPass() {
    $$('[data-pass]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.pass === pass)));
    $$('.deep-block', current).forEach(details => { details.open = pass === 'deep'; });
    $('#mode-hint').textContent = pass === 'first'
      ? '先读本节必学和代表题；第二遍内容保持折叠，需要时单独打开。'
      : '本节第二遍已展开。随时切回第一遍，不需要把整章一次读完。';
  }
  function route(initial = false) {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { hash = ''; }
    const target = document.getElementById(hash);
    const unit = target?.closest('.comm-unit') || units.find(item => item.id === hash) || units[0];
    const changed = unit !== current;
    current = unit;
    const allToggle = $('#show-all');
    if (allToggle) allToggle.textContent = showingAll ? '恢复逐题阅读' : '展开全部题目';
    units.forEach(item => { item.hidden = showingAll ? false : item !== current; });
    $$('.unit-nav').forEach(nav => { nav.hidden = nav.dataset.chapter !== current.dataset.chapter; });
    $$('.chapter-nav [data-chapter]').forEach(link => {
      if (link.dataset.chapter === current.dataset.chapter) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
    $$('.unit-nav a').forEach(link => {
      if (link.hash === '#' + current.id) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
    const title = $('.unit-heading h2', current).textContent;
    document.title = title + ' · 通原两遍辅导';
    $('#current-label').textContent = current.dataset.chapterTitle + ' · ' + title;
    const index = ids.indexOf(current.id);
    for (const [id, adjacent, prefix] of [['previous-unit', units[index - 1], '← '], ['next-unit', units[index + 1], '下一节 → ']]) {
      const link = $('#' + id);
      link.hidden = !adjacent;
      if (adjacent) {
        link.href = '#' + adjacent.id;
        link.textContent = prefix + adjacent.dataset.short;
      }
    }
    $('#contents-links').replaceChildren();
    units.filter(item => item.dataset.chapter === current.dataset.chapter).forEach(item => {
      const a = document.createElement('a');
      a.href = '#' + item.id;
      a.textContent = item.dataset.short;
      $('#contents-links').append(a);
    });
    applyPass();
    if (!initial || location.hash) {
      const scrollTarget = target && current.contains(target) ? target : current;
      requestAnimationFrame(() => scrollTarget.scrollIntoView({block: 'start', behavior: 'instant'}));
    }
    if (changed && figureDialog.open) figureDialog.close();
  }
  $$('[data-pass]').forEach(button => button.addEventListener('click', () => {pass = button.dataset.pass; applyPass();}));
  window.addEventListener('hashchange', () => {showingAll = false; route();});
  $$('.unit-nav a').forEach(link => link.addEventListener('click', () => {
    if (showingAll && link.hash === location.hash) {showingAll = false; route();}
  }));
  $('#open-contents').addEventListener('click', event => {
    contentsOpener = event.currentTarget;
    if (!contents.open) contents.showModal();
  });
  $('[data-close-contents]').addEventListener('click', () => contents.close());
  contents.addEventListener('close', () => contentsOpener?.focus({preventScroll:true}));
  $('#contents-links').addEventListener('click', event => {if (event.target.closest('a')) contents.close();});
  contents.addEventListener('click', event => {if (event.target === contents) contents.close();});

  function setZoom(value) {
    figureScale = Math.min(4, Math.max(.2, value));
    figureImage.style.width = Math.round(figureWidth * figureScale) + 'px';
    $('#zoom-value').textContent = Math.round(figureScale * 100) + '%';
  }
  function fitFigure() {setZoom(Math.min(1, ($('#figure-canvas').clientWidth - 28) / figureWidth));}
  function openFigure(img, opener) {
    figureOpener = opener;
    figureImage.onload = () => {figureWidth = figureImage.naturalWidth || 1000; fitFigure();};
    figureImage.src = img.src;
    figureImage.alt = img.alt;
    $('#figure-title').textContent = img.alt || '清晰大图';
    $('#figure-caption').textContent = img.closest('figure')?.querySelector('figcaption')?.textContent || '';
    $('#open-figure-file').href = img.src;
    if (!figureDialog.open) figureDialog.showModal();
    if (figureImage.complete) {figureWidth = figureImage.naturalWidth || 1000; fitFigure();}
    $('#figure-canvas').scrollTop = 0;
    $('#figure-canvas').scrollLeft = 0;
  }
  $$('[data-open-figure]').forEach(button => button.addEventListener('click', () => openFigure(button.closest('figure').querySelector('img'), button)));
  $$('.comm-figure img').forEach(img => img.addEventListener('click', () => openFigure(img, img.closest('figure').querySelector('button'))));
  $('#close-figure').addEventListener('click', () => figureDialog.close());
  figureDialog.addEventListener('close', () => figureOpener?.focus({preventScroll:true}));
  $('#zoom-in').addEventListener('click', () => setZoom(figureScale * 1.25));
  $('#zoom-out').addEventListener('click', () => setZoom(figureScale / 1.25));
  $('#zoom-fit').addEventListener('click', fitFigure);
  $('#zoom-readable').addEventListener('click', () => setZoom(1));
  $$('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  const allButton = $('#show-all');
  if (allButton) allButton.addEventListener('click', () => {
    showingAll = !showingAll;
    allButton.textContent = showingAll ? '恢复逐题阅读' : '展开全部题目';
    route();
  });
  $$('[data-copy-answer]').forEach(button => button.addEventListener('click', async () => {
    const answer = button.closest('.comm-unit').querySelector('.copy-answer');
    const status = button.parentElement.querySelector('[role=status]');
    if (!answer) {status.textContent = '请选择并复制下面的解答正文。';return;}
    const clone = answer.cloneNode(true);
    $$('math', clone).forEach(math => {math.replaceWith(document.createTextNode(math.querySelector('annotation')?.textContent || math.textContent));});
    $$('figure,button,.copy-toolbar', clone).forEach(el => el.remove());
    const text = clone.textContent.replace(/\n{3,}/g, '\n\n').trim();
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = '已复制解答文字（公式保留可编辑写法）。';
    } catch {
      const range = document.createRange();range.selectNodeContents(answer);
      const selection = window.getSelection();selection.removeAllRanges();selection.addRange(range);
      status.textContent = '已选中解答，请使用系统复制。';
    }
  }));
  route(true);
})();
