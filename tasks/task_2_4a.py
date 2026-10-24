"""Task 2.4a: which ATS terms survive, and the shifts the pump leaves behind.

The symbolic half (normal ordering, displaced-frame Stark/Kerr, tone ratios) is closed
form. The time-dependent half integrates the bare rotating-frame circuit Hamiltonian
and compares it with two_mode(..., extra_H=). Records need the merged l0-core API.
"""
import argparse
import math
import time

from src import config as C

import numpy as np
import jax.numpy as jnp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import dynamiqs as dq
from scipy.optimize import curve_fit
from scipy.special import j1

from src.circuit import (
    circuit_rotating_H, eps_p_for_g2, extra_H, g2_from_circuit, resonant_terms,
    sin_phi_terms, static_coef, static_terms,
)
from src.model import two_mode, vacuum2

PHI_A, PHI_B = 0.06, 0.3
DAMP = math.exp(-(PHI_A ** 2 + PHI_B ** 2) / 2.0)
W0 = C.TWO_PI * 800.0                 # 0.8 GHz
W_A, W_B, W_P = 5.0 * W0, 6.0 * W0, 4.0 * W0
EJ = C.TWO_PI * 4.0e4                 # 40 GHz
N_ALPHA2 = 4.41                       # nominal |alpha|^2, for the dressed-g2 note


def _mhz(z):
    return float(np.real(z) / C.TWO_PI)


def _cross(method, reference, actual, tol, ref_id=None):
    reference, actual = float(reference), float(actual)
    rel = 0.0 if reference == 0.0 and actual == 0.0 else abs(actual - reference) / abs(reference)
    return {
        "method": method, "ref_id": ref_id, "value": reference,
        "rel_diff": float(rel), "tol": float(tol), "agree": bool(rel <= tol),
    }


def _integer_resonant_count(max_order=7):
    """How many odd monomials satisfy 5(p-q)+6(r-s) = ±4. Independent of the float scan."""
    n_hit = 0
    for p, q, r, s, _n in _odd_upto(max_order):
        beat = 5 * (p - q) + 6 * (r - s)
        if beat in (4, -4):
            n_hit += 1
    return n_hit


def _odd_upto(max_order):
    for p in range(max_order + 1):
        for q in range(max_order + 1 - p):
            for r in range(max_order + 1 - p - q):
                for s in range(max_order + 1 - p - q - r):
                    n = p + q + r + s
                    if n and n <= max_order and n % 2:
                        yield p, q, r, s, n


def _pack_terms(terms, resonant_keys):
    rows = []
    for t in terms:
        key = (t["p"], t["q"], t["r"], t["s"])
        da, db = t["p"] - t["q"], t["r"] - t["s"]
        rows.append({
            "p": t["p"], "q": t["q"], "r": t["r"], "s": t["s"], "order": t["order"],
            "freq_over_w0": 5 * da + 6 * db,
            "coef_MHz": _mhz(t["coef"]),
            "resonant": key in resonant_keys,
        })
    return rows


