"""Rewrite the L5 and L7 presets from main's verified results (no hand-typed numbers).

    python site/scripts/export_main_l5_l7.py [--ref origin/main]

Run from the repo root. Reads results/s2/*.json straight out of git (git show <ref>:<path>),
so the working tree can stay on `integrated`. Selection mirrors research/s2/summarize.py on main:
per alpha keep the largest truncation (Na*Nb), n_th = 0, eps_Z = 0, kappa_a = kappa_b = default.
Two-mode Gamma_X is kept for alpha <= 2.5 (main's ALPHA_CONVERGED); other points are kept only when
their truncation spread is under 5%. Every record id is "main@<sha>:<path>" so the UI chips cite
the exact file. Valley 1 readout traces use main's symmetry <b>_-(t) = -<b>_+(t)^* (readout.py).
Nothing that is not on main is filled in: eps = 3 has no Gamma_X(eps) run, so its cost stays null.
"""
import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path

PRESETS = Path(__file__).resolve().parents[1] / "src" / "academy" / "presets"
KAPPA_A = 0.058433623356770145
ALPHA_CONVERGED = 2.5
SPREAD_MAX = 0.05
READOUT_GRID = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0]
READOUT_ALPHA = 2.1
DECIMATE = 6  # 601 samples over 4 us -> one every 0.04 us (about 8 per 3.2 MHz ring period)


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def load(ref, path):
    return json.loads(git("show", f"{ref}:{path}"))


def default_bath(d):
    return d["n_th"] == 0 and d["kappa_a"] == KAPPA_A and abs(d["kappa_b"] - 16.336281798666924) < 1e-9


def best_by_alpha(rows, key):
    by = defaultdict(list)
    for path, d in rows:
        if key in d:
            by[round(d["alpha"], 3)].append((path, d))
    out = {}
    for al, rs in sorted(by.items()):
        rs.sort(key=lambda pr: pr[1]["na"] * (pr[1]["nb"] or 1))
        top_path, top = rs[-1]
        spread = max(abs(d[key] - top[key]) / top[key] for _, d in rs) if len(rs) > 1 else 0.0
        out[al] = (top[key], spread, top_path)
    return out


