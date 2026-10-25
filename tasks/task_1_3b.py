"""Task 1.3(b): prepare |+α⟩ in the two-mode model, and cost it (1.3c).

Vacuum inflation conserves a → −a, so it lands on the even cat. Method (ii) is a
finite real-axis pulse with the pump off, then stabilization. Pranav's intro script
drove the memory while the pump was already on; that is pump_on=True, not (ii).
"""
import argparse

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

from src import config as C
from src.analysis import code_projector, z_logical
from src.model import coherent2, one_mode, two_mode, vacuum2

T_EVAL = 3.0
TAUS_NS = (20, 50, 100, 200)
EX_RATIOS = (0.02, 0.05, 0.1, 0.2)
T_OFFS = (0.1, 0.2, 0.4)
METRIC_KEYS = ("re_a", "im_a", "fid", "p_right", "parity", "purity", "leakage",
               "n_a", "n_b", "top2_a", "top_b")
# Intro-track anchor: results/task_1_3b.json, β = α, t = 2 µs, 32×12. Method (i).
PRANAV_F_T2 = 0.9999915936048853


def metrics_extra(Na, Nb, alpha):
    """save_extra(t, rho) -> memory observables. rho_a is Na×Na; never the full state."""
    ket = dq.coherent(Na, alpha).to_jax()
    Z = dq.asqarray(z_logical(Na, alpha)).to_jax()
    P = dq.asqarray(code_projector(Na, alpha)).to_jax()
    parity = jnp.diag(((-1.0) ** jnp.arange(Na)).astype(jnp.complex128))
    a_mat = jnp.diag(jnp.sqrt(jnp.arange(1, Na, dtype=float)), k=1).astype(jnp.complex128)
    n_a = jnp.arange(Na, dtype=float)
    n_b = jnp.arange(Nb, dtype=float)

    def extra(t, rho):
        rho_a = dq.ptrace(rho, 0, (Na, Nb)).to_jax()
        rho_b = dq.ptrace(rho, 1, (Na, Nb)).to_jax()
        ea = jnp.trace(rho_a @ a_mat)
        fid = (jnp.conj(ket).T @ rho_a @ ket)[0, 0]
        return {
            "re_a": jnp.real(ea),
            "im_a": jnp.imag(ea),
            "fid": jnp.real(fid),
            "p_right": (1.0 + jnp.real(jnp.trace(Z @ rho_a))) / 2.0,
            "parity": jnp.real(jnp.trace(parity @ rho_a)),
            "purity": jnp.real(jnp.trace(rho_a @ rho_a)),
            "leakage": 1.0 - jnp.real(jnp.trace(P @ rho_a)),
            "n_a": jnp.real(jnp.sum(n_a * jnp.diag(rho_a))),
            "n_b": jnp.real(jnp.sum(n_b * jnp.diag(rho_b))),
            "top2_a": jnp.real(rho_a[-1, -1] + rho_a[-2, -2]),
            "top_b": jnp.real(rho_b[-1, -1]),
            "rho_a": rho_a,
        }

    return extra


def _unpack(res, t):
    out = {"t_us": np.asarray(t, dtype=float)}
    for k in METRIC_KEYS:
        out[k] = np.asarray(res.extra[k]).real
    out["rho_a"] = np.asarray(res.extra["rho_a"])
    return out


def _solve(H, jumps, rho0, t, extra):
    return dq.mesolve(H, jumps, rho0, t, method=C.METHOD, save_states=False, save_extra=extra)


def _concat(tr1, tr2):
    """Drop tr1's last sample; tr2 starts on that same state."""
    out = {"t_us": np.concatenate([tr1["t_us"][:-1], tr2["t_us"]])}
    for k in METRIC_KEYS:
        out[k] = np.concatenate([tr1[k][..., :-1], tr2[k]], axis=-1)
    if "rho_a" in tr1 and "rho_a" in tr2:
        out["rho_a"] = np.concatenate([tr1["rho_a"][..., :-1, :, :], tr2["rho_a"]], axis=-3)
    return out


def run_ideal(Na, Nb, alpha, t_eval):
    """Method (i): instantaneous displacement, then nominal stabilization."""
    H, jumps, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    t = jnp.linspace(0.0, t_eval, 301)
    res = _solve(H, jumps, coherent2(Na, Nb, alpha), t, metrics_extra(Na, Nb, alpha))
    return _unpack(res, t)


def run_pulse(Na, Nb, alpha, tau_us, t_eval, pump_on=False):
    """Method (ii): displace with g2 = eps_d = 0, then stabilize. pump_on is not (ii)."""
    eps_x = float(alpha) / float(tau_us)
    if pump_on:
        H, jumps, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_x=eps_x)
    else:
        H, jumps, _ = two_mode(Na, Nb, 0.0, 0.0, C.KAPPA_B, C.KAPPA_A, eps_x=eps_x)
    extra = metrics_extra(Na, Nb, alpha)
    t = jnp.linspace(0.0, tau_us, 51)
    res = _solve(H, jumps, vacuum2(Na, Nb), t, extra)
    tr = _unpack(res, np.asarray(t) - float(tau_us))
    tr["eps_x"] = eps_x
    tr["analytic_re_a"] = float((2 * eps_x / C.KAPPA_A) * (1 - np.exp(-C.KAPPA_A * tau_us / 2)))
    tr["pump_on"] = bool(pump_on)
    if t_eval <= 0:
        return tr
    H2, j2, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    t2 = jnp.linspace(0.0, t_eval, 301)
    res2 = _solve(H2, j2, res.final_state, t2, extra)
    return _concat(tr, _unpack(res2, t2))