def collect_sym(n_t=512, max_order=7):
    """Every symbolic number the records and the derivation quote. Rates stay in rad/µs until _mhz."""
    g2_035 = g2_from_circuit(EJ, 0.035, PHI_A, PHI_B)
    eps_star = eps_p_for_g2(C.G2, EJ, PHI_A, PHI_B, W_A, W_B, W_P, W0)
    st = static_terms(EJ, eps_star, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                      max_order=max_order, displaced=True, n_t=n_t)
    st35 = static_terms(EJ, 0.035, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                        max_order=4, displaced=True, n_t=n_t)
    und = static_terms(EJ, 0.035, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                       max_order=max_order, displaced=False, n_t=n_t)

    def coef(terms, *k):
        return static_coef(terms, *k)

    sa, sb = coef(st, 1, 1, 0, 0).real, coef(st, 0, 0, 1, 1).real
    ka, kb = coef(st, 2, 2, 0, 0).real, coef(st, 0, 0, 2, 2).real
    chi = coef(st, 1, 1, 1, 1).real
    g2_disp = coef(st, 0, 2, 1, 0).real
    # |n,0> -> |n-2,1>: a†a³b† contributes (n-2), a†²a⁴b† contributes (n-2)(n-3).
    n_cat = N_ALPHA2
    g_eff = (coef(st, 0, 2, 1, 0)
             + (n_cat - 2) * coef(st, 1, 3, 1, 0)
             + (n_cat - 2) * (n_cat - 3) * coef(st, 2, 4, 1, 0))

    c2_analytic = -2.0 * (EJ * eps_star) ** 2 * DAMP * sum(
        2.0 * ph ** 2 * w / (w ** 2 - W_P ** 2) for ph, w in ((PHI_A, W_A), (PHI_B, W_B)))
    stark_b_analytic = -c2_analytic * DAMP * PHI_B ** 2

    tone_a = (C.G2 / (EJ * PHI_A * DAMP), W_A, 0.0)   # undisplaced linear piece = g2
    tone_b = (C.G2 / (EJ * PHI_B * DAMP), W_B, 0.0)
    ta = static_terms(EJ, eps_star, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                      max_order=3, displaced=True, tone=tone_a, n_t=n_t)
    tb = static_terms(EJ, eps_star, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                      max_order=3, displaced=True, tone=tone_b, n_t=n_t)
    lin_a = coef(ta, 0, 1, 0, 0)
    lin_b = coef(tb, 0, 0, 0, 1)

    nt_rows = []
    for nt in (256, 512, 1024):
        s = static_terms(EJ, eps_star, PHI_A, PHI_B, W_A, W_B, W_P, W0,
                         max_order=4, displaced=True, n_t=nt)
        nt_rows.append({
            "n_t": nt,
            "stark_a": _mhz(coef(s, 1, 1, 0, 0)),
            "stark_b": _mhz(coef(s, 0, 0, 1, 1)),
            "kerr_a": _mhz(coef(s, 2, 2, 0, 0)),
            "kerr_b": _mhz(coef(s, 0, 0, 2, 2)),
            "chi_ab": _mhz(coef(s, 1, 1, 1, 1)),
        })

    res = resonant_terms(sin_phi_terms(PHI_A, PHI_B, max_order), W_A, W_B, W_P, tol=1e-6 * W0)
    res_keys = {(t["p"], t["q"], t["r"], t["s"]) for t in res}
    table = _pack_terms(st, res_keys)

    delta = 2.0 * sa - sb + 2.0 * ka          # rad/µs, added to the bare pump
    return {
        "eps_p_star": float(eps_star),
        "eps_undisplaced": float(0.035 * 0.763 / abs(g2_035 / C.TWO_PI)),
        "g2_sym_MHz": _mhz(g2_035),
        "g2_disp_MHz": _mhz(g2_disp),
        "g2_disp_0035_MHz": _mhz(coef(st35, 0, 2, 1, 0)),
        "g2_undisp_static_MHz": _mhz(coef(und, 0, 2, 1, 0)),
        "stark_a_MHz": _mhz(sa), "stark_b_MHz": _mhz(sb),
        "kerr_a_MHz": _mhz(ka), "kerr_b_MHz": _mhz(kb), "chi_ab_MHz": _mhz(chi),
        "kerr_b_K_MHz": _mhz(-2.0 * kb),
        "sa": float(sa), "sb": float(sb), "ka": float(ka), "kb": float(kb), "chi": float(chi),
        "g2_disp": float(g2_disp),
        "delta_retune": float(delta),
        "wp_prime_GHz": float((W_P + delta) / C.TWO_PI / 1e3),
        "wb_drive_GHz": float((W_B + sb) / C.TWO_PI / 1e3),
        "g_eff_over_g2": float(np.real(g_eff / g2_disp)),
        "g_bs_over_ez": float(np.real(coef(ta, 0, 1, 1, 0) / lin_a)),
        "g_sp_over_ed": float(np.real(coef(tb, 0, 0, 1, 2) / lin_b)),
        "a2_over_ed": float(np.real(coef(tb, 0, 2, 0, 0) / lin_b)),
        "stark_b_analytic_MHz": _mhz(stark_b_analytic),
        "g2_tutorial_MHz": _mhz(-EJ * eps_star * PHI_A ** 2 * PHI_B),
        "resonant_keys": sorted(res_keys),
        "resonant_count": len(res_keys),
        "integer_count": _integer_resonant_count(max_order),
        "table": table,
        "nt_rows": nt_rows,
        "max_order": max_order,
        "n_t": n_t,
        "loss_3g2_per_us": None,  # filled below once g_bs is known
    }


def _loss_at_3g2(g_bs_over_ez):
    """Extra memory loss 4 g_bs²/κ_b when a flux tone supplies ε_Z = 3 g₂."""
    g_bs = g_bs_over_ez * 3.0 * C.G2
    return float(4.0 * g_bs ** 2 / C.KAPPA_B)


def _writers():
    try:
        from src.results import record, save_arrays, std_params
        from src.convergence import convergence_block
        from src.plotting import save as save_fig
    except ImportError as exc:
        raise SystemExit(
            "PAUSED_FOR_L0_CORE: record(), convergence_block or plotting.save(quick=) "
            f"is not on this branch yet ({exc})."
        )
    return record, save_arrays, std_params, convergence_block, save_fig


def _params(eps_p, max_order):
    _record, _arrays, std_params, _block, _fig = _writers()
    return std_params(EJ_GHz=40, phi_a=PHI_A, phi_b=PHI_B, wa_GHz=4.0, wb_GHz=4.8,
                      wp_GHz=3.2, eps_p=eps_p, max_order=max_order)


def _brute_g2():
    """⟨0,1|sin φ̂|2,0⟩/√2 is c(0,2,1,0); same 2 E_J ε_p × ½ combination as g2_from_circuit."""
    n = 30
    x = np.diag(np.sqrt(np.arange(1, n)), 1)
    x = x + x.T
    eye = np.eye(n)
    lam, v = np.linalg.eigh(PHI_A * np.kron(x, eye) + PHI_B * np.kron(eye, x))
    s = (v * np.sin(lam)) @ v.T
    c = s[1, 2 * n] / math.sqrt(2.0)
    return float(2.0 * EJ * 0.035 * 0.5 * c)


