"""Export the Section 2 numbers the site's Results pages plot. Reads only saved results/.

    python site/scripts/export_results.py      # writes site/src/research/results.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.s2 import notebook_figs as F
from research.s2.common import G2, KAPPA_A, KAPPA_B, KAPPA_2
from src import spectral as S

OUT = ROOT / "site" / "src" / "research" / "results.json"


def rnd(x, s=5):
    return float(f"{float(x):.{s}g}")


def bit_flips():
    two = {a: d for a, d in F.largest(d for d in F.load("gx_two_*.json") if F.nominal(d)).items() if a <= 2.5}
    td = json.loads((ROOT / "results" / "task_2_1.json").read_text())
    ag = np.linspace(0.7, 2.5, 60)
    slopes = []
    by = {}
    for d in F.load("gx_two_*.json"):
        if d["eps_z_over_g2"] == 0 and d["n_th"] == 0 and abs(d["kappa_b"] / (2 * np.pi) - 2.6) < 1e-9:
            by.setdefault(d["alpha"], {}).setdefault((d["na"], d["nb"]), {})[d["kappa_a"]] = d["gamma_x"]
    for a, sizes in sorted(by.items()):
        cands = [(na * nb, m) for (na, nb), m in sizes.items() if len(m) >= 3]
        if cands:
            m = max(cands, key=lambda c: c[0])[1]
            k = np.array(sorted(m))
            slopes.append([rnd(a**2), rnd(np.polyfit(np.log(k), np.log([m[x] for x in k]), 1)[0], 3)])
    return {
        "eig": [{"alpha": a, "gx": rnd(d["gamma_x"]), "na": d["na"], "nb": d["nb"]} for a, d in two.items()],
        "td": [{"alpha": rnd(c["alpha"], 3), "fit": rnd(c["fit"]["gamma_per_us"]), "eig": rnd(c["eigenvalue"]["gamma_per_us"]),
                "rel": rnd(c["checks"]["fit_vs_eigen_relative_change"], 2)} for c in td["cases"]],
        "gamma_fit": rnd(td["scaling_fit"]["exponent"], 3),
        "one_loss": [[rnd(a**2), rnd(S.gamma_x_channel1(a, KAPPA_A))] for a in ag],
        "two_loss": [[rnd(a**2), rnd(S.gamma_x_channel2(a, KAPPA_A, KAPPA_2))] for a in ag],
        "kappa_slope": slopes,
    }


def phase_flips():
    d = json.loads((ROOT / "results" / "task_2_2.json").read_text())
    return {
        "cases": [{"alpha": rnd(c["alpha"], 3), "fit": rnd(c["fit"]["gamma_per_us"], 7), "eig": rnd(c["eigenvalue"]["gamma_per_us"], 7),
                   "offset": rnd(c["fit"]["offset"], 4), "rel": rnd(c["checks"]["fit_vs_eigen_relative_change"], 2),
                   "ideal": rnd(S.gamma_z_theory(c["alpha"], KAPPA_A), 7)} for c in d["cases"]],
        "slope": rnd(d["scaling_fit"]["slope_per_us"], 5),
        "slope_pred": rnd(d["scaling_fit"]["predicted_slope_per_us"], 5),
    }


def readout():
    d = json.loads((ROOT / "results" / "task_2_3.json").read_text())
    z = np.load(ROOT / "results" / "task_2_3_trajectories.npz")
    i = int(np.argmin(abs(z["production_ratios"] - 0.05)))
    t = z["production_t"]
    b = z["production_expects"][i, :, d["observable_order"].index("b"), :]
    b0 = 0.05 * G2 / (2 * d["configuration"]["alpha"] * G2)
    s = [x for x in d["drive_summaries"] if abs(x["drive_ratio"] - 0.05) < 1e-9][0]
    k = slice(None, None, 4)
    return {
        "b0": rnd(b0), "t": [rnd(x, 4) for x in t[k]],
        "re_plus": [rnd(x / b0, 4) for x in b[0].real[k]], "re_minus": [rnd(x / b0, 4) for x in b[1].real[k]],
        "settle_us": s["settling_time_us"], "ring_us": rnd(s["ring_period_us"], 3), "contrast_err": rnd(s["relative_contrast_error"], 3),
        "lin_period_us": rnd(d["linearized"]["period_us"], 3),
    }


def better_readout():
    p = F.load("pulse_a2.10_30x8_T2_peak.json")[0]
    rows = []
    for r in p["rows"]:
        if r["family"] == "none":
            continue
        rows.append({"family": r["family"], "level": r["level"], "snr": rnd(r["snr"], 4), "p_flip": rnd(r["p_flip"], 4),
                     "err1": rnd(F.readout_error(r, 1.0), 4), "err05": rnd(F.readout_error(r, 0.5), 4),
                     "b_re": [rnd(x, 4) for x in r["b_re"]], "b_im": [rnd(x, 4) for x in r["b_im"]],
                     "pulse": [rnd(x, 4) for x in r["pulse_over_g2"]]})
    best = {f: min((r for r in rows if r["family"] == f), key=lambda r: r["err1"]) for f in ("square", "res", "bang")}
    best05 = {f: min(r["err05"] for r in rows if r["family"] == f) for f in ("square", "res", "bang")}
    scan = sorted(F.load("circuit_na10_nb4_T0.15_dp*.json"), key=lambda d: d["dp_MHz"])
    o = F.load("opt_a2.10_30x8_T0.5_pk1_bang_mu1_s0.json")[0]
    wr = np.sqrt(4 * G2**2 * o["alpha"]**2 - KAPPA_B**2 / 16)
    tb = (np.arange(o["bins"]) + 0.5) * o["T"] / o["bins"]
    return {
        "T": p["T"], "t": [rnd(x, 4) for x in p["t"]], "rows": rows,
        "best": {f: {"level": r["level"], "err1": r["err1"]} for f, r in best.items()}, "best05": best05,
        "omega_r_MHz": rnd(wr / (2 * np.pi), 3),
        "circuit": [[d["dp_MHz"], rnd(d["max_abs_diff_na_averaged"], 4)] for d in scan],
        "opt": {"t": [rnd(x, 4) for x in tb], "peak": o["peak"], "start": [rnd(o["peak"] * np.sign(np.cos(wr * x)), 3) for x in tb],
                "best": [rnd(x, 4) for x in o["best"]["pulse_over_g2"]]},
    }


def main():
    out = {"source": "results/ (tasks 2.1-2.4); regenerate with python site/scripts/export_results.py",
           "params": {"g2": rnd(G2), "kappa_b": rnd(KAPPA_B), "kappa_a": rnd(KAPPA_A), "kappa_2": rnd(KAPPA_2), "alpha": 2.1},
           "gx": bit_flips(), "gz": phase_flips(), "readout": readout(), "better": better_readout()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