def run_biased(Na, Nb, alpha, ratios, t_off, t_eval, drive="x"):
    """Method (iii): stabilization on, eps_x = r g2 for t_off, then the drive off.

    drive='z' is the forbidden eps(a+a†) demo. It is not a preparation method.
    """
    ratios = np.atleast_1d(np.asarray(ratios, dtype=float))
    amps = jnp.asarray(ratios * C.G2)
    if drive == "x":
        H1, jumps, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_x=amps)
    elif drive == "z":
        H1, jumps, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=amps)
    else:
        raise ValueError(f"drive must be 'x' or 'z', got {drive!r}")
    extra = metrics_extra(Na, Nb, alpha)
    n1 = int(round(t_off / 0.01)) + 1
    t1 = jnp.linspace(0.0, t_off, n1)
    res1 = _solve(H1, jumps, vacuum2(Na, Nb), t1, extra)
    H2, j2, _ = two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    n2 = int(round((t_eval - t_off) / 0.01)) + 1
    t2 = jnp.linspace(t_off, t_eval, max(n2, 2))
    res2 = _solve(H2, j2, res1.final_state, t2, extra)
    out = _concat(_unpack(res1, t1), _unpack(res2, t2))
    out["ratios"] = ratios
    out["drive"] = drive
    return out


def one_mode_endpoint(protocol, Na, alpha, t_eval, tau_us=0.0, ratio=0.0, t_off=0.0, drive="x"):
    """Same protocol on the effective model. Used as a cross-check once production runs."""
    extra_ket = dq.coherent(Na, alpha).to_jax()
    Z = dq.asqarray(z_logical(Na, alpha)).to_jax()

    def extra(t, rho):
        r = rho.to_jax()
        fid = jnp.real((jnp.conj(extra_ket).T @ r @ extra_ket)[0, 0])
        p_right = (1.0 + jnp.real(jnp.trace(Z @ r))) / 2.0
        return {"fid": fid, "p_right": p_right}

    if protocol == "ideal":
        H, jumps, _ = one_mode(Na, C.KAPPA_2, alpha, C.KAPPA_A)
        res = _solve(H, jumps, dq.coherent(Na, alpha), jnp.linspace(0.0, t_eval, 2), extra)
    elif protocol == "pulse":
        eps_x = alpha / tau_us
        H, jumps, _ = one_mode(Na, 0.0, alpha, C.KAPPA_A, eps_x=eps_x)
        res = _solve(H, jumps, dq.fock(Na, 0), jnp.linspace(0.0, tau_us, 2), extra)
        H2, j2, _ = one_mode(Na, C.KAPPA_2, alpha, C.KAPPA_A)
        res = _solve(H2, j2, res.final_state, jnp.linspace(0.0, t_eval, 2), extra)
    elif protocol == "biased":
        amp = ratio * C.G2
        kw = {"eps_x": amp} if drive == "x" else {"eps_z": amp}
        H, jumps, _ = one_mode(Na, C.KAPPA_2, alpha, C.KAPPA_A, **kw)
        res = _solve(H, jumps, dq.fock(Na, 0), jnp.linspace(0.0, t_off, 2), extra)
        H2, j2, _ = one_mode(Na, C.KAPPA_2, alpha, C.KAPPA_A)
        res = _solve(H2, j2, res.final_state, jnp.linspace(t_off, t_eval, 2), extra)
    else:
        raise ValueError(protocol)
    return {"fidelity": float(np.asarray(res.extra["fid"])[-1]),
            "p_right": float(np.asarray(res.extra["p_right"])[-1])}


def main(quick=False, methods=("ideal", "pulse", "biased"), na=32, nb=12, conv=True, write_table=False):
    """Entry point. Production records were not written in the 10:45 cutoff commit.

    Passing an int as the first argument used to mean main(Na, Nb) in the intro script.
    That call is rejected so it cannot launch a 32×12 run by accident.
    """
    if not isinstance(quick, bool):
        raise TypeError("main(quick: bool, ..., na=, nb=). Intro-track main(Na, Nb) was replaced; "
                        "its numbers remain in results/task_1_3b.json.")
    if isinstance(methods, str):
        methods = tuple(s.strip() for s in methods.split(",") if s.strip())
    print(f"l3-prep main quick={quick} methods={methods} na={na} nb={nb} conv={conv} "
          f"write_table={write_table}")
    print("Production mesolve, records and figures were not run before the 10:45 EDT stop. "
          "See docs/plan/status/l3-prep.md.")
    return {"quick": quick, "methods": methods, "na": na, "nb": nb, "pranav_F_t2": PRANAV_F_T2}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    p.add_argument("--methods", default="ideal,pulse,biased")
    p.add_argument("--na", type=int, default=32)
    p.add_argument("--nb", type=int, default=12)
    p.add_argument("--no-conv", action="store_true")
    p.add_argument("--write-table", action="store_true")
    args = p.parse_args()
    main(quick=args.quick, methods=args.methods, na=args.na, nb=args.nb,
         conv=not args.no_conv, write_table=args.write_table)
