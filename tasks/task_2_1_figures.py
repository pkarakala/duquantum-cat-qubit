"""Task 2.1 figures. Reads records only, except --committor which diagonalizes once.

--committor is a separate job: it is an eigen solve, not a record read.
"""
from src import config as C

import argparse
import json

import matplotlib.pyplot as plt
import numpy as np

from src.plotting import save
from src.results import RES_DIR
from tasks.task_2_1_channels import gamma_ch1, gamma_ch2, load_any
from tasks.task_2_1_eig import record_id


def _load_all(quick=False):
    folder = RES_DIR / ("quick/records" if quick else "records")
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("t2_1.*.json")):
        out.append(json.loads(path.read_text()))
    return out


def _series(recs, prefix):
    rows = [r for r in recs if r["id"].startswith(prefix) and r["id"].endswith(".nth0")]
    rows.sort(key=lambda r: r["params"]["alpha"])
    return rows


def _fig_gamma(recs, quick):
    one = _series(recs, "t2_1.gamma_x.eig.one_mode.")
    two = _series(recs, "t2_1.gamma_x.eig.two_mode.")
    if not one and not two:
        print("skip task_2_1_gamma_x: no eig records")
        return
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    if one:
        a = np.array([r["params"]["alpha"] for r in one])
        g = np.array([r["value"] for r in one])
        ok = np.array([bool((r.get("convergence") or {}).get("converged")) for r in one])
        ax.plot(a[ok] ** 2, g[ok], "o-", color="C0", label="one-mode eig")
        if np.any(~ok):
            ax.plot(a[~ok] ** 2, g[~ok], "o", color="0.6", label="one-mode unconverged")
        aa = np.linspace(min(a), max(a), 200)
        ch1 = np.array([gamma_ch1(x, C.KAPPA_A) for x in aa])
        ch2 = np.array([gamma_ch2(x, C.KAPPA_A, C.KAPPA_2, c=1.0) for x in aa])
        c = 1.0
        try:
            c = float(load_any(record_id("c2", "one_mode"), quick=quick)["value"])
        except (FileNotFoundError, OSError, ValueError, KeyError):
            pass
        ax.plot(aa ** 2, ch1, "--", color="C0", lw=1, label="channel 1")
        ax.plot(aa ** 2, ch2, ":", color="C1", lw=1, label="channel 2, c=1")
        ax.plot(aa ** 2, ch1 + c * ch2, color="C3", lw=1, label=f"ch1 + {c:.2f} ch2")
    if two:
        a = np.array([r["params"]["alpha"] for r in two])
        g = np.array([r["value"] for r in two], dtype=float)
        u = np.array([r["uncertainty"] or 0.0 for r in two], dtype=float)
        ax.errorbar(a ** 2, g, yerr=u, fmt="s", color="C2", label="two-mode eig")
    td = [r for r in recs if r["id"].startswith("t2_1.gamma_x.td.")]
    if td:
        ax.plot([r["params"]["alpha"] ** 2 for r in td], [r["value"] for r in td],
                "o", mfc="none", color="k", label="time domain")
    ax.axvline(2.1 ** 2, color="0.5", lw=0.8)
    ax.set(yscale="log", xlabel=r"$\alpha^2$", ylabel=r"$\Gamma_X$ (1/µs)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    if one and two:
        by1 = {r["params"]["alpha"]: r["value"] for r in one}
        by2 = {r["params"]["alpha"]: r["value"] for r in two}
        common = sorted(set(by1) & set(by2))
        if common:
            ins = ax.inset_axes([0.15, 0.15, 0.35, 0.28])
            ins.plot(common, [by2[a] / by1[a] for a in common], "s-")
            ins.set_title("two/one", fontsize=8)
            ins.tick_params(labelsize=7)
    save(fig, "task_2_1_gamma_x", quick=quick)
    plt.close(fig)


def _fig_slope(recs, quick):
    rows = [r for r in recs if r["id"].startswith("t2_1.gamma_local_slope.")]
    if not rows:
        print("skip task_2_1_local_slope")
        return
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for model in ("one_mode", "two_mode"):
        sub = [r for r in rows if f".{model}." in r["id"]]
        sub.sort(key=lambda r: r["params"]["alpha"])
        if sub:
            ax.plot([r["params"]["alpha"] ** 2 for r in sub], [r["value"] for r in sub], "o-", label=model)
    ax.axhline(4, color="0.4", lw=0.8, label="4")
    ax.axhline(2, color="0.4", lw=0.8, ls="--", label="2")
    ax.axhline(np.log(4.2), color="C3", lw=0.8, ls=":", label="ln 4.2")
    ax.set(xlabel=r"$\alpha^2$", ylabel=r"local $\gamma$")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    save(fig, "task_2_1_local_slope", quick=quick)
    plt.close(fig)


def _fig_kappa(recs, quick):
    rows = [r for r in recs if r["id"].startswith("t2_1.kappa_a_exponent.")]
    if not rows:
        print("skip task_2_1_kappa_a_sweep")
        return
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    rows.sort(key=lambda r: r["params"]["alpha"])
    ax.plot([r["params"]["alpha"] ** 2 for r in rows], [r["value"] for r in rows], "o-")
    ax.axhline(1, color="0.4", lw=0.8)
    ax.axhline(2, color="0.4", lw=0.8, ls="--")
    ax.set(xlabel=r"$\alpha^2$", ylabel=r"d ln $\Gamma_X$ / d ln $\kappa_a$")
    ax.grid(alpha=0.3)
    save(fig, "task_2_1_kappa_a_sweep", quick=quick)
    plt.close(fig)


def _fig_thermal(recs, quick):
    rows = [r for r in recs if r["id"].startswith("t2_1.gamma_x.eig.") and not r["id"].endswith(".nth0")]
    if not rows:
        print("skip task_2_1_thermal")
        return
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    nth_vals = sorted({r["params"]["n_th"] for r in rows})
    for n in nth_vals:
        sub = [r for r in rows if r["params"]["n_th"] == n and "one_mode" in r["id"]]
        sub.sort(key=lambda r: r["params"]["alpha"])
        if sub:
            ax.plot([r["params"]["alpha"] ** 2 for r in sub], [r["value"] for r in sub], "o-", label=f"n_th={n:g}")
    ax.set(yscale="log", xlabel=r"$\alpha^2$", ylabel=r"$\Gamma_X$ (1/µs)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    save(fig, "task_2_1_thermal", quick=quick)
    plt.close(fig)


def _committor(quick=False):
    """One-mode right and left odd eigenvectors at alpha=2.1. Two-mode only if a record exists."""
    import dynamiqs as dq
    from scipy.sparse.linalg import eigs

    from src.model import one_mode
    from src.spectral import left_eigvec_operator, liouvillian, sector_indices, unvec

    try:
        rec = load_any(record_id("eig", "one_mode", 2.1, 0.0), quick=quick)
        N = int(rec["truncation"]["Na"])
    except (FileNotFoundError, OSError, ValueError, KeyError):
        N = C.trunc_for(2.1, "eig")[0]
    H, jumps, _a = one_mode(N, C.KAPPA_2, 2.1, kappa_a=C.KAPPA_A)
    L = liouvillian(H, jumps)
    idx = sector_indices(N, 1, 1)
    A = L.tocsr()[idx, :].tocsc()[:, idx]
    vals, vecs = eigs(A, k=2, sigma=0.0, which="LM", tol=1e-12)
    j = int(np.argmin(np.abs(vals)))
    v = np.zeros(L.shape[0], dtype=complex)
    v[idx] = vecs[:, j]
    right = unvec(v, N)
    left = left_eigvec_operator(H, jumps, N, 1, sector="odd")
    left_h = 0.5 * (left + left.conj().T)

    def panel(op):
        _x, _y, w = dq.wigner(np.asarray(op), xmax=5.0, ymax=5.0, npixels=81)
        w = np.asarray(w)
        return w

    panels = [panel(right), panel(left_h)]
    titles = [f"one-mode right, N={N}", "one-mode left"]
    try:
        rec2 = load_any(record_id("eig", "two_mode", 2.1, 0.0), quick=quick)
        Na, Nb = int(rec2["truncation"]["Na"]), int(rec2["truncation"]["Nb"])
        from src.model import two_mode
        H2, jumps2, _ = two_mode(Na, Nb, C.G2, 2.1 ** 2 * C.G2, C.KAPPA_B, C.KAPPA_A)
        W = left_eigvec_operator(H2, jumps2, Na, Nb, sector="odd")
        W = 0.5 * (W + W.conj().T)
        mem = dq.ptrace(dq.asqarray(W, dims=(Na, Nb)), 0, (Na, Nb))
        panels.append(panel(mem))
        titles.append(f"two-mode memory, {Na}x{Nb}")
    except (FileNotFoundError, OSError, ValueError, KeyError):
        pass
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 3.6))
    if len(panels) == 1:
        axes = [axes]
    for ax, w, title in zip(axes, panels, titles):
        v = float(np.max(np.abs(w))) or 1.0
        ax.imshow(np.asarray(w).T, origin="lower", cmap="RdBu_r", vmin=-v, vmax=v,
                  extent=[-5, 5, -5, 5])
        ax.set_title(title, fontsize=9)
        ax.set(xlabel="Re", ylabel="Im")
    save(fig, "task_2_1_committor_wigner", quick=quick)
    plt.close(fig)


def main(quick=False, committor=False):
    recs = _load_all(quick)
    if not recs:
        print("no t2_1 records; figures skipped")
    else:
        _fig_gamma(recs, quick)
        _fig_slope(recs, quick)
        _fig_kappa(recs, quick)
        _fig_thermal(recs, quick)
    if committor:
        _committor(quick)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Task 2.1 figures from records")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--committor", action="store_true")
    args = p.parse_args()
    main(quick=args.quick, committor=args.committor)
