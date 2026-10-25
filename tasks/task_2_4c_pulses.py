"""Task 2.4c: linear-response readout pulses and the matched-cost frontier.

The map from ε_Z(t) to Δ⟨b⟩ is the matrix R_b. Its top right-singular vector maximises
signal energy at fixed drive energy. Gains here are that identity, inside linear response.
A two-mode win is a separate check (tasks/task_2_4c_verify.py) and is not claimed here.

Cost (iii) uses Dubovitskii's Z-drive term when the l4b grid is absent:
per-direction (2 ε² /(κ₂ α²)) e^{−2α²}, doubled because our Γ_X is twice per-direction.
That proxy is proportional to ∫ε² dt, so matched C_X equals matched drive energy.
"""
import argparse
import time

import numpy as np
import matplotlib.pyplot as plt

from src import config as C
from src.linresp import optimal_pulse, response_matrices, ringing
from src.plotting import save as save_fig
from src.provenance import git_info
from src.pulses import (
    clear, energy, from_bins, leakage_proxy, ramp, snr, square,
)
from src.results import save_arrays, std_params, record

# Reference square sits at 0.1 g₂ (RESEARCH §7 signal-size point, inside the linear regime).
REF_OVER_G2 = 0.1
SQUARE_SWEEP = (0.05, 0.1, 0.25, 0.5, 0.75, 1.0)
RAMP_TAUS = (0.1, 0.2, 0.4, 0.8)
CLEAR_KICKS = (1.5, 2.0, 3.0)
CLEAR_TIMES = (0.05, 0.10, 0.16)
BIN_DT = 0.025  # µs; T = 1 µs → 40 bins, the same grid as the fast tests
SAMPLES_PER_US = 200
COST_NOTE = (
    "illustrative: analytic cost proxy until l4b grid lands. "
    "Dubovitskii per-direction (2 eps^2/(kappa_2 alpha^2)) exp(-2 alpha^2), "
    "doubled to our Gamma_X. Under this proxy C_X ∝ drive energy, so matched "
    "cost (iii) equals matched cost (i)."
)


def n_bins_for(T):
    return max(8, int(round(float(T) / BIN_DT)))


def sample_grid(T):
    n_samples = max(20, int(round(float(T) * SAMPLES_PER_US)))
    return np.linspace(0.0, float(T), n_samples + 1), n_samples


def delta_gamma_pref(alpha):
    """dΓ_X / d(ε²). Γ_X here is the decay of Re⟨a⟩ = 2 × Dubovitskii per direction."""
    return 4.0 * np.exp(-2.0 * alpha**2) / (C.KAPPA_2 * alpha**2)


def cost_x(edges, values, alpha):
    return float(delta_gamma_pref(alpha) * energy(edges, values))


def peak_mhz(edges, values):
    dt = float(np.median(np.diff(edges)))
    spec = np.abs(np.fft.rfft(np.asarray(values, float)))
    freq = np.fft.rfftfreq(len(values), d=dt)  # cycles/µs == MHz
    if freq.size < 2:
        return float("nan"), spec, freq
    k = int(np.argmax(spec[1:])) + 1
    return float(freq[k]), spec, freq


def clear_name(kmul, kick_t):
    ks = str(int(kmul)) if float(kmul).is_integer() else f"{kmul:g}"
    return f"clear_k{ks}_t{kick_t:.2f}"


def family_of(name):
    if name == "square" or name.startswith("square_"):
        return "square"
    for prefix in ("ramp_cos", "ramp_lin", "clear", "svd", "gen"):
        if name == prefix or name.startswith(prefix):
            return prefix
    return "other"


def evaluate(edges, values, R_b, R_a, t, alpha):
    values = np.asarray(values, float)
    db = R_b @ values
    da = R_a @ values
    peak, _, _ = peak_mhz(edges, values)
    return {
        "snr": snr(t, db, C.KAPPA_B),
        "energy": energy(edges, values),
        "leak": leakage_proxy(t, da),
        "cost": cost_x(edges, values, alpha),
        "peak_amp": float(np.max(np.abs(values))),
        "fft_mhz": peak,
        "db": db,
    }


def matched_gains(ev, ref):
    """SNR after scaling the pulse onto the reference square's cost, over the square SNR."""
    out = {}
    for key, src in (("E", "energy"), ("L", "leak"), ("C", "cost")):
        scale = ref[src] / ev[src]
        snr_m = ev["snr"] * scale  # |Δb|² and every quadratic cost scale the same way
        out[f"snr_{key}"] = float(snr_m)
        out[f"gain_{key}"] = float(snr_m / ref["snr"])
    return out


