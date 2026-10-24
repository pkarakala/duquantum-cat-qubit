"""Task 2.3: transmon-free readout of the memory bit through the buffer.

Each well is prepared first (eps_z = 0 from a coherent state), then eps_z (a + a†) is switched on.
<b> settles to -/+ eps/(2 alpha g2) (Réglade S17) after ringing at 3.14 MHz with envelope kappa_b/4,
as the 2x2 model in src/linresp.py predicts. Also measures the readout-induced dephasing
2 eps^2/(kappa_2 alpha^2) (Réglade S18), which validates SNR = kappa_b ∫|Δ<b>|² dt.
Run: python -m tasks.task_2_3 [--quick] [--part linresp|signals|dephasing|figures|all]
"""
import argparse
import json
import time

from src import config as C
import numpy as np
import jax.numpy as jnp
import matplotlib.pyplot as plt
import dynamiqs as dq
from scipy.optimize import curve_fit

from src import linresp
from src import results as R
from src.analysis import settle_time
from src.plotting import save as save_fig

SCRIPT = "tasks/task_2_3.py"
EPS_GRID = (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0)      # eps_z / g2
EPS_NOMINAL = 0.1                                    # "well below g2", as the prompt asks
EPS_DEPH = (0.0, 0.2, 0.5, 1.0)
T_PREP, T_ON, N_T = 3.0, 3.0, 1501                   # 2 ns grid
SS_WINDOW = (2.5, 3.0)                               # residual transient e^{-kappa_b/4 * 2.5} ~ 4e-5
FIT_WINDOW = (0.05, 2.0)
T_DEPH, N_T_DEPH, T0_DEPH = 6.0, 3001, 1.5
NA_SWEEP, NB_SWEEP, NA_SWEEP_DEPH = (20, 24, 28, 32), (6, 8, 10), (24, 28, 32)
REL_TOL = {"b_ss": 1e-3, "ring_freq": 1e-3, "settle": 1e-2, "dephasing": 1e-2}
QUICK = dict(na=16, nb=5, t_prep=1.0, t_on=1.5, eps=(0.1, 1.0), eps_deph=(0.0, 0.5), t_deph=3.0)

ALPHA_TAG = f"a{C.ALPHA:.2f}"
LINRESP_ID = f"t2_3.ring_freq.linresp.two_mode.{ALPHA_TAG}"
RING_ID = f"t2_3.ring_freq.td.two_mode.{ALPHA_TAG}"


def ez_tag(x):
    return f"ez{x:.3g}g2"


def b_ss_id(x, well):
    return f"t2_3.b_ss.td.two_mode.{ALPHA_TAG}.{ez_tag(x)}.well{'p' if well > 0 else 'm'}"


def deph_id(x):
    return f"t2_3.dephasing.td.two_mode.{ALPHA_TAG}.{ez_tag(x)}"


_L0 = None


def _l0():
    """CONTRACT §3/§5/§7 names that arrive with the l0-core merge.

    Imported on first simulation, not at module import, so fit_damped_sine (fast test 5)
    loads on this branch before two_mode grows eps_z, coherent2 and cat2.
    """
    global _L0
    if _L0 is None:
        from src.analysis import code_basis, code_projector, fit_exp_offset, top_projector
        from src.convergence import convergence_block, sweep
        from src.model import cat2, coherent2, two_mode
        _L0 = {
            "two_mode": two_mode, "coherent2": coherent2, "cat2": cat2,
            "code_basis": code_basis, "code_projector": code_projector,
            "top_projector": top_projector, "fit_exp_offset": fit_exp_offset,
            "sweep": sweep, "convergence_block": convergence_block,
        }
    return _L0


def _load_record(rid):
    """Production record, else the quick/ copy (load_record only reads results/records)."""
    try:
        return R.load_record(rid)
    except FileNotFoundError:
        path = R.RES_DIR / "quick" / "records" / f"{rid}.json"
        if path.is_file():
            return json.loads(path.read_text())
        raise


def _artifacts(arrays_id, figure, quick):
    root = "results/quick" if quick else "results"
    fig = f"figures/quick/{figure}.png" if quick else f"figures/{figure}.png"
    return {"arrays": f"{root}/arrays/{arrays_id}.npz", "figure": fig}


# ---------------------------------------------------------------- simulations

