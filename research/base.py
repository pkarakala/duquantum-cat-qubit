from common import *
Na, Nb = 32, 8
a, b = two_mode(Na, Nb)
H = g2*(a@a@b.dag()) + g2*(a.dag()@a.dag()@b) - eps_d*(b+b.dag())
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
psi0 = dq.tensor(dq.fock(Na,0), dq.fock(Nb,0))
ts = jnp.linspace(0, 3.0, 601)
t0=time.time()
r = dq.mesolve(H, jops, psi0, ts, exp_ops=[a.dag()@a, b.dag()@b])
print('time', time.time()-t0)
na = np.real(np.array(r.expects[0])); nb = np.real(np.array(r.expects[1]))
tt=np.array(ts)
i = na.argmax(); print('peak na', na[i], 'at', tt[i], 'peak nb', nb.max(), 'at', tt[nb.argmax()], 'final', na[-1])
# settling to within 1% of final
fin = na[-1]; bad = np.where(np.abs(na-fin)>0.01*fin)[0]; print('settle 1%', tt[bad[-1]+1])
# ringing period: find local maxima
from scipy.signal import argrelextrema
mx = argrelextrema(na, np.greater)[0]; mn = argrelextrema(na, np.less)[0]
print('maxima t', tt[mx][:6], 'vals', na[mx][:6]); print('minima t', tt[mn][:6], na[mn][:6])
np.savez('base.npz', t=tt, na=na, nb=nb)
G = 2*g2*alpha; gam = kb/2
print('linear theory: omega', np.sqrt(G**2-gam**2/4), 'period', 2*np.pi/np.sqrt(G**2-gam**2/4), 'env decay rate', gam/2, 'settle1%', np.log(100)/(gam/2))