def build_shapes(T, n_bins, amp, R_b, R_a):
    """Native pulses. SVD and gen are already scaled to the reference square's bin energy."""
    shapes = [("square", *square(T, amp, n_bins))]
    for kind in ("cos", "lin"):
        for tau in RAMP_TAUS:
            shapes.append((f"ramp_{kind}_tau{tau:.1f}", *ramp(T, amp, tau, n_bins, kind=kind)))
    for kmul in CLEAR_KICKS:
        for kick_t in CLEAR_TIMES:
            shapes.append((clear_name(kmul, kick_t), *clear(T, kmul * amp, kick_t, amp, n_bins)))
    disc = n_bins * amp**2  # ||ε||² of the reference square; uniform bins ⇒ same ∫ε² dt
    eps_svd, _ = optimal_pulse(R_b, energy=disc)
    # delta * tr(L) / n = (1e-9 * n) * tr(L) / n = 1e-9 * tr(L), the brief's Tikhonov term
    eps_gen, _ = optimal_pulse(R_b, R_a, energy=disc, delta=1e-9 * n_bins)
    shapes.append(("svd", *from_bins(eps_svd, T)))
    shapes.append(("gen", *from_bins(eps_gen, T)))
    return shapes


def compute_block(alpha, T, amp):
    t, n_samples = sample_grid(T)
    n_bins = n_bins_for(T)
    R_b, R_a = response_matrices(T, n_bins, n_samples, C.G2, C.KAPPA_B, alpha)
    shapes = build_shapes(T, n_bins, amp, R_b, R_a)
    rows = []
    for name, edges, values in shapes:
        ev = evaluate(edges, values, R_b, R_a, t, alpha)
        ev.update(name=name, alpha=float(alpha), T=float(T), edges=edges, values=np.asarray(values, float),
                  linear_ok=bool(ev["peak_amp"] <= C.G2 * (1 + 1e-9)), kind="candidate")
        rows.append(ev)
    ref = next(r for r in rows if r["name"] == "square")
    for ev in rows:
        ev.update(matched_gains(ev, ref))
    for factor in SQUARE_SWEEP:
        edges, values = square(T, factor * C.G2, n_bins)
        ev = evaluate(edges, values, R_b, R_a, t, alpha)
        ev.update(name="square", alpha=float(alpha), T=float(T), edges=edges, values=values,
                  linear_ok=bool(ev["peak_amp"] <= C.G2 * (1 + 1e-9)), kind="sweep",
                  gain_E=1.0, gain_L=1.0, gain_C=1.0, snr_E=ev["snr"], snr_L=ev["snr"], snr_C=ev["snr"])
        rows.append(ev)
    return rows


def choose_finalists(rows):
    """Tokens fixed by the α = 2.1, T = 1 µs linear-response frontier."""
    here = [r for r in rows if r["kind"] == "candidate" and r["alpha"] == 2.1 and r["T"] == 1.0 and r["linear_ok"]]
    def best(prefix):
        cands = [r for r in here if r["name"] == prefix or r["name"].startswith(prefix)]
        return max(cands, key=lambda r: r["gain_E"])["name"]
    names = ["square", best("ramp_cos"), best("ramp_lin"), best("clear"), "svd", "gen"]
    return names


def snr_id(alpha, name, T):
    # Lowercase: record ids reject the brief's capital T (CONTRACT §6.3).
    return f"t2_4c.snr.linresp.two_mode.a{alpha:.2f}.p{name}.t{T:.1f}us"


def cost_id(alpha, name):
    return f"t2_4c.cost.linresp.two_mode.a{alpha:.2f}.p{name}"


def _finite_or_omit(d):
    return {k: float(v) for k, v in d.items() if np.isfinite(v)}