def signals(Na, Nb, eps_over_g2, *, t_prep=T_PREP, t_on=T_ON, n_t=N_T, wells=(+1, -1)) -> dict:
    """Prepare each well for t_prep with eps_z = 0 (from coherent2), then switch eps_z on, batched over eps.

    Returns {'t', 'eps_over_g2', well: {'a', 'b', 'adb', 'leak', 'top_a', 'top_b', 'prep_top_a', 'prep_top_b'}}
    with arrays of shape (n_eps, n_t) (complex for a, b, a†b), t measured from the switch-on.
    """
    # One batched argument inside two_mode (eps_z). mesolve then cartesian-batches that H
    # with the well axis on the state, so expects is (n_eps, n_wells, n_ops, n_t).
    L = _l0()
    x = np.atleast_1d(np.asarray(eps_over_g2, dtype=float))
    wells = tuple(wells)
    H0, jumps, (a, b) = L["two_mode"](Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)
    H, _, _ = L["two_mode"](Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=jnp.asarray(x * C.G2))
    top_a = dq.tensor(L["top_projector"](Na, 2), dq.eye(Nb))
    top_b = dq.tensor(dq.eye(Na), L["top_projector"](Nb, 1))
    psi0 = dq.stack([L["coherent2"](Na, Nb, w * C.ALPHA) for w in wells])
    # A handful of prep samples, not just the endpoint: the gate is the MAX top-Fock
    # population during preparation. final_state is still the state at t_prep.
    prep = dq.mesolve(H0, jumps, psi0, jnp.linspace(0.0, t_prep, 31), method=C.METHOD,
                      exp_ops=[top_a, top_b], save_states=False)
    ops = [a, b, a.dag() @ b, dq.tensor(L["code_projector"](Na, C.ALPHA), dq.eye(Nb)), top_a, top_b]
    t = jnp.linspace(0.0, t_on, n_t)
    res = dq.mesolve(H, jumps, prep.final_state, t, method=C.METHOD, exp_ops=ops, save_states=False)
    e = np.asarray(res.expects)
    ep = np.asarray(prep.expects)
    if e.shape != (len(x), len(wells), len(ops), n_t):
        raise RuntimeError(f"readout expects shape {e.shape}, expected "
                           f"{(len(x), len(wells), len(ops), n_t)} (eps, well, op, time)")
    if ep.shape[:2] != (len(wells), 2):
        raise RuntimeError(f"prep expects shape {ep.shape}, expected (n_wells, 2, n_prep)")
    ep = ep.real
    out = {"t": np.asarray(t), "eps_over_g2": x}
    for i, w in enumerate(wells):
        out[w] = {"a": e[:, i, 0], "b": e[:, i, 1], "adb": e[:, i, 2],
                  "leak": 1.0 - e[:, i, 3].real, "top_a": e[:, i, 4].real, "top_b": e[:, i, 5].real,
                  "prep_top_a": float(ep[i, 0].max()), "prep_top_b": float(ep[i, 1].max())}
    return out


def dephasing_traces(Na, Nb, eps_over_g2, *, t_end=T_DEPH, n_t=N_T_DEPH) -> dict:
    """From |C+> with eps_z on at t = 0 (batched): X_L, Y_L in the {C+, C-} basis and memory parity.

    X_L = |C+><C+| - |C-><C-|, Y_L = i(|C-><C+| - |C+><C-|). Returns {'t', 'xl', 'yl', 'parity'}, (n_eps, n_t).
    """
    L = _l0()
    x = np.atleast_1d(np.asarray(eps_over_g2, dtype=float))
    H, jumps, _ = L["two_mode"](Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A,
                                eps_z=jnp.asarray(x * C.G2))
    cp, cm = L["code_basis"](Na, C.ALPHA)
    xl = cp @ cp.dag() - cm @ cm.dag()
    yl = 1j * (cm @ cp.dag() - cp @ cm.dag())
    ops = [dq.tensor(op, dq.eye(Nb)) for op in (xl, yl, dq.parity(Na))]
    t = jnp.linspace(0.0, t_end, n_t)
    res = dq.mesolve(H, jumps, L["cat2"](Na, Nb, C.ALPHA, +1), t, method=C.METHOD,
                     exp_ops=ops, save_states=False)
    e = np.asarray(res.expects)
    if e.shape != (len(x), 3, n_t):
        raise RuntimeError(f"dephasing expects shape {e.shape}, expected {(len(x), 3, n_t)}")
    e = e.real
    return {"t": np.asarray(t), "eps_over_g2": x, "xl": e[:, 0], "yl": e[:, 1], "parity": e[:, 2]}


# ---------------------------------------------------------------- analysis helpers

def steady_value(t, y, window=SS_WINDOW):
    """Mean of y over t in window (last axis); complex in, complex out."""
    t = np.asarray(t)
    m = (t >= window[0]) & (t <= window[1])
    if not m.any():
        raise ValueError(f"no samples in window {window}")
    return np.asarray(y)[..., m].mean(axis=-1)


def _damped(t, A, sigma, omega, phi):
    return A * np.exp(-sigma * t) * np.cos(omega * t + phi)


def _amp_phase(t, y, sigma, omega):
    """Best (A, phi) at fixed (sigma, omega): the model is linear in A cos(phi), A sin(phi)."""
    env = np.exp(-sigma * t)
    B = np.stack([env * np.cos(omega * t), env * np.sin(omega * t)], axis=1)
    (c, s), *_ = np.linalg.lstsq(B, y, rcond=None)
    return float(np.hypot(c, s)), float(np.arctan2(-s, c)), float(np.sum((B @ [c, s] - y) ** 2))


def fit_damped_sine(t, y, p0=None) -> dict:
    """Fit y = A e^{-sigma t} cos(omega t + phi). p0 = (A, sigma, omega, phi) or None.

    Default p0: omega from the zero-crossing spacing, sigma from a 1-D scan with (A, phi) solved
    linearly at each trial sigma. Returns omega, sigma, A (>= 0), phi, their stderrs, rel_rms_residual.
    """
    t, y = np.asarray(t, dtype=float), np.asarray(y, dtype=float)
    scale = float(np.max(np.abs(y)))
    yn = y / scale                                       # curve_fit tolerances are relative to O(1) data
    if p0 is None:
        s = np.signbit(yn)
        i = np.nonzero(s[1:] != s[:-1])[0]
        if len(i) < 2:
            raise ValueError("need at least two zero crossings to guess omega")
        tc = t[i] - yn[i] * (t[i + 1] - t[i]) / (yn[i + 1] - yn[i])
        omega0 = np.pi / np.mean(np.diff(tc))
        sigmas = np.geomspace(1e-3 * omega0, 3 * omega0, 400)
        sigma0 = sigmas[np.argmin([_amp_phase(t, yn, sg, omega0)[2] for sg in sigmas])]
        A0, phi0, _ = _amp_phase(t, yn, sigma0, omega0)
        p = (A0, sigma0, omega0, phi0)
    else:
        A0, sigma0, omega0, phi0 = p0
        p = (A0 / scale, sigma0, omega0, phi0)
    popt, pcov = curve_fit(_damped, t, yn, p0=p, maxfev=20000)
    A, sigma, omega, phi = popt
    if A < 0:
        A, phi = -A, phi + np.pi
    resid = yn - _damped(t, *popt)
    err = np.sqrt(np.abs(np.diag(pcov)))
    return {"omega": float(omega), "sigma": float(sigma), "A": float(A * scale),
            "phi": float((phi + np.pi) % (2 * np.pi) - np.pi),
            "omega_stderr": float(err[2]), "sigma_stderr": float(err[1]),
            "rel_rms_residual": float(np.sqrt(np.mean(resid**2) / np.mean(yn**2)))}


