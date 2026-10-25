"""The only importer of the simulator.

Prefer P0's ``run_one_mode`` / ``run_two_mode``. This worktree has no P0 package and no
P1 browser solver, so ``MockSimClient`` speaks the CONTRACT §3 request shape and answers
from the closed forms already printed in LEVELS.md. It labels itself ``mock-sim``.
A test double that omits ``source`` is reported as the live channel the request used.
"""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path

PRESET_NAMES = ("correct", "missing_kappa_b", "eps_z_drive_wrong", "a_bd2_wrong")
TWO_MODE_TIMEOUT_S = 6.0
TWO_MODE_MIN_REMAINING_S = 8.0
_TWO_MODE = asyncio.Semaphore(1)
PRESET_DIR = Path(__file__).resolve().parents[2] / "precomputed" / "presets"

# κ_a from src/config.py (2π·9.3e-3). Duplicated as a float so this module does not
# import dynamiqs just to scale L2's slider. P0 applies the real constant when it runs.
_KAPPA_A = 0.05843318276972615


def kappa_a() -> float:
    try:
        from src.config import KAPPA_A

        return float(KAPPA_A)
    except Exception:
        return _KAPPA_A


class MockSimClient:
    """CONTRACT-shaped client used when P0 and P1 are not in this worktree."""

    label = "mock-sim"

    def one_mode(self, req: dict) -> dict:
        init_alpha = float(req.get("init_alpha") or 0)
        alpha = float(req.get("alpha") or 0)
        kappa_a_scale = float(req.get("kappa_a_scale") or 0)
        kappa2_scale = float(req.get("kappa2_scale") or 0)
        t_end = float(req.get("t_end_us") or 0)
        if req.get("init") == "fock":
            return {"error": "no_fock_init", "source": "mock-sim"}
        if alpha == 0 and kappa2_scale == 0 and kappa_a_scale == 0:
            n0 = init_alpha ** 2
            return {"t_us": [0.0, t_end], "n": [n0, n0], "parity": [1.0, 1.0], "source": "mock-sim"}
        if alpha == 0 and kappa2_scale == 0 and kappa_a_scale > 0:
            kappa = kappa_a_scale * kappa_a()
            return {
                "t_us": [0.0, 0.5, t_end or 2.0],
                "n": [4.0, 4.0 * math.exp(-kappa * 0.5), 4.0 * math.exp(-kappa * (t_end or 2.0))],
                "parity": [1.0, 1.0, 1.0],
                "source": "mock-sim",
            }
        if alpha == 0 and kappa_a_scale == 0:
            plateau = 0.5 * (1.0 - math.exp(-2.0 * init_alpha ** 2))
            return {
                "t_us": [0.0, t_end or 2.0],
                "n": [init_alpha ** 2, plateau],
                "parity": [1.0, 1.0],
                "source": "mock-sim",
            }
        n_ss = alpha ** 2
        parity = 0.2 if kappa_a_scale >= 1 else 0.98
        return {
            "t_us": [0.0, 1.0, t_end or 2.0],
            "n": [0.0, n_ss, n_ss],
            "parity": [1.0, parity, parity if kappa_a_scale < 1 else parity * 0.5],
            "source": "mock-sim",
        }

    async def two_mode(self, req: dict) -> dict:
        return {
            "t_us": [0.0, 2.0],
            "na": [0.0, 4.41],
            "nb": [0.0, 0.2],
            "source": "mock-sim",
            "Na": req.get("Na"),
            "Nb": req.get("Nb"),
        }


def p1_present() -> bool:
    root = Path(__file__).resolve().parents[3]
    return (root / "site" / "src" / "sim" / "index.ts").is_file()


def get_client():
    try:
        from server.app import sim as p0

        if hasattr(p0, "run_one_mode"):
            return _P0Client(p0)
    except Exception:
        pass
    # P1 is in-browser. Without it, and without P0, the contract client is the mock.
    return MockSimClient()


