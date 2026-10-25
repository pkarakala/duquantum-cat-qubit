"""Write the level presets and the Wigner / linear-response fixtures.

Two-mode grids above the live cap (24×6 and 32×12) are references, not live
requests. Level 7 is computed at 16×5 because the l4a readout arrays are not
on this branch. Run from the repo root: python -m server.precompute --levels all
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from src import config as C
import dynamiqs as dq

from server.app.expr import to_python
from server.app.sim import WIGNER_PIXELS, run_expr, run_one_mode, run_two_mode

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "server" / "precomputed" / "presets"
WIGNER = ROOT / "server" / "tests" / "fixtures" / "wigner"
LINRESP = ROOT / "server" / "tests" / "fixtures" / "linresp"
H2 = json.loads((ROOT / "server" / "tests" / "fixtures" / "expr" / "h_2ph.json").read_text())["tree"]
JUMP_B = json.loads((ROOT / "server" / "tests" / "fixtures" / "expr" / "jump_buffer.json").read_text())["tree"]
JUMP_A = json.loads((ROOT / "server" / "tests" / "fixtures" / "expr" / "jump_memory.json").read_text())["tree"]


def _dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {path.relative_to(ROOT)}")


def _save(name: str, response: dict, **note) -> None:
    body = dict(response)
    body["meta"] = dict(response.get("meta") or {})
    body["meta"]["preset"] = name
    body["meta"].update(note)
    _dump(PRESETS / f"{name}.json", body)


def _one(**kwargs) -> dict:
    req = {
        "alpha": 2.1,
        "kappa2_scale": 0.0,
        "kappa_a_scale": 0.0,
        "N": 30,
        "t_end_us": 0.05,
        "n_t": 3,
        "init": "coherent",
        "outputs": ["n", "parity", "re_a"],
    }
    req.update(kwargs)
    if req.get("init") == "coherent" and "init_alpha" not in req:
        req["init_alpha"] = req["alpha"]
    return run_one_mode(req)


def _expr(tree, jumps, **kwargs) -> dict:
    req = {
        "H": tree,
        "jumps": jumps,
        "params": {},
        "modes": "one",
        "N": 30,
        "t_end_us": 1.0,
        "n_t": 201,
        "init": "coherent",
        "init_alpha": 2.0,
        "outputs": ["n", "parity", "re_a"],
    }
    req.update(kwargs)
    return run_expr(req)


def write_l1() -> None:
    for name, alpha in (("L1", 2.1), ("L1_alpha_1", 1.0), ("L1_alpha_2", 2.0), ("L1_alpha_3", 3.0)):
        outputs = ["n", "parity", "re_a"]
        extra = {}
        if name == "L1":
            outputs = outputs + ["wigner"]
            extra["wigner_times"] = [0.0]
        _save(name, _one(alpha=alpha, outputs=outputs, **extra), level="L1")


def write_l2() -> None:
    # Single-photon loss is not the cat dissipator, so this level goes through ExprTree.
    rotate = {"op": "mul", "args": [{"op": "num", "value": float(C.TWO_PI)}, {"op": "sym", "name": "n_a"}]}
    still = {"op": "num", "value": 0}
    jump = {"op": "mul", "args": [{"op": "sqrt", "arg": {"op": "param", "name": "kappa_a"}}, {"op": "sym", "name": "a"}]}
    positions = {
        "L2": (float(np.log(2) / 0.5), rotate),
        "L2_kappa_0": (0.0, rotate),
        "L2_kappa_ln2": (float(np.log(2) / 0.5), rotate),
        "L2_kappa_1mhz": (float(C.TWO_PI), still),
    }
    for name, (kappa, hamiltonian) in positions.items():
        result = _expr(hamiltonian, [] if kappa == 0 else [jump], params={"kappa_a": kappa})
        _save(name, result, level="L2", kappa_a=kappa)


def write_l3() -> None:
    zero = {"op": "num", "value": 0}
    jump = {
        "op": "mul",
        "args": [
            {"op": "sqrt", "arg": {"op": "param", "name": "kappa2"}},
            {"op": "pow", "base": {"op": "sym", "name": "a"}, "exp": 2},
        ],
    }
    positions = {
        "L3": (2.0, 1.0),
        "L3_k2_quarter": (2.0, 0.25),
        "L3_k2_nominal": (2.0, 1.0),
        "L3_k2_four": (2.0, 4.0),
    }
    for name, (alpha, scale) in positions.items():
        result = _expr(
            zero, [jump],
            params={"kappa2": float(C.KAPPA_2) * scale},
            init_alpha=alpha,
            t_end_us=3.0,
            n_t=301,
        )
        _save(name, result, level="L3", alpha=alpha, kappa2_scale=scale)


def write_l4() -> None:
    base = {
        "kappa2_scale": 1.0,
        "N": 30,
        "init": "vacuum",
        "t_end_us": 2.0,
        "n_t": 201,
        "outputs": ["n", "parity", "re_a"],
    }
    specs = {
        "L4": {"alpha": float(C.ALPHA), "kappa_a_scale": 0.0, "outputs": ["n", "parity", "re_a", "wigner"], "wigner_times": [0.0, 1.0, 2.0]},
        "L4_alpha_1": {"alpha": 1.0, "kappa_a_scale": 0.0},
        "L4_alpha_2_5": {"alpha": 2.5, "kappa_a_scale": 0.0},
        "L4_loss_x20": {"alpha": float(C.ALPHA), "kappa_a_scale": 20.0},
    }
    for name, spec in specs.items():
        req = dict(base)
        req.update(spec)
        _save(name, run_one_mode(req), level="L4")


def _two(name: str, note: dict | None = None, **kwargs) -> None:
    req = {
        "alpha": float(C.ALPHA),
        "Na": 16,
        "Nb": 5,
        "t_end_us": 2.0,
        "init": "vacuum",
        "outputs": ["na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity"],
    }
    req.update(kwargs)
    meta = {"level": "L6", "Na": req["Na"], "Nb": req["Nb"]}
    if note:
        meta.update(note)
    _save(name, run_two_mode(req), **meta)


def _expr_two(name: str, hamiltonian, jumps) -> None:
    result = run_expr({
        "H": hamiltonian,
        "jumps": jumps,
        "params": {},
        "modes": "two",
        "Na": 16,
        "Nb": 5,
        "t_end_us": 2.0,
        "n_t": 201,
        "init": "vacuum",
        "outputs": ["na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity"],
    })
    _save(name, result, level="L6", Na=16, Nb=5, compiled=to_python(hamiltonian))


def _eps_z_wrong():
    return {
        "op": "add",
        "args": [
            {"op": "mul", "args": [{"op": "param", "name": "g2"}, {"op": "pow", "base": {"op": "sym", "name": "a"}, "exp": 2}, {"op": "sym", "name": "bd"}]},
            {"op": "mul", "args": [{"op": "param", "name": "g2"}, {"op": "pow", "base": {"op": "sym", "name": "ad"}, "exp": 2}, {"op": "sym", "name": "b"}]},
            {"op": "mul", "args": [{"op": "param", "name": "eps_z"}, {"op": "add", "args": [{"op": "sym", "name": "a"}, {"op": "sym", "name": "ad"}]}]},
        ],
    }


def _a_bd2():
    return {
        "op": "add",
        "args": [
            {"op": "mul", "args": [{"op": "param", "name": "g2"}, {"op": "sym", "name": "a"}, {"op": "pow", "base": {"op": "sym", "name": "bd"}, "exp": 2}]},
            {"op": "mul", "args": [{"op": "param", "name": "g2"}, {"op": "sym", "name": "ad"}, {"op": "pow", "base": {"op": "sym", "name": "b"}, "exp": 2}]},
            {"op": "mul", "args": [{"op": "num", "value": -1}, {"op": "param", "name": "eps_d"}, {"op": "add", "args": [{"op": "sym", "name": "b"}, {"op": "sym", "name": "bd"}]}]},
        ],
    }


def write_l6() -> None:
    _two(
        "correct",
        outputs=["na", "nb", "b_re", "b_im", "top2_a", "top_b", "parity", "wigner"],
        wigner_times=[0.0, 0.25, 2.0],
    )
    _expr_two("missing_kappa_b", H2, [JUMP_A])
    # eps_z has no config default, so the wrong memory drive passes it in params.
    result = run_expr({
        "H": _eps_z_wrong(),
        "jumps": [JUMP_B, JUMP_A],
        "params": {"eps_z": float(C.EPS_D)},
        "modes": "two",
        "Na": 16,
        "Nb": 5,
        "t_end_us": 2.0,
        "n_t": 201,
        "init": "vacuum",
        "outputs": ["na", "nb", "parity"],
    })
    _save("eps_z_drive_wrong", result, level="L6", Na=16, Nb=5, note="memory Z drive instead of the buffer drive")
    _expr_two("a_bd2_wrong", _a_bd2(), [JUMP_B, JUMP_A])
    _two(
        "starter_24x6", note={"reference": True, "published_peak_na": 6.114517213948512},
        Na=24, Nb=6, t_end_us=3.0, n_t=301, outputs=["na", "nb", "top2_a", "top_b"],
    )
    _two(
        "converged_32x12", note={"reference": True, "published_peak_na": 6.894411732563246},
        Na=32, Nb=12, t_end_us=3.0, n_t=301, outputs=["na", "nb", "top2_a", "top_b"],
    )


def write_l7() -> None:
    ratios = (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 3.0)
    index = []
    for ratio in ratios:
        wells = {}
        for sign, label in ((1.0, "plus"), (-1.0, "minus")):
            wells[label] = run_two_mode({
                "alpha": float(C.ALPHA),
                "Na": 16,
                "Nb": 5,
                "t_end_us": 2.0,
                "init": "coherent",
                "init_alpha": sign * float(C.ALPHA),
                "eps_z_over_g2": ratio,
                "outputs": ["na", "b_re", "b_im"],
            })
        name = f"L7_eps_{str(ratio).replace('.', 'p')}"
        payload = {
            "eps_z_over_g2": ratio,
            "truncation": "16x5",
            "label": "computed at the live shape; l4a readout arrays are not on this branch",
            "plus": wells["plus"],
            "minus": wells["minus"],
        }
        _dump(PRESETS / f"{name}.json", payload)
        index.append(name)
    _dump(PRESETS / "L7.json", {
        "truncation": "16x5",
        "label": "computed at the live shape; l4a readout arrays are not on this branch",
        "files": index,
        "eps_z_over_g2": list(ratios),
    })


def write_wigner() -> None:
    N = 30
    states = {
        "vacuum": dq.fock(N, 0),
        "coherent2": dq.coherent(N, 2.0),
        "catplus2": dq.unit(dq.coherent(N, 2.0) + dq.coherent(N, -2.0)),
    }
    for name, state in states.items():
        xvec, yvec, wigner = dq.wigner(state, xmax=4.0, ymax=4.0, npixels=WIGNER_PIXELS)
        x = [float(v) for v in np.asarray(xvec)]
        y = [float(v) for v in np.asarray(yvec)]
        w = np.real(np.asarray(wigner))
        if name == "vacuum":
            i = int(np.argmin(np.abs(x)))
            j = int(np.argmin(np.abs(y)))
            center = float(w[i, j])
            if abs(center - 2 / np.pi) > 1e-6:
                raise SystemExit(f"vacuum W(0,0)={center}, expected 2/pi")
        _dump(WIGNER / f"{name}.json", {
            "N": N,
            "xmax": 4,
            "ymax": 4,
            "npixels": WIGNER_PIXELS,
            "x": x,
            "y": y,
            "w": w.tolist(),
        })


def _step(matrix, state, drive, dt):
    prop = expm(matrix * dt)
    eye = np.eye(2, dtype=np.complex128)
    particular = (prop - eye) @ np.linalg.solve(matrix, drive)
    return prop @ state + particular


def _response(edges, eps, well=1.0):
    g2, kappa_b, alpha = float(C.G2), float(C.KAPPA_B), float(C.ALPHA)
    coupling = -2j * well * g2 * alpha
    matrix = np.array([[0, coupling], [coupling, -0.5 * kappa_b]], dtype=np.complex128)
    poles = np.linalg.eigvals(matrix)
    dt = 0.002
    t_end = float(edges[-1])
    times = np.arange(0.0, t_end + dt * 0.5, dt)
    drive_vec = np.array([-1j, 0.0], dtype=np.complex128)
    state = np.zeros(2, dtype=np.complex128)
    buffer = [0j]
    prev = 0.0
    for t in times[1:]:
        # Hold the drive of the bin that contains the left edge of this step.
        bin_index = min(max(int(np.searchsorted(edges, prev, side="right") - 1), 0), len(eps) - 1)
        state = _step(matrix, state, drive_vec * float(eps[bin_index]), float(t - prev))
        buffer.append(state[1])
        prev = float(t)
    b = np.asarray(buffer)
    trap = getattr(np, "trapezoid", None) or np.trapz
    snr = float(kappa_b * trap(np.abs(b) ** 2, times))
    return {
        "edges_us": [float(v) for v in edges],
        "eps": [float(v) for v in eps],
        "t_us": [float(v) for v in times],
        "delta_b_re": [float(v) for v in np.real(b)],
        "delta_b_im": [float(v) for v in np.imag(b)],
        "snr": snr,
        "poles_re": [float(v) for v in np.real(poles)],
        "poles_im": [float(v) for v in np.imag(poles)],
        "g2": g2,
        "kappa_b": kappa_b,
        "alpha": alpha,
        "well": well,
        "reference_impl": True,
    }


def write_linresp() -> None:
    g2 = float(C.G2)
    square = _response([0.0, 1.0], [0.5 * g2])
    poles = sorted(zip(square["poles_re"], square["poles_im"]), key=lambda item: item[1])
    # λ = −4.08 ± 19.72i /µs at the nominal point.
    imag = abs(poles[-1][1])
    real = poles[-1][0]
    if abs(real + 4.08) > 0.05 or abs(imag - 19.72) > 0.05:
        raise SystemExit(f"linresp poles {poles} are not −4.08 ± 19.72i")
    n_bins = 20
    edges = [i / n_bins for i in range(n_bins + 1)]
    eps = [0.5 * g2 * 0.5 * (1 - np.cos(np.pi * (i + 0.5) / n_bins)) for i in range(n_bins)]
    _dump(LINRESP / "square.json", square)
    _dump(LINRESP / "cosramp.json", _response(edges, eps))
    _dump(LINRESP / "clear.json", _response([0.0, 1.0], [0.0]))


def write_index() -> None:
    files = sorted(path.name for path in PRESETS.glob("*.json") if path.name != "index.json")
    _dump(PRESETS / "index.json", {"presets": files})


def benchmark() -> None:
    one = {
        "alpha": float(C.ALPHA), "kappa2_scale": 1.0, "kappa_a_scale": 1.0,
        "N": 30, "t_end_us": 2.0, "n_t": 200, "init": "vacuum", "outputs": ["n"],
    }
    two = {
        "alpha": float(C.ALPHA), "Na": 16, "Nb": 5, "t_end_us": 2.0,
        "init": "vacuum", "outputs": ["na"],
    }
    out = {}
    for label, fn, req in (("one_mode", run_one_mode, one), ("two_mode", run_two_mode, two)):
        t0 = time.perf_counter()
        fn(req)
        out[f"cold_{label}_s"] = round(time.perf_counter() - t0, 3)
        t0 = time.perf_counter()
        fn(req)
        out[f"warm_{label}_s"] = round(time.perf_counter() - t0, 3)
    print(json.dumps(out))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--levels", default="all", choices=["all", "quick", "fixtures", "l1", "l2", "l3", "l4", "l6", "l7", "benchmark"])
    args = parser.parse_args()
    choice = args.levels
    if choice in ("all", "quick", "fixtures", "l1"):
        write_wigner()
        write_linresp()
    if choice in ("all", "quick", "l1"):
        write_l1()
    if choice == "quick":
        write_index()
        return
    if choice in ("all", "l2"):
        write_l2()
    if choice in ("all", "l3"):
        write_l3()
    if choice in ("all", "l4"):
        write_l4()
    if choice in ("all", "l6"):
        write_l6()
    if choice in ("all", "l7"):
        write_l7()
    if choice == "benchmark":
        benchmark()
        return
    if choice == "all":
        write_index()


if __name__ == "__main__":
    main()
