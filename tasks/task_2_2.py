"""Task 2.2: phase-flip rate Gamma_Z from the decay of memory parity.

Start in the even cat. Single-photon loss is the only parity-changing process, so
<P(t)> = A exp(-Gamma_Z t) + C with C = 1/cosh(2 alpha^2). A pure exponential is
biased (about -55% at alpha = 1). Compare Gamma_Z with 2 kappa_a alpha^2 coth(2 alpha^2).
"""
import argparse
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: the macOS backend aborts without a window server

from src import config as C
import numpy as np
import jax.numpy as jnp
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import dynamiqs as dq

from src.model import two_mode, cat2
from src.analysis import fit_exp_offset, top_projector
from src.convergence import sweep, convergence_block
from src.results import RES_DIR, record, save_arrays, load_record, std_params
from src.plotting import save as save_fig

ALPHAS = (1.0, 1.4, 1.8, 2.1, 2.4, 2.7)
WINDOW = 2.5
N_T = 201
NB_SWEEP = (6, 8)
NA_STEP = 4
SLOPE_ID = "t2_2.slope_over_2kappa_a.td.two_mode"
INTRO_1_3A_ID = "t1_3a.gamma_z.td.two_mode.a2.10"
INTRO_1_3A_VALUE = 0.5135
SCRIPT = "tasks/task_2_2.py"
REL_TOL = 1e-3
FIG_PARITY = "task_2_2_parity_decay"
FIG_GAMMA = "task_2_2_gamma_z_vs_alpha2"


def nbar_ss(alpha) -> float:
    """Steady photon number of the C± mixture, alpha^2 coth(2 alpha^2)."""
    x = float(alpha) ** 2
    return float(x / np.tanh(2.0 * x))


def gamma_z_pred(alpha, kappa_a=C.KAPPA_A, n_th=0.0, nbar=None) -> float:
    """2 kappa_a [(1 + 2 n_th) nbar + n_th], with nbar = alpha^2 coth(2 alpha^2) by default."""
    if nbar is None:
        nbar = nbar_ss(alpha)
    return float(2.0 * kappa_a * ((1.0 + 2.0 * n_th) * nbar + n_th))


def parity_ss(alpha) -> float:
    """Steady parity 1/cosh(2 alpha^2). Not zero, so the fit needs an offset."""
    return float(1.0 / np.cosh(2.0 * float(alpha) ** 2))


def t_window(alpha) -> float:
    """2.5 predicted lifetimes, long enough for the offset to show."""
    return float(WINDOW / gamma_z_pred(alpha))


def td_id(alpha, n_th=0.0) -> str:
    rid = f"t2_2.gamma_z.td.two_mode.a{float(alpha):.2f}"
    if n_th:
        rid += f".nth{n_th:g}"
    return rid


def eig_id(alpha) -> str:
    return f"t2_2.gamma_z.eig.two_mode.a{float(alpha):.2f}"


def model(alpha, Na, Nb, n_th=0.0):
    """two_mode at eps_d = alpha^2 * g2. C.EPS_D is the alpha = 2.1 value only."""
    return two_mode(Na, Nb, C.G2, float(alpha) ** 2 * C.G2, C.KAPPA_B, C.KAPPA_A, n_th=n_th)


def slope_over_2kappa_a(alpha, gamma, sigma=None) -> dict:
    """Linear fit Gamma = intercept + slope * alpha^2, then ratio = slope / (2 kappa_a).

    sigma weights the points as 1/sigma (numpy polyfit: that is 1/sigma^2 in the
    sum of squares). The coth factor is larger at small alpha, so the ratio on the
    full grid sits slightly under 1 (0.9959) and the intercept is positive.
    """
    x = np.asarray(alpha, dtype=float) ** 2
    y = np.asarray(gamma, dtype=float)
    kwargs = {}
    if sigma is not None:
        sig = np.asarray(sigma, dtype=float)
        if np.any(sig <= 0):
            raise ValueError("sigma must be positive")
        kwargs["w"] = 1.0 / sig
    # Two points fix a line and the residual variance is zero, so a scaled
    # covariance is undefined. The quick legend only needs the ratio.
    if x.size < 3:
        coeff = np.polyfit(x, y, 1, **kwargs)
        cov = np.zeros((2, 2))
    else:
        coeff, cov = np.polyfit(x, y, 1, cov=True, **kwargs)
    slope, intercept = float(coeff[0]), float(coeff[1])
    two_ka = 2.0 * C.KAPPA_A
    return {
        "ratio": slope / two_ka,
        "ratio_stderr": float(np.sqrt(cov[0, 0]) / two_ka),
        "intercept": intercept,
        "intercept_stderr": float(np.sqrt(cov[1, 1])),
    }


