/* Full-width redraw reader. Intentionally does not read or write learning-progress storage. */
(() => {
  'use strict';
  const sections = ['21', '22', '23', '24', '25', '26'];
  const titles = {21:'离散时间序列的傅里叶变换（DTFT）',22:'周期序列与离散傅里叶级数（DFS）',23:'有限长序列的离散傅里叶变换（DFT）',24:'频域采样定理',25:'快速傅里叶变换（FFT）',26:'DFT 的应用'};
  const $ = selector => document.querySelector(selector);
  const lesson = $('#lesson');
  const data = new Map();
  let current = '', pass = 'first', requestId = 0, openedBy = null;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const localPath = value => {
    if (typeof value !== 'string' || !value || /^(?:[a-z]+:|\/\/)/i.test(value) || /(?:^|\/)\.\.(?:\/|$)/.test(value)) return '';
    return value;
  };
  const html = value => {
    const template = document.createElement('template');
    template.innerHTML = String(value ?? '');
    template.content.querySelectorAll('script,iframe,object,embed,style,link,meta,form').forEach(el => el.remove());
    template.content.querySelectorAll('*').forEach(el => {
      [...el.attributes].forEach(attr => {
        if (/^on/i.test(attr.name) || /^(?:srcdoc)$/i.test(attr.name) || /^(?:href|src|xlink:href)$/i.test(attr.name) && /^\s*(?:javascript|data|vbscript):/i.test(attr.value)) el.removeAttribute(attr.name);
      });
    });
    return template.innerHTML;
  };
  const cardId = (section, id) => `${section.id}/${id}`;
  const normalize = input => {
    if (!input || typeof input !== 'object' || !/^dsp-2[1-6]$/.test(input.id) || !input.title || !Array.isArray(input.cards) || !input.cards.length) throw Error('本节内容文件尚不完整');
    const ids = new Set();
    input.cards.forEach((card, index) => {
      card.id = String(card.id || `card-${index + 1}`);
      if (ids.has(card.id)) throw Error('知识板编号重复');
      ids.add(card.id);
      card.level = card.level === 'deep' ? 'deep' : 'essential';
      card.sourcePages = Array.isArray(card.sourcePages) ? [...new Set(card.sourcePages.map(Number).filter(n => Number.isInteger(n) && n > 0))] : [];
    });
    return input;
  };
  async function getSection(id) {
    if (!data.has(id)) {
      const code = id.replace('dsp-', '');
      data.set(id, fetch(`dsp-redraw/ch2-${code}.json`).then(response => {
        if (!response.ok) throw Error('本节重绘与辅导尚未完成');
        return response.json();
      }).then(normalize));
    }
    return data.get(id);
  }
  function sourceText(section, pages) {
    if (!pages?.length) return '';
    return `${section.number || section.id.replace('dsp-', '').split('').join('.')} · 原PPT P${pages.join('、P')}`;
  }
  function pageHref(section, page) {
    const path = localPath(section.source?.readerUrl);
    return path ? `${path.split('#')[0]}#p${String(page).padStart(2, '0')}` : '';
  }
  function pageImage(section, page) {
    const pattern = localPath(section.source?.imagePattern);
    return pattern ? pattern.replace('{page}', String(page)) : '';
  }
  function sourceLinks(section, pages) {
    return pages.map(page => {
      const href = pageHref(section, page);
      return href ? `<a href="${escape(href)}" target="_blank" rel="noopener" aria-label="打开 ${escape(section.number)} 原PPT第${page}页">P${page} ↗</a>` : `<span>P${page}</span>`;
    }).join('');
  }
  function figureHtml(figure, kind = 'redraw') {
    if (!figure || !localPath(figure.src)) return '';
    const alt = figure.alt || figure.caption || '本节重绘图';
    return `<figure class="dr-figure" data-kind="${kind}"><div class="dr-figure-toolbar"><span>${kind === 'source' ? '原页仅作对照；可能保留转换问题' : '矢量重绘 · 窄屏可横向滑动'}</span><button type="button" data-open-figure>全屏看清楚 ↗</button></div><div class="dr-figure-scroll" tabindex="0" role="region" aria-label="${escape(alt)}，可横向滚动"><img src="${escape(figure.src)}" alt="${escape(alt)}" loading="lazy" decoding="async" tabindex="0" role="button" aria-label="放大：${escape(alt)}"></div>${figure.caption ? `<figcaption>${escape(figure.caption)}</figcaption>` : ''}</figure>`;
  }
  function referenceHtml(card) {
    const book = card.textbook;
    const pages = value => escape(Array.isArray(value) ? value.join('、') : value || '未标明');
    return `${book ? `<p>教材对照：${escape(book.edition || '方勇第3版')}，印刷页 ${pages(book.printedPages)}；PDF文件页 ${pages(book.pdfPages)}。</p>` : ''}${card.corrections?.length ? `<div class="dr-corrections"><strong>原页核对说明</strong><ul>${card.corrections.map(item => `<li>${item.sourcePage ? `P${escape(item.sourcePage)}：` : ''}${escape(item.text || item)}</li>`).join('')}</ul></div>` : ''}`;
  }
  function comparisonHtml(section, card) {
    const pages = card.sourcePages || [];
    if (!pages.length) return '';
    const hasImage = !!pageImage(section, pages[0]);
    return `<details class="dr-source-compare" data-source-card="${escape(card.id)}"><summary>${hasImage ? '原PPT对照 · 按需打开，不挤占重绘' : '原PPT来源 · 查看对应页码'}</summary><p>${escape(section.source?.title || '原课件')} · ${sourceText(section, pages)}</p><div class="dr-source-links">${sourceLinks(section, pages)}</div>${referenceHtml(card)}${hasImage ? `<label>选择原页 <select aria-label="${escape(card.title)}的原PPT对照页">${pages.map(page => `<option value="${page}">原PPT P${page}</option>`).join('')}</select></label><div class="dr-source-image-slot"></div>` : '<p>此小节原课件图尚未在本站公开；这里保留真实源页映射，不提供无效原图链接。</p>'}</details>`;
  }
  function cardHtml(section, card, index) {
    const deep = card.level === 'deep';
    const isExample = card.type === 'example';
    const label = deep ? '扩展 · 第二遍' : isExample ? '必学 · 代表例题' : '必学 · 第一遍';
    const levelClass = deep ? 'deep' : isExample ? 'example' : '';
    const top = `<div><span class="dr-level ${levelClass}">${label}</span><h3>${escape(card.title)}</h3><p class="dr-card-source">${escape(sourceText(section, card.sourcePages))}</p></div>`;
    const figures = card.figures || (card.figure ? [card.figure] : []);
    const body = `<div class="dr-card-body">${html(card.bodyHtml)}${figures.map(figure => figureHtml(figure)).join('')}${card.pitfall ? `<aside class="dr-pitfall"><strong>避坑：</strong>${escape(card.pitfall)}</aside>` : ''}${card.check ? `<details class="dr-check"><summary>停一下，自己答：${escape(card.check.question)}</summary><div class="dr-answer">${html(card.check.answerHtml)}</div></details>` : ''}${comparisonHtml(section, card)}</div>`;
    return deep ? `<details class="dr-card dr-deep-card" id="${escape(cardId(section, card.id))}" data-card-id="${escape(card.id)}"><summary>${top}</summary>${body}</details>` : `<article class="dr-card" id="${escape(cardId(section, card.id))}" data-card-id="${escape(card.id)}"><header class="dr-card-head"><span class="dr-card-number">${String(index + 1).padStart(2, '0')}</span>${top}</header>${body}</article>`;
  }
  function exampleCard(section) {
    const example = section.example;
    if (!example) return null;
    const steps = Array.isArray(example.stepsHtml) ? example.stepsHtml.join('') : example.stepsHtml;
    return {id:'representative-example',type:'example',title:example.title || '一道代表例题',level:'essential',sourcePages:example.sourcePages || [],bodyHtml:`<div class="dr-example-step"><h4>已知与所求</h4>${html(example.problemHtml)}</div><div class="dr-example-step"><h4>为什么这样做 · 逐步解答</h4>${html(steps)}</div><div class="dr-example-step"><h4>结果</h4>${html(example.answerHtml)}</div>${example.checkHtml ? `<div class="dr-example-step"><h4>检查结果</h4>${html(example.checkHtml)}</div>` : ''}`,figure:example.figure,figures:example.figures,pitfall:example.pitfall,textbook:example.textbook,corrections:example.corrections};
  }
  function pageMapHtml(section, cards) {
    const count = Number(section.source?.pageCount) || Math.max(0, ...cards.flatMap(card => card.sourcePages || []));
    if (!count) return '';
    const mapped = Array.from({length:count}, (_, n) => {
      const page = n + 1;
      const declared = section.pageMap?.find(item => Number(item.page) === page);
      const links = cards.filter(card => card.sourcePages?.includes(page) || declared?.cardIds?.includes(card.id));
      return `<div class="dr-map-item"><strong>原PPT P${page}</strong>${links.length ? links.map(card => `<a href="#${escape(cardId(section, card.id))}">${escape(card.title)}</a>`).join('') : declared?.note ? '<span>封面 / 背景 / 重复页，见说明（非独立知识点）</span>' : '<span class="dr-unmapped">本页映射待补齐，不能视为已覆盖</span>'}${declared?.note ? `<small>${escape(declared.note)}</small>` : ''}</div>`;
    }).join('');
    return `<details class="dr-page-map"><summary>原PPT逐页索引 · ${count} 页如何对应知识板</summary><p>按知识组织重绘，合并重复或铺垫页，但保留每一原页的对应位置。页号是PPT物理页，不是教材页。</p><div class="dr-map-grid">${mapped}</div></details>`;
  }
  function renderSection(section) {
    const essential = section.cards.filter(card => card.level !== 'deep');
    const deep = section.cards.filter(card => card.level === 'deep');
    const example = exampleCard(section);
    // Put the worked example before optional deep material: the first pass is a bounded route.
    const cards = [...essential, ...(example ? [example] : []), ...deep];
    const corrections = section.corrections || [];
    const textbook = section.textbook;
    const firstMinutes = Number(section.firstPassMinutes);
    const deepMinutes = Number(section.deepPassMinutes);
    lesson.innerHTML = `<header class="dr-section-head" id="${escape(section.id)}"><p class="dr-eyebrow">SECTION ${escape(section.number || '')} · ${essential.length} 块必学${deep.length ? ` / ${deep.length} 块扩展` : ''}</p><h2>${escape(section.number || '')} ${escape(section.title)}</h2><p>${escape(section.brief)}</p><div class="dr-time-chips">${firstMinutes > 0 ? `<span class="dr-chip">第一遍约 ${firstMinutes} 分钟</span>` : ''}${deepMinutes > 0 ? `<span class="dr-chip">第二遍约 ${deepMinutes} 分钟</span>` : ''}<span class="dr-chip">主图全宽 · 原图按需对照</span></div><p class="dr-time-disclaimer">时间为建议安排，并非实测或学习保证；难点可以停下，不必赶进度。</p></header>${section.firstPass?.length ? `<aside class="dr-first-goals"><h3>这一遍，带走这些就够了</h3><ul>${section.firstPass.map(item => `<li>${escape(item)}</li>`).join('')}</ul></aside>` : ''}${cards.map((card, index) => cardHtml(section, card, index)).join('')}${section.pitfalls?.length ? `<aside class="dr-corrections"><h3>本节易错清单</h3><ul>${section.pitfalls.map(item => `<li>${escape(item)}</li>`).join('')}</ul></aside>` : ''}${corrections.length ? `<aside class="dr-corrections"><h3>原课件 / 教材的核对与纠正</h3><ul>${corrections.map(item => `<li>${item.sourcePage ? `<strong>P${escape(item.sourcePage)}：</strong>` : ''}${escape(item.text || item)}</li>`).join('')}</ul></aside>` : ''}${textbook ? `<p class="dr-card-source">教材对照：印刷页 ${escape(Array.isArray(textbook.printedPages) ? textbook.printedPages.join('、') : textbook.printedPages)}；PDF文件页 ${escape(Array.isArray(textbook.pdfPages) ? textbook.pdfPages.join('、') : textbook.pdfPages)}。两种页码不混用。</p>` : ''}${section.sourceNote ? `<p class="dr-card-source">${escape(section.sourceNote)}</p>` : ''}${pageMapHtml(section, cards)}${section.deepLinks?.length ? `<section class="dr-deep-links"><h3>第二遍，再按需深入</h3>${section.deepLinks.filter(link => localPath(link.href)).map(link => `<a href="${escape(link.href)}">${escape(link.label)} ↗</a>`).join('')}</section>` : ''}`;
    $('#contents-title').textContent = `${section.number} · 本节目录`;
    $('#contents-list').innerHTML = cards.map(card => `<a href="#${escape(cardId(section, card.id))}"><span>${card.level === 'deep' ? '扩展' : card.type === 'example' ? '例题' : '必学'}</span>${escape(card.title)}</a>`).join('');
    lesson.querySelectorAll('.dr-source-compare').forEach(details => {
      const card = cards.find(item => item.id === details.dataset.sourceCard);
      const select = details.querySelector('select');
      const update = () => {
        if (!select) return;
        const page = Number(select.value);
        details.querySelector('.dr-source-image-slot').innerHTML = figureHtml({src:pageImage(section, page),alt:`${section.number} 原PPT第${page}页`,caption:'原PPT对照页，可能保留转换缺陷；主阅读请看上方重绘与公式。'}, 'source');
      };
      details.addEventListener('toggle', () => {if (details.open && !details.querySelector('.dr-source-image-slot img')) update();});
      select?.addEventListener('change', update);
    });
    lesson.querySelectorAll('.dr-card-body table').forEach(table => {
      if (table.parentElement.classList.contains('table-scroll')) return;
      const wrap = document.createElement('div');wrap.className = 'table-scroll';table.replaceWith(wrap);wrap.append(table);
    });
    lesson.querySelectorAll('.formula,.math,.display-math,.math-block').forEach(block => {
      block.tabIndex = 0;
      block.setAttribute('role', 'region');block.setAttribute('aria-label', '公式，可横向滚动');
    });
    document.title = `DSP ${section.number} · ${section.title} · 清晰重绘`;
    applyPass(false);
  }
  function applyPass(announce = true) {
    document.querySelectorAll('[data-pass]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.pass === pass)));
    lesson.querySelectorAll('.dr-deep-card').forEach(details => {details.open = pass === 'deep';});
    $('#mode-hint').textContent = pass === 'first' ? '先读必学和代表例题；“扩展 · 第二遍”保持折叠，需要时再打开。' : '已展开本节深挖：补推导、辨条件、做检查。必学仍保留，方便回看。';
    if (announce) $('#mode-hint').setAttribute('role','status');
  }
  function routeInfo() {
    let hash = '';try {hash = decodeURIComponent(location.hash.slice(1));} catch (_) {}
    const [requested, ...rest] = hash.split('/');
    return {id:/^dsp-2[1-6]$/.test(requested) ? requested : (current || 'dsp-21'), card:rest.join('/')};
  }
  function jumpToCard(id, card) {
    if (!card) return;
    const target = document.getElementById(`${id}/${card}`);
    if (target) {if (target.tagName === 'DETAILS') target.open = true;target.scrollIntoView({block:'start'});}
  }
  async function route() {
    if ($('#figure-dialog').open) $('#figure-dialog').close();
    if ($('#contents-dialog').open) $('#contents-dialog').close();
    const {id, card} = routeInfo();
    if (id === current && lesson.dataset.loaded === id) {jumpToCard(id, card);return;}
    const token = ++requestId;
    current = id;
    lesson.dataset.loaded = '';
    lesson.setAttribute('aria-busy', 'true');
    lesson.innerHTML = '<div class="dr-loading" role="status">正在载入本节辅导…</div>';
    $('#section-nav').querySelectorAll('a').forEach(link => {if (link.hash === `#${id}`) link.setAttribute('aria-current', 'page');else link.removeAttribute('aria-current');});
    const index = sections.indexOf(id.replace('dsp-', ''));
    const prev = $('#previous-section'), next = $('#next-section');
    prev.hidden = index === 0;next.hidden = index === sections.length - 1;
    prev.href = `#dsp-${sections[Math.max(0, index - 1)]}`;next.href = `#dsp-${sections[Math.min(sections.length - 1, index + 1)]}`;
    prev.textContent = index ? `← 2.${index} 上一节` : '上一节';next.textContent = index < 5 ? `下一节 2.${index + 2} →` : '下一节';
    try {
      const section = await getSection(id);
      if (token !== requestId) return;
      renderSection(section);
      lesson.dataset.loaded = id;
      if (card) jumpToCard(id, card);
      else if (location.hash) lesson.scrollIntoView({block:'start'});
    } catch (error) {
      if (token !== requestId) return;
      lesson.innerHTML = `<section class="dr-error"><p class="dr-eyebrow">${escape(id.replace('dsp-', '').split('').join('.'))} · 尚未完成</p><h2>${escape(titles[id.replace('dsp-', '')])}</h2><p>本节重绘与辅导尚未成功载入，不能视为已完成。其他小节仍可正常阅读。</p><p><a href="dsp.html">返回现有 DSP 目录</a>，或刷新后重试。</p><small>${escape(error.message)}</small></section>`;
      $('#contents-list').innerHTML = '<p>本节尚无可用目录。</p>';
    } finally {if (token === requestId) lesson.setAttribute('aria-busy', 'false');}
  }
  const contents = $('#contents-dialog');
  $('#open-contents').addEventListener('click', () => contents.showModal());
  $('[data-close-contents]').addEventListener('click', () => contents.close());
  contents.addEventListener('click', event => {if (event.target.closest('a')) contents.close();});
  document.querySelectorAll('[data-pass]').forEach(button => button.addEventListener('click', () => {pass = button.dataset.pass;applyPass();}));
  // The fullscreen dialog uses its own scroll surface; there is no forced two-column comparison.
  const viewer = $('#figure-dialog'), viewerImage = $('#figure-image'), canvas = $('#figure-canvas');
  let naturalWidth = 960, naturalHeight = 600, scale = 1;
  const setScale = value => {
    scale = Math.max(.15, Math.min(4, value));
    viewerImage.style.width = `${Math.round(naturalWidth * scale)}px`;
    $('#zoom-value').value = `${Math.round(scale * 100)}%`;
    $('#zoom-out').disabled = scale <= .15;
    $('#zoom-in').disabled = scale >= 4;
  };
  const widthScale = () => (canvas.clientWidth - (innerWidth <= 450 ? 16 : 30)) / naturalWidth;
  const fitScale = () => Math.max(.15, Math.min(4, widthScale(), (canvas.clientHeight - 30) / naturalHeight));
  const readableScale = () => Math.max(widthScale(), Math.min(1, 900 / naturalWidth));
  function openFigure(figure, trigger) {
    const image = figure.querySelector('img');
    if (!image) return;
    openedBy = trigger;
    const caption = figure.querySelector('figcaption')?.textContent || '';
    $('#figure-dialog-title').textContent = `${figure.dataset.kind === 'source' ? '原页对照 · ' : ''}${figure.closest('.dr-card')?.querySelector('h3')?.textContent || '清晰大图'}`;
    $('#figure-caption').textContent = caption;
    $('#open-figure-file').href = image.getAttribute('src');
    viewerImage.alt = image.alt;
    naturalWidth = image.naturalWidth || 960;
    naturalHeight = image.naturalHeight || 600;
    viewerImage.src = image.src;
    if (!viewer.open) viewer.showModal();
    document.body.style.overflow = 'hidden';
    setScale(readableScale());
    canvas.scrollLeft = 0;canvas.scrollTop = 0;
    viewerImage.onload = () => {naturalWidth = viewerImage.naturalWidth || 960;naturalHeight = viewerImage.naturalHeight || 600;setScale(readableScale());};
    $('#close-figure').focus();
  }
  // Keep authored SVG labels near their native size on phones; only the image region scrolls.
  lesson.addEventListener('load', event => {
    const image = event.target;
    if (image instanceof HTMLImageElement && image.closest('.dr-figure-scroll')) image.style.minWidth = `${Math.min(image.naturalWidth || 960, 960)}px`;
  }, true);
  lesson.addEventListener('click', event => {
    const control = event.target.closest('[data-open-figure],.dr-figure-scroll img');
    if (control) openFigure(control.closest('.dr-figure'), control);
  });
  lesson.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('.dr-figure-scroll img')) {event.preventDefault();openFigure(event.target.closest('.dr-figure'), event.target);}
  });
  $('#close-figure').addEventListener('click', () => viewer.close());
  viewer.addEventListener('close', () => {document.body.style.overflow = '';(openedBy?.isConnected ? openedBy : lesson).focus({preventScroll:true});});
  $('#zoom-out').addEventListener('click', () => setScale(scale / 1.25));
  $('#zoom-in').addEventListener('click', () => setScale(scale * 1.25));
  $('#zoom-fit').addEventListener('click', () => {setScale(fitScale());canvas.scrollLeft = 0;canvas.scrollTop = 0;});
  $('#zoom-readable').addEventListener('click', () => setScale(readableScale()));
  viewer.addEventListener('keydown', event => {
    if (event.key === '+' || event.key === '=') {event.preventDefault();setScale(scale * 1.25);}
    if (event.key === '-') {event.preventDefault();setScale(scale / 1.25);}
  });
  window.addEventListener('hashchange', route);
  route();
  Promise.allSettled(sections.map(code => getSection(`dsp-${code}`))).then(results => {
    const complete = results.filter(item => item.status === 'fulfilled');
    const minutes = complete.reduce((sum, item) => sum + (Number(item.value.firstPassMinutes) || 0), 0);
    if (complete.length === 6 && minutes > 0) $('#course-time').textContent = `全章第一遍建议约 ${minutes} 分钟；第二遍分节深入。时间为估计，非实测。`;
    else if (complete.length < 6) $('#course-time').textContent = `${complete.length}/6 节已可载入；未完成小节会明确提示。各节时间为建议，非实测。`;
  });
})();
