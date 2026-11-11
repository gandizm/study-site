#!/usr/bin/env python3
"""Build static, accessible two-pass teaching pages from reviewed Markdown.

Requirements: pandoc and lxml. No CDN, user data, network, or legacy progress writes.
"""
from pathlib import Path
import re, subprocess, shutil, html as esc, json, os
from copy import deepcopy
from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
INPUT = ROOT / 'docs/communications-lessons'
UPSTREAM = Path(os.environ.get('COMM_INPUT_DIR', str(INPUT)))
INPUT.mkdir(parents=True, exist_ok=True)

def clean_source(text):
    # Public lesson provenance names and physical pages are kept; operational paths are not.
    text = re.sub(r'\[([^\]]+)\]\(https://(?:docs|drive)\.google\.com/[^)]+\)',r'\1',text)
    return '\n'.join(line for line in text.splitlines() if not re.search(r'/workspace/|library_file_id|libfile_|agent_notes|collaboration\.', line)) + '\n'

for name in ['roadmap.md','chapter5.md','chapter6.md','chapter7.md','homework-first.md','homework-last.md']:
    source = UPSTREAM/name
    if source.exists() and source.resolve() != (INPUT/name).resolve():
        (INPUT/name).write_text(clean_source(source.read_text()), encoding='utf-8')

def convert(text):
    text = re.sub(r'(?m)(?<!\n)\n(?=##?\s)', '\n\n', text)
    text = re.sub(r'\{\\rm\s+([^{}]+)\}', r'\\mathrm{\1}', text)
    proc = subprocess.run(['pandoc','-f','markdown+tex_math_dollars+tex_math_single_backslash','-t','html5','--mathml','--wrap=none'],input=text,text=True,capture_output=True,check=True)
    if proc.stderr.strip():
        raise ValueError('Pandoc conversion warning: '+proc.stderr)
    return html.fragment_fromstring('<div>'+proc.stdout+'</div>')

def node(tag, text=None, **attrs):
    el=html.Element(tag)
    for key,value in attrs.items():el.set(key.replace('_','-'),str(value))
    if text is not None:el.text=text
    return el

def figure(filename, alt, caption=None):
    el=node('figure',_class='comm-figure')
    el.set('class','comm-figure');el.attrib.pop('-class',None)
    bar=node('div',_class='figure-toolbar');bar.set('class','figure-toolbar');bar.attrib.pop('-class',None)
    bar.append(node('span','原创重绘 · 单图全宽'))
    bar.append(node('button','放大看清楚 ↗',type='button',data_open_figure=''))
    el.append(bar)
    el.append(node('img',src='communications-redraw/assets/'+filename,alt=alt,loading='lazy',width='1000'))
    el.append(node('figcaption',caption or alt))
    return el

def decorate(fragment):
    for table in list(fragment.xpath('.//table')):
        wrap=node('div',role='region',aria_label='表格，可横向滚动',tabindex='0');wrap.set('class','table-scroll')
        parent=table.getparent();parent.replace(table,wrap);wrap.append(table)
    for math in fragment.xpath('.//*[local-name()="math"]'):
        if math.get('display')=='block':
            parent=math.getparent()
            if parent.tag=='span':parent.set('class','math display');parent.set('role','region');parent.set('aria-label','公式，可横向滚动');parent.set('tabindex','0')
            elif parent.tag=='p':parent.set('role','region');parent.set('aria-label','公式，可横向滚动');parent.set('tabindex','0')
    for img in list(fragment.xpath('.//img')):
        src=img.get('src','');filename=Path(src).name
        if src.startswith('figures/'):
            replacement=figure(filename,img.get('alt','课件重绘'))
            parent=img.getparent()
            if parent.tag in ['p','figure']:
                # Pandoc figures may include a caption. Replace only the image container.
                if parent.tag=='p' and parent.getparent() is not None:parent.getparent().replace(parent,replacement)
                else:parent.getparent().replace(parent,replacement)
            else:parent.replace(img,replacement)
    return fragment