def write_records(rows, finalists, quick):
    wanted = [r for r in rows if r["kind"] == "candidate" and r["name"] in finalists]
    for r in wanted:
        numerics = _finite_or_omit({
            "gain_energy": r["gain_E"],
            "gain_leakage": r["gain_L"],
            "gain_cost": r["gain_C"],
            "fft_peak_MHz": r["fft_mhz"],
            "drive_energy": r["energy"],
            "leakage_proxy": r["leak"],
        })
        # Linear response: SNR and C_X both scale with ε², so snr_E/snr = E_ref/E_native.
        scale = float(np.sqrt(r["snr_E"] / r["snr"]))
        cost_matched = float(r["cost"] * (r["snr_E"] / r["snr"]))
        notes = (
            "linear response, truncation-free. SNR value is at drive energy matched to the "
            f"reference square (amp = {REF_OVER_G2:g} g2). gain_cost uses the analytic proxy; "
            "two-mode cross-check was not run this turn (hard stop). " + COST_NOTE
        )
        record(
            snr_id(r["alpha"], r["name"], r["T"]),
            task="2.4c", quantity="snr", value=r["snr_E"], units="1", method="linresp",
            params=std_params(alpha=r["alpha"], eps_z=r["peak_amp"] * scale, pulse=r["name"], T_us=r["T"]),
            script="tasks/task_2_4c_pulses.py",
            convergence=None, numerics=numerics, cross_check=None,
            artifacts={"figure": "figures/task_2_4c_comparison.png",
                       "arrays": "results/arrays/t2_4c.frontier.npz"},
            notes=notes, quick=quick,
        )
        if r["T"] == 1.0:
            record(
                cost_id(r["alpha"], r["name"]),
                task="2.4c", quantity="cost", value=cost_matched, units="1", method="linresp",
                params=std_params(alpha=r["alpha"], eps_z=r["peak_amp"] * scale, pulse=r["name"], T_us=1.0),
                script="tasks/task_2_4c_pulses.py",
                convergence=None,
                numerics=_finite_or_omit({"gain_cost": r["gain_C"], "gain_energy": r["gain_E"]}),
                notes=COST_NOTE + " Value is C_X of the energy-matched pulse (equal to the reference square).",
                quick=quick,
            )


def save_frontier(rows, finalists, quick):
    def col(key, cast=float):
        return np.array([cast(r[key]) if not isinstance(r[key], str) else r[key] for r in rows])
    save_arrays(
        "t2_4c.frontier", quick=quick,
        name=np.array([r["name"] for r in rows], dtype="U64"),
        kind=np.array([r["kind"] for r in rows], dtype="U16"),
        alpha=col("alpha"), T=col("T"), snr=col("snr"), drive_energy=col("energy"),
        leakage=col("leak"), cost_x=col("cost"),
        gain_energy=col("gain_E"), gain_leakage=col("gain_L"), gain_cost=col("gain_C"),
        snr_matched_energy=col("snr_E"), peak_amp=col("peak_amp"),
        linear_ok=np.array([r["linear_ok"] for r in rows]),
        fft_peak_MHz=col("fft_mhz"),
        finalist=np.array([r["name"] in finalists and r["kind"] == "candidate" for r in rows]),
    )


def save_pulses(rows, finalists, quick):
    """Energy-matched finalist waveforms at α = 2.1, T = 1 µs (the comparison that is shipped)."""
    ref = next(r for r in rows if r["kind"] == "candidate" and r["name"] == "square"
               and r["alpha"] == 2.1 and r["T"] == 1.0)
    payload = {
        "name": np.array(finalists, dtype="U64"),
        "alpha": np.array(2.1), "T": np.array(1.0),
        "amp_ref": np.array(REF_OVER_G2 * C.G2),
    }
    for name in finalists:
        r = next(x for x in rows if x["kind"] == "candidate" and x["name"] == name
                 and x["alpha"] == 2.1 and x["T"] == 1.0)
        scale = np.sqrt(ref["energy"] / r["energy"])
        payload[f"edges__{name}"] = r["edges"]
        payload[f"values__{name}"] = r["values"] * scale
    save_arrays("t2_4c.pulses", quick=quick, **payload)