def fit_dephasing(t, xl, yl, t0=T0_DEPH) -> dict:
    """Gamma_Z from |z| = sqrt(X_L^2 + Y_L^2) (insensitive to the eps_z rotation about Z_L) with
    fit_exp_offset on t >= t0, plus the rotation rate from the unwrapped phase (informational)."""
    t, xl, yl = np.asarray(t), np.asarray(xl), np.asarray(yl)
    m = t >= t0
    z = np.hypot(xl, yl)
    f = _l0()["fit_exp_offset"](t[m], z[m])
    # phase is meaningful only while |z| is well above its steady offset
    mp = m & (z > 0.05 * z[m][0])
    phase = np.unwrap(np.arctan2(yl[mp], xl[mp]))
    omega = abs(float(np.polyfit(t[mp], phase, 1)[0])) if mp.sum() > 2 else 0.0
    return {"gamma": float(f["gamma"]), "gamma_stderr": float(f["gamma_stderr"]),
            "rel_rms_residual": float(f["rel_rms_residual"]), "A": float(f["A"]), "C": float(f["C"]),
            "omega": omega, "fit_window_us": [float(t0), float(t[-1])]}


def count_overshoots(t, y, y_ss, rel=0.01):
    """Local extrema of y beyond the target (in the step direction) by more than rel."""
    d = (np.asarray(y) - y_ss) / y_ss
    peaks = np.nonzero((d[1:-1] > d[:-2]) & (d[1:-1] >= d[2:]) & (d[1:-1] > rel))[0] + 1
    return int(len(peaks)), [float(v) for v in d[peaks]]


def linresp_trace(t, eps_over_g2):
    """b of the +alpha well from the 2x2 model for a constant eps switched on at t = 0: (n_eps, n_t), real."""
    return np.array([linresp.response(np.full(len(t), x * C.G2), t, C.G2, C.KAPPA_B, C.ALPHA)[1].real
                     for x in np.atleast_1d(eps_over_g2)])


def gamma_z0_pred():
    return 2 * C.KAPPA_A * C.ALPHA**2 / np.tanh(2 * C.ALPHA**2)


def s18_pred(x):
    """Réglade S18: 2 eps^2/(kappa_2 alpha^2) with eps = x g2."""
    return 2 * (x * C.G2) ** 2 / (C.KAPPA_2 * C.ALPHA**2)


def _xcheck(method, value, ref_value, tol, ref_id=None):
    rel = abs(value / ref_value - 1)
    return {"method": method, "ref_id": ref_id, "value": float(ref_value), "rel_diff": float(rel),
            "tol": tol, "agree": bool(rel <= tol)}


# ---------------------------------------------------------------- metrics (one truncation)

def signal_metrics(s, *, ss_window=SS_WINDOW, fit_window=FIT_WINDOW, eps_nominal=EPS_NOMINAL):
    """Scalar results of one signals() run, from the +alpha well (Δb = 2 Re b+ exactly by symmetry)."""
    t, x = s["t"], s["eps_over_g2"]
    out = {}
    for k, xv in enumerate(x):
        if xv > 0:
            out[f"b_ss_{ez_tag(xv)}"] = float(steady_value(t, s[+1]["b"][k], ss_window).real)
    k = int(np.argmin(np.abs(x - eps_nominal)))
    y = 2 * s[+1]["b"][k].real
    y_ss = float(steady_value(t, y, ss_window))
    r = linresp.ringing(C.G2, C.KAPPA_B, C.ALPHA)
    m = (t >= fit_window[0]) & (t <= fit_window[1])
    fit = fit_damped_sine(t[m], y[m] - y_ss, p0=(-y_ss, r["decay_per_us"], r["omega_d"], 0.0))
    out.update({"ring_freq": fit["omega"] / (2 * np.pi), "sigma": fit["sigma"],
                "settle_5pct": settle_time(t, y, y_ss, 0.05), "settle_1pct": settle_time(t, y, y_ss, 0.01)})
    return out


def deph_metrics(d, t0=T0_DEPH):
    fits = [fit_dephasing(d["t"], d["xl"][k], d["yl"][k], t0) for k in range(len(d["eps_over_g2"]))]
    k0 = int(np.argmin(np.abs(d["eps_over_g2"])))
    g0 = fits[k0]["gamma"]
    return {f"dephasing_{ez_tag(xv)}": fits[k]["gamma"] - g0
            for k, xv in enumerate(d["eps_over_g2"]) if xv > 0}


