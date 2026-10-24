# Re-run the three inflation schedules at a larger truncation and save curves for the workbook
from common import *
import sys, json
Na, Nb = int(sys.argv[1]), int(sys.argv[2])
a, b = two_mode(Na, Nb)
Hc = g2*(a@a@b.dag()) + g2*(a.dag()@a.dag()@b)
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
psi0 = dq.tensor(dq.fock(Na,0), dq.fock(Nb,0))
ts = jnp.linspace(0, 2.5, 251); tt = np.array(ts)
# top-level populations as truncation monitors
Ptop_a = dq.tensor(dq.proj(dq.fock(Na,Na-1)) + dq.proj(dq.fock(Na,Na-2)), dq.eye(Nb))
Ptop_b = dq.tensor(dq.eye(Na), dq.proj(dq.fock(Nb,Nb-1)))
kind = jnp.array([0, 1, 2])
def f(t):
    step = jnp.ones(3)
    lin = jnp.clip(t/0.6, 0, 1)
    two = jnp.where(t < 0.26, 0.7, 1.0)
    return -eps_d*jnp.where(kind == 0, 1.0, jnp.where(kind == 1, lin, two))
H = Hc + dq.modulated(f, b+b.dag())
t0 = time.time()
r = dq.mesolve(H, jops, psi0, ts, exp_ops=[a.dag()@a, b.dag()@b, Ptop_a, Ptop_b], save_states=False)
E = np.real(np.array(r.expects)); print('time', time.time()-t0)
out = dict(Na=Na, Nb=Nb, t=tt.round(3).tolist())
for i, name in enumerate(['step', 'linear', 'twostep']):
    m = metrics(tt, E[i,0], E[i,1], 4.4026)
    print(name, m, 'max top_a', E[i,2].max(), 'max top_b', E[i,3].max())
    out[name] = dict(na=E[i,0].round(4).tolist(), nb=E[i,1].round(4).tolist(), **m, topa=float(E[i,2].max()), topb=float(E[i,3].max()))
json.dump(out, open(f'verify_{Na}x{Nb}.json', 'w'))