def copy_toolbar():
    div=node('div');div.set('class','copy-toolbar')
    div.append(node('button','复制解答文字',type='button',data_copy_answer=''))
    div.append(node('button','打印当前题',type='button',data_print=''))
    status=node('span',role='status',aria_live='polite');status.set('class','copy-status');div.append(status)
    return div

def classify_block(title):
    if any(word in title for word in ['第二遍','深挖','选读','推导细节','按需展开','学习解释']):return 'deep'
    return 'normal'

def sections(text):
    frag=decorate(convert(text))
    result=[];title=None;items=[];preamble=[]
    for el in list(frag):
        if el.tag=='h1':continue
        if el.tag=='h2':
            if title is not None:result.append((title,items))
            title=el.text_content();items=[]
        elif title is None:preamble.append(el)
        else:items.append(el)
    if title is not None:result.append((title,items))
    return result,preamble

def wrap_blocks(items, homework=False):
    out=[];heading=None;body=[]
    def flush():
        if not body:return
        if heading is None:
            wrap=node('div');wrap.set('class','unit-prose')
            for el in body:wrap.append(el)
            out.append(wrap);return
        title=heading.text_content()
        deep=classify_block(title)=='deep'
        wrap=node('details' if deep else 'section');wrap.set('class','deep-block' if deep else 'lesson-block')
        if deep:
            summary=node('summary');label=node('span','按需阅读' if '学习解释' in title else '扩展 · 第二遍');label.set('class','deep-label');summary.append(label);label.tail=title;wrap.append(summary)
        else:
            title_el=node('h3', '可抄解答 · 分步完成' if homework and '分步解答' in title else title);title_el.set('class','block-title');wrap.append(title_el)
        content=node('div');content.set('class','block-body')
        if homework and ('分步解答' in title or '可抄解答' in title):
            content.append(copy_toolbar());answer=node('div');answer.set('class','copy-answer')
            for el in body:answer.append(el)
            content.append(answer)
        else:
            for el in body:content.append(el)
        # Later homework chapters mark the answer within the first-pass prose.
        if homework and not content.xpath('.//*[@class="copy-answer"]'):
            elements=list(content); start=next((i for i,el in enumerate(elements) if el.tag=='p' and el.text_content().strip().startswith(('可抄解答','可抄证明'))),None)
            if start is not None:
                stop=next((i for i in range(start+1,len(elements)) if elements[i].tag=='p' and elements[i].text_content().strip().startswith(('为什么','自检','一句话'))),len(elements))
                content.insert(start+1,copy_toolbar());answer=node('div');answer.set('class','copy-answer')
                content.insert(start+2,answer)
                for el in elements[start+1:stop]:answer.append(el)
        if '自检' in title:
            elements=list(content)
            start=next((i for i,el in enumerate(elements) if el.tag=='p' and el.text_content().strip().startswith(('答案','答：'))),None)
            if start is not None:
                answer=node('details');answer.set('class','answer-check');answer.append(node('summary','先自己想，再看答案'))
                content.insert(start,answer)
                for el in elements[start:]:answer.append(el)
        wrap.append(content);out.append(wrap)
    for el in items:
        if el.tag=='h3':flush();heading=el;body=[]
        else:body.append(el)
    flush()
    return out

CHAPTERS={
 'intro':('三章学习地图','三章主线'),
 'ch5':('第五章 · 模拟信号数字化','5 · 模拟数字化'),
 'ch6':('第六章 · 数字基带传输','6 · 基带传输'),
 'ch7':('第七章 · 数字频带传输','7 · 频带传输'),
 'homework':('第五章 · 八题边抄边学','第五章作业')
}
EXTRA_FIGURES={
 'intro':[('three-chapter-chain.svg','三章在同一条通信链路里的位置')],
 'ch5':[], 'ch6':[], 'ch7':[]
}