def _p0_parity(alpha, n_th, parity):
    """fit_exp_offset wants (gamma, A, C), with A the amplitude at t = 0."""
    pred = gamma_z_pred(alpha, n_th=n_th)
    if n_th:
        # Thermal steady parity is not 1/cosh; start the offset at the last sample.
        c0 = float(parity[-1])
        return (pred, float(parity[0] - c0), c0)
    c0 = parity_ss(alpha)
    return (pred, 1.0 - c0, c0)


def run_td(alpha, Na, Nb, n_th=0.0, t_end=None, n_t=N_T, t0=0.0) -> dict:
    """Parity decay from |C+> x |0>_b. Fit A exp(-Gamma t) + C on t >= t0."""
    if t_end is None:
        t_end = t_window(alpha)
    H, jumps, (a, b) = model(alpha, Na, Nb, n_th=n_th)
    rho0 = cat2(Na, Nb, alpha, +1)
    tsave = jnp.linspace(0.0, float(t_end), int(n_t))
    parity_op = dq.tensor(dq.parity(Na), dq.eye(Nb))
    top2 = dq.tensor(top_projector(Na, 2), dq.eye(Nb))
    t_start = time.perf_counter()
    res = dq.mesolve(
        H, jumps, rho0, tsave, method=C.METHOD_LONG,
        exp_ops=[parity_op, a.dag() @ a, b.dag() @ b, top2],
        save_states=False,
    )
    wall = time.perf_counter() - t_start
    t = np.asarray(tsave, dtype=float)
    cols = [np.ravel(np.real(np.asarray(res.expects[i]))) for i in range(4)]
    if any(col.shape != (t.shape[0],) for col in cols):
        raise RuntimeError(f"expects columns have shapes {[c.shape for c in cols]}, t is {t.shape}")
    parity, n_a, n_b, top2_a = cols
    m = t >= t0
    p0 = _p0_parity(alpha, n_th, parity)
    fit = fit_exp_offset(t[m], parity[m], p0=p0)
    late = t >= 0.5
    if int(np.count_nonzero(late)) >= 8:
        gamma_late = float(fit_exp_offset(t[late], parity[late], p0=p0)["gamma"])
    else:
        gamma_late = float(fit["gamma"])
    # <n_a> settles at nbar. If the cat already sits there, the amplitude is noise:
    # use the window mean and do not trust that gamma.
    n_guess = nbar_ss(alpha)
    try:
        nfit = fit_exp_offset(
            t[m], n_a[m], p0=(p0[0], float(n_a[m][0] - n_guess), n_guess),
        )
    except (RuntimeError, ValueError):
        nfit = None
    if nfit is None or abs(nfit["A"]) < 1e-6:
        nbar_meas = float(np.mean(n_a[m]))
        gamma_from_n = 0.0 if nfit is None else float(nfit["gamma"])
    else:
        nbar_meas = float(nfit["C"])
        gamma_from_n = float(nfit["gamma"])
    print(
        f"  solve a={float(alpha):.2f} Na={Na} Nb={Nb} n_th={n_th:g} "
        f"gamma={fit['gamma']:.6f} wall={wall:.1f}s",
        flush=True,
    )
    return {
        "t": t, "parity": parity, "n_a": n_a, "n_b": n_b, "top2_a": top2_a,
        "gamma": float(fit["gamma"]), "gamma_stderr": float(fit["gamma_stderr"]),
        "A": float(fit["A"]), "C": float(fit["C"]),
        "rel_rms_residual": float(fit["rel_rms_residual"]),
        "fit_window_us": [float(t[m][0]), float(t[m][-1])],
        "gamma_t0_0p5": gamma_late,
        "nbar_meas": nbar_meas, "gamma_from_n": gamma_from_n,
        "max_top2_a": float(np.max(top2_a)), "max_n_b": float(np.max(n_b)),
        "wall_s": float(wall),
    }


def _low_spectrum():
    try:
        from src.spectral import low_spectrum
    except ImportError:
        return None
    return low_spectrum


def _mode_value(spec, key, index):
    if key not in spec:
        raise KeyError(f"low_spectrum result has no {key!r}; keys={sorted(spec)}")
    arr = np.asarray(spec[key])
    if arr.shape == ():
        return float(np.real(arr))
    return float(np.real(arr.ravel()[index]))


def run_eig(alpha, Na, Nb) -> dict:
    """Gamma_Z = rates[1] of the even Liouvillian block (rates[0] is the steady state)."""
    low_spectrum = _low_spectrum()
    if low_spectrum is None:
        raise ImportError("src.spectral is not importable (l1-spectral is not merged)")
    H, jumps, _ = model(alpha, Na, Nb)
    t_start = time.perf_counter()
    spec = low_spectrum(H, jumps, Na, Nb, k=4, sector="even")
    wall = time.perf_counter() - t_start
    rates = [float(np.real(x)) for x in np.asarray(spec["rates"]).ravel()]
    if len(rates) < 2:
        raise RuntimeError(f"even block returned {len(rates)} rates, need at least 2")
    sigma = spec["sigma"] if spec.get("sigma") is not None else 0.0
    out = {
        "gamma": rates[1],
        "rate0": rates[0],
        "rates": rates,
        "rel_residual": _mode_value(spec, "rel_residual", 1),
        "edge_weight": _mode_value(spec, "edge_weight", 1),
        "cond_est": _mode_value(spec, "cond_est", 1),
        "sigma": float(np.asarray(sigma).reshape(-1)[0]),
        "wall_s": float(wall),
    }
    print(
        f"  eig a={float(alpha):.2f} Na={Na} Nb={Nb} gamma={out['gamma']:.6f} "
        f"rate0={out['rate0']:.3e} rel_residual={out['rel_residual']:.3e} "
        f"edge={out['edge_weight']:.3e} wall={wall:.1f}s",
        flush=True,
    )
    return out


