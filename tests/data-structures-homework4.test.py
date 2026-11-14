#!/usr/bin/env python3
"""Numerical, tree-structure, SVG, source, link, and isolated-content regression checks."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import json, heapq, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
f=json.loads((ROOT/'tests/data-structures-homework4-fixtures.json').read_text())

# Independent complete-tree child enumeration, including odd/even boundary cases.
for n in range(1,2002):
    counts=Counter(int(2*i<=n)+int(2*i+1<=n) for i in range(1,n+1))
    assert counts[0]==(n+1)//2
    assert counts[2]==(n-1)//2
    assert counts[1]==int(n%2==0)
    assert counts[0]==counts[2]+1
c=f['complete']; assert c=={'n':1001,'n0':501,'n1':0,'n2':500}

# Reconstruct without using the authored answer tree, then compare every child.
t=f['traversal']; rebuilt={}
def reconstruct(ino,post):
    if not ino: assert not post; return None
    assert len(ino)==len(post) and set(ino)==set(post)
    root=post[-1]; k=ino.index(root)
    left=reconstruct(ino[:k],post[:k]);right=reconstruct(ino[k+1:],post[k:-1])
    rebuilt[root]=[left,right];return root
assert reconstruct(t['inorder'],t['postorder'])==t['root']
assert rebuilt==t['children']
def visit(root,order):
    if root is None:return ''
    left,right=rebuilt[root];parts={'N':root,'L':visit(left,order),'R':visit(right,order)}
    return ''.join(parts[x] for x in order)
assert visit('A','NLR')==t['preorder']=='ABCDEFGH'
assert visit('A','LNR')=='BDCEAFHG'
assert visit('A','LRN')=='DECBHGFA'

# Authored Huffman tree: correct weights, exactly original leaves, and all paths.
h=f['huffman'];w=h['weights'];children=h['children'];depths={}
def inspect(node,depth=0):
    if node not in children:depths[node]=depth;return w[node]
    kids=children[node];assert len(kids)==2
    assert inspect(kids[0],depth+1)+inspect(kids[1],depth+1)==w[node]
    return w[node]
assert inspect(h['root'])==sum(w[x] for x in h['original_leaves'])==41
assert set(depths)==set(h['original_leaves'])
assert depths=={'17':1,'2a':4,'2b':4,'5':3,'3':4,'4':4,'8':3}
assert len(children)==6 and len(w)==13
assert sum(w[x]*depth for x,depth in depths.items())==h['wpl']==100
heap=[8,2,5,3,2,17,4];heapq.heapify(heap);merges=[]
while len(heap)>1:
    a=heapq.heappop(heap);b=heapq.heappop(heap);merges.append(a+b);heapq.heappush(heap,a+b)
assert merges==h['merge_sums']==[4,7,9,15,24,41]
assert sum(merges)==100
assert 17+8*3+5*3+4*3+3*4+2*5+2*5==100 # Tie alternative described in text.

# SVG edges must be the exact mathematical trees, not merely plausible pictures.
ns={'s':'http://www.w3.org/2000/svg'}
for name,model in [('traversal',t['children']),('huffman',children)]:
    svg=ET.fromstring((SITE/f'assets/data-structures-homework4/{name}-tree.svg').read_text())
    assert svg.find('s:title',ns) is not None and svg.find('s:desc',ns) is not None
    expected={(p,c,s) for p,kids in model.items() for c,s in zip(kids,['左','右']) if c}
    actual={(e.attrib['data-parent'],e.attrib['data-child'],e.attrib['data-side']) for e in svg.findall('s:path',ns)}
    assert actual==expected
    nodes=[e.attrib['data-node'] for e in svg.findall('s:g',ns)]
    assert len(nodes)==len(set(nodes))==(8 if name=='traversal' else 13)
    assert set(nodes)==(set(t['children']) if name=='traversal' else set(w))
ET.fromstring((SITE/'assets/data-structures-homework4/complete-tree-boundary.svg').read_text())

class Page(HTMLParser):
    def __init__(self,text):super().__init__();self.ids=[];self.refs=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        for key in ['src','href']:
            if key in a:self.refs.append(a[key])

for name in ['data-structures-homework4.html','data-structures-homework4-answers.html']:
    text=(SITE/name).read_text();p=Page(text)
    assert len(p.ids)==len(set(p.ids)),f'Duplicate ID in {name}'
    assert all(x in p.ids for x in ['main','q1','q2','q3'])
    for ref in p.refs:
        u=urlsplit(ref)
        assert not u.scheme and not u.netloc, f'Unexpected external dependency: {ref}'
        if not u.path:
            if u.fragment:assert unquote(u.fragment) in p.ids,ref
            continue
        assert u.path.startswith('/study-site/'),ref
        target=SITE/unquote(u.path.removeprefix('/study-site/'))
        assert target.exists(),f'Missing target: {name} -> {ref}'
    for answer in ['501','500','ABCDEFGH','BDCEAFHG','DECBHGFA','100','41']:
        assert answer in text
    assert '未向课程平台提交' in text or '不连接或提交课程平台' in text
    assert 'data-structures-homework4.js' in text
lesson=(SITE/'data-structures-homework4.html').read_text()
assert all(x in lesson for x in ['copy-q1','copy-q2','copy-q3','traversal-player','traversal-order'])
assert '不能去重' in lesson and '路径长度' in lesson and '490 + 11 = 501' in lesson
js=(SITE/'data-structures-homework4.js').read_text()
for forbidden in ['localStorage','sessionStorage','indexedDB','fetch(','XMLHttpRequest','sendBeacon','innerHTML']:
    assert forbidden not in js,forbidden
for order in ['ABCDEFGH','BDCEAFHG','DECBHGFA']:assert order in js
assert 'min-width:0' in (SITE/'data-structures-homework4.css').read_text()
assert 'break-before:page' in (SITE/'data-structures-homework4.css').read_text()
print('PASS: 2001 complete-tree cases; exact reconstructed tree and traversals; Huffman optimum/leaf depths/tie alternative; 3 SVGs; new-page links, IDs, copy targets and privacy isolation.')
