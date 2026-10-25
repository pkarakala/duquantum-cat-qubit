"""Task 2.1: Gamma_X = -lambda_1 of the odd Z2 block, with a truncation sweep at every alpha.

The 20x6 block at alpha=2.1 is a truncation trap (edge weight above 1e-6, rate about 20x too high).
One-mode may extend to N=80. Two-mode auto-extend stays inside l1's NA_EIG_MAX/NB_EIG_MAX
(32 and 8 while config still has None). An explicit --na-list/--nb-list is not clipped.
"""
from src import config as C

import argparse

import numpy as np

from src.convergence import convergence_block, converged_at
from src.model import one_mode, two_mode
from src.results import record, save_arrays, std_params
from src.spectral import gamma_x, low_spectrum

SCRIPT = "tasks/task_2_1_eig.py"
REL_TOL = 1e-3
# l1 measured these; config.py is frozen and still has None.
NA_CAP = C.NA_EIG_MAX or 32
NB_CAP = C.NB_EIG_MAX or 8


def record_id(kind, model, alpha=None, n_th=0.0) -> str:
    if kind == "eig":
        return f"t2_1.gamma_x.eig.{model}.a{alpha:.2f}.nth{n_th:g}"
    if kind == "td":
        return f"t2_1.gamma_x.td.{model}.a{alpha:.2f}"
    if kind == "slope":
        return f"t2_1.gamma_local_slope.eig.{model}.a{alpha:.2f}"
    if kind == "kexp":
        return f"t2_1.kappa_a_exponent.eig.one_mode.a{alpha:.2f}"
    if kind == "fit":
        return f"t2_1.gamma_fit.eig.{model}.nth{n_th:g}"
    if kind == "fit_td":
        return f"t2_1.gamma_fit.td.{model}.nth0"
    if kind == "c2":
        return "t2_1.channel2_c.eig.one_mode.nth0"
    raise ValueError(f"unknown record kind {kind!r}")


def build(model, alpha, Na, Nb, kappa_a=C.KAPPA_A, n_th=0.0):
    if model == "one_mode":
        H, jumps, _ = one_mode(int(Na), C.KAPPA_2, alpha, kappa_a=kappa_a, n_th=n_th)
        return H, jumps
    if model == "two_mode":
        H, jumps, _ = two_mode(
            int(Na), int(Nb), C.G2, alpha ** 2 * C.G2, C.KAPPA_B, kappa_a, n_th=n_th,
        )
        return H, jumps
    raise ValueError(f"model must be 'one_mode' or 'two_mode', got {model!r}")


def solve(model, alpha, Na, Nb, kappa_a=C.KAPPA_A, n_th=0.0) -> dict:
    """gamma_x plus passes = residual < 1e-4 and edge_weight < 1e-6. One-mode uses Nb=1."""
    if model == "one_mode":
        Nb = 1
    H, jumps = build(model, alpha, Na, Nb, kappa_a=kappa_a, n_th=n_th)
    out = gamma_x(H, jumps, int(Na), int(Nb))
    out["passes"] = bool(out["rel_residual"] < 1e-4 and out["edge_weight"] < 1e-6)
    return out


def _default_lists(model, alpha):
    n0 = C.trunc_for(float(alpha), "eig")[0]
    if model == "one_mode":
        return [n0, n0 + 8, n0 + 16], [1]
    nb = [6, 8, 10] if alpha <= 1.4 + 1e-12 else [8, 10, 12]
    return [n0, n0 + 4, n0 + 8], nb


def _grid(model):
    if model == "one_mode":
        return [round(float(a), 2) for a in np.arange(0.8, 2.701, 0.1)]
    alphas = [round(float(a), 2) for a in np.arange(0.8, 3.001, 0.2)]
    if 2.1 not in alphas:
        alphas.append(2.1)
    return sorted(alphas)


def attach_cross_check(rid, entry, quick=False):
    """Replace the cross-check with the same method, or append, and rewrite via record()."""
    from tasks.task_2_1_channels import load_any

    rec = load_any(rid, quick=quick)
    entry = dict(entry)
    rel = float(entry["rel_diff"])
    tol = float(entry["tol"])
    entry["rel_diff"] = rel
    entry["tol"] = tol
    entry["agree"] = bool(rel <= tol)
    checks = list(rec.get("cross_check") or [])
    replaced = False
    new = []
    for c in checks:
        if c.get("method") == entry["method"]:
            new.append(entry)
            replaced = True
        else:
            new.append(c)
    if not replaced:
        new.append(entry)
    prov = rec["provenance"]
    record(
        rid, task=rec["task"], quantity=rec["quantity"], value=rec["value"],
        units=rec["units"], method=rec["method"], params=rec["params"],
        script=prov["script"], truncation=rec.get("truncation"),
        uncertainty=rec.get("uncertainty"), convergence=rec.get("convergence"),
        numerics=rec.get("numerics"), cross_check=new, artifacts=rec.get("artifacts"),
        wall_s=prov.get("wall_s"), notes=rec.get("notes"), quick=quick,
    )