def write_sym(bundle, quick, tdsim_g2_mhz=None):
    record, save_arrays, _std, convergence_block, save_fig = _writers()
    params_035 = _params(0.035, bundle["max_order"])
    params_star = _params(bundle["eps_p_star"], bundle["max_order"])
    script = "tasks/task_2_4a.py"
    t0 = time.perf_counter()

    checks_g2 = [_cross("brute_force_matrix_element", _mhz(_brute_g2()), bundle["g2_sym_MHz"], 1e-6)]
    if tdsim_g2_mhz is not None:
        rescaled = abs(tdsim_g2_mhz) * 0.035 / bundle["eps_p_star"]
        checks_g2.append(_cross(
            "tdsim_rescaled_to_0.035", rescaled, abs(bundle["g2_sym_MHz"]), 0.03,
            ref_id="t2_4a.g2.tdsim.circuit"))
    notes_sym = (
        f"eps_p for |g2|/2pi=0.763 without displacement = {bundle['eps_undisplaced']:.5f}; "
        f"eps_p* (displaced) = {bundle['eps_p_star']:.5f}. "
        f"Sign: g2<0 puts alpha^2=eps_d/g2<0 (cat on the imaginary axis). "
        f"A pump phase of pi flips g2 and leaves the Stark shift alone: a gauge. "
        f"iQuHACK g2/2pi (no 1/2, no e^-Phi/2) at eps_p* = {bundle['g2_tutorial_MHz']:.4f} MHz "
        f"({abs(bundle['g2_tutorial_MHz'] / bundle['g2_disp_MHz']):.3f} times |g2_disp|). "
        f"g2_disp/2pi at eps_p* = {bundle['g2_disp_MHz']:.4f} MHz; "
        f"at eps_p=0.035, g2_disp/2pi = {bundle['g2_disp_0035_MHz']:.4f} MHz. "
        f"Dressed g2(n_a=4.41)/g2 = {bundle['g_eff_over_g2']:.4f}. "
        "Undisplaced static a^2 b† uses the full sin(eps cos) = 2 J1 cos + ..., "
        "so it differs from the eps/2 formula by eps^2/8 ~ 1.5e-4."
    )
    record(
        "t2_4a.g2.sym.circuit", task="2.4a", quantity="g2", value=bundle["g2_sym_MHz"],
        units="MHz", method="normal_ordered_bch_rwa1", params=params_035, script=script,
        convergence=None, cross_check=checks_g2, quick=quick,
        wall_s=time.perf_counter() - t0, notes=notes_sym,
        artifacts={"arrays": "results/arrays/t2_4a.resonant_terms.sym.circuit.npz"},
    )

    def nt_block(key):
        rows = [{"n_t": r["n_t"], key: r[key]} for r in bundle["nt_rows"]]
        fixed = {"eps_p": bundle["eps_p_star"], "max_order": 4}
        return convergence_block({"n_t": (fixed, rows)}, key=key, rel_tol=1e-8, chosen={"n_t": 512})

    analytic = {
        "stark_a": bundle["stark_b_analytic_MHz"] * (PHI_A / PHI_B) ** 2,
        "stark_b": bundle["stark_b_analytic_MHz"],
        "kerr_a": bundle["stark_b_analytic_MHz"] * (-(PHI_A ** 2) / 4.0) * (PHI_A / PHI_B) ** 2,
        "kerr_b": bundle["stark_b_analytic_MHz"] * (-(PHI_B ** 2) / 4.0),
        "chi_ab": bundle["stark_b_analytic_MHz"] * (-(PHI_A ** 2)),
    }
    # kerr_a / stark_a = -phi_a^2/4 and stark_a/stark_b = phi_a^2/phi_b^2, so
    # kerr_a = stark_b_analytic * (phi_a/phi_b)^2 * (-phi_a^2/4). chi/stark_b = -phi_a^2.
    values = {
        "stark_a": bundle["stark_a_MHz"], "stark_b": bundle["stark_b_MHz"],
        "kerr_a": bundle["kerr_a_MHz"], "kerr_b": bundle["kerr_b_MHz"],
        "chi_ab": bundle["chi_ab_MHz"],
    }
    shift_notes = (
        f"eps_p*={bundle['eps_p_star']:.5f}. "
        f"omega_p'/2pi={bundle['wp_prime_GHz']:.6f} GHz "
        f"(bare 3.2 GHz plus {bundle['delta_retune'] / C.TWO_PI:.3f} MHz). "
        f"Buffer drive at omega_b+stark_b: {bundle['wb_drive_GHz']:.6f} GHz. "
        f"K_b/2pi=-2*kerr_b={bundle['kerr_b_K_MHz']:.4f} MHz (Ferrari's realistic value is 1 MHz); "
        f"chi/2pi={bundle['chi_ab_MHz']:.4f} MHz (Ferrari 0.5 MHz). "
        f"g_bs/eps_Z={bundle['g_bs_over_ez']:.5f} (flux tone at omega_a, displaced). "
        f"g_sp/eps_d={bundle['g_sp_over_ed']:.5f}; memory two-photon / eps_d={bundle['a2_over_ed']:.3e}. "
        f"At eps_Z=3 g2, 4 g_bs^2/kappa_b={_loss_at_3g2(bundle['g_bs_over_ez']):.4f}/us "
        f"(kappa_a={C.KAPPA_A:.4f}/us). kappa neglected in xi (kappa_b/2 Delta ~ 1e-3). "
        "n_t sweep is the convergence axis (closed form in Fock space; no Na, Nb)."
    )
    for quantity in ("stark_a", "stark_b", "kerr_a", "kerr_b", "chi_ab"):
        checks = [_cross("analytic_C2", analytic[quantity], values[quantity], 0.05)]
        record(
            f"t2_4a.{quantity}.sym.circuit", task="2.4a", quantity=quantity,
            value=values[quantity], units="MHz", method="displaced_frame_rwa1",
            params=params_star, script=script, convergence=nt_block(quantity),
            cross_check=checks, quick=quick, notes=shift_notes,
            wall_s=time.perf_counter() - t0,
        )

    table = bundle["table"]
    save_arrays(
        "t2_4a.resonant_terms.sym.circuit", quick=quick,
        p=np.array([r["p"] for r in table]),
        q=np.array([r["q"] for r in table]),
        r=np.array([r["r"] for r in table]),
        s=np.array([r["s"] for r in table]),
        order=np.array([r["order"] for r in table]),
        freq_over_w0=np.array([r["freq_over_w0"] for r in table], dtype=float),
        coef_MHz=np.array([r["coef_MHz"] for r in table]),
        resonant=np.array([r["resonant"] for r in table]),
    )
    fam = ", ".join(str(k) for k in bundle["resonant_keys"])
    record(
        "t2_4a.resonant_terms.sym.circuit", task="2.4a", quantity="resonant_terms",
        value=bundle["resonant_count"], units="count", method="rwa_frequency_scan",
        params=params_035, script=script, convergence=None, quick=quick,
        cross_check=[_cross("integer_diophantine", bundle["integer_count"],
                            bundle["resonant_count"], 0.0)],
        notes=(
            f"max_order={bundle['max_order']}. The 12 monomials (p,q,r,s) are: {fam}. "
            "Each has (p-q, r-s) in {(-2, +1), (+2, -1)}, i.e. the a^2 b† family plus h.c. "
            "Nearest miss is one unit of 0.8 GHz. "
            "Formal higher-harmonic resonances (displaced frame, eps_p*) are negligible next to g2: "
            "a†^4 b^2 (order 6, at 2 omega_p) is about 4e-6 MHz; "
            "a^2 b^3 (7 omega_p) and a^2 b†^5 (5 omega_p) are below 1e-9 MHz."
        ),
        artifacts={"arrays": "results/arrays/t2_4a.resonant_terms.sym.circuit.npz",
                   "figure": "figures/task_2_4a_terms.png"},
        wall_s=time.perf_counter() - t0,
    )
    _plot_terms(bundle, save_fig, quick)
    print(f"sym: g2/2pi={bundle['g2_sym_MHz']:.4f} MHz, eps_p*={bundle['eps_p_star']:.5f}, "
          f"stark_b={bundle['stark_b_MHz']:.3f} MHz, resonant={bundle['resonant_count']}")


