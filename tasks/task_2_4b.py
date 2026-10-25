"""Task 2.4b: readout SNR against the bit-flip rate as the Z drive grows.

The drive ε_Z(a+a†) is a Z_L rotation along the separatrix. The two one-way
flip rates stay equal. The cost that matters is Γ_X, from population that
leaves the code space, not from a tilt of the double well.
"""
import argparse
import copy
import json
import time
from pathlib import Path

import jax.numpy as jnp
import matplotlib
import numpy as np
from scipy.integrate import trapezoid

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import dynamiqs as dq

from src import config as C
from src.analysis import code_projector, fit_exp_offset
from src.convergence import convergence_block, sweep
from src.linresp import response
from src.model import coherent2, two_mode
from src.plotting import save as save_fig
from src.results import RES_DIR, record, save_arrays, std_params
from src.spectral import deflated, gamma_x, liouvillian, low_spectrum, unvec

ALPHAS = (1.0, 1.2, 1.4)
ALPHA_HI = 2.1
TS = (0.5, 1.0, 2.0)
SCRIPT = "tasks/task_2_4b.py"
_EIG_CACHE = {}
_PREP = {}

# Nb grows with |<b>_ss| = (eps/g2) / (2 alpha). Na is the eig starting point.
_TRUNC = {
    1.0: (18, ((1.0, 8), (1.5, 10), (2.0, 12), (3.0, 14))),
    1.2: (20, ((1.0, 8), (1.5, 10), (2.0, 10), (3.0, 12))),
    1.4: (22, ((1.0, 8), (1.5, 8), (2.0, 10), (3.0, 12))),
    2.1: (28, ((1.0, 8),)),
}


def _alpha_key(alpha):
    key = min(_TRUNC, key=lambda a: abs(a - float(alpha)))
    if abs(key - float(alpha)) > 1e-6:
        raise ValueError(f"alpha {alpha} is outside the 2.4b set {tuple(_TRUNC)}")
    return key


def eps_grid(alpha) -> list[float]:
    """eps_z/g2 samples. The α=2.1 row stays inside ε/g2 ≤ 1."""
    if abs(float(alpha) - ALPHA_HI) < 1e-6:
        return [0.2, 0.5, 1.0]
    _alpha_key(alpha)
    return [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]


def trunc_2_4b(alpha, x) -> tuple[int, int]:
    Na, breaks = _TRUNC[_alpha_key(alpha)]
    for limit, Nb in breaks:
        if float(x) <= limit + 1e-12:
            return Na, Nb
    return Na, breaks[-1][1]


def rid(quantity, method, alpha, x, T=None, tag=None) -> str:
    """CONTRACT §6.3 id. x uses .3g so 1.0 prints as 1 and 0.05 stays 0.05."""
    s = f"t2_4b.{quantity}.{method}.two_mode.a{float(alpha):.2f}.ez{float(x):.3g}g2"
    if T is not None:
        s += f".T{float(T):.1f}us"
    if tag:
        s += f".{tag}"
    return s


def _snr(t, delta_b, kappa_b) -> float:
    """κ_b ∫|Δ⟨b⟩|² dt. Identical to src.pulses.snr (trapezoid, not a rewrite of the physics)."""
    return float(kappa_b * trapezoid(np.abs(np.asarray(delta_b)) ** 2, np.asarray(t, dtype=float)))


def gamma_m(alpha, eps) -> float:
    """Measurement dephasing 2 ε² / (κ₂ α²), Réglade S18. eps is rad/µs."""
    return float(2.0 * eps**2 / (C.KAPPA_2 * alpha**2))


def dub_dgx(alpha, eps) -> float:
    """Dubovitskii cost in our Γ_X convention: 2 γ_m exp(-2α²)."""
    return float(2.0 * gamma_m(alpha, eps) * np.exp(-2.0 * alpha**2))


def omega_z(alpha, eps) -> float:
    """In-code Z_L rotation 4 α ε (rad/µs)."""
    return float(4.0 * alpha * eps)


def leak_pred(alpha, eps) -> float:
    """1 - exp(-δ²), δ = ε / (2 κ₂ α²), the imaginary well shift."""
    delta = eps / (2.0 * C.KAPPA_2 * alpha**2)
    return float(1.0 - np.exp(-delta**2))


def _gamma_z_one_mode(alpha):
    """2 κ_a α² coth(2α²). Index selector for the even block, not a fitted value."""
    return float(2.0 * C.KAPPA_A * alpha**2 / np.tanh(2.0 * alpha**2))


def _gamma_y_one_mode(alpha):
    coth = 1.0 / np.tanh(2.0 * alpha**2)
    return float(C.KAPPA_A * alpha**2 * (coth + 1.0))


def pick_rates(lams, rel_imag=1e-6) -> dict:
    """Γ_X is the slowest near-real decay. Γ_Z is the slowest oscillating conjugate pair.

    Eigenvalues with Re λ ≥ 0 are the deflated steady mode (or unstable junk) and are ignored.
    """
    zs = [complex(z) for z in lams if complex(z).real < 0]
    near, osc = [], []
    for z in zs:
        if abs(z.imag) <= rel_imag * abs(z):
            near.append(z)
        else:
            osc.append(z)
    gamma_x, lam_x = None, None
    if near:
        lam_x = min(near, key=abs)
        gamma_x = float(-lam_x.real)
    unused = list(osc)
    pairs = []
    while unused:
        z = unused.pop(0)
        match, best = None, None
        for w in unused:
            scale = max(abs(z), abs(w), 1e-12)
            err = abs(z.real - w.real) + abs(z.imag + w.imag)
            if err <= 1e-5 * scale and (best is None or err < best):
                best, match = err, w
        if match is not None:
            unused.remove(match)
            pairs.append(z)
    if not pairs:
        return {"gamma_x": gamma_x, "gz_re": None, "gz_im": None, "lam_x": lam_x, "lam_z": None}
    lam_z = min(pairs, key=lambda z: abs(z.real))
    return {
        "gamma_x": gamma_x,
        "gz_re": float(-lam_z.real),
        "gz_im": float(abs(lam_z.imag)),
        "lam_x": lam_x,
        "lam_z": lam_z,
    }


def _diag_at(spec, lam):
    if lam is None or not spec["lams"]:
        return {"rel_residual": None, "edge_weight": None, "cond_est": None}
    i = int(np.argmin([abs(complex(z) - complex(lam)) for z in spec["lams"]]))
    cond = spec["cond_est"][i]
    return {
        "rel_residual": float(spec["rel_residual"][i]),
        "edge_weight": float(spec["edge_weight"][i]),
        "cond_est": None if cond is None else float(cond),
    }


