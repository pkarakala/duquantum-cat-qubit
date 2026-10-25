"""Task 2.4 add-on: turn readout SNR into assignment error, including the bit flips the readout causes.

For two coherent output fields sqrt(kappa_b)<b>_+-(t), homodyne along the difference with a matched filter
gives Gaussian outcomes whose means differ by 2 sqrt(SNR) noise standard deviations (SNR as in pulse_eval /
readout: kappa_b int |<b>_+ - <b>_-|^2 dt, efficiency eta). So

    error(t) = 1/2 erfc(sqrt(eta SNR(t) / 2))          (overlap of the two outcome distributions)
             + 1/2 (1 - exp(-Gamma_X(eps_Z) t))        (the memory flipped during the readout)

SNR(t) comes from the step-drive runs (readout.py, T = 4 us, extended linearly at the final rate) and
Gamma_X(eps_Z) from the eigen-solver (gx_eig.py, interpolated in log). We report, per alpha, the best error
over drive level and time, and the shortest time to 99% / 99.9% assignment.
"""
import argparse
import glob
import json

import numpy as np
from scipy.special import erfc

from research.s2.common import save


def gamma_x_table(alpha):
    pts = {}
    for f in glob.glob(f"results/s2/gx_two_a{alpha:.2f}_*_ka1_nth0_ez*_kb1.json"):
        d = json.load(open(f))
        if d["nb"] == 8:
            pts[d["eps_z_over_g2"]] = d["gamma_x"]
    e = np.array(sorted(pts))
    return e, np.array([pts[k] for k in e])


def analyse(path, eta=1.0, tmax=60.0, snr_scale=1.0, gx_scale=1.0):
    d = json.load(open(path))
    t = np.array(d["t"])
    e, g = gamma_x_table(d["alpha"])
    T = np.linspace(0.01, tmax, 12000)
    out = {"alpha": d["alpha"], "best": None, "t99": None, "t999": None}
    for r in d["runs"]:
        eps = r["eps_over_g2"]
        if eps > e.max():                     # no eigen data: Gamma_X would be extrapolated
            continue
        s = np.array(r["snr"])
        rate = (s[-1] - s[-100]) / (t[-1] - t[-100])
        S = snr_scale * np.where(T <= t[-1], np.interp(T, t, s), s[-1] + rate * (T - t[-1]))
        G = gx_scale * np.exp(np.interp(eps, e, np.log(g)))
        err = 0.5 * erfc(np.sqrt(eta * S / 2)) + 0.5 * (1 - np.exp(-G * T))
        i = int(np.argmin(err))
        if out["best"] is None or err[i] < out["best"]["error"]:
            out["best"] = {"error": float(err[i]), "eps_over_g2": eps, "t_us": float(T[i]), "gamma_x": float(G)}
        for key, lim in (("t99", 1e-2), ("t999", 1e-3)):
            ok = np.flatnonzero(err < lim)
            if ok.size and (out[key] is None or T[ok[0]] < out[key]["t_us"]):
                out[key] = {"t_us": float(T[ok[0]]), "eps_over_g2": eps}
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--eta", type=float, default=1.0)
    a = p.parse_args()
    rows = []
    for f in sorted(glob.glob("results/s2/readout_a*_*x8_T4.json")):
        alpha = json.load(open(f))["alpha"]
        if len(gamma_x_table(alpha)[0]) < 4:  # need Gamma_X(eps_Z) to price the flips
            continue
        r = analyse(f, a.eta)
        rows.append(r)
        b = r["best"]
        print(f"alpha {alpha}: best error {b['error']:.2e} (eps {b['eps_over_g2']} g2, t {b['t_us']:.1f} us); "
              f"99% in {r['t99'] and round(r['t99']['t_us'], 2)} us; 99.9% in {r['t999'] and round(r['t999']['t_us'], 2)} us")
    save(f"fidelity_eta{a.eta:g}", {"eta": a.eta, "rows": rows})


if __name__ == "__main__":
    main()