def _plot_terms(bundle, save_fig, quick):
    rows = [r for r in bundle["table"] if r["order"] <= 7 and abs(r["coef_MHz"]) > 0]
    mag = np.array([abs(r["coef_MHz"]) for r in rows])
    res = np.array([r["resonant"] for r in rows])
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.scatter(np.flatnonzero(~res), mag[~res], s=18, c="0.55", label="off resonant")
    ax.scatter(np.flatnonzero(res), mag[res], s=28, c="C3", label="a²b† family")
    ax.set_yscale("log")
    ax.set(xlabel="monomial index (order ≤ 7)", ylabel="|static coefficient| (MHz)",
           title=f"Displaced-frame static terms at ε_p* = {bundle['eps_p_star']:.4f}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    save_fig(fig, "task_2_4a_terms", quick=quick)
    plt.close(fig)


def _method(rtol=1e-8, atol=1e-10):
    # GHz terms need ~10 ps steps; the default 1e5-step cap stops a 0.3 µs trace early.
    return dq.method.Tsit5(rtol=rtol, atol=atol, max_steps=10_000_000)


def _cosine_force(eps, phi):
    """Amplitude of F(t) = F0 cos(ω_p t) in i ξ̇ = ω ξ + F, fundamental of sin(ε_p cos)."""
    return 4.0 * EJ * DAMP * phi * float(j1(eps))


def _xi_lab(t, omega, w_pump, f0):
    a = -(f0 / 2.0) / (omega - w_pump)
    b = -(f0 / 2.0) / (omega + w_pump)
    return a * np.exp(-1j * w_pump * t) + b * np.exp(1j * w_pump * t)


def _rabi(t, g, delta):
    w = np.sqrt(4.0 * g * g + delta * delta)
    return (4.0 * g * g) / (w * w) * np.sin(0.5 * w * t) ** 2


def _tls(t, omega, delta):
    """(c_e, c_g) for H = [[0, Ω], [Ω, δ]], c_e(0) = 1. δ = E_01 − E_20."""
    w = np.sqrt(delta ** 2 + 4.0 * omega * omega)
    phase = np.exp(-1j * delta * t / 2.0)
    cg = -2j * omega / w * phase * np.sin(w * t / 2.0)
    ce = phase * (np.cos(w * t / 2.0) + 1j * delta / w * np.sin(w * t / 2.0))
    return ce, cg


def _fit_exchange(t, p01, ce, cg, g_guess):
    g_hat, delta_free = curve_fit(
        _rabi, t, p01, p0=[abs(g_guess), 0.0],
        bounds=([0.0, -np.inf], [np.inf, np.inf]), maxfev=20000,
    )[0]
    # Population fixes |δ|. The relative phase of c_g and c_e fixes the sign
    # (a global phase from D(ξ) is removed before comparing).
    omega = -abs(g_hat)   # g2 < 0, matrix element of a²b† is √2 g2

    def cost(delta):
        ce_m, cg_m = _tls(t, omega, delta)
        pred = np.angle(cg_m * np.conj(ce_m))
        got = np.angle(cg * np.conj(ce))
        weight = np.abs(cg)
        dphi = np.angle(np.exp(1j * (got - pred)))
        mean = np.angle(np.sum(weight * np.exp(1j * dphi))) if np.sum(weight) else 0.0
        dphi = np.angle(np.exp(1j * (dphi - mean)))
        return float(np.sum(weight * dphi ** 2))

    delta_abs = abs(float(delta_free))
    delta = delta_abs if cost(delta_abs) <= cost(-delta_abs) else -delta_abs
    pred = _rabi(t, g_hat, delta)
    rms = float(np.sqrt(np.mean((p01 - pred) ** 2)))
    return {
        "G": float(g_hat), "delta": float(delta), "g2_MHz": float(g_hat / math.sqrt(2.0) / C.TWO_PI),
        "rel_rms": rms / max(float(np.max(p01)), 1e-12), "pmax": float(np.max(p01)),
    }


def _exchange(w_pump, t_end, na, nb, n_save, eps, method):
    """|2,0> → |0,1> in the displaced frame. H is NOT pre-displaced: ξ(t) is divided out afterwards."""
    h = circuit_rotating_H(na, nb, EJ, eps, PHI_A, PHI_B, W_A, W_B, w_pump, max_order=5)
    f0_a, f0_b = _cosine_force(eps, PHI_A), _cosine_force(eps, PHI_B)
    # t = 0 amplitudes. Linear response, same pump frequency as H.
    xi_a0 = _xi_lab(np.array([0.0]), W_A, w_pump, f0_a)[0]
    xi_b0 = _xi_lab(np.array([0.0]), W_B, w_pump, f0_b)[0]
    psi0 = dq.tensor(
        dq.displace(na, complex(xi_a0)) @ dq.fock(na, 2),
        dq.displace(nb, complex(xi_b0)) @ dq.fock(nb, 0),
    )
    t = np.linspace(0.0, t_end, n_save)
    res = dq.sesolve(h, psi0, jnp.asarray(t), method=method, save_states=True)
    states = np.asarray(res.states.to_jax()).reshape(n_save, na * nb)
    xi_a = _xi_lab(t, W_A, w_pump, f0_a) * np.exp(1j * W_A * t)
    xi_b = _xi_lab(t, W_B, w_pump, f0_b) * np.exp(1j * W_B * t)
    p01 = np.empty(n_save)
    ce = np.empty(n_save, dtype=complex)
    cg = np.empty(n_save, dtype=complex)
    for i in range(n_save):
        da = np.asarray(dq.displace(na, -complex(xi_a[i])).to_jax())
        db = np.asarray(dq.displace(nb, -complex(xi_b[i])).to_jax())
        flipped = np.kron(da, db) @ states[i]
        ce[i] = flipped[2 * nb + 0]
        cg[i] = flipped[0 * nb + 1]
        p01[i] = abs(cg[i]) ** 2
    return t, p01, ce, cg


def run_v1(bundle, quick):
    """Bare pump vs Stark-retuned pump. Recalibrate once if the 0.3 µs trace misses P=0.95."""
    eps = bundle["eps_p_star"]
    if quick:
        t_end, na, nb, n_save = 0.1, 6, 4, 201
        sweeps = None
    else:
        t_end, na, nb, n_save = 0.3, 10, 8, 601
        sweeps = {"Na": [8, 10], "Nb": [6, 8]}
    method = _method()
    g_guess = math.sqrt(2.0) * abs(bundle["g2_disp"])
    w_retuned = W_P + bundle["delta_retune"]
    out = {"t_end": t_end, "Na": na, "Nb": nb, "eps": eps}
    t0 = time.perf_counter()
    t, p_bare, _, _ = _exchange(W_P, t_end, na, nb, n_save, eps, method)
    _, p_ret, ce, cg = _exchange(w_retuned, t_end, na, nb, n_save, eps, method)
    fit = _fit_exchange(t, p_ret, ce, cg, g_guess)
    print(f"V1 first retune: max P01 bare={p_bare.max():.4f} retuned={fit['pmax']:.4f} "
          f"|g2|/2pi={fit['g2_MHz']:.4f} MHz  delta/2pi={fit['delta'] / C.TWO_PI:.3f} MHz")
    p_final, fit_final, w_final = p_ret, fit, w_retuned
    delta_applied = 0.0
    # A 0.1 µs quick trace cannot reach the 0.232 µs full-transfer peak, so it always
    # sits below 0.95. Recalibrate only on the production window.
    if not quick and fit["pmax"] < 0.95:
        w_try = w_retuned - fit["delta"]
        _, p_try, ce2, cg2 = _exchange(w_try, t_end, na, nb, n_save, eps, method)
        fit_try = _fit_exchange(t, p_try, ce2, cg2, g_guess)
        print(f"V1 recalibration: max P01={fit_try['pmax']:.4f} "
              f"shift/2pi={-fit['delta'] / C.TWO_PI:.3f} MHz")
        if fit_try["pmax"] >= fit["pmax"]:
            p_final, fit_final, w_final = p_try, fit_try, w_try
            delta_applied = -fit["delta"]
    # rtol 1e-8 -> 1e-10 on the trace we keep. The gate is |ΔP01| < 1e-4.
    rtol_shift = None
    if not quick:
        _, p_tight, _, _ = _exchange(w_final, t_end, na, nb, n_save, eps, _method(rtol=1e-10, atol=1e-12))
        rtol_shift = float(np.max(np.abs(p_tight - p_final)))
        print(f"V1 rtol 1e-10 vs 1e-8: max |ΔP01|={rtol_shift:.3e}")
    na_fits, nb_fits = {}, {}
    if sweeps:
        for na_i in sweeps["Na"]:
            if na_i == na:
                na_fits[na_i] = fit_final["g2_MHz"]
                continue
            _, p_i, ce_i, cg_i = _exchange(w_final, t_end, na_i, nb, n_save, eps, method)
            na_fits[na_i] = _fit_exchange(t, p_i, ce_i, cg_i, g_guess)["g2_MHz"]
        for nb_i in sweeps["Nb"]:
            if nb_i == nb:
                nb_fits[nb_i] = fit_final["g2_MHz"]
                continue
            _, p_i, ce_i, cg_i = _exchange(w_final, t_end, na, nb_i, n_save, eps, method)
            nb_fits[nb_i] = _fit_exchange(t, p_i, ce_i, cg_i, g_guess)["g2_MHz"]
    g_half = math.sqrt(2.0) * abs(bundle["g2_disp"])
    g_tutorial = math.sqrt(2.0) * abs(bundle["g2_tutorial_MHz"]) * C.TWO_PI
    out.update({
        "t": t, "p_bare": p_bare, "p_retuned": p_final, "fit": fit_final,
        "w_final": float(w_final), "delta_applied": float(delta_applied),
        "rtol_shift": rtol_shift, "na_fits": na_fits, "nb_fits": nb_fits,
        "p_half": _rabi(t, g_half, 0.0), "p_tutorial": _rabi(t, g_tutorial, 0.0),
        "wall_s": time.perf_counter() - t0,
    })
    return out


def _moments_displaced(t, expects, w_pump, eps, stark_b):
    """⟨n_a⟩_d and ⟨b_d⟩ e^{i stark t} from rotating-frame moments and the linear ξ."""
    a, na, b, a2 = (np.asarray(expects[i]) for i in range(4))
    f0_a, f0_b = _cosine_force(eps, PHI_A), _cosine_force(eps, PHI_B)
    xi_a = _xi_lab(t, W_A, w_pump, f0_a) * np.exp(1j * W_A * t)
    xi_b = _xi_lab(t, W_B, w_pump, f0_b) * np.exp(1j * W_B * t)
    n_d = np.real(na) - 2.0 * np.real(np.conj(xi_a) * a) + np.abs(xi_a) ** 2
    b_d = b - xi_b
    b_eff = b_d * np.exp(1j * stark_b * t)
    a2_d = a2 - 2.0 * xi_a * a + xi_a ** 2
    return n_d, b_eff, a2_d


def run_v2(bundle, quick, alpha2, na, nb):
    """Inflation from the displaced vacuum. E0/E1/E2 are two_mode comparisons (needs l0-core extra_H)."""
    import inspect
    if "extra_H" not in inspect.signature(two_mode).parameters:
        raise SystemExit(
            "PAUSED_FOR_L0_CORE: two_mode(..., extra_H=) is not merged, so V2 cannot be compared yet."
        )
    eps = bundle["eps_p_star"]
    if na is None:
        na = 8 if quick else 12
    if nb is None:
        nb = 4 if quick else 6
    t_end, n_save = (40e-3, 81) if quick else (0.2, 401)
    eps_d = alpha2 * abs(bundle["g2_disp"])
    w_pump = W_P + bundle["delta_retune"]
    method = _method()
    h_ats = circuit_rotating_H(na, nb, EJ, eps, PHI_A, PHI_B, W_A, W_B, w_pump, max_order=5)
    a, b = dq.destroy(na, nb)
    # destroy() is sparse; adding it to the dense circuit H every step densifies and warns.
    b_dense = dq.asqarray(jnp.asarray(b.to_jax()), dims=(na, nb))
    stark_b = bundle["sb"]

    def h_total(t):
        drive = -eps_d * (
            b_dense * jnp.exp(1j * stark_b * t) + b_dense.dag() * jnp.exp(-1j * stark_b * t))
        return h_ats(t) + drive

    h = dq.timecallable(h_total)
    jumps = [jnp.sqrt(C.KAPPA_B) * b, jnp.sqrt(C.KAPPA_A) * a]
    f0_a, f0_b = _cosine_force(eps, PHI_A), _cosine_force(eps, PHI_B)
    xi_a0 = complex(_xi_lab(np.array([0.0]), W_A, w_pump, f0_a)[0])
    xi_b0 = complex(_xi_lab(np.array([0.0]), W_B, w_pump, f0_b)[0])
    psi0 = dq.tensor(dq.displace(na, xi_a0) @ dq.fock(na, 0), dq.displace(nb, xi_b0) @ dq.fock(nb, 0))
    t = np.linspace(0.0, t_end, n_save)
    ops = [a, a.dag() @ a, b, a @ a]
    res = dq.mesolve(h, jumps, psi0, jnp.asarray(t), exp_ops=ops, method=method, save_states=False)
    n_d, b_eff, a2_d = _moments_displaced(t, res.expects, w_pump, eps, stark_b)

    g2 = bundle["g2_disp"]
    g2_tutorial = -EJ * eps * PHI_A ** 2 * PHI_B
    x_e1 = extra_H(na, nb, bundle["ka"], bundle["kb"], bundle["chi"])
    models = {
        "E0": two_mode(na, nb, g2, eps_d, C.KAPPA_B, C.KAPPA_A),
        "E1": two_mode(na, nb, g2, eps_d, C.KAPPA_B, C.KAPPA_A, extra_H=x_e1),
        "E2": two_mode(na, nb, g2_tutorial, eps_d, C.KAPPA_B, C.KAPPA_A),
    }
    ref = {}
    for name, (h_m, jumps_m, (a_m, b_m)) in models.items():
        r = dq.mesolve(h_m, jumps_m, vacuum2(na, nb), jnp.asarray(t), method=method, save_states=False,
                       exp_ops=[a_m.dag() @ a_m, b_m])
        ref[name] = (np.real(np.asarray(r.expects[0])), np.asarray(r.expects[1]))
    errors = {}
    for name, (n_ref, b_ref) in ref.items():
        errors[name] = {
            "dn": float(np.max(np.abs(n_d - n_ref))),
            "db": float(np.max(np.abs(b_eff - b_ref))),
        }
        print(f"V2 {name}: max|Δn_a|={errors[name]['dn']:.4f} max|Δb|={errors[name]['db']:.4f}")
    return {
        "t": t, "n_d": n_d, "b_eff": b_eff, "a2_d": a2_d, "ref": ref, "errors": errors,
        "Na": na, "Nb": nb, "alpha2": alpha2, "eps_d": eps_d, "t_end": t_end,
        "re_a2_final": float(np.real(a2_d[-1])),
    }


def _plot_validation(v1, v2, save_fig, quick):
    fig, ax = plt.subplots(1, 2 if v2 is None else 3, figsize=(11 if v2 is None else 14, 3.8))
    ax[0].plot(v1["t"], v1["p_bare"], lw=1.5, label="bare pump")
    ax[0].plot(v1["t"], v1["p_retuned"], lw=1.5, label="retuned pump")
    ax[0].plot(v1["t"], v1["p_half"], "k--", lw=1, label="½ formula, δ=0")
    ax[0].plot(v1["t"], v1["p_tutorial"], ":", lw=1, label="no-½ formula, δ=0")
    ax[0].set(xlabel="t (µs)", ylabel="P(|0,1⟩)", title="V1 exchange in the displaced frame")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=0.3)
    if v2 is not None:
        ax[1].plot(v2["t"], v2["n_d"], lw=1.8, label="circuit")
        for name, style in (("E0", "--"), ("E1", "-"), ("E2", ":")):
            ax[1].plot(v2["t"], v2["ref"][name][0], style, lw=1.2, label=name)
        ax[1].set(xlabel="t (µs)", ylabel="⟨n_a⟩ displaced", title="V2 inflation")
        ax[1].legend(fontsize=7)
        ax[1].grid(alpha=0.3)
        ax[2].plot(v2["t"], np.real(v2["b_eff"]), lw=1.8, label="circuit Re⟨b⟩_eff")
        ax[2].plot(v2["t"], np.real(v2["ref"]["E1"][1]), lw=1.2, label="E1")
        ax[2].plot(v2["t"], np.real(v2["ref"]["E2"][1]), ":", lw=1.2, label="E2")
        ax[2].set(xlabel="t (µs)", ylabel="Re ⟨b⟩", title="buffer amplitude")
        ax[2].legend(fontsize=7)
        ax[2].grid(alpha=0.3)
    save_fig(fig, "task_2_4a_validation", quick=quick)
    plt.close(fig)