def _eig_once(alpha, x, Na, Nb, k):
    """One full-deflated shift-invert. Callers that only need helpers must not reach here."""
    H, jumps, _ = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=x * C.G2)
    t0 = time.perf_counter()
    spec = low_spectrum(H, jumps, Na, Nb, k=k, sector="full_deflated")
    picked = pick_rates(spec["lams"])
    dx = _diag_at(spec, picked["lam_x"])
    dz = _diag_at(spec, picked["lam_z"])
    note = ""
    if picked["gz_re"] is None:
        note = "code-space pair not identifiable: Zeno regime ends"
    return {
        "alpha": float(alpha), "x": float(x), "Na": int(Na), "Nb": int(Nb), "k": int(k),
        "gamma_x": picked["gamma_x"], "gz_re": picked["gz_re"], "gz_im": picked["gz_im"],
        "lam_x": picked["lam_x"], "lam_z": picked["lam_z"],
        **dx, "gz_rel_residual": dz["rel_residual"], "gz_edge_weight": dz["edge_weight"],
        "gz_cond_est": dz["cond_est"], "note": note, "escalated": False,
        "wall_s": time.perf_counter() - t0, "sector": "full_deflated", "sigma": 0.0,
    }


def eig_point(alpha, x, Na, Nb, k=4, escalate=True) -> dict:
    """Γ_X and the code-space pair at one (α, ε/g2, truncation).

    k=4 often misses the pair once Ω_Z reaches the buffer scale, so a miss retries k=8.
    edge_weight ≥ 1e-6 retries once at Nb+2. A second miss is recorded, not claimed.
    """
    key = (round(float(alpha), 6), round(float(x), 6), int(Na), int(Nb), int(k), bool(escalate))
    if key in _EIG_CACHE:
        return _EIG_CACHE[key]
    pt = _eig_once(alpha, x, Na, Nb, k)
    if pt["gz_re"] is None and k < 8:
        pt = _eig_once(alpha, x, Na, Nb, 8)
        pt["note"] = (pt["note"] + " retried at k=8").strip()
    if escalate and pt["edge_weight"] is not None and pt["edge_weight"] >= 1e-6:
        nxt = eig_point(alpha, x, Na, Nb + 2, k=pt["k"], escalate=False)
        nxt["escalated"] = True
        nxt["note"] = (nxt.get("note") or "") + (
            f" edge_weight {pt['edge_weight']:.3e} at Nb={int(Nb)}; reran at Nb={int(Nb) + 2}."
        )
        if nxt["edge_weight"] is not None and nxt["edge_weight"] >= 1e-6:
            nxt["note"] += " edge_weight still >= 1e-6; not claimable."
        _EIG_CACHE[key] = nxt
        return nxt
    _EIG_CACHE[key] = pt
    return pt


def _steady_state(H, jumps, Na, Nb) -> np.ndarray:
    """Solve deflated(L) vec(ρ) = η vec(I), then normalize the trace.

    Deflation moves the steady eigenvalue from 0 to η D, so the linear system is nonsingular.
    """
    from scipy.sparse.linalg import spsolve

    D = Na * Nb
    eta = 1.0
    A = deflated(liouvillian(H, jumps), D, eta)
    rhs = np.zeros(D * D, dtype=np.complex128)
    rhs[np.arange(D) * (D + 1)] = eta
    rho = unvec(spsolve(A, rhs), D)
    rho = rho / np.trace(rho)
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho)


def _expects(res, n_x, n_ops):
    """Return expectations as (n_x, n_ops, n_t). dynamiqs batches ahead of the operator axis."""
    e = np.asarray(res.expects)
    if e.ndim == 2 and e.shape[0] == n_ops:
        e = e[None, ...]
    if e.ndim == 3 and e.shape[0] == n_ops and e.shape[1] == n_x:
        e = np.transpose(e, (1, 0, 2))
    if e.shape[:2] != (n_x, n_ops):
        raise RuntimeError(f"expects shape {np.asarray(res.expects).shape}, wanted ({n_x}, {n_ops}, n_t)")
    return e


def _prepare(alpha, Na, Nb, t_prep):
    key = (round(float(alpha), 6), int(Na), int(Nb), round(float(t_prep), 6))
    if key in _PREP:
        return _PREP[key]
    H, jumps, (_a, b) = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A)
    proj = dq.tensor(code_projector(Na, alpha), dq.eye(Nb))
    states, leak0 = {}, {}
    for s in (+1.0, -1.0):
        res = dq.mesolve(
            H, jumps, coherent2(Na, Nb, s * alpha), [0.0, t_prep],
            method=C.METHOD, exp_ops=[b, proj], save_states=False,
        )
        states[s] = res.final_state
        e = _expects(res, 1, 2)
        leak0[s] = float(1.0 - np.real(e[0, 1, -1]))
    out = {"states": states, "leak0": leak0, "proj": proj}
    _PREP[key] = out
    return out


def _late_mean(t, y, t0=1.5, t1=2.0):
    m = (t >= t0 - 1e-12) & (t <= t1 + 1e-12)
    if not np.any(m):
        # --quick and the 12×4 symmetry test stop before 1.5 µs.
        m = t >= (t[-1] - 0.2 * max(t[-1] - t[0], 1e-9))
    return float(np.mean(y[m]))


def _lin_delta(t, eps, alpha):
    """Δb = b(+α) − b(−α) = 2 b(+α) for this linearization (flipping the well flips b)."""
    _da, b = response(np.full(np.shape(t), float(eps)), t, C.G2, C.KAPPA_B, alpha, well=+1)
    return 2.0 * b


def td_alpha(alpha, xs, Na, Nb, t_prep=3.0, t_end=2.0, dt=0.002) -> dict:
    """Prepare both wells with ε_Z = 0, then switch a batch of readout drives on.

    Δ⟨b⟩ cancels the shared κ_a offset. SNR is the heterodyne integral of that difference.
    """
    xs = [float(x) for x in xs]
    prep = _prepare(alpha, Na, Nb, t_prep)
    _H, jumps, (_a, b) = two_mode(
        Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=jnp.asarray(xs) * C.G2,
    )
    # Rebuild H bound to the same jumps; two_mode above is the driven generator.
    H = _H
    proj = prep["proj"]
    t = np.arange(0.0, t_end + dt / 2.0, dt)
    saved = {}
    for s in (+1.0, -1.0):
        res = dq.mesolve(
            H, jumps, prep["states"][s], t, method=C.METHOD,
            exp_ops=[b, proj], save_states=False,
        )
        saved[s] = _expects(res, len(xs), 2)
    b_p, b_m = saved[+1.0][:, 0, :], saved[-1.0][:, 0, :]
    leak_p = 1.0 - np.real(saved[+1.0][:, 1, :])
    leak_m = 1.0 - np.real(saved[-1.0][:, 1, :])
    delta = b_p - b_m
    snr, snr_lin, leakage = {}, {}, []
    for i, x in enumerate(xs):
        snr[x] = {}
        snr_lin[x] = {}
        dlin = _lin_delta(t, x * C.G2, alpha)
        for T in TS:
            if t[-1] + 1e-9 < T:
                continue
            m = t <= T + 1e-12
            snr[x][T] = _snr(t[m], delta[i, m], C.KAPPA_B)
            snr_lin[x][T] = _snr(t[m], dlin[m], C.KAPPA_B)
        leakage.append(_late_mean(t, leak_p[i]))
    return {
        "t": t, "xs": xs, "b_plus": b_p, "b_minus": b_m, "delta_b": delta,
        "leak_plus": leak_p, "leak_minus": leak_m, "snr": snr, "snr_lin": snr_lin,
        "leakage": leakage, "leakage0": float(prep["leak0"][+1.0]),
        "sym_max": float(np.max(np.abs(b_m + np.conj(b_p)))),
        "leak_well_diff": float(np.max(np.abs(leak_p - leak_m))),
    }