def _cross(method, ours, check, tol, ref_id=None) -> dict:
    rel = abs(float(ours) - float(check)) / abs(float(check))
    return {
        "method": method,
        "ref_id": ref_id,
        "value": float(check),
        "rel_diff": float(rel),
        "tol": float(tol),
        "agree": bool(rel <= tol),
    }


def _load_if(rid):
    path = RES_DIR / "records" / f"{rid}.json"
    if not path.exists():
        return None
    return load_record(rid)


def _td_checks(alpha, gamma, nbar_meas, n_th):
    """Analytic checks written with the time-domain record. Eigen is added by --summary."""
    if n_th:
        return [_cross("analytic_thermal", gamma, 0.5728, 0.02)]
    checks = [
        _cross("analytic_coth", gamma, gamma_z_pred(alpha), 0.02),
        _cross("analytic_2kappa_nbar", gamma, 2.0 * C.KAPPA_A * nbar_meas, 0.02),
    ]
    if abs(float(alpha) - 2.1) < 1e-9:
        intro = _load_if(INTRO_1_3A_ID)
        checks.append(_cross(
            "intro_1_3a_inflation_fit", gamma, INTRO_1_3A_VALUE, 0.02,
            ref_id=INTRO_1_3A_ID if intro is not None else None,
        ))
    return checks


def _grid(alpha, quick, n_th):
    if quick:
        return {
            "na_values": [12, 16], "nb_values": [4, 6], "na_star": 16, "nb_star": 6,
            "t_end": 1.0 / gamma_z_pred(alpha, n_th=n_th), "n_t": 81, "extend": False,
        }
    na0, _ = C.trunc_for(alpha, "steady")
    return {
        "na_values": [na0 - NA_STEP, na0, na0 + NA_STEP],
        "nb_values": list(NB_SWEEP),
        "na_star": na0 + NA_STEP,
        "nb_star": 8,
        "t_end": None,
        "n_t": N_T,
        "extend": True,
    }


def _spread(rows_na, rows_nb):
    """|Gamma(chosen) - Gamma(previous)| on each axis. Unextended, that is Na0+4 vs Na0 and Nb 8 vs 6."""
    na = sorted(rows_na, key=lambda r: r["Na"])
    nb = sorted(rows_nb, key=lambda r: r["Nb"])
    d_na = abs(na[-1]["gamma_z"] - na[-2]["gamma_z"])
    d_nb = abs(nb[-1]["gamma_z"] - nb[-2]["gamma_z"])
    return d_na, d_nb


