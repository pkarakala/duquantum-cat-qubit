from common import *
import sys, json
Na, Nb = int(sys.argv[1]), int(sys.argv[2])
a, b = two_mode(Na, Nb)
Hc = g2*(a@a@b.dag()) + g2*(a.dag()@a.dag()@b)
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
psi0 = dq.tensor(dq.fock(Na,0), dq.fock(Nb,0))
ts = jnp.linspace(0, 2.5, 501); tt=np.array(ts)
ref = 4.4026
res = {}
def run(name, f, labels):
    H = Hc + dq.modulated(f, b+b.dag())
    t0=time.time(); r = dq.mesolve(H, jops, psi0, ts, exp_ops=[a.dag()@a, b.dag()@b], save_states=False)
    E = np.real(np.array(r.expects)); E = E.reshape(-1, 2, len(tt))
    rows = [(labels[i], metrics(tt, E[i,0], E[i,1], ref)) for i in range(len(labels))]
    rows.sort(key=lambda x: x[1]['settle'])
    print(name, f'{time.time()-t0:.0f}s'); [print('  ', r_) for r_ in rows[:6]]
    res[name] = dict(best=rows[0], curves={str(labels[i]): E[i].tolist() for i in range(len(labels))})
# two-step (Posicast) refined
A1s = np.array([0.7,0.75,0.8,0.85,0.9]); t1s = np.array([0.22,0.26,0.30,0.34,0.38])
A1g, t1g = np.meshgrid(A1s, t1s, indexing='ij'); A1f=jnp.array(A1g.ravel()); t1f=jnp.array(t1g.ravel())
run('twostep', lambda t: -eps_d*jnp.where(t < t1f, A1f, 1.0), [(float(x),float(y)) for x,y in zip(A1f,t1f)])
# linear ramp over tau
taus = jnp.array([0.1,0.2,0.3,0.4,0.5,0.6,0.8])
run('linramp', lambda t: -eps_d*jnp.clip(t/taus, 0, 1), [float(x) for x in taus])
# smooth sin^2 ramp
run('sin2ramp', lambda t: -eps_d*jnp.where(t<taus, jnp.sin(jnp.pi*t/(2*taus))**2, 1.0), [float(x) for x in taus])
json.dump({k: dict(best=v['best']) for k,v in res.items()}, open(f'shapes_{Na}x{Nb}.json','w'))
np.save(f'shapes_{Na}x{Nb}_curves.npy', res, allow_pickle=True)