def _uncertainty(block):
    unc = 0.0
    for info in block["sweeps"].values():
        res = info["results"]
        if len(res) >= 2:
            unc = max(unc, abs(res[-1] - res[-2]))
    return float(unc)


def _cache_get(cache, model, alpha, Na, Nb, kappa_a, n_th):
    key = (model, float(alpha), int(Na), int(Nb), float(kappa_a), float(n_th))
    if key not in cache:
        cache[key] = solve(model, alpha, Na, Nb, kappa_a=kappa_a, n_th=n_th)
    return cache[key]


def run_alpha(model, alpha, na_list, nb_list, n_th=0.0, quick=False, full_l_check=False,
              kappa_a=C.KAPPA_A):
    """Sweep, write the eig record, and return its path. One-mode extends by +8 up to N=80."""
    cache = {}
    alpha = float(alpha)
    if model == "one_mode":
        na_list = list(na_list)
        rows = []
        guard = 0
        while guard < 12:
            guard += 1
            rows = []
            for Na in na_list:
                sol = _cache_get(cache, model, alpha, Na, 1, kappa_a, n_th)
                rows.append({"Na": int(Na), "Gamma_X": sol["gamma_x"]})
            chosen_na = int(converged_at(rows, "Gamma_X", "Na", REL_TOL))
            block = convergence_block(
                {"Na": ({"Nb": 1}, rows)}, "Gamma_X", REL_TOL, {"Na": chosen_na},
            )
            if block["converged"] or na_list[-1] >= 80:
                break
            na_list.append(int(na_list[-1]) + 8)
        chosen = _cache_get(cache, model, alpha, chosen_na, 1, kappa_a, n_th)
        trunc = {"Na": int(chosen_na), "Nb": 1}
        sweeps_for_arrays = {"na": [r["Na"] for r in rows], "na_gamma": [r["Gamma_X"] for r in rows]}
    else:
        na_list = list(na_list)
        nb_list = list(nb_list)
        if len(na_list) < 2 or len(nb_list) < 2:
            raise ValueError("two-mode sweeps need at least 2 Na and 2 Nb values")
        extended = False
        while True:
            chosen_na = int(na_list[-2])
            chosen_nb = int(nb_list[-2])
            na_rows = []
            for Na in na_list:
                sol = _cache_get(cache, model, alpha, Na, chosen_nb, kappa_a, n_th)
                na_rows.append({"Na": int(Na), "Gamma_X": sol["gamma_x"]})
            nb_rows = []
            for Nb in nb_list:
                sol = _cache_get(cache, model, alpha, chosen_na, Nb, kappa_a, n_th)
                nb_rows.append({"Nb": int(Nb), "Gamma_X": sol["gamma_x"]})
            block = convergence_block(
                {"Na": ({"Nb": chosen_nb}, na_rows), "Nb": ({"Na": chosen_na}, nb_rows)},
                "Gamma_X", REL_TOL, {"Na": chosen_na, "Nb": chosen_nb},
            )
            if extended or block["converged"]:
                break
            grew = False
            if block["needed"]["Na"] > chosen_na and na_list[-1] + 4 <= NA_CAP:
                na_list.append(int(na_list[-1]) + 4)
                grew = True
            if block["needed"]["Nb"] > chosen_nb and nb_list[-1] + 2 <= NB_CAP:
                nb_list.append(int(nb_list[-1]) + 2)
                grew = True
            extended = True
            if not grew:
                break
        chosen = _cache_get(cache, model, alpha, chosen_na, chosen_nb, kappa_a, n_th)
        trunc = {"Na": int(chosen_na), "Nb": int(chosen_nb)}
        sweeps_for_arrays = {
            "na": [r["Na"] for r in na_rows], "na_gamma": [r["Gamma_X"] for r in na_rows],
            "nb": [r["Nb"] for r in nb_rows], "nb_gamma": [r["Gamma_X"] for r in nb_rows],
        }

    rid = record_id("eig", model, alpha, n_th)
    notes = None
    if quick:
        notes = "quick smoke; not a production claim"
    if not chosen["passes"]:
        notes = ((notes + " ") if notes else "") + (
            "chosen eigenvalue fails acceptance (rel_residual < 1e-4 and edge_weight < 1e-6); not claimable"
        )
    if not block["converged"]:
        notes = ((notes + " ") if notes else "") + "convergence.converged is false; not claimable"
    lams = np.asarray(chosen["lams"])
    numerics = {
        "rel_residual": chosen["rel_residual"],
        "edge_weight": chosen["edge_weight"],
        "cond_est": chosen["cond_est"],
        "sector": "odd",
        "sigma": 0.0,
        "k": 2,
        "passes": chosen["passes"],
    }
    params = std_params(alpha=alpha, n_th=n_th, model=model)
    if float(kappa_a) != float(C.KAPPA_A):
        params = {**params, "kappa_a_over_nominal": float(kappa_a / C.KAPPA_A)}
    arr_name = f"results/quick/arrays/{rid}.npz" if quick else f"results/arrays/{rid}.npz"
    path = record(
        rid, task="2.1", quantity="Gamma_X", value=chosen["gamma_x"],
        uncertainty=_uncertainty(block), units="1/us", method="liouvillian_eig_odd_sector",
        params=params, script=SCRIPT, truncation=trunc, convergence=block, numerics=numerics,
        artifacts={"arrays": arr_name, "figure": "figures/task_2_1_gamma_x.png"},
        wall_s=float(sum(s["wall_s"] for s in cache.values())), notes=notes, quick=quick,
    )
    save_arrays(
        rid, quick=quick, lams_real=np.real(lams), lams_imag=np.imag(lams), **{
            k: np.asarray(v) for k, v in sweeps_for_arrays.items()
        },
    )
    print(
        f"RESULT {rid} gamma_x={chosen['gamma_x']:.6e} trunc={trunc} "
        f"passes={chosen['passes']} converged={block['converged']} "
        f"resid={chosen['rel_residual']:.3e} edge={chosen['edge_weight']:.3e}"
    )
    if full_l_check:
        H, jumps = build(model, alpha, trunc["Na"], trunc["Nb"], kappa_a=kappa_a, n_th=n_th)
        spec = low_spectrum(H, jumps, trunc["Na"], trunc["Nb"], k=4, sector="full_deflated")
        rate = float(spec["rates"][0])
        rel = abs(rate - chosen["gamma_x"]) / abs(chosen["gamma_x"])
        attach_cross_check(
            rid,
            {"method": "full_deflated_liouvillian", "value": rate, "rel_diff": rel, "tol": 1e-3},
            quick=quick,
        )
        print(f"FULL_L {rid} rate={rate:.6e} rel_diff={rel:.3e}")
    return path


