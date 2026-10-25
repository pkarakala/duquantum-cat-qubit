"""Five tutor tools. Gemini declares them; the server is the only thing that runs them."""

from __future__ import annotations

import math
from pathlib import Path

from server.app.tutor import grids, records, simbridge

DECLARATIONS = [
    {
        "name": "run_sim",
        "description": "Run the level simulator, or the precomputed stand-in, and return a short summary.",
        "parameters": {
            "type": "object",
            "properties": {
                "level_id": {"type": "string", "enum": [f"L{i}" for i in range(1, 9)]},
                "params": {
                    "type": "object",
                    "properties": {
                        "alpha": {"type": "number"},
                        "kappa": {"type": "number"},
                        "kappa2_scale": {"type": "number"},
                        "kappa_a_scale": {"type": "number"},
                        "n": {"type": "number"},
                        "alpha2": {"type": "number"},
                        "eps_z_over_g2": {"type": "number"},
                        "valley": {"type": "number"},
                        "loss": {"type": "string"},
                        "build": {"type": "string"},
                        "init": {"type": "string"},
                        "state": {"type": "string"},
                        "tree": {"type": "object"},
                        "pulse": {"type": "array", "items": {"type": "number"}, "minItems": 20, "maxItems": 20},
                    },
                },
            },
            "required": ["level_id"],
        },
    },
    {
        "name": "get_level_state",
        "description": "Return the learner's current controls, prediction and last simulation summary.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_record",
        "description": "Read one verified results/records JSON by id.",
        "parameters": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "lookup_grid",
        "description": "Look up a precomputed curve: rates, readout, level-6 builds or pulses.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": list(grids.GRID_NAMES)},
                "params": {"type": "object"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "check",
        "description": "Run the level's pass check. A failure is remembered for the hint ladder.",
        "parameters": {
            "type": "object",
            "properties": {
                "level_id": {"type": "string"},
                "answer": {},
            },
            "required": ["level_id"],
        },
    },
]

assert [item["name"] for item in DECLARATIONS] == [
    "run_sim",
    "get_level_state",
    "get_record",
    "lookup_grid",
    "check",
]


def _answer_number(answer, *keys):
    if isinstance(answer, (int, float)) and not isinstance(answer, bool):
        return float(answer)
    if isinstance(answer, dict):
        for key in keys:
            value = answer.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return None


def _log_interp(xs, ys, x):
    """Log-linear interpolation. No extrapolation."""
    pairs = sorted((float(a), float(b)) for a, b in zip(xs, ys) if b > 0)
    if len(pairs) < 2 or x < pairs[0][0] or x > pairs[-1][0]:
        return None
    for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            t = (x - x0) / (x1 - x0)
            return math.exp(math.log(y0) + t * (math.log(y1) - math.log(y0)))
    return None


def evaluate_check(level_id: str, answer, state: dict, grid: dict | None = None) -> dict:
    params = dict((state or {}).get("params") or {})
    if answer is None:
        answer = params
    if level_id == "L1":
        alpha = _answer_number(answer, "alpha", "abs_alpha")
        if alpha is None:
            alpha = _answer_number(params, "alpha")
        passed = alpha is not None and 2.08 <= abs(alpha) <= 2.12
        return {"pass": passed, "message": "α is in range" if passed else "α is outside [2.08, 2.12]"}
    if level_id == "L2":
        kappa = _answer_number(answer, "kappa")
        if kappa is None:
            kappa = _answer_number(params, "kappa")
        passed = kappa is not None and 1.32 <= kappa <= 1.46
        return {"pass": bool(passed), "message": "κ halves ⟨n⟩ near 0.5 µs" if passed else "κ is outside [1.32, 1.46]"}
    if level_id == "L3":
        plateau = _answer_number(answer, "plateau", "n_final", "n")
        passed = plateau is not None and 0.43 <= plateau <= 0.47
        return {"pass": bool(passed), "message": "plateau is in range" if passed else "plateau is outside [0.43, 0.47]"}
    if level_id == "L4":
        n = _answer_number(answer, "n", "n_at_1us")
        parity = _answer_number(answer, "parity", "parity_at_1us")
        passed = n is not None and parity is not None and 4.3 <= n <= 4.5 and parity > 0.9
        return {"pass": bool(passed), "message": "cat check" if passed else "need ⟨n⟩ in [4.3, 4.5] and parity > 0.9"}
    if level_id == "L5":
        alpha2 = _answer_number(answer, "alpha2")
        if alpha2 is None:
            alpha2 = _answer_number(params, "alpha2")
        if alpha2 is None or not (alpha2 < 8.56):
            return {"pass": False, "message": "need α² < 8.56"}
        gamma = None
        if grid and grid.get("xs") and grid.get("ys"):
            gamma = _log_interp(grid["xs"], grid["ys"], alpha2)
        if gamma is None:
            return {"pass": False, "message": "no verified data here"}
        t_x = 1.0 / gamma
        passed = t_x > 1000.0
        return {"pass": passed, "message": "T_X and T_Z" if passed else "T_X is under 1 ms"}
    if level_id == "L6":
        steady = _answer_number(answer, "steady_na", "n", "na")
        passed = steady is not None and abs(steady / 4.41 - 1) <= 0.02
        return {"pass": bool(passed), "message": "steady ⟨n_a⟩" if passed else "steady ⟨n_a⟩ is not within 2% of 4.41"}
    if level_id == "L7":
        snr = _answer_number(answer, "snr")
        if snr is None and grid:
            snr = _answer_number(grid, "snr")
        passed = snr is not None and snr >= 1
        return {"pass": bool(passed), "message": "SNR" if passed else "SNR is under 1"}
    if level_id == "L8":
        try:
            import src.linresp  # noqa: F401
        except Exception:
            return {"pass": None, "message": "use ▶ Score"}
        return {"pass": None, "message": "use ▶ Score"}
    return {"pass": False, "message": "unknown level"}