def run_td_study(alpha, quick=False, n_th=0.0, grid=None) -> dict:
    """Na and Nb sweeps, then the time-domain record at the chosen truncation."""
    g = grid or _grid(alpha, quick, n_th)
    na_values = list(g["na_values"])
    nb_values = list(g["nb_values"])
    na_star, nb_star = g["na_star"], g["nb_star"]
    traces = {}

    def fn(Na, Nb):
        key = (int(Na), int(Nb))
        if key not in traces:
            traces[key] = run_td(
                alpha, key[0], key[1], n_th=n_th, t_end=g["t_end"], n_t=g["n_t"],
            )
        return {"gamma_z": traces[key]["gamma"]}

    def one_block(na_values, na_star):
        rows_na = sweep(fn, "Na", na_values, {"Nb": nb_star})
        rows_nb = sweep(fn, "Nb", nb_values, {"Na": na_star})
        block = convergence_block(
            {"Na": ({"Nb": nb_star}, rows_na), "Nb": ({"Na": na_star}, rows_nb)},
            key="gamma_z", rel_tol=REL_TOL, chosen={"Na": na_star, "Nb": nb_star},
        )
        return rows_na, rows_nb, block

    rows_na, rows_nb, block = one_block(na_values, na_star)
    n_ext = 0
    while g["extend"] and n_ext < 2 and (
        not block["converged"] or traces[(na_star, nb_star)]["max_top2_a"] >= 1e-6
    ):
        n_ext += 1
        na_star = na_star + NA_STEP
        na_values = na_values + [na_star]
        print(f"  extend Na to {na_star} (extension {n_ext}/2)", flush=True)
        rows_na, rows_nb, block = one_block(na_values, na_star)

    chosen = traces[(na_star, nb_star)]
    d_na, d_nb = _spread(rows_na, rows_nb)
    gamma = chosen["gamma"]
    uncertainty = float(max(chosen["gamma_stderr"], d_na, d_nb))
    pred = gamma_z_pred(alpha, n_th=n_th)
    rid = td_id(alpha, n_th)
    total_wall = float(sum(r["wall_s"] for r in traces.values()))
    notes = (
        "Offset fit of memory parity from the even cat. "
        "eps_d = alpha^2 * g2. Steady parity 1/cosh(2 alpha^2)."
    )
    if n_ext:
        notes += f" Extended Na by +4, {n_ext} time(s), because gamma or the Fock tail had not settled."
    if n_th:
        notes += " Thermal jumps on; prediction 2 kappa_a [(1+2 n_th) nbar + n_th] = 0.5728 at this point."
    checks = _td_checks(alpha, gamma, chosen["nbar_meas"], n_th)
    # Gamma_Z = 2 kappa_a * n_eq with n_eq the equal C+/C- mixture. The parity steady
    # state is not that mixture when P_ss = 1/cosh(2 alpha^2) is appreciable (alpha=1):
    # <n>_ss = n_eq + P_ss (n_+ - n_-)/2, about 7.6% below n_eq. 2 kappa_a <n>_ss then
    # misses Gamma_Z. That is the steady-state weight, not a failed rate.
    nbar_miss = any(c["method"] == "analytic_2kappa_nbar" and not c["agree"] for c in checks)
    if nbar_miss:
        notes += (
            " analytic_2kappa_nbar misses because <n>_ss is the parity-weighted cat mixture, "
            "not alpha^2 coth(2 alpha^2). The coth check is the rate test."
        )
    numerics = {
        "fit_window_us": chosen["fit_window_us"],
        "gamma_stderr": chosen["gamma_stderr"],
        "rel_rms_residual": chosen["rel_rms_residual"],
        "A": chosen["A"],
        "C_fit": chosen["C"],
        "C_pred": parity_ss(alpha),
        "gamma_t0_0p5": chosen["gamma_t0_0p5"],
        "nbar_meas": chosen["nbar_meas"],
        "gamma_from_n": chosen["gamma_from_n"],
        "max_top2_a": chosen["max_top2_a"],
        "max_n_b": chosen["max_n_b"],
        "n_t": int(g["n_t"]),
        "rtol": float(C.METHOD_LONG.rtol),
    }
    fig = f"figures/quick/{FIG_GAMMA}.png" if quick else f"figures/{FIG_GAMMA}.png"
    arr = f"results/quick/arrays/{rid}.npz" if quick else f"results/arrays/{rid}.npz"
    record(
        rid, task="2.2", quantity="Gamma_Z", value=gamma, units="1/us",
        method="time_domain_fit_exp_offset",
        params=std_params(alpha=float(alpha), n_th=float(n_th)),
        script=SCRIPT, truncation={"Na": int(na_star), "Nb": int(nb_star)},
        uncertainty=uncertainty, convergence=block, numerics=numerics,
        cross_check=checks,
        artifacts={"figure": fig, "arrays": arr}, wall_s=total_wall, notes=notes, quick=quick,
    )
    payload = {
        "t": chosen["t"],
        "fit_A": np.asarray(chosen["A"]),
        "fit_gamma": np.asarray(gamma),
        "fit_C": np.asarray(chosen["C"]),
        "wall_s": np.asarray(total_wall),
    }
    for (Na, Nb), r in sorted(traces.items()):
        payload[f"parity_Na{Na}_Nb{Nb}"] = r["parity"]
        payload[f"n_a_Na{Na}_Nb{Nb}"] = r["n_a"]
        payload[f"n_b_Na{Na}_Nb{Nb}"] = r["n_b"]
        payload[f"top2_a_Na{Na}_Nb{Nb}"] = r["top2_a"]
    save_arrays(rid, quick=quick, **payload)
    rel = gamma / pred - 1.0
    print(
        f"td {rid} Na={na_star} Nb={nb_star} gamma={gamma:.6f} pred={pred:.6f} "
        f"rel={rel:+.4%} C={chosen['C']:.5f} resid={chosen['rel_rms_residual']:.2e} "
        f"top2={chosen['max_top2_a']:.2e} nb_rel={d_nb / abs(gamma):.2e} "
        f"late={chosen['gamma_t0_0p5'] / gamma - 1:+.4%} "
        f"converged={block['converged']} wall={total_wall:.1f}s",
        flush=True,
    )
    if not quick and not block["converged"]:
        print(
            "DECISION NEEDED\n"
            f"> **Q:** Gamma_Z(alpha={alpha}) is not converged at Na={na_star}, Nb={nb_star} "
            f"(Na spread {d_na:.3g}, Nb spread {d_nb:.3g}). Extend further or report?\n"
            "> **Options:** A) report the unconverged value with the spread as the uncertainty; "
            "B) block until reviewed.\n"
            "> **Recommendation:** B if the two largest Na still disagree by more than 1e-3.\n"
            "> **Blocking?** no: other alphas continue.\n",
            flush=True,
        )
    if not quick and nbar_miss:
        print(
            "DECISION NEEDED\n"
            f"> **Q:** Γ_Z(α={alpha}) matches 2κ_aα²coth(2α²) "
            f"(rel {rel:+.2%}) but 2κ_a·n̄_meas misses it. "
            "Is that two-mode error, or the parity-weighted steady state?\n"
            "> **Options:** A) report agree=false on analytic_2kappa_nbar and keep the coth check; "
            "B) block until reviewed.\n"
            "> **Recommendation:** A. ⟨n⟩_ss = n_eq + P_ss (n_+ − n_-)/2 with "
            "P_ss = 1/cosh(2α²). At α=1 that shift is 7.6%; at α≥1.4 it is under 0.2%.\n"
            "> **Blocking?** no: the other alphas still run.\n",
            flush=True,
        )
    if not quick and n_th == 0.0 and abs(rel) > 0.02:
        print(
            "DECISION NEEDED\n"
            f"> **Q:** Γ_Z(α={alpha}) misses 2κ_aα²coth(2α²) by {100 * abs(rel):.2f}% after convergence "
            f"(Na up to {na_star}, Nb 6/8 agree to {d_nb / abs(gamma):.3g}). "
            "Accept as a two-mode dressing effect or investigate?\n"
            "> **Options:** A) report with the measured 2κ_a·n̄ comparison as the explanation; "
            "B) block until reviewed.\n"
            "> **Recommendation:** A if analytic_2kappa_nbar agrees: the only two-mode correction "
            "left is dressing of order kappa_a/kappa_2.\n"
            "> **Blocking?** no: finished the other α meanwhile.\n",
            flush=True,
        )
    return {
        "alpha": float(alpha), "gamma": gamma, "uncertainty": uncertainty, "pred": pred,
        "A": chosen["A"], "C": chosen["C"], "t": chosen["t"], "parity": chosen["parity"],
        "converged": bool(block["converged"]), "id": rid, "nbar_meas": chosen["nbar_meas"],
        "rel": float(rel),
    }