def r6(x):
    return float(f"{x:.6g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="origin/main")
    a = ap.parse_args()
    sha = git("rev-parse", "--short", a.ref).strip()
    cite = lambda p: f"main@{sha}:{p}"  # noqa: E731
    files = [p for p in git("ls-tree", "-r", "--name-only", a.ref, "results/s2").split() if p.endswith(".json")]
    gx = [(p, load(a.ref, p)) for p in files if p.split("/")[-1].startswith("gx_")]
    base = [(p, d) for p, d in gx if d["eps_z_over_g2"] == 0 and default_bath(d)]

    def grid(model, alpha_max):
        rows = [(p, d) for p, d in base if d["model"] == model]
        gxs = best_by_alpha(rows, "gamma_x")
        gzs = best_by_alpha(rows, "gamma_z_eig")
        keep = lambda tbl: [  # noqa: E731
            {"alpha2": r6(al * al), "gamma": v, "id": cite(path)}
            for al, (v, spread, path) in tbl.items() if al <= alpha_max and spread <= SPREAD_MAX
        ]
        return {"gammaX": keep(gxs), "gammaZ": keep(gzs)}

    two = grid("two", ALPHA_CONVERGED)
    one = grid("one", 3.0)
    l5 = [{
        "id": "L5", "levelId": "L5", "source": "precomputed",
        "params": {"alpha2": 4, "model": "one_mode"}, "ranges": {"alpha2": [1, 9]},
        "result": {
            "summary": f"Liouvillian-gap rates from main@{sha} (results/s2/gx_*.json)",
            "records": one, "recordsByModel": {"one_mode": one, "two_mode": two},
            "meta": {"source": "precomputed", "provenance": f"main@{sha}:results/s2/gx_*.json via site/scripts/export_main_l5_l7.py"},
        },
        "note": f"Real: Gamma_X (gamma_x) and Gamma_Z (gamma_z_eig) from main@{sha} results/s2/gx_{{one,two}}_*.json, largest truncation per alpha, two-mode alpha <= 2.5.",
    }]

    # L7: readout traces + SNR(1 us) at alpha = 2.1, Gamma_X(eps)/Gamma_X(0) from the 2.4b runs.
    # Largest truncation whose run list covers the whole eps grid.
    covering = []
    for p in sorted(f for f in files if f.split("/")[-1].startswith(f"readout_a{READOUT_ALPHA:.2f}_")):
        d = load(a.ref, p)
        have = {r["eps_over_g2"] for r in d["runs"]}
        if all(any(abs(e - h) < 1e-9 for h in have) for e in READOUT_GRID):
            covering.append((d["na"] * d["nb"], p, d))
    _, ro_path, ro = max(covering)
    t = ro["t"]
    i1 = next(i for i, x in enumerate(t) if x >= 1.0 - 1e-12)  # np.searchsorted(t, 1.0), as summarize.py
    g0 = best_by_alpha([(p, d) for p, d in base if d["model"] == "two"], "gamma_x")[READOUT_ALPHA]
    drive = [(p, d) for p, d in gx if d["model"] == "two" and d["eps_z_over_g2"] > 0 and default_bath(d)
             and abs(d["alpha"] - READOUT_ALPHA) < 1e-9]
    by_eps = defaultdict(list)
    for p, d in drive:
        by_eps[d["eps_z_over_g2"]].append((p, d))
    cost = {}
    for eps, rs in by_eps.items():
        p, d = max(rs, key=lambda pr: pr[1]["na"] * pr[1]["nb"])
        cost[eps] = (d["gamma_x"] / g0[0], p)
    tradeoff, entries = [], []
    for eps in READOUT_GRID:
        run = next(r for r in ro["runs"] if abs(r["eps_over_g2"] - eps) < 1e-9)
        snr1 = run["snr"][i1]
        rel, cpath = cost.get(eps, (None, None))
        row = {"eps": eps, "snr": r6(snr1), "alpha": READOUT_ALPHA, "id": cite(ro_path)}
        if rel is not None:
            row["gammaXRel"] = r6(rel)
            row["gammaXRelId"] = cite(cpath)
        tradeoff.append(row)
        idx = list(range(0, len(t), DECIMATE))
        bre = [r6(run["b_re"][i]) for i in idx]
        bim = [r6(run["b_im"][i]) for i in idx]
        entries.append((eps, {
            "summary": f"Readout traces from main@{sha}:{ro_path}",
            "signals": {"tUs": [r6(t[i]) for i in idx], "bPlusRe": bre, "bPlusIm": bim,
                        "bMinusRe": [r6(-x) for x in bre], "bMinusIm": bim},
            "snr": r6(snr1),
            "ring": {"fMHz": r6(run["ring"]["f_MHz"]), "Q": r6(run["ring"]["Q"]), "settle1pctUs": run["settle_1pct_us"]},
            "meta": {"source": "precomputed", "provenance": cite(ro_path)},
        }))
    l7 = []
    for eps, result in entries:
        result["tradeoff"] = tradeoff
        pid = "L7" if eps == 1.0 else "L7_eps_" + (f"{eps:g}".replace(".", "_"))
        l7.append({
            "id": pid, "levelId": "L7", "source": "precomputed",
            "params": {"eps": eps if eps != int(eps) else int(eps), "valley": "0"}, "ranges": {"eps": [0.05, 3]},
            "result": result,
            "note": (f"Real: main@{sha}:{ro_path} (alpha 2.1, {ro['na']}x{ro['nb']}), every {DECIMATE}th sample; "
                     "valley 1 = -conj(valley 0) per research/s2/readout.py. Bit-flip cost = Gamma_X(eps)/Gamma_X(0) from "
                     "results/s2/gx_two_a2.10_*_ez*.json" + ("" if eps in cost else "; no Gamma_X run at this eps on main, cost left blank") + "."),
        })
    (PRESETS / "L5.json").write_text(json.dumps(l5, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (PRESETS / "L7.json").write_text(json.dumps(l7, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("sha", sha, "readout", ro_path, "g0", g0)
    for k, g in (("one", one), ("two", two)):
        print(k, "gammaX", [(p["alpha2"], f"{p['gamma']:.4e}") for p in g["gammaX"]])
        print(k, "gammaZ", [(p["alpha2"], f"{p['gamma']:.5f}") for p in g["gammaZ"]])
    for row in tradeoff:
        print("L7", row["eps"], row["snr"], row.get("gammaXRel"))


if __name__ == "__main__":
    main()
