#!/usr/bin/env node
'use strict';
// Rebuild with NODE_PATH pointing to mathjax-full@3.2.2 and marked@16.4.2.
// All formulas are static vector output. No third-party runtime is loaded by the page.
const fs=require('node:fs'),path=require('node:path');
const notation=require('./em-textbook-notation.cjs');
const {marked}=require('marked');
const {mathjax}=require('mathjax-full/js/mathjax.js');
const {TeX}=require('mathjax-full/js/input/tex.js');
const {SVG}=require('mathjax-full/js/output/svg.js');
const {liteAdaptor}=require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler}=require('mathjax-full/js/handlers/html.js');

require('mathjax-full/js/input/tex/base/BaseConfiguration.js');
require('mathjax-full/js/input/tex/ams/AmsConfiguration.js');
require('mathjax-full/js/input/tex/newcommand/NewcommandConfiguration.js');
require('mathjax-full/js/input/tex/boldsymbol/BoldsymbolConfiguration.js');
const root=path.resolve(__dirname,'..');
const adaptor=liteAdaptor();RegisterHTMLHandler(adaptor);
const tex=new TeX({packages:['base','ams','newcommand','boldsymbol'],formatError(_jax,error){throw error;}});
const svg=new SVG({fontCache:'none'});
const doc=mathjax.document('',{InputJax:tex,OutputJax:svg});
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
let count=0;
async function render(md){
  md=md.replace(/(<\/(?:section|details)>)\n(?=\S)/g,'$1\n\n').replace(/(?<!\n)\n(?=#{1,6} )/g,'\n\n');
  md=md.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  const formulas=[];
  md=md.replace(/\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$|\\\(([\s\S]*?)\\\)|(?<!\\)\$([^$\n]+?)(?<!\\)\$/g,(all,a,b,c,d)=>{
    const display=a!==undefined||b!==undefined,source=notation.normalizeTex((a??b??c??d).trim()),id=formulas.length;
    formulas.push({source,display});return `EMMATHPLACEHOLDER${id}END`;
  });
  let html=marked.parse(md,{gfm:true,breaks:false});
  for(let i=0;i<formulas.length;i++){
    const {source,display}=formulas[i];
    const node=doc.convert(notation.definitions+notation.typesetTex(source),{display});
    let output=adaptor.outerHTML(node).replace('<svg ','<svg aria-hidden="true" ');
    if(/data-mml-node="merror"|<text\b/.test(output))throw Error('Formula did not render fully: '+source);
    const tag=display?'div':'span';
    const math=`<${tag} class="hw-math hw-math-${display?'display':'inline'}" data-tex="${escape(source)}" role="math" aria-label="${escape(source)}"${display?' tabindex="0"':''}>${output}</${tag}>`;
    const placeholder=`EMMATHPLACEHOLDER${i}END`;
    html=display?html.replace(`<p>${placeholder}</p>`,math).replace(placeholder,math):html.replace(placeholder,math);count++;
  }
  html=html.replace(/<table>/g,'<div class="table-scroll" tabindex="0" role="region" aria-label="表格，可横向滚动"><table>').replace(/<\/table>/g,'</table></div>');
  return html;
}
const questions=[{id:'q251',title:'2.5-1 · 电场、磁场与能量流向',md:'q251.md',images:[['original-2-5-1.png','教材原题，印刷第62页 / PDF第79页']],ppt:[['ppt2.html#p47','第2章 P47 · 由场方程推坡印廷定理'],['ppt2.html#p48','P48 · 储能、体损耗与功率平衡'],['ppt2.html#p49','P49 · 坡印廷矢量与能流方向'],['ppt2.html#p51','P51 · 类比：导线侧面能流与焦耳热']]},{id:'q363',title:'3.6-3 · 60°导体劈与镜像法',md:'q363.md',images:[['original-3-6-3.png','教材原题，印刷第104页 / PDF第121页'],['figure-3-6-3b.png','题目引用图 3.6-3(b)，印刷第90页 / PDF第107页']],ppt:[['ppt3.html#p05','第3章 P5 · 静电场唯一性定理'],['ppt3.html#p06','P6 · 镜像法的原则'],['ppt3.html#p11','P11 · 接地导体劈与五镜像'],['ppt3.html#p12','P12 · 60°导体劈的镜像示意'],['ppt3.html#p13','P13 · 镜像法小结与本次作业']]}];
(async()=>{
  let bodies='';
  for(const q of questions){
    const md=fs.readFileSync(path.join(root,'docs/em-energy-wedge',q.md),'utf8');
    bodies+=`<article class="em-section" id="${q.id}"><div class="em-question-head"><h2>${q.title}</h2><a href="#top">回到两题目录 ↑</a></div><p class="em-label">原题与来源</p>`;
    for(const [file,caption]of q.images)bodies+=`<figure class="original-question em-source"><a href="assets/em-energy-wedge/${file}" target="_blank" rel="noopener" aria-label="打开原尺寸：${caption}"><img src="assets/em-energy-wedge/${file}" alt="${caption}" loading="lazy"></a><figcaption>${caption}。点击原图查看原尺寸。</figcaption></figure>`;
    bodies+=`<div class="em-ppt-links" aria-label="对应原课件">${q.ppt.map(([url,label])=>`<a href="/study-site/${url}">${label}</a>`).join('')}</div><figure><div class="hw-figure-scroll"><img class="hw-diagram" src="assets/em-energy-wedge/${q.id==='q251'?'energy-flow.svg':'image-charges.svg'}" alt="${q.id==='q251'?'导电介质的轴向电流、环向磁场与向内能流':'按本题精确坐标画出的六个点电荷与60°物理角域'}"></div><figcaption>教学示意图，与上方教材原图分开标明。${q.id==='q363'?'Q1—Q6 对应正文编号 1—6。':''}窄屏可横向滑动查看全图。</figcaption></figure><div class="em-body">${await render(md)}</div></article>`;
  }
  const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="电磁场作业2.5-1与3.6-3：原题、可抄主解、多种解法、完整推导与教材课件回链。"><title>能流与镜像法 · 两题多解</title><link rel="stylesheet" href="/study-site/homework-20261028.css"><link rel="stylesheet" href="/study-site/em-energy-wedge.css"></head><body><main id="top"><header class="hw-hero"><p class="hw-eyebrow">ELECTROMAGNETICS · 2026.11.14</p><h1>能流与镜像法<br>两题多解</h1><p>2.5-1 看能量怎样流进介质并变成热；3.6-3 用镜像电荷满足60°导体的边界。先看可抄主解，需要时展开推导、方法比较与自检。</p><p class="source-note">钟顺时《电磁场与波》第2版（2015）。完整条件以本页原题和引用原图为准；页码区分教材印刷页、PDF文件页与PPT物理页。</p></header><nav class="em-roadmap" aria-label="两道作业"><a href="#q251"><strong>2.5-1</strong><span>导电介质 · 坡印廷矢量 · 总损耗</span></a><a href="#q363"><strong>3.6-3</strong><span>60°劈 · 接地导体劈与五镜像 · 电位</span></a></nav><div class="em-ppt-links" aria-label="直接阅读可抄主解"><a href="#q251-answer">直接到 2.5-1 可抄主解 ↓</a><a href="#q363-answer">直接到 3.6-3 可抄主解 ↓</a></div><div class="hw-tools"><button id="emExpand" type="button">展开全部推导</button><button id="emCollapse" type="button">收起扩展推导</button><button id="emPrint" type="button">打印两题</button><button id="emAskOpen" type="button">复制问题给 dot</button></div><div class="hw-content">${bodies}</div><footer class="hw-footer"><p>原题仅摘录本次题目及必要引用图，不公开整本教材。题解交付不代替独立检查，也不代表作业已提交。</p><p><a href="/study-site/ppt.html#homework">电磁场作业归档</a> · <a href="/study-site/courses.html">学习首页</a></p></footer></main><dialog class="hw-ask-dialog" id="emAskDialog" aria-labelledby="emAskTitle"><h2 id="emAskTitle">复制问题与定位</h2><div class="em-ask-grid"><label>选择题目<select id="emAskQuestion"><option value="q251">2.5-1 · 能流与损耗</option><option value="q363">3.6-3 · 60°劈镜像</option></select></label><label>补充你卡住的地方<textarea id="emAskText" rows="9"></textarea></label></div><p id="emAskStatus" role="status" aria-live="polite"></p><div class="hw-tools"><button type="button" id="emAskCopy">复制</button><button type="button" id="emAskClose">关闭</button></div></dialog><script src="/study-site/em-energy-wedge.js"></script><script src="/study-site/phase2-preview.js"></script></body></html>`;
  fs.writeFileSync(path.join(root,'site/em-energy-wedge-homework.html'),html);
  console.log(`Built 2 questions with ${count} static SVG formulas.`);
})().catch(e=>{console.error(e);process.exitCode=1;});

