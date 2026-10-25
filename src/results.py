"""Write every reported number to results/ so README claims are checkable.

`save` is the original flat-JSON API of the intro tasks. `record` writes one validated
duq.record/v2 file per reported number (CONTRACT §6), with provenance filled in automatically.
"""
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np

from src import config as C
from src.provenance import provenance

RES_DIR = Path(__file__).resolve().parent.parent / "results"

SCHEMA = "duq.record/v2"
ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$")
_CONVERGENCE_KEYS = ("key", "rel_tol", "sweeps", "needed", "converged")
_CROSS_CHECK_KEYS = ("method", "rel_diff", "tol", "agree")


def save(name, data):
    RES_DIR.mkdir(exist_ok=True)
    path = RES_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print("saved", path)
    return path


def std_params(alpha=C.ALPHA, n_th=0.0, eps_z=0.0, eps_x=0.0, **extra) -> dict:
    """Nominal parameters in lab units (rounded so 2*pi round-off never shows up in a record)."""
    return {
        "g2_MHz": round(C.G2 / C.TWO_PI, 9),
        "kappa_b_MHz": round(C.KAPPA_B / C.TWO_PI, 9),
        "kappa_a_kHz": round(C.KAPPA_A / C.TWO_PI * 1e3, 9),
        "alpha": float(alpha),
        "n_th": float(n_th),
        "eps_z_over_g2": float(eps_z / C.G2),
        "eps_x_over_g2": float(eps_x / C.G2),
        **extra,
    }


def _check_id(id):
    if not isinstance(id, str) or not ID_RE.fullmatch(id):
        raise ValueError(f"bad record id {id!r}: must match {ID_RE.pattern}")


def _finite_real(x, name):
    """A real finite scalar as float; rejects bool, complex, strings, arrays, NaN and inf."""
    arr = None if isinstance(x, (str, bytes)) else np.asarray(x)
    if arr is None or arr.ndim != 0 or arr.dtype.kind not in "iuf" or not np.isfinite(arr):
        raise ValueError(f"{name} must be a finite real scalar, got {x!r}")
    return float(arr)


def _is_absolute(path):
    return (PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute()
            or path.startswith(("\\", "~")) or re.match(r"^[A-Za-z]:", path) is not None)


def _jsonable(x):
    """Recursively convert numpy / jax scalars and arrays (and Paths) to plain JSON types."""
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if x is None or isinstance(x, (str, bool, int, float)):
        return x
    if isinstance(x, Path):
        return x.as_posix()
    if isinstance(x, np.generic):
        return x.item()
    if hasattr(x, "tolist"):
        return _jsonable(x.tolist())
    return x   # json.dumps rejects anything left


def _check_cross_check(cross_check):
    if not isinstance(cross_check, (list, tuple)):
        raise ValueError("cross_check must be a list of dicts")
    for i, c in enumerate(cross_check):
        if not isinstance(c, dict) or any(k not in c for k in _CROSS_CHECK_KEYS):
            raise ValueError(f"cross_check[{i}] needs keys {_CROSS_CHECK_KEYS} (the tolerance must be stated)")
        rel_diff = _finite_real(c["rel_diff"], f"cross_check[{i}].rel_diff")
        tol = _finite_real(c["tol"], f"cross_check[{i}].tol")
        if not isinstance(c["agree"], (bool, np.bool_)) or bool(c["agree"]) != (rel_diff <= tol):
            raise ValueError(f"cross_check[{i}].agree must be the bool rel_diff <= tol "
                             f"({rel_diff} <= {tol}), got {c['agree']!r}")


def record(id, *, task, quantity, value, units, method, params, script,
           truncation=None, uncertainty=None, convergence=None, numerics=None,
           cross_check=None, artifacts=None, wall_s=None, notes=None, quick=False) -> Path:
    """Validate and write results/records/<id>.json (results/quick/records/ if quick).

    Fills 'schema' and 'provenance' automatically; absent optional fields are written as null.
    Raises ValueError on a bad id, a non-finite value or a missing / malformed field.
    """
    _check_id(id)
    for name, s in (("task", task), ("quantity", quantity), ("units", units),
                    ("method", method), ("script", script)):
        if not isinstance(s, str) or not s.strip():
            raise ValueError(f"{name} must be a non-empty string, got {s!r}")
    if _is_absolute(script):
        raise ValueError(f"script must be repo-relative (absolute paths leak user names), got {script!r}")
    if not isinstance(params, dict):
        raise ValueError("params must be a dict (use std_params(...))")
    value = _finite_real(value, "value")
    if uncertainty is not None:
        uncertainty = _finite_real(uncertainty, "uncertainty")
    for name, d in (("truncation", truncation), ("numerics", numerics), ("artifacts", artifacts)):
        if d is not None and not isinstance(d, dict):
            raise ValueError(f"{name} must be a dict or None")
    if convergence is not None and (not isinstance(convergence, dict)
                                    or any(k not in convergence for k in _CONVERGENCE_KEYS)):
        raise ValueError(f"convergence must be a dict with keys {_CONVERGENCE_KEYS} (or None)")
    if cross_check is not None:
        _check_cross_check(cross_check)
    if notes is not None and not isinstance(notes, str):
        raise ValueError("notes must be a string or None")

    script = script.replace("\\", "/")
    rec = {
        "schema": SCHEMA, "id": id, "task": task, "quantity": quantity,
        "value": value, "uncertainty": uncertainty, "units": units, "method": method,
        "params": params, "truncation": truncation, "convergence": convergence,
        "numerics": numerics, "cross_check": cross_check, "artifacts": artifacts,
        "notes": notes, "provenance": provenance(script, wall_s),
    }
    try:
        text = json.dumps(_jsonable(rec), indent=2, allow_nan=False)
    except (TypeError, ValueError) as e:
        raise ValueError(f"record {id} is not strict JSON: {e}") from e

    out = RES_DIR / "quick" / "records" if quick else RES_DIR / "records"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{id}.json"
    path.write_text(text + "\n")
    print("saved", path)
    return path


def save_arrays(id, quick=False, **arrays) -> Path:
    """np.savez_compressed to results/arrays/<id>.npz (results/quick/arrays/ if quick)."""
    _check_id(id)
    out = RES_DIR / "quick" / "arrays" if quick else RES_DIR / "arrays"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{id}.npz"
    np.savez_compressed(path, **{k: np.asarray(v) for k, v in arrays.items()})
    print("saved", path)
    return path


def load_record(id) -> dict:
    _check_id(id)
    return json.loads((RES_DIR / "records" / f"{id}.json").read_text())
