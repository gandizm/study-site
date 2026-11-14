#!/usr/bin/env python3
"""Render the subject navigation, homework sections and identical homepages.

Add a new assignment to site/study-catalog.json and run this script. published_on
is the first publication of that assignment batch, NOT its latest correction.
Existing reader text, page IDs, controls, scripts and records are left intact.
"""
from pathlib import Path
from html import escape
from urllib.parse import urlsplit
import json, re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
CATALOG = json.loads((SITE / 'study-catalog.json').read_text())
SUBJECTS = CATALOG['subjects']
BASE = '/study-site/'
VERSION = '20261112'
NAV_START, NAV_END = '<!-- study-nav:start -->', '<!-- study-nav:end -->'
HW_START, HW_END = '<!-- study-homework:start -->', '<!-- study-homework:end -->'

def link(path):
    return escape(BASE + path, quote=True)

def subject_for(path):
    name = path.name
    if name.startswith('party-school'): return 'party-school'
    if name.startswith('network'): return 'network'
    if name.startswith('communications'): return 'communications'
    if name.startswith('data-structures'): return 'data-structures'
    if name.startswith('dsp') or path.parts[0].startswith('dsp'): return 'dsp'
    if name.startswith('em-') or re.match(r'ppt\d*\.html$', name): return 'em'
    return None

def is_preview(path):
    return ('preview' in str(path) or path.name in ['course-qa.html', 'math-layout-check.html'])

def navigation(path):
    current = subject_for(path)
    label = next((s['name'] for s in SUBJECTS if s['id'] == current), '选择科目')
    links = []
    for s in SUBJECTS:
        active = (' aria-current="page"' if path.as_posix() == s['url'] else ' aria-current="true"') if s['id'] == current else ''
        links.append(f'<a href="{link(s["url"])}"{active}>{escape(s["name"])}</a>')
    return (NAV_START + '\n<nav class="study-global-nav" aria-label="全站科目导航">'
            f'<a class="study-home" href="{BASE}courses.html">学习首页</a>'
            f'<details class="study-subject-menu" open><summary>科目 · {escape(label)}</summary>'
            '<div class="study-subject-links">' + ''.join(links) + '</div></details></nav>\n' + NAV_END)

def assignment_card(a, *, latest=False):
    s = next(s for s in SUBJECTS if s['id'] == a['subject'])
    extra = ''.join(f'<a class="secondary" href="{link(x["url"])}">{escape(x["label"])}</a>' for x in a.get('links', []))
    badge = f'<span class="study-badge">最新作业 · {escape(s["name"])}</span>' if latest else f'<span class="study-meta">{a["published_on"]} · 作业批次</span>'
    meta = f'<p class="study-meta">{a["published_on"]} 新增' + (f' · {a["updated_on"]} 更新' if a.get('updated_on') else '') + '</p>'
    cls = 'study-item study-latest' if latest else 'study-item'
    title_tag = 'h2' if latest else 'h3'
    return (f'<article class="{cls}" data-assignment="{escape(a["url"],quote=True)}"><div>{badge}'
            f'<{title_tag}>{escape(a["title"])}</{title_tag}><p>{escape(a["description"])}</p>'
            f'{meta if latest else ""}</div><div class="actions"><a class="primary" href="{link(a["url"])}">{escape(a["action"])}</a>{extra}</div></article>')

def homework(subject):
    items = sorted((a for a in CATALOG['assignments'] if a['subject'] == subject), key=lambda a: a['published_on'], reverse=True)
    out = '<section class="study-section" id="homework"><div class="study-section-heading"><h2>作业</h2><p>按作业批次排列，旧题保留在本科目</p></div>'
    if not items:
        out += '<p class="study-empty">目前没有独立的指定作业页。辅导中的代表例题与自测仍在对应章节，不把它们算成新作业。</p>'
    else:
        out += assignment_card(items[0])
        if len(items) > 1:
            out += f'<details class="study-archive"><summary>历史作业 · {len(items)-1} 份</summary><div class="study-grid">'
            out += ''.join(assignment_card(a) for a in items[1:]) + '</div></details>'
    return HW_START + '\n' + out + '</section>\n' + HW_END