def write_tdsim(bundle, v1, v2, quick):
    record, save_arrays, _std, convergence_block, save_fig = _writers()
    script = "tasks/task_2_4a.py"
    params = _params(bundle["eps_p_star"], 5)
    fit = v1["fit"]
    if v1["na_fits"]:
        rows_na = [{"Na": k, "Nb": v1["Nb"], "g2": v} for k, v in sorted(v1["na_fits"].items())]
        rows_nb = [{"Nb": k, "Na": v1["Na"], "g2": v} for k, v in sorted(v1["nb_fits"].items())]
        conv = convergence_block(
            {"Na": ({"Nb": v1["Nb"]}, rows_na), "Nb": ({"Na": v1["Na"]}, rows_nb)},
            key="g2", rel_tol=2e-3, chosen={"Na": v1["Na"], "Nb": v1["Nb"]},
        )
    else:
        conv = None
    g2_disp = abs(bundle["g2_disp_MHz"])
    g2_sym_rescaled = abs(bundle["g2_sym_MHz"]) * bundle["eps_p_star"] / 0.035
    checks = [
        _cross("g2_disp", g2_disp, fit["g2_MHz"], 0.03),
        _cross("g2_sym_rescaled", g2_sym_rescaled, fit["g2_MHz"], 0.03, ref_id="t2_4a.g2.sym.circuit"),
    ]
    # The sym record's second check needs this fit. Rewrite it now that the number exists.
    write_sym(bundle, quick, tdsim_g2_mhz=fit["g2_MHz"])
    notes = (
        f"eps_p*={bundle['eps_p_star']:.5f}. G/2pi={fit['G'] / C.TWO_PI:.4f} MHz, "
        f"delta_fit/2pi={fit['delta'] / C.TWO_PI:.4f} MHz, "
        f"extra pump shift applied/2pi={v1['delta_applied'] / C.TWO_PI:.4f} MHz. "
        f"max P01 bare={float(np.max(v1['p_bare'])):.4f}, retuned={fit['pmax']:.4f}. "
        f"rtol 1e-10 change in P01={v1['rtol_shift']}. "
        f"omega_p' /2pi = {v1['w_final'] / C.TWO_PI / 1e3:.6f} GHz."
    )
    if v2 is not None:
        notes += (
            f" V2 alpha2={v2['alpha2']}, Na={v2['Na']}, Nb={v2['Nb']}: "
            + ", ".join(f"{k} max|dn|={v['dn']:.4f} max|db|={v['db']:.4f}"
                        for k, v in v2["errors"].items())
            + f". Re⟨a²⟩_d(final)={v2['re_a2_final']:.4f}."
        )
    arrays = dict(t_v1=v1["t"], p01_bare=v1["p_bare"], p01_retuned=v1["p_retuned"],
                  p01_half=v1["p_half"], p01_tutorial=v1["p_tutorial"])
    if v2 is not None:
        arrays.update(t_v2=v2["t"], n_td=v2["n_d"], b_td=np.real(v2["b_eff"]),
                      n_e0=v2["ref"]["E0"][0], n_e1=v2["ref"]["E1"][0], n_e2=v2["ref"]["E2"][0],
                      b_e1=np.real(v2["ref"]["E1"][1]))
    save_arrays("t2_4a.g2.tdsim.circuit", quick=quick, **arrays)
    _plot_validation(v1, v2, save_fig, quick)
    record(
        "t2_4a.g2.tdsim.circuit", task="2.4a", quantity="g2", value=fit["g2_MHz"],
        units="MHz", method="tdsim_rabi_fit", params=params, script=script,
        truncation={"Na": v1["Na"], "Nb": v1["Nb"]}, convergence=conv,
        numerics={"fit_window_us": v1["t_end"], "rel_rms_residual": fit["rel_rms"]},
        cross_check=checks, quick=quick, notes=notes, wall_s=v1["wall_s"],
        artifacts={"figure": "figures/task_2_4a_validation.png",
                   "arrays": "results/arrays/t2_4a.g2.tdsim.circuit.npz"},
    )
    # Bare-pump population calibrates 2 stark_a - stark_b. Rewrite that one check onto stark_b
    # only when the trace is long enough for the saturated amplitude to mean a detuning.
    if v1["t_end"] >= 0.25:
        record_stark_v1(bundle, v1, quick)


