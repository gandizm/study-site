"""Standard-library-only checks for the data-structures source reader and homework."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,re,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'
class Parse(HTMLParser):
 def __init__(self,text):
  super().__init__();self.ids=[];self.refs=[];self.images=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  for k in ['href','src']:
   if k in a:self.refs.append(a[k])
  if tag=='img':self.images.append(a)

sources=json.loads((SITE/'data-structures-source-map.json').read_text())['chapters']
assert len(sources)==8 and sum(c['pdf_pages'] for c in sources)==69
for c in sources:
 pdf=SITE/c['source_pdf']
 assert pdf.stat().st_size==c['bytes']
 assert hashlib.sha256(pdf.read_bytes()).hexdigest()==c['sha256']
 assert len(c['page_images'])==c['pdf_pages']
 for p in c['page_images']:assert (SITE/p).is_file()
 reader=Parse((SITE/c['reader']).read_text())
 for i in range(1,c['pdf_pages']+1):assert f'p{i:02}' in reader.ids

pages=list(SITE.glob('data-structures*.html'))
for path in pages:
 text=path.read_text();p=Parse(text)
 assert len(p.ids)==len(set(p.ids)),f'duplicate IDs: {path}'
 assert 'name="viewport"' in text
 assert not any(x in text for x in ['/workspace/','libfile_','Sentinel_'])
 for i in p.images:assert i.get('alt'),f'missing alt in {path}'
 for ref in p.refs:
  url=urlsplit(ref)
  if url.scheme or not url.path and not url.fragment:continue
  target=path if not url.path else SITE/url.path.removeprefix('/study-site/')
  assert target.exists(),f'missing target {ref} in {path}'
  if url.fragment and target.suffix=='.html':
   assert unquote(url.fragment) in Parse(target.read_text()).ids,f'missing fragment {ref}'
for name in ['data-structures-homework3.html','data-structures-homework3-answers.html']:
 p=Parse((SITE/name).read_text());assert all(f'q{i}' in p.ids for i in range(1,5))
for name in ['index.html','courses.html']:
 assert 'id="data-structures-entry"' in (SITE/name).read_text()
assert (SITE/'index.html').read_bytes()==(SITE/'courses.html').read_bytes()
svgs=list((SITE/'assets/data-structures-homework3').rglob('*.svg'))
assert len(svgs)==9
for s in svgs:ET.parse(s)

# Independently derive the queue states and address result.
f=r=1;arr=[None]*11;expected=[(1,6),(3,6),(3,0),(4,0),(4,3)]
for stage,(action,items) in enumerate([('in','debgh'),('out','de'),('in','ijklm'),('out','b'),('in','nopqr')]):
 for x in items:
  if action=='in':
   if (r+1)%11!=f:arr[r]=x;r=(r+1)%11
  else:assert arr[f]==x;arr[f]=None;f=(f+1)%11
 assert (f,r)==expected[stage]
assert (r-f+11)%11==10
m=(1115-1110)+1;base=1110-m-2
assert m==6 and base==1102 and base+3*m==1120
assert 1-(1115-1110)==-4

fixtures=json.loads((ROOT/'tests/data-structures-fixtures.json').read_text())
assert [(s['front'],s['rear']) for s in fixtures['q1'][1:]]==expected
assert ' '.join(fixtures['q2']['postfix'])=='A B C * D / - E F ** +'
assert len(fixtures['q2']['steps'])==18 and len(fixtures['q2']['reductions'])==5
ns=[];os=['#'];snapshots=[([],['#'])];precedence={'#':-1,'+':1,'-':1,'*':2,'/':2,'**':3};counter=0
for tok in ['A','-','B','*','C','/','D','+','E','**','F','#']:
 if tok.isalpha():ns.append(tok);snapshots.append((ns.copy(),os.copy()));continue
 while os[-1]!='#' and precedence[os[-1]]>=precedence[tok]:
  op=os.pop();right=ns.pop();left=ns.pop();counter+=1;ns.append('T'+str(counter));snapshots.append((ns.copy(),os.copy()))
 if tok=='#':snapshots.append((ns.copy(),os.copy()));break
 os.append(tok);snapshots.append((ns.copy(),os.copy()))
assert snapshots==[(s['NS'],s['OS']) for s in fixtures['q2']['steps']]
for key,want_num,want_cpot in [('A',[3,2,1,0,1,1],[1,4,6,7,7,8]),('B',[3,3,2,2,1,1,1,1,3],[1,4,7,9,11,12,13,14,15])]:
 d=fixtures['q4'][key];a=d['matrix'];triples=[(i+1,j+1,v) for i,row in enumerate(a) for j,v in enumerate(row) if v]
 num=[sum(v!=0 for v in row) for row in a];cpot=[1]
 for count in num[:-1]:cpot.append(cpot[-1]+count)
 assert num==want_num and cpot==want_cpot and len(triples)==d['tu']
 assert list(map(list,triples))==d['triples'] and num==d['num'] and cpot==d['cpot']
 rebuilt=[[0]*len(a[0]) for _ in a]
 for i,j,v in triples:rebuilt[i-1][j-1]=v
 assert rebuilt==a
print(f'PASS: {len(pages)} pages, 8 exact PDFs, 69 original-page images, {len(svgs)} SVG diagrams, local links/anchors, queue/address/matrix math.')