class _Cache:
    """Run each truncation once: the Na and Nb sweeps share their (28, 8) corner."""

    def __init__(self, fn):
        self.fn, self.rows = fn, {}

    def __call__(self, Na, Nb):
        if (Na, Nb) not in self.rows:
            t0 = time.time()
            self.rows[(Na, Nb)] = {**self.fn(Na, Nb), "wall_s": time.time() - t0}
            print(f"  sweep point {Na}x{Nb}: {self.rows[(Na, Nb)]['wall_s']:.1f} s", flush=True)
        return self.rows[(Na, Nb)]


def _sweeps(cache, na_values, nb_values, na_fixed, nb_fixed):
    sweep = _l0()["sweep"]
    rows_na = sweep(cache, "Na", na_values, {"Nb": nb_fixed})
    rows_nb = sweep(cache, "Nb", nb_values, {"Na": na_fixed})
    return {"Na": ({"Nb": nb_fixed}, rows_na), "Nb": ({"Na": na_fixed}, rows_nb)}


def _block(sw, key, rel_tol, chosen, sign=1.0):
    if sw is None:
        return None
    flipped = {ax: (fixed, [{**r, key: sign * r[key]} for r in rows]) for ax, (fixed, rows) in sw.items()}
    return _l0()["convergence_block"](flipped, key, rel_tol, chosen)


def _sweep_spread(block):
    if block is None:
        return None
    return float(max(abs(v["results"][-1] - v["results"][-2]) for v in block["sweeps"].values()))


# ---------------------------------------------------------------- parts

def part_linresp(quick=False):
    """Analytic 2x2 record; cross-checked against the eigenvalues of M and (if present) the td fit."""
    r = linresp.ringing(C.G2, C.KAPPA_B, C.ALPHA)
    lam = linresp.poles(C.G2, C.KAPPA_B, C.ALPHA)
    M, _ = linresp.system(C.G2, C.KAPPA_B, C.ALPHA)
    f_eig = float(np.max(np.linalg.eigvals(M).imag)) / (2 * np.pi)
    xc = [_xcheck("eigvals_of_M", r["freq_MHz"], f_eig, 1e-9)]
    try:
        td = _load_record(RING_ID)
        xc.append(_xcheck("td_damped_sine_fit", r["freq_MHz"], td["value"], 0.05, RING_ID))
    except FileNotFoundError:
        pass
    numerics = {**r, "poles_re": [float(v) for v in lam.real], "poles_im": [float(v) for v in lam.imag],
                "dc_gain": linresp.dc_gain(C.G2, C.ALPHA)}
    R.record(LINRESP_ID, task="2.3", quantity="ring_freq", value=r["freq_MHz"], units="MHz",
             method="linresp", params=R.std_params(alpha=C.ALPHA), script=SCRIPT, numerics=numerics,
             cross_check=xc, notes="analytic 2x2 linearization, truncation-independent", quick=quick)
    print({k: numerics[k] for k in ("freq_MHz", "decay_per_us", "Q", "t_settle_5pct_us", "t_settle_1pct_us")})
    return numerics