def plot_pulses(rows, finalists, quick):
    pole = ringing(C.G2, C.KAPPA_B, 2.1)["freq_MHz"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    for name in finalists:
        r = next(x for x in rows if x["kind"] == "candidate" and x["name"] == name
                 and x["alpha"] == 2.1 and x["T"] == 1.0)
        t = r["edges"][:-1]
        ax[0].step(t, r["values"], where="post", lw=1.4, label=name)
        _, spec, freq = peak_mhz(r["edges"], r["values"])
        ax[1].plot(freq, spec / spec.max(), lw=1.4, label=name)
    ax[1].axvline(pole, color="k", ls="--", lw=1.0, label=f"pole {pole:.2f} MHz")
    ax[0].set(xlabel="t (µs)", ylabel="ε_Z (rad/µs)", title="2.4c pulse shapes (native, 0.1 g₂)")
    ax[1].set(xlabel="frequency (MHz)", ylabel="|FFT| / max", xlim=(0, 8),
              title="pulse spectra")
    for a in ax:
        a.grid(alpha=0.3)
        a.legend(fontsize=7)
    save_fig(fig, "task_2_4c_pulses", quick=quick)
    plt.close(fig)


def plot_comparison(rows, finalists, quick):
    here = [r for r in rows if r["alpha"] == 2.1 and r["T"] == 1.0]
    sweep = [r for r in here if r["kind"] == "sweep"]
    sweep = sorted(sweep, key=lambda r: r["energy"])
    cands = [r for r in here if r["kind"] == "candidate"]
    colors = {"square": "C0", "ramp_cos": "C1", "ramp_lin": "C2", "clear": "C3", "svd": "C4", "gen": "C5"}
    fig, ax = plt.subplots(1, 3, figsize=(12, 4.0))
    pairs = (("energy", "drive energy ∫ε² dt"), ("leak", "leakage proxy ∫|δa|² dt"),
             ("cost", "analytic C_X (illustrative)"))
    for a, (key, label) in zip(ax, pairs):
        a.plot([r[key] for r in sweep], [r["snr"] for r in sweep], color="k", lw=1.5, label="square sweep")
        for r in cands:
            fam = family_of(r["name"])
            mark = "*" if r["name"] in ("svd", "gen") else "o"
            a.scatter(r[key], r["snr"], c=colors.get(fam, "gray"), marker=mark, s=40, zorder=3,
                      label=r["name"] if r["name"] in finalists else None)
        a.set(xlabel=label, ylabel="SNR")
        a.grid(alpha=0.3)
    ax[0].legend(fontsize=6)
    fig.suptitle("2.4c linear response at α = 2.1, T = 1 µs (native amplitude, not yet a two-mode claim)")
    save_fig(fig, "task_2_4c_comparison", quick=quick)
    plt.close(fig)


def print_table(rows, finalists):
    print("\nmatched-cost gains at α=2.1, T=1 µs (linear response)")
    print(f"{'name':22} {'SNR':10} {'gain_E':8} {'gain_L':8} {'gain_C':8} {'fft_MHz':8} {'peak':8}")
    for name in finalists:
        r = next(x for x in rows if x["kind"] == "candidate" and x["name"] == name
                 and x["alpha"] == 2.1 and x["T"] == 1.0)
        print(f"{name:22} {r['snr_E']:10.6f} {r['gain_E']:8.4f} {r['gain_L']:8.4f} "
              f"{r['gain_C']:8.4f} {r['fft_mhz']:8.3f} {r['peak_amp']:8.4f}")
    svd = next(x for x in rows if x["name"] == "svd" and x["kind"] == "candidate"
               and x["alpha"] == 2.1 and x["T"] == 1.0)
    sq = next(x for x in rows if x["name"] == "square" and x["kind"] == "candidate"
              and x["alpha"] == 2.1 and x["T"] == 1.0)
    print(f"SVD FFT peak {svd['fft_mhz']:.4f} MHz; plant pole "
          f"{ringing(C.G2, C.KAPPA_B, 2.1)['freq_MHz']:.4f} MHz")
    print(f"SQUARE_SNR {sq['snr_E']:.8f} SVD_SNR {svd['snr_E']:.8f} "
          f"GAIN_E {svd['gain_E']:.6f} GAIN_L {svd['gain_L']:.6f} GAIN_C {svd['gain_C']:.6f}")


def main(quick=False):
    info = git_info()
    if not quick and info["dirty"]:
        raise SystemExit("refusing production run: src/tasks/tools are dirty; commit the code first")
    t0 = time.time()
    alphas = (2.1,) if quick else (2.1, 1.0)
    Ts = (1.0,) if quick else (0.5, 1.0, 2.0)
    amp = REF_OVER_G2 * C.G2
    rows = []
    for alpha in alphas:
        for T in Ts:
            rows.extend(compute_block(alpha, T, amp))
    finalists = choose_finalists(rows)
    print("finalists:", ", ".join(finalists))
    write_records(rows, finalists, quick)
    save_frontier(rows, finalists, quick)
    save_pulses(rows, finalists, quick)
    plot_pulses(rows, finalists, quick)
    plot_comparison(rows, finalists, quick)
    print_table(rows, finalists)
    print(f"wall_s {time.time() - t0:.2f} quick={quick}")
    return finalists


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true")
    main(p.parse_args().quick)
