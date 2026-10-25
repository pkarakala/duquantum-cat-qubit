"""Task 2.1 channel formulas and the record-side overlays.

Channel 1 is the code-space Golden Rule, Gamma = kappa_a alpha^2 (coth(2 alpha^2) - 1).
Channel 2 is the out-and-back rate c (kappa_a^2 / kappa_2) exp(-2 alpha^2). The fitted c
is never used as its own cross-check: the parameter-free overlay is c = 1.
"""
from src import config as C

import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from src.results import RES_DIR, load_record, record, save_arrays, std_params

SCRIPT = "tasks/task_2_1_channels.py"


def _scalar(x):
    arr = np.asarray(x, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    return arr


def gamma_ch1(alpha, kappa_a):
    """Exact code-space rate kappa_a alpha^2 (coth(2 alpha^2) - 1)."""
    a2 = np.asarray(alpha, dtype=float) ** 2
    return _scalar(np.asarray(kappa_a, dtype=float) * a2 * (1.0 / np.tanh(2.0 * a2) - 1.0))


def gamma_ch1_approx(alpha, kappa_a):
    """2 kappa_a alpha^2 exp(-4 alpha^2), the large-alpha form of channel 1."""
    a2 = np.asarray(alpha, dtype=float) ** 2
    return _scalar(2.0 * np.asarray(kappa_a, dtype=float) * a2 * np.exp(-4.0 * a2))


def gamma_ch2(alpha, kappa_a, kappa_2, c=1.0):
    """c (kappa_a^2 / kappa_2) exp(-2 alpha^2). c = 1 is Dubovitskii per direction, doubled."""
    a2 = np.asarray(alpha, dtype=float) ** 2
    return _scalar(c * np.asarray(kappa_a, dtype=float) ** 2 / kappa_2 * np.exp(-2.0 * a2))


def gamma_thermal_extra(alpha, kappa_a, n_th, c_th=1.0):
    """c_th kappa_a n_th exp(-2 alpha^2), the thermal piece on top of the vacuum channels."""
    a2 = np.asarray(alpha, dtype=float) ** 2
    return _scalar(c_th * np.asarray(kappa_a, dtype=float) * n_th * np.exp(-2.0 * a2))


def crossover_alpha2(kappa_a, kappa_2):
    """Naive alpha^2 where kappa_a ~ kappa_2 e^{-2 alpha^2}, dropping the alpha^2 prefactor."""
    return float(np.log(kappa_2 / kappa_a) / 2.0)


def crossover_alpha2_exact(kappa_a, kappa_2, c=1.0):
    """alpha^2 where gamma_ch1 = gamma_ch2(c), bracketed on [1, 6]."""
    def f(x):
        a = float(np.sqrt(x))
        return gamma_ch1(a, kappa_a) - gamma_ch2(a, kappa_a, kappa_2, c=c)
    return float(brentq(f, 1.0, 6.0))


def local_slope(alpha2, gamma) -> np.ndarray:
    """Positive -d ln Gamma / d(alpha^2). np.gradient, as specified."""
    return -np.gradient(np.log(np.asarray(gamma, dtype=float)), np.asarray(alpha2, dtype=float))


def global_gamma(alpha2, gamma, window) -> dict:
    """Least squares of ln Gamma vs alpha^2 on window=(a_lo, a_hi) in alpha, not alpha^2."""
    alpha2 = np.asarray(alpha2, dtype=float)
    gamma = np.asarray(gamma, dtype=float)
    alpha = np.sqrt(alpha2)
    m = (alpha >= window[0]) & (alpha <= window[1])
    x = alpha2[m]
    coef, cov = np.polyfit(x, np.log(gamma[m]), 1, cov=True)
    return {
        "gamma": float(-coef[0]),
        "gamma_stderr": float(np.sqrt(cov[0, 0])),
        "intercept": float(coef[1]),
        "window": [float(window[0]), float(window[1])],
    }


def kappa_a_exponent(kappas, gammas) -> dict:
    """Log-log slope d ln Gamma / d ln kappa_a, plus the local gradient."""
    lk = np.log(np.asarray(kappas, dtype=float))
    lg = np.log(np.asarray(gammas, dtype=float))
    return {"slope": float(np.polyfit(lk, lg, 1)[0]), "local": np.gradient(lg, lk)}


def fit_c(alpha, lam1, kappa_a, kappa_2, window=(1.6, 2.7)) -> dict:
    """Geometric-mean c on the window: exp(mean ln((lam1 - ch1) / ch2(c=1)))."""
    alpha = np.atleast_1d(np.asarray(alpha, dtype=float))
    lam1 = np.atleast_1d(np.asarray(lam1, dtype=float))
    m = (alpha >= window[0]) & (alpha <= window[1])
    ratio = (lam1[m] - gamma_ch1(alpha[m], kappa_a)) / gamma_ch2(alpha[m], kappa_a, kappa_2, c=1.0)
    return {
        "c": float(np.exp(np.mean(np.log(ratio)))),
        "c_min": float(np.min(ratio)),
        "c_max": float(np.max(ratio)),
    }


def load_any(rid, quick=False) -> dict:
    """load_record, or results/quick/records/<rid>.json when quick."""
    if not quick:
        return load_record(rid)
    path = RES_DIR / "quick" / "records" / f"{rid}.json"
    return json.loads(path.read_text())


def _records(model, n_th=0.0, quick=False):
    folder = RES_DIR / ("quick/records" if quick else "records")
    if not folder.is_dir():
        return []
    suffix = f".nth{n_th:g}.json"
    prefix = f"t2_1.gamma_x.eig.{model}."
    out = []
    for path in sorted(folder.glob(prefix + "*" + suffix)):
        rec = json.loads(path.read_text())
        if rec.get("id", "").endswith(f".nth{n_th:g}") and ".a" in rec["id"]:
            out.append(rec)
    return out


def _alpha_of(rec):
    return float(rec["params"]["alpha"])


def _rel(check, claimed):
    return float(abs(check - claimed) / abs(claimed))


def _cross(method, check, claimed, tol, **extra):
    rel = _rel(check, claimed)
    return {"method": method, "value": float(check), "rel_diff": rel, "tol": float(tol),
            "agree": bool(rel <= tol), **extra}


def _level_block(values):
    """values = (level0, level1) of the derived scalar. rel_tol 1e-2 as specified."""
    from src.convergence import convergence_block
    rows = [{"trunc_level": 0, "q": float(values[0])}, {"trunc_level": 1, "q": float(values[1])}]
    return convergence_block({"trunc_level": ({}, rows)}, "q", 1e-2, {"trunc_level": 0})


def _alt_gamma(rec):
    """Largest-truncation sweep value that differs most from the chosen value."""
    chosen = float(rec["value"])
    best = chosen
    best_gap = -1.0
    sweeps = (rec.get("convergence") or {}).get("sweeps") or {}
    for info in sweeps.values():
        vals = info["values"]
        res = info["results"]
        if not res:
            continue
        # largest truncation on this axis
        i = int(np.argmax(vals))
        gap = abs(res[i] - chosen)
        if gap > best_gap:
            best_gap = gap
            best = float(res[i])
    return best


def main(quick=False, skip_kappa=False):
    from tasks.task_2_1_eig import attach_cross_check, record_id, solve

    one = _records("one_mode", 0.0, quick)
    two = _records("two_mode", 0.0, quick)
    if not one and not two:
        print("no nth0 eig records; channels has nothing to overlay")
        return

    def pack(recs):
        recs = sorted(recs, key=_alpha_of)
        a = np.array([_alpha_of(r) for r in recs])
        g = np.array([float(r["value"]) for r in recs])
        return recs, a, g

    one_recs, a1, g1 = pack(one) if one else ([], np.array([]), np.array([]))
    two_recs, a2, g2 = pack(two) if two else ([], np.array([]), np.array([]))

    # (a) fitted c on one-mode, window [1.6, 2.7]. Outside [0.8, 2.0] is a decision, not a clamp.
    c_fit = None
    if len(a1):
        m = (a1 >= 1.6) & (a1 <= 2.7)
        if int(m.sum()) >= 2:
            c_fit = fit_c(a1[m], g1[m], C.KAPPA_A, C.KAPPA_2)
            print("fitted c", c_fit)
            if not (0.8 <= c_fit["c"] <= 2.0):
                print("DECISION NEEDED (l2b-gamma-x): fitted c is outside [0.8, 2.0].")
            g_alt = np.array([_alt_gamma(r) for r in one_recs])
            c_alt = fit_c(a1[m], g_alt[m], C.KAPPA_A, C.KAPPA_2)
            rid = record_id("c2", "one_mode")
            rel = _rel(c_fit["c"], 1.0)
            # tol 0.5: the second-order estimate drops higher orders in kappa_a/kappa_2.
            record(
                rid, task="2.1", quantity="channel2_c", value=c_fit["c"], units="1",
                method="geometric_mean_residual", script=SCRIPT,
                params=std_params(n_th=0.0, model="one_mode"),
                uncertainty=max(abs(c_fit["c"] - c_fit["c_min"]), abs(c_fit["c"] - c_fit["c_max"])),
                convergence=_level_block((c_fit["c"], c_alt["c"])),
                numerics={"c_min": c_fit["c_min"], "c_max": c_fit["c_max"], "window": [1.6, 2.7]},
                cross_check=[_cross("c_equals_1", 1.0, c_fit["c"], 0.5)],
                notes="c = 1 is the cross-check. The fit is not reused as an independent check.",
                quick=quick,
            )
            save_arrays(
                rid, quick=quick, alpha=a1, alpha2=a1 ** 2,
                ch1=np.array([gamma_ch1(a, C.KAPPA_A) for a in a1]),
                ch2=np.array([gamma_ch2(a, C.KAPPA_A, C.KAPPA_2, c=1.0) for a in a1]),
                total=np.array([
                    gamma_ch1(a, C.KAPPA_A) + c_fit["c"] * gamma_ch2(a, C.KAPPA_A, C.KAPPA_2, c=1.0)
                    for a in a1
                ]),
                lam1=g1,
            )

    # (b) parameter-free analytic cross-check, c = 1, tol 0.3
    for rec in list(one_recs) + list(two_recs):
        a = _alpha_of(rec)
        pred = gamma_ch1(a, C.KAPPA_A) + gamma_ch2(a, C.KAPPA_A, C.KAPPA_2, c=1.0)
        attach_cross_check(rec["id"], _cross("analytic_channels", pred, rec["value"], 0.3), quick=quick)

    # (c) kappa_a sweep. One-mode only. Skipped on --quick (that path only reads records).
    if one_recs and not skip_kappa and not quick:
        factors = np.array([0.25, 0.5, 1.0, 2.0, 4.0])
        by_a = {_alpha_of(r): r for r in one_recs}
        for alpha in (1.0, 1.4, 1.8, 2.1):
            rec = by_a.get(alpha)
            if rec is None:
                print("kappa sweep skipped, no one-mode record at", alpha)
                continue
            n0 = int(rec["truncation"]["Na"])
            gammas = []
            gammas_alt = []
            for f in factors:
                ka = float(f) * C.KAPPA_A
                gammas.append(solve("one_mode", alpha, n0, 1, kappa_a=ka)["gamma_x"])
                gammas_alt.append(solve("one_mode", alpha, n0 + 8, 1, kappa_a=ka)["gamma_x"])
            gammas = np.array(gammas)
            gammas_alt = np.array(gammas_alt)
            ex = kappa_a_exponent(factors * C.KAPPA_A, gammas)
            ex_alt = kappa_a_exponent(factors * C.KAPPA_A, gammas_alt)
            pred = np.array([
                gamma_ch1(alpha, f * C.KAPPA_A) + gamma_ch2(alpha, f * C.KAPPA_A, C.KAPPA_2, c=1.0)
                for f in factors
            ])
            ex_pred = kappa_a_exponent(factors * C.KAPPA_A, pred)
            rid = record_id("kexp", "one_mode", alpha)
            record(
                rid, task="2.1", quantity="kappa_a_exponent", value=ex["slope"], units="1",
                method="loglog_polyfit", script=SCRIPT,
                params=std_params(alpha=alpha, n_th=0.0, model="one_mode"),
                truncation={"Na": n0, "Nb": 1},
                convergence=_level_block((ex["slope"], ex_alt["slope"])),
                numerics={"local": [float(x) for x in ex["local"]], "factors": factors.tolist()},
                cross_check=[_cross("analytic_channels_c1", ex_pred["slope"], ex["slope"], 0.1)],
                quick=quick,
            )
            save_arrays(rid, quick=quick, kappa_factor=factors, gamma=gammas, gamma_alt=gammas_alt,
                        local=np.asarray(ex["local"]))
            print("kappa exponent", alpha, ex["slope"])

    # (d) local slope per converged alpha, and (e) global gamma on [1.0, 2.1]
    for model, recs, alphas, gammas in (
        ("one_mode", one_recs, a1, g1), ("two_mode", two_recs, a2, g2),
    ):
        if len(alphas) < 3:
            print("slope/fit skipped for", model, "need >= 3 alphas, have", len(alphas))
            continue
        slope = local_slope(alphas ** 2, gammas)
        g_alt = np.array([_alt_gamma(r) for r in recs])
        slope_alt = local_slope(alphas ** 2, g_alt)
        ch = np.array([gamma_ch1(a, C.KAPPA_A) + gamma_ch2(a, C.KAPPA_A, C.KAPPA_2) for a in alphas])
        slope_ch = local_slope(alphas ** 2, ch)
        for a, s, s_alt, s_ch, rec in zip(alphas, slope, slope_alt, slope_ch, recs):
            if not (rec.get("convergence") or {}).get("converged"):
                continue
            rid = record_id("slope", model, float(a))
            record(
                rid, task="2.1", quantity="gamma_local_slope", value=float(s), units="1",
                method="np_gradient_ln_gamma", script=SCRIPT,
                params=std_params(alpha=float(a), n_th=0.0, model=model),
                truncation=rec.get("truncation"),
                convergence=_level_block((s, s_alt)),
                cross_check=[_cross("analytic_channels_c1", float(s_ch), float(s), 0.25)],
                quick=quick,
            )
        window = (1.0, 2.1)
        if np.sum((alphas >= 1.0) & (alphas <= 2.1)) >= 3:
            fit = global_gamma(alphas ** 2, gammas, window)
            fit_alt = global_gamma(alphas ** 2, g_alt, window)
            fit_ch = global_gamma(alphas ** 2, ch, window)
            numerics = {
                "gamma_stderr": fit["gamma_stderr"], "intercept": fit["intercept"],
                "window": fit["window"],
            }
            for name, win in (("low", (0.8, 1.4)), ("high", (1.8, float(alphas.max())))):
                if np.sum((alphas >= win[0]) & (alphas <= win[1])) >= 3:
                    numerics[f"alt_{name}"] = global_gamma(alphas ** 2, gammas, win)["gamma"]
            rid = record_id("fit", model, n_th=0.0)
            record(
                rid, task="2.1", quantity="gamma_fit", value=fit["gamma"], units="1",
                method="log_linear_alpha2", script=SCRIPT,
                params=std_params(n_th=0.0, model=model),
                uncertainty=fit["gamma_stderr"],
                convergence=_level_block((fit["gamma"], fit_alt["gamma"])),
                numerics=numerics,
                cross_check=[_cross("analytic_channels_c1", fit_ch["gamma"], fit["gamma"], 0.1)],
                notes="Primary window alpha in [1.0, 2.1]. Tol 0.1 vs the c=1 channel model.",
                quick=quick,
            )
            print("gamma_fit", model, fit["gamma"])


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Task 2.1 channel overlays from eig records")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--skip-kappa", action="store_true")
    args = p.parse_args()
    main(quick=args.quick, skip_kappa=args.skip_kappa or args.quick)
