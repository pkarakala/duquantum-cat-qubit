# Heisenberg-picture "fidelity map": J_T = e^{L^dag T}(|alpha><alpha|), so F(rho0) = Tr(J_T rho0) for ANY rho0
from common import *
import scipy.linalg as sla
N = 30
a = dq.destroy(N)
jops = [jnp.sqrt(k2)*(a@a - alpha**2*dq.eye(N)), jnp.sqrt(ka)*a]
S = np.array(dq.slindbladian(dq.zeros(N), jops).to_jax())
O = np.array(dq.coherent_dm(N, alpha).to_jax())
vec = lambda M: M.reshape(-1, order='F'); unvec = lambda v: v.reshape(N, N, order='F')
# check convention: S @ vec(rho) vs lindbladian(rho)
rho = np.array(dq.coherent_dm(N, 0.7).to_jax())
Lr = np.array(dq.lindbladian(dq.zeros(N), jops, dq.coherent_dm(N, 0.7)).to_jax())
fo = 'F' if np.allclose(S@vec(rho), vec(Lr)) else 'C'
vec = lambda M, o=fo: M.reshape(-1, order=o); unvec = lambda v, o=fo: v.reshape(N, N, order=o)
print('vec order', fo, np.abs(S@vec(rho)-vec(Lr)).max())
out = {}
for T in [0.25, 0.5, 1.0, 2.0]:
    P = sla.expm(S*T)
    J = unvec(P.conj().T @ vec(O)); J = (J + J.conj().T)/2
    # sanity: forward check at beta=1
    r = dq.mesolve(dq.zeros(N), jops, dq.coherent(N, 1.0), jnp.array([0, T]))
    Ff = float(np.real(dq.expect(dq.coherent_dm(N, alpha), r.states[-1])))
    psi = np.array(dq.coherent(N, 1.0).to_jax()).ravel()
    Fh = float(np.real(psi.conj()@J@psi))
    w, V = np.linalg.eigh(J)
    # energy-constrained optimum: best seed in span{|0>,|1>} and in Fock <= 2
    sub2 = np.linalg.eigvalsh(J[:2,:2])[-1]; sub3 = np.linalg.eigvalsh(J[:3,:3])[-1]
    # coherent map
    xs = np.linspace(-2.5, 2.5, 51)
    Q = np.zeros((51, 51))
    for i, x in enumerate(xs):
        for j, y in enumerate(xs):
            ps = np.array(dq.coherent(N, x+1j*y).to_jax()).ravel(); Q[j, i] = np.real(ps.conj()@J@ps)
    # min |beta| real giving F>=0.99, 0.999
    bs = np.linspace(0, 2.5, 251); Fb = np.array([np.real((lambda p: p.conj()@J@p)(np.array(dq.coherent(N, bb).to_jax()).ravel())) for bb in bs])
    def first(th):
        k = np.where(Fb >= th)[0]; return float(bs[k[0]]) if len(k) else None
    print(f'T={T}: fwd F(beta=1)={Ff:.4f} heis={Fh:.4f} | best seed any={w[-1]:.4f} span01={sub2:.4f} span012={sub3:.4f} | F(beta=0)={Fb[0]:.4f} F(0.5)={Fb[50]:.4f} F(1)={Fb[100]:.4f} F(1.5)={Fb[150]:.4f} | beta for .99={first(.99)} .999={first(.999)} max={Fb.max():.4f} at {bs[Fb.argmax()]:.2f}')
    out[T] = dict(Q=Q, bs=bs, Fb=Fb)
np.savez('heis.npz', xs=xs, **{f'Q{T}': out[T]['Q'] for T in out}, **{f'Fb{T}': out[T]['Fb'] for T in out}, bs=bs)