class ToolSession:
    def __init__(
        self,
        *,
        level_id: str,
        state: dict,
        learner_id: str,
        store,
        levels: dict,
        remaining_s: float = 10.0,
        client=None,
        records_dir: Path | None = None,
        precomputed_dir: Path | None = None,
        preset_dir: Path | None = None,
    ):
        self.level_id = level_id
        self.state = state
        self.learner_id = learner_id
        self.store = store
        self.levels = levels
        self.remaining_s = remaining_s
        self.client = client
        self.records_dir = records_dir
        self.precomputed_dir = precomputed_dir
        self.preset_dir = preset_dir
        self.calls = 0

    async def dispatch(self, name: str, args: dict | None) -> dict:
        self.calls += 1
        if self.calls > 3:
            return {"error": "tool_budget_exhausted: answer now"}
        args = dict(args or {})
        if name == "get_level_state":
            return {"source": "state", "state": self.state}
        if name == "get_record":
            return records.get_record(args.get("id") or "", self.records_dir)
        if name == "lookup_grid":
            return grids.lookup_grid(
                args.get("name") or "",
                args.get("params") or {},
                records_dir=self.records_dir,
                precomputed_dir=self.precomputed_dir,
            )
        if name == "check":
            return self._check(args)
        if name == "run_sim":
            return await self._run_sim(args)
        return {"error": "unknown_tool"}

    def _reject_params(self, params: dict) -> dict | None:
        controls = (self.levels["levels"][self.level_id].get("controls") or {})
        for key, value in params.items():
            if key not in controls or not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            lo, hi = controls[key]
            if value < lo or value > hi:
                return {"error": "param_out_of_range", "param": key}
        pulse = params.get("pulse")
        if pulse is not None and (not isinstance(pulse, list) or len(pulse) != 20):
            return {"error": "param_out_of_range", "param": "pulse"}
        return None

    async def _run_sim(self, args: dict) -> dict:
        level_id = args.get("level_id")
        if level_id != self.level_id:
            return {"error": "level_mismatch"}
        params = dict(args.get("params") or {})
        bad = self._reject_params(params)
        if bad:
            return bad
        result = await simbridge.run_level(
            level_id,
            params,
            state=self.state,
            remaining_s=self.remaining_s,
            client=self.client,
            preset_dir=self.preset_dir,
        )
        return result

    def _check(self, args: dict) -> dict:
        level_id = args.get("level_id") or self.level_id
        if level_id != self.level_id:
            return {"error": "level_mismatch"}
        answer = args.get("answer")
        if answer is None:
            answer = (self.state or {}).get("params")
        result = evaluate_check(level_id, answer, self.state)
        if result.get("pass") is False and self.store is not None and self.learner_id:
            self.store.increment_failed(self.learner_id, level_id)
            result["failed_checks"] = self.store.failed_count(self.learner_id, level_id)
        return result