def _cross(method, value, ref, tol, ref_id=None):
    ref, value, tol = float(ref), float(value), float(tol)
    denom = abs(ref) if abs(ref) > 0 else 1.0
    rel = abs(value - ref) / denom
    return {
        "method": method, "ref_id": ref_id, "value": ref,
        "rel_diff": rel, "tol": tol, "agree": bool(rel <= tol),
    }


def _rec_dir(quick):
    return RES_DIR / "quick" / "records" if quick else RES_DIR / "records"


def _have(id, quick):
    return (_rec_dir(quick) / f"{id}.json").is_file()


def _load(id, quick):
    path = _rec_dir(quick) / f"{id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def _accepted(rel, edge):
    return rel is not None and edge is not None and rel < 1e-4 and edge < 1e-6


def _numerics(pt, extra=None):
    num = {
        "rel_residual": pt["rel_residual"], "edge_weight": pt["edge_weight"],
        "cond_est": pt["cond_est"], "sector": "full_deflated", "sigma": 0.0, "k": pt["k"],
    }
    if extra:
        num.update(extra)
    return num


def snr_ids_ok():
    """CONTRACT writes T{T:.1f}us, but results.ID_RE is lowercase. Do not rewrite the tag."""
    from src.results import _check_id

    try:
        _check_id("t2_4b.snr.td.two_mode.a1.00.ez1g2.T1.0us")
    except ValueError:
        return False
    return True


def _write(id, quick, force, **kwargs):
    if _have(id, quick) and not force:
        print("skip", id)
        return None
    return record(id, script=SCRIPT, quick=quick, **kwargs)


def _rel_tol(alpha):
    return 1e-2 if abs(alpha - ALPHA_HI) < 1e-6 else 1e-3


def _gamma_row(alpha, x, Na, Nb):
    pt = eig_point(alpha, x, int(Na), int(Nb), escalate=False)
    if pt["gamma_x"] is None:
        raise RuntimeError(f"no Γ_X at alpha={alpha}, eps/g2={x}, {Na}x{Nb}")
    return {"gamma_x": float(pt["gamma_x"])}


def _sweeps_gamma(alpha, x, Na, Nb, tier):
    """Tier 1 sweeps Na and Nb. Tier 2 sweeps Na only; Nb is judged by edge_weight."""
    rel = _rel_tol(alpha)
    na_rows = sweep(
        lambda **kw: _gamma_row(alpha, x, kw["Na"], kw["Nb"]),
        "Na", [Na, Na + 4], {"Nb": Nb},
    )
    sweeps = {"Na": ({"Nb": Nb, "eps_over_g2": float(x)}, na_rows)}
    if tier == 1:
        nb_rows = sweep(
            lambda **kw: _gamma_row(alpha, x, kw["Na"], kw["Nb"]),
            "Nb", [Nb, Nb + 2], {"Na": Na},
        )
        sweeps["Nb"] = ({"Na": Na, "eps_over_g2": float(x)}, nb_rows)
    return convergence_block(sweeps, "gamma_x", rel, {"Na": Na, "Nb": Nb})


def _baselines(alpha, Na, Nb):
    """Odd-sector Γ_X, even-sector X_L, odd-sector Y_L, all at ε = 0.

    low_spectrum drops the deflated eigenvalue, so X_L is the even rate nearest
    2 κ_a α² coth(2α²) (rates[0] in d5d9709). The brief's rates[1] assumed a
    retained null vector. Y_L is the odd rate nearest κ_a α² (coth+1), which is rates[1].
    """
    H, jumps, _ = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A)
    odd_g = gamma_x(H, jumps, Na, Nb)
    even = low_spectrum(H, jumps, Na, Nb, k=2, sector="even")
    odd = low_spectrum(H, jumps, Na, Nb, k=2, sector="odd")
    iz = int(np.argmin([abs(float(r) - _gamma_z_one_mode(alpha)) for r in even["rates"]]))
    iy = int(np.argmin([abs(float(r) - _gamma_y_one_mode(alpha)) for r in odd["rates"]]))
    return {
        "gx_odd": float(odd_g["gamma_x"]),
        "gx_odd_num": odd_g["numerics"],
        "gz0": float(even["rates"][iz]),
        "gy0": float(odd["rates"][iy]),
        "gz_index": iz, "gy_index": iy,
        "even_diag": _diag_at(even, even["lams"][iz]),
        "even_rates": [float(r) for r in even["rates"]],
        "odd_rates": [float(r) for r in odd["rates"]],
    }


def _tier_xs(alpha, tier):
    grid = eps_grid(alpha)
    if tier == 1:
        xs = [0.0] + [x for x in grid if x <= 1.0 + 1e-12]
        donors = [0.0, 1.0]
    else:
        xs = [x for x in grid if x >= 1.5 - 1e-12]
        donors = [3.0]
    donors = [d for d in donors if any(abs(d - x) < 1e-12 for x in xs)]
    rest = [x for x in xs if all(abs(x - d) > 1e-12 for d in donors)]
    return donors + rest, donors


def _donor(x, donors):
    above = [d for d in donors if d + 1e-12 >= x]
    return min(above, key=lambda d: d - x) if above else max(donors)


def _s18(gz, gx, base, alpha, eps):
    gm = gamma_m(alpha, eps)
    half = 0.5 * (base["gz0"] + base["gy0"])
    d_corr = gz - half - 0.5 * (gx - base["gx0"])
    d_raw = gz - base["gz0"]
    return gm, d_corr, d_raw, half + gm + 0.5 * (gx - base["gx0"])


