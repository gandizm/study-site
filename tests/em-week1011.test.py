"""Static mathematical publication, exact boundary checks and phasor conventions."""
from pathlib import Path
from html.parser import HTMLParser
from math import pi,sin,cos,sinh,cosh,log,isclose,sqrt
import cmath,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]; S=R/'site'
IDS=['q372','q373','q514','q521','q532','q534']
class Page(HTMLParser):
 def __init__(self,t):super().__init__();self.ids=[];self.math=[];self.svg=0;self.text=[];self.details=[];self.feed(t)
 def handle_starttag(self,t,a):
  a=dict(a)
  if 'id' in a:self.ids.append(a['id'])
  if 'data-tex' in a:self.math.append(a)
  if t=='svg':self.svg+=1
  if t=='details':self.details.append(a)
 def handle_data(self,t):self.text.append(t)
for f in ['em-week1011-homework.html','em-week1011-answers.html']:
 t=(S/f).read_text();p=Page(t)
 assert all(q in p.ids and q+'-answer' in p.ids for q in IDS)
 assert len(p.ids)==len(set(p.ids)),f
 assert len(p.math)==(375 if f.endswith('homework.html') else 84) and p.svg>=len(p.math)
 assert all(a['role']=='math' and a['aria-label']==a['data-tex'] for a in p.math)
 assert not any(w in t for w in ['EMMATHPLACEHOLDER','data-mml-node="merror"','/tmp/','/workspace/','localhost','chatgpt.com/api/library','drive.google.com'])
 assert not any(re.search(r'^\s*#{1,6} |\*\*',v) for v in p.text)
 assert not any(re.search(r'\\(?:mathbf|boldsymbol|vec)\b',a['data-tex']) for a in p.math)
 assert '9787302389484' in t and '有效值' in t and '最大值' in t
 assert not re.search(r'<(?:p|li|h[1-6])[^>]*>[^<]*\\[\[(]',t)
 if f.endswith('homework.html'):
  assert len(p.details)>=15
  assert all('open' not in d for d in p.details if 'study-subject-menu' not in d.get('class',''))
for q in IDS:assert (R/f'docs/em-week1011/{q}.md').exists()
for q in ['q372','q373']:ET.parse(S/f'assets/em-week1011/{q}-boundary.svg')
assert not list((S/'assets/em-week1011').glob('*.png')),'Do not publish textbook scans'
# Triangular boundary Fourier coefficients, including its half-height peak.
b=1.7;u=2.4
for n in range(1,12):
 N=8000;h=b/N
 integ=sum((u*y/b if y<=b/2 else u*(1-y/b))*sin(n*pi*y/b)*h for y in ((i+.5)*h for i in range(N)))
 assert abs(2*integ/b-4*u*sin(n*pi/2)/(n*n*pi*pi))<2e-8
for y in [0,b/8,b/3,b/2,3*b/4,b]:
 v=sum(4*u*sin(n*pi/2)*sin(n*pi*y/b)/(n*n*pi*pi) for n in range(1,2000,2))
 expected=u*min(y/b,1-y/b)
 assert abs(v-expected)<0.00025
# Mixed boundary: exact solution and outward-from-conductor surface-charge sign.
a=.8;b=1.3;u=4;k=3*pi/(2*b)
def phi(x,y):return u*sinh(k*x)*sin(k*y)/sinh(k*a)
for x in [.01,.3,.7]:
 assert abs(phi(x,0))<1e-13
 assert abs(u*k*sinh(k*x)*cos(k*b)/sinh(k*a))<1e-13
 h=1e-4;y=.4
 lap=(phi(x+h,y)+phi(x-h,y)+phi(x,y+h)+phi(x,y-h)-4*phi(x,y))/h**2
 assert abs(lap)<2e-6
 assert -k*u*sinh(k*x)/sinh(k*a)<0
for y in [.01,.2,.7,1.2]:assert isclose(phi(a,y),u*sin(k*y),abs_tol=1e-12)
# Four phasor conversions, tested at non-special angles.
for t in [.17,.6,1.5,3.2]:
 z=.43;E=2.;H=1.3;theta=.62
 assert isclose((-1j*E*cmath.exp(-1j*z)*cmath.exp(1j*t)).real,E*sin(t-z),abs_tol=1e-12)
 assert isclose((E*(3*sqrt(3)/2+.5j)*cmath.exp(1j*t)).real,E*sin(t)+3*E*cos(t+pi/6),abs_tol=1e-12)
 assert isclose((1j*cmath.exp(1j*(t-z))).real,-sin(t-z),abs_tol=1e-12)
 assert isclose((-1j*H*cmath.exp(1j*(t-z*sin(theta)))).real,H*sin(t-z*sin(theta)),abs_tol=1e-12)
# Direct time averages: peak factors are 1/2, RMS factors are 1.
N=4000
assert isclose(sum(sin(2*pi*i/N-.7)**2 for i in range(N))/N,.5,abs_tol=1e-12)
assert isclose(sum(2*cos(2*pi*i/N+pi/6)**2 for i in range(N))/N,1,abs_tol=1e-12)
U=2*cmath.exp(.8j);I=3*cmath.exp(-.4j);target=U*I.conjugate()/2
assert isclose(target.real,3*cos(1.2),abs_tol=1e-12)
a=.3;b=1.7;h=(b-a)/20000
flux=sum(U*I.conjugate()/(2*log(b/a)*(a+(i+.5)*h))*h for i in range(20000))
assert abs(flux-target)<1e-8
js=(S/'em-week1011.js').read_text()
assert not any(x in js for x in ['localStorage','sessionStorage','indexedDB','fetch(','XMLHttpRequest','window.open'])
assert (S/'em-week1011-answers.txt').read_text().count('【')==6
print('PASS: six sourced solutions, accessible static SVGs, original diagrams, both boundary-value checks, four phasor conversions, peak/RMS and complex-power checks, no scans or progress writes.')
