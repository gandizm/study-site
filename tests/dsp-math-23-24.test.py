#!/usr/bin/env python3
"""Numerical invariants and published SVG data for DSP 2.3/2.4; standard library only."""
from pathlib import Path
import json,math,cmath,random,xml.etree.ElementTree as ET,unittest
ROOT=Path(__file__).resolve().parents[1]
def dft(x):
 N=len(x);return [sum(v*cmath.exp(-2j*math.pi*k*n/N) for n,v in enumerate(x)) for k in range(N)]
def idft(X):
 N=len(X);return [sum(v*cmath.exp(2j*math.pi*k*n/N) for k,v in enumerate(X))/N for n in range(N)]
def circ(x,y):
 N=len(x);assert len(y)==N
 return [sum(x[m]*y[(n-m)%N] for m in range(N)) for n in range(N)]
def lin(x,y):return [sum(x[m]*y[n-m] for m in range(len(x)) if 0<=n-m<len(y)) for n in range(len(x)+len(y)-1)]
def fold(x,N):return [sum(x[n] for n in range(k,len(x),N)) for k in range(N)]
def svg_data(name):
 root=ET.parse(ROOT/'site/dsp-redraw/assets'/f'{name}.svg').getroot()
 return json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
class MathAndAssets(unittest.TestCase):
 def close(self,x,y):
  self.assertEqual(len(x),len(y))
  for a,b in zip(x,y):self.assertLess(abs(a-b),1e-10)
 def test_inverse_and_parseval(self):
  rng=random.Random(20261030)
  for N in (3,4,5,6,8,16):
   x=[complex(rng.random(),rng.random()) for _ in range(N)];X=dft(x)
   self.close(idft(X),x);self.assertAlmostEqual(sum(abs(v)**2 for v in x),sum(abs(v)**2 for v in X)/N,places=10)
 def test_shift_signs(self):
  x=[2,1,3,1,.5];N=len(x);X=dft(x)
  for m in (1,-2):self.close(dft([x[(n+m)%N] for n in range(N)]),[v*cmath.exp(2j*math.pi*k*m/N) for k,v in enumerate(X)])
 def test_frequency_shift(self):
  x=[1,0,0,0,0,2,0,0,0,0];X=dft(x)
  self.close(dft([v*cmath.exp(-2j*math.pi*3*n/10) for n,v in enumerate(x)]),[X[(k+3)%10] for k in range(10)])
  self.close(dft(x),[3,-1]*5)
 def test_convolution_theorems(self):
  x=[1,2j,3,4];y=[2,1,-1j,3];X=dft(x);Y=dft(y)
  self.close(idft([a*b for a,b in zip(X,Y)]),circ(x,y))
  self.close(dft([a*b for a,b in zip(x,y)]),[v/4 for v in circ(X,Y)])
 def test_original_classroom_example(self):
  x=[1,2,2,1];a=lin(x,x);self.close(a,[1,4,8,10,8,4,1])
  answers={4:[9,8,9,10],6:[2,4,8,10,8,4],7:a,8:a+[0]}
  for N,ans in answers.items():self.close(circ(x+[0]*(N-4),x+[0]*(N-4)),ans);self.close(fold(a,N),ans)
  data=svg_data('23-convolution-fold');self.close(data['linear'],a);self.close(data['circular4'],answers[4])
 def test_rectangle_spectrum_graphs(self):
  data=svg_data('23-rectangle-samples');a=dft([1]*4+[0]*4);b=dft([1]*4+[0]*12)
  self.close(b[::2],a)
  for N in (8,16):self.close(data['magnitudes'][str(N)],[abs(v) for v in dft([1]*4+[0]*(N-4))])
  self.close(a,[4,1-1j*(1+math.sqrt(2)),0,1-1j*(math.sqrt(2)-1),0,1+1j*(math.sqrt(2)-1),0,1+1j*(1+math.sqrt(2))])
 def test_shift_graph(self):
  d=svg_data('23-circular-shift');x=d['original'];self.close(d['left1'],x[1:]+x[:1]);self.close(d['right2'],x[-2:]+x[:-2])
 def test_conjugate_and_symmetry(self):
  x=[1,2j,3,1-1j];N=4;X=dft(x)
  self.close(dft([v.conjugate() if isinstance(v,complex) else v for v in x]),[X[-k%N].conjugate() for k in range(N)])
  ep=[(x[n]+complex(x[-n%N]).conjugate())/2 for n in range(N)];op=[(x[n]-complex(x[-n%N]).conjugate())/2 for n in range(N)]
  self.close(dft(ep),[v.real for v in X]);self.close(dft(op),[1j*v.imag for v in X])
  d=svg_data('23-real-symmetry');self.close(dft(d['input']),[complex(*v) for v in d['dft']])
 def test_two_real_sequence_separation(self):
  N=32;x=[.8**n for n in range(N)];y=[.6**n for n in range(N)];F=dft([a+1j*b for a,b in zip(x,y)])
  self.close([(F[k]+F[-k%N].conjugate())/2 for k in range(N)],dft(x));self.close([(F[k]-F[-k%N].conjugate())/(2j) for k in range(N)],dft(y))
 def test_frequency_sampling_folding(self):
  d=svg_data('24-rectangle-fold');x=d['input']
  for N in (3,4,5,6):
   samples=[sum(v*cmath.exp(-2j*math.pi*k*n/N) for n,v in enumerate(x)) for k in range(N)]
   self.close(idft(samples),d['folds'][str(N)]);self.close(fold(x,N),d['folds'][str(N)])
  self.close(idft([5,1,1,1]),[2,1,1,1]);r=svg_data('24-residue-fold');self.close(r['output'],fold(x,4))
 def test_exponential_sampling_graph(self):
  d=svg_data('24-exponential-fold');a=d['a']
  for N,error in zip(d['N'],d['relativeErrors']):
   X=[1/(1-a*cmath.exp(-2j*math.pi*k/N)) for k in range(N)];self.close(idft(X),[a**n/(1-a**N) for n in range(N)])
   self.assertAlmostEqual(error,a**N/(1-a**N),places=13)
 def test_interpolation_and_removable_singularity(self):
  N=5;x=[1,2,-1,0,.5];X=dft(x)
  for omega in (0,.37,2*math.pi/5,math.pi,2*math.pi):
   direct=sum(v*cmath.exp(-1j*omega*n) for n,v in enumerate(x))
   reconstructed=sum(X[k]*sum(cmath.exp(-1j*(omega-2*math.pi*k/N)*n) for n in range(N)) for k in range(N))/N
   self.assertLess(abs(direct-reconstructed),1e-10)
 def test_page_coverage_and_reading_levels(self):
  for num,total,essential in [('23',53,8),('24',11,5)]:
   d=json.loads((ROOT/'site/dsp-redraw'/f'ch2-{num}.json').read_text());ids={c['id'] for c in d['cards']}
   self.assertEqual(sorted(x['page'] for x in d['pageMap']),list(range(1,total+1)))
   self.assertEqual(sum(c['level']=='essential' for c in d['cards']),essential)
   for r in d['pageMap']:self.assertTrue(r['cardIds']);self.assertTrue(set(r['cardIds'])<=ids)
   self.assertEqual({p for c in d['cards'] for p in c['sourcePages']},set(range(1,total+1)))
if __name__=='__main__':unittest.main(verbosity=2)
