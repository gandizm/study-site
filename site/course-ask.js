/* User-triggered context handoff, never a chat API or progress mutation. */
(()=>{'use strict';
const requestedFocus=new URLSearchParams(location.search).get('focus');
function setup(){
 const core=window.CourseAskCore;if(!core)return;
 const articles=[...document.querySelectorAll('.slide-page,.homework-question')];if(!articles.length)return;
 const isComm=location.pathname.includes('communications'),course=isComm?'通信原理':'计算机网络',chapter=isComm?'第4章':'CH1',courseId=isComm?'communications-ch4':'network-queueing',sourceId=isComm?'communications-ch4-main':'network-ch1-main',route=location.pathname;
 const dialog=document.createElement('dialog');dialog.className='ask-dot-dialog';dialog.setAttribute('aria-label','整理并复制提问');
 dialog.innerHTML='<div class="ask-dot-inner"><div class="ask-dot-top"><h2>复制这里的问题</h2><button class="ask-dot-button ask-dot-close" aria-label="关闭提问">×</button></div><p class="ask-dot-location"></p><div class="ask-dot-context"></div><label for="ask-dot-question">你卡在哪里？</label><textarea id="ask-dot-question"></textarea><div class="ask-dot-intents">'+['符号什么意思','这一步怎么来','为什么这样','和前页什么关系'].map(x=>'<button class="ask-dot-button" type="button">'+x+'</button>').join('')+'</div><div class="ask-dot-actions"><button class="ask-dot-button primary" data-action="copy">复制提问</button></div><p class="ask-dot-feedback" role="status" aria-live="polite"></p><details class="ask-dot-copy-preview"><summary>查看复制内容 / 手动复制</summary><textarea aria-label="待复制的提问内容"></textarea></details><p class="ask-dot-note">只携带当前内容位置和你的问题，不附学习进度、用时或账户数据。复制后请自行粘贴到要提问的对话。</p></div>';
 document.body.append(dialog);
 const input=dialog.querySelector('#ask-dot-question'),preview=dialog.querySelector('.ask-dot-copy-preview textarea'),status=dialog.querySelector('.ask-dot-feedback'),context=dialog.querySelector('.ask-dot-context');let current=null,lastFocus=null,pendingSelection=null;const recent=new WeakMap();
 function serial(node){
  if(!node)return '';
  if(node.nodeType===3)return node.textContent;
  if(node.nodeType===11)return [...node.childNodes].map(serial).join('');
  if(node.nodeType!==1)return '';
  if(node.matches('button,.ask-dot-page,.ask-dot-section,.math-scroll-hint'))return '';
  if(node.matches('svg.formula'))return '\\('+node.getAttribute('data-latex')+'\\)';
  return [...node.childNodes].map(serial).join('')+(/^(P|H[1-6]|DIV)$/.test(node.tagName)?'\n':'');
 }
 function stableKey(value){let h=2166136261;for(const c of value){h^=c.codePointAt(0);h=Math.imul(h,16777619);}return (h>>>0).toString(36);}
 function cleanClone(source){const clone=source.cloneNode(true);const elements=[...(clone.nodeType===1?[clone]:[]),...clone.querySelectorAll('*')];for(const el of elements){el.removeAttribute('id');el.removeAttribute('tabindex');if(el.hasAttribute('data-ask-math-control')){el.removeAttribute('role');el.removeAttribute('aria-label');el.removeAttribute('data-ask-math-control');}if(el.matches('svg.formula')){el.setAttribute('role','img');el.setAttribute('aria-label',el.dataset.latex||el.getAttribute('aria-label')||'数学公式');}if(el.matches('button,.math-scroll-hint'))el.remove();}return clone;}
 function packet(){
  if(!current)return '';
  return course+' · '+chapter+' · '+current.label+'\n课程：'+courseId+'；原课件：'+sourceId+'\n位置：'+current.heading+'\n返回原页：'+current.link+'\n\n'+(current.excerpt?'这里的内容：\n'+current.excerpt+'\n\n':'')+'我的问题：'+(input.value.trim()||'请从这里卡住的一步讲清楚，不必重讲整页。');
 }
 function refresh(){preview.value=packet();}
 function selected(article){
  const selection=window.getSelection();if(!selection||selection.isCollapsed||!article.contains(selection.anchorNode)||!article.contains(selection.focusNode))return null;
  const range=selection.getRangeAt(0).cloneRange(),node=range.commonAncestorContainer,element=node.nodeType===1?node:node.parentElement;
  return {fragment:range.cloneContents(),block:element?.closest('.explanation,.deep-section,.note,.method-note'),text:selection.toString().trim()};
 }
 function open(article,block,trigger,formula,choice=null){
  lastFocus=trigger;const page=article.dataset.page,label=page?'原PPT P'+page:'本次作业 '+article.id.replace('q','第')+'题';
  choice=choice||selected(article);if(choice?.block)block=choice.block;
  const headingNode=block?.querySelector('h2,h3,summary')||article.querySelector('h1,h2');
  const heading=(headingNode?.textContent||label).trim(),headingSource=serial(headingNode).trim()||heading;
  const chosen=choice?.text||'';
  const picked=(formula?.closest('.key-equation,p,li,td,th')||formula)||block?.querySelector('p')||article.querySelector('.teaching .explanation p,.teaching .deep-content p')||article.querySelector('.page-heading h1,h2');
  const url=new URL(route,location.origin);if(page)url.searchParams.set('p',page);url.searchParams.set('focus',(formula||block||article).id);if(window.CoursePreview)url.searchParams.set('preview','1');if(!page)url.hash=article.id;
  const sourceExcerpt=chosen?serial(choice.fragment).trim():serial(picked).trim();
  const excerpt=sourceExcerpt.length<=3500?sourceExcerpt:'（所选内容较长，本次仅附定位。请缩小选区后重新提问，以保留完整公式。）';
  current={label,heading:headingSource,link:url.toString(),excerpt};context.replaceChildren();
  if(chosen&&sourceExcerpt.length<=3500)context.append(cleanClone(choice.fragment));else if(chosen)context.textContent=excerpt;else if(picked)context.append(cleanClone(picked));
  dialog.querySelector('.ask-dot-location').textContent=course+' · '+chapter+' · '+label+' · '+heading;
  input.value='请从这里卡住的一步讲清楚，不必重讲整页。';status.textContent='整理好后复制；此处不会发送消息。';dialog.querySelector('details').open=false;refresh();dialog.showModal();input.focus();
 }
 input.addEventListener('input',refresh);
 dialog.querySelector('.ask-dot-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>lastFocus?.focus({preventScroll:true}));
 dialog.querySelectorAll('.ask-dot-intents button').forEach(b=>b.addEventListener('click',()=>{input.value=b.textContent+'？请结合这里的内容解释。';refresh();input.focus();}));
 dialog.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',async()=>{
  const buttons=[...dialog.querySelectorAll('[data-action]')];buttons.forEach(x=>x.disabled=true);
  const result=await core.act({text:preview.value,clipboard:navigator.clipboard});
  status.textContent=result.copied?'已复制，请自行粘贴到要提问的对话。':'未能自动复制，请在下面选中文本手动复制。';
  if(!result.copied){dialog.querySelector('details').open=true;preview.focus();preview.select();}buttons.forEach(x=>x.disabled=false);
 }));
 articles.forEach(article=>{
  const page=article.dataset.page,prefix=page?'p'+page:article.id;if(!article.id)article.id=prefix;
  const host=article.querySelector('.teaching')||article;
  host.addEventListener('pointerdown',e=>{
   const target=e.target instanceof Element?e.target:null;if(!target||target.closest('button,a,input,textarea,select'))return;
   const block=target.closest('.explanation,.deep-section,.note,.method-note'),formula=target.closest('[data-ask-math-control]')?.querySelector('svg.formula');
   if(block||formula)recent.set(article,{block,formula});
  });
  [...host.querySelectorAll(':scope > .explanation,:scope > .deep-section,:scope > .note,:scope > .method-note')].forEach((block,i)=>{
   if(!block.id)block.id=prefix+'-s-'+stableKey(serial(block.querySelector('h2,h3,summary')))+'-'+String(i+1); 
  });
  const formulaCounts=new Map();host.querySelectorAll('svg.formula').forEach((svg,i)=>{
   svg.dataset.latex=svg.getAttribute('aria-label')||'';const key=stableKey(svg.dataset.latex),ordinal=(formulaCounts.get(key)||0)+1;formulaCounts.set(key,ordinal);svg.dataset.askFormula=prefix+'-f-'+key+'-'+ordinal;svg.id=svg.dataset.askFormula;
   // Reuse the existing baseline/scroll wrapper; do not change SVG semantics
   // or insert layout-affecting buttons around the equation.
   const control=svg.parentElement;control.tabIndex=0;control.setAttribute('role','button');control.setAttribute('aria-label','询问公式：'+svg.dataset.latex);control.dataset.askMathControl='true';
   const activate=()=>open(article,svg.closest('.explanation,.deep-section,.note,.method-note')||host,control,svg);
   control.addEventListener('click',activate);control.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});
  });
 });
 const launch=document.createElement('button');launch.className='ask-dot-button ask-dot-launch';launch.type='button';launch.textContent='复制提问';launch.title='可先选择一段文字，或点击公式，再整理问题并复制';
 const toolbar=document.querySelector('.top .course-links')||document.querySelector('.top');if(toolbar)toolbar.append(launch);
 const visible=()=>articles.find(a=>!a.hidden)||articles[0];
 launch.addEventListener('pointerdown',()=>{pendingSelection=selected(visible());});
 launch.addEventListener('click',()=>{const article=visible(),choice=selected(article)||pendingSelection,previous=recent.get(article);pendingSelection=null;open(article,choice?.block||previous?.block||null,launch,choice?null:previous?.formula,choice);});
 if(requestedFocus){const target=document.getElementById(requestedFocus);if(target){for(let p=target;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;requestAnimationFrame(()=>target.scrollIntoView({block:'start'}));}}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);else setup();
})();
