# "Moon cat" variant (Rousseau et al., Alice & Bob, arXiv:2502.07892): add lambda*(a^dag a) to the pair-exchange operator.
# H = g2[(a^2 + lam a^dag a) b^dag + h.c.] - eps (b + b^dag), eps = g2*alpha^2*(1+lam) so that <n> ~ alpha^2 stays roughly fixed.
from common import *
import sys
Na, Nb = int(sys.argv[1]), int(sys.argv[2])
a, b = two_mode(Na, Nb)
lams = [0.0, 0.2, 0.4]
ts = jnp.linspace(0, 2.0, 401); tt = np.array(ts)
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
Pa = dq.tensor(dq.coherent_dm(Na, alpha), dq.eye(Nb))
for lam in lams:
    X = a@a + lam*(a.dag()@a)
    H = g2*(X@b.dag() + X.dag()@b) - g2*alpha**2*(1+lam)*(b+b.dag())
    psi0 = [dq.tensor(dq.fock(Na,0), dq.fock(Nb,0)), dq.tensor(dq.coherent(Na,1.0), dq.fock(Nb,0))]
    t0=time.time(); r = dq.mesolve(H, jops, psi0, ts, exp_ops=[a.dag()@a, b.dag()@b, Pa], save_states=False)
    E = np.real(np.array(r.expects))
    m = metrics(tt, E[0,0], E[0,1])
    F = E[1,2]
    print(f'lam={lam}: vac start {m} | beta=1 start F(0.25)={F[50]:.4f} F(0.5)={F[100]:.4f} F(2)={F[-1]:.4f}  ({time.time()-t0:.0f}s)', flush=True)
