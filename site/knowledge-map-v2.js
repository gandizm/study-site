/* Recovery edition: missing validation/bootstrap/sync sections reconstructed.
 * This is a NEW core artifact, not the byte-identical frozen original.
 * Existing-reader navigation and rendering below are restored from recorded source.
 */
(function(root) {
  'use strict';
  function validateKnowledgeMap(input, availablePages) {
    if (!input || input.version !== 1 || !Array.isArray(input.nodes) || !input.nodes.length) throw new Error('知识图谱版本或节点列表无效。');
    const allowed = new Set(availablePages.map(Number));
    const ids = new Set();
    const nodes = input.nodes.map(raw => {
      if (!raw || typeof raw.id !== 'string' || !raw.id.trim() || ids.has(raw.id)) throw new Error('知识节点 ID 缺失或重复。');
      ids.add(raw.id);
      if (typeof raw.label !== 'string' || !raw.label.trim()) throw new Error('知识节点名称缺失。');
      if (!Array.isArray(raw.pages) || !raw.pages.length || raw.pages.some(p => !Number.isInteger(p) || !allowed.has(p))) throw new Error('知识节点引用了不存在的原 PPT 页。');
      if (new Set(raw.pages).size !== raw.pages.length) throw new Error('知识节点页码重复。');
      if (raw.prerequisites != null && !Array.isArray(raw.prerequisites)) throw new Error('先修节点格式无效。');
      const anchors = {};
      if (raw.anchors != null) {
        if (typeof raw.anchors !== 'object' || Array.isArray(raw.anchors)) throw new Error('逐页讲义锚点格式无效。');
        for (const [page, anchor] of Object.entries(raw.anchors)) {
          if (!raw.pages.includes(Number(page)) || typeof anchor !== 'string' || !anchor.trim()) throw new Error('逐页讲义锚点与节点页码不匹配。');
          anchors[page] = anchor;
        }
      }
      if (raw.anchor != null && (typeof raw.anchor !== 'string' || !raw.anchor.trim())) throw new Error('讲义锚点无效。');
      return {id:raw.id, label:raw.label.trim(), pages:[...raw.pages], summary:typeof raw.summary === 'string' ? raw.summary : '',
        section:typeof raw.section === 'string' && raw.section.trim() ? raw.section : '知识主线',
        prerequisites:[...(raw.prerequisites || [])], source:raw.source === 'supplement' ? 'supplement' : 'ppt',
        type:typeof raw.type === 'string' ? raw.type : 'concept', anchor:raw.anchor || '', anchors};
    });
    const edges = [], edgeKeys = new Set();
    function addEdge(from, to, label) {
      if (!ids.has(from) || !ids.has(to) || from === to || typeof label !== 'string' || !label.trim()) throw new Error('知识关系的端点或名称无效。');
      const edge = {from,to,label:label.trim()};
      const key = JSON.stringify([edge.from,edge.to,edge.label]);
      if (!edgeKeys.has(key)) { edgeKeys.add(key); edges.push(edge); }
    }
    nodes.forEach(node => node.prerequisites.forEach(id => addEdge(id,node.id,'先修')));
    if (input.edges != null && !Array.isArray(input.edges)) throw new Error('知识关系列表无效。');
    (input.edges || []).forEach(edge => { if (!edge) throw new Error('知识关系无效。'); addEdge(edge.from,edge.to,edge.label); });
    const covered = new Set(nodes.flatMap(node => node.pages));
    return {version:1,id:typeof input.id === 'string' ? input.id : 'knowledge-map',title:typeof input.title === 'string' ? input.title : '本章知识图谱',nodes,edges,
      coveredPages:[...covered].sort((a,b)=>a-b),missingPages:[...allowed].filter(page=>!covered.has(page)).sort((a,b)=>a-b)};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {validateKnowledgeMap};
  if (!root.document) return;
  const document = root.document;
  const loader = document.currentScript || document.querySelector('script[data-knowledge-map]');
  const dataURL = loader?.getAttribute('data-knowledge-map') || '';
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }
  function button(className, text, label) {
    const node = element('button', className, text); node.type = 'button';
    if (label) node.setAttribute('aria-label', label);
    return node;
  }
  function bootstrap() {
    if (document.querySelector('#knowledge-map')) return;
    const main = document.querySelector('main'), select = document.querySelector('#pageSelect');
    const articles = [...document.querySelectorAll('.slide-page[data-page]')];
    if (!main || !select || !articles.length) return;
    const pages = articles.map(article => Number(article.dataset.page));
    if (pages.some(page => !Number.isInteger(page)) || new Set(pages).size !== pages.length) return;
    const pageArticles = new Map(articles.map(article => [Number(article.dataset.page),article]));
    articles.forEach(article => article.querySelector('.teaching')?.setAttribute('tabindex','-1'));
    const cards = new Map(), groups = [], pageButtons = new Map(), backStack = [];
    let data = null, current = Number(select.value), selectedId = '', expanded = true;
    if (!pageArticles.has(current)) current = Number(articles.find(article => !article.hidden)?.dataset.page || pages[0]);
    let knownPage = current, lastDestination = current + ':', isNavigating = false, navigationToken = 0;
    const storageKey = 'study-knowledge-map-ui:' + root.location.pathname;
    const compactQuery = '(max-width: 520px), (max-width: 1150px) and (max-height: 600px)';
    let mapEntryRequested = false, entryRevealConsumed = false, dockToken = 0, dockReturn = null, dockResume = null, entryInteraction = false;
    try { expanded = root.sessionStorage.getItem(storageKey) !== 'closed'; } catch (_) {}
    try {
      const original = root.performance?.getEntriesByType('navigation')?.[0]?.name;
      mapEntryRequested = new URL(root.location.href).searchParams.get('map') === '1' || Boolean(original && new URL(original).searchParams.get('map') === '1');
      if (mapEntryRequested) expanded = true;
    } catch (_) {}

    const workspace = element('div', 'km-workspace');
    main.before(workspace);
    workspace.append(main);
    document.body.classList.add('km-enabled');
    const aside = element('aside', 'km-panel');
    aside.id = 'knowledge-map';
    aside.setAttribute('aria-label', '常驻知识图谱');
    const header = element('div', 'km-header');
    const toggle = button('km-toggle', '', '收起知识图谱');
    toggle.setAttribute('aria-controls', 'km-content');
    const title = element('strong', 'km-title', '知识图谱');
    const currentLabel = element('span', 'km-current', 'P' + current);
    const chevron = element('span', 'km-chevron', '▾');
    chevron.setAttribute('aria-hidden', 'true');
    toggle.append(title, currentLabel, chevron);
    const backButton = button('km-back', '↶ 返回', '返回上次阅读位置');
    backButton.disabled = true;
    header.append(toggle, backButton);
    const content = element('div', 'km-content');
    content.id = 'km-content';
    const description = element('p', 'km-description', '点击概念或页码，同时定位原 PPT 与讲义。图谱会一直保留。');
    const actions = element('div', 'km-actions');
    const locate = button('km-locate', '定位当前', '在知识图谱中定位当前原 PPT 页');
    const read = button('km-read', '读本页讲义', '将键盘焦点移到当前页讲义，图谱保持展开');
    actions.append(locate, read);
    const searchLabel = element('label', 'km-search-label');
    searchLabel.append(element('span', 'km-sr-only', '搜索知识节点或原 PPT 页码'));
    const search = element('input', 'km-search');
    search.type = 'search'; search.placeholder = '搜索概念 / P页码';
    search.setAttribute('aria-label', '搜索知识节点或原 PPT 页码');
    searchLabel.append(search);
    const count = element('p', 'km-count', '正在载入本章图谱…');
    const notice = element('p', 'km-notice'); notice.hidden = true;
    const graph = element('nav', 'km-graph');
    graph.setAttribute('aria-label', '知识节点、先修关系与原 PPT 页码');
    const empty = element('p', 'km-empty', '没有匹配的节点。可清空搜索或点“定位当前”。'); empty.hidden = true;
    const live = element('div', 'km-sr-only'); live.setAttribute('role', 'status'); live.setAttribute('aria-live', 'polite');
    content.append(description, actions, searchLabel, count, notice, graph, empty);
    aside.append(header, content, live);
    workspace.prepend(aside);

    function readerMode() {
      const compact = Boolean(root.matchMedia?.(compactQuery).matches);
      const narrow = root.innerWidth ? root.innerWidth <= 520 : Boolean(root.matchMedia?.('(max-width: 520px)').matches);
      const modal = document.querySelector('#modal'), modalImage = modal?.querySelector('img');
      return JSON.stringify([root.location.pathname, compact ? (narrow ? 'stacked' : 'beside') : 'desktop',
        root.innerWidth || 0, root.innerHeight || 0,
        workspace.classList.contains('kgv2-roomy-workspace'), root.CourseChapterGraph?.state?.().mode || 'overview',
        Boolean(modal && !modal.hidden), Boolean(modalImage?.classList.contains('modal-fit'))]);
    }
    function dockPosition() {
      return {page: current, mode: readerMode(), windowTop: root.scrollY || 0, windowLeft: root.scrollX || 0,
        readerTop: main.scrollTop || 0, readerLeft: main.scrollLeft || 0};
    }
    function changeDockVisibility(open, before) {
      const token = ++dockToken, nav = navigationToken;
      if (!root.matchMedia?.(compactQuery).matches) { dockReturn = null; dockResume = null; return; }
      const restore = open ? null : dockReturn;
      const previous = open ? dockResume : null;
      const samePosition = (a, b) => a && b && a.page === b.page && a.mode === b.mode &&
        a.windowTop === b.windowTop && a.windowLeft === b.windowLeft &&
        a.readerTop === b.readerTop && a.readerLeft === b.readerLeft;
      const resume = previous && samePosition(previous.collapsed, before) ? previous.reading : null;
      // Capture before collapse can clamp main's scroll range. A reopen may
      // resume it only while the collapsed reading position is still unchanged.
      dockResume = open ? null : {reading: before, collapsed: dockPosition()};
      root.requestAnimationFrame(() => {
        if (token !== dockToken || nav !== navigationToken || expanded !== open || visiblePage() !== current || !root.matchMedia?.(compactQuery).matches) return;
        if (open) {
          // A cancelled/pending reveal is not an actual reading-location change.
          // Keep a return origin only once this opening really aligns the dock.
          if (!dockReturn) dockReturn = before;
          // Only explicit map entry/open reveals the bounded two-region dock.
          // Ordinary graph page jumps retain their own saved scroll positions.
          const reading = resume && resume.page === current && resume.mode === readerMode() ? resume : before;
          if (reading.page === current) { main.scrollTop = reading.readerTop; main.scrollLeft = reading.readerLeft; }
          const top = (root.scrollY || 0) + workspace.getBoundingClientRect().top;
          root.scrollTo?.(root.scrollX || 0, Math.max(0, top));
        } else if (restore) {
          // Closing is not history. A different page, course, viewport/layout,
          // diagram view or original-image mode owns its current reading place.
          if (restore.page === current && restore.mode === readerMode()) {
            main.scrollTop = restore.readerTop; main.scrollLeft = restore.readerLeft;
            root.scrollTo?.(restore.windowLeft, restore.windowTop);
          }
          dockReturn = null;
        }
        if (!open && dockResume) dockResume.collapsed = dockPosition();
      });
    }
    function cancelPendingDockReveal(event) {
      ++dockToken; entryInteraction = true;
      if (!expanded) {
        dockReturn = null;
        // The reopen button's own pointer/key activation is not new reading.
        if (!toggle.contains(event?.target)) dockResume = null;
      }
    }
    // A slow map fetch must never bring the document back after the reader has
    // started interacting. Input also invalidates a queued open/close frame.
    ['wheel', 'touchstart', 'pointerdown'].forEach(name => root.addEventListener(name, cancelPendingDockReveal, {capture: true, passive: true}));
    root.addEventListener('keydown', event => {
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) cancelPendingDockReveal(event);
    }, {capture: true});
    function setExpanded(next, remember = true) {
      const changed = next !== expanded, before = changed && remember ? dockPosition() : null;
      expanded = next;
      aside.classList.toggle('km-collapsed', !next);
      workspace.classList.toggle('km-map-collapsed', !next);
      content.hidden = !next;
      toggle.setAttribute('aria-expanded', String(next));
      toggle.setAttribute('aria-label', (next ? '收起' : '展开') + '知识图谱，当前原 PPT 第' + current + '页');
      chevron.textContent = next ? '▾' : '▸';
      if (remember) try { root.sessionStorage.setItem(storageKey, next ? 'open' : 'closed'); } catch (_) {}
      if (changed && remember) changeDockVisibility(next, before);
    }
    setExpanded(expanded, false);
    toggle.addEventListener('click', () => setExpanded(!expanded));

    function visiblePage() {
      const article = articles.find(a => !a.hidden);
      return article ? Number(article.dataset.page) : Number(select.value);
    }
    function snapshot() {
      const article = pageArticles.get(current);
      const teaching = article?.querySelector('.teaching');
      const viewport = article?.querySelector('.slide-viewport');
      return {page: current, nodeId: selectedId, destination: lastDestination,
        teachingTop: teaching?.scrollTop || 0, teachingLeft: teaching?.scrollLeft || 0,
        pptTop: viewport?.scrollTop || 0, pptLeft: viewport?.scrollLeft || 0,
        pptZoom: Number.parseInt(article?.querySelector('.slide-toolbar output')?.textContent, 10) || 100,
        windowTop: root.scrollY || 0, windowLeft: root.scrollX || 0,
        readerTop: main.scrollTop || 0, readerLeft: main.scrollLeft || 0,
        mapTop: graph.scrollTop, search: search.value};
    }
    function updateBack() {
      backButton.disabled = !backStack.length;
    }
    function scrollCardIntoGraph(card) {
      if (!card || card.hidden) return;
      const rect = card.getBoundingClientRect(), box = graph.getBoundingClientRect();
      if (rect.top < box.top || rect.bottom > box.bottom) graph.scrollTop += rect.top - box.top - 8;
    }
    function syncPage(page, announce = false) {
      page = Number(page);
      if (!pageArticles.has(page)) return;
      current = page; knownPage = page;
      currentLabel.textContent = 'P' + page;
      toggle.setAttribute('aria-label', (expanded ? '收起' : '展开') + '知识图谱，当前原 PPT 第' + page + '页');
      if (!data) return;
      if (!data.nodes.some(node => node.id === selectedId && node.pages.includes(page))) selectedId = data.nodes.find(node => node.pages.includes(page))?.id || data.nodes[0].id;
      cards.forEach((card, id) => {
        const inPage = data.nodes.find(node => node.id === id).pages.includes(page);
        card.classList.toggle('km-node-current', inPage);
        card.classList.toggle('km-node-selected', id === selectedId);
        const primary = card.querySelector('.km-node-title');
        if (inPage) primary.setAttribute('aria-current', 'page'); else primary.removeAttribute('aria-current');
      });
      pageButtons.forEach((buttons, p) => buttons.forEach(b => {
        b.classList.toggle('km-page-current', p === page);
        if (p === page) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
      }));
      if (announce) live.textContent = '已定位原 PPT 第' + page + '页与本页讲义。知识图谱保持' + (expanded ? '展开。' : '收起，可随时展开。');
    }
    function navigate(page, nodeId, options = {}) {
      page = Number(page);
      if (!pageArticles.has(page)) { live.textContent = '此原 PPT 页不存在，未跳转。'; return false; }
      const node = data?.nodes.find(item => item.id === nodeId);
      const anchor = options.anchor || node?.anchors[page] || node?.anchor || '';
      const destination = page + ':' + anchor;
      const previous = snapshot();
      const token = ++navigationToken;
      cancelPendingDockReveal();
      if (!options.restore && (page !== current || destination !== lastDestination)) {
        backStack.push(previous); if (backStack.length > 100) backStack.shift();
      }
      selectedId = nodeId || selectedId; lastDestination = destination;
      isNavigating = true;
      const url = new URL(root.location.href);
      url.hash = 'p' + String(page).padStart(2, '0');
      if (page !== current) {
        // Existing viewers replace history. Push BEFORE their select handler so Back works.
        try {
          const state = { ...(root.history.state || {}), studyKnowledgePage: page };
          if (options.restore) root.history.replaceState(state, '', url.href);
          else root.history.pushState(state, '', url.href);
        } catch (_) {}
      }
      select.value = String(page);
      select.dispatchEvent(new Event('change', {bubbles: true}));
      syncPage(page, true); updateBack();
      // The original viewer resets both panes in its animation frame. Run after it.
      root.requestAnimationFrame(() => {
        if (token !== navigationToken) return;
        const article = pageArticles.get(page);
        if (article.hidden) {
          live.textContent = '现有阅读器未能定位此页，请用顶部页码选择器重试。';
          isNavigating = false; return;
        }
        const teaching = article.querySelector('.teaching');
        const viewport = article.querySelector('.slide-viewport');
        if (options.restore) {
          const saved = options.restore;
          if (teaching) { teaching.scrollTop = saved.teachingTop; teaching.scrollLeft = saved.teachingLeft; }
          if (viewport) {
            // Restore through the original viewer controls, keeping its private scale state in sync.
            const toolbar = article.querySelector('.slide-toolbar');
            const zoomIn = toolbar?.querySelector('[data-zoom="in"]');
            const desired = Math.max(100, Math.min(300, saved.pptZoom || 100));
            let attempts = 0;
            while (zoomIn && !zoomIn.disabled && attempts++ < 8 &&
              (Number.parseInt(toolbar.querySelector('output')?.textContent, 10) || 100) < desired) zoomIn.click();
            viewport.scrollTop = saved.pptTop; viewport.scrollLeft = saved.pptLeft;
          }
          search.value = saved.search; filterGraph(); graph.scrollTop = saved.mapTop;
          lastDestination = saved.destination;
          // Revealing a page can update formula-scroll hints in ResizeObserver
          // after this frame, shifting the browser's scroll anchor. Reapply once
          // on the following frame, after that layout, never after a newer jump.
          root.requestAnimationFrame(() => {
            if (token !== navigationToken || article.hidden || current !== page) return;
            if (teaching) { teaching.scrollTop = saved.teachingTop; teaching.scrollLeft = saved.teachingLeft; }
            if (viewport) { viewport.scrollTop = saved.pptTop; viewport.scrollLeft = saved.pptLeft; }
            main.scrollTop = saved.readerTop || 0; main.scrollLeft = saved.readerLeft || 0;
            root.scrollTo?.(saved.windowLeft || 0, saved.windowTop || 0);
          });
        } else if (teaching) {
          // IDs are resolved only inside this page's teaching pane, never arbitrary selectors.
          const target = anchor ? [...teaching.querySelectorAll('[id]')].find(el => el.id === anchor) : null;
          if (target) teaching.scrollTop += target.getBoundingClientRect().top - teaching.getBoundingClientRect().top - 12;
          else teaching.scrollTop = 0;
        }
        // Compact layouts scroll the page as well as the two reading panes.
        // Keep the graph in place on jumps, and restore the originating page view.
        const windowPosition = options.restore || previous;
        main.scrollTop = windowPosition.readerTop || 0; main.scrollLeft = windowPosition.readerLeft || 0;
        root.scrollTo?.(windowPosition.windowLeft || 0, windowPosition.windowTop || 0);
        syncPage(page); isNavigating = false;
      });
      return true;
    }
    backButton.addEventListener('click', () => {
      const saved = backStack.pop(); if (!saved) return;
      navigate(saved.page, saved.nodeId, {restore: saved}); updateBack();
      if (!backStack.length) toggle.focus({preventScroll: true});
    });
    function filterGraph() {
      if (!data) return;
      const query = search.value.trim().toLocaleLowerCase();
      const pageMatch = query.match(/^(?:p|第)?\s*(\d+)\s*页?$/i);
      let visible = 0;
      data.nodes.forEach(node => {
        const match = !query || (pageMatch ? node.pages.includes(Number(pageMatch[1])) :
          [node.label, node.summary, node.section].join(' ').toLocaleLowerCase().includes(query));
        cards.get(node.id).hidden = !match; if (match) visible++;
      });
      groups.forEach(group => { group.hidden = ![...group.querySelectorAll('.km-node')].some(card => !card.hidden); });
      empty.hidden = visible !== 0;
      count.textContent = (query ? '找到 ' + visible + ' / ' : '') + data.nodes.length + ' 个节点 · ' + data.edges.length + ' 条关系 · 覆盖 ' + data.coveredPages.length + '/' + pages.length + ' 页';
    }
    search.addEventListener('input', filterGraph);
    locate.addEventListener('click', () => {
      search.value = ''; filterGraph(); setExpanded(true);
      const card = cards.get(selectedId); scrollCardIntoGraph(card); card?.querySelector('.km-node-title').focus({preventScroll: true});
    });
    read.addEventListener('click', () => {
      const teaching = pageArticles.get(current)?.querySelector('.teaching');
      if (!teaching) return;
      teaching.focus({preventScroll: true});
      if (root.matchMedia?.(compactQuery).matches) {
        // Compact readers have a separate scrolling region, never underneath
        // the diagram. Only this explicit action reveals the lecture and dock.
        main.scrollTop += teaching.getBoundingClientRect().top - main.getBoundingClientRect().top - 8;
        const top = (root.scrollY || 0) + workspace.getBoundingClientRect().top;
        root.scrollTo?.(root.scrollX || 0, Math.max(0, top));
      }
    });
    graph.addEventListener('keydown', event => {
      if (!event.target.classList.contains('km-node-title') || !['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
      const buttons = [...graph.querySelectorAll('.km-node:not([hidden]) .km-node-title')];
      const index = buttons.indexOf(event.target);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length-1 : Math.max(0, Math.min(buttons.length-1, index + (event.key === 'ArrowDown' ? 1 : -1)));
      event.preventDefault(); buttons[next]?.focus({preventScroll: true}); scrollCardIntoGraph(buttons[next]?.closest('.km-node'));
    });
    aside.addEventListener('keydown', event => {
      if (event.key === 'Escape' && expanded) {
        event.preventDefault(); setExpanded(false); toggle.focus({preventScroll: true});
      }
    });
    function onPageChange(event) {
      const page = Number(event.detail?.page);
      root.requestAnimationFrame(() => {
        if (isNavigating) return;
        const previousPage = knownPage;
        syncPage(pageArticles.has(page) ? visiblePage() : Number(select.value));
        if (current !== previousPage) { lastDestination = current + ':'; cancelPendingDockReveal(); }
      });
    }
    ['course:pagechange', 'em:pagechange', 'dsp:pagechange'].forEach(name => root.addEventListener(name, onPageChange));
    root.addEventListener('hashchange', () => root.requestAnimationFrame(() => syncPage(visiblePage())));
    root.addEventListener('popstate', () => {
      ++navigationToken; isNavigating = false; cancelPendingDockReveal();
      const p = Number(root.location.hash.replace(/^#p/, ''));
      if (pageArticles.has(p) && visiblePage() !== p) { select.value = String(p); select.dispatchEvent(new Event('change', {bubbles: true})); }
      root.requestAnimationFrame(() => syncPage(visiblePage(), true));
    });

    function render(map) {
      data = map;
      const nodeIndex = new Map(data.nodes.map(node => [node.id, node]));
      title.textContent = data.edges.length ? '知识图谱' : '逐页知识索引';
      description.textContent = data.title + '。点击节点或 P 页码，原 PPT 与讲义同步定位，图谱不会关闭。';
      const sectionMap = new Map();
      data.nodes.forEach(node => {
        let section = sectionMap.get(node.section);
        if (!section) {
          section = element('section', 'km-group');
          const heading = element('h2', 'km-group-title', node.section);
          section.append(heading, element('ol', 'km-nodes'));
          sectionMap.set(node.section, section); groups.push(section); graph.append(section);
        }
        const card = element('li', 'km-node'); card.dataset.nodeId = node.id;
        const primary = button('km-node-title', node.label, node.label + '，跳转原 PPT 第' + node.pages[0] + '页');
        primary.addEventListener('click', () => navigate(node.pages[0], node.id));
        card.append(primary);
        if (node.source === 'supplement') card.append(element('span', 'km-source', '补充讲解 · 回链原PPT'));
        if (node.summary) card.append(element('p', 'km-summary', node.summary));
        const row = element('div', 'km-pages'); row.setAttribute('role', 'group'); row.setAttribute('aria-label', node.label + '对应的原 PPT 页');
        node.pages.forEach(page => {
          const link = button('km-page', 'P' + page, node.label + '，原 PPT 第' + page + '页及本页讲义');
          link.dataset.page = String(page);
          link.addEventListener('click', () => navigate(page, node.id));
          if (!pageButtons.has(page)) pageButtons.set(page, []);
          pageButtons.get(page).push(link); row.append(link);
        });
        card.append(row);
        const incoming = data.edges.filter(edge => edge.to === node.id);
        const outgoing = data.edges.filter(edge => edge.from === node.id);
        if (incoming.length || outgoing.length) {
          const relations = element('ul', 'km-relations'); relations.setAttribute('aria-label', node.label + '的概念关系');
          // Show incoming edges, plus outgoing only for roots, so each directed edge is readable without noise.
          const shownEdges = incoming.length ? incoming.map(edge => ({edge, direction: 'in'})) : outgoing.map(edge => ({edge, direction: 'out'}));
          shownEdges.forEach(({edge, direction}) => {
            const other = nodeIndex.get(direction === 'in' ? edge.from : edge.to);
            const relation = element('li', 'km-relation');
            const target = button('km-related', other.label, (direction === 'in' ? '前置或关联：' : '后续关联：') + other.label + '，原 PPT 第' + other.pages[0] + '页');
            target.addEventListener('click', () => {
              navigate(other.pages[0], other.id);
              search.value = ''; filterGraph(); scrollCardIntoGraph(cards.get(other.id));
              cards.get(other.id)?.querySelector('.km-node-title').focus({preventScroll: true});
            });
            const arrow = element('span', 'km-edge-label', direction === 'in' ? ' → ' + edge.label + ' → 本节点' : '本节点 → ' + edge.label + ' → ');
            if (direction === 'in') relation.append(target, arrow); else relation.append(arrow, target);
            relations.append(relation);
          });
          card.append(relations);
        }
        section.querySelector('ol').append(card); cards.set(node.id, card);
      });
      if (data.missingPages.length) {
        notice.hidden = false; notice.textContent = '图谱尚未覆盖原 PPT P' + data.missingPages.join('、P') + '。这些页仍可由顶部页码选择器访问。';
      }
      filterGraph(); syncPage(visiblePage());
      if (!search.value) scrollCardIntoGraph(cards.get(selectedId));
      aside.dataset.ready = 'true';
      if (mapEntryRequested && !entryRevealConsumed) {
        entryRevealConsumed = true;
        if (expanded && !entryInteraction) changeDockVisibility(true, dockPosition());
      }
      root.dispatchEvent(new CustomEvent('knowledge-map:ready', {detail: {id: data.id, nodes: data.nodes.length, pages: data.coveredPages.length}}));
    }
    function fallback(reason) {
      notice.hidden = true;
      const index = {version: 1, id: 'page-index', title: '原 PPT 逐页索引（概念关系尚待整理）', nodes: articles.map(article => ({
        id: 'page-' + article.dataset.page,
        label: article.querySelector('.page-heading h1, .page-heading h2, h1, h2')?.textContent.trim() || '原 PPT 第' + article.dataset.page + '页',
        pages: [Number(article.dataset.page)], section: '真实原 PPT 页码'
      }))};
      render(validateKnowledgeMap(index, pages));
      notice.hidden = false;
      notice.textContent = reason || '本章暂提供真实页码索引，概念关系尚待补全。';
      aside.dataset.fallback = 'true';
    }
    root.CourseKnowledgeMap = {validate: validateKnowledgeMap, navigate,
      current: () => ({page: current, nodeId: selectedId, expanded, backCount: backStack.length}),
      get data() { return data; }};
    if (!dataURL) { fallback(); return; }
    let url;
    try {
      url = new URL(dataURL, document.baseURI);
      if (url.origin !== root.location.origin) throw new Error('知识图谱必须为本站同源文件。');
    } catch (error) { fallback(error.message); return; }
    root.fetch(url.href, {credentials: 'same-origin'}).then(response => {
      if (!response.ok) throw new Error('知识图谱文件未能载入。');
      return response.json();
    }).then(json => render(validateKnowledgeMap(json, pages))).catch(error => {
      fallback('概念图谱暂未载入，已保留真实逐页索引。' + error.message);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootstrap, {once: true});
  else bootstrap();
})(typeof window !== 'undefined' ? window : globalThis);