def part_signals(quick=False, na=None, nb=None, conv=True):
    t_start = time.time()
    if quick:
        Na, Nb = na or QUICK["na"], nb or QUICK["nb"]
        grid, t_prep, t_on = QUICK["eps"], QUICK["t_prep"], QUICK["t_on"]
    else:
        Na0, Nb0 = C.trunc_for(C.ALPHA, "steady")
        Na, Nb = na or Na0, nb or Nb0
        grid, t_prep, t_on = EPS_GRID, T_PREP, T_ON
    ss_window = (t_on - 0.5, t_on)
    fit_window = (FIT_WINDOW[0], min(FIT_WINDOW[1], t_on))
    n_t = int(round(t_on / 0.002)) + 1
    kw = dict(t_prep=t_prep, t_on=t_on, n_t=n_t)

    print(f"signals: {Na}x{Nb}, eps/g2 = {(0.0,) + tuple(grid)}", flush=True)
    s = signals(Na, Nb, (0.0,) + tuple(grid), **kw)
    wall_main = time.time() - t_start
    print(f"  production run: {wall_main:.1f} s", flush=True)
    t, x = s["t"], s["eps_over_g2"]
    met = signal_metrics(s, ss_window=ss_window, fit_window=fit_window)

    sw = None
    if conv and not quick:
        cache = _Cache(lambda Na_, Nb_: signal_metrics(signals(Na_, Nb_, grid, wells=(+1,), **kw),
                                                       ss_window=ss_window, fit_window=fit_window))
        cache.rows[(Na, Nb)] = {**met, "wall_s": wall_main}
        sw = _sweeps(cache, NA_SWEEP, NB_SWEEP, 28, 8)
    chosen = {"Na": Na, "Nb": Nb}
    trunc = {"Na": Na, "Nb": Nb}
    conv_note = "" if sw is not None else (" quick" if quick else " no convergence sweep (--no-conv)")

    # ε = 0 baseline: <b>_0 = i kappa_a/(4 g2), purely imaginary by the e^{i pi b†b} K symmetry
    b0 = complex(steady_value(t, s[+1]["b"][0], ss_window))
    sym_b = float(np.max(np.abs(s[-1]["b"] + np.conj(s[+1]["b"]))))
    sym_a = float(np.max(np.abs(s[-1]["a"] + np.conj(s[+1]["a"]))))
    sym = max(sym_b, sym_a)
    max_top2_a = max(max(float(s[w]["top_a"].max()), s[w]["prep_top_a"]) for w in (+1, -1))
    max_top_b = max(max(float(s[w]["top_b"].max()), s[w]["prep_top_b"]) for w in (+1, -1))

    wall = time.time() - t_start
    params_x = lambda xv: R.std_params(alpha=C.ALPHA, eps_z=xv * C.G2)
    summary = {"b_ss": {}}
    for k, xv in enumerate(x):
        if xv == 0:
            continue
        eps = xv * C.G2
        for w in (+1, -1):
            bss = complex(steady_value(t, s[w]["b"][k], ss_window))
            ass = complex(steady_value(t, s[w]["a"][k], ss_window))
            adb = complex(steady_value(t, s[w]["adb"][k], ss_window))
            ehr = abs(adb - (-eps / (2 * C.G2) + 1j * C.KAPPA_A * ass / (4 * C.G2))) / (eps / (2 * C.G2))
            s17 = -w * eps / (2 * C.ALPHA * C.G2)
            xc = [_xcheck("analytic_S17", bss.real, s17, 0.05),
                  # large-signal form b_ss = -eps/(2 g2 <a>*) with the measured (shifted) well
                  _xcheck("S17_measured_well", bss.real, (-eps / (2 * C.G2 * np.conj(ass))).real, 0.05)]
            blk = _block(sw, f"b_ss_{ez_tag(xv)}", REL_TOL["b_ss"], chosen, sign=float(w))
            numerics = {"im_b_minus_baseline": bss.imag - b0.imag, "baseline_im": b0.imag,
                        "re_a_ss": ass.real, "im_a_ss": ass.imag,
                        "pred_im_a": -eps / (2 * C.KAPPA_2 * C.ALPHA**2),
                        "leakage_ss": float(steady_value(t, s[w]["leak"][k], ss_window)),
                        "symmetry_residual": sym, "ehrenfest_residual": float(ehr),
                        "max_top2_a": max_top2_a, "max_top_b": max_top_b,
                        "ss_window_us": list(ss_window), "t_prep_us": t_prep}
            notes = ("Re<b> averaged over the window after switching eps_z on; the -alpha well's "
                     "convergence block is the +alpha sweep with the sign flipped (exact symmetry "
                     f"<b>_- = -<b>_+*, verified at {Na}x{Nb} to {sym:.1e})." + conv_note)
            R.record(b_ss_id(xv, w), task="2.3", quantity="b_ss", value=bss.real, units="dimensionless",
                     method="mesolve_switch_on", params=params_x(xv), script=SCRIPT, truncation=trunc,
                     uncertainty=_sweep_spread(blk), convergence=blk, numerics=numerics, cross_check=xc,
                     artifacts=_artifacts(RING_ID, "task_2_3_linearity", quick),
                     wall_s=wall, notes=notes, quick=quick)
            summary["b_ss"][(xv, w)] = (bss.real, xc[0]["rel_diff"], float(ehr))

    # ringing and settling at the nominal eps, from Δb = <b>+ - <b>- (baseline cancels)
    k = int(np.argmin(np.abs(x - EPS_NOMINAL)))
    y = (s[+1]["b"][k] - s[-1]["b"][k]).real
    y_ss = float(steady_value(t, y, ss_window))
    r = linresp.ringing(C.G2, C.KAPPA_B, C.ALPHA)
    m = (t >= fit_window[0]) & (t <= fit_window[1])
    fit = fit_damped_sine(t[m], y[m] - y_ss, p0=(-y_ss, r["decay_per_us"], r["omega_d"], 0.0))
    f_td = fit["omega"] / (2 * np.pi)
    n_over, overs = count_overshoots(t, y, y_ss)
    y_lin = 2 * linresp_trace(t, x[k])[0]
    y_lin_ss = float(steady_value(t, y_lin, ss_window))
    lin_settle = {p: settle_time(t, y_lin, y_lin_ss, p) for p in (0.05, 0.01)}
    td_settle = {p: settle_time(t, y, y_ss, p) for p in (0.05, 0.01)}
    fits_all = {}
    for kk, xv in enumerate(x):
        if 0 < xv <= 1.0:
            yy = (s[+1]["b"][kk] - s[-1]["b"][kk]).real
            yy_ss = float(steady_value(t, yy, ss_window))
            fits_all[xv] = fit_damped_sine(t[m], yy[m] - yy_ss, p0=(-yy_ss, r["decay_per_us"], r["omega_d"], 0.0))
    ring_num = {"fit_window_us": list(fit_window), "omega_stderr": fit["omega_stderr"],
                "rel_rms_residual": fit["rel_rms_residual"], "sigma_fit": fit["sigma"],
                "sigma_stderr": fit["sigma_stderr"], "sigma_pred": r["decay_per_us"],
                "sigma_rel_diff": abs(fit["sigma"] / r["decay_per_us"] - 1),
                "n_overshoots_1pct": n_over, "overshoots_rel": overs, "delta_b_ss": y_ss,
                "eps_over_g2": float(x[k]),
                "fits_by_eps": {f"{xv:g}": {"freq_MHz": fv["omega"] / (2 * np.pi), "sigma": fv["sigma"]}
                                for xv, fv in fits_all.items()}}
    blk = _block(sw, "ring_freq", REL_TOL["ring_freq"], chosen)
    R.record(RING_ID, task="2.3", quantity="ring_freq", value=f_td, units="MHz", method="damped_sine_fit",
             params=params_x(x[k]), script=SCRIPT, truncation=trunc,
             uncertainty=fit["omega_stderr"] / (2 * np.pi), convergence=blk, numerics=ring_num,
             cross_check=[_xcheck("linresp", f_td, r["freq_MHz"], 0.05, LINRESP_ID)],
             artifacts=_artifacts(RING_ID, "task_2_3_buffer_signals", quick),
             wall_s=wall, notes="fit of Re Δ<b>(t) - Δb_ss to A e^{-σt} cos(ωt + φ)." + conv_note,
             quick=quick)
    dt = float(t[1] - t[0])
    for p, name, env in ((0.05, "settle_5pct", r["t_settle_5pct_us"]), (0.01, "settle_1pct", r["t_settle_1pct_us"])):
        rid = f"t2_3.{name}.td.two_mode.{ALPHA_TAG}"
        R.record(rid, task="2.3", quantity=name, value=td_settle[p], units="us", method="settle_time",
                 params=params_x(x[k]), script=SCRIPT, truncation=trunc, uncertainty=dt,
                 convergence=_block(sw, name, REL_TOL["settle"], chosen),
                 numerics={"rel": p, "grid_dt_us": dt, "delta_b_ss": y_ss,
                           "linresp_same_metric": lin_settle[p], "linresp_envelope": env},
                 cross_check=[_xcheck("linresp_same_metric", td_settle[p], lin_settle[p], 0.15),
                              _xcheck("linresp_envelope", td_settle[p], env, 0.25, LINRESP_ID)],
                 artifacts=_artifacts(RING_ID, "task_2_3_buffer_signals", quick),
                 wall_s=wall, notes="first time after which Re Δ<b> stays within the band of its "
                                    "steady value; uncertainty = grid step." + conv_note, quick=quick)

    xs = x[x > 0]
    R.save_arrays(RING_ID, quick=quick, t_us=t, eps_over_g2=xs,
                  b_plus=s[+1]["b"][x > 0], b_minus=s[-1]["b"][x > 0],
                  a_plus=s[+1]["a"][x > 0], a_minus=s[-1]["a"][x > 0],
                  leak_plus=s[+1]["leak"][x > 0], b_baseline=s[+1]["b"][0], a_baseline=s[+1]["a"][0],
                  b_lin=linresp_trace(t, xs), adb_plus=s[+1]["adb"][x > 0],
                  top_a_plus=s[+1]["top_a"][x > 0], top_b_plus=s[+1]["top_b"][x > 0],
                  t_prep_us=t_prep, ss_window_us=np.array(ss_window), Na=Na, Nb=Nb)
    part_linresp(quick=quick)                          # now with the td cross-check
    plot_signals(quick=quick)
    plot_linearity(quick=quick)
    print({"ring_freq_MHz": f_td, "sigma": fit["sigma"], "settle": td_settle, "linresp_settle": lin_settle,
           "symmetry_residual": sym, "max_top2_a": max_top2_a, "max_top_b": max_top_b,
           "n_overshoots_1pct": n_over, "wall_s": time.time() - t_start})
    return {"metrics": met, "sweeps": sw, "symmetry": sym, "wall_s": time.time() - t_start}