def _anchors():
    """Print the anchor table. Writes nothing."""
    print("one-mode N=40")
    for alpha, anchor in ((1.0, 2.2819e-3), (1.4, 1.0744e-4), (1.8, 2.0693e-6), (2.1, 1.1699e-7)):
        out = solve("one_mode", alpha, 40, 1)
        rel = abs(out["gamma_x"] - anchor) / anchor
        print(f"  a={alpha:.1f} anchor={anchor:.4e} got={out['gamma_x']:.6e} rel={rel:.3e} "
              f"passes={out['passes']} edge={out['edge_weight']:.3e}")
    print("two-mode 28x8")
    for alpha, anchor in ((1.0, 2.3007e-3), (1.4, 1.2021e-4), (1.8, 4.0696e-6), (2.1, 3.8831e-7)):
        out = solve("two_mode", alpha, 28, 8)
        rel = abs(out["gamma_x"] - anchor) / anchor
        print(f"  a={alpha:.1f} anchor={anchor:.4e} got={out['gamma_x']:.6e} rel={rel:.3e} "
              f"passes={out['passes']} edge={out['edge_weight']:.3e}")
    print("alpha=2.1 Nb=6 Na=28/32/36 (expect ~3.987e-7) and the 20x6 trap")
    for Na, Nb, anchor in ((28, 6, 3.987e-7), (32, 6, 3.987e-7), (36, 6, 3.987e-7), (20, 6, 7.607e-6)):
        out = solve("two_mode", 2.1, Na, Nb)
        rel = abs(out["gamma_x"] - anchor) / anchor
        print(f"  {Na}x{Nb} anchor={anchor:.4e} got={out['gamma_x']:.6e} rel={rel:.3e} "
              f"passes={out['passes']} edge={out['edge_weight']:.3e}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Task 2.1 Gamma_X eigenvalues")
    p.add_argument("--model", choices=("one_mode", "two_mode"))
    p.add_argument("--alpha", type=float, nargs="*")
    p.add_argument("--na-list", default=None)
    p.add_argument("--nb-list", default=None)
    p.add_argument("--nth", type=float, default=0.0)
    p.add_argument("--full-l-check", action="store_true")
    p.add_argument("--anchors", action="store_true")
    p.add_argument("--quick", action="store_true")
    args = p.parse_args(argv)
    if args.anchors:
        _anchors()
        return
    na_user = [int(x) for x in args.na_list.split(",")] if args.na_list else None
    nb_user = [int(x) for x in args.nb_list.split(",")] if args.nb_list else None
    models = [args.model] if args.model else (["one_mode", "two_mode"] if args.quick else ["one_mode"])
    for model in models:
        if args.quick and model == "one_mode":
            alphas, na, nb = [1.0, 1.4], [20, 24, 28], [1]
        elif args.quick and model == "two_mode":
            alphas, na, nb = [1.0], [14, 16, 18], [4, 6]
        else:
            alphas = args.alpha if args.alpha else _grid(model)
            na, nb = na_user, nb_user
        for alpha in alphas:
            na_def, nb_def = _default_lists(model, alpha)
            na_i = na if na is not None else na_def
            nb_i = nb if nb is not None else nb_def
            if model == "one_mode":
                nb_i = [1]
            run_alpha(model, alpha, na_i, nb_i, n_th=args.nth, quick=args.quick,
                      full_l_check=args.full_l_check)


if __name__ == "__main__":
    main()