def _eig_grid(alpha, quick):
    if quick:
        return {"na_values": [12], "nb_values": [4], "na_star": 12, "nb_star": 4}
    na0, _ = C.trunc_for(alpha, "eig")
    return {
        "na_values": [na0, na0 + NA_STEP],
        "nb_values": list(NB_SWEEP),
        "na_star": na0 + NA_STEP,
        "nb_star": 8,
    }


def run_eig_study(alpha, quick=False) -> dict:
    """Even-block Gamma_Z. Requires src.spectral (not on this branch until l1-spectral merges)."""
    g = _eig_grid(alpha, quick)
    traces = {}

    def fn(Na, Nb):
        key = (int(Na), int(Nb))
        if key not in traces:
            traces[key] = run_eig(alpha, key[0], key[1])
        return {"gamma_z": traces[key]["gamma"]}

    na_star, nb_star = g["na_star"], g["nb_star"]
    rows_na = sweep(fn, "Na", g["na_values"], {"Nb": nb_star})
    rows_nb = sweep(fn, "Nb", g["nb_values"], {"Na": na_star})
    # A one-point quick smoke cannot satisfy the two-truncation rule; say so.
    if len(g["na_values"]) < 2 or len(g["nb_values"]) < 2:
        block = {
            "key": "gamma_z", "rel_tol": REL_TOL,
            "sweeps": {
                "Na": {"fixed": {"Nb": nb_star}, "values": list(g["na_values"]),
                       "results": [r["gamma_z"] for r in rows_na]},
                "Nb": {"fixed": {"Na": na_star}, "values": list(g["nb_values"]),
                       "results": [r["gamma_z"] for r in rows_nb]},
            },
            "needed": {"Na": na_star, "Nb": nb_star},
            "converged": False,
        }
        notes_quick = " Quick grid is a single truncation, so converged is false."
    else:
        block = convergence_block(
            {"Na": ({"Nb": nb_star}, rows_na), "Nb": ({"Na": na_star}, rows_nb)},
            key="gamma_z", rel_tol=REL_TOL, chosen={"Na": na_star, "Nb": nb_star},
        )
        notes_quick = ""
    chosen = traces[(na_star, nb_star)]
    d_na, d_nb = (0.0, 0.0) if len(traces) < 2 else _spread(rows_na, rows_nb)
    uncertainty = float(max(d_na, d_nb)) if len(traces) >= 2 else None
    pred = gamma_z_pred(alpha)
    td = _load_if(td_id(alpha))
    checks = [_cross("analytic_coth", chosen["gamma"], pred, 0.02)]
    if td is not None:
        checks.append(_cross("time_domain_fit", chosen["gamma"], td["value"], 0.01, ref_id=td["id"]))
    passed = (
        abs(chosen["rate0"]) < 1e-8
        and chosen["rel_residual"] < 1e-4
        and chosen["edge_weight"] < 1e-6
    )
    rid = eig_id(alpha)
    record(
        rid, task="2.2", quantity="Gamma_Z", value=chosen["gamma"], units="1/us",
        method="liouvillian_eig_even_sector",
        params=std_params(alpha=float(alpha)), script=SCRIPT,
        truncation={"Na": int(na_star), "Nb": int(nb_star)},
        uncertainty=uncertainty, convergence=block,
        numerics={
            "rel_residual": chosen["rel_residual"],
            "edge_weight": chosen["edge_weight"],
            "cond_est": chosen["cond_est"],
            "sector": "even",
            "sigma": chosen["sigma"],
            "k": 4,
            "rate0": chosen["rate0"],
        },
        cross_check=checks,
        artifacts={"figure": f"figures/{FIG_GAMMA}.png", "arrays": None},
        wall_s=float(sum(r["wall_s"] for r in traces.values())),
        notes=("Even block, rates[1]. rates[0] is the steady state." + notes_quick
               + ("" if passed else " ACCEPTANCE FAILED (residual, edge, or rate0).")),
        quick=quick,
    )
    print(
        f"eig {rid} gamma={chosen['gamma']:.6f} pred={pred:.6f} "
        f"acceptance={'PASS' if passed else 'FAIL'} converged={block['converged']}",
        flush=True,
    )
    return {"alpha": float(alpha), "gamma": chosen["gamma"], "passed": passed}