def make_units(text,chapter,homework=False):
    chunks,preamble=sections(text);units=[];source_footer=[]
    for index,(title,items) in enumerate(chunks):
        if homework:
            match=re.search(r'5\.9\.(\d+)',title)
            if not match:source_footer.extend(items);continue
            uid='q'+match.group(1);short='5.9.'+match.group(1)
        else:
            uid=f'{chapter}-{index:02d}'
            short=re.sub(r'^[零一二三四五六七八九十\d]+\s*[.、·：:]\s*','',title)
            short=re.sub(r'\*','',short)
            if len(short)>25:short=short[:24]+'…'
        unit=node('article',id=uid,data_chapter=chapter,data_chapter_title=CHAPTERS[chapter][0],data_short=short)
        unit.set('class','comm-unit');unit.set('aria-labelledby',uid+'-title')
        if homework and any(el.tag=='h3' and '学习解释' in el.text_content() for el in items):
            unit.set('data-answer-first','true')
        header=node('header');header.set('class','unit-heading');label=node('p',CHAPTERS[chapter][0]);label.set('class','unit-index');header.append(label);header.append(node('h2',title,id=uid+'-title'));unit.append(header)
        for block in wrap_blocks(items,homework):unit.append(block)
        units.append(unit)
    if units and chapter=='intro':units[0].insert(1,figure('three-chapter-chain.svg','三章在同一条通信链路里的位置'))
    chapter_figures = {
        'ch5-01':('hw-5-9-1.svg','作业5.9.1对照：抽样后副本重叠要相加'),
        'ch5-03':('quantization-midpoint.svg','作业5.9.9对照：量化范围与中点重建'),
        'ch5-09':('tdm-slots.svg','作业5.9.25对照：抽样周期、时隙与脉宽'),
        'ch6-01':('line-codes.svg','同一比特串的三种线路码型'),
        'ch6-03':('zero-isi-sinc.svg','波形重叠不等于抽样点有干扰'),
        'ch6-04':('raised-cosine.svg','固定码元速率下的升余弦带宽与时域尾巴'),
        'ch6-06':('binary-decision.svg','等概双极高斯噪声判决模型'),
        'ch7-00':('digital-modulations.svg','幅度、频率、相位：同一比特串的三种发送方式'),
        'ch7-10':('qpsk-constellation.svg','QPSK星座：两条正交方向各承载一个比特')
    }
    for unit in units:
        if unit.get('id') in chapter_figures:
            # Let first-time concepts precede the more complete reference figure.
            deep=next((el for el in unit if el.get('class')=='deep-block'),None)
            pos=unit.index(deep) if deep is not None else len(unit)
            unit.insert(pos,figure(*chapter_figures[unit.get('id')]))
    # First-pass foundations for chapters 6 and 7 precede inherited detailed lessons.
    novice_figures = {
        'ch6-00':('novice-pulse-convolution.svg','脉冲、移位与短记忆卷积示例'),
        'ch6-06':('novice-noise-decision.svg','噪声把抽样值推过门限的过程'),
        'ch6-07':('novice-eye-diagram.svg','由升余弦总响应叠加的眼图及加入扰动的示意'),
        'ch7-00':('novice-carrier-coherent.svg','相位、相干乘法与整段平均'),
        'ch7-10':('novice-qpsk-iq.svg','QPSK比特对、星座坐标与合成载波'),
    }
    for unit in units:
        if unit.get('id') in novice_figures:
            filename, alt = novice_figures[unit.get('id')]
            first = next((el for el in unit if el.get('class') == 'lesson-block'), None)
            unit.insert(unit.index(first)+1 if first is not None else len(unit),
                        figure(filename, alt, alt+'。图中数值用于解释概念，不是实际链路测量。'))
    # Specific original numerical illustrations supplement the reviewed prose.
    if homework:
        extras={'q9':('quantization-midpoint.svg','0～20 V分40格：量程边界与重建电平分开'), 'q14':('alaw-cell.svg','输入−95：幅度小格92～96，中点94'), 'q25':('tdm-slots.svg','24路轮流占用时隙，脉宽为半个时隙')}
        for unit in units:
            if unit.get('id') in extras:
                if unit.get('data-answer-first')=='true':
                    explanation=next((el for el in unit if el.get('class')=='deep-block' and '学习解释' in el.xpath('./summary')[0].text_content()),None)
                    if explanation is not None:
                        explanation.xpath('./div[@class="block-body"]')[0].insert(0,figure(*extras[unit.get('id')]))
                else:
                    first=next((el for el in unit if el.get('class')=='lesson-block'),None)
                    unit.insert(unit.index(first)+1 if first is not None else len(unit),figure(*extras[unit.get('id')]))
    return units

