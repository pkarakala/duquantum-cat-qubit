"""Small, testable helpers shared by every task."""
import numpy as np
import jax.numpy as jnp
import dynamiqs as dq


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


def memory_trace_distance(states, reference):
    """Trace distance at each time after zero-padding the smaller Fock space.

    Inputs have shape (time, N, N). Keep the entire reference state: projecting
    and renormalizing it would hide missing population. Retain solver noise.
    """
    states, reference = np.asarray(states), np.asarray(reference)
    if (states.ndim != 3 or reference.ndim != 3
            or states.shape[0] != reference.shape[0]
            or states.shape[1] != states.shape[2]
            or reference.shape[1] != reference.shape[2]
            or states.shape[1] > reference.shape[1]):
        raise ValueError("Expected equal-time square states with N <= reference N")
    extra = reference.shape[1] - states.shape[1]
    delta = np.pad(states, ((0, 0), (0, extra), (0, extra))) - reference
    delta = (delta + delta.conj().swapaxes(-1, -2)) / 2
    return 0.5 * np.abs(np.linalg.eigvalsh(delta)).sum(axis=-1)


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