def _series_from_records():
    series, eig = [], []
    for alpha in ALPHAS:
        rec = load_record(td_id(alpha))
        arr = np.load(RES_DIR / "arrays" / f"{td_id(alpha)}.npz")
        Na, Nb = int(rec["truncation"]["Na"]), int(rec["truncation"]["Nb"])
        num = rec["numerics"]
        pred_check = next(c for c in rec["cross_check"] if c["method"] == "analytic_coth")
        series.append({
            "alpha": float(alpha),
            "t": np.asarray(arr["t"], dtype=float),
            "parity": np.asarray(arr[f"parity_Na{Na}_Nb{Nb}"], dtype=float),
            "A": float(num["A"]),
            "C": float(num["C_fit"]),
            "gamma": float(rec["value"]),
            "uncertainty": float(rec["uncertainty"]),
            "pred": float(pred_check["value"]),
        })
        e = _load_if(eig_id(alpha))
        if e is not None:
            eig.append((float(alpha), float(e["value"])))
    return series, eig


def draw_figures(series, quick, slope_ratio=None, eig=None):
    """Parity collapse, and Gamma_Z versus alpha^2. Eigen points are drawn when present."""
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    for s in series:
        line, = ax[0].plot(s["t"], s["parity"], lw=1.6, label=fr"$\alpha={s['alpha']:.1f}$")
        fit = s["A"] * np.exp(-s["gamma"] * s["t"]) + s["C"]
        ax[0].plot(s["t"], fit, ls="--", color=line.get_color(), lw=1.0)
        ax[0].axhline(parity_ss(s["alpha"]), ls=":", color=line.get_color(), lw=0.8)
        z = (s["parity"] - s["C"]) / s["A"]
        m = z > 1e-4
        ax[1].semilogy(s["pred"] * s["t"][m], z[m], lw=1.6, color=line.get_color(),
                       label=fr"$\alpha={s['alpha']:.1f}$")
    xs = np.linspace(0.0, WINDOW, 300)
    ax[1].semilogy(xs, np.exp(-xs), "k--", lw=1.0, label=r"$e^{-x}$")
    ax[0].set(xlabel="t (µs)", ylabel=r"$\langle P\rangle$", title="parity decay")
    ax[1].set(xlabel=r"$\Gamma_{\mathrm{pred}}\,t$", ylabel=r"$(\langle P\rangle-C)/A$",
              title="lifetimes collapse")
    extra = [
        Line2D([0], [0], color="k", ls="--", lw=1, label="offset fit"),
        Line2D([0], [0], color="k", ls=":", lw=1, label=r"$1/\cosh(2\alpha^2)$"),
    ]
    h, lab = ax[0].get_legend_handles_labels()
    ax[0].legend(h + extra, lab + [e.get_label() for e in extra], fontsize=7)
    ax[1].legend(fontsize=7)
    for a in ax:
        a.grid(alpha=0.3)
    save_fig(fig, FIG_PARITY, quick=quick)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    aa = np.linspace(min(s["alpha"] for s in series) - 0.05, max(s["alpha"] for s in series) + 0.05, 200)
    ax[0].plot(aa ** 2, [gamma_z_pred(a) for a in aa], "k-", lw=1.2, label=r"$2\kappa_a\alpha^2\mathrm{coth}(2\alpha^2)$")
    ax[0].plot(aa ** 2, 2.0 * C.KAPPA_A * aa ** 2, "k--", lw=1.0, label=r"$2\kappa_a\alpha^2$")
    x = np.array([s["alpha"] ** 2 for s in series])
    y = np.array([s["gamma"] for s in series])
    yerr = np.array([s["uncertainty"] for s in series])
    ratio_txt = f"{slope_ratio:.4f}" if slope_ratio is not None else "n/a"
    ax[0].errorbar(x, y, yerr=yerr, fmt="o", ms=5, lw=1, capsize=3, zorder=3,
                   label=fr"time domain, slope$/2\kappa_a$ = {ratio_txt}")
    if eig:
        ax[0].plot([a ** 2 for a, _ in eig], [g for _, g in eig], "o", ms=7, mfc="none",
                   color="C3", zorder=4, label="even-block eigenvalue")
    rel = np.array([s["gamma"] / s["pred"] - 1.0 for s in series])
    ax[1].axhspan(-0.02, 0.02, color="0.85", label=r"$\pm 2\%$")
    ax[1].axhline(0.0, color="k", lw=0.8)
    ax[1].plot(x, rel, "o-", lw=1.2, label="time domain")
    if eig:
        pred_e = {s["alpha"]: s["pred"] for s in series}
        ax[1].plot([a ** 2 for a, _ in eig], [g / pred_e[a] - 1.0 for a, g in eig],
                   "o", ms=7, mfc="none", color="C3", label="eigenvalue")
    ax[0].set(xlabel=r"$\alpha^2$", ylabel=r"$\Gamma_Z$ (1/µs)", title="phase-flip rate")
    ax[1].set(xlabel=r"$\alpha^2$", ylabel=r"$\Gamma/\Gamma_{\mathrm{pred}}-1$", title="versus the coth law")
    ax[0].legend(fontsize=7)
    ax[1].legend(fontsize=7)
    for a in ax:
        a.grid(alpha=0.3)
    save_fig(fig, FIG_GAMMA, quick=quick)
    plt.close(fig)


