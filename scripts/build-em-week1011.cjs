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
const questions=[
 {id:'q372',number:'3.7-2',title:'矩形区域 · 三角形右边界电位',pages:'印刷第104页 / PDF第121页',ppt:[['ppt3.html#p14','第3章 P14 · 分离变量法'],['ppt3.html#p15','P15 · 拉普拉斯方程分离'],['ppt3.html#p16','P16 · 边界条件与本征函数'],['ppt3.html#p24','P24 · 本节小结与作业']]},
 {id:'q373',number:'3.7-3',title:'混合边界 · 顶边法向导数为零',pages:'印刷第105页 / PDF第122页',ppt:[['ppt3.html#p14','第3章 P14 · 分离变量法'],['ppt3.html#p16','P16 · 分离常数和边界'],['ppt3.html#p24','P24 · 本节小结与作业']]},
 {id:'q514',number:'5.1-4',title:'正弦场 · 瞬时式与矢量相量',pages:'印刷第161页 / PDF第178页',ppt:[['ppt5.html#p03','第5章 P3 · 正弦量与复数'],['ppt5.html#p08','P8 · 相量小结与本题']]},
 {id:'q521',number:'5.2-1',title:'时谐场 · 复 Maxwell 方程',pages:'印刷第161页 / PDF第178页',ppt:[['ppt5.html#p10','第5章 P10 · 复 Maxwell 方程'],['ppt5.html#p15','P15 · 本节小结与作业']]},
 {id:'q532',number:'5.3-2',title:'同轴线 · 向负载传输的总功率',pages:'印刷第161页 / PDF第178页',ppt:[['ppt5.html#p17','第5章 P17 · 复坡印廷矢量'],['ppt5.html#p20','P20 · 瞬时值与平均值'],['ppt5.html#p25','P25 · 本节作业']]},
 {id:'q534',number:'5.3-4',title:'有效值相量 · 瞬时与平均功率流',pages:'印刷第161—162页 / PDF第178—179页',ppt:[['ppt5.html#p17','第5章 P17 · 复坡印廷矢量'],['ppt5.html#p20','P20 · 瞬时值与平均值'],['ppt5.html#p25','P25 · 本节作业']]}
];
const sourceNote='钟顺时《电磁场与波》第2版（2015），ISBN 9787302389484。页码区分印刷页、PDF文件页与PPT物理页。本页提供核对后的题目条件转述、原创题解和自绘示意，不公开教材扫描页。';
const head=(title,extra='')=>`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="第10—11周电磁场六题：分离变量、相量、复 Maxwell 方程与复坡印廷矢量。教材原题、可抄答案、详细推导及原PPT。"><title>${title}</title><link rel="stylesheet" href="/study-site/homework-20261028.css"><link rel="stylesheet" href="/study-site/em-energy-wedge.css"><link rel="stylesheet" href="/study-site/em-week1011.css"></head><body${extra}><main id="top">`;
const notationNote='<aside class="em-note"><strong>符号与相量约定</strong><p>矢量在主字母上方加短横线，单位方向只加尖帽；下标和撇号放在横线外。第5章相量保留圆点。一般题采用峰值相量；5.3-4 按题意采用带下标 e 的有效值相量，两者的功率系数不可混用。各题的重建式和系数在对应解答中明确写出。</p></aside>';
(async()=>{
 let bodies='',answers='';
 for(const q of questions){
  const md=fs.readFileSync(path.join(root,'docs/em-week1011',q.id+'.md'),'utf8');
  const answer=md.match(new RegExp(`<section[^>]*id="${q.id}-answer"[^>]*>([\\s\\S]*?)<\\/section>`));
  if(!answer)throw Error('Missing copyable answer section '+q.id);
  const body=await render(md);
  bodies+=`<article class="em-section" id="${q.id}"><div class="em-question-head"><h2>${q.number} · ${q.title}</h2><a href="#top">回到六题目录</a></div><p class="em-source-list">题目条件已核对：钟顺时《电磁场与波》第2版，${q.pages}。</p>${['q372','q373'].includes(q.id)?`<figure><div class="hw-figure-scroll"><img class="hw-diagram" src="assets/em-week1011/${q.id}-boundary.svg" alt="${q.number} 的边界条件与右边界电位自绘示意"></div><figcaption>按本题条件重新绘制，非教材扫描图。窄屏可横向查看。</figcaption></figure>`:''}<div class="em-ppt-links" aria-label="对应原课件">${q.ppt.map(([url,label])=>`<a href="/study-site/${url}">${label}</a>`).join('')}</div><div class="em-body">${body}</div></article>`;
  answers+=`<article class="em-section" id="${q.id}"><h2>${q.number} · ${q.title}</h2><div class="em-body"><section class="em-answer" id="${q.id}-answer">${await render(answer[1])}</section></div><p><a href="em-week1011-homework.html#${q.id}">查看本题原题与详细解析</a></p></article>`;
 }
 const roadmap=`<nav class="em-roadmap" aria-label="六道作业">${questions.map(q=>`<a href="#${q.id}"><strong>${q.number}</strong><span>${q.title}</span></a>`).join('')}</nav>`;
 const html=head('第10—11周 · 电磁场六题多解')+`<header class="hw-hero"><p class="hw-eyebrow">ELECTROMAGNETICS · 第10—11周</p><h1>电磁场六题<br>从边界到能量流</h1><p>3.7-2、3.7-3、5.1-4、5.2-1、5.3-2、5.3-4。先看可以直接手写的主解，再按需展开推导与方法比较，不从头重讲整章。</p><p class="source-note">${sourceNote}</p></header>${roadmap}<div class="em-ppt-links"><a href="em-week1011-answers.html">只看可抄答案 / 打印</a><a href="em-week1011-answers.txt">纯文本答案</a><a href="ppt.html#homework">电磁场作业归档</a></div>${notationNote}<div class="hw-tools"><button id="emExpand" type="button">展开全部推导</button><button id="emCollapse" type="button">收起扩展推导</button><button id="emPrint" type="button">打印六题</button><button id="emAskOpen" type="button">复制问题给 dot</button></div><div class="hw-content">${bodies}</div><footer class="hw-footer"><p>条件及符号已与上述教材页核对。题解交付不代表作业已提交，也不会修改学习进度或计时记录。</p><a href="/study-site/courses.html">学习首页</a></footer></main><dialog class="hw-ask-dialog" id="emAskDialog" aria-labelledby="emAskTitle"><h2 id="emAskTitle">复制问题与定位</h2><div class="em-ask-grid"><label>选择题目<select id="emAskQuestion">${questions.map(q=>`<option value="${q.id}">${q.number} · ${q.title}</option>`).join('')}</select></label><label>补充你卡住的地方<textarea id="emAskText" rows="9"></textarea></label></div><p id="emAskStatus" role="status" aria-live="polite"></p><div class="hw-tools"><button type="button" id="emAskCopy">复制</button><button type="button" id="emAskClose">关闭</button></div></dialog><script src="/study-site/em-week1011.js"></script><script src="/study-site/phase2-preview.js"></script></body></html>`;
 fs.writeFileSync(path.join(root,'site/em-week1011-homework.html'),html);
 fs.writeFileSync(path.join(root,'site/em-week1011-answers.html'),head('电磁场第10—11周 · 可抄答案',' class="em-answer-only"')+`<header class="hw-hero"><p class="hw-eyebrow">COPY / PRINT</p><h1>六题可抄答案</h1><p>${sourceNote}</p><p><a href="em-week1011-homework.html">返回详细解析与原题</a> · <a href="em-week1011-answers.txt">纯文本</a></p></header>${notationNote}<div class="hw-tools"><button type="button" onclick="window.print()">打印答案</button></div><div class="hw-content">${answers}</div></main><script src="/study-site/phase2-preview.js"></script></body></html>`);
 console.log(`Built six verified questions and copy-only page with ${count} static SVG formulas.`);
})().catch(e=>{console.error(e);process.exitCode=1;});
