"""Physics checks against the committed intro-track anchors."""
import numpy as np
import pytest

from src import config as C
from server.app.sim import WIGNER_PIXELS, run_one_mode, run_two_mode


def test_wigner_vacuum_convention():
    """dynamiqs hbar=0.5 puts vacuum at W(0, 0) = 2/π. P1 matches this grid."""
    import dynamiqs as dq

    ket = dq.fock(30, 0)
    xvec, yvec, wigner = dq.wigner(ket, xmax=4.0, ymax=4.0, npixels=WIGNER_PIXELS)
    x = np.asarray(xvec)
    y = np.asarray(yvec)
    w = np.asarray(wigner)
    i = int(np.argmin(np.abs(x)))
    j = int(np.argmin(np.abs(y)))
    assert abs(x[i]) < 1e-12 and abs(y[j]) < 1e-12
    assert abs(float(w[i, j]) - 2 / np.pi) < 1e-6


@pytest.mark.slow
def test_one_mode_physics():
    """Vacuum to cat, nominal κ₂ with κ_a on. Task 1.0c final_n[1] = 4.403969."""
    result = run_one_mode({
        "alpha": float(C.ALPHA),
        "kappa2_scale": 1.0,
        "kappa_a_scale": 1.0,
        "N": 30,
        "t_end_us": 2.0,
        "n_t": 200,
        "init": "vacuum",
        "outputs": ["n", "parity"],
    })
    final_n = result["n"][-1]
    assert abs(final_n - 4.403969) / 4.403969 < 0.01
    assert len(result["n"]) == 200
    assert result["meta"]["engine"] == "dynamiqs 0.3.7"


def test_two_mode_live_shape():
    """16×5 over 2 µs. The memory overshoots α², and every series has 201 samples."""
    result = run_two_mode({
        "alpha": float(C.ALPHA),
        "Na": 16,
        "Nb": 5,
        "t_end_us": 2.0,
        "init": "vacuum",
        "outputs": ["na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity"],
    })
    for name in ("t_us", "na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity"):
        assert len(result[name]) == 201, name
    assert max(result["na"]) > 4.41
