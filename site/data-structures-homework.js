(() => {
 'use strict';
 const printButton=document.querySelector('[data-print]');
 if(printButton) printButton.addEventListener('click',()=>window.print());
 document.querySelectorAll('.table-scroll,.diagram-scroll,.svg-scroll').forEach(el=>{el.tabIndex=0;el.setAttribute('aria-label','可横向滚动的表格或图示');});
})();