def home():
    latest = max(CATALOG['assignments'], key=lambda a: (a['published_on'], a['url']))
    cards = []
    for i, s in enumerate(SUBJECTS, 1):
        cards.append(f'<section class="study-item" id="{s["id"]}-entry"><span class="study-number">{i:02d} / {s["label"]}</span>'
                     f'<h2>{s["name"]}</h2><p>{s["description"]}</p><p class="study-meta">{s["scope"]}</p>'
                     f'<div class="actions"><a class="primary" href="{link(s["url"])}">进入{s["name"]}</a></div></section>')
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>课程伴学 · 学习首页</title><link rel="stylesheet" href="/study-site/course-hub.css"></head><body>'
            '<main class="study-directory"><header class="study-hero"><p class="eyebrow">YOUR STUDY DESK · 按科目学习</p>'
            '<h1>先选科目，<br>再开始学习。</h1><p>作业、辅导和原课件都收在对应科目里。首页只保留最新一份作业，旧作业到科目内查找。</p></header>'
            '<section class="study-section" id="latest-homework" aria-label="最新作业">' + assignment_card(latest, latest=True) + '</section>'
            '<section class="study-section" id="subjects"><div class="study-section-heading"><h2>全部科目</h2><p>每门课，一个入口</p></div>'
            '<div class="study-grid">' + ''.join(cards) + '</div></section>'
            '<aside class="note">旧页面、原课件和阅读记录全部保留。翻页不会自动标记已读，计时仍由你手动开始。</aside>'
            '<footer><a href="/study-site/materials.html">材料来源与版本说明</a><p>只列实际可用的内容，不把预览页或未完成章节当成课程。</p></footer></main><script src="/study-site/phase2-preview.js"></script></body></html>\n')

HUB_URLS = {s['url'] for s in SUBJECTS} | {'index.html', 'courses.html', 'knowledge-maps.html', 'materials.html'}
ASSIGNMENT_URLS = {a['url'] for a in CATALOG['assignments']}

def simplify_old_navigation(text):
    def change(match):
        block = match.group(0)
        opening = block.split('>', 1)[0]
        global_candidate = any(x in opening for x in ['course-nav', 'course-links', 'hw-nav', 'toplinks', 'aria-label="课程切换"', 'aria-label="课程导航"', 'aria-label="网站导航"'])
        if not global_candidate: return block
        # A second course-nav in the original homework is its question TOC.
        if not re.search(r'href=["\'](?!#)', block): return block
        def keep_anchor(a):
            href = re.search(r'href=["\']([^"\']+)', a.group(0))
            if not href: return a.group(0)
            name = urlsplit(href.group(1)).path.rsplit('/', 1)[-1]
            return '' if name in HUB_URLS | ASSIGNMENT_URLS else a.group(0)
        block = re.sub(r'<a\b[^>]*>.*?</a>', keep_anchor, block, flags=re.S)
        if not re.search(r'<(?:a|button|select)\b', block): return ''
        block = re.sub(r' aria-label="[^"]*"', '', block, count=1)
        return block.replace('<nav', '<nav aria-label="本课阅读工具"', 1)
    return re.sub(r'<nav\b[^>]*>.*?</nav>', change, text, flags=re.S)

def install(path):
    rel = path.relative_to(SITE)
    text = path.read_text()
    # Two legacy information pages rely on HTML's implicit head/body elements.
    if not re.search(r'<body\b', text):
        text = re.sub(r'(<html\b[^>]*>)', r'\1<head>', text, count=1)
        text = text.replace('<main>', '</head><body><main>', 1)
        text = text.replace('</html>', '</body></html>', 1)
    text = re.sub(r'\n?' + re.escape(NAV_START) + r'.*?' + re.escape(NAV_END) + r'\n?', '', text, flags=re.S)
    text = re.sub(r'<link\b[^>]*href="/study-site/study-navigation\.css[^>]*>\n?', '', text)
    text = re.sub(r'<script\b[^>]*src="/study-site/study-navigation\.js[^>]*></script>\n?', '', text)
    text = simplify_old_navigation(text)
    text = re.sub(r'(?m)^[ \t]+$', '', text)
    text = text.replace('</head>', f'<link rel="stylesheet" href="{BASE}study-navigation.css?v={VERSION}">\n</head>', 1)
    text = re.sub(r'(<body\b[^>]*>)\s*', lambda m: m.group(1) + '\n' + navigation(rel) + '\n', text, count=1)
    text = text.replace('</body>', f'<script src="{BASE}study-navigation.js?v={VERSION}"></script>\n</body>', 1)
    path.write_text(text)

if __name__ == '__main__':
    homepage = home()
    for name in ['index.html', 'courses.html']:
        (SITE / name).write_text(homepage)
    for s in SUBJECTS:
        path = SITE / s['url']
        text = path.read_text()
        if HW_START not in text:
            raise SystemExit(f'Missing homework slot in {path}')
        text = re.sub(re.escape(HW_START) + r'.*?' + re.escape(HW_END), lambda m: homework(s['id']), text, flags=re.S)
        path.write_text(text)
    count = 0
    for path in sorted(SITE.rglob('*.html')):
        if not is_preview(path.relative_to(SITE)):
            install(path); count += 1
    print(f'Rendered two homepages, {len(SUBJECTS)} subject homework sections and {count} subject-only navigation bars.')