def record_stark_v1(bundle, v1, quick):
    """Add the V1 detuning cross-check onto the stark_b record (tol 0.1, brief §7)."""
    record, _arrays, _std, convergence_block, _fig = _writers()
    pmax = float(np.max(v1["p_bare"]))
    g = math.sqrt(2.0) * abs(bundle["g2_disp"])
    # Pmax = 4G²/(4G²+δ²) on a trace that covers the peak. Guard a numerical zero.
    if pmax <= 0 or pmax >= 1:
        return
    delta_bare = 2.0 * g * math.sqrt(max(1.0 / pmax - 1.0, 0.0))
    predicted = abs(bundle["delta_retune"])
    # The first-order retune is 2 stark_a - stark_b (+ a negligible 2 kerr_a).
    # Re-record stark_b with the analytic check AND this one. Convergence is rebuilt.
    rows = [{"n_t": r["n_t"], "stark_b": r["stark_b"]} for r in bundle["nt_rows"]]
    conv = convergence_block(
        {"n_t": ({"eps_p": bundle["eps_p_star"], "max_order": 4}, rows)},
        key="stark_b", rel_tol=1e-8, chosen={"n_t": bundle["n_t"]},
    )
    checks = [
        _cross("analytic_C2", bundle["stark_b_analytic_MHz"], bundle["stark_b_MHz"], 0.05),
        _cross("v1_bare_detuning", delta_bare / C.TWO_PI, predicted / C.TWO_PI, 0.1),
    ]
    record(
        "t2_4a.stark_b.sym.circuit", task="2.4a", quantity="stark_b",
        value=bundle["stark_b_MHz"], units="MHz", method="displaced_frame_rwa1",
        params=_params(bundle["eps_p_star"], bundle["max_order"]),
        script="tasks/task_2_4a.py", convergence=conv, cross_check=checks, quick=quick,
        notes=(
            f"V1 bare-pump |delta|/2pi={delta_bare / C.TWO_PI:.3f} MHz from max P01={pmax:.4f}; "
            f"2*stark_a - stark_b + 2*kerr_a = {predicted / C.TWO_PI:.3f} MHz. "
            f"eps_p*={bundle['eps_p_star']:.5f}, omega_p'/2pi={bundle['wp_prime_GHz']:.6f} GHz, "
            f"buffer drive {bundle['wb_drive_GHz']:.6f} GHz."
        ),
    )


