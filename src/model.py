"""Build the physics once. Each function returns (H, jump_ops, operators)."""
import jax.numpy as jnp
import dynamiqs as dq


def one_mode(N, kappa_2, alpha, kappa_a=0.0):
    """Effective model: L2 = sqrt(kappa_2) (a^2 - alpha^2), plus memory loss sqrt(kappa_a) a.

    kappa_2 may be an array: the jump operator then carries a leading batch axis
    and dq.mesolve runs every value in one call.
    """
    a = dq.destroy(N)
    k2 = jnp.asarray(kappa_2)
    L2 = jnp.sqrt(k2)[..., None, None] * (a @ a - alpha**2 * dq.eye(N))
    jumps = [L2]
    if kappa_a:
        jumps.append(jnp.sqrt(kappa_a) * a)
    return dq.zeros(N), jumps, a


def two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a):
    """Full memory + buffer model from the challenge prompt (rotating frame, real g2)."""
    a, b = dq.destroy(Na, Nb)
    H = g2 * (a @ a @ b.dag()) + g2 * (a.dag() @ a.dag() @ b) - eps_d * (b + b.dag())
    jumps = [jnp.sqrt(kappa_b) * b, jnp.sqrt(kappa_a) * a]
    return H, jumps, (a, b)


def vacuum2(Na, Nb):
    return dq.tensor(dq.fock(Na, 0), dq.fock(Nb, 0))
