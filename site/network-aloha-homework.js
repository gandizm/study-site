/* Copy only the chosen public answer, never user input or progress. */
(() => {
  'use strict';
  const questions = Array.from(document.querySelectorAll('.ah-question'));
  const state = document.querySelector('#copy-status');
  const lines = a => [...a.querySelectorAll('.ah-step')].map(p => p.getAttribute('data-copy') || p.textContent).join('\n');
  function legacy(value) {
    const field = document.createElement('textarea');
    field.value=value;field.readOnly=true;field.setAttribute('aria-label','复制答案');
    field.style.cssText='position:fixed;left:0;top:0;opacity:0';
    document.body.append(field);
    try { field.focus({preventScroll:true});field.select();field.setSelectionRange(0,field.value.length);return document.execCommand('copy'); }
    catch { return false; } finally { field.remove(); }
  }
  for (const btn of document.querySelectorAll('button[data-copy-id]')) {
    btn.hidden=false;
    btn.addEventListener('click', async () => {
      const id=btn.dataset.copyId, q=document.getElementById(id);
      const value=id==='all'?questions.map((a,i)=>'第 '+(i+1)+' 题\n'+lines(a)).join('\n\n'):lines(q);
      let ok=false;
      try { if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(value);ok=true;} } catch {}
      if(!ok)ok=legacy(value);
      const message=ok?(id==='all'?'已复制七题答案。':'已复制第 '+id.slice(1)+' 题答案。'):'没有复制成功。请长按选择答案，或打开纯文本版。';
      state.textContent=message;
      const row=btn.closest('.ah-question');if(row)row.querySelector('.ah-status').textContent=message;
      btn.focus({preventScroll:true});
    });
  }
  const print=document.querySelector('#print-answers');print.hidden=false;print.addEventListener('click',()=>window.print());
})();
