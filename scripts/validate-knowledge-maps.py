#!/usr/bin/env python3
"""Standard-library deployment gate for graph schema, page coverage and asset identity."""
import hashlib,json,sys
from html.parser import HTMLParser
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,parse_qs,unquote
SITE=Path(__file__).resolve().parents[1]/'site'
class Reader(HTMLParser):
 def __init__(self):super().__init__();self.pages=[];self.scripts=[];self.styles=[];self.maps=[];self.map_script_indices=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='article' and 'slide-page' in a.get('class','').split():self.pages.append(int(a['data-page']))
  if tag=='script':
   self.scripts.append(a.get('src',''))
   if 'data-knowledge-map' in a:self.maps.append(a['data-knowledge-map']);self.map_script_indices.append(len(self.scripts)-1)
  if tag=='link' and a.get('rel')=='stylesheet':self.styles.append(a.get('href',''))
def resource(href):
 u=urlsplit(href);assert not u.scheme and not u.netloc, f'External resource: {href}'
 p=unquote(u.path);p=p[len('/study-site/'):] if p.startswith('/study-site/') else p
 assert not p.startswith('/'),href
 f=(SITE/p).resolve();assert f.is_relative_to(SITE.resolve()) and f.is_file(),f'Missing resource: {href}';return f
ASSET_SETS={
 'v1':{'scripts':['knowledge-map.js','knowledge-neighborhood.js'],
       'styles':['knowledge-map.css','knowledge-reader-shell.css','knowledge-neighborhood.css']},
 'v2':{'scripts':['knowledge-map-v2.js','knowledge-chapter-graph.js'],
       'styles':['knowledge-map.css','knowledge-reader-shell-v2.css','knowledge-chapter-graph.css']}
}
ASSET_NAMES={name for assets in ASSET_SETS.values() for names in assets.values() for name in names}
def asset_name(href):
 return PurePosixPath(unquote(urlsplit(href).path)).name
def check_assets(reader,chapter):
 names={kind:[asset_name(href) for href in getattr(reader,kind)] for kind in ['scripts','styles']}
 selected=[version for version,assets in ASSET_SETS.items()
           if all([name for name in names[kind] if name in ASSET_NAMES]==assets[kind]
                  for kind in ['scripts','styles'])]
 assert len(selected)==1,f'{chapter}: require one complete, ordered V1 or V2 asset set without duplicates or mixing'
 assets=ASSET_SETS[selected[0]]
 core_index=names['scripts'].index(assets['scripts'][0])
 assert reader.map_script_indices==[core_index],f'{chapter}: map URL must belong to the selected graph core script'
 viewer_indices=[i for i,name in enumerate(names['scripts']) if name.endswith('-viewer.js') or name=='companion-reader.js']
 # Some unchanged EM readers embed their viewer inline rather than loading a file.
 assert not viewer_indices or max(viewer_indices)<core_index,f'{chapter}: viewer must precede graph core'
 for href in reader.maps+[href for href in reader.scripts+reader.styles if asset_name(href) in ASSET_NAMES]:
  assert parse_qs(urlsplit(href).query).get('v')==[hashlib.sha256(resource(href).read_bytes()).hexdigest()[:12]],f'{chapter}: stale hash {href}'
 return selected[0]
def check():
 r=json.loads((SITE/'knowledge-map-registry.json').read_text(encoding='utf-8'));assert r['schemaVersion']==1
 seen=set()
 for row in r['maps']:
  chapter=row['chapterId'];assert chapter not in seen;seen.add(chapter)
  g=json.loads(resource(row['knowledgeMapPath']).read_text(encoding='utf-8'));assert g['version']==1 and g['id']==chapter
  p=Reader();p.feed(resource(row['readerPath']).read_text(encoding='utf-8'));pages=set(p.pages)
  assert len(pages)==len(p.pages)==row['readerPageCount'],f'{chapter}: page count'
  assert len(p.maps)==1 and resource(p.maps[0])==resource(row['knowledgeMapPath'])
  check_assets(p,chapter)
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
