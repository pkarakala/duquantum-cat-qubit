"""Build the physics once. Each function returns (H, jump_ops, operators).

Drive quadratures (RESEARCH §4.1): eps_z (a + a†) pushes <a> along Im (readout, a Z_L rotation;
it can never select a well from vacuum), eps_x i(a† - a) pushes <a> along +Re (state preparation).
With every optional argument at its default, H and the jumps are bit-identical to the intro track.
"""
import numpy as np
import jax.numpy as jnp
import dynamiqs as dq


def _is_zero(x):
    """True only for a concrete scalar 0, so default calls add no term at all (bit-identical H)."""
    try:
        return np.ndim(x) == 0 and float(x) == 0.0
    except TypeError:   # a jax tracer (grad / jit through a drive amplitude): keep the term
        return False


def _scaled(x, op):
    """x * op; an array x becomes a leading batch axis."""
    if np.ndim(x) == 0:
        return x * op
    return jnp.asarray(x)[..., None, None] * op


def _check_batched(*args, extra=0):
    # two batched arguments would broadcast element-wise, not as a sweep grid: refuse
    if sum(np.ndim(v) > 0 for v in args) + extra > 1:
        raise ValueError("at most one batched argument per call")


def loss_jumps(a, kappa_a, n_th=0.0) -> list:
    """[sqrt(kappa_a (1 + n_th)) a] + ([sqrt(kappa_a n_th) a†] if n_th > 0). Empty list if kappa_a == 0."""
    if n_th < 0:
        raise ValueError(f"n_th must be >= 0, got {n_th}")
    if _is_zero(kappa_a):
        return []
    jumps = [jnp.sqrt(kappa_a * (1 + n_th)) * a]
    if n_th > 0:
        jumps.append(jnp.sqrt(kappa_a * n_th) * a.dag())
    return jumps


def drive_ops(a) -> tuple:
    """(X, P) = (a + a†, i(a† - a)), both Hermitian.

    eps_z * X: READOUT drive. Heisenberg d<a>/dt = -i eps_z pushes along the IMAGINARY axis
               (a Z_L rotation in the code space); it can NOT select a well from vacuum.
    eps_x * P: d<a>/dt = +eps_x pushes along +Re; breaks alpha -> -alpha (state preparation).
    """
    return a + a.dag(), 1j * (a.dag() - a)


def _drive_terms(a, eps_z, eps_x):
    X, P = drive_ops(a)
    return [_scaled(e, op) for e, op in ((eps_z, X), (eps_x, P)) if not _is_zero(e)]


def one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0):
    """Effective model: L2 = sqrt(kappa_2) (a^2 - alpha^2), plus memory loss (loss_jumps).

    H = eps_z X + eps_x P (dq.zeros(N) when both are 0). kappa_2, eps_z or eps_x may be an
    array: the operator then carries a leading batch axis and dq.mesolve runs every value in
    one call. At most one of them may be batched per call.
    """
    _check_batched(kappa_2, eps_z, eps_x)
    a = dq.destroy(N)
    k2 = jnp.asarray(kappa_2)
    L2 = jnp.sqrt(k2)[..., None, None] * (a @ a - alpha**2 * dq.eye(N))
    jumps = [L2] + loss_jumps(a, kappa_a, n_th)
    H = dq.zeros(N)
    for term in _drive_terms(a, eps_z, eps_x):
        H = H + term
    return H, jumps, a


def two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None):
    """Full memory + buffer model from the challenge prompt (rotating frame, real g2).

    H = g2 a^2 b† + g2 a†^2 b - eps_d (b + b†) + eps_z X + eps_x P + extra_H
    jumps = [sqrt(kappa_b) b, sqrt(kappa_a (1 + n_th)) a, (sqrt(kappa_a n_th) a† if n_th > 0)]
    eps_z or eps_x may be an array (one batched argument per call). extra_H is an operator on
    the (Na, Nb) space, e.g. Kerr or Stark terms from Task 2.4a.
    """
    _check_batched(eps_z, eps_x, extra=int(extra_H is not None and len(extra_H.shape) > 2))
    if extra_H is not None and extra_H.shape[-1] != Na * Nb:
        raise ValueError(f"extra_H acts on dimension {extra_H.shape[-1]}, expected Na*Nb = {Na * Nb}")
    a, b = dq.destroy(Na, Nb)
    H = g2 * (a @ a @ b.dag()) + g2 * (a.dag() @ a.dag() @ b) - eps_d * (b + b.dag())
    for term in _drive_terms(a, eps_z, eps_x):
        H = H + term
    if extra_H is not None:
        H = H + (extra_H if isinstance(extra_H, dq.QArray) else dq.asqarray(extra_H, dims=(Na, Nb)))
    jumps = [jnp.sqrt(kappa_b) * b] + loss_jumps(a, kappa_a, n_th)
    return H, jumps, (a, b)


def vacuum2(Na, Nb):
    return dq.tensor(dq.fock(Na, 0), dq.fock(Nb, 0))


def coherent2(Na, Nb, alpha):
    """|alpha>_a (x) |0>_b."""
    return dq.tensor(dq.coherent(Na, alpha), dq.fock(Nb, 0))


def cat2(Na, Nb, alpha, sign=+1):
    """|C±>_a (x) |0>_b with |C±> = unit(|alpha> ± |-alpha>)."""
    if sign not in (+1, -1):
        raise ValueError(f"sign must be +1 or -1, got {sign!r}")
    cat = dq.unit(dq.coherent(Na, alpha) + sign * dq.coherent(Na, -alpha))
    return dq.tensor(cat, dq.fock(Nb, 0))