def run_eig(alpha, tier, quick, force):
    """Write one Γ_X and one Γ_Z record per grid point, resuming past existing ids."""
    if quick:
        return _run_eig_quick(force)
    alpha = float(alpha)
    xs, donors = _tier_xs(alpha, tier)
    conv = {}
    base = None
    for x in xs:
        Na, Nb = trunc_2_4b(alpha, x)
        gx_id = rid("gamma_x", "eig", alpha, x)
        if _have(gx_id, quick) and not force:
            print("skip", gx_id)
            rec = _load(gx_id, quick)
            if rec and rec.get("convergence"):
                conv[x] = rec["convergence"]
            if abs(x) < 1e-12 and rec is not None:
                gz = _load(rid("gamma_z", "eig", alpha, 0.0), quick)
                base = {
                    "gx0": rec["value"],
                    "gz0": None if gz is None else gz["value"],
                    "gy0": None if gz is None else (gz.get("numerics") or {}).get("gamma_y0"),
                    "gx_odd": rec["value"],
                }
            continue
        if x in donors or abs(x) < 1e-12:
            print(f"sweep alpha={alpha} eps/g2={x} at {Na}x{Nb}")
            conv[x] = _sweeps_gamma(alpha, x, Na, Nb, 1 if abs(x) < 1e-12 else tier)
        donor = _donor(x, donors if donors else [x])
        block = copy.deepcopy(conv.get(donor))
        note_conv = ""
        if donor != x and block is not None:
            note_conv = f" convergence reused from eps/g2={donor:g} (nearest checked at or above, same alpha)."
        if abs(x) < 1e-12:
            base = _baselines(alpha, Na, Nb)
            base["gx0"] = None  # filled from the full-deflated point below
        pt = eig_point(alpha, x, Na, Nb, escalate=True)
        if pt["Nb"] != Nb:
            note_conv += f" reported truncation is {pt['Na']}x{pt['Nb']} after the edge rerun."
            if block is not None:
                block["converged"] = False
        if pt["gamma_x"] is None:
            print("no gamma_x", gx_id, pt["note"])
            continue
        if base is None:
            loaded = _load(rid("gamma_z", "eig", alpha, 0.0), quick)
            gx_rec = _load(rid("gamma_x", "eig", alpha, 0.0), quick)
            if loaded and gx_rec and "gamma_y0" in (loaded.get("numerics") or {}):
                base = {
                    "gx0": gx_rec["value"], "gz0": loaded["value"],
                    "gy0": loaded["numerics"]["gamma_y0"], "gx_odd": None,
                }
        if abs(x) < 1e-12 and base is not None:
            base["gx0"] = pt["gamma_x"]
        eps = x * C.G2
        ccs = []
        notes = (pt["note"] + note_conv).strip()
        if abs(x) < 1e-12 and base is not None:
            ccs.append(_cross("odd_sector_gamma_x", pt["gamma_x"], base["gx_odd"], 1e-6))
            notes += (
                f" even rates={base['even_rates']} X_L index {base['gz_index']}; "
                f"odd rates={base['odd_rates']} Y_L index {base['gy_index']}."
            )
        elif base is not None and base.get("gx0") is not None:
            ref = base["gx0"] + dub_dgx(alpha, eps)
            ccs.append(_cross("dubovitskii_overlay", pt["gamma_x"], ref, 0.3))
        if abs(alpha - 1.2) < 1e-9 and abs(x - 0.5) < 1e-12:
            neg = eig_point(alpha, -0.5, pt["Na"], pt["Nb"], escalate=False)
            if neg["gamma_x"] is not None:
                ccs.append(_cross("parity_mirror_eps", pt["gamma_x"], neg["gamma_x"], 1e-8))
        td_id = rid("gamma_x", "td", alpha, x)
        td_rec = _load(td_id, quick)
        if td_rec is not None:
            ccs.append(_cross("time_domain_fit", pt["gamma_x"], td_rec["value"], 0.02, td_id))
        if not ccs:
            # Every eigen record needs a stated check. The overlay is the drive cost, tol 0.3.
            ccs.append(_cross("dubovitskii_overlay", pt["gamma_x"], dub_dgx(alpha, eps), 0.3))
        claim = _accepted(pt["rel_residual"], pt["edge_weight"])
        if block is not None and not claim:
            block["converged"] = False
            notes += " acceptance failed (rel_residual or edge_weight)."
        _write(
            gx_id, quick, force, task="2.4b", quantity="gamma_x", value=pt["gamma_x"],
            units="1/us", method="liouvillian_eig_full_deflated",
            params=std_params(alpha=alpha, eps_z=eps),
            truncation={"Na": pt["Na"], "Nb": pt["Nb"]}, convergence=block,
            numerics=_numerics(pt), cross_check=ccs, wall_s=pt["wall_s"],
            notes=notes or None,
            artifacts={"figure": "figures/task_2_4b_tradeoff.png", "arrays": "results/arrays/t2_4b.grid.npz"},
        )
        gz_id = rid("gamma_z", "eig", alpha, x)
        if pt["gz_re"] is None or (base is None and abs(x) > 1e-12):
            print("no gamma_z record", gz_id, pt["note"])
            continue
        if abs(x) < 1e-12:
            gz_value = base["gz0"]
            gz_im = 0.0
            sector_note = "value is the even-sector X_L rate"
            gz_num = {
                "rel_residual": base["even_diag"]["rel_residual"],
                "edge_weight": base["even_diag"]["edge_weight"],
                "cond_est": base["even_diag"]["cond_est"],
                "sector": "even", "sigma": 0.0, "k": 2,
                "gamma_y0": base["gy0"], "gz_im": 0.0, "omega_z": 0.0,
                "one_mode_gamma_z": _gamma_z_one_mode(alpha),
            }
            pred = 0.5 * (base["gz0"] + base["gy0"])
            gz_cc = [_cross("S18_corrected", gz_value, pred, 0.10)]
        else:
            gm, d_corr, d_raw, pred = _s18(pt["gz_re"], pt["gamma_x"], base, alpha, eps)
            gz_value = pt["gz_re"]
            oz = omega_z(alpha, eps)
            gz_num = _numerics(pt, {
                "gz_im": pt["gz_im"], "omega_z": oz,
                "dGZ_corr": d_corr, "dGZ_raw": d_raw, "gamma_m": gm,
                "dGZ_corr_over_gamma_m": None if gm == 0 else d_corr / gm,
                "dGZ_raw_over_gamma_m": None if gm == 0 else d_raw / gm,
                "gz_im_over_omega_z": None if oz == 0 else pt["gz_im"] / oz,
                "gz_rel_residual": pt["gz_rel_residual"], "gz_edge_weight": pt["gz_edge_weight"],
            })
            gz_cc = [_cross("S18_corrected", gz_value, pred, 0.10)]
            sector_note = pt["note"]
        _write(
            gz_id, quick, force, task="2.4b", quantity="gamma_z", value=gz_value,
            units="1/us", method="liouvillian_eig_full_deflated" if abs(x) > 1e-12 else "liouvillian_eig_even",
            params=std_params(alpha=alpha, eps_z=eps),
            truncation={"Na": pt["Na"], "Nb": pt["Nb"]}, convergence=block,
            numerics=gz_num, cross_check=gz_cc, wall_s=pt["wall_s"],
            notes=(sector_note + note_conv).strip() or None,
        )