def main(part, quick, alpha2, na, nb):
    n_t = 256 if quick else 512
    max_order = 5 if quick else 7
    t0 = time.perf_counter()
    bundle = collect_sym(n_t=n_t, max_order=max_order)
    bundle["loss_3g2_per_us"] = _loss_at_3g2(bundle["g_bs_over_ez"])
    print(f"sym collected in {time.perf_counter() - t0:.1f}s: eps_p*={bundle['eps_p_star']:.5f} "
          f"g2_disp={bundle['g2_disp_MHz']:.4f} MHz stark_b={bundle['stark_b_MHz']:.3f} MHz "
          f"wp'={bundle['wp_prime_GHz']:.6f} GHz", flush=True)
    # Fail before a multi-minute trace if the record API is not merged yet.
    if part in ("sym", "all"):
        write_sym(bundle, quick)
        if part == "sym":
            return
    _writers()
    v1 = None
    # The queued α=2.1 job is an inflation run. Don't repeat the exchange on that invocation.
    if alpha2 == 1.0:
        v1 = run_v1(bundle, quick)
    v2 = run_v2(bundle, quick, alpha2, na, nb) if part in ("tdsim", "all") else None
    if v1 is None:
        _record, save_arrays, _std, _block, _fig = _writers()
        save_arrays(
            "t2_4a.inflation.tdsim.circuit", quick=quick,
            t_v2=v2["t"], n_td=v2["n_d"], b_td=np.real(v2["b_eff"]),
            n_e0=v2["ref"]["E0"][0], n_e1=v2["ref"]["E1"][0], n_e2=v2["ref"]["E2"][0],
            alpha2=np.array([v2["alpha2"]]), Na=np.array([v2["Na"]]), Nb=np.array([v2["Nb"]]),
        )
        print("V2-only traces saved under t2_4a.inflation.tdsim.circuit (no g2 fit on this invocation).")
        return
    write_tdsim(bundle, v1, v2, quick)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Task 2.4a circuit reduction")
    p.add_argument("--part", choices=("sym", "tdsim", "all"), default="all")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--alpha2", type=float, default=1.0, help="|alpha|^2 of the V2 buffer drive")
    p.add_argument("--na", type=int, default=None)
    p.add_argument("--nb", type=int, default=None)
    args = p.parse_args()
    main(args.part, args.quick, args.alpha2, args.na, args.nb)
