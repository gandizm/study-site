(() => {
  'use strict';
  const dialog = document.getElementById('emAskDialog');
  const open = document.getElementById('emAskOpen');
  const select = document.getElementById('emAskQuestion');
  const text = document.getElementById('emAskText');
  const status = document.getElementById('emAskStatus');
  const titles = {q251:'2.5-1：圆形平行板导电介质中的场、能流与损耗',q363:'3.6-3：60°导体劈中的点电荷与镜像法'};
  function template() {
    const q=select.value;
    text.value=`请解释电磁场作业 ${titles[q]}。\n页面：https://gandizm.github.io/study-site/em-energy-wedge-homework.html#${q}\n我卡在：\n我目前的理解：`;
    status.textContent='只复制问题和定位，不会打开聊天，也不会自动发送。';
  }
  open.addEventListener('click',()=>{
    const q=location.hash.slice(1); if(q==='q251'||q==='q363') select.value=q;
    template(); dialog.showModal(); select.focus();
  });
  select.addEventListener('change',template);
  document.getElementById('emAskClose').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>open.focus());
  document.getElementById('emAskCopy').addEventListener('click',async()=>{
    try {await navigator.clipboard.writeText(text.value);status.textContent='已复制。你可以自行粘贴到聊天中。';}
    catch {text.focus();text.select();status.textContent='未能自动复制，内容已选中，请手动复制。';}
  });
  document.getElementById('emExpand').addEventListener('click',()=>document.querySelectorAll('.em-body details').forEach(d=>d.open=true));
  document.getElementById('emCollapse').addEventListener('click',()=>document.querySelectorAll('.em-body details').forEach(d=>d.open=false));
  document.getElementById('emPrint').addEventListener('click',()=>window.print());
  let saved=[];
  addEventListener('beforeprint',()=>{saved=[...document.querySelectorAll('.em-body details')].map(d=>[d,d.open]);saved.forEach(([d])=>d.open=true);});
  addEventListener('afterprint',()=>saved.forEach(([d,isOpen])=>d.open=isOpen));
})();