def part_dephasing(quick=False, na=None, nb=None, conv=True):
    t_start = time.time()
    if quick:
        Na, Nb = na or QUICK["na"], nb or QUICK["nb"]
        grid, t_end = QUICK["eps_deph"], QUICK["t_deph"]
    else:
        Na0, Nb0 = C.trunc_for(C.ALPHA, "steady")
        Na, Nb = na or Na0, nb or Nb0
        grid, t_end = EPS_DEPH, T_DEPH
    n_t = int(round(t_end / 0.002)) + 1
    print(f"dephasing: {Na}x{Nb}, eps/g2 = {grid}", flush=True)
    d = dephasing_traces(Na, Nb, grid, t_end=t_end, n_t=n_t)
    wall_main = time.time() - t_start
    print(f"  production run: {wall_main:.1f} s", flush=True)
    t, x = d["t"], d["eps_over_g2"]
    fits = [fit_dephasing(t, d["xl"][k], d["yl"][k]) for k in range(len(x))]
    k0 = int(np.argmin(np.abs(x)))
    g0 = fits[k0]["gamma"]
    par0 = _l0()["fit_exp_offset"](t[t >= T0_DEPH], d["parity"][k0][t >= T0_DEPH])

    sw = None
    if conv and not quick:
        cache = _Cache(lambda Na_, Nb_: deph_metrics(dephasing_traces(Na_, Nb_, grid, t_end=t_end, n_t=n_t)))
        cache.rows[(Na, Nb)] = {**deph_metrics(d), "wall_s": wall_main}
        sw = _sweeps(cache, NA_SWEEP_DEPH, NB_SWEEP, 28, 8)
    chosen = {"Na": Na, "Nb": Nb}
    conv_note = "" if sw is not None else (" quick" if quick else " no convergence sweep (--no-conv)")
    wall = time.time() - t_start
    for k, xv in enumerate(x):
        if xv == 0:
            continue
        dg = fits[k]["gamma"] - g0
        tol = 0.25 if xv < 0.3 else 0.10
        try:
            ref = b_ss_id(xv, +1)
            db = 2 * abs(_load_record(ref)["value"])   # |Δb_ss| = 2 |Re <b>+|; quick/ if that is all we have
        except FileNotFoundError:
            ref, db = None, 2 * abs(xv * C.G2 * linresp.dc_gain(C.G2, C.ALPHA))
        pointer = C.KAPPA_B / 2 * db**2
        numerics = {"gamma_z_eps": fits[k]["gamma"], "gamma_z_0": g0, "gamma_z_0_pred": gamma_z0_pred(),
                    "gamma_z_0_parity_fit": par0["gamma"], "omega_fit": fits[k]["omega"],
                    "omega_pred": 4 * C.ALPHA * xv * C.G2, "fit_window_us": fits[k]["fit_window_us"],
                    "gamma_stderr": float(np.hypot(fits[k]["gamma_stderr"], fits[k0]["gamma_stderr"])),
                    "rel_rms_residual": fits[k]["rel_rms_residual"], "delta_b_ss_used": db}
        R.record(deph_id(xv), task="2.3", quantity="dephasing", value=dg, units="1/us",
                 method="coherence_fit", params=R.std_params(alpha=C.ALPHA, eps_z=xv * C.G2), script=SCRIPT,
                 truncation={"Na": Na, "Nb": Nb}, uncertainty=numerics["gamma_stderr"],
                 convergence=_block(sw, f"dephasing_{ez_tag(xv)}", REL_TOL["dephasing"], chosen),
                 numerics=numerics,
                 cross_check=[_xcheck("analytic_S18", dg, s18_pred(xv), tol),
                              _xcheck("pointer_kappa_b_half_db2", dg, pointer, tol, ref)],
                 artifacts=_artifacts(deph_id(xv), "task_2_3_dephasing", quick),
                 wall_s=wall, notes="Gamma_Z(eps) - Gamma_Z(0), each from fit_exp_offset on "
                                    "|z| = sqrt(<X_L>^2 + <Y_L>^2), t >= 1.5 us, from |C+>." + conv_note,
                 quick=quick)
        z = np.hypot(d["xl"], d["yl"])
        R.save_arrays(deph_id(xv), quick=quick, t_us=t, xl=d["xl"][k], yl=d["yl"][k], parity=d["parity"][k],
                      z_abs=z[k], xl0=d["xl"][k0], yl0=d["yl"][k0], parity0=d["parity"][k0], z_abs0=z[k0],
                      eps_over_g2=xv, Na=Na, Nb=Nb)
    plot_dephasing(quick=quick)
    print({"gamma_z_0": g0, "gamma_z_0_parity": par0["gamma"], "pred": gamma_z0_pred(),
           "delta": {f"{xv:g}": fits[k]["gamma"] - g0 for k, xv in enumerate(x) if xv > 0},
           "s18": {f"{xv:g}": s18_pred(xv) for xv in x if xv > 0}, "wall_s": time.time() - t_start})
    return {"fits": fits, "parity0": par0, "sweeps": sw, "wall_s": time.time() - t_start}