def serialize(el):return html.tostring(el,encoding='unicode',method='html')

def page(units,homework=False):
    chapter_ids=list(dict.fromkeys(unit.get('data-chapter') for unit in units))
    chapter_nav=''.join(f'<a href="#{next(u.get('id') for u in units if u.get("data-chapter")==ch)}" data-chapter="{ch}">{esc.escape(CHAPTERS[ch][1])}</a>' for ch in chapter_ids)
    if homework:
        chapter_nav='<a href="communications-course-redraw.html">返回三章主线</a><a href="communications-course-redraw.html#ch5-00">先学第五章</a><a href="communications-ch5-ppt.html">原逐页伴读</a><a href="communications.html">通原目录</a>'
    unit_nav=''
    for ch in chapter_ids:
        links=''.join(f'<a href="#{u.get('id')}">{esc.escape(u.get("data-short"))}</a>' for u in units if u.get('data-chapter')==ch)
        unit_nav+=f'<nav class="unit-nav" data-chapter="{ch}" aria-label="{esc.escape(CHAPTERS[ch][0])}小节">{links}</nav>'
    title='第五章八题 · 边抄边学' if homework else '通原5—7章 · 先理顺，再算透'
    lede='第13、14、25题已按教材与PPT重新核对：先看原题和完整书面解答，学习解释可按需展开。其余五题保留从零讲解与分步解答。' if homework else '按完全没学过来读：先看图中的量，再认符号和单位，亲手算一小步，最后才归纳公式。一次只读一个单元，不以看完页面代替学会。'
    route_note='5.9.1、3、9、13、14、15、20、25。误差统一采用“输入−重建”；第14题与第15题的段内码规则不同。' if homework else '先进入“三章主线”，再按5 → 6 → 7学习。第五章作业可以同步做，不必等三章全部学完。'
    extra_control='<button type="button" id="show-all">展开全部题目</button>' if homework else ''
    body='\n'.join(serialize(unit) for unit in units)
    script_version='20261111-homework' if homework else '20261110b'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="通信原理第5至7章：从零梳理脉络、逐个解释概念、代表题、第二遍推导与第五章作业带做。"><title>{title}</title><link rel="stylesheet" href="communications-redraw.css?v=20261110"><script defer src="communications-redraw.js?v={script_version}"></script></head>
