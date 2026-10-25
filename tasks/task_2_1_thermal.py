"""Task 2.1 thermal photons. n_th = 0 is not rewritten: those IDs are the eig records.

The extra rate is fit against kappa_a n_th exp(-2 alpha^2) after removing 2 n_th Gamma^(1),
because both a and a-dag Golden-Rule matrix elements scale the code-space channel.
c_th is reported, not assumed.
"""
from src import config as C

import argparse

import numpy as np

from src.results import record, std_params
from tasks.task_2_1_channels import (
    _alpha_of, _records, _rel, gamma_ch1, gamma_thermal_extra, global_gamma,
)
from tasks.task_2_1_eig import record_id, run_alpha

SCRIPT = "tasks/task_2_1_thermal.py"


def fit_c_th(alpha, g0, g_th, n_th, kappa_a=C.KAPPA_A, window=(1.6, 2.7)):
    """Least squares of (Delta Gamma - 2 n_th Gamma_ch1) against kappa_a n_th exp(-2 alpha^2)."""
    alpha = np.asarray(alpha, dtype=float)
    m = (alpha >= window[0]) & (alpha <= window[1])
    if int(m.sum()) < 2:
        return None
    a = alpha[m]
    resid = (np.asarray(g_th)[m] - np.asarray(g0)[m]) - 2.0 * n_th * gamma_ch1(a, kappa_a)
    basis = kappa_a * n_th * np.exp(-2.0 * a ** 2)
    return float(np.dot(resid, basis) / np.dot(basis, basis))


def main(model="one_mode", alphas=None, n_ths=None, quick=False):
    n_ths = [n for n in (n_ths or [0.01, 0.03, 0.05]) if n != 0.0]
    if quick:
        model = "one_mode"
        alphas = [1.0]
        n_ths = [0.01]
    if alphas is None:
        alphas = [round(float(a), 2) for a in np.arange(0.8, 2.701, 0.1)] if model == "one_mode" else [1.0, 1.4, 1.8, 2.1]
    for n_th in n_ths:
        for alpha in alphas:
            if quick:
                run_alpha(model, alpha, [20, 24, 28], [1], n_th=n_th, quick=True)
            else:
                from tasks.task_2_1_eig import _default_lists
                na, nb = _default_lists(model, alpha)
                run_alpha(model, alpha, na, nb, n_th=n_th, quick=False)
        vac = _records(model, 0.0, quick)
        hot = _records(model, n_th, quick)
        if len(hot) < 3 or len(vac) < 3:
            print("thermal gamma_fit skipped", model, n_th)
            continue
        by0 = {_alpha_of(r): float(r["value"]) for r in vac}
        pairs = [( _alpha_of(r), float(r["value"])) for r in hot if _alpha_of(r) in by0]
        pairs.sort()
        a = np.array([p[0] for p in pairs])
        g = np.array([p[1] for p in pairs])
        g0 = np.array([by0[x] for x in a])
        if np.sum((a >= 1.0) & (a <= 2.1)) < 3:
            print("thermal window empty", model, n_th)
            continue
        fit = global_gamma(a ** 2, g, (1.0, 2.1))
        fit0 = global_gamma(a ** 2, g0, (1.0, 2.1))
        c_th = fit_c_th(a, g0, g, n_th)
        # c_th = 1 prediction: vacuum curve plus the code-space enhancement and the e^{-2 alpha^2} piece.
        # Tol 0.5 because the brief says this prefactor is uncertain by about x2.
        g_pred = g0 + 2.0 * n_th * gamma_ch1(a, C.KAPPA_A) + gamma_thermal_extra(a, C.KAPPA_A, n_th, c_th=1.0)
        fit_pred = global_gamma(a ** 2, g_pred, (1.0, 2.1))
        rel = _rel(fit_pred["gamma"], fit["gamma"])
        rid = record_id("fit", model, n_th=n_th)
        record(
            rid, task="2.1", quantity="gamma_fit", value=fit["gamma"], units="1",
            method="log_linear_alpha2", script=SCRIPT,
            params=std_params(n_th=n_th, model=model), uncertainty=fit["gamma_stderr"],
            numerics={
                "gamma_stderr": fit["gamma_stderr"], "window": [1.0, 2.1],
                "gamma_nth0": fit0["gamma"], "c_th": c_th,
                "delta_gamma_fit": fit["gamma"] - fit0["gamma"],
            },
            cross_check=[{
                "method": "gautier_cth1_gamma_fit", "value": fit_pred["gamma"],
                "rel_diff": rel, "tol": 0.5, "agree": bool(rel <= 0.5),
            }],
            notes="c_th is a fit, not an assumption. The cross-check uses c_th=1, not the fitted c_th.",
            quick=quick,
        )
        print("thermal", model, n_th, "gamma", fit["gamma"], "c_th", c_th, "vs nth0", fit0["gamma"])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Task 2.1 thermal Gamma_X")
    p.add_argument("--model", choices=("one_mode", "two_mode"), default="one_mode")
    p.add_argument("--alpha", type=float, nargs="*")
    p.add_argument("--nth", type=float, nargs="*", default=[0.01, 0.03, 0.05])
    p.add_argument("--quick", action="store_true")
    args = p.parse_args()
    main(model=args.model, alphas=args.alpha, n_ths=args.nth, quick=args.quick)
