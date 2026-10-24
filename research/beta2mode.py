# Displace-then-inflate in the full two-mode model; compare to Heisenberg basin map of the effective model
from common import *
import sys
Na, Nb = int(sys.argv[1]), int(sys.argv[2])
a, b = two_mode(Na, Nb)
H = g2*(a@a@b.dag()) + g2*(a.dag()@a.dag()@b) - eps_d*(b+b.dag())
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
betas = [0.0, 0.5, 1.0, 1.12, 1.5, 2.1]
psi0 = [dq.tensor(dq.coherent(Na, be), dq.fock(Nb,0)) for be in betas]
Pa = dq.tensor(dq.coherent_dm(Na, alpha), dq.eye(Nb))
ts = jnp.linspace(0, 2.0, 201); tt = np.array(ts)
t0=time.time()
r = dq.mesolve(H, jops, psi0, ts, exp_ops=[Pa, a, a.dag()@a], save_states=False)
E = np.array(r.expects); print('time', time.time()-t0)
for i, be in enumerate(betas):
    F = np.real(E[i,0]); 
    k = np.where(F >= 0.99*F[-1])[0]
    print(f'beta={be}: F(0.25)={F[25]:.4f} F(0.5)={F[50]:.4f} F(1)={F[100]:.4f} F(2)={F[-1]:.4f} Re<a>/alpha(2)={np.real(E[i,1,-1])/alpha:.4f} peak na={np.real(E[i,2]).max():.2f}')
np.savez(f'beta2mode_{Na}x{Nb}.npz', t=tt, E=E, betas=betas)
