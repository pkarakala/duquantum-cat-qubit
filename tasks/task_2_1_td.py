"""Task 2.1 time-domain Gamma_X: fit Re<a>(t) after the buffer ringdown.

Alpha = 0.6 is not a double well and is rejected. Alpha > 1.4 is not run: T_X reaches seconds.
The fit window starts at 3 us, after the kappa_b/4 ringdown, and is 100 us in production.
"""
from src import config as C

import argparse

import jax.numpy as jnp
import numpy as np
import dynamiqs as dq

from src.analysis import fit_exp_decay
from src.convergence import convergence_block
from src.model import coherent2, one_mode, two_mode
from src.results import load_record, record, save_arrays, std_params
from tasks.task_2_1_channels import global_gamma, load_any
from tasks.task_2_1_eig import attach_cross_check, record_id, solve

SCRIPT = "tasks/task_2_1_td.py"
TIGHT = dq.method.Tsit5(rtol=1e-10, atol=1e-12, max_steps=10_000_000)


def fit_window(t, y, t0=3.0, window=100.0) -> dict:
    """Log-linear Gamma on t0 <= t <= t0+window, with the polyfit stderr."""
    t = np.asarray(t, dtype=float)
    y = np.real(np.asarray(y, dtype=float))
    m = (t >= t0) & (t <= t0 + window)
    tt, yy = t[m], y[m]
    # Gamma itself comes from fit_exp_decay; polyfit(cov=True) supplies the stderr.
    gamma, A = fit_exp_decay(tt, yy)
    _coef, cov = np.polyfit(tt, np.log(np.abs(yy)), 1, cov=True)
    gamma = float(gamma)
    A = float(A)
    fit = A * np.exp(-gamma * tt)
    rel_rms = float(np.sqrt(np.mean((yy - fit) ** 2)) / np.sqrt(np.mean(yy ** 2)))
    return {
        "gamma": gamma,
        "A": A,
        "gamma_stderr": float(np.sqrt(cov[0, 0])),
        "rel_rms_residual": rel_rms,
        "fit_window_us": [float(t0), float(t0 + window)],
    }


def simulate(model, alpha, Na, Nb, T, method):
    """(t, Re<a>, parity) from |alpha> (x) |0>. tsave has 10 points per us."""
    if alpha < 0.8 - 1e-12:
        raise ValueError(f"alpha={alpha} is below 0.8; 0.6 is not a double well and is excluded")
    Na, Nb = int(Na), int(Nb)
    n = int(round(T * 10)) + 1
    tsave = jnp.linspace(0.0, float(T), n)
    if model == "one_mode":
        H, jumps, a = one_mode(Na, C.KAPPA_2, alpha, kappa_a=C.KAPPA_A)
        psi0 = dq.coherent(Na, alpha)
        parity = dq.parity(Na)
    elif model == "two_mode":
        H, jumps, (a, _b) = two_mode(Na, Nb, C.G2, alpha ** 2 * C.G2, C.KAPPA_B, C.KAPPA_A)
        psi0 = coherent2(Na, Nb, alpha)
        parity = dq.tensor(dq.parity(Na), dq.eye(Nb))
    else:
        raise ValueError(model)
    res = dq.mesolve(
        H, jumps, psi0, tsave, exp_ops=[(a + a.dag()) / 2, parity],
        method=method, save_states=False,
    )
    t = np.asarray(tsave)
    re_a = np.real(np.asarray(res.expects[0]))
    par = np.real(np.asarray(res.expects[1]))
    return t, re_a, par


