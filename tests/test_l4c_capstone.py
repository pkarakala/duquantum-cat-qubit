"""Lane l4c-capstone: pulse shapes, the SVD optimality identity, and two small two-mode checks.

Fast tests are linear algebra. The two-mode checks are marked slow (brief 10 §5).
"""
import numpy as np
import pytest

from src import config as C


def test_pulse_shapes_and_energy():
    from src.pulses import clear, energy, from_bins, ramp, square

    edges, values = square(1.0, 2.0, 40)
    assert edges.shape == (41,) and values.shape == (40,)
    assert np.all(np.diff(edges) > 0)
    # ∫ (2)^2 dt over 1 µs
    assert abs(energy(edges, values) - 4.0) <= 1e-12

    edges, values = ramp(1.0, 2.5, 0.3, 60, kind="cos")
    assert edges.shape == (61,) and np.all(np.diff(edges) > 0)
    assert values[0] == 0.0
    # value on a bin is the envelope at its left edge, so the first bin at or after tau is amp
    k = int(np.searchsorted(edges[:-1], 0.3, side="left"))
    assert abs(values[k] - 2.5) <= 1e-12
    assert np.all(values[:k] < 2.5)

    edges, values = ramp(1.0, 2.5, 0.3, 60, kind="lin")
    assert values[0] == 0.0
    k = int(np.searchsorted(edges[:-1], 0.3, side="left"))
    assert abs(values[k] - 2.5) <= 1e-12
    assert np.all(values[:k] <= 2.5 + 1e-12)

    edges, values = clear(1.0, 3.0, 0.2, 1.0, 40)
    assert edges.shape == (41,) and np.all(np.diff(edges) > 0)
    t_left = edges[:-1]
    assert np.all(values[t_left < 0.2] == 3.0)
    assert np.all(values[t_left >= 0.2] == 1.0)

    edges, values = from_bins(np.array([1.0, -2.0, 0.5]), 1.5)
    assert edges.shape == (4,) and np.all(np.diff(edges) > 0)
    assert abs(edges[-1] - 1.5) <= 1e-12
    assert np.allclose(values, [1.0, -2.0, 0.5])


def test_snr_known_signal():
    from src.pulses import snr

    t = np.linspace(0.0, 1.0, 4001)
    delta_b = np.full(t.shape, 0.1)
    # κ_b ∫ |Δb|² dt = 16.33628 * 0.01 * 1, and a constant is exact under the trapezoid rule
    got = snr(t, delta_b, 16.33628)
    assert abs(got - 0.1633628) <= 1e-6


def test_svd_gain_ge_square_gain_equal_energy():
    from src.linresp import optimal_pulse, response_matrices
    from src.pulses import square

    T, n_bins, n_samples = 1.0, 40, 200
    R_b, _ = response_matrices(T, n_bins, n_samples, C.G2, C.KAPPA_B, C.ALPHA)
    eps_svd, _ = optimal_pulse(R_b, energy=1.0)
    _, eps_sq = square(T, 1.0 / np.sqrt(n_bins), n_bins)
    g_svd = float(np.linalg.norm(R_b @ eps_svd) ** 2)
    g_sq = float(np.linalg.norm(R_b @ eps_sq) ** 2)
    # Rayleigh quotient: the top singular vector wins at fixed ||ε||². Relative slack 1e-12.
    assert g_svd >= g_sq * (1.0 - 1e-12)


def test_generalized_pulse_ratio_ge_square():
    from src.linresp import optimal_pulse, response_matrices
    from src.pulses import square

    T, n_bins, n_samples = 1.0, 40, 200
    R_b, R_a = response_matrices(T, n_bins, n_samples, C.G2, C.KAPPA_B, C.ALPHA)
    # optimal_pulse adds (delta * tr(L) / n) I; delta = 1e-9 * n makes that 1e-9 * tr(L) I
    eps_g, _ = optimal_pulse(R_b, R_a, energy=1.0, delta=1e-9 * n_bins)
    _, eps_sq = square(T, 1.0 / np.sqrt(n_bins), n_bins)

    def ratio(eps):
        num = float(np.linalg.norm(R_b @ eps) ** 2)
        den = float(np.linalg.norm(R_a @ eps) ** 2)
        return num / den

    assert ratio(eps_g) >= ratio(eps_sq) * (1.0 - 1e-12)


