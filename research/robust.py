"""How much does the stabilization forgive a miscalibrated displacement pulse?

Prepare |+alpha> by displacing the vacuum to |beta> and letting the two-photon dissipation
finish the job. Without stabilization the result is just |beta>, with fidelity
|<alpha|beta>|^2 = exp(-|beta - alpha|^2). With it, every beta in the right half-plane is
pulled toward +alpha, so errors in pulse phase and amplitude are largely forgiven.
We use the Heisenberg basin map of research/heis.py (effective one-mode model, T = 1 us) to
get the fidelity for every beta at once, and report the windows of phase and amplitude
error that still give F >= 0.99 and 0.999. Task 1.3b checks the same thing in the two-mode model.
Run:  python -m research.robust [--n 30 --t 1.0]   (seconds)
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt

from src import config as C
from src.plotting import save as save_fig
from src.results import save as save_res
from research.common import OUT, basin_map, coherent_fidelity


def window(x, ok):
    return [float(x[ok].min()), float(x[ok].max())] if ok.any() else None


def main(N, T):
    J, _ = basin_map(N, T)
    raw = lambda be: np.exp(-np.abs(be - C.ALPHA) ** 2)
    bs = np.linspace(0.5, 4.0, 351)
    ths = np.linspace(0, 90, 181)
    pb = C.ALPHA * np.exp(1j * np.deg2rad(ths))
    Fs, Fp = coherent_fidelity(J, bs), coherent_fidelity(J, pb)
    out = {"N": N, "T_us": T, "alpha": C.ALPHA,
           "phase_table": {f"{d}": {"stabilized": float(Fp[np.argmin(np.abs(ths - d))]),
                                    "raw": float(raw(pb[np.argmin(np.abs(ths - d))]))}
                           for d in (0, 10, 20, 30, 45, 60, 75)}}
    for th in (0.99, 0.999):
        out[f"F{th}"] = {"amplitude_window_stabilized": window(bs, Fs >= th),
                         "amplitude_window_raw": window(bs, raw(bs) >= th),
                         "max_phase_error_stabilized_deg": float(ths[Fp >= th].max()) if (Fp >= th).any() else None,
                         "max_phase_error_raw_deg": float(ths[raw(pb) >= th].max()) if (raw(pb) >= th).any() else None}
    print(out)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot(ths, Fp, lw=2, label=f"stabilized ({T} µs)"); ax[0].plot(ths, raw(pb), "--", lw=2, label="pulse alone")
    ax[0].set(xlabel="phase error (deg), |β| = α", ylabel="fidelity with |+α⟩")
    ax[1].plot(bs, Fs, lw=2, label=f"stabilized ({T} µs)"); ax[1].plot(bs, raw(bs), "--", lw=2, label="pulse alone")
    ax[1].set(xlabel="real β")
    for x in ax:
        x.axhline(0.99, color="gray", ls=":"); x.legend(fontsize=8); x.grid(alpha=0.3); x.set_ylim(0, 1.02)
    save_fig(fig, f"{OUT}/robust_N{N}")
    save_res(f"{OUT}/robust_N{N}", out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=C.N_SINGLE)
    p.add_argument("--t", type=float, default=1.0)
    a = p.parse_args()
    main(a.n, a.t)
