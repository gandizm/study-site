/* Optional local-neighborhood view for the persistent knowledge-map reader. */
(function(root) {
  'use strict';
  function neighborhoodModel(map, nodeId, limit = 3) {
    const nodes = new Map(map.nodes.map(node => [node.id, node]));
    const current = nodes.get(nodeId) || map.nodes[0];
    const incoming = new Map(), outgoing = new Map();
    for (const edge of map.edges || []) {
      const collection = edge.to === current.id ? incoming : edge.from === current.id ? outgoing : null;
      if (!collection) continue;
      const otherId = edge.to === current.id ? edge.from : edge.to;
      if (!nodes.has(otherId)) continue;
      if (!collection.has(otherId)) collection.set(otherId, {node: nodes.get(otherId), labels: []});
      const labels = collection.get(otherId).labels;
      if (!labels.includes(edge.label)) labels.push(edge.label);
    }
    const count = Math.max(1, Math.min(3, Number.isInteger(limit) ? limit : 3));
    return {current, incoming: [...incoming.values()].slice(0, count), outgoing: [...outgoing.values()].slice(0, count),
      incomingTotal: incoming.size, outgoingTotal: outgoing.size};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {neighborhoodModel};
  if (!root.document) return;
  const document = root.document;
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }
  function button(className, text) { const node = el('button', className, text); node.type = 'button'; return node; }
  function svg(tag, attrs) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
    return node;
  }
  function start() {
    const api = root.CourseKnowledgeMap;
    const panel = document.querySelector('#knowledge-map[data-ready="true"]');
    if (!api?.data || !panel || panel.querySelector('.kmn-view') || !api.data.edges.length) return;
    const content = panel.querySelector('.km-content');
    const list = panel.querySelector('.km-graph');
    const search = panel.querySelector('.km-search');
    const description = panel.querySelector('.km-description');
    const compact = root.matchMedia('(max-width: 520px)');
    let mode = 'graph', lastKey = '';
    panel.classList.add('kmn-enabled');
    description.hidden = true;
    const switcher = el('div', 'kmn-switcher'); switcher.setAttribute('role', 'tablist'); switcher.setAttribute('aria-label', '知识图谱视图');
    const graphTab = button('kmn-tab', '节点连线'); graphTab.id = 'kmn-graph-tab'; graphTab.setAttribute('role', 'tab'); graphTab.setAttribute('aria-controls', 'kmn-view');
    const listTab = button('kmn-tab', '概念清单'); listTab.id = 'kmn-list-tab'; listTab.setAttribute('role', 'tab'); listTab.setAttribute('aria-controls', 'kmn-list-view');
    switcher.append(graphTab, listTab); description.before(switcher);
    list.id = 'kmn-list-view'; list.setAttribute('role', 'tabpanel'); list.setAttribute('aria-labelledby', listTab.id);
    const view = el('section', 'km-graph kmn-view'); view.id = 'kmn-view'; view.setAttribute('role', 'tabpanel'); view.setAttribute('aria-labelledby', graphTab.id);
    list.before(view);
    // One independently scrollable controls column avoids overlapping grid rows
    // in short landscape layouts while retaining every control in list mode.
    const controls = el('div', 'kmn-controls');
    content.prepend(controls);
    controls.append(switcher, description, panel.querySelector('.km-actions'),
      panel.querySelector('.km-search-label'), panel.querySelector('.km-count'), panel.querySelector('.km-notice'));

    // The stable list shows each edge at its target, and outgoing edges at roots.
    // Complete non-root cards here so "all relations" means BOTH directions for
    // the selected concept without changing the validated graph or edge counts.
    const nodeIndex = new Map(api.data.nodes.map(node => [node.id, node]));
    for (const card of list.querySelectorAll('.km-node')) {
      const node = nodeIndex.get(card.dataset.nodeId);
      if (!node || !api.data.edges.some(edge => edge.to === node.id)) continue;
      const outgoing = api.data.edges.filter(edge => edge.from === node.id);
      const relations = card.querySelector('.km-relations');
      if (!relations) continue;
      for (const edge of outgoing) {
        const other = nodeIndex.get(edge.to);
        const relation = el('li', 'km-relation kmn-outgoing-relation');
        relation.dataset.from = node.id; relation.dataset.to = other.id;
        const target = button('km-related', other.label);
        target.setAttribute('aria-label', '出向关系：' + node.label + '，通过“' + edge.label + '”关联到' + other.label + '。打开原PPT P' + other.pages[0]);
        target.addEventListener('click', () => {
          go(other); search.value = ''; search.dispatchEvent(new Event('input', {bubbles:true}));
          root.requestAnimationFrame(() => {
            const destination = [...list.querySelectorAll('.km-node')].find(item => item.dataset.nodeId === other.id);
            destination?.querySelector('.km-node-title')?.focus({preventScroll:true});
          });
        });
        relation.append(el('span', 'km-edge-label', '本节点 → ' + edge.label + ' → '), target);
        relations.append(relation);
      }
    }

    function locateListCard() {
      const current = api.current();
      const card = [...list.querySelectorAll('.km-node')].find(card => card.dataset.nodeId === current.nodeId && !card.hidden);
      if (!card) return;
      const rect = card.getBoundingClientRect(), box = list.getBoundingClientRect();
      if (rect.top < box.top || rect.bottom > box.bottom) list.scrollTop += rect.top - box.top - 8;
    }
    function setMode(next) {
      mode = next === 'list' ? 'list' : 'graph';
      list.hidden = mode !== 'list'; view.hidden = mode !== 'graph';
      content.classList.toggle('kmn-graph-mode', mode === 'graph');
      graphTab.setAttribute('aria-selected', String(mode === 'graph')); listTab.setAttribute('aria-selected', String(mode === 'list'));
      graphTab.tabIndex = mode === 'graph' ? 0 : -1; listTab.tabIndex = mode === 'list' ? 0 : -1;
      if (mode === 'list') root.requestAnimationFrame(locateListCard);
      else { refresh(); root.requestAnimationFrame(revealCurrentGraph); }
    }
    function revealCurrentGraph() {
      if (view.hidden) return;
      const current = view.querySelector('.kmn-current-node');
      if (!current) return;
      const rect = current.getBoundingClientRect(), box = view.getBoundingClientRect();
      if (box.height <= 0) return;
      if (rect.top < box.top + 2 || rect.bottom > box.bottom - 2) {
        view.scrollTop += rect.top - box.top - Math.max(0, (box.height - rect.height) / 2);
      }
    }
    graphTab.addEventListener('click', () => setMode('graph'));
    listTab.addEventListener('click', () => setMode('list'));
    switcher.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 'graph' : event.key === 'End' ? 'list' : mode === 'graph' ? 'list' : 'graph';
      setMode(next); (next === 'graph' ? graphTab : listTab).focus({preventScroll: true});
    });
    search.addEventListener('input', () => setMode('list'));
    panel.querySelector('.km-locate').addEventListener('click', () => {
      setMode('graph'); view.querySelector('.kmn-current-node')?.focus({preventScroll: true});
    });
    panel.querySelector('.km-toggle').addEventListener('click', () => {
      if (api.current().expanded) root.requestAnimationFrame(revealCurrentGraph);
    });
    function go(node, page) {
      if (api.navigate(page || node.pages[0], node.id)) { lastKey = ''; refresh(); }
    }
    function refresh() {
      const state = api.current();
      const key = state.nodeId + ':' + state.page + ':' + compact.matches;
      if (lastKey === key) return;
      lastKey = key;
      const model = neighborhoodModel(api.data, state.nodeId, compact.matches ? 1 : 3);
      const hadFocus = view.contains?.(document.activeElement);
      view.replaceChildren();
      // A page button may have been reached by scrolling the tiny graph dock.
      // Keep the newly selected concept itself visible after every graph jump.
      view.scrollTop = 0;
      const heading = el('h2', 'kmn-heading', '当前概念的直接联系');
      const canvas = el('div', 'kmn-canvas'); canvas.setAttribute('role', 'group'); canvas.setAttribute('aria-label', model.current.label + '的局部节点连线图');
      const lines = svg('svg', {viewBox: '0 0 100 100', preserveAspectRatio: 'none', 'aria-hidden': 'true', focusable: 'false'});
      const defs = svg('defs');
      const marker = svg('marker', {id:'kmn-arrowhead',viewBox:'0 0 6 6',refX:'5.5',refY:'3',markerWidth:'3',markerHeight:'3',orient:'auto',markerUnits:'userSpaceOnUse'});
      marker.append(svg('path',{d:'M0,0 L6,3 L0,6 Z',fill:'currentColor'})); defs.append(marker); lines.append(defs); canvas.append(lines);
      const positions = count => count === 1 ? [50] : count === 2 ? [25,75] : [17,50,83];
      function sideNodes(items, side) {
        if (!items.length) {
          const empty = el('p', 'kmn-empty-side kmn-' + side, side === 'in' ? '本图起点' : '暂无出向关系');
          canvas.append(empty); return;
        }
        items.forEach((item, index) => {
          const y = positions(items.length)[index];
          const related = button('kmn-node kmn-' + side, '');
          related.style.top = y + '%';
          related.dataset.nodeId = item.node.id; related.title = item.node.label;
          const labels = item.labels.join(' / ');
          related.setAttribute('aria-label', side === 'in'
            ? item.node.label + '，通过“' + labels + '”关联到当前概念' + model.current.label + '。打开原PPT P' + item.node.pages[0]
            : '当前概念' + model.current.label + '，通过“' + labels + '”关联到' + item.node.label + '。打开原PPT P' + item.node.pages[0]);
          related.append(el('span', 'kmn-node-name', item.node.label), el('small', 'kmn-edge-caption', side === 'in' ? labels + ' →' : '→ ' + labels));
          related.addEventListener('click', () => go(item.node));
          canvas.append(related);
          lines.append(svg('path', {d: side === 'in'
            ? `M28,${y} C32,${y} 32,50 36,50`
            : `M64,50 C68,50 68,${y} 72,${y}`, fill:'none', stroke:'currentColor', 'stroke-width':'.6', 'marker-end':'url(#kmn-arrowhead)'}));
        });
      }
      sideNodes(model.incoming,'in'); sideNodes(model.outgoing,'out');
      const currentButton = button('kmn-node kmn-current-node', '');
      currentButton.title = model.current.label;
      currentButton.setAttribute('aria-current', 'page');
      currentButton.setAttribute('aria-label', '当前概念：' + model.current.label + '。当前原PPT第' + state.page + '页');
      currentButton.append(el('small', 'kmn-current-tag', '当前概念'), el('span', 'kmn-node-name', model.current.label));
      currentButton.addEventListener('click', () => go(model.current, model.current.pages.includes(state.page) ? state.page : model.current.pages[0]));
      canvas.append(currentButton);
      const pages = el('div', 'km-pages kmn-current-pages'); pages.setAttribute('role','group'); pages.setAttribute('aria-label', '当前概念的真实原 PPT 页码');
      model.current.pages.forEach(page => {
        const link = button('km-page' + (page === state.page ? ' km-page-current' : ''), 'P' + page);
        link.dataset.page=String(page); link.setAttribute('aria-label', model.current.label + '，原PPT第' + page + '页及本页讲义');
        if (page === state.page) link.setAttribute('aria-current','page');
        link.addEventListener('click', () => go(model.current, page)); pages.append(link);
      });
      const coverage = el('p', 'kmn-coverage', '显示 ' + model.incoming.length + '/' + model.incomingTotal + ' 个入向节点 · ' + model.outgoing.length + '/' + model.outgoingTotal + ' 个出向节点');
      const all = button('kmn-all-relations', '在清单查看全部关系');
      all.addEventListener('click', () => { search.value = ''; search.dispatchEvent(new Event('input', {bubbles:true})); setMode('list'); root.requestAnimationFrame(() => {
        const card = [...list.querySelectorAll('.km-node')].find(card => card.dataset.nodeId === api.current().nodeId);
        card?.querySelector('.km-node-title')?.focus({preventScroll: true});
      }); });
      view.append(heading, canvas, pages, coverage, all);
      if (hadFocus) currentButton.focus({preventScroll: true});
      root.requestAnimationFrame(revealCurrentGraph);
    }
    function deferredRefresh() { root.requestAnimationFrame(() => root.requestAnimationFrame(refresh)); }
    ['course:pagechange','em:pagechange','dsp:pagechange','hashchange','popstate'].forEach(type => root.addEventListener(type,deferredRefresh));
    panel.addEventListener('click', deferredRefresh);
    compact.addEventListener('change', () => { lastKey = ''; refresh(); });
    setMode('graph');
    root.CourseKnowledgeNeighborhood = {refresh, setMode, model: () => neighborhoodModel(api.data, api.current().nodeId, compact.matches ? 1 : 3)};
  }
  root.addEventListener('knowledge-map:ready', start);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})(typeof window !== 'undefined' ? window : globalThis);
