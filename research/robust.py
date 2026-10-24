# How forgiving is "displace, then let the dissipation finish"? Compare stabilized fidelity (basin map J)
# with the raw overlap |<alpha|beta>|^2 of an unstabilized displacement.
from common import *
import scipy.linalg as sla
N = 30; a = dq.destroy(N)
jops = [jnp.sqrt(k2)*(a@a - alpha**2*dq.eye(N)), jnp.sqrt(ka)*a]
S = np.array(dq.slindbladian(dq.zeros(N), jops).to_jax()); O = np.array(dq.coherent_dm(N, alpha).to_jax())
J = (sla.expm(S*1.0).conj().T @ O.reshape(-1, order='F')).reshape(N, N, order='F')
F = lambda be: float(np.real((lambda p: p.conj()@J@p)(np.array(dq.coherent(N, be).to_jax()).ravel())))
raw = lambda be: float(np.exp(-abs(be-alpha)**2))
for th in [0, 10, 20, 30, 45, 60, 75]:
    be = alpha*np.exp(1j*np.deg2rad(th)); print(f'phase error {th:2d} deg: stabilized {F(be):.4f}  raw {raw(be):.4f}')
bs = np.linspace(0.5, 4.0, 351); Fs = np.array([F(x) for x in bs]); Rs = np.array([raw(x) for x in bs])
for th in [0.99, 0.999]:
    k = bs[Fs >= th]; r = bs[Rs >= th]
    print(f'F>={th}: stabilized beta in [{k.min():.2f}, {k.max():.2f}]   raw beta in [{r.min():.2f}, {r.max():.2f}]')
# phase window at |beta|=alpha
ths = np.linspace(0, 90, 181); Fp = np.array([F(alpha*np.exp(1j*np.deg2rad(t))) for t in ths]); Rp = np.array([raw(alpha*np.exp(1j*np.deg2rad(t))) for t in ths])
for th in [0.99, 0.999]:
    print(f'F>={th}: stabilized phase error up to {ths[Fp>=th].max():.1f} deg, raw up to {ths[Rp>=th].max():.1f} deg')
