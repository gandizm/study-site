/* Isolated instructional UI. No storage, network requests or course submissions. */
(() => {
  'use strict';
  document.documentElement.classList.add('hw4-enhanced');
  document.querySelectorAll('[data-print]').forEach(button => {
    button.addEventListener('click', () => window.print());
  });
  let statusTimeout;
  function announce(message) {
    const status = document.getElementById('copy-status');
    if (!status) return;
    status.textContent = message;
    status.hidden = false;
    clearTimeout(statusTimeout);
    statusTimeout = setTimeout(() => { status.hidden = true; }, 6500);
  }
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const source = document.getElementById(button.dataset.copy);
      if (!source) return;
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(source.textContent);
        announce('答案已复制。树图也可通过“可抄答案 / 打印”查看。');
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(source);
        const selection = window.getSelection();
        if (selection) { selection.removeAllRanges(); selection.addRange(range); }
        announce('未能自动复制。答案已选中，请使用浏览器的复制操作。');
      }
    });
  });
  const player = document.getElementById('traversal-player');
  if (!player) return;
  const orders = {
    pre: {name:'先序', rule:'根 → 左 → 右', sequence:'ABCDEFGH'},
    in: {name:'中序', rule:'左 → 根 → 右', sequence:'BDCEAFHG'},
    post: {name:'后序', rule:'左 → 右 → 根', sequence:'DECBHGFA'}
  };
  const select = document.getElementById('traversal-order');
  const status = document.getElementById('traversal-status');
  const output = document.getElementById('traversal-sequence');
  const nodes = document.querySelectorAll('[data-tree="traversal"] [data-node]');
  const buttons = [...player.querySelectorAll('[data-traversal]')];
  let index = -1;
  function render() {
    const order = orders[select.value] || orders.pre;
    const seen = order.sequence.slice(0,index+1);
    const current = order.sequence[index];
    nodes.forEach(node => {
      node.classList.toggle('is-visited', seen.includes(node.dataset.node));
      node.classList.toggle('is-current', node.dataset.node === current);
    });
    output.replaceChildren();
    for (let i=0;i<seen.length;i++) {
      const chip = document.createElement('span');
      chip.textContent = seen[i];
      if(i===index) chip.setAttribute('aria-current','step');
      output.appendChild(chip);
    }
    status.textContent = index < 0
      ? `${order.name}：${order.rule}。点击“下一步”访问第一个结点。`
      : `${order.name} · 第 ${index+1} / 8 步：访问 ${current}。${index===7 ? '遍历完成：'+seen+'。' : '已输出：'+seen+'。'}`;
    buttons.forEach(button => {
      button.disabled = button.dataset.traversal === 'prev' ? index < 0
        : button.dataset.traversal === 'next' ? index >= order.sequence.length-1 : index < 0;
    });
  }
  select.addEventListener('change', () => { index=-1; render(); });
  buttons.forEach(button => button.addEventListener('click', () => {
    const action=button.dataset.traversal;
    if (action==='next') index=Math.min(index+1,7);
    if (action==='prev') index=Math.max(index-1,-1);
    if (action==='reset') index=-1;
    render();
  }));
  render();
})();