def test_svd_pulse_spectrum_reported(capsys):
    from src.linresp import optimal_pulse, response_matrices

    T, n_bins, n_samples = 1.0, 40, 200
    R_b, _ = response_matrices(T, n_bins, n_samples, C.G2, C.KAPPA_B, C.ALPHA)
    eps, _ = optimal_pulse(R_b, energy=1.0)
    dt = T / n_bins
    spec = np.abs(np.fft.rfft(eps))
    freq = np.fft.rfftfreq(n_bins, d=dt)  # cycles per µs == MHz
    k = int(np.argmax(spec[1:])) + 1
    peak = float(freq[k])
    print(f"SVD pulse FFT peak: {peak:.6f} MHz")
    assert np.isfinite(peak) and peak > 0.0
    captured = capsys.readouterr()
    assert "SVD pulse FFT peak:" in captured.out


def _baseline_subtracted_delta_b(Na, Nb, alpha, edges, values, t, method):
    """Δ⟨b⟩(t) = (⟨b⟩₊ − ⟨b⟩₊,ε=0) − (⟨b⟩₋ − ⟨b⟩₋,ε=0) after a 3 µs well preparation."""
    from tasks.task_2_4c_verify import well_expectation_b

    bp = well_expectation_b(Na, Nb, +alpha, edges, values, t, method, prep_us=3.0)
    bm = well_expectation_b(Na, Nb, -alpha, edges, values, t, method, prep_us=3.0)
    bp0 = well_expectation_b(Na, Nb, +alpha, edges, np.zeros_like(values), t, method, prep_us=3.0)
    bm0 = well_expectation_b(Na, Nb, -alpha, edges, np.zeros_like(values), t, method, prep_us=3.0)
    return (bp - bp0) - (bm - bm0)


@pytest.mark.slow
def test_linresp_vs_two_mode_small_amplitude():
    from src.linresp import response
    from src.pulses import square

    Na, Nb, alpha = 16, 5, 2.1
    eps = 0.1 * C.G2
    edges, values = square(1.0, eps, 40)
    t = np.linspace(0.0, 1.0, 81)
    method = C.METHOD
    db = _baseline_subtracted_delta_b(Na, Nb, alpha, edges, values, t, method)
    eps_t = np.full(t.shape, eps)
    _, bp = response(eps_t, t, C.G2, C.KAPPA_B, alpha, well=+1)
    _, bm = response(eps_t, t, C.G2, C.KAPPA_B, alpha, well=-1)
    db_lin = bp - bm
    mask = (t >= 0.2) & (t <= 1.0)
    num = float(np.sqrt(np.mean(np.abs(db[mask] - db_lin[mask]) ** 2)))
    den = float(np.sqrt(np.mean(np.abs(db_lin[mask]) ** 2)))
    rel = num / den
    print(f"linresp vs two-mode RMS relative Δb: {rel:.4f}")
    assert rel <= 0.10


@pytest.mark.slow
def test_readout_symmetry_with_pulse():
    import dynamiqs as dq

    from src.pulses import clear
    from tasks.task_2_4c_verify import well_expectation_b

    Na, Nb, alpha = 14, 5, C.ALPHA
    edges, values = clear(0.4, 0.30, 0.08, 0.15, 20)
    t = np.linspace(0.0, 0.4, 41)
    # tighter than C.METHOD so the integrator can resolve an exact antiunitary identity
    method = dq.method.Tsit5(rtol=1e-12, atol=1e-14, max_steps=10_000_000)
    bp = well_expectation_b(Na, Nb, +alpha, edges, values, t, method, prep_us=0.0)
    bm = well_expectation_b(Na, Nb, -alpha, edges, values, t, method, prep_us=0.0)
    err = float(np.max(np.abs(bm + np.conj(bp))))
    print(f"readout symmetry max |⟨b⟩₋ + conj(⟨b⟩₊)|: {err:.3e}")
    assert err <= 1e-9
