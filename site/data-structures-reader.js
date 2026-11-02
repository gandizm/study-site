(() => {
 'use strict';
 const pages = Array.from(document.querySelectorAll('.source-page'));
 const select = document.getElementById('source-select');
 const zoom = document.getElementById('source-zoom');
 const prev = document.getElementById('source-prev');
 const next = document.getElementById('source-next');
 const status = document.getElementById('source-status');
 if (!pages.length || !select || !zoom || !prev || !next || !status) return;
 document.querySelectorAll('.source-viewport').forEach(el=>{el.tabIndex=0;el.setAttribute('aria-label','可横向和纵向滚动的课件原页');});
 let current = 0;
 function render() {
  const id = location.hash.slice(1);
  const index = pages.findIndex(p => p.id === id);
  current = index < 0 ? 0 : index;
  pages.forEach((p,i) => {p.hidden=i!==current;});
  select.value=pages[current].id;
  prev.disabled=current===0;next.disabled=current===pages.length-1;
  const img=pages[current].querySelector('img');
  img.style.width=zoom.value+'%';
  status.textContent='PDF 原页 '+(current+1)+' / '+pages.length+'。放大后可在原页区域横向滚动；页码不是单张幻灯片编号。';
 }
 function go(i) {if(i>=0&&i<pages.length) location.hash=pages[i].id;}
 select.addEventListener('change',()=>go(pages.findIndex(p=>p.id===select.value)));
 prev.addEventListener('click',()=>go(current-1));
 next.addEventListener('click',()=>go(current+1));
 zoom.addEventListener('change',render);
 addEventListener('hashchange',render);
 render();
})();