<body class="comm-page"><a class="skip" href="#lesson">跳到学习内容</a>
<header class="comm-header"><a class="comm-brand" href="communications.html">通信原理<small>5—7章 · 两遍辅导</small></a><nav aria-label="课程导航"><a href="communications.html">通原目录</a><a href="communications-ch5-homework.html">第五章作业</a><a href="courses.html">全部课程</a></nav></header>
<main class="comm-main"><section class="comm-intro"><p class="eyebrow">一条主线 · 先必学，再深挖</p><h1>{title}</h1><p class="lede">{lede}</p><p class="route-note">{route_note}</p></section>
<p class="start-note"><a href="communications-course-redraw.html#ch5-00">第一次学？从“一条电压曲线”开始 →</a></p>
<nav class="chapter-nav" aria-label="选择章节">{chapter_nav}</nav>{unit_nav}
<div class="workbar"><div class="pass-switch" role="group" aria-label="选择学习遍数"><button type="button" data-pass="first" aria-pressed="true">第一遍 · 从零学</button><button type="button" data-pass="deep" aria-pressed="false">第二遍 · 展开深挖</button></div><button id="open-contents" type="button" aria-haspopup="dialog">本节目录 ☷</button></div><p class="mode-hint" id="mode-hint">从本节起步逐段读，先做小检查再看答案；第二遍可按需展开。</p><p class="unit-lead" id="current-label" aria-live="polite"></p>{extra_control}
<div id="lesson">{body}</div><nav class="bottom-nav" aria-label="继续学习"><a id="previous-unit" href="#{units[0].get('id')}">上一节</a><a href="#">回到路线起点 ↑</a><a id="next-unit" href="#{units[-1].get('id')}">下一节</a></nav>
<aside class="record-note"><strong>原有伴读与记录保留。</strong>本页不修改原课件的完成标记、计时或本机学习记录。原页号与教材页号分开标注；新增讲解是按概念重排，不要求再通读旧版一遍。公式为原生MathML，图为同源SVG，无需外部数学库。</aside></main>
<footer class="comm-footer">原课件：通信原理A 第5章141页、第6章116页、第7章125页。作业：赵恒凯等《现代通信原理（第2版）》5.9节。<a href="communications-redraw/source-map.json">来源与范围</a></footer>
<dialog class="contents-dialog" id="contents-dialog" aria-labelledby="contents-title"><header><h2 id="contents-title">当前章目录</h2><button type="button" data-close-contents>关闭</button></header><nav id="contents-links" aria-label="跳到知识单元"></nav></dialog>
<dialog class="figure-dialog" id="figure-dialog" aria-labelledby="figure-title"><header><h2 id="figure-title">清晰大图</h2><button type="button" id="close-figure">关闭 ✕</button></header><div class="figure-controls" role="group" aria-label="大图缩放"><button type="button" id="zoom-out" aria-label="缩小大图">−</button><output id="zoom-value" aria-live="polite">100%</output><button type="button" id="zoom-in" aria-label="放大大图">＋</button><button type="button" id="zoom-fit">适合窗口</button><button type="button" id="zoom-readable">清晰尺寸</button><a id="open-figure-file" target="_blank" rel="noopener">单独打开 ↗</a></div><div id="figure-canvas" class="figure-canvas" tabindex="0" role="region" aria-label="大图，可横向与纵向滚动"><img id="figure-image" alt=""></div><figcaption id="figure-caption"></figcaption></dialog>
<noscript><p class="noscript">JavaScript未开启时，下方内容按顺序完整展示，第二遍仍可手动展开。目录链接与公式可直接阅读。</p></noscript></body></html>'''

course=[]
if (INPUT/'roadmap.md').exists():course+=make_units((INPUT/'roadmap.md').read_text(),'intro')
for n in [5,6,7]:
    file=INPUT/f'chapter{n}.md'
    if file.exists():course+=make_units(file.read_text(),f'ch{n}')
if course:(SITE/'communications-course-redraw.html').write_text(page(course),encoding='utf-8')
homework=[]
for name in ['homework-first.md','homework-last.md']:
    file=INPUT/name
    if file.exists():homework+=make_units(file.read_text(),'homework',True)
if homework:(SITE/'communications-ch5-homework.html').write_text(page(homework,True),encoding='utf-8')
metadata={'version':1,'updated':'2026-11-10','teachingOrder':'零基础起步→读图与符号→小步数值例→自行检查→课内公式；第二遍补推导','chapters':[{'chapter':n,'source':f'通信原理A_Chapt{n}.ppt','physicalPages':pages,'published':(INPUT/f'chapter{n}.md').exists()} for n,pages in [(5,141),(6,116),(7,125)]],'homework':{'textbook':'赵恒凯等《现代通信原理（第2版）》','ISBN':'978-7-302-54559-0','section':'5.9','questions':[1,3,9,13,14,15,20,25],'printedPages':[144,145,146,147],'pdfPages':[164,165,166,167],'scansPublished':False},'courseUnits':[{'id':u.get('id'),'chapter':u.get('data-chapter'),'title':u.xpath('.//h2')[0].text_content()} for u in course],'questionUnits':[u.get('id') for u in homework]}
(SITE/'communications-redraw/source-map.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'courseUnits':len(course),'homeworkQuestions':len(homework),'chapters':[n for n in [5,6,7] if (INPUT/f'chapter{n}.md').exists()]},ensure_ascii=False))