def _run_eig_quick(force):
    """12×4 smoke. Not a production eigenvalue and not a substitute for tier 1."""
    alpha, x, Na, Nb = 1.0, 0.1, 12, 4
    pt = eig_point(alpha, x, Na, Nb, k=4, escalate=False)
    if pt["gamma_x"] is None:
        print("quick eig found no gamma_x")
        return
    _write(
        rid("gamma_x", "eig", alpha, x), True, force, task="2.4b", quantity="gamma_x",
        value=pt["gamma_x"], units="1/us", method="liouvillian_eig_full_deflated",
        params=std_params(alpha=alpha, eps_z=x * C.G2), truncation={"Na": Na, "Nb": Nb},
        numerics=_numerics(pt),
        cross_check=[_cross("dubovitskii_overlay", pt["gamma_x"], dub_dgx(alpha, x * C.G2), 0.3)],
        wall_s=pt["wall_s"], notes="quick 12x4 smoke; " + pt["note"], convergence=None,
    )


def _td_targets(quick, alpha):
    if quick:
        return [(1.0, [0.1, 0.5], 12, 4, 1.0, 1.0, (0.5, 1.0))]
    if alpha is None:
        alphas = (*ALPHAS, ALPHA_HI)
    else:
        alphas = (float(alpha),)
    jobs = []
    for a in alphas:
        Na, _ = trunc_2_4b(a, 0.0)
        xs = eps_grid(a)
        low = [x for x in xs if x <= 1.0 + 1e-12]
        high = [x for x in xs if x >= 1.5 - 1e-12]
        if low:
            jobs.append((a, low, Na, 8, 3.0, 2.0, TS))
        if high:
            _na, nb = trunc_2_4b(a, max(high))
            jobs.append((a, high, Na, nb, 3.0, 2.0, TS))
    return jobs


def _cache_path(quick):
    folder = RES_DIR / "quick" / "arrays" if quick else RES_DIR / "arrays"
    return folder / "t2_4b.td.npz"


def _store_td(rows, quick):
    path = _cache_path(quick)
    old = {}
    if path.is_file():
        with np.load(path) as z:
            for i, (a, x) in enumerate(zip(z["alpha"], z["eps_over_g2"])):
                old[(round(float(a), 6), round(float(x), 6))] = {k: z[k][i] for k in z.files}
    for row in rows:
        old[(round(row["alpha"], 6), round(row["eps_over_g2"], 6))] = row
    keys = sorted(old)
    cols = {name: [] for name in (
        "alpha", "eps_over_g2", "Na", "Nb", "snr_T0.5", "snr_T1.0", "snr_T2.0",
        "snr_lin_T0.5", "snr_lin_T1.0", "snr_lin_T2.0", "snr_rate", "leakage", "leakage0",
        "sym_max", "leak_well_diff",
    )}
    for key in keys:
        row = old[key]
        for name in cols:
            cols[name].append(row[name])
    save_arrays("t2_4b.td", quick=quick, **{k: np.asarray(v, dtype=float) for k, v in cols.items()})


def _td_row(alpha, x, Na, Nb, out, index, leak0):
    snr = out["snr"].get(x, {})
    snr_lin = out["snr_lin"].get(x, {})

    def grab(store, T):
        return store[T] if T in store else np.nan

    s2, s1 = grab(snr, 2.0), grab(snr, 1.0)
    return {
        "alpha": float(alpha), "eps_over_g2": float(x), "Na": Na, "Nb": Nb,
        "snr_T0.5": grab(snr, 0.5), "snr_T1.0": s1, "snr_T2.0": s2,
        "snr_lin_T0.5": grab(snr_lin, 0.5), "snr_lin_T1.0": grab(snr_lin, 1.0),
        "snr_lin_T2.0": grab(snr_lin, 2.0),
        "snr_rate": (s2 - s1) if np.isfinite(s2) and np.isfinite(s1) else np.nan,
        "leakage": out["leakage"][index], "leakage0": leak0,
        "sym_max": out["sym_max"], "leak_well_diff": out["leak_well_diff"],
    }


def _write_td_records(row, quick, force, convergence, conv_note):
    alpha, x = row["alpha"], row["eps_over_g2"]
    eps = x * C.G2
    trunc = {"Na": int(row["Na"]), "Nb": int(row["Nb"])}
    notes = (
        f"sym_max={row['sym_max']:.3e}; leak_well_diff={row['leak_well_diff']:.3e}. " + conv_note
    ).strip()
    pred = row["leakage0"] + leak_pred(alpha, eps)
    _write(
        rid("leakage", "td", alpha, x), quick, force, task="2.4b", quantity="leakage",
        value=float(row["leakage"]), units="probability", method="two_mode_mesolve",
        params=std_params(alpha=alpha, eps_z=eps), truncation=trunc, convergence=convergence,
        cross_check=[_cross("analytic_displacement", row["leakage"], pred, 0.2)],
        notes=notes,
    )
    if not snr_ids_ok():
        print("SNR json records blocked: uppercase T in the CONTRACT tag. Values stay in t2_4b.td.npz.")
        return
    for T, key, lin_key in ((0.5, "snr_T0.5", "snr_lin_T0.5"), (1.0, "snr_T1.0", "snr_lin_T1.0"),
                            (2.0, "snr_T2.0", "snr_lin_T2.0")):
        if not np.isfinite(row[key]):
            continue
        _write(
            rid("snr", "td", alpha, x, T=T), quick, force, task="2.4b", quantity="snr",
            value=float(row[key]), units="1", method="two_mode_mesolve_trapz",
            params=std_params(alpha=alpha, eps_z=eps, T_us=T), truncation=trunc,
            convergence=convergence,
            cross_check=[_cross("linear_response", row[key], row[lin_key], 0.10)],
            notes=notes,
        )