# ---------------------------------------------------------------- figures (from arrays only)

def _arrays(rid, quick):
    base = R.RES_DIR / "quick" / "arrays" if quick else R.RES_DIR / "arrays"
    with np.load(base / f"{rid}.npz") as f:
        return {k: f[k] for k in f.files}


def plot_signals(quick=False):
    A = _arrays(RING_ID, quick)
    t, x = A["t_us"], A["eps_over_g2"]
    ss_window = tuple(A["ss_window_us"])
    show = [k for k, xv in enumerate(x) if np.isclose(xv, [0.1, 0.5, 1.0]).any()] or list(range(len(x)))
    base = A["b_baseline"]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for k in show:
        c = ax[0].plot(t, A["b_plus"][k].real, lw=1.6, label=f"+α, ε={x[k]:g} g₂")[0].get_color()
        ax[0].plot(t, A["b_minus"][k].real, lw=1.6, color=c, alpha=0.5)
        ax[0].plot(t, A["b_lin"][k], "--", color="k", lw=0.8)
        ax[0].plot(t, -A["b_lin"][k], "--", color="k", lw=0.8)
        ax[1].plot(t, A["b_plus"][k].imag - base.imag, color=c, lw=1.4, label=f"+α, ε={x[k]:g} g₂")
        ax[1].plot(t, A["b_minus"][k].imag - base.imag, color=c, lw=1.4, ls=":")
    ax[0].set(xlabel="t after switch-on (µs)", ylabel="Re⟨b⟩", title="buffer signal (faded: −α; dashed: 2×2 linresp)")
    ax[1].set(xlabel="t after switch-on (µs)", ylabel="Im⟨b⟩ − Im⟨b⟩₀",
              title=f"imaginary part minus baseline {base[-1].imag:.4f}i")
    k = int(np.argmin(np.abs(x - EPS_NOMINAL)))
    y = (A["b_plus"][k] - A["b_minus"][k]).real
    y_ss = float(steady_value(t, y, ss_window))
    y_lin = 2 * A["b_lin"][k]
    ax[2].plot(t, y / y_ss, lw=1.8, label=f"two-mode, ε={x[k]:g} g₂")
    ax[2].plot(t, y_lin / float(steady_value(t, y_lin, ss_window)), "--", color="k", lw=1, label="2×2 linresp")
    for p, ls in ((0.05, "-"), (0.01, ":")):
        ax[2].axhspan(1 - p, 1 + p, color="gray", alpha=0.15 if p == 0.05 else 0.3)
        ts = settle_time(t, y, y_ss, p)
        ax[2].axvline(ts, color="C3", ls=ls, lw=1, label=f"{int(p * 100)}% settle {ts:.3f} µs")
    ax[2].set(xlabel="t after switch-on (µs)", ylabel="Δ⟨b⟩ / Δ⟨b⟩_ss", ylim=(-0.1, 1.7),
              title="readout contrast Δ⟨b⟩ = ⟨b⟩₊ − ⟨b⟩₋")
    for a_ in ax:
        a_.grid(alpha=0.3)
        a_.legend(fontsize=7)
    save_fig(fig, "task_2_3_buffer_signals", quick=quick)
    plt.close(fig)


