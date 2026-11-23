#!/usr/bin/env node
'use strict';
/* Apply the reviewed static SVG cache (plain Node); --render rebuilds that cache
 * after changing the two notation macros or the companion LaTeX sources.
 * Renderer dependencies, not deployed to readers: @mathjax/src@4.1.0,
 * @mathjax/mathjax-newcm-font@4.1.0. No browser runtime or CDN. */
const fs=require('node:fs'), path=require('node:path'), zlib=require('node:zlib');
const {createHash}=require('node:crypto');
const notation=require('./em-textbook-notation.cjs');
const root=path.resolve(__dirname,'..'), partDir=path.join(root,'source-parts/em-companion-notation');
const chapters=[0,1,2,3,5,6,7], pages=chapters.flatMap(n=>['ppt'+n+'.html','em-math-preview-'+n+'.html']);
const candidates=/\\(?:mathbf|boldsymbol|hat)(?![A-Za-z])/;
const tag=/(<svg\b(?=[^>]*\bclass="formula(?:\s[^"]*)?")(?=[^>]*\baria-label="([^"]+)")[^>]*>)\s*<use\b[^>]*\bhref="#math-[^"]+"[^>]*>\s*<\/use>\s*<\/svg>/g;
const dec=s=>s.replace(/&quot;/g,'"').replace(/&#(?:39|x27);/gi,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const esc=s=>s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const hash=s=>createHash('sha256').update(s).digest('hex');
const id=(t,inline)=>hash((inline?'T:':'D:')+t).slice(0,32);
const revision=hash(notation.companionDefinitions+'\n'+notation.companionTex.toString());
const sourceOf=(name)=>fs.readFileSync(path.join(root,'site',name),'utf8');
function formulas(s){
  return Array.from(s.matchAll(tag),m=>({raw:dec(m[2]),inline:/class="formula inline"/.test(m[1])})).filter(f=>candidates.test(f.raw));
}
const normalize=notation.companionTex;
function writeCache(data){
  const packed=zlib.deflateSync(Buffer.from(JSON.stringify(data)),{level:9}), entries=[];
  fs.mkdirSync(partDir,{recursive:true});
  for(let off=0;off<packed.length;off+=49152){
    const bytes=packed.subarray(off,off+49152), filename='svg.'+String(entries.length+1).padStart(3,'0')+'.b64';
    fs.writeFileSync(path.join(partDir,filename),bytes.toString('base64')+'\n');
    entries.push({file:filename,bytes:bytes.length,sha256:hash(bytes)});
  }
  fs.writeFileSync(path.join(partDir,'manifest.json'),JSON.stringify({format:1,revision,sha256:hash(packed),parts:entries},null,2)+'\n');
}
function readCache(){
  const manifest=JSON.parse(fs.readFileSync(path.join(partDir,'manifest.json'),'utf8'));
  if(manifest.format!==1||manifest.revision!==revision||!manifest.parts.length||manifest.parts.length>120)throw Error('Regenerate the companion cache after changing its notation definitions.');
  const packed=Buffer.concat(manifest.parts.map((part,i)=>{
    if(part.file!=='svg.'+String(i+1).padStart(3,'0')+'.b64')throw Error('Invalid companion cache part');
    const b=Buffer.from(fs.readFileSync(path.join(partDir,part.file),'utf8').trim(),'base64');
    if(b.length!==part.bytes||b.length>49152||hash(b)!==part.sha256)throw Error('Damaged companion cache part '+part.file);
    return b;
  }));
  if(hash(packed)!==manifest.sha256)throw Error('Bad companion cache');
  return JSON.parse(zlib.inflateSync(packed,{maxOutputLength:40*1024*1024}));
}
async function render(){
  const {mathjax}=require('@mathjax/src/js/mathjax.js'),{TeX}=require('@mathjax/src/js/input/tex.js');
  const {SVG}=require('@mathjax/src/js/output/svg.js'),{liteAdaptor}=require('@mathjax/src/js/adaptors/liteAdaptor.js');
  const {RegisterHTMLHandler}=require('@mathjax/src/js/handlers/html.js');
  require('@mathjax/src/js/util/asyncLoad/node.js');
  for(const p of ['base/Base','ams/Ams','newcommand/Newcommand','boldsymbol/Boldsymbol'])require('@mathjax/src/js/input/tex/'+p+'Configuration.js');
  const {MathJaxNewcmFont}=require('@mathjax/mathjax-newcm-font/js/svg.js');
  const adaptor=liteAdaptor();RegisterHTMLHandler(adaptor);
  const tex=new TeX({packages:['base','ams','newcommand','boldsymbol'],formatError(_j,e){throw e;}});
  const svg=new SVG({fontCache:'global',fontData:MathJaxNewcmFont,
    dynamicPrefix:path.dirname(require.resolve('@mathjax/mathjax-newcm-font/js/svg/dynamic/script.js')),
    displayOverflow:'overflow',linebreaks:{inline:false}});
  const doc=mathjax.document('',{InputJax:tex,OutputJax:svg});
  const items={};
  for(const p of pages){
    const source=sourceOf(p);
    if(source.includes('class="em-companion-defs"'))throw Error('Rebuild from the unprocessed static sources');
    for(const {raw,inline} of formulas(source)){
      const n=normalize(raw),key=id(n,inline);if(items[key])continue;
      let math;
      try {math=adaptor.outerHTML(await doc.convertPromise(notation.companionDefinitions+n,{display:!inline}));}
      catch(e){throw Error(p+' '+raw+' -> '+n+': '+e);}
      const m=math.match(/^<mjx-container\b[^>]*>\s*<svg\b([^>]*)>([\s\S]*)<\/svg>\s*<\/mjx-container>$/);
      if(!m||/mjx-break|data-mml-node="merror"|data-c="5C"|data-mml-node="mtext"[^>]*mathcolor="red"/.test(math))throw Error('Invalid static SVG: '+p+' '+raw);
      const box=m[1].match(/\bviewBox="([^"]+)"/)[1].split(/[\s,]+/).map(Number);
      if(box.length!==4||box.some(x=>!Number.isFinite(x))||box[2]<=0||box[3]<=0||box[2]>90000)throw Error('Unexpected formula geometry: '+p+' '+raw);
      // Keep mathematical layout nodes for regression checks, but remove the
      // compiler's repetitive source strings. aria-label on each use is canonical.
      const body=m[2].replace(/ data-latex="[^"]*"/g,'').replace(/ data-mjx-texclass="[^"]*"/g,'');
      if(Array.from(body.matchAll(/<text\b[^>]*>([^<]*)<\/text>/g)).some(x=>!/[^\u0000-\u00ff]/.test(x[1])))throw Error('Fallback math text: '+raw);
      items[key]={box,body};
    }
  }
  const defs={};const cache=adaptor.outerHTML(svg.fontCache.getCache());
  for(const m of cache.matchAll(/<path\b[^>]*\bid="([^"]+)"[^>]*(?:><\/path>|\/>)/g))defs[m[1]]=m[0].replace(/><\/path>$/,'/>');
  const data={items,defs};
  for(const x of Object.values(items))for(const y of x.body.matchAll(/xlink:href="#([^"]+)"/g))if(!defs[y[1]])throw Error('No glyph '+y[1]);
  writeCache(data);console.log('Rendered '+Object.keys(items).length+' unique equations, '+Object.keys(defs).length+' offline glyphs');
}
function number(x){return Number(x.toFixed(5));}
function apply(){
  const {items,defs}=readCache();let changed=0;const nPages=[];
  for(const name of pages){
    let src=sourceOf(name);
    if(src.includes('class="em-companion-defs"'))continue;
    const used=new Set(), instances=new Map();let n=0;
    const before=formulas(src).length;
    // Consume only a known formula shape and its optional inline baseline span.
    // The rest of every page, including all PPT image bytes, is passed through.
    const rex=new RegExp('(<span class="inline-math-scroll"[^>]*>)?'+tag.source,'g');
    src=src.replace(rex,(whole,wrapper,opening,label)=>{
      const raw=dec(label);if(!candidates.test(raw))return whole;
      const norm=normalize(raw),inline=/class="formula inline"/.test(opening),key=id(norm,inline),item=items[key];
      if(!item)throw Error('New formula in '+name+'; rerun --render: '+raw);
      const [x,y,w,h]=item.box,depth=number((y+h)/1000),uid='em-eq-'+key;
      for(const g of item.body.matchAll(/xlink:href="#([^"]+)"/g))used.add(g[1]);
      instances.set(uid,'<symbol id="'+uid+'" viewBox="'+item.box.join(' ')+'">'+item.body+'</symbol>');
      n++;
      const accessible=norm.replace(/\\emvec\{/g,'\\bar{').replace(/\\emunit\{/g,'\\hat{').replace(/\\emdiff\{/g,'\\overline{\\mathrm d ');
      const beforeTag=wrapper?wrapper.replace(/vertical-align:\s*-?[\d.]+em/g,'vertical-align:'+(-depth)+'em'):''; 
      return beforeTag+'<svg class="formula '+(inline?'inline ':'')+'em-companion-formula" role="img" aria-label="'+esc(accessible)+'" data-tex="'+esc(norm)+'" '+(inline?'data-math-style="text" data-math-depth="'+depth+'" ':'')+'width="'+number(w/1000)+'em" height="'+number(h/1000)+'em" viewBox="0 0 '+w+' '+h+'" style="width:'+number(w/1000)+'em;height:'+number(h/1000)+'em;'+(inline?'--math-depth:'+depth+'em;display:block':'')+'"><use href="#'+uid+'"></use></svg>';
    });
    if(n!==before)throw Error('Incomplete conversion on '+name+': '+n+'/'+before);
    if(!n)continue;
    const symbols='<svg class="em-companion-defs" width="0" height="0" aria-hidden="true" focusable="false" style="position:absolute;overflow:hidden" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><defs>'+[...used].map(k=>defs[k]).join('')+[...instances.values()].join('')+'</defs></svg>';
    src=src.replace(/(<body\b[^>]*>)/,'$1'+symbols)
      .replace('</head>','<link rel="stylesheet" href="/study-site/em-companion-notation.css?v=2">\n</head>');
    if(name==='ppt2.html'||name==='em-math-preview-2.html'){
      src=src.replaceAll('这里用粗体下标','这里用下标')
        .replaceAll('P49的粗体','P49 中上方带短横的').replaceAll('是外向面积元；粗体','是外向面积元；上方带短横的').replaceAll('原页用不加粗的','原页用不带短横的')
        .replaceAll('这里无粗体的','这里不带短横的');
    }
    fs.writeFileSync(path.join(root,'site',name),src);
    nPages.push(name+':'+n);changed+=n;
  }
  console.log('Static textbook notation: '+changed+' occurrences; '+nPages.join(', '));
}
if(require.main===module){(process.argv.includes('--render')?render():Promise.resolve().then(apply)).catch(e=>{console.error(e);process.exitCode=1;});}
module.exports={id,formulas,apply,render,readCache,normalize,pages};