def _smallest_trunc(eig):
    """Smallest Na*Nb in the eig sweeps whose Gamma is within 1e-3 of the chosen value."""
    chosen = float(eig["value"])
    cands = []
    sweeps = (eig.get("convergence") or {}).get("sweeps") or {}
    if "Na" in sweeps:
        nb = int(sweeps["Na"]["fixed"].get("Nb", 1))
        for na, g in zip(sweeps["Na"]["values"], sweeps["Na"]["results"]):
            if abs(g - chosen) <= 1e-3 * abs(chosen):
                cands.append((int(na) * nb, int(na), nb))
    if "Nb" in sweeps:
        na = int(sweeps["Nb"]["fixed"]["Na"])
        for nb, g in zip(sweeps["Nb"]["values"], sweeps["Nb"]["results"]):
            if abs(g - chosen) <= 1e-3 * abs(chosen):
                cands.append((na * int(nb), na, int(nb)))
    if not cands:
        tr = eig["truncation"]
        return int(tr["Na"]), int(tr["Nb"])
    cands.sort()
    return cands[0][1], cands[0][2]


def _write_td(model, alpha, Na, Nb, fit, drift_rel, uncertainty, eig_same, quick, t, re_a):
    rid = record_id("td", model, alpha)
    rel = abs(fit["gamma"] - eig_same) / abs(eig_same)
    numerics = {
        "fit_window_us": fit["fit_window_us"],
        "gamma_stderr": fit["gamma_stderr"],
        "rel_rms_residual": fit["rel_rms_residual"],
        "rtol": 1e-10 if not quick else 1e-8,
        "drift_rel": None if quick else float(drift_rel),
    }
    notes = None
    if quick:
        notes = "quick smoke; not a production claim"
    elif drift_rel >= 0.005:
        notes = f"drift_rel={drift_rel:.3e} is not < 0.5%; not claimable"
    if rel > 0.02:
        notes = ((notes + " ") if notes else "") + (
            f"td vs eig rel_diff={rel:.3e} exceeds 0.02 at the same truncation; not claimable"
        )
    record(
        rid, task="2.1", quantity="Gamma_X", value=fit["gamma"], uncertainty=uncertainty,
        units="1/us", method="time_domain_fit_re_a", script=SCRIPT,
        params=std_params(alpha=alpha, n_th=0.0, model=model),
        truncation={"Na": int(Na), "Nb": int(Nb)},
        numerics=numerics,
        cross_check=[{
            "method": "liouvillian_eig_same_truncation", "value": float(eig_same),
            "rel_diff": float(rel), "tol": 0.02, "agree": bool(rel <= 0.02),
        }],
        notes=notes, quick=quick,
    )
    save_arrays(rid, quick=quick, t=np.asarray(t), re_a=np.asarray(re_a))
    eig_id = record_id("eig", model, alpha, 0.0)
    try:
        load_any(eig_id, quick=quick)
    except (FileNotFoundError, OSError, ValueError):
        print("no eig record to attach", eig_id)
    else:
        attach_cross_check(eig_id, {
            "method": "time_domain_fit", "ref_id": rid, "value": fit["gamma"],
            "rel_diff": float(rel), "tol": 0.02,
        }, quick=quick)
    print(f"RESULT {rid} gamma_x={fit['gamma']:.6e} eig_same={eig_same:.6e} rel={rel:.3e} "
          f"drift={drift_rel}")
    return fit["gamma"]