def plot_linearity(quick=False):
    A = _arrays(RING_ID, quick)
    t, x = A["t_us"], A["eps_over_g2"]
    w = tuple(A["ss_window_us"])
    bp, bm = steady_value(t, A["b_plus"], w).real, steady_value(t, A["b_minus"], w).real
    ap = steady_value(t, A["a_plus"], w)
    leak = steady_value(t, A["leak_plus"], w).real
    s17 = x * C.G2 / (2 * C.ALPHA * C.G2)
    xx = np.geomspace(x.min() / 1.5, x.max() * 1.5, 100)
    fig, ax = plt.subplots(1, 4, figsize=(18, 3.8))
    ax[0].loglog(x, -bp, "o", label="−Re⟨b⟩₊")
    ax[0].loglog(x, bm, "x", ms=8, label="Re⟨b⟩₋")
    ax[0].loglog(xx, xx / (2 * C.ALPHA), "k--", lw=1, label="S17: ε/(2αg₂)")
    ax[0].set(xlabel="ε_Z / g₂", ylabel="|Re⟨b⟩_ss|", title="readout contrast vs drive")
    ax[1].semilogx(x, -bp / s17 - 1, "o-", label="+α")
    ax[1].semilogx(x, bm / s17 - 1, "x--", label="−α")
    ax[1].axhspan(-0.05, 0.05, color="gray", alpha=0.15, label="±5% gate (ε ≤ g₂)")
    ax[1].set(xlabel="ε_Z / g₂", ylabel="Re⟨b⟩_ss / S17 − 1", title="deviation from linear response")
    ax[2].loglog(x, -ap.imag, "o", label="−Im⟨a⟩_ss (+α)")
    ax[2].loglog(xx, xx * C.G2 / (2 * C.KAPPA_2 * C.ALPHA**2), "k--", lw=1, label="ε/(2κ₂α²)")
    ax[2].set(xlabel="ε_Z / g₂", ylabel="−Im⟨a⟩_ss", title="both wells shift along −Im")
    ax[3].loglog(x, np.maximum(leak, 1e-16), "o-")
    ax[3].set(xlabel="ε_Z / g₂", ylabel="1 − ⟨Π_code⟩", title="leakage out of the code space (+α)")
    for a_ in ax:
        a_.grid(alpha=0.3, which="both")
        if a_.get_legend_handles_labels()[0]:
            a_.legend(fontsize=7)
    save_fig(fig, "task_2_3_linearity", quick=quick)
    plt.close(fig)


def plot_dephasing(quick=False):
    grid = QUICK["eps_deph"] if quick else EPS_DEPH
    xs = [xv for xv in grid if xv > 0]
    arrs = {xv: _arrays(deph_id(xv), quick) for xv in xs}
    t = arrs[xs[0]]["t_us"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    z0 = arrs[xs[0]]["z_abs0"]
    f0 = fit_dephasing(t, arrs[xs[0]]["xl0"], arrs[xs[0]]["yl0"])
    ax[0].semilogy(t, z0, lw=1.6, label=f"ε=0: Γ_Z={f0['gamma']:.4f}/µs")
    dg, s18, ptr = [], [], []
    for xv in xs:
        f = fit_dephasing(t, arrs[xv]["xl"], arrs[xv]["yl"])
        ax[0].semilogy(t, arrs[xv]["z_abs"], lw=1.6, label=f"ε={xv:g} g₂: Γ_Z={f['gamma']:.4f}/µs")
        dg.append(f["gamma"] - f0["gamma"])
    ax[0].axvline(T0_DEPH, color="gray", ls=":", lw=1)
    ax[0].set(xlabel="t (µs)", ylabel="|z| = √(⟨X_L⟩² + ⟨Y_L⟩²)", title="coherence of |C₊⟩ under readout drive")
    xx = np.linspace(0, max(xs) * 1.1, 100)
    ax[1].plot(xx, s18_pred(xx), "k--", lw=1, label="S18: 2ε²/(κ₂α²)")
    ax[1].plot(xs, dg, "o", ms=8, label="two-mode fit ΔΓ_Z")
    try:
        db = [2 * abs(_load_record(b_ss_id(xv, +1))["value"]) for xv in xs]
    except FileNotFoundError:
        db = None
    if db is not None:
        ax[1].plot(xs, [C.KAPPA_B / 2 * v**2 for v in db], "s", mfc="none", ms=10,
                   label="pointer (κ_b/2)|Δb_ss|²")
    ax[1].set(xlabel="ε_Z / g₂", ylabel="Γ_Z(ε) − Γ_Z(0) (1/µs)", title="measurement-induced dephasing")
    for a_ in ax:
        a_.grid(alpha=0.3)
        a_.legend(fontsize=7)
    save_fig(fig, "task_2_3_dephasing", quick=quick)
    plt.close(fig)


def main(part="all", quick=False, na=None, nb=None, conv=True):
    out = {}
    if part in ("linresp", "all"):
        out["linresp"] = part_linresp(quick=quick)
    if part in ("signals", "all"):
        out["signals"] = part_signals(quick=quick, na=na, nb=nb, conv=conv)
    if part in ("dephasing", "all"):
        out["dephasing"] = part_dephasing(quick=quick, na=na, nb=nb, conv=conv)
    if part == "figures":
        plot_signals(quick=quick)
        plot_linearity(quick=quick)
        plot_dephasing(quick=quick)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quick", action="store_true", help="16x5 smoke run, outputs to results/quick")
    p.add_argument("--part", default="all", choices=["linresp", "signals", "dephasing", "figures", "all"])
    p.add_argument("--na", type=int, default=None)
    p.add_argument("--nb", type=int, default=None)
    p.add_argument("--no-conv", action="store_true", help="skip the Na / Nb convergence sweeps")
    a = p.parse_args()
    main(part=a.part, quick=a.quick, na=a.na, nb=a.nb, conv=not a.no_conv)