def _gamma_at_na(rec, na):
    sweep_na = rec["convergence"]["sweeps"]["Na"]
    values = sweep_na["values"]
    for i, v in enumerate(values):
        if int(v) == int(na):
            return float(sweep_na["results"][i])
    raise KeyError(f"{rec['id']} Na sweep {values} has no Na={na}")


def write_summary():
    """Slope record, eigen and 1.3a cross-checks, both figures. No simulation."""
    missing = [td_id(a) for a in ALPHAS if _load_if(td_id(a)) is None]
    if missing:
        raise SystemExit(f"--summary needs production td records, missing {missing}")
    gammas, sigmas = [], []
    for alpha in ALPHAS:
        rec = load_record(td_id(alpha))
        gammas.append(float(rec["value"]))
        sigmas.append(float(rec["uncertainty"]))
        checks = [
            _cross("analytic_coth", rec["value"], gamma_z_pred(alpha), 0.02),
            _cross("analytic_2kappa_nbar", rec["value"],
                   2.0 * C.KAPPA_A * rec["numerics"]["nbar_meas"], 0.02),
        ]
        eig = _load_if(eig_id(alpha))
        if eig is not None:
            checks.append(_cross(
                "liouvillian_eig_even", rec["value"], eig["value"], 0.01, ref_id=eig["id"],
            ))
        if abs(alpha - 2.1) < 1e-9:
            intro = _load_if(INTRO_1_3A_ID)
            checks.append(_cross(
                "intro_1_3a_inflation_fit", rec["value"], INTRO_1_3A_VALUE, 0.02,
                ref_id=INTRO_1_3A_ID if intro is not None else None,
            ))
        record(
            rec["id"], task=rec["task"], quantity=rec["quantity"], value=rec["value"],
            units=rec["units"], method=rec["method"], params=rec["params"], script=SCRIPT,
            truncation=rec["truncation"], uncertainty=rec["uncertainty"],
            convergence=rec["convergence"], numerics=rec["numerics"], cross_check=checks,
            artifacts=rec["artifacts"], wall_s=rec["provenance"]["wall_s"], notes=rec["notes"],
        )
    fit = slope_over_2kappa_a(ALPHAS, gammas, sigmas)
    fit_14 = slope_over_2kappa_a(ALPHAS[1:], gammas[1:], sigmas[1:])
    # Same weights at every Na offset, so the offset-+4 row is the reported ratio
    # whenever the saved value is the Na0+4 truncation.
    rows = []
    for offset in (-NA_STEP, 0, NA_STEP):
        gs = []
        for alpha in ALPHAS:
            rec = load_record(td_id(alpha))
            na0, _ = C.trunc_for(alpha, "steady")
            gs.append(_gamma_at_na(rec, na0 + offset))
        rows.append({
            "Na_offset": offset,
            "slope_over_2kappa_a": slope_over_2kappa_a(ALPHAS, gs, sigmas)["ratio"],
        })
    block = convergence_block(
        {"Na_offset": ({"Nb": 8}, rows)},
        key="slope_over_2kappa_a", rel_tol=REL_TOL, chosen={"Na_offset": NA_STEP},
    )
    record(
        SLOPE_ID, task="2.2", quantity="slope_over_2kappa_a", value=fit["ratio"], units="1",
        method="weighted_linear_fit_vs_alpha2",
        params=std_params(fit_alphas=[float(a) for a in ALPHAS]),
        script=SCRIPT, truncation={"Na_offset": NA_STEP, "Nb": 8},
        uncertainty=fit["ratio_stderr"], convergence=block,
        numerics={
            "intercept": fit["intercept"],
            "intercept_stderr": fit["intercept_stderr"],
            "ratio_alpha_ge_1p4": fit_14["ratio"],
        },
        cross_check=[
            _cross("analytic_coth_grid", fit["ratio"], 0.9959, 0.02),
            _cross("prompt_linear", fit["ratio"], 1.0, 0.02),
        ],
        artifacts={"figure": f"figures/{FIG_GAMMA}.png", "arrays": None},
        notes=(
            "Weighted (1/uncertainty^2) fit of Gamma_td vs alpha^2, divided by 2 kappa_a. "
            "Na_offset = Na - Na0 with Na0 = trunc_for(alpha, 'steady')[0]; the sweep reuses "
            "each alpha's Na-sweep Gamma at Nb=8 and the chosen-point uncertainties as weights. "
            "Chosen offset +4. The coth grid itself gives 0.9959 because coth(2 alpha^2) - 1 "
            "is larger at small alpha, so a straight line undershoots 2 kappa_a slightly. "
            "Reglade et al. see a slope ~25% above this model; that is outside the Hamiltonian, not fitted."
        ),
    )
    print(
        f"slope {SLOPE_ID} ratio={fit['ratio']:.6f} ± {fit['ratio_stderr']:.3g} "
        f"intercept={fit['intercept']:.4g} ratio(alpha>=1.4)={fit_14['ratio']:.6f} "
        f"converged={block['converged']}",
        flush=True,
    )
    series, eig = _series_from_records()
    draw_figures(series, quick=False, slope_ratio=fit["ratio"], eig=eig or None)