class _P0Client:
    label = "p0"

    def __init__(self, module):
        self._module = module

    def one_mode(self, req: dict) -> dict:
        raw = self._module.run_one_mode(req)
        raw = dict(raw)
        raw.setdefault("source", "live-one-mode")
        return raw

    async def two_mode(self, req: dict) -> dict:
        runner = getattr(self._module, "run_two_mode", None)
        if runner is None:
            raise RuntimeError("run_two_mode missing")
        raw = await asyncio.to_thread(runner, req)
        raw = dict(raw)
        raw.setdefault("source", "live-two-mode-16x5")
        return raw


def one_mode_request(level_id: str, params: dict) -> dict | None:
    """Return the CONTRACT one-mode body, or None when the level must echo state (Fock)."""
    params = params or {}
    if level_id == "L1":
        if params.get("init") == "fock" or params.get("state") in {"fock", "Fock"}:
            return None
        return {
            "alpha": 0,
            "kappa2_scale": 0,
            "kappa_a_scale": 0,
            "init": "coherent",
            "init_alpha": float(params.get("alpha", 2.1)),
            "t_end_us": 0.05,
            "n_t": 2,
            "N": 30,
            "outputs": ["n", "parity"],
        }
    if level_id == "L2":
        kappa = float(params.get("kappa", 1.386))
        return {
            "alpha": 0,
            "kappa2_scale": 0,
            "kappa_a_scale": kappa / kappa_a(),
            "init": "coherent",
            "init_alpha": 2,
            "t_end_us": 2,
            "n_t": 21,
            "N": 30,
            "outputs": ["n", "parity"],
        }
    if level_id == "L3":
        return {
            "alpha": 0,
            "kappa2_scale": float(params.get("kappa2_scale", 1)),
            "kappa_a_scale": 0,
            "init": "coherent",
            "init_alpha": float(params.get("alpha", 2)),
            "t_end_us": 2,
            "n_t": 21,
            "N": 30,
            "outputs": ["n", "parity"],
        }
    if level_id == "L4":
        loss = params.get("loss")
        scale = 20.0 if loss in {"x20", "on", True, 20, 20.0} else float(params.get("kappa_a_scale") or 0)
        return {
            "alpha": float(params.get("alpha", 2.1)),
            "kappa2_scale": 1,
            "kappa_a_scale": scale,
            "init": "vacuum",
            "t_end_us": 2,
            "n_t": 41,
            "N": 30,
            "outputs": ["n", "parity"],
        }
    return None


def _at(times: list, values: list, target: float):
    if not values:
        return None
    if not times or len(times) != len(values):
        return values[-1]
    best = min(range(len(times)), key=lambda i: abs(float(times[i]) - target))
    return values[best]


def summarize_one(level_id: str, raw: dict) -> dict:
    source = raw.get("source") or "live-one-mode"
    times = list(raw.get("t_us") or [])
    n = list(raw.get("n") or [])
    parity = list(raw.get("parity") or [])
    out = {"source": source, "record_ids": list(raw.get("record_ids") or [])}
    if level_id == "L1":
        out["n0"] = n[0] if n else None
    elif level_id == "L2":
        out["n_at_0_5us"] = _at(times, n, 0.5)
        out["n_final"] = n[-1] if n else None
        # Halving time of 4 e^{−κt} is ln 2 / κ. Recover κ from the 0.5 µs sample when we can.
        n_half = out["n_at_0_5us"]
        if n_half and n_half > 0:
            kappa = -math.log(n_half / 4.0) / 0.5
            out["t_half"] = math.log(2) / kappa if kappa else None
        else:
            out["t_half"] = None
    elif level_id == "L3":
        out["plateau"] = n[-1] if n else None
        out["parity"] = parity[-1] if parity else None
    elif level_id == "L4":
        out["n_at_1us"] = _at(times, n, 1.0)
        out["parity_at_1us"] = _at(times, parity, 1.0)
        out["parity_final"] = parity[-1] if parity else None
    else:
        out["n_final"] = n[-1] if n else None
    return {key: value for key, value in out.items() if value is not None}


def load_preset(name: str, directory: Path | None = None) -> dict:
    directory = directory or PRESET_DIR
    path = directory / f"{name}.json"
    if not path.is_file():
        return {"preset": name, "available": False, "source": "preset", "record_ids": []}
    payload = json.loads(path.read_text())
    payload = dict(payload)
    payload["preset"] = name
    payload["source"] = "preset"
    payload.setdefault("record_ids", [])
    return payload


