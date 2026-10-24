# Joint gradient optimization (jax.grad through dq.mesolve) of a memory drive eps1(t) and buffer drive eps_d(t)
# to prepare |+alpha> fast, starting from vacuum, in the two-mode model. Controls are piecewise constant.
from common import *
import optax, sys, json
Na, Nb = int(sys.argv[1]), int(sys.argv[2]); T = float(sys.argv[3]); nbins = int(sys.argv[4]); iters = int(sys.argv[5])
e1max = 2*np.pi*float(sys.argv[6])   # memory drive amplitude cap, rad/us
a, b = two_mode(Na, Nb)
Hc = g2*(a@a@b.dag()) + g2*(a.dag()@a.dag()@b)
jops = [jnp.sqrt(kb)*b, jnp.sqrt(ka)*a]
psi0 = dq.tensor(dq.fock(Na,0), dq.fock(Nb,0))
Pa = dq.tensor(dq.coherent_dm(Na, alpha), dq.eye(Nb))
Thold = 0.3                                   # after T: controls back to nominal, check state stays
edges = jnp.linspace(0, T, nbins+1)
times = jnp.concatenate([edges, jnp.array([T+Thold])])
tsave = jnp.concatenate([jnp.zeros(1), jnp.linspace(T, T+Thold, 7)])   # tsave[0]=0 sets the start time
def controls(p):
    e1 = e1max*jnp.tanh(p['u']) + 1j*e1max*jnp.tanh(p['v'])   # each quadrature capped at e1max
    ed = eps_d*(1 + 0.8*jnp.tanh(p['w']))      # buffer drive in [0.2, 1.8] x nominal
    return jnp.concatenate([e1, jnp.zeros(1)]), jnp.concatenate([ed, jnp.array([eps_d])])
def loss(p):
    e1, ed = controls(p)
    H = Hc + dq.pwc(times, e1, a.dag()) + dq.pwc(times, jnp.conj(e1), a) + dq.pwc(times, -ed, b+b.dag())
    r = dq.mesolve(H, jops, psi0, tsave, exp_ops=[Pa], save_states=False, gradient=dq.gradient.BackwardCheckpointed())
    F = jnp.real(r.expects[0, 1:])
    return 1 - jnp.mean(F), F
if iters == 0:   # baselines on the same loss: displacement pulse (capped drive, pump off) then nominal inflation
    for nd in [0, 1, 2, 3]:
        u = jnp.zeros(nbins); v = jnp.where(jnp.arange(nbins) < nd, 20.0, 0.0)   # tanh(20)=1 -> full i*e1max
        w = jnp.where(jnp.arange(nbins) < nd, -20.0, 0.0)                        # buffer drive at its 0.2x floor during the pulse
        L, F = loss(dict(u=u, v=v, w=w))
        print(f'baseline: {nd} bins of i*e1max (beta={float(e1max*nd*T/nbins):.2f}) then inflate: loss {float(L):.5f} F {np.round(np.array(F),4)}')
    raise SystemExit
key = jax.random.PRNGKey(0)
p = dict(u=jnp.zeros(nbins), v=0.1*jnp.ones(nbins), w=jnp.zeros(nbins))   # start with a weak i*eps push
if len(sys.argv) > 7 and sys.argv[7] == 'disp':   # warm start from the displacement baseline
    k = jnp.arange(nbins) < 3
    p = dict(u=jnp.zeros(nbins), v=jnp.where(k, 2.5, 0.0), w=jnp.where(k, -2.5, 0.0))
opt = optax.adam(0.15); st = opt.init(p)
vg = jax.jit(jax.value_and_grad(loss, has_aux=True))
hist=[]
for it in range(iters):
    t0=time.time(); (L, F), g = vg(p); upd, st = opt.update(g, st); p = optax.apply_updates(p, upd)
    hist.append(float(L))
    if it % 5 == 0 or it == iters-1: print(f'it {it} loss {float(L):.5f} F(T..T+0.3) {np.round(np.array(F),4)} {time.time()-t0:.1f}s', flush=True)
e1, ed = controls(p)
json.dump(dict(T=T, nbins=nbins, e1_re=np.real(np.array(e1)).tolist(), e1_im=np.imag(np.array(e1)).tolist(), ed=np.array(ed).tolist(), hist=hist, Ffinal=np.array(F).tolist()), open(f'grape_T{T}_{Na}x{Nb}_e{sys.argv[6]}_{sys.argv[7] if len(sys.argv)>7 else "cold"}.json','w'))