def _check_td(alpha, x, Na, Nb, t_prep, t_end, base_row):
    """Rerun the largest drive of a batch at Na+4 and Nb+2. Tolerances are the brief's, not retuned."""
    rows = [("Na", Na + 4, Nb), ("Nb", Na, Nb + 2), ("base", Na, Nb)]
    snr_rows, leak_rows = [], []
    out_rows = {}
    for axis, na, nb in rows:
        if axis == "base":
            out_rows[axis] = base_row
            continue
        out = td_alpha(alpha, [x], na, nb, t_prep=t_prep, t_end=t_end)
        out_rows[axis] = _td_row(alpha, x, na, nb, out, 0, out["leakage0"])
    for axis, na, nb in rows:
        snr_rows.append({"Na": na, "Nb": nb, "snr": out_rows[axis if axis != "base" else "base"]["snr_T1.0"]})
        leak_rows.append({"Na": na, "Nb": nb, "leakage": out_rows[axis if axis != "base" else "base"]["leakage"]})
    # convergence_block wants one axis at a time and two values. Build Na and Nb pairs against the base.
    def pair(axis, key, src):
        a = next(r for r in src if (r["Na"], r["Nb"]) == ((Na + 4, Nb) if axis == "Na" else (Na, Nb + 2)))
        b = next(r for r in src if (r["Na"], r["Nb"]) == (Na, Nb))
        rows_ = sorted([a, b], key=lambda r: r[axis])
        return rows_

    snr_block = convergence_block(
        {
            "Na": ({"Nb": Nb}, pair("Na", "snr", snr_rows)),
            "Nb": ({"Na": Na}, pair("Nb", "snr", snr_rows)),
        },
        "snr", 1e-3, {"Na": Na, "Nb": Nb},
    )
    leak_block = convergence_block(
        {
            "Na": ({"Nb": Nb}, pair("Na", "leakage", leak_rows)),
            "Nb": ({"Na": Na}, pair("Nb", "leakage", leak_rows)),
        },
        "leakage", 1e-2, {"Na": Na, "Nb": Nb},
    )
    return snr_block, leak_block


def run_td(quick, force, alpha=None):
    rows = []
    for a, xs, Na, Nb, t_prep, t_end, _Ts in _td_targets(quick, alpha):
        print(f"td alpha={a} eps/g2={xs} {Na}x{Nb} t_prep={t_prep} t_end={t_end}")
        t0 = time.perf_counter()
        out = td_alpha(a, xs, Na, Nb, t_prep=t_prep, t_end=t_end)
        print(f"  sym_max={out['sym_max']:.3e} leak_well_diff={out['leak_well_diff']:.3e} "
              f"wall_s={time.perf_counter() - t0:.1f}")
        batch = []
        for i, x in enumerate(xs):
            batch.append(_td_row(a, x, Na, Nb, out, i, out["leakage0"]))
        zero = {
            "alpha": float(a), "eps_over_g2": 0.0, "Na": Na, "Nb": Nb,
            "snr_T0.5": 0.0, "snr_T1.0": 0.0, "snr_T2.0": 0.0,
            "snr_lin_T0.5": 0.0, "snr_lin_T1.0": 0.0, "snr_lin_T2.0": 0.0,
            "snr_rate": 0.0, "leakage": out["leakage0"], "leakage0": out["leakage0"],
            "sym_max": 0.0, "leak_well_diff": 0.0,
        }
        largest = max(batch, key=lambda r: r["eps_over_g2"])
        snr_block, leak_block = _check_td(a, largest["eps_over_g2"], Na, Nb, t_prep, t_end, largest)
        for row in [zero] + batch:
            donor = row["eps_over_g2"] == largest["eps_over_g2"] or row["eps_over_g2"] == 0.0
            note = "truncation check at this drive." if row["eps_over_g2"] == largest["eps_over_g2"] else (
                "eps=0 is the preparation endpoint; truncation check is on the largest drive of this batch."
                if row["eps_over_g2"] == 0.0 else
                f"convergence reused from eps/g2={largest['eps_over_g2']:g}, the largest drive of this batch."
            )
            _write_td_records(row, quick, force, leak_block if donor or row["eps_over_g2"] != 0 else copy.deepcopy(leak_block), note)
            rows.append(row)
    if rows:
        _store_td(rows, quick)


def run_tdgx(quick, force):
    """Time-domain Γ_X at α=1, ε/g2 in {0.1, 0.3}. The fit window starts after the 3 µs ringdown."""
    alpha = 1.0
    xs = (0.1, 0.3)
    if quick:
        sizes, fit_from = ((12, 4),), 0.4
    else:
        sizes, fit_from = ((16, 6), (20, 6)), 3.0
    fits = {}
    for x in xs:
        for Na, Nb in sizes:
            H0, jumps0, _ = two_mode(Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A)
            gx0 = gamma_x(H0, jumps0, Na, Nb)["gamma_x"]
            W = min(100.0, 4.0 / (gx0 + dub_dgx(alpha, x * C.G2)))
            if quick:
                W = min(W, 1.0)
            prep = _prepare(alpha, Na, Nb, 0.5 if quick else 3.0)
            H, jumps, (a, _b) = two_mode(
                Na, Nb, C.G2, alpha**2 * C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=x * C.G2,
            )
            t_end = fit_from + W
            t = np.arange(0.0, t_end + 0.025, 0.05 if not quick else 0.02)
            res = dq.mesolve(
                H, jumps, prep["states"][+1.0], t, method=C.METHOD_LONG,
                exp_ops=[a], save_states=False,
            )
            e = _expects(res, 1, 1)[0, 0]
            m = (t >= fit_from) & (t <= fit_from + W + 1e-12)
            y = np.real(e[m])
            fit = fit_exp_offset(t[m], y, p0=(gx0 + dub_dgx(alpha, x * C.G2), y[0] - y[-1], y[-1]))
            fits[(x, Na, Nb)] = fit
            print(f"tdgx eps/g2={x} {Na}x{Nb} gamma={fit['gamma']:.6e} window={W:.2f}")
        small, big = sizes[0], sizes[-1]
        fit_s, fit_b = fits[(x, *small)], fits[(x, *big)]
        ccs = []
        if big != small:
            ccs.append(_cross("truncation_20x6", fit_s["gamma"], fit_b["gamma"], 0.02))
        eig_id = rid("gamma_x", "eig", alpha, x)
        eig_rec = _load(eig_id, quick)
        if eig_rec is not None:
            ccs.append(_cross("liouvillian_eig", fit_s["gamma"], eig_rec["value"], 0.02, eig_id))
        if not ccs:
            ccs.append(_cross(
                "dubovitskii_window", fit_s["gamma"],
                gx0 + dub_dgx(alpha, x * C.G2), 0.3,
            ))
        block = None
        if big != small:
            block = convergence_block(
                {"Na": ({"Nb": small[1]}, [
                    {"Na": small[0], "gamma_x": fit_s["gamma"]},
                    {"Na": big[0], "gamma_x": fit_b["gamma"]},
                ])},
                "gamma_x", 0.02, {"Na": small[0]},
            )
        _write(
            rid("gamma_x", "td", alpha, x), quick, force, task="2.4b", quantity="gamma_x",
            value=fit_s["gamma"], units="1/us", method="mesolve_re_a_fit",
            params=std_params(alpha=alpha, eps_z=x * C.G2),
            truncation={"Na": small[0], "Nb": small[1]}, uncertainty=fit_s["gamma_stderr"],
            convergence=block, cross_check=ccs,
            numerics={
                "fit_window_us": [fit_from, fit_from + W],
                "gamma_stderr": fit_s["gamma_stderr"],
                "rel_rms_residual": fit_s["rel_rms_residual"],
            },
            notes=None if not quick else "quick smoke, not the production window",
        )


