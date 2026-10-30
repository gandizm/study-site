"""Independent numerical checks of Chapter 2 conventions (stdlib only)."""
import cmath,math,unittest
PI=math.pi
def dft(x,N=None):
 N=N or len(x);return [sum(v*cmath.exp(-2j*PI*k*n/N) for n,v in enumerate(x)) for k in range(N)]
def idft(X):
 N=len(X);return [sum(v*cmath.exp(2j*PI*k*n/N) for k,v in enumerate(X))/N for n in range(N)]
def convolution(x,h):return [sum(x[k]*h[n-k] for k in range(len(x)) if 0<=n-k<len(h)) for n in range(len(x)+len(h)-1)]
class DSPMath(unittest.TestCase):
 def close(self,a,b):self.assertEqual(len(a),len(b));self.assertLess(max(abs(x-y) for x,y in zip(a,b)),1e-10)
 def test_dft_inverse_and_parseval(self):
  x=[2+1j,-3,4j,1,5];X=dft(x);self.close(idft(X),x);self.assertAlmostEqual(sum(abs(v)**2 for v in x),sum(abs(v)**2 for v in X)/len(x))
 def test_dfs_normalization_and_orthogonality(self):
  N=8;x=[1]*4+[0]*4;X=dft(x);a=[v/N for v in X]
  self.close([sum(a[k]*cmath.exp(2j*PI*k*n/N) for k in range(N)) for n in range(N)],x)
  for m in range(-16,17):self.assertLess(abs(sum(cmath.exp(2j*PI*k*m/N) for k in range(N))/N-(1 if m%N==0 else 0)),1e-10)
 def test_frequency_sampling_folds_not_truncates(self):
  x=[1]*5;self.close(idft(dft(x,4)),[2,1,1,1]);self.close(idft(dft(x,5)),x)
  x=[1,-1,2,3,4,-2,1];N=4;self.close(idft(dft(x,N)),[sum(x[n::N]) for n in range(N)])
 def test_infinite_exponential_periodic_sum(self):
  a=.5;N=4;X=[1/(1-a*cmath.exp(-2j*PI*k/N)) for k in range(N)]
  self.close(idft(X),[a**n/(1-a**N) for n in range(N)])
 def test_padding_convolution(self):
  x=[1,2,3];h=[2,-1];N=len(x)+len(h)-1;X=dft(x,N);H=dft(h,N)
  self.close(idft([a*b for a,b in zip(X,H)]),convolution(x,h))
 def test_fft_identity_four_points(self):
  x=[1,2,3,4];E=dft(x[::2]);O=dft(x[1::2]);out=[0j]*4
  for k in range(2):w=cmath.exp(-2j*PI*k/4);out[k]=E[k]+w*O[k];out[k+2]=E[k]-w*O[k]
  self.close(out,dft(x));self.close(idft(dft(x)),x)
 def test_operation_ratio(self):
  N=1024;stages=int(math.log2(N));mult_ratio=N*N/(N*stages/2);total_ratio=(N*N+N*(N-1))/(N*stages*1.5)
  self.assertAlmostEqual(mult_ratio,204.8);self.assertAlmostEqual(total_ratio,136.46666666666667)
if __name__=='__main__':unittest.main(verbosity=2)
