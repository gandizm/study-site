/* Recovered deterministic harness, rerun against the NEW recovery core.
 * This is not a browser layout test and does not inherit prior pass evidence. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
class FakeEvent {constructor(type,options={}) {this.type=type;Object.assign(this,options);} preventDefault(){this.defaultPrevented=true;}}
class Target {constructor(){this.listeners={};} addEventListener(type,fn){(this.listeners[type]||=[]).push(fn);} dispatchEvent(event){event.target ||= this;for(const fn of this.listeners[event.type]||[])fn(event);return true;}}
let document;
function simpleMatch(el,selector){
 selector=selector.trim();
 if(selector.includes(':not([hidden])')){if(el.hidden)return false;selector=selector.replace(':not([hidden])','');}
 const attrs=[...selector.matchAll(/\[([^=\]]+)(?:="([^"]*)")?\]/g)];
 for(const [,name,value]of attrs){const found=name==='hidden'?(el.hidden?'':null):el.getAttribute(name);if(found===null||(value!==undefined&&found!==value))return false;}
 selector=selector.replace(/\[[^\]]+\]/g,'');
 const id=selector.match(/#([\w-]+)/);if(id&&el.id!==id[1])return false;
 for(const [,name]of selector.matchAll(/\.([\w-]+)/g))if(!el.classList.contains(name))return false;
 const tag=selector.match(/^[\w-]+/);return !tag||el.tagName===tag[0].toLowerCase();
}
function matches(el,selector){return selector.split(',').some(part=>{const bits=part.trim().split(/\s+/);if(!simpleMatch(el,bits.pop()))return false;let parent=el.parent;while(bits.length){const bit=bits.pop();while(parent&&!simpleMatch(parent,bit))parent=parent.parent;if(!parent)return false;parent=parent.parent;}return true;});}
class El extends Target {
 constructor(tag){super();this.tagName=tag;this.style={};this.children=[];this.attrs={};this.dataset={};this.hidden=false;this.scrollTop=0;this.scrollLeft=0;this.className='';this._text='';this.value='';this.disabled=false;this.id='';this.classList={contains:n=>this.className.split(/\s+/).includes(n),add:(...ns)=>{this.className=[...new Set([...this.className.split(/\s+/).filter(Boolean),...ns])].join(' ');},remove:n=>{this.className=this.className.split(/\s+/).filter(x=>x!==n).join(' ');},toggle:(n,v)=>{if(v===undefined)v=!this.classList.contains(n);v?this.classList.add(n):this.classList.remove(n);return v;}};}
 set textContent(x){this._text=String(x);this.children=[];}get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
 setAttribute(k,v){this.attrs[k]=String(v);if(k==='id')this.id=String(v);if(k==='class')this.className=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);}
 getAttribute(k){if(k==='id')return this.id||null;if(k==='class')return this.className;if(k.startsWith('data-'))return this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]??null;return this.attrs[k]??null;}
 removeAttribute(k){delete this.attrs[k];}
 append(...els){for(const el of els){if(el.parent)el.parent.children.splice(el.parent.children.indexOf(el),1);el.parent=this;this.children.push(el);}}
 prepend(...els){for(const el of [...els].reverse()){if(el.parent)el.parent.children.splice(el.parent.children.indexOf(el),1);el.parent=this;this.children.unshift(el);}}
 before(el){const p=this.parent;if(el.parent)el.parent.children.splice(el.parent.children.indexOf(el),1);p.children.splice(p.children.indexOf(this),0,el);el.parent=p;}
 querySelectorAll(selector){const result=[];function walk(el){for(const child of el.children){if(matches(child,selector))result.push(child);walk(child);}}walk(this);return result;}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
 closest(selector){let el=this;while(el){if(matches(el,selector))return el;el=el.parent;}return null;}
 replaceChildren(...els){this.children.forEach(c=>{c.parent=null;});this.children=[];this._text='';this.append(...els);}
 contains(target){return target===this||this.children.some(c=>c.contains(target));}
 focus(){document.activeElement=this;}
 getBoundingClientRect(){const height=this.mockHeight??100;return{top:this.mockTop||0,bottom:(this.mockTop||0)+height,left:0,right:200,width:200,height};}
 click(){if(!this.disabled)this.dispatchEvent(new FakeEvent('click'));}
}
(async()=>{
 document=new El('document');document.readyState='complete';document.baseURI='https://example.org/study-site/chapter.html';document.createElement=tag=>new El(tag);document.body=new El('body');document.append(document.body);
 const select=new El('select');select.id='pageSelect';select.value='1';document.body.append(select);
 const main=new El('main');document.body.append(main);
 const pages=[1,2,3].map(n=>{const article=new El('article');article.className='slide-page';article.dataset.page=String(n);article.hidden=n!==1;const teaching=new El('section');teaching.className='teaching';const anchor=new El('section');anchor.id='detail-'+n;anchor.mockTop=400;teaching.append(anchor);const viewport=new El('div');viewport.className='slide-viewport';const toolbar=new El('div');toolbar.className='slide-toolbar';const output=new El('output');output.textContent='100%';const zoomIn=new El('button');zoomIn.setAttribute('data-zoom','in');zoomIn.addEventListener('click',()=>{output.textContent=(parseInt(output.textContent,10)+25)+'%';});toolbar.append(output,zoomIn);article.append(toolbar,viewport,teaching);main.append(article);return article;});
 const script=new El('script');script.setAttribute('data-knowledge-map','/study-site/knowledge-map.json');document.currentScript=script;
 const root=new Target();root.document=document;root.location=new URL(document.baseURI+'#p01');root.sessionStorage={value:'closed',getItem(){return this.value;},setItem(k,v){this.value=v;}};
 root.performance={getEntriesByType(){return[{name:document.baseURI+'?map=1#p01'}];}};
 const history=[];const urls=[root.location.href];let historyIndex=0;root.history={state:null,pushState(state,_,url){this.state=state;history.push(url);urls.splice(historyIndex+1);urls.push(url);historyIndex++;root.location=new URL(url);},replaceState(state,_,url){this.state=state;urls[historyIndex]=url;root.location=new URL(url);},back(){if(historyIndex>0){root.location=new URL(urls[--historyIndex]);root.dispatchEvent(new FakeEvent('popstate'));root.dispatchEvent(new FakeEvent('hashchange'));}},forward(){if(historyIndex<urls.length-1){root.location=new URL(urls[++historyIndex]);root.dispatchEvent(new FakeEvent('popstate'));root.dispatchEvent(new FakeEvent('hashchange'));}}};
 const frames=[];root.requestAnimationFrame=fn=>{frames.push(fn);};const flush=()=>{while(frames.length)frames.shift()();};
 const graph={version:1,id:'test',title:'测试',nodes:[{id:'first',label:'基础',pages:[1],section:'起点'},{id:'second',label:'应用',pages:[2],prerequisites:['first'],anchors:{'2':'detail-2'}},{id:'third',label:'检查',pages:[3],prerequisites:['second']},{id:'fourth',label:'出向四',pages:[3],prerequisites:['second']},{id:'fifth',label:'出向五',pages:[3],prerequisites:['second']},{id:'sixth',label:'出向六',pages:[3],prerequisites:['second']}],edges:[{from:'first',to:'third',label:'检验'}]};
 root.fetch=async()=>({ok:true,json:async()=>graph});
 select.addEventListener('change',()=>{const p=Number(select.value);root.dispatchEvent(new FakeEvent('course:pagechange',{detail:{page:p}}));pages.forEach(a=>a.hidden=Number(a.dataset.page)!==p);root.requestAnimationFrame(()=>{pages[p-1].querySelector('.teaching').scrollTop=0;pages[p-1].querySelector('.slide-toolbar output').textContent='100%';pages[p-1].querySelector('.slide-viewport').scrollTop=0;});});
 document.createElementNS=(_,tag)=>new El(tag);const compactQuery={matches:false,addEventListener(){}};root.matchMedia=()=>compactQuery;
 root.addEventListener('hashchange',()=>{select.value=String(Number(root.location.hash.replace('#p','')));select.dispatchEvent(new FakeEvent('change'));});
 const sandbox={window:root,document,URL,URLSearchParams,Event:FakeEvent,CustomEvent:FakeEvent,console};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../site/knowledge-map.js'),'utf8'),sandbox);
 await new Promise(resolve=>setImmediate(resolve));flush();
 const $=s=>document.querySelector(s);
 assert.equal($('#knowledge-map').dataset.ready,'true');assert.equal($('#knowledge-map').dataset.fallback,undefined);
 assert.equal($('.km-toggle').getAttribute('aria-expanded'),'true','original ?map=1 opens despite remembered collapse');
 assert.equal(document.querySelectorAll('.km-node').length,6);assert.ok(document.querySelectorAll('.km-relation').length>=3);
 assert.equal(main.parent.className,'km-workspace');assert.equal($('#knowledge-map').closest('.slide-page'),null);
 const originalMap=$('#knowledge-map');
 pages[0].querySelector('.teaching').scrollTop=177;pages[0].querySelector('.slide-toolbar output').textContent='175%';pages[0].querySelector('.slide-viewport').scrollTop=250;
 $('.km-page[data-page="2"]').click();flush();
 assert.equal(select.value,'2');assert.equal($('#knowledge-map'),originalMap);assert.equal($('.km-toggle').getAttribute('aria-expanded'),'true');
 assert.equal($('.km-page[data-page="2"]').getAttribute('aria-current'),'page');assert.equal(root.CourseKnowledgeMap.current().backCount,1);assert.equal(history.length,1);
 assert.equal(pages[1].querySelector('.teaching').scrollTop,388,'deep anchor applies after reader frame reset');
 $('.km-back').click();flush();assert.equal(select.value,'1');assert.equal(pages[0].querySelector('.teaching').scrollTop,177);assert.equal(root.CourseKnowledgeMap.current().backCount,0);
 assert.equal(pages[0].querySelector('.slide-toolbar output').textContent,'175%');assert.equal(pages[0].querySelector('.slide-viewport').scrollTop,250);
 select.value='3';select.dispatchEvent(new FakeEvent('change'));flush();assert.equal(root.CourseKnowledgeMap.current().page,3);
 $('.km-page[data-page="3"]').click();flush();assert.equal(root.CourseKnowledgeMap.current().backCount,0,'ordinary navigation resets destination');
 $('.km-toggle').click();assert.equal($('.km-content').hidden,true);$('.km-page[data-page="1"]').click();flush();assert.equal($('.km-toggle').getAttribute('aria-expanded'),'false');
 $('.km-toggle').click();$('.km-search').value='P2';$('.km-search').dispatchEvent(new FakeEvent('input'));assert.equal(document.querySelectorAll('.km-node:not([hidden])').length,1);
 $('.km-search').value='no match';$('.km-search').dispatchEvent(new FakeEvent('input'));assert.equal($('.km-empty').hidden,false);
 $('.km-locate').click();assert.equal($('.km-search').value,'');assert.equal(document.activeElement.classList.contains('km-node-title'),true);
 $('.km-read').click();assert.equal(document.activeElement.className,'teaching');assert.equal(document.activeElement.getAttribute('tabindex'),'-1');
 $('.km-page[data-page="2"]').click();$('.km-page[data-page="3"]').click();flush();assert.equal(select.value,'3');assert.equal(root.CourseKnowledgeMap.current().page,3);
 assert.equal(root.CourseKnowledgeMap.navigate(999,'first'),false);assert.equal(select.value,'3');
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../site/knowledge-neighborhood.js'),'utf8'),sandbox);flush();
 assert.equal($('.kmn-view').hidden,false);assert.equal($('#kmn-list-view').hidden,true);
 assert.ok($('.kmn-controls').contains($('.kmn-switcher')));assert.ok($('.kmn-controls').contains($('.km-actions')));assert.ok($('.kmn-controls').contains($('.km-search')));
 assert.ok($('.kmn-canvas svg').querySelectorAll('path').length>1);assert.equal(document.querySelectorAll('.kmn-current-node').length,1);assert.equal(root.CourseKnowledgeNeighborhood.model().current.id,'third');
 $('.kmn-current-node').mockTop=240;root.CourseKnowledgeNeighborhood.setMode('graph');flush();assert.equal($('.kmn-view').scrollTop,240);$('.kmn-current-node').mockTop=0;
 const incoming=$('.kmn-node.kmn-in');assert.ok(incoming);$('.kmn-view').scrollTop=130;incoming.click();flush();assert.equal($('.kmn-view').scrollTop,0);
 assert.equal(select.value,'2');assert.equal(root.CourseKnowledgeNeighborhood.model().current.id,'second');assert.equal($('#knowledge-map'),originalMap);
 $('.kmn-tab[aria-controls="kmn-list-view"]').click();flush();assert.equal($('#kmn-list-view').hidden,false);
 $('.km-search').value='P1';$('.km-search').dispatchEvent(new FakeEvent('input'));flush();assert.equal($('.kmn-view').hidden,true);
 $('.kmn-tab[aria-controls="kmn-view"]').click();flush();$('.kmn-all-relations').click();flush();assert.equal($('.km-search').value,'');
 root.CourseKnowledgeMap.navigate(2,'second');flush();root.CourseKnowledgeNeighborhood.refresh();flush();
 const completeModel=root.CourseKnowledgeNeighborhood.model();assert.equal(completeModel.incomingTotal,1);assert.equal(completeModel.outgoingTotal,4);assert.equal(completeModel.outgoing.length,3);
 root.CourseKnowledgeNeighborhood.setMode('graph');flush();$('.kmn-all-relations').click();flush();const secondCard=$('.km-node[data-node-id="second"]');
 assert.equal(secondCard.querySelectorAll('.kmn-outgoing-relation').length,4);assert.equal(secondCard.querySelectorAll('.km-relation').length,5);
 assert.equal($('.km-node[data-node-id="first"]').querySelectorAll('.kmn-outgoing-relation').length,0);assert.equal(root.CourseKnowledgeMap.data.edges.length,6);
 assert.deepEqual(secondCard.querySelectorAll('.kmn-outgoing-relation').map(row=>row.dataset.to),['third','fourth','fifth','sixth']);
 secondCard.querySelectorAll('.kmn-outgoing-relation')[3].querySelector('.km-related').click();flush();assert.equal(select.value,'3');assert.equal(root.CourseKnowledgeMap.current().nodeId,'sixth');
 assert.equal($('#kmn-list-view').hidden,false);assert.equal($('#knowledge-map'),originalMap);
 root.dispatchEvent(new FakeEvent('knowledge-map:ready'));flush();assert.equal(secondCard.querySelectorAll('.kmn-outgoing-relation').length,4);
 root.CourseKnowledgeNeighborhood.setMode('graph');flush();$('.km-toggle').click();$('.kmn-view').mockHeight=0;
 root.CourseKnowledgeMap.navigate(2,'second');flush();$('.kmn-current-node').mockTop=240;$('.kmn-view').scrollTop=0;
 root.CourseKnowledgeNeighborhood.setMode('graph');flush();assert.equal($('.kmn-view').scrollTop,0);
 $('.kmn-view').mockHeight=100;$('.km-toggle').click();flush();assert.equal($('.kmn-view').scrollTop,240);
 $('.kmn-current-node').mockTop=0;$('.kmn-view').scrollTop=77;$('#knowledge-map').dispatchEvent(new FakeEvent('click'));flush();assert.equal($('.kmn-view').scrollTop,77);
 compactQuery.matches=true;root.CourseKnowledgeNeighborhood.setMode('graph');flush();assert.ok(root.CourseKnowledgeNeighborhood.model().incoming.length<=1);assert.ok(root.CourseKnowledgeNeighborhood.model().outgoing.length<=1);
 root.CourseKnowledgeMap.navigate(1,'first');flush();root.CourseKnowledgeMap.navigate(2,'second');flush();root.history.back();flush();assert.equal(select.value,'1');root.history.forward();flush();assert.equal(select.value,'2');assert.equal(root.CourseKnowledgeNeighborhood.model().current.id,'second');
 root.location.hash='p03';root.dispatchEvent(new FakeEvent('hashchange'));flush();assert.equal(select.value,'3');assert.equal(root.CourseKnowledgeNeighborhood.model().current.id,'third');assert.equal($('#knowledge-map'),originalMap);
 console.log('NEW recovery core + byte-exact neighborhood DOM simulation PASS: persistence, real-select navigation, current state, deep anchor, history, return/zoom/scroll, explicit collapse, search/focus, rapid navigation, full outgoing edges, compact cap and hidden/short-view reveal. This is NOT a browser geometry pass.');
})().catch(error=>{console.error(error);process.exitCode=1;});
