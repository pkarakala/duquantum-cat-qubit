"""Liouvillian spectra with scipy.sparse: bit-flip and phase-flip rates as eigenvalues.

Why: Gamma_X falls like e^{-gamma alpha^2}, so fitting Re<a>(t) needs simulations as long
as T_X (seconds at alpha = 2.1). The same rate is the slowest nonzero eigenvalue of the
Liouvillian, which a sparse shift-invert solve finds in seconds to minutes at any alpha.

Conventions (row-major vectorisation, vec(A rho B) = (A kron B^T) vec(rho)):
    L = -i (H x I - I x H^T) + sum_k [J x J* - 1/2 J^dag J x I - 1/2 I x (J^dag J)^T]
Every term of the cat model is invariant under a -> -a, so L keeps the memory-parity
difference (n_a - m_a) mod 2 of each matrix element |n><m|. The odd block holds Z_L, Y_L
(bit flips: Gamma_X = -lambda_1(odd)); the even block holds the steady state and X_L
(parity: Gamma_Z = -lambda_1(even, nonzero)).
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def destroy(N):
    return sp.diags(np.sqrt(np.arange(1, N, dtype=float)), 1, format="csr")


def ops_two_mode(Na, Nb):
    a = sp.kron(destroy(Na), sp.identity(Nb), format="csr")
    b = sp.kron(sp.identity(Na), destroy(Nb), format="csr")
    return a, b


def hamiltonian_two_mode(Na, Nb, g2, eps_d, eps_z=0.0):
    a, b = ops_two_mode(Na, Nb)
    ad, bd = a.T.tocsr(), b.T.tocsr()
    H = g2 * (a @ a @ bd + ad @ ad @ b) - eps_d * (b + bd)
    if eps_z:
        H = H + eps_z * (a + ad)
    return H.astype(complex), a, b


def jumps_two_mode(a, b, kappa_b, kappa_a, n_th=0.0):
    J = [np.sqrt(kappa_b) * b, np.sqrt(kappa_a * (1 + n_th)) * a]
    if n_th:
        J.append(np.sqrt(kappa_a * n_th) * a.T.tocsr())
    return J


def ops_one_mode(N):
    return destroy(N)


def one_mode(N, kappa_2, alpha, kappa_a, n_th=0.0, eps_z=0.0):
    """Effective model L2 = sqrt(k2)(a^2 - alpha^2); returns (H, jumps, a)."""
    a = destroy(N)
    ad = a.T.tocsr()
    H = sp.csr_matrix((N, N), dtype=complex)
    if eps_z:
        H = H + eps_z * (a + ad)
    J = [np.sqrt(kappa_2) * (a @ a - alpha**2 * sp.identity(N)),
         np.sqrt(kappa_a * (1 + n_th)) * a]
    if n_th:
        J.append(np.sqrt(kappa_a * n_th) * ad)
    return H, J, a


def liouvillian(H, jumps):
    d = H.shape[0]
    I = sp.identity(d, format="csr")
    L = -1j * (sp.kron(H, I) - sp.kron(I, H.T))
    for J in jumps:
        J = sp.csr_matrix(J, dtype=complex)
        JdJ = (J.conj().T @ J).tocsr()
        L = L + sp.kron(J, J.conj()) - 0.5 * sp.kron(JdJ, I) - 0.5 * sp.kron(I, JdJ.T)
    return L.tocsc()


def parity_sector_index(dims, sector):
    """Indices of vec(rho) with (n_a - m_a) % 2 == sector. dims = (Na,) or (Na, Nb); memory first."""
    Na = dims[0]
    rest = int(np.prod(dims[1:])) if len(dims) > 1 else 1
    na = np.repeat(np.arange(Na), rest)          # memory photon number of each basis state
    d = Na * rest
    diff = (na[:, None] - na[None, :]) % 2       # row-major: index = i*d + j
    return np.flatnonzero(diff.reshape(d * d) == sector)


def slowest(L, k=3, sigma=0.0, which="LM"):
    """k eigenvalues of L closest to sigma (shift-invert), sorted by |Re|."""
    vals = spla.eigs(L, k=k, sigma=sigma, which=which, return_eigenvectors=False,
                     tol=1e-12, maxiter=5000)
    return vals[np.argsort(np.abs(vals.real))]


def gamma_x_odd(L, dims, k=3):
    """Bit-flip rate: -Re of the slowest eigenvalue of the odd block (no zero mode there)."""
    idx = parity_sector_index(dims, 1)
    Lo = L[idx][:, idx].tocsc()
    vals = slowest(Lo, k=k)
    return -vals[0].real, vals


def gamma_z_even(L, dims, k=3):
    """Phase-flip rate: slowest nonzero eigenvalue of the even block (skip the steady state)."""
    idx = parity_sector_index(dims, 0)
    Le = L[idx][:, idx].tocsc()
    vals = slowest(Le, k=k, sigma=-1e-3)
    nz = vals[np.abs(vals) > 1e-9]
    return -nz[0].real, vals


# ---- analytic predictions (RESEARCH.md §5-6) -------------------------------------------------

def coth(x):
    return 1.0 / np.tanh(x)


def gamma_x_channel1(alpha, kappa_a):
    """Code-space (Golden-Rule) channel: kappa_a alpha^2 (coth 2alpha^2 - 1) ~ 2 kappa_a alpha^2 e^{-4alpha^2}."""
    a2 = alpha**2
    return kappa_a * a2 * (coth(2 * a2) - 1)


def gamma_x_channel2(alpha, kappa_a, kappa_2, c=1.0):
    """Out-of-code-space channel: c (kappa_a^2 / kappa_2) e^{-2 alpha^2} (Dubovitskii, doubled)."""
    return c * kappa_a**2 / kappa_2 * np.exp(-2 * alpha**2)


def gamma_z_theory(alpha, kappa_a):
    a2 = alpha**2
    return 2 * kappa_a * a2 * coth(2 * a2)
