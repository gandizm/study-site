/* Browser-free behavioral checks for the actual lesson script. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../site/data-structures-homework4.js'),'utf8');
class Element {
  constructor(dataset={}){this.dataset=dataset;this.listeners={};this.classes=new Set();this.children=[];this.attributes={};this.disabled=false;this.hidden=false;this.textContent='';this.value='pre';this.classList={add:x=>this.classes.add(x),toggle:(x,b)=>b?this.classes.add(x):this.classes.delete(x)};}
  addEventListener(type,fn){this.listeners[type]=fn;}
  fire(type){return this.listeners[type]?.();}
  querySelectorAll(){return this.buttons||[];}
  replaceChildren(){this.children=[];}
  appendChild(el){this.children.push(el);}
  setAttribute(k,v){this.attributes[k]=v;}
}
function environment(withPlayer=true,clipboard=true){
  const player=new Element(),select=new Element(),status=new Element(),output=new Element(),toast=new Element();
  const buttons=['prev','next','reset'].map(x=>new Element({traversal:x}));player.buttons=buttons;
  const nodes=[...'ABCDEFGH'].map(node=>new Element({node}));
  const print=new Element(),copy=new Element({copy:'copy-q1'}),answer=new Element();answer.textContent='501 / 500 / 0';
  const byId={'traversal-player':withPlayer?player:null,'traversal-order':select,'traversal-status':status,'traversal-sequence':output,'copy-status':toast,'copy-q1':answer};
  const state={printed:0,copied:null,selected:null};
  const document={documentElement:new Element(),getElementById:id=>byId[id],createElement:()=>new Element(),createRange:()=>({selectNodeContents:x=>state.selected=x}),querySelectorAll:q=>q==='[data-print]'?[print]:q==='[data-copy]'?[copy]:nodes};
  const navigator={};if(clipboard)navigator.clipboard={writeText:async text=>{state.copied=text;}};
  vm.runInNewContext(code,{document,navigator,window:{print:()=>state.printed++,getSelection:()=>({removeAllRanges(){},addRange(){}})},setTimeout:()=>1,clearTimeout(){}});
  return {buttons,nodes,select,status,output,toast,print,copy,answer,state,document};
}
(async()=>{
  const e=environment();const [prev,next,reset]=e.buttons;
  assert(prev.disabled&&reset.disabled&&!next.disabled);
  for(const [value,expected] of Object.entries({pre:'ABCDEFGH',in:'BDCEAFHG',post:'DECBHGFA'})){
    e.select.value=value;e.select.fire('change');assert.equal(e.output.children.length,0);assert(prev.disabled&&reset.disabled&&!next.disabled);
    for(let i=0;i<8;i++){
      next.fire('click');assert.equal(e.output.children.map(x=>x.textContent).join(''),expected.slice(0,i+1));
      assert.equal(e.nodes.filter(x=>x.classes.has('is-current')).length,1);
      assert.equal(e.nodes.find(x=>x.classes.has('is-current')).dataset.node,expected[i]);
      assert.equal(e.nodes.filter(x=>x.classes.has('is-visited')).length,i+1);
    }
    assert(next.disabled);next.fire('click');assert.equal(e.output.children.length,8);
    prev.fire('click');assert.equal(e.output.children.length,7);assert(!next.disabled);
    reset.fire('click');assert.equal(e.output.children.length,0);assert(prev.disabled&&reset.disabled);
    prev.fire('click');assert.equal(e.output.children.length,0);
  }
  e.print.fire('click');assert.equal(e.state.printed,1);
  await e.copy.fire('click');assert.equal(e.state.copied,e.answer.textContent);assert(!e.toast.hidden);
  const answerOnly=environment(false);answerOnly.print.fire('click');assert.equal(answerOnly.state.printed,1);await answerOnly.copy.fire('click');assert.equal(answerOnly.state.copied,answerOnly.answer.textContent);
  const fallback=environment(true,false);await fallback.copy.fire('click');assert.equal(fallback.state.selected,fallback.answer);assert(fallback.toast.textContent.includes('未能自动复制'));
  console.log('PASS: all 3 traversal modes, start/end bounds, repeated clicks, reset/change, highlights, print, copy success/fallback and answer-only page.');
})();
