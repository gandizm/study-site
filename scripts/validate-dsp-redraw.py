#!/usr/bin/env python3
"""Check redraw coverage, local assets, controlled scope, and unchanged progress contracts."""
import json,re,sys,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';DATA=SITE/'dsp-redraw'
EXPECTED={'21':35,'22':24,'23':53,'24':11,'25':31,'26':31}
class Text(HTMLParser):
 def __init__(self):super().__init__();self.text=[];self.links=[];self.active=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  allowed=set('p div span strong em b i u small ul ol li table thead tbody tfoot tr th td caption h2 h3 h4 h5 h6 br hr a code pre sub sup blockquote details summary math mrow mi mn mo mtext mspace mfrac msqrt mroot msup msub msubsup munder mover munderover mtable mtr mtd mfenced mstyle menclose semantics annotation annotation-xml'.split())
  assert t in allowed, f'Unexpected HTML tag <{t}>; escape text comparisons with &lt;'
  assert t not in ('script','iframe','object','embed'),f'Active tag {t}'
  assert not any(k.lower().startswith('on') for k in a),'Inline event handler'
  for k in ('href','src'):
   if k in a:self.links.append(a[k])
 def handle_data(self,d):self.text.append(d)
def resource(url):
 u=urlsplit(url)
 assert not u.scheme and not u.netloc, f'Not a same-origin resource: {url}'
 if not u.path:return
 path=unquote(u.path).removeprefix('/study-site/')
 assert not path.startswith('/'),url
 f=(SITE/path).resolve();assert f.is_relative_to(SITE.resolve()) and f.is_file(),f'Missing: {url}'
def htmlcheck(s):
 p=Text();p.feed(s)
 for u in p.links:resource(u)
 assert not re.search(r'\\(?:frac|sum|begin|omega|mathrm)\b',' '.join(p.text)), 'Raw LaTeX shown as prose'
 return len(re.findall(r'[\u3400-\u9fff]',' '.join(p.text)))
def validate():
 total=0;mins=0
 for no,count in EXPECTED.items():
  p=DATA/f'ch2-{no}.json';d=json.loads(p.read_text());assert d['id']==f'dsp-{no}';assert d['source']['pageCount']==count
  assert d.get('title') and d.get('brief');assert 0<d['firstPassMinutes']<=35
  mins+=d['firstPassMinutes'];cards=d['cards'];ids=[c['id'] for c in cards];assert len(ids)==len(set(ids)) and ids
  words=0
  for c in cards:
   assert c['level'] in ('essential','deep');assert c.get('title');assert c.get('bodyHtml')
   n=htmlcheck(c['bodyHtml']);words+=n if c['level']=='essential' else 0
   assert all(type(x)==int and 1<=x<=count for x in c['sourcePages'])
   for f in c.get('figures', ([c['figure']] if c.get('figure') else [])):
    assert f.get('alt');resource(f['src'])
    if f['src'].endswith('.svg'):
     svg=ET.parse(SITE/f['src'].removeprefix('/study-site/')).getroot();assert svg.get('viewBox'),f['src']
   if c.get('check'):htmlcheck(c['check'].get('answerHtml',''))
  if d.get('example'):ids.append('representative-example')
  pages=d['pageMap'];assert sorted(x['page'] for x in pages)==list(range(1,count+1)),f'{no}: must map every source page exactly once'
  for row in pages:
   assert row.get('cardIds') or row.get('note'),f'{no} P{row["page"]}: unexplained empty mapping'
   assert all(x in ids for x in row.get('cardIds',[])),f'{no}: unknown card'
  example=d.get('example');assert example,f'{no}: one representative example required'
  for k in ('problemHtml','stepsHtml','answerHtml','checkHtml'):
   assert example.get(k),f'{no}: incomplete example {k}';words+=htmlcheck(example[k])
  assert len(d.get('pitfalls',[]))>=2
  for x in d.get('deepLinks',[]):resource(x['href'])
  for k in ('readerUrl',):
   if d['source'].get(k):resource(d['source'][k])
  print(f'PASS 2.{no[-1]}: {count}/{count} source pages; {len(cards)} cards ({sum(c["level"]=="essential" for c in cards)} essential); first pass ~{words} Chinese characters + formulas; estimated {d["firstPassMinutes"]} min')
  assert words<=2600,f'{no}: first-pass prose exceeds controlled budget ({words})'
  total+=count
 assert total==185
 assert mins<=150,f'First-pass planning estimate too large: {mins}'
 assert not re.search(r'localStorage\.(?:setItem|removeItem|clear)\s*\(', (SITE/'dsp-redraw.js').read_text()),'New reader must not modify old reading records'
 print(f'PASS total: {total} source pages; first-pass estimate {mins} min (not measured); no new progress writes')
if __name__=='__main__':validate()