def run_one(model, alpha, quick=False):
    if alpha > 1.4 + 1e-12:
        raise ValueError(f"time domain is not run above alpha=1.4 (got {alpha})")
    alpha = float(alpha)
    if quick:
        Na, Nb, T = 20, 1, 30.0
        t, re_a, _ = simulate(model, alpha, Na, Nb, T, C.METHOD_LONG)
        fit = fit_window(t, re_a, t0=3.0, window=27.0)
        eig_same = solve(model, alpha, Na, Nb)["gamma_x"]
        return _write_td(model, alpha, Na, Nb, fit, None, fit["gamma_stderr"], eig_same, True, t, re_a)

    eig = load_record(record_id("eig", model, alpha, 0.0))
    Na, Nb = _smallest_trunc(eig)
    t_loose, re_loose, _ = simulate(model, alpha, Na, Nb, 103.0, C.METHOD_LONG)
    loose = fit_window(t_loose, re_loose)
    t, re_a, _ = simulate(model, alpha, Na, Nb, 103.0, TIGHT)
    tight = fit_window(t, re_a)
    drift = abs(loose["gamma"] - tight["gamma"]) / abs(tight["gamma"])
    unc = float(np.sqrt(tight["gamma_stderr"] ** 2 + (loose["gamma"] - tight["gamma"]) ** 2))
    # Convergence: Na +/- 4 and Nb +/- 2 at the loose tolerance. rel_tol 5e-3.
    rows_na = [{"Na": Na, "Gamma_X": loose["gamma"]}]
    t2, y2, _ = simulate(model, alpha, Na + 4, Nb, 103.0, C.METHOD_LONG)
    rows_na.append({"Na": Na + 4, "Gamma_X": fit_window(t2, y2)["gamma"]})
    sweeps = {"Na": ({"Nb": Nb}, rows_na)}
    chosen = {"Na": Na}
    if model == "two_mode":
        rows_nb = [{"Nb": Nb, "Gamma_X": loose["gamma"]}]
        t3, y3, _ = simulate(model, alpha, Na, Nb + 2, 103.0, C.METHOD_LONG)
        rows_nb.append({"Nb": Nb + 2, "Gamma_X": fit_window(t3, y3)["gamma"]})
        sweeps["Nb"] = ({"Na": Na}, rows_nb)
        chosen["Nb"] = Nb
    block = convergence_block(sweeps, "Gamma_X", 5e-3, chosen)
    eig_same = solve(model, alpha, Na, Nb)["gamma_x"]
    gamma = _write_td(model, alpha, Na, Nb, tight, drift, unc, eig_same, False, t, re_a)
    # Rewrite convergence onto the record. _write_td did not have the block yet.
    rec = load_record(record_id("td", model, alpha))
    record(
        rec["id"], task=rec["task"], quantity=rec["quantity"], value=rec["value"],
        units=rec["units"], method=rec["method"], params=rec["params"], script=SCRIPT,
        truncation=rec["truncation"], uncertainty=rec["uncertainty"], convergence=block,
        numerics=rec["numerics"], cross_check=rec["cross_check"], artifacts=rec.get("artifacts"),
        notes=rec.get("notes"),
    )
    return gamma


def _fit_curve(model, alphas, gammas):
    if len(alphas) < 3:
        print("td gamma_fit skipped for", model)
        return
    fit = global_gamma(np.asarray(alphas) ** 2, np.asarray(gammas), (0.8, 1.4))
    rid = record_id("fit_td", model)
    record(
        rid, task="2.1", quantity="gamma_fit", value=fit["gamma"], units="1",
        method="log_linear_alpha2", script=SCRIPT,
        params=std_params(n_th=0.0, model=model), uncertainty=fit["gamma_stderr"],
        numerics={"gamma_stderr": fit["gamma_stderr"], "window": fit["window"],
                  "intercept": fit["intercept"]},
        notes="Time-domain gamma on alpha in [0.8, 1.4]. Eig cross-check is attached when that fit exists.",
    )
    print("td gamma_fit", model, fit["gamma"])


def main(argv=None):
    p = argparse.ArgumentParser(description="Task 2.1 time-domain Gamma_X")
    p.add_argument("--model", choices=("one_mode", "two_mode"))
    p.add_argument("--alpha", type=float, nargs="*")
    p.add_argument("--quick", action="store_true")
    args = p.parse_args(argv)
    if args.quick:
        run_one("one_mode", 1.0, quick=True)
        return
    models = [args.model] if args.model else ["one_mode", "two_mode"]
    default = {
        "one_mode": [0.8, 1.0, 1.2, 1.4],
        "two_mode": [1.0, 1.4, 0.8, 1.2],
    }
    for model in models:
        alphas = args.alpha if args.alpha else default[model]
        got_a, got_g = [], []
        for alpha in alphas:
            g = run_one(model, float(alpha), quick=False)
            got_a.append(float(alpha))
            got_g.append(g)
        order = np.argsort(got_a)
        _fit_curve(model, np.asarray(got_a)[order], np.asarray(got_g)[order])


if __name__ == "__main__":
    main()
