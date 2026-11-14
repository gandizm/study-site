"""Subject taxonomy, newest-assignment policy, links, and preserved reader controls."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, importlib.util

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
spec = importlib.util.spec_from_file_location('navigation', ROOT/'scripts/build-study-navigation.py')
nav = importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
catalog = json.loads((SITE/'study-catalog.json').read_text())
subjects = catalog['subjects']; assignments = catalog['assignments']

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.refs=[]; self.ids=[]; self.globals=0; self.active=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
        if tag=='nav' and a.get('class')=='study-global-nav': self.globals+=1
        for key in ['href','src']:
            if a.get(key):self.refs.append(a[key])
        if tag=='a' and a.get('aria-current'):self.active.append(a.get('href'))

pages={p:Page(p.read_text()) for p in SITE.rglob('*.html')}
official={p:a for p,a in pages.items() if not nav.is_preview(p.relative_to(SITE))}
for p,a in official.items():
    assert a.globals==1, f'Expected one global navigation: {p}'
    text=p.read_text()
    for s in subjects: assert nav.link(s['url']) in text
    subject=nav.subject_for(p.relative_to(SITE))
    if subject:
        expected='/study-site/'+next(s['url'] for s in subjects if s['id']==subject)
        assert expected in a.active, f'Wrong active subject: {p}'
    for ref in a.refs:
        u=urlsplit(ref)
        if u.scheme or u.netloc or not u.path:continue
        if u.path.startswith('/study-site/'):
            target=SITE/unquote(u.path.removeprefix('/study-site/'))
        elif u.path.startswith('/'):continue
        else:target=p.parent/unquote(u.path)
        assert target.exists(),f'Missing target {ref} from {p}'

assert (SITE/'index.html').read_bytes()==(SITE/'courses.html').read_bytes()
latest=max(assignments,key=lambda a:(a['published_on'],a['url']))
for name in ['index.html','courses.html']:
    text=(SITE/name).read_text(); a=pages[SITE/name]
    hw=[x for x in assignments if '/study-site/'+x['url'] in a.refs]
    assert hw==[latest], f'Homepage must show only the latest assignment: {name}'
    assert text.count('data-assignment=')==1
    assert '/study-site/phase2-preview.js' in text
    for s in subjects:assert f'id="{s["id"]}-entry"' in text
for s in subjects:
    p=SITE/s['url'];a=pages[p]
    assert all(i in a.ids for i in ['homework','learning','reference'])
    for hw in assignments:
        if hw['subject']==s['id']:assert '/study-site/'+hw['url'] in a.refs

# New UI is presentation-only and must not access any learning storage or service.
js=(SITE/'study-navigation.js').read_text()
assert not any(x in js for x in ['localStorage','sessionStorage','indexedDB','fetch(','XMLHttpRequest'])
assert "url.searchParams.set('preview', '1')" in js
assert "anchor.getAttribute('href').startsWith('#')" in js
for p,a in official.items():
    if 'ppt' in p.name and p.name!='ppt.html' and 'id="pageSelect"' in p.read_text():
        assert all(x in a.ids for x in ['pageSelect','prev','next']),f'Lost reader controls: {p}'
for name,count in [('ppt.html',7),('dsp.html',2),('communications.html',1),('network.html',1)]:
    text=(SITE/name).read_text()
    if name=='ppt.html':
        # Original EM progress maps .card by index; homework cards must not join it.
        assert text.count('class="card"')==count
    else:assert text.count('data-course-progress')==count
assert 'id="openLearningPath"' in (SITE/'dsp-21-ppt.html').read_text()
assert 'id="openLearningPath"' in (SITE/'dsp-22-ppt.html').read_text()
print(f'PASS: {len(official)} pages, {len(subjects)} subject hubs, {len(assignments)} homework batches, latest-only homepages, all local href/src targets, reader controls and progress bindings.')
