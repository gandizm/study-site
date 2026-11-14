"""Numerical physics, original-source hashes, and static publication contract."""
from pathlib import Path
from html.parser import HTMLParser
from math import sqrt, pi, cos, sin, isclose
import hashlib, re, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; SITE=ROOT/'site'
class Page(HTMLParser):
    def __init__(self,s):
        super().__init__();self.ids=[];self.math=[];self.details=[];self.refs=[];self.svg=0;self.text=[];self.feed(s)
    def handle_data(self,s):self.text.append(s)
    def handle_starttag(self,t,a):
        d=dict(a)
        if 'id' in d:self.ids.append(d['id'])
        if 'data-tex' in d:self.math.append(d)
        if t=='details':self.details.append(d)
        if t=='svg':self.svg+=1
        for key in ['href','src']:
            if key in d:self.refs.append(d[key])
text=(SITE/'em-energy-wedge-homework.html').read_text(); p=Page(text)
assert len(p.math)==354 and p.svg>=354
assert all(m.get('role')=='math' and m.get('aria-label')==m['data-tex'] for m in p.math)
assert len(p.ids)==len(set(p.ids))
assert all(i in p.ids for i in ['q251','q363','q251-answer','q363-answer','emAskDialog','emExpand','emCollapse'])
assert len(p.details)==15 # 14 teaching folds plus shared navigation.
assert all('open' not in d for d in p.details if 'study-subject-menu' not in d.get('class',''))
assert not any(x in text for x in ['EMMATHPLACEHOLDER','data-mml-node="merror"','/workspace/','source/363','localhost','直角劈'])
assert not re.search(r'<(?:p|li|h[1-6])[^>]*>[^<]*\\[\[(]',text)
assert not any(re.search(r'^\s*#{1,6} |\*\*',s) for s in p.text)
assert '60°' in text and '点电荷' in text and '除真实点电荷位置外' in text
for ref in p.refs:
    if ref.startswith('/study-site/'):
        relative=ref.removeprefix('/study-site/').split('?')[0].split('#')[0]
        assert (SITE/relative).exists(),ref
    if ref.startswith('assets/'):
        assert (SITE/ref).exists(),ref
for name,expected in {
 'original-2-5-1.png':'937dbbe6bb4c1ee894b0b04a371d47f883701910dcd691051bac50354921fe88',
 'original-3-6-3.png':'de86be19cf16b046ba9edddf1512f13cb85a2acfa9f1bc27effd788b0216611a',
 'figure-3-6-3b.png':'ccca738345fc20415e4599677e332862ab6668daebd2da3edf4764fd97044daf'
}.items():assert hashlib.sha256((SITE/'assets/em-energy-wedge'/name).read_bytes()).hexdigest()==expected
for name in ['energy-flow.svg','image-charges.svg']:
    ET.parse(SITE/'assets/em-energy-wedge'/name)
for chapter,pages in [(2,[47,48,49,51]),(3,[5,6,11,12,13])]:
    source=(SITE/f'ppt{chapter}.html').read_text()
    for n in pages:assert f'id="p{n:02}"' in source or f'id="p{n}"' in source
# Q251: side flux, local Joule loss, and equivalent circuit must agree.
for a,d,sigma,u in [(2,.01,3,7),(.8,.0002,.01,150),(1,.02,0,5),(1,.01,2,-4)]:
    E=u/d; J=sigma*E; total=sigma*pi*a*a*u*u/d
    for rho in [a/100,a/4,a/2,a]:
        H=J*rho/2; Sr=-E*H
        assert isclose(-Sr*2*pi*rho*d,sigma*E*E*pi*rho*rho*d,rel_tol=1e-12,abs_tol=1e-12)
    assert isclose(u*J*pi*a*a,total,rel_tol=1e-12,abs_tol=1e-12)
    if sigma:assert isclose(u*u/(d/(sigma*pi*a*a)),total,rel_tol=1e-12)
# Q363: all five image points lie outside the physical wedge; pair cancellation on both faces.
a=(sqrt(3)-1)/2;b=(sqrt(3)+1)/2
charges=[(1,1,1),(a,b,-1),(-b,a,1),(-b,-a,-1),(a,-b,1),(1,-1,-1)]
assert sum(x>0 and 0<y<sqrt(3)*x for x,y,s in charges)==1
def kernel(x,y,z=0):return sum(s/sqrt((x-xi)**2+(y-yi)**2+z*z) for xi,yi,s in charges)
for angle in [0,pi/3]:
    for r in [0,.1,.5,1,2,4,10]:
        for z in [0,.8,-2]:assert abs(kernel(r*cos(angle),r*sin(angle),z))<2e-14
assert isclose(kernel(2,1),.3200314700267503,rel_tol=1e-13)
assert isclose(kernel(2,1)*4.5e-8*8.9875517923e9,129.43347350525,rel_tol=1e-9)
js=(SITE/'em-energy-wedge.js').read_text()
assert not any(x in js for x in ['localStorage','sessionStorage','indexedDB','fetch(','XMLHttpRequest','window.open'])
print('PASS: 354 accessible static SVG formulas; 14 collapsed teaching sections; 3 exact original crops; source anchors; Q251 power checks; Q363 image geometry, 42 boundary samples and numeric potential; no progress writes.')
