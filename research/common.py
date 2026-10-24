import dynamiqs as dq, jax, jax.numpy as jnp, numpy as np, time
dq.set_precision('double')
g2 = 2*np.pi*0.763; kb = 2*np.pi*2.6; ka = 2*np.pi*9.3e-3; alpha = 2.1
eps_d = alpha**2*g2; k2 = 4*g2**2/kb
def two_mode(Na=32, Nb=8):
    a, b = dq.destroy(Na, Nb)
    return a, b
def ptrace_a(states, Na, Nb):
    return dq.ptrace(states, 0, (Na, Nb))
dq.set_progress_meter(False)
def metrics(tt, na, nb, ref=None):
    fin = na[-1] if ref is None else ref
    bad = np.where(np.abs(na-fin)>0.01*fin)[0]
    ts = tt[bad[-1]+1] if len(bad) and bad[-1]+1 < len(tt) else (np.inf if len(bad) else 0.0)
    return dict(peak=float(na.max()), nbpk=float(nb.max()), settle=float(ts), final=float(na[-1]))