def run_thermal(quick=False):
    """Optional: alpha=2.1, n_th=0.05, Na=32 and 36, Nb=6 and 8."""
    if quick:
        run_td_study(2.1, quick=True, n_th=0.05)
        return
    run_td_study(2.1, n_th=0.05, grid={
        "na_values": [32, 36], "nb_values": [6, 8], "na_star": 36, "nb_star": 8,
        "t_end": None, "n_t": N_T, "extend": True,
    })


def _skip_eig(alphas):
    print("SKIP --eig: src/spectral.py is not on this branch (l1-spectral is not merged).")
    print("Nothing eigenvalue-related was simulated. Queue, from the worktree root:")
    for alpha in alphas:
        print(f"  python -m tasks.task_2_2 --eig --alpha {alpha:.1f}")
    print("  python -m tasks.task_2_2 --summary")


def main(alphas=ALPHAS, quick=False, eig=False, thermal=False, summary=False):
    if summary:
        if quick:
            raise SystemExit("--summary reads production records; drop --quick")
        write_summary()
        return
    if eig:
        if _low_spectrum() is None:
            _skip_eig(alphas)
        else:
            for alpha in alphas:
                run_eig_study(alpha, quick=quick)
        if not thermal:
            return
    if thermal and not eig:
        run_thermal(quick=quick)
        return
    if thermal and eig:
        run_thermal(quick=quick)
        return
    series = []
    for alpha in alphas:
        series.append(run_td_study(alpha, quick=quick))
    if quick and series:
        ratios = slope_over_2kappa_a(
            [s["alpha"] for s in series], [s["gamma"] for s in series],
        )["ratio"] if len(series) >= 2 else None
        draw_figures(series, quick=True, slope_ratio=ratios)


def _parse():
    p = argparse.ArgumentParser(description="Task 2.2: phase-flip rate Gamma_Z")
    p.add_argument("--quick", action="store_true", help="smoke grid, writes results/quick and figures/quick")
    p.add_argument("--alpha", type=float, nargs="+", default=None, help="alphas to run (default: all six)")
    p.add_argument("--eig", action="store_true", help="even-block eigenvalue (needs src.spectral)")
    p.add_argument("--thermal", action="store_true", help="optional n_th=0.05 point at alpha=2.1")
    p.add_argument("--summary", action="store_true", help="slope, cross-checks and figures from saved records")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse()
    if args.alpha is not None:
        alphas = tuple(args.alpha)
    elif args.quick and not args.thermal:
        # Brief §7: the smoke grid is alpha = 1.0 and 1.4 unless --alpha is set.
        alphas = (1.0, 1.4)
    else:
        alphas = ALPHAS
    main(alphas, quick=args.quick, eig=args.eig, thermal=args.thermal, summary=args.summary)
