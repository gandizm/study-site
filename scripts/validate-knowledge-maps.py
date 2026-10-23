#!/usr/bin/env python3
"""Standard-library deployment gate for graph schema, page coverage and asset identity."""
import hashlib,json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
SITE=Path(__file__).resolve().parents[1]/'site'
class Reader(HTMLParser):
 def __init__(self):super().__init__();self.pages=[];self.scripts=[];self.styles=[];self.maps=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='article' and 'slide-page' in a.get('class','').split():self.pages.append(int(a['data-page']))
  if tag=='script':
   self.scripts.append(a.get('src',''))
   if 'data-knowledge-map' in a:self.maps.append(a['data-knowledge-map'])
  if tag=='link' and a.get('rel')=='stylesheet':self.styles.append(a.get('href',''))
def resource(href):
 u=urlsplit(href);assert not u.scheme and not u.netloc, f'External resource: {href}'
 p=unquote(u.path);p=p[len('/study-site/'):] if p.startswith('/study-site/') else p
 assert not p.startswith('/'),href
 f=(SITE/p).resolve();assert f.is_relative_to(SITE.resolve()) and f.is_file(),f'Missing resource: {href}';return f
def check():
 r=json.loads((SITE/'knowledge-map-registry.json').read_text(encoding='utf-8'));assert r['schemaVersion']==1
 seen=set()
 for row in r['maps']:
  chapter=row['chapterId'];assert chapter not in seen;seen.add(chapter)
  g=json.loads(resource(row['knowledgeMapPath']).read_text(encoding='utf-8'));assert g['version']==1 and g['id']==chapter
  p=Reader();p.feed(resource(row['readerPath']).read_text(encoding='utf-8'));pages=set(p.pages)
  assert len(pages)==len(p.pages)==row['readerPageCount'],f'{chapter}: page count'
  assert len(p.maps)==1 and resource(p.maps[0])==resource(row['knowledgeMapPath'])
  for asset in ['knowledge-map.js','knowledge-neighborhood.js']:
   assert sum(asset in x for x in p.scripts)==1,f'{chapter}: script {asset}'
  for asset in ['knowledge-map.css','knowledge-neighborhood.css','knowledge-reader-shell.css']:
   assert sum(asset in x for x in p.styles)==1,f'{chapter}: style {asset}'
  assert next(i for i,x in enumerate(p.scripts) if 'knowledge-map.js' in x)<next(i for i,x in enumerate(p.scripts) if 'knowledge-neighborhood.js' in x)
  for href in p.maps+[x for x in p.scripts+p.styles if any(n in x for n in ['knowledge-map.','knowledge-neighborhood.','knowledge-reader-shell.'])]:
   assert parse_qs(urlsplit(href).query).get('v')==[hashlib.sha256(resource(href).read_bytes()).hexdigest()[:12]],f'{chapter}: stale hash {href}'
  nodes=g['nodes'];ids={n['id'] for n in nodes};assert nodes and len(ids)==len(nodes)==row['nodeCount']
  covered=set();deps={}
  for n in nodes:
   assert n.get('label') and n.get('summary'),f'{chapter}/{n["id"]}: concept explanation'
   refs=n['pages'];assert refs and len(refs)==len(set(refs));assert all(type(x)is int and x in pages for x in refs)
   covered.update(refs);deps[n['id']]=n.get('prerequisites',[]);assert all(x in ids and x!=n['id'] for x in deps[n['id']])
  assert covered==pages,f'{chapter}: uncovered {sorted(pages-covered)}'
  for e in g.get('edges',[]):assert e['from'] in ids and e['to'] in ids and e.get('label')
  active=set();done=set()
  def visit(n):
   assert n not in active,f'{chapter}: prerequisite cycle'
   if n in done:return
   active.add(n)
   for x in deps[n]:visit(x)
   active.remove(n);done.add(n)
  for n in ids:visit(n)
  print(f'PASS {chapter}: {len(nodes)} nodes; {len(pages)} real reader pages; assets and prerequisite DAG valid')
 assert seen,'Empty graph registry'
if __name__=='__main__':
 try:check()
 except (AssertionError,ValueError,KeyError,OSError) as e:print(f'FAIL {e}',file=sys.stderr);sys.exit(1)