def two_mode_request(params: dict) -> dict:
    t_end = float(params.get("t_end_us") or 2)
    return {
        "H": params.get("tree"),
        "jumps": params.get("jumps") or [],
        "params": params.get("expr_params") or {},
        "modes": "two",
        "Na": 16,
        "Nb": 5,
        "n_t": 201,
        "t_end_us": min(3.0, t_end),
        "init": "vacuum",
        "outputs": ["na", "nb", "parity"],
    }


async def run_level(
    level_id: str,
    params: dict,
    *,
    state: dict | None = None,
    remaining_s: float = 10.0,
    client=None,
    preset_dir: Path | None = None,
    two_mode_timeout_s: float | None = None,
) -> dict:
    client = client or get_client()
    params = dict(params or {})
    state = state or {}
    spec_mode = {
        "L5": "redirect",
        "L7": "redirect",
        "L6": "two_or_preset",
        "L8": "linresp",
    }.get(level_id, "one")

    if spec_mode == "redirect":
        grid = "gamma_x_vs_alpha2" if level_id == "L5" else "readout_signals"
        return {"error": "use_lookup_grid", "grid": grid, "source": "grid", "record_ids": []}

    if level_id == "L8":
        return _linresp(params)

    if level_id == "L6":
        return await _run_l6(
            params,
            remaining_s=remaining_s,
            client=client,
            preset_dir=preset_dir,
            timeout_s=TWO_MODE_TIMEOUT_S if two_mode_timeout_s is None else two_mode_timeout_s,
        )

    request = one_mode_request(level_id, params)
    if request is None:
        summary = ((state.get("last_sim") or {}).get("summary")) or ""
        return {"summary": summary, "source": "state", "record_ids": []}
    raw = client.one_mode(request)
    if not isinstance(raw, dict):
        raw = {"source": "live-one-mode"}
    summary = summarize_one(level_id, raw)
    summary["request_alpha"] = request.get("alpha")
    summary["request_init"] = request.get("init")
    summary["request_kappa_a_scale"] = request.get("kappa_a_scale")
    return summary


def _linresp(params: dict) -> dict:
    pulse = params.get("pulse")
    try:
        import src.linresp as linresp  # type: ignore
    except Exception:
        return {"pass": None, "message": "use ▶ Score", "source": "state", "record_ids": []}
    if not pulse:
        return {"message": "use ▶ Score", "source": "state", "record_ids": []}
    try:
        score = linresp.score_pulse(pulse)  # optional helper; absent on this branch
    except Exception:
        score = None
    return {"snr": score, "source": "state", "record_ids": [], "message": "use ▶ Score" if score is None else ""}


async def _run_l6(params, *, remaining_s, client, preset_dir, timeout_s: float) -> dict:
    build = params.get("build")
    if build in PRESET_NAMES:
        preset = load_preset(build, preset_dir)
        preset["source"] = "preset"
        return preset
    if not params.get("tree"):
        preset = load_preset("correct", preset_dir)
        preset["source"] = "preset"
        preset["note"] = "no build and no tree"
        return preset
    if remaining_s < TWO_MODE_MIN_REMAINING_S:
        preset = load_preset("correct", preset_dir)
        preset["source"] = "preset"
        preset["skipped"] = "two-mode"
        return preset
    request = two_mode_request(params)
    try:
        async with _TWO_MODE:
            raw = await asyncio.wait_for(client.two_mode(request), timeout=min(timeout_s, remaining_s))
    except (asyncio.TimeoutError, TimeoutError):
        preset = load_preset("correct", preset_dir)
        preset["source"] = "preset"
        preset["timed_out"] = True
        return preset
    raw = dict(raw or {})
    na = list(raw.get("na") or [])
    steady = sum(na[-5:]) / len(na[-5:]) if na else None
    return {
        "source": raw.get("source") or "live-two-mode-16x5",
        "steady_na": steady if steady is not None else raw.get("steady_na"),
        "Na": request["Na"],
        "Nb": request["Nb"],
        "record_ids": list(raw.get("record_ids") or []),
    }
