'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function el(){return {handlers:{},value:'',textContent:'',open:false,focused:false,selected:false,addEventListener(n,f){this.handlers[n]=f;},focus(){this.focused=true;},select(){this.selected=true;},showModal(){this.open=true;},close(){this.open=false;this.handlers.close?.();}};}
const ids=['emAskDialog','emAskOpen','emAskQuestion','emAskText','emAskStatus','emAskClose','emAskCopy','emExpand','emCollapse','emPrint'];
const es=Object.fromEntries(ids.map(x=>[x,el()]));es.emAskQuestion.value='q372';const details=[{open:false},{open:true}],events={};let copied='',prints=0,fail=false;
const ctx={document:{getElementById:i=>es[i],querySelectorAll:()=>details},location:{hash:'#q534-answer'},navigator:{clipboard:{writeText:async s=>{if(fail)throw Error('denied');copied=s;}}},window:{print(){prints++;}},addEventListener:(n,f)=>events[n]=f};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../site/em-week1011.js'),'utf8'),ctx);
(async()=>{
 es.emAskOpen.handlers.click();assert(es.emAskDialog.open);assert.equal(es.emAskQuestion.value,'q534');assert(es.emAskText.value.includes('有效值'));assert(es.emAskText.value.includes('功率流'));assert(es.emAskText.value.includes('https://gandizm.github.io/study-site/em-week1011-homework.html#q534'));
 es.emAskText.value+='我不懂有效值因子';await es.emAskCopy.handlers.click();assert(copied.endsWith('我不懂有效值因子'));assert(es.emAskStatus.textContent.includes('已复制'));
 fail=true;await es.emAskCopy.handlers.click();assert(es.emAskText.selected);assert(es.emAskStatus.textContent.includes('手动复制'));
 es.emAskClose.handlers.click();assert(!es.emAskDialog.open&&es.emAskOpen.focused);
 es.emAskQuestion.value='q372';es.emAskQuestion.handlers.change();assert(es.emAskText.value.includes('#q372'));assert(!es.emAskText.value.includes('#q534-answer'));
 es.emExpand.handlers.click();assert(details.every(x=>x.open));es.emCollapse.handlers.click();assert(details.every(x=>!x.open));
 details[1].open=true;events.beforeprint();assert(details.every(x=>x.open));events.afterprint();assert.deepEqual(details.map(x=>x.open),[false,true]);es.emPrint.handlers.click();assert.equal(prints,1);
 console.log('PASS: six-question copy context, edited text, failure fallback, close/refocus, expand/collapse and restored print states.');
})().catch(e=>{console.error(e);process.exitCode=1;});