def _grid_points():
    pts = []
    for alpha in (*ALPHAS, ALPHA_HI):
        for x in [0.0, *eps_grid(alpha)]:
            pts.append((float(alpha), float(x)))
    return pts


def _findings(rows):
    lines = ["| alpha | eps/g2 | GX/GX0 | dGX/Dub | dGZ_corr/gm | gz_im/OZ | snr_rate/dGX | e^{2a^2} | (L-L0)/leak_pred |",
             "|---|---|---|---|---|---|---|---|---|"]
    by = {(round(r["alpha"], 6), round(r["eps_over_g2"], 6)): r for r in rows}
    for alpha in (*ALPHAS, ALPHA_HI):
        base = by.get((round(alpha, 6), 0.0))
        gx0 = None if base is None else base.get("gamma_x")
        for x in (0.1, 0.3, 1.0):
            r = by.get((round(alpha, 6), round(x, 6)))
            if r is None:
                lines.append(f"| {alpha:.2f} | {x:g} | pending | | | | | {np.exp(2 * alpha**2):.4g} | |")
                continue
            eps = x * C.G2
            gx, gz = r.get("gamma_x"), r.get("gamma_z_re")
            ratio = (gx / gx0) if gx is not None and gx0 not in (None, 0) and np.isfinite(gx) else np.nan
            dub = dub_dgx(alpha, eps)
            dgz = r.get("dGZ_corr")
            gm = gamma_m(alpha, eps)
            oz = omega_z(alpha, eps)
            dG = (gx - gx0) if gx is not None and gx0 is not None else np.nan
            snr = r.get("snr_rate")
            leak = r.get("leakage")
            leak0 = r.get("leakage0")
            pred = leak_pred(alpha, eps)

            def fmt(v):
                return "pending" if v is None or not np.isfinite(v) else f"{v:.4g}"

            lines.append(
                f"| {alpha:.2f} | {x:g} | {fmt(ratio)} | {fmt((gx - gx0) / dub if np.isfinite(dG) and dub else np.nan)} | "
                f"{fmt(dgz / gm if dgz is not None and gm else np.nan)} | "
                f"{fmt((r.get('gamma_z_im') or np.nan) / oz if oz else np.nan)} | "
                f"{fmt(snr / dG if snr is not None and np.isfinite(dG) and dG else np.nan)} | "
                f"{np.exp(2 * alpha**2):.4g} | "
                f"{fmt((leak - leak0) / pred if leak is not None and leak0 is not None and pred else np.nan)} |"
            )
    return "\n".join(lines)


def run_assemble(quick):
    """37-row grid. Missing eigen or SNR entries stay NaN so a partial run is still readable."""
    pts = _grid_points()
    if len(pts) != 37:
        raise RuntimeError(f"grid has {len(pts)} rows, expected 37")
    td = {}
    path = _cache_path(quick)
    if path.is_file():
        with np.load(path) as z:
            for i in range(len(z["alpha"])):
                td[(round(float(z["alpha"][i]), 6), round(float(z["eps_over_g2"][i]), 6))] = {
                    k: float(z[k][i]) for k in z.files
                }
    rows = []
    pending = []
    for alpha, x in pts:
        gx = _load(rid("gamma_x", "eig", alpha, x), quick)
        gz = _load(rid("gamma_z", "eig", alpha, x), quick)
        td_row = td.get((round(alpha, 6), round(x, 6)), {})
        snr = {}
        for T, key in ((0.5, "snr_T0.5"), (1.0, "snr_T1.0"), (2.0, "snr_T2.0")):
            rec = _load(rid("snr", "td", alpha, x, T=T), quick) if snr_ids_ok() else None
            snr[key] = rec["value"] if rec else td_row.get(key, np.nan)
        gx_v = gx["value"] if gx else np.nan
        num = (gx or {}).get("numerics") or {}
        conv = (gx or {}).get("convergence") or {}
        ok = bool(gx) and bool(conv.get("converged")) and _accepted(num.get("rel_residual"), num.get("edge_weight"))
        if not np.isfinite(gx_v):
            pending.append(f"a{alpha:.2f} ez{x:.3g}g2")
        rows.append({
            "alpha": alpha, "eps_over_g2": x, "gamma_x": gx_v,
            "gamma_z_re": gz["value"] if gz else np.nan,
            "gamma_z_im": np.nan if not gz else (gz.get("numerics") or {}).get("gz_im", np.nan),
            "snr_T0.5": snr["snr_T0.5"], "snr_T1.0": snr["snr_T1.0"], "snr_T2.0": snr["snr_T2.0"],
            "snr_rate": td_row.get("snr_rate", np.nan),
            "leakage": td_row.get("leakage", np.nan), "leakage0": td_row.get("leakage0", np.nan),
            "dGZ_corr": None if not gz else (gz.get("numerics") or {}).get("dGZ_corr"),
            "gamma_x_ok": ok,
        })
    gx0 = {}
    for r in rows:
        if abs(r["eps_over_g2"]) < 1e-12 and np.isfinite(r["gamma_x"]):
            gx0[round(r["alpha"], 6)] = r["gamma_x"]
    cols = {
        "alpha": [r["alpha"] for r in rows],
        "eps_over_g2": [r["eps_over_g2"] for r in rows],
        "gamma_x": [r["gamma_x"] for r in rows],
        "gamma_z_re": [r["gamma_z_re"] for r in rows],
        "snr_T0.5": [r["snr_T0.5"] for r in rows],
        "snr_T1.0": [r["snr_T1.0"] for r in rows],
        "snr_T2.0": [r["snr_T2.0"] for r in rows],
        "leakage": [r["leakage"] for r in rows],
        "gamma_x_rel": [r["gamma_x"] / gx0[round(r["alpha"], 6)]
                        if round(r["alpha"], 6) in gx0 and np.isfinite(r["gamma_x"]) else np.nan for r in rows],
        "gamma_z_im": [np.nan if r["gamma_z_im"] is None else r["gamma_z_im"] for r in rows],
        "snr_rate": [r["snr_rate"] for r in rows],
        "gamma_x_ok": [bool(r["gamma_x_ok"]) for r in rows],
    }
    save_arrays("t2_4b.grid", quick=quick, **{k: np.asarray(v) for k, v in cols.items()})
    _figures(rows, pending, quick)
    table = _findings(rows)
    print(table)
    _write_findings(table, pending)
    return table


