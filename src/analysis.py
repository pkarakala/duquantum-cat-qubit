"""Small, testable helpers shared by every task."""
import numpy as np
import jax.numpy as jnp
import dynamiqs as dq
from scipy.optimize import curve_fit


def memory_state(rho, Na, Nb):
    """Partial trace over the buffer: rho_a = Tr_b(rho)."""
    return dq.ptrace(rho, 0, (Na, Nb))


def top_projector(N, k):
    """Projector onto the highest k Fock levels of an N-level mode."""
    d = np.zeros(N)
    d[-k:] = 1.0
    return dq.asqarray(np.diag(d).astype(complex))


def cat_plus(N, alpha):
    """Even cat |C+> = (|alpha> + |-alpha>) / norm."""
    return dq.unit(dq.coherent(N, alpha) + dq.coherent(N, -alpha))


def memory_extras(Na, Nb, alpha):
    """save_extra callback: memory-only quantities at every saved time, without storing
    the full two-mode density matrix (which is large for converged truncations)."""
    cp = cat_plus(Na, alpha).to_jax()
    ap, am = dq.coherent(Na, alpha).to_jax(), dq.coherent(Na, -alpha).to_jax()
    par = jnp.diag((-1.0) ** jnp.arange(Na))

    def extra(t, rho):
        r = memory_state(rho, Na, Nb).to_jax()
        return {
            "parity": jnp.real(jnp.trace(par @ r)),
            "fid_cat": jnp.real(jnp.conj(cp).T @ r @ cp)[0, 0],
            "purity": jnp.real(jnp.trace(r @ r)),
            # |<alpha|rho_a|-alpha>|: about 1/2 for the cat, 0 for a 50/50 mixture
            "coherence": jnp.abs(jnp.conj(ap).T @ r @ am)[0, 0],
            "re_a": jnp.real(jnp.trace(r @ jnp.diag(jnp.sqrt(jnp.arange(1, Na)), 1))),
            "pop_top2_a": jnp.real(r[-1, -1] + r[-2, -2]),
        }

    return extra


def fit_exp_decay(t, y):
    """Fit y = A exp(-gamma t) by linear regression on log|y|. Returns (gamma, A)."""
    t, y = np.asarray(t), np.asarray(y)
    slope, intercept = np.polyfit(t, np.log(np.abs(y)), 1)
    return -slope, float(np.exp(intercept))


def settle_time(t, y, target, rel=0.01):
    """First time after which y stays within rel of target."""
    t, y = np.asarray(t), np.asarray(y)
    outside = np.where(np.abs(y - target) > rel * abs(target))[0]
    if len(outside) == 0:
        return float(t[0])
    return float(t[min(outside[-1] + 1, len(t) - 1)])


def fit_exp_offset(t, y, p0=None) -> dict:
    """Fit y = A exp(-gamma t) + C (scipy curve_fit). p0 = (gamma, A, C).

    Use it for parity: the steady parity is 1/cosh(2 alpha^2) != 0, so a pure exponential is
    biased. Internally the fit runs in t - t[0] (A is still reported at t = 0), so a window
    that starts late stays well conditioned. Returns floats
    {'gamma', 'A', 'C', 'gamma_stderr', 'rel_rms_residual' = rms(y - fit) / rms(y)}.
    """
    t, y = np.asarray(t, dtype=float), np.asarray(y, dtype=float)
    t0 = t[0]
    if p0 is None:   # already in the shifted frame: y[0] - y[-1] is the amplitude at t0
        q0 = (3.0 / (t[-1] - t0), y[0] - y[-1], y[-1])
    else:
        g0, A0, C0 = p0
        q0 = (g0, A0 * np.exp(-g0 * t0), C0)

    def model(s, g, A, c):
        return A * np.exp(-g * s) + c

    popt, pcov = curve_fit(model, t - t0, y, p0=q0, maxfev=20000)
    g, A_t0, c = popt
    resid = y - model(t - t0, *popt)
    return {
        "gamma": float(g),
        "A": float(A_t0 * np.exp(g * t0)),
        "C": float(c),
        "gamma_stderr": float(np.sqrt(pcov[0, 0])),
        "rel_rms_residual": float(np.sqrt(np.mean(resid**2)) / np.sqrt(np.mean(y**2))),
    }


def code_basis(N, alpha) -> tuple:
    """(|C+>, |C->) kets on N levels, |C±> = unit(|alpha> ± |-alpha>)."""
    ap, am = dq.coherent(N, alpha), dq.coherent(N, -alpha)
    return dq.unit(ap + am), dq.unit(ap - am)


def z_logical(N, alpha):
    """Z_L = |C+><C-| + |C-><C+| = (|alpha><alpha| - |-alpha><-alpha|) / sqrt(1 - e^{-4 alpha^2})."""
    cp, cm = code_basis(N, alpha)
    return cp @ cm.dag() + cm @ cp.dag()


def code_projector(N, alpha):
    """Projector onto span{|alpha>, |-alpha>} = |C+><C+| + |C-><C-|."""
    cp, cm = code_basis(N, alpha)
    return cp @ cp.dag() + cm @ cm.dag()


def _expect_dm(op, rho_a):
    r = jnp.asarray(rho_a.to_jax() if hasattr(rho_a, "to_jax") else rho_a)
    if r.ndim != 2 or r.shape[0] != r.shape[1]:
        raise ValueError(f"expected one unbatched density matrix, got shape {r.shape}")
    return float(jnp.real(jnp.trace(op.to_jax() @ r)))


def leakage(rho_a, alpha) -> float:
    """1 - Tr(code_projector rho_a): population outside the cat code space."""
    return 1.0 - _expect_dm(code_projector(rho_a.shape[-1], alpha), rho_a)


def p_right_well(rho_a, alpha) -> float:
    """(1 + Tr(z_logical rho_a)) / 2: probability of the +alpha well."""
    return (1.0 + _expect_dm(z_logical(rho_a.shape[-1], alpha), rho_a)) / 2
