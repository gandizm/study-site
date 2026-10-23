/* Whole-chapter graph candidate. Reuses CourseKnowledgeMap; never writes progress. */
(function(root){
'use strict';
function pageRanges(pages){
 const sorted=[...new Set(pages)].sort((a,b)=>a-b),parts=[];let start=sorted[0],end=start;
 for(const n of sorted.slice(1)){if(n===end+1){end=n;continue;}parts.push('P'+start+(end>start?'–'+end:''));start=end=n;}
 if(start!=null)parts.push('P'+start+(end>start?'–'+end:''));return parts.join('、');
}
function chapterModel(data,options={}){
 const index=new Map(data.nodes.map(n=>[n.id,n]));
 const allEdges=data.edges.map((e,i)=>({...e,key:'edge-'+i}));
 const rootId=index.has(options.rootId)?options.rootId:data.nodes[0].id;
 const depth=options.depth==null?Infinity:Math.max(0,Number(options.depth));
 const distances=new Map([[rootId,0]]),queue=[rootId];
 const adjacent=new Map(data.nodes.map(n=>[n.id,new Set()]));
 allEdges.forEach(e=>{adjacent.get(e.from)?.add(e.to);adjacent.get(e.to)?.add(e.from);});
 for(let i=0;i<queue.length;i++){const id=queue[i],d=distances.get(id);if(d>=depth)continue;for(const next of adjacent.get(id)||[])if(!distances.has(next)){distances.set(next,d+1);queue.push(next);}}
 const chosen=options.focus?new Set(distances.keys()):new Set(index.keys());
 const nodes=data.nodes.filter(n=>chosen.has(n.id));const edges=allEdges.filter(e=>chosen.has(e.from)&&chosen.has(e.to));
 const groups=[];const sections=new Map();
 nodes.forEach(n=>{const label=options.focus?'关联距离 '+distances.get(n.id):(n.section||'知识主线');if(!sections.has(label)){const group={id:'topic-'+groups.length,label,nodes:[],order:groups.length+1};sections.set(label,group);groups.push(group);}sections.get(label).nodes.push(n);});
 const collapsed=new Set(options.collapsed||[]),positions=new Map(),nodeGroup=new Map();
 if(options.focus){groups.sort((a,b)=>Number(a.label.split(' ').at(-1))-Number(b.label.split(' ').at(-1)));groups.forEach((g,i)=>g.order=i+1);}
 const columns=options.focus?groups.length:Math.min(3,Math.max(1,groups.length)),groupWidth=options.focus?222:590,gap=options.focus?100:40,heights=Array(columns).fill(28);
 for(const group of groups){
  group.collapsed=collapsed.has(group.label);group.nodes.sort((a,b)=>a.pages[0]-b.pages[0]||a.label.localeCompare(b.label));
  let column=options.focus?groups.indexOf(group):heights.indexOf(Math.min(...heights));group.x=28+column*(groupWidth+gap);group.y=heights[column];group.width=groupWidth;
  group.height=group.collapsed?92:66+Math.ceil(group.nodes.length/(options.focus?1:3))*(options.focus?116:90);
  heights[column]+=group.height+40;
  group.nodes.forEach((node,i)=>{nodeGroup.set(node.id,group.id);if(!group.collapsed)positions.set(node.id,{x:group.x+18+(options.focus?0:i%3)*188,y:group.y+62+(options.focus?i:Math.floor(i/3))*(options.focus?116:90),width:176,height:72,group:group.id});});
 }
 const byGroup=new Map(groups.map(g=>[g.id,g]));const aggregate=new Map();
 for(const edge of edges){const from=nodeGroup.get(edge.from),to=nodeGroup.get(edge.to);if(from===to)continue;const key=from+'>'+to;if(!aggregate.has(key))aggregate.set(key,{key:'group-'+key,from,to,edges:[]});aggregate.get(key).edges.push(edge);}
 return{rootId,depth,nodes,edges,allEdges,groups,positions,nodeGroup,byGroup,groupEdges:[...aggregate.values()],distances,width:columns*(groupWidth+gap)+16,height:Math.max(...heights)+8,totalNodes:data.nodes.length,totalEdges:allEdges.length};
}
if(typeof module!=='undefined'&&module.exports)module.exports={chapterModel,pageRanges};
if(!root.document)return;
const document=root.document;
const NS='http://www.w3.org/2000/svg';
function el(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;return x;}
function svg(tag,attrs={}){const x=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))x.setAttribute(k,String(v));return x;}
function btn(text,label){const x=el('button','',text);x.type='button';if(label)x.setAttribute('aria-label',label);return x;}
function start(){
 const api=root.CourseKnowledgeMap,panel=document.querySelector('#knowledge-map[data-ready="true"]');
 if(!api?.data||!panel||panel.classList.contains('kgv2-enabled'))return;
 if(panel.classList.contains('kmn-enabled'))return; // Integrator must replace, not stack, graph extensions.
 const data=api.data,content=panel.querySelector('.km-content'),list=panel.querySelector('.km-graph');
 const nodeIndex=new Map(data.nodes.map(n=>[n.id,n]));
 const state={mode:'overview',rootId:api.current().nodeId,collapsed:new Set(),collapsedByMode:{},cameras:{},roomy:false};
 let model=null,zoom=1,rendering=false,drag=null,renderSerial=0,searchReturn='overview',selectedEdgeText='';
 panel.classList.add('kgv2-enabled');
 const originalControls=[...content.children].filter(x=>x!==list&&x.className!=='km-empty');originalControls.forEach(x=>x.hidden=true);
 const bar=el('div','kgv2-toolbar');bar.setAttribute('aria-label','整章图谱视图与缩放');
 const mode=el('select','kgv2-mode');mode.setAttribute('aria-label','图谱范围');
 for(const [value,label]of [['overview','整章主题总览'],['focus2','关联距离 · 2层'],['focus3','关联距离 · 3层'],['all','整章全部关系'],['list','概念清单（辅助）']]){const option=el('option','',label);option.value=value;mode.append(option);}
 const minus=btn('−','缩小图谱'),plus=btn('＋','放大图谱'),fit=btn('适合','让当前图的全部节点进入视窗');
 const menu=el('details','kgv2-menu');const menuSummary=el('summary','','更多');menu.append(menuSummary);
 const menuBody=el('div','kgv2-menu-body');menu.append(menuBody);
 const current=btn('定位当前概念'),focus=btn('以当前为展开起点'),actual=btn('100% 阅读大小'),expand=btn('展开全部主题'),collapse=btn('折叠全部主题'),roomy=btn('放大图谱区域');
 const topic=el('select','kgv2-topics');topic.setAttribute('aria-label','定位教学主题');const first=el('option','','定位一个主题…');first.value='';topic.append(first);
 [...new Set(data.nodes.map(n=>n.section||'知识主线'))].forEach(label=>{const o=el('option','',label);o.value=label;topic.append(o);});
 const listSearch=panel.querySelector('.km-search-label'),read=panel.querySelector('.km-read');
 if(listSearch){listSearch.hidden=false;menuBody.append(listSearch);}if(read){read.hidden=false;menuBody.append(read);read.addEventListener('click',()=>{menu.open=false;});}
 menuBody.append(current,focus,actual,expand,collapse,topic,roomy);
 const help=el('p','kgv2-help','按既有教学主题分区，不等同于原PPT章节。关联距离沿入向和出向关系计算，不表示推导层级。拖动空白或滚动平移，＋/−缩放，点节点跳真实页。普通跳页不改变镜头。');menuBody.append(help);
 bar.append(mode,minus,fit,plus,menu);
 const frame=el('div','kgv2-frame'),viewport=el('div','kgv2-viewport');viewport.tabIndex=0;viewport.setAttribute('role','region');viewport.setAttribute('aria-label','可平移缩放的整章知识图谱，方向键平移，加减键缩放，Home适合全图');
 const space=el('div','kgv2-space'),drawing=svg('svg',{'class':'kgv2-drawing',role:'group','aria-label':'整章概念节点与有向关系'});space.append(drawing);viewport.append(space);frame.append(viewport);
 const mini=svg('svg',{'class':'kgv2-minimap',tabindex:'0',role:'button','aria-label':'图谱总览定位器，点击定位；按Enter适合全图',preserveAspectRatio:'none'});frame.append(mini);
 const edgeTip=el('div','kgv2-edge-tip');edgeTip.hidden=true;edgeTip.tabIndex=0;edgeTip.setAttribute('role','region');edgeTip.setAttribute('aria-label','关系方向与标签，长内容可滚动，Escape关闭');const tipClose=btn('×','关闭关系提示');tipClose.className='kgv2-tip-close';tipClose.hidden=true;frame.append(edgeTip,tipClose);
 const status=el('div','kgv2-status');status.setAttribute('aria-live','polite');
 const detail=el('details','kgv2-detail'),summary=el('summary'),detailBody=el('div','kgv2-detail-body');detail.append(summary,detailBody);
 content.append(bar,frame,status,detail);list.hidden=true;
 function camera(){return{zoom,left:viewport.scrollLeft,top:viewport.scrollTop};}
 function saveCamera(){const box=viewport.getBoundingClientRect();if(model&&!rendering&&state.mode!=='list'&&box.width>0&&box.height>0)state.cameras[state.mode]=camera();}
 function setZoom(next,center){
  const old=zoom;const box=viewport.getBoundingClientRect();const anchor=center||{x:box.width/2,y:box.height/2};
  const worldX=(viewport.scrollLeft+anchor.x)/old,worldY=(viewport.scrollTop+anchor.y)/old;
  zoom=Math.max(Number.EPSILON,Math.min(2.4,Number.isFinite(next)?next:1));drawing.style.transform='scale('+zoom+')';space.style.width=model.width*zoom+'px';space.style.height=model.height*zoom+'px';
  drawing.classList.toggle('kgv2-low-detail',zoom<.55);drawing.style.setProperty?.('--kg-label-scale',Math.max(1,.50/zoom));
  for(const title of drawing.querySelectorAll('.kgv2-topic-title'))title.textContent=zoom<.32?title.dataset.order+'. '+[...title.dataset.label].slice(0,zoom<.18?4:5).join('')+(title.dataset.label.length>(zoom<.18?4:5)?'…':''):title.dataset.full;
  viewport.scrollLeft=worldX*zoom-anchor.x;viewport.scrollTop=worldY*zoom-anchor.y;saveCamera();renderMini();
 }
 function fitAll(){const box=viewport.getBoundingClientRect();if(!model||box.width<=0||box.height<=0)return;setZoom(Math.min((box.width-20)/model.width,(box.height-20)/model.height));viewport.scrollLeft=0;viewport.scrollTop=0;saveCamera();renderMini();}
 function revealWorld(rect,scale){if(!rect)return;const box=viewport.getBoundingClientRect();setZoom(scale||Math.min(1.2,(box.width-26)/rect.width,(box.height-20)/rect.height));viewport.scrollLeft=Math.max(0,(rect.x+rect.width/2)*zoom-box.width/2);viewport.scrollTop=Math.max(0,(rect.y+rect.height/2)*zoom-box.height/2);saveCamera();renderMini();}
 function restoreCamera(saved){setZoom(saved.zoom);viewport.scrollLeft=saved.left;viewport.scrollTop=saved.top;saveCamera();renderMini();}
 function pathBetween(a,b,offset=0){const ax=a.x+a.width/2,ay=a.y+a.height/2,bx=b.x+b.width/2,by=b.y+b.height/2;const dx=bx-ax,dy=by-ay;if(Math.abs(dx)>Math.abs(dy))return`M${ax+(dx>0?a.width/2:-a.width/2)},${ay} C${(ax+bx)/2+offset},${ay+offset} ${(ax+bx)/2+offset},${by+offset} ${bx+(dx>0?-b.width/2:b.width/2)},${by}`;return`M${ax},${ay+(dy>0?a.height/2:-a.height/2)} C${ax+offset},${(ay+by)/2+offset} ${bx+offset},${(ay+by)/2+offset} ${bx},${by+(dy>0?-b.height/2:b.height/2)}`;}
 function activate(element,fn){element.addEventListener('click',fn);element.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();fn(event);}});}
 function drawEdge(from,to,label,edge,grouped){
  if(!from||!to)return;const pair=grouped?[]:model.edges.filter(e=>(e.from===edge.from&&e.to===edge.to)||(e.from===edge.to&&e.to===edge.from)),index=pair.findIndex(e=>e.key===edge.key),offset=pair.length>1?(index-(pair.length-1)/2)*28:0;const p=svg('path',{d:pathBetween(from,to,offset),'class':grouped?'kgv2-edge kgv2-group-edge':'kgv2-edge','marker-end':'url(#kgv2-arrow)',tabindex:'0',role:'button','aria-label':label,'data-edge':edge.key});
  if(!grouped){p.dataset.from=edge.from;p.dataset.to=edge.to;}else{p.dataset.groupFrom=edge.from;p.dataset.groupTo=edge.to;}
  const title=svg('title');title.textContent=label;p.append(title);
  const related=grouped?edge.edges:pair;const tipLabel=label+(related.length>1?'（两端共 '+related.length+' 条关系，点击完整查看）':'');
  const show=()=>{edgeTip.textContent=tipLabel;edgeTip.hidden=false;tipClose.hidden=false;};const hide=()=>{edgeTip.textContent=selectedEdgeText;edgeTip.hidden=!selectedEdgeText;tipClose.hidden=edgeTip.hidden;};
  p.addEventListener('pointerenter',show);p.addEventListener('focus',show);p.addEventListener('pointerleave',hide);p.addEventListener('blur',hide);
  activate(p,()=>{selectedEdgeText=tipLabel;show();for(const x of drawing.querySelectorAll('.kgv2-edge-selected'))x.classList.remove('kgv2-edge-selected');p.classList.add('kgv2-edge-selected');drawing.querySelector('[data-edge-label="'+edge.key+'"]')?.classList.add('kgv2-edge-selected');showRelations(related,'关系详情 · '+related.length+' 条完整标注');});drawing.append(p);


 }
 function clearTip(){selectedEdgeText='';edgeTip.hidden=true;tipClose.hidden=true;for(const x of drawing.querySelectorAll('.kgv2-edge-selected'))x.classList.remove('kgv2-edge-selected');}
 tipClose.addEventListener('click',clearTip);for(const item of [edgeTip,tipClose])item.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();clearTip();viewport.focus({preventScroll:true});}});
 function showRelations(edges,label){detail.open=true;summary.textContent=label;detailBody.replaceChildren();edges.forEach(edge=>relationRow(edge));}
 function relationRow(edge){const from=nodeIndex.get(edge.from),to=nodeIndex.get(edge.to),row=el('div','kgv2-relation');const a=btn(from.label),b=btn(to.label);a.addEventListener('click',()=>go(from));b.addEventListener('click',()=>go(to));row.append(a,el('span','', ' → '+edge.label+' → '),b);detailBody.append(row);}
 function go(node,page){if(api.navigate(page||node.pages[0],node.id))updateCurrent();}
 function updateCurrent(){
  const active=api.current(),node=nodeIndex.get(active.nodeId);if(!node)return;clearTip();
  for(const g of drawing.querySelectorAll('[data-node]')){const selected=g.dataset.node===node.id;g.classList.toggle('kgv2-selected',selected);g.setAttribute('aria-current',selected?'page':'false');}
  for(const group of drawing.querySelectorAll('[data-topic]'))group.classList.toggle('kgv2-topic-current',model?.nodeGroup.get(node.id)===group.dataset.topic);
  for(const edge of drawing.querySelectorAll('[data-edge], [data-edge-label]')){edge.classList.toggle('kgv2-edge-current',edge.dataset.from===node.id||edge.dataset.to===node.id);}
  summary.textContent='P'+active.page+' · '+node.label+' · 讲解与全部关系';detailBody.replaceChildren();
  if(node.source==='supplement')detailBody.append(el('p','kgv2-source','补充讲解（非原PPT内容）'));detailBody.append(el('p','kgv2-node-summary',node.summary));const pages=el('div','kgv2-page-links');node.pages.forEach(p=>{const b=btn('P'+p,node.label+'，原PPT第'+p+'页及讲义');b.classList.toggle('kgv2-page-current',p===active.page);b.addEventListener('click',()=>go(node,p));pages.append(b);});detailBody.append(pages);
  const incoming=data.edges.filter(e=>e.to===node.id),outgoing=data.edges.filter(e=>e.from===node.id);detailBody.append(el('p','kgv2-rel-count',incoming.length+' 条入向 / '+outgoing.length+' 条出向关系（完整）'));[...incoming,...outgoing].forEach(relationRow);renderMini();
 }
 function renderMini(){if(!model)return;mini.setAttribute('viewBox',`0 0 ${model.width} ${model.height}`);mini.replaceChildren();for(const g of model.groups)mini.append(svg('rect',{x:g.x,y:g.y,width:g.width,height:g.height,rx:12,'class':'kgv2-mini-group'}));
  const currentRect=model.positions.get(api.current().nodeId);if(currentRect)mini.append(svg('rect',{x:currentRect.x,y:currentRect.y,width:currentRect.width,height:currentRect.height,'class':'kgv2-mini-current'}));
  const box=viewport.getBoundingClientRect();mini.append(svg('rect',{x:viewport.scrollLeft/zoom,y:viewport.scrollTop/zoom,width:box.width/zoom,height:box.height/zoom,'class':'kgv2-mini-camera'}));}
 function renderDiagram(reset=false){
  saveCamera();rendering=true;const serial=++renderSerial;clearTip();const focused=state.mode==='focus2'||state.mode==='focus3';model=chapterModel(data,{focus:focused,depth:state.mode==='focus3'?3:2,rootId:state.rootId,collapsed:[...state.collapsed]});
  drawing.replaceChildren();drawing.setAttribute('width',model.width);drawing.setAttribute('height',model.height);
  const defs=svg('defs'),marker=svg('marker',{id:'kgv2-arrow',viewBox:'0 0 8 8',refX:7,refY:4,markerWidth:6,markerHeight:6,orient:'auto',markerUnits:'userSpaceOnUse'});marker.append(svg('path',{d:'M0 0 L8 4 L0 8 Z',fill:'context-stroke'}));defs.append(marker);drawing.append(defs);
  if(state.mode==='overview')for(const edge of model.groupEdges)drawEdge(model.byGroup.get(edge.from),model.byGroup.get(edge.to),model.byGroup.get(edge.from).label+' → '+edge.edges.length+' 条跨主题关系 → '+model.byGroup.get(edge.to).label+'，点击查看完整方向与标签',edge,true);
  for(const group of model.groups){const g=svg('g',{'class':'kgv2-topic','data-topic':group.id});g.append(svg('rect',{x:group.x,y:group.y,width:group.width,height:group.height,rx:16,'class':'kgv2-topic-background'}));const header=svg('g',{tabindex:'0',role:'button','aria-expanded':String(!group.collapsed),'aria-label':group.label+'，'+group.nodes.length+'个概念，点击'+(group.collapsed?'展开':'折叠')});
   header.append(svg('rect',{x:group.x+4,y:group.y+4,width:group.width-8,height:46,rx:12,'class':'kgv2-topic-header'}));const title=svg('text',{x:group.x+16,y:group.y+31,'class':'kgv2-topic-title'});title.dataset.order=group.order;title.dataset.label=group.label;title.dataset.full=group.order+'. '+group.label+' ('+group.nodes.length+') '+(group.collapsed?'＋':'−');title.dataset.short=group.order+'. '+[...group.label].slice(0,5).join('')+(group.label.length>5?'…':'')+' '+(group.collapsed?'＋':'');title.textContent=title.dataset.full;header.append(title);activate(header,()=>{group.collapsed?state.collapsed.delete(group.label):state.collapsed.add(group.label);renderDiagram();});g.append(header);drawing.append(g);}
  if(state.mode==='overview'){for(const edge of model.edges.filter(e=>model.nodeGroup.get(e.from)===model.nodeGroup.get(e.to)))drawEdge(model.positions.get(edge.from),model.positions.get(edge.to),nodeIndex.get(edge.from).label+' → '+edge.label+' → '+nodeIndex.get(edge.to).label,edge,false);}
  else for(const edge of model.edges)drawEdge(model.positions.get(edge.from),model.positions.get(edge.to),nodeIndex.get(edge.from).label+' → '+edge.label+' → '+nodeIndex.get(edge.to).label,edge,false);
  for(const node of model.nodes){const p=model.positions.get(node.id);if(!p)continue;const g=svg('g',{'class':'kgv2-node','data-node':node.id,tabindex:'0',role:'button','aria-label':node.label+'，真实PPT '+node.pages.map(p=>'P'+p).join('、')+'，点击跳页并保持图谱镜头'});g.append(svg('rect',{x:p.x,y:p.y,width:p.width,height:p.height,rx:10}));
   const title=svg('title');title.textContent=node.label+'\n'+node.summary;g.append(title);const chars=[...node.label];for(let line=0;line<2;line++){const t=svg('text',{x:p.x+12,y:p.y+23+line*18,'class':'kgv2-node-label'});t.textContent=chars.slice(line*11,line*11+11).join('')+(line===1&&chars.length>22?'…':'');g.append(t);}
   const pages=svg('text',{x:p.x+12,y:p.y+61,'class':'kgv2-node-pages'});pages.textContent=pageRanges(node.pages);g.append(pages);activate(g,()=>go(node));drawing.append(g);}
  const shownEdges=model.edges.filter(e=>model.positions.has(e.from)&&model.positions.has(e.to)).length;
  status.textContent=model.positions.size+'/'+model.totalNodes+' 概念 · '+(state.mode==='overview'?'主题汇总图；全章 '+model.totalEdges+' 条关系':'已绘 '+shownEdges+'/'+model.edges.length+' 条关系')+(model.positions.size<model.nodes.length?'；折叠隐藏 '+(model.nodes.length-model.positions.size)+' 概念 / '+(model.edges.length-shownEdges)+' 条节点边，可展开':'')+(focused?' · 起点：'+nodeIndex.get(state.rootId).label+' · 关联距离≤'+model.depth:'');
  updateCurrent();rendering=false;root.requestAnimationFrame(()=>{if(serial!==renderSerial||state.mode==='list')return;const saved=state.cameras[state.mode];if(saved&&!reset)restoreCamera(saved);else if(focused&&model.positions.has(state.rootId))revealWorld(model.positions.get(state.rootId),.85);else fitAll();});

 }
 function setMode(next,fromSelector=false){saveCamera();state.collapsedByMode[state.mode]=state.collapsed;if(fromSelector&&(next==='focus2'||next==='focus3')&&state.rootId!==api.current().nodeId){state.rootId=api.current().nodeId;delete state.cameras.focus2;delete state.cameras.focus3;}state.mode=next;state.collapsed=state.collapsedByMode[next]||(state.collapsedByMode[next]=new Set());mode.value=next;const asList=next==='list';list.hidden=!asList;frame.hidden=asList;status.hidden=asList;minus.disabled=plus.disabled=fit.disabled=asList;rendering=true;if(!asList)renderDiagram();rendering=false;menu.open=false;}
 mode.addEventListener('change',()=>setMode(mode.value,true));minus.addEventListener('click',()=>setZoom(zoom/1.3));plus.addEventListener('click',()=>setZoom(zoom*1.3));fit.addEventListener('click',fitAll);
 actual.addEventListener('click',()=>{setZoom(1);menu.open=false;});current.addEventListener('click',()=>{const n=nodeIndex.get(api.current().nodeId);state.collapsed.delete(n.section||'知识主线');const band=model?.byGroup.get(model.nodeGroup.get(n.id));if(band)state.collapsed.delete(band.label);if(state.mode==='list'||!model.nodes.some(x=>x.id===n.id))setMode('overview');else renderDiagram();root.requestAnimationFrame(()=>revealWorld(model.positions.get(n.id),.95));menu.open=false;});
 focus.addEventListener('click',()=>{state.rootId=api.current().nodeId;setMode('focus2');state.collapsed.clear();state.collapsedByMode.focus3=new Set();delete state.cameras.focus2;delete state.cameras.focus3;renderDiagram(true);});expand.addEventListener('click',()=>{state.collapsed.clear();renderDiagram();menu.open=false;});collapse.addEventListener('click',()=>{state.collapsed=new Set([...data.nodes.map(n=>n.section||'知识主线'),...model.groups.map(g=>g.label)]);renderDiagram(true);menu.open=false;});
 topic.addEventListener('change',()=>{const label=topic.value;if(state.mode!=='overview'&&state.mode!=='all')setMode('overview');root.requestAnimationFrame(()=>{const group=model.groups.find(g=>g.label===label);if(group)revealWorld(group);});menu.open=false;});roomy.addEventListener('click',()=>{state.roomy=!state.roomy;panel.classList.toggle('kgv2-roomy',state.roomy);panel.parentElement?.classList.toggle('kgv2-roomy-workspace',state.roomy);roomy.textContent=state.roomy?'恢复并排阅读':'放大图谱区域';menu.open=false;root.requestAnimationFrame(renderMini);});
 panel.querySelector('.km-search')?.addEventListener('input',event=>{if(event.target.value.trim()){if(state.mode!=='list'){searchReturn=state.mode;setMode('list');menu.open=true;}}else if(state.mode==='list')setMode(searchReturn);});
 viewport.addEventListener('scroll',()=>{saveCamera();renderMini();},{passive:true});
 viewport.addEventListener('wheel',event=>{if(event.ctrlKey||event.metaKey){event.preventDefault();const box=viewport.getBoundingClientRect();setZoom(zoom*(event.deltaY<0?1.15:1/1.15),{x:event.clientX-box.left,y:event.clientY-box.top});}},{passive:false});
 viewport.addEventListener('pointerdown',event=>{if(event.pointerType==='touch'||event.button!==0||event.target.closest?.('[role="button"]'))return;drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.setPointerCapture?.(event.pointerId);});
 viewport.addEventListener('pointermove',event=>{if(drag&&event.pointerId===drag.id){viewport.scrollLeft=drag.left-(event.clientX-drag.x);viewport.scrollTop=drag.top-(event.clientY-drag.y);}});const end=()=>drag=null;viewport.addEventListener('pointerup',end);viewport.addEventListener('pointercancel',end);
 viewport.addEventListener('keydown',event=>{if(event.target!==viewport)return;const dirs={ArrowLeft:[-70,0],ArrowRight:[70,0],ArrowUp:[0,-70],ArrowDown:[0,70]};if(dirs[event.key]){event.preventDefault();viewport.scrollLeft+=dirs[event.key][0];viewport.scrollTop+=dirs[event.key][1];}else if(['+','=','-','Home'].includes(event.key)){event.preventDefault();event.key==='Home'?fitAll():setZoom(zoom*(event.key==='-'?1/1.3:1.3));}});
 mini.addEventListener('click',event=>{const box=mini.getBoundingClientRect(),view=viewport.getBoundingClientRect();viewport.scrollLeft=(event.clientX-box.left)/box.width*model.width*zoom-view.width/2;viewport.scrollTop=(event.clientY-box.top)/box.height*model.height*zoom-view.height/2;saveCamera();renderMini();});mini.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fitAll();}});
 menu.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.open){e.stopPropagation();menu.open=false;menuSummary.focus();}});
 function delayedCurrent(){root.requestAnimationFrame(()=>root.requestAnimationFrame(updateCurrent));}
 ['course:pagechange','em:pagechange','dsp:pagechange','hashchange','popstate'].forEach(type=>root.addEventListener(type,delayedCurrent));
 panel.querySelector('.km-back')?.addEventListener('click',delayedCurrent);
 panel.querySelector('.km-toggle')?.addEventListener('click',()=>root.requestAnimationFrame(()=>{if(!panel.classList.contains('km-collapsed')&&state.mode!=='list'){const box=viewport.getBoundingClientRect();if(box.width>0&&box.height>0&&!state.cameras[state.mode]){if(state.mode==='focus2'||state.mode==='focus3')revealWorld(model.positions.get(state.rootId),.85);else fitAll();}else renderMini();}}));
 root.addEventListener('resize',()=>root.requestAnimationFrame(renderMini));
 renderDiagram();
 root.CourseChapterGraph={model:()=>model,state:()=>({mode:state.mode,rootId:state.rootId,collapsed:[...state.collapsed],camera:camera(),cameras:JSON.parse(JSON.stringify(state.cameras))}),setMode,fit:fitAll,focusCurrent:()=>focus.click(),locate:()=>current.click()};
}
root.addEventListener('knowledge-map:ready',start);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:globalThis);