def _figures(rows, pending, quick):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for alpha in (*ALPHAS, ALPHA_HI):
        sub = [r for r in rows if abs(r["alpha"] - alpha) < 1e-9
               and np.isfinite(r["gamma_x"]) and np.isfinite(r["snr_T1.0"])
               and r["gamma_x"] > 0 and r["snr_T1.0"] > 0 and r["eps_over_g2"] > 0]
        if not sub:
            continue
        gx0 = next((r["gamma_x"] for r in rows if abs(r["alpha"] - alpha) < 1e-9 and abs(r["eps_over_g2"]) < 1e-12), None)
        if not gx0:
            continue
        xs = [r["gamma_x"] / gx0 for r in sub]
        ys = [r["snr_T1.0"] for r in sub]
        ax.loglog(xs, ys, "o", label=f"α={alpha:.1f}")
        for r, x, y in zip(sub, xs, ys):
            ax.annotate(f"{r['eps_over_g2']:g}", (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)
        grid = np.geomspace(0.05, 3.0, 40)
        t = np.linspace(0.0, 1.0, 501)
        overlay_x, overlay_y = [], []
        for x in grid:
            overlay_x.append(1.0 + dub_dgx(alpha, x * C.G2) / gx0)
            dlin = _lin_delta(t, x * C.G2, alpha)
            overlay_y.append(_snr(t, dlin, C.KAPPA_B))
        ax.loglog(overlay_x, overlay_y, "--", lw=1.0)
    ax.axhline(1.0, color="0.5", lw=0.8)
    ax.set(xlabel=r"$\Gamma_X(\varepsilon)/\Gamma_X(0)$", ylabel="SNR (T = 1 µs)",
           title="Readout SNR against the bit-flip rate")
    ax.legend(fontsize=8)
    cap = "Pending eigen points: " + (", ".join(pending) if pending else "none")
    fig.text(0.01, 0.01, cap, fontsize=6, wrap=True)
    save_fig(fig, "task_2_4b_tradeoff", quick=quick)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 7.5))
    for alpha in (*ALPHAS, ALPHA_HI):
        sub = [r for r in rows if abs(r["alpha"] - alpha) < 1e-9 and r["eps_over_g2"] > 0]
        gx0 = next((r["gamma_x"] for r in rows if abs(r["alpha"] - alpha) < 1e-9 and abs(r["eps_over_g2"]) < 1e-12), np.nan)
        xx = np.array([r["eps_over_g2"] for r in sub])
        if len(xx) == 0:
            continue
        dgx = np.array([r["gamma_x"] - gx0 if np.isfinite(r["gamma_x"]) else np.nan for r in sub])
        axes[0, 0].loglog(xx, dgx, "o", label=f"α={alpha:.1f}")
        line = np.geomspace(0.05, 3, 20)
        axes[0, 0].loglog(line, [dub_dgx(alpha, x * C.G2) for x in line], "--", lw=1)
        gm = np.array([gamma_m(alpha, x * C.G2) for x in xx])
        dgz = np.array([r["dGZ_corr"] if r["dGZ_corr"] is not None else np.nan for r in sub])
        axes[0, 1].plot(gm, dgz, "o", label=f"α={alpha:.1f}")
        snr = np.array([r["snr_rate"] for r in sub], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            axes[1, 0].plot(xx, snr / dgx, "o", label=f"α={alpha:.1f}")
        axes[1, 0].axhline(np.exp(2 * alpha**2), ls="--", lw=1)
        leak0 = next((r["leakage0"] for r in rows if abs(r["alpha"] - alpha) < 1e-9), np.nan)
        leak = np.array([r["leakage"] - leak0 if np.isfinite(r["leakage"]) else np.nan for r in sub])
        pred = np.array([leak_pred(alpha, x * C.G2) for x in xx])
        axes[1, 1].plot(pred, leak, "o", label=f"α={alpha:.1f}")
    href = np.array([1e-4, 1.0])
    axes[0, 1].plot(href, href, "k--", lw=0.8)
    axes[1, 1].plot(href, href, "k--", lw=0.8)
    axes[0, 0].set(xlabel=r"$\varepsilon/g_2$", ylabel=r"$\Delta\Gamma_X$", title="(a) bit-flip cost")
    axes[0, 1].set(xlabel=r"$\gamma_m$", ylabel=r"$\Delta\Gamma_Z^{corr}$", title="(b) S18 dephasing")
    axes[1, 0].set(xlabel=r"$\varepsilon/g_2$", ylabel=r"snr rate / $\Delta\Gamma_X$", title=r"(c) versus $e^{2\alpha^2}$")
    axes[1, 1].set(xlabel="leak_pred", ylabel="leakage − leakage(0)", title="(d) well shift")
    for ax in axes.ravel():
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    save_fig(fig, "task_2_4b_rates_vs_eps", quick=quick)
    plt.close(fig)


def _write_findings(table, pending):
    path = Path("docs/plan/status/l4b-tradeoff.md")
    if not path.is_file():
        return
    block = (
        "<!-- findings-begin -->\n"
        + table
        + "\n\nPending eigen ids: "
        + (", ".join(pending) if pending else "none")
        + "\n<!-- findings-end -->\n"
    )
    text = path.read_text()
    if "<!-- findings-begin -->" in text:
        pre, rest = text.split("<!-- findings-begin -->", 1)
        _old, post = rest.split("<!-- findings-end -->", 1)
        path.write_text(pre + block + post)
    else:
        path.write_text(text.rstrip() + "\n\n## Findings\n" + block)


def main(argv=None):
    p = argparse.ArgumentParser(description="Task 2.4b readout contrast versus bit-flip rate")
    p.add_argument("--part", choices=("td", "tdgx", "eig", "assemble"), default="td")
    p.add_argument("--alpha", type=float, default=None)
    p.add_argument("--tier", type=int, choices=(1, 2), default=None)
    p.add_argument("--quick", action="store_true")
    p.add_argument("--force", action="store_true")
    a = p.parse_args(argv)
    ok = snr_ids_ok()
    print("snr id uppercase T accepted:" , ok)
    if a.part == "eig":
        if a.quick:
            run_eig(1.0, 1, True, a.force)
        else:
            if a.alpha is None or a.tier is None:
                raise SystemExit("--part eig needs --alpha and --tier")
            run_eig(a.alpha, a.tier, False, a.force)
    elif a.part == "td":
        run_td(a.quick, a.force, None if a.quick else a.alpha)
    elif a.part == "tdgx":
        run_tdgx(a.quick, a.force)
    elif a.part == "assemble":
        run_assemble(a.quick)


if __name__ == "__main__":
    main()
