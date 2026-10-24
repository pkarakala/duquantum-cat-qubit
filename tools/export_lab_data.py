"""Export results/ into the Lab live JSON bundle (CONTRACT §13).

Stdlib + numpy only. Never import src.* (that would pull dynamiqs into the Lab build).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import numpy as np

# l4b t2_4b.grid.npz columns (brief 09 §7 / 11 §4). Dotted keys stay in this dict.
L4B_KEYS = {
    "alpha": "alpha",
    "eps_over_g2": "eps_over_g2",
    "gamma_x": "gamma_x",
    "gamma_x_rel": "gamma_x_rel",
    "gamma_x_ok": "gamma_x_ok",
    "snr_T1us": "snr_T1.0",
    "gamma_z_re": "gamma_z_re",
    "leakage": "leakage",
}

# l4c array files (brief 10 §7 / 11 §4).
L4C_KEYS = {
    "pulses": "t2_4c.pulses.npz",
    "frontier": "t2_4c.frontier.npz",
}

NAMES = ("records", "inflation", "errors", "readout", "verify")
TWO_PI = 2.0 * math.pi


def tokens(rid: str) -> tuple[str, str, str, str]:
    parts = rid.split(".")
    parts += [""] * (4 - len(parts))
    return parts[0], parts[1], parts[2], parts[3]


def param(rec: dict, key: str, default: Any = None) -> Any:
    return (rec.get("params") or {}).get(key, default)


def n_th_of(rec: dict) -> float:
    v = param(rec, "n_th", 0.0)
    try:
        return float(v or 0.0)
    except (TypeError, ValueError):
        return 0.0


def alpha_of(rec: dict) -> float | None:
    v = param(rec, "alpha")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def rel_close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-12)


def sig6(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (list, tuple)):
        return [sig6(v) for v in x]
    if isinstance(x, np.ndarray):
        return sig6(x.tolist())
    if isinstance(x, (np.floating, float)):
        v = float(x)
        if not math.isfinite(v):
            raise ValueError(f"non-finite float {v}")
        if v == 0.0:
            return 0.0
        return float(f"{v:.6g}")
    if isinstance(x, (np.integer, int)):
        return int(x)
    return x


def fixneg0(v: float) -> float:
    return 0.0 if v == 0.0 else v


def load_records(results: str | Path = "results") -> list[dict]:
    root = Path(results)
    index = root / "index.json"
    recs: list[dict] = []
    if index.is_file():
        data = json.loads(index.read_text())
        recs = list(data.get("records") or [])
    else:
        recdir = root / "records"
        if recdir.is_dir():
            for p in sorted(recdir.glob("*.json")):
                recs.append(json.loads(p.read_text()))
    recs.sort(key=lambda r: str(r.get("id", "")))
    return recs


def downsample(frames: np.ndarray, x: np.ndarray, y: np.ndarray, max_px: int = 81) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x)
    y = np.asarray(y)
    frames = np.asarray(frames)
    sx = max(1, math.ceil(x.size / max_px))
    sy = max(1, math.ceil(y.size / max_px))
    return frames[:, ::sy, ::sx], x[::sx], y[::sy]


def constants_from(records: list[dict]) -> tuple[float, float, float, float]:
    for r in records:
        p = r.get("params") or {}
        if "g2_MHz" in p:
            g2 = TWO_PI * float(p["g2_MHz"])
            kb = TWO_PI * float(p.get("kappa_b_MHz", 2.6))
            ka = TWO_PI * float(p.get("kappa_a_kHz", 9.3)) * 1e-3
            k2 = 4.0 * g2 * g2 / kb
            return g2, kb, ka, k2
    g2 = TWO_PI * 0.763
    kb = TWO_PI * 2.6
    ka = TWO_PI * 9.3e-3
    return g2, kb, ka, 4.0 * g2 * g2 / kb


def build_inflation(records: list[dict], arrays_dir: str | Path) -> dict | None:
    path = Path(arrays_dir) / "lab.inflation_wigner.npz"
    if not path.is_file():
        return None
    z = np.load(path)
    t_us = np.asarray(z["t_us"], dtype=float)
    na = np.asarray(z["na"], dtype=float)
    nb = np.asarray(z["nb"], dtype=float)
    top2_a = np.asarray(z["top2_a"], dtype=float)
    top_b = np.asarray(z["top_b"], dtype=float)
    eff_t = np.asarray(z["eff_t_us"], dtype=float)
    eff_na = np.asarray(z["eff_na"], dtype=float)
    x = np.asarray(z["x"], dtype=float)
    y = np.asarray(z["y"], dtype=float)
    frames = np.asarray(z["frames"], dtype=float)
    frame_t = np.asarray(z["frame_t_us"], dtype=float)
    frames, x, y = downsample(frames, x, y, 81)
    w_frames = []
    for k, tf in enumerate(frame_t):
        w = np.round(frames[k], 4)
        w = np.where(w == 0.0, 0.0, w)
        w_frames.append({"t_us": sig6(float(tf)), "w": [[fixneg0(float(v)) for v in row] for row in w]})
    rec_ids = sorted(r["id"] for r in records if tokens(r.get("id", ""))[0] == "t1_1")
    return {
        "t_us": sig6(t_us.tolist()),
        "na": sig6(na.tolist()),
        "nb": sig6(nb.tolist()),
        "top2_a": sig6(top2_a.tolist()),
        "top_b": sig6(top_b.tolist()),
        "effective": {"t_us": sig6(eff_t.tolist()), "na": sig6(eff_na.tolist())},
        "wigner": {"x": sig6(x.tolist()), "y": sig6(y.tolist()), "frames": w_frames},
        "record_ids": rec_ids,
    }


def _rate_point(rec: dict) -> dict | None:
    a = alpha_of(rec)
    if a is None:
        return None
    unc = rec.get("uncertainty", None)
    if unc is not None:
        try:
            unc = float(unc)
        except (TypeError, ValueError):
            unc = None
    return {"alpha2": sig6(a * a), "value": sig6(float(rec["value"])), "unc": sig6(unc) if unc is not None else None, "id": rec["id"]}


def _select(records: list[dict], task: str, quantity: str, method: str | None = None, model: str | None = None) -> list[dict]:
    out = []
    for r in records:
        t, q, m, mdl = tokens(r.get("id", ""))
        if t == task and q == quantity and (method is None or m == method) and (model is None or mdl == model):
            out.append(r)
    return out


def _local_slope(one: list[dict], two: list[dict]) -> dict:
    series = {"one_mode": one, "two_mode": two}
    mids: dict[float, dict[str, float]] = {}
    for name, pts in series.items():
        ordered = sorted((p for p in pts if p["value"] not in (None, 0)), key=lambda p: p["alpha2"])
        for i in range(len(ordered) - 1):
            x0, y0 = float(ordered[i]["alpha2"]), float(ordered[i]["value"])
            x1, y1 = float(ordered[i + 1]["alpha2"]), float(ordered[i + 1]["value"])
            if y0 <= 0 or y1 <= 0 or x1 == x0:
                continue
            mid = sig6(0.5 * (x0 + x1))
            mids.setdefault(mid, {})[name] = sig6(-(math.log(y1) - math.log(y0)) / (x1 - x0))
    alpha2 = sorted(mids)
    return {
        "alpha2": alpha2,
        "one_mode": [mids[a].get("one_mode") for a in alpha2],
        "two_mode": [mids[a].get("two_mode") for a in alpha2],
        "source": "finite_difference",
    }


def _closed_form_analytic(records: list[dict]) -> dict:
    _g2, _kb, ka, k2 = constants_from(records)
    a2 = np.linspace(0.5, 9.0, 200)
    # RESEARCH §5: ch1 = κ_a α² (coth 2α² − 1), ch2 = (κ_a²/κ₂) e^{−2α²}.
    ch1 = ka * a2 * (1.0 / np.tanh(2.0 * a2) - 1.0)
    ch2 = (ka * ka / k2) * np.exp(-2.0 * a2)
    return {
        "alpha2": sig6(a2.tolist()),
        "ch1": sig6(ch1.tolist()),
        "ch2": sig6(ch2.tolist()),
        "total": sig6((ch1 + ch2).tolist()),
        "source": "exporter_closed_form_RESEARCH_5",
    }


def _analytic_from_npz(arrays_dir: Path) -> dict | None:
    hits = sorted(arrays_dir.glob("t2_1.*channel*.npz"))
    if not hits:
        return None
    z = np.load(hits[0])
    needed = ("alpha2", "ch1", "ch2", "total")
    if not all(k in z for k in needed):
        return None
    return {k: sig6(np.asarray(z[k], dtype=float).tolist()) for k in needed}


def build_errors(records: list[dict], arrays_dir: str | Path) -> dict | None:
    t21 = [r for r in records if tokens(r.get("id", ""))[0] == "t2_1"]
    t22 = [r for r in records if tokens(r.get("id", ""))[0] == "t2_2"]
    if not t21 and not t22:
        return None
    arrays = Path(arrays_dir)

    eig = _select(t21, "t2_1", "gamma_x", "eig")
    one_mode = [_rate_point(r) for r in eig if tokens(r["id"])[3] == "one_mode" and n_th_of(r) == 0.0]
    two_mode = [_rate_point(r) for r in eig if tokens(r["id"])[3] == "two_mode" and n_th_of(r) == 0.0]
    td = []
    for r in _select(t21, "t2_1", "gamma_x", "td"):
        p = _rate_point(r)
        if p:
            p = {**p, "model": tokens(r["id"])[3]}
            td.append(p)
    one_mode = [p for p in one_mode if p]
    two_mode = [p for p in two_mode if p]
    td = [p for p in td if p]

    thermal_recs = [r for r in eig if n_th_of(r) > 0.0]
    th_model = "two_mode" if any(tokens(r["id"])[3] == "two_mode" for r in thermal_recs) else "one_mode"
    thermal: dict[str, list] = {}
    for r in thermal_recs:
        if tokens(r["id"])[3] != th_model:
            continue
        key = format(n_th_of(r), "g")
        p = _rate_point(r)
        if p:
            thermal.setdefault(key, []).append(p)

    analytic = _analytic_from_npz(arrays) or _closed_form_analytic(records)

    slope_recs = _select(t21, "t2_1", "gamma_local_slope")
    if slope_recs:
        sl_one = [_rate_point(r) for r in slope_recs if tokens(r["id"])[3] == "one_mode"]
        sl_two = [_rate_point(r) for r in slope_recs if tokens(r["id"])[3] == "two_mode"]
        local_slope = _local_slope([p for p in sl_one if p], [p for p in sl_two if p])
        local_slope["source"] = "records"
    else:
        local_slope = _local_slope(one_mode, two_mode)

    gz_td, gz_eig, pred_a2, pred_v = [], [], [], []
    for r in _select(t22, "t2_2", "gamma_z", "td", "two_mode"):
        if n_th_of(r) != 0.0:
            continue
        p = _rate_point(r)
        if not p:
            continue
        gz_td.append(p)
        val = None
        for xc in r.get("cross_check") or []:
            if xc.get("method") == "analytic_coth" and xc.get("value") is not None:
                val = float(xc["value"])
                break
        pred_a2.append(p["alpha2"])
        pred_v.append(sig6(val) if val is not None else p["value"])
    for r in _select(t22, "t2_2", "gamma_z", "eig", "two_mode"):
        p = _rate_point(r)
        if p:
            gz_eig.append(p)

    return {
        "gamma_x": {
            "one_mode": one_mode,
            "two_mode": two_mode,
            "td": td,
            "analytic": analytic,
            "thermal": thermal,
            "thermal_model": th_model,
            "local_slope": local_slope,
        },
        "gamma_z": {"td": gz_td, "eig": gz_eig, "pred": {"alpha2": pred_a2, "value": pred_v}},
    }


def _stride(n: int, max_n: int) -> slice:
    if n <= max_n:
        return slice(None)
    return slice(None, None, max(1, math.ceil(n / max_n)))


def _signals_dict(t: np.ndarray, bp: np.ndarray, bm: np.ndarray, eps: float | None = None) -> dict:
    sl = _stride(t.size, 400)
    t, bp, bm = t[sl], bp[sl], bm[sl]
    out = {
        "t_us": sig6(t.real.astype(float).tolist()),
        "b_plus_re": sig6(np.real(bp).astype(float).tolist()),
        "b_plus_im": sig6(np.imag(bp).astype(float).tolist()),
        "b_minus_re": sig6(np.real(bm).astype(float).tolist()),
        "b_minus_im": sig6(np.imag(bm).astype(float).tolist()),
    }
    if eps is not None:
        out["eps_over_g2"] = sig6(float(eps))
    return out


def _match_t24b(records: list[dict], alpha: float, eps: float) -> str | None:
    for r in records:
        t, q, _m, _mdl = tokens(r.get("id", ""))
        if t != "t2_4b" or q != "gamma_x":
            continue
        ra = alpha_of(r)
        re = param(r, "eps_z_over_g2")
        try:
            re = float(re)
        except (TypeError, ValueError):
            continue
        if ra is not None and rel_close(ra, alpha) and rel_close(re, eps):
            return r["id"]
    return None


def _tradeoff_from_npz(path: Path, records: list[dict]) -> list[dict]:
    z = np.load(path)
    n = len(z[L4B_KEYS["alpha"]])
    gx = np.asarray(z[L4B_KEYS["gamma_x"]], dtype=float)
    alpha = np.asarray(z[L4B_KEYS["alpha"]], dtype=float)
    eps = np.asarray(z[L4B_KEYS["eps_over_g2"]], dtype=float)
    snr = np.asarray(z[L4B_KEYS["snr_T1us"]], dtype=float)
    rel_key = L4B_KEYS["gamma_x_rel"]
    if rel_key in z.files:
        rel = np.asarray(z[rel_key], dtype=float)
    else:
        rel = np.full(n, np.nan)
        for a in np.unique(alpha):
            mask = alpha == a
            zero = np.where(mask & (np.abs(eps) <= 1e-12))[0]
            g0 = float(gx[zero[0]]) if len(zero) else float(gx[mask][0])
            if g0 != 0:
                rel[mask] = gx[mask] / g0
    ok = np.ones(n, dtype=bool)
    if L4B_KEYS["gamma_x_ok"] in z.files:
        ok = np.asarray(z[L4B_KEYS["gamma_x_ok"]]).astype(bool)
    rows = []
    for i in range(n):
        if not math.isfinite(float(rel[i])) or not math.isfinite(float(snr[i])):
            continue
        rows.append(
            {
                "eps_over_g2": sig6(float(eps[i])),
                "snr_T1us": sig6(float(snr[i])),
                "gamma_x_rel": sig6(float(rel[i])),
                "id": _match_t24b(records, float(alpha[i]), float(eps[i])),
                "alpha": sig6(float(alpha[i])),
                "ok": bool(ok[i]),
            }
        )
    return rows


def _tradeoff_from_records(records: list[dict]) -> list[dict]:
    rows = []
    gx = [r for r in records if tokens(r.get("id", ""))[0] == "t2_4b" and tokens(r.get("id", ""))[1] == "gamma_x"]
    by_alpha: dict[float, list[dict]] = {}
    for r in gx:
        a = alpha_of(r)
        if a is None:
            continue
        by_alpha.setdefault(a, []).append(r)
    for a, recs in by_alpha.items():
        g0 = None
        for r in recs:
            e = param(r, "eps_z_over_g2", None)
            try:
                e = float(e)
            except (TypeError, ValueError):
                continue
            if abs(e) <= 1e-12:
                g0 = float(r["value"])
                break
        if g0 in (None, 0):
            g0 = float(recs[0]["value"]) if recs else 1.0
        for r in recs:
            e = param(r, "eps_z_over_g2", None)
            try:
                e = float(e)
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "eps_over_g2": sig6(e),
                    "snr_T1us": sig6(float((r.get("numerics") or {}).get("snr_T1us") or 0.0)),
                    "gamma_x_rel": sig6(float(r["value"]) / g0 if g0 else 1.0),
                    "id": r["id"],
                    "alpha": sig6(a),
                    "ok": True,
                }
            )
    return rows


def _pulses_from_arrays(arrays: Path, records: list[dict]) -> dict:
    pulses: dict[str, dict] = {}
    ppath = arrays / L4C_KEYS["pulses"]
    if not ppath.is_file():
        return pulses
    z = np.load(ppath, allow_pickle=True)
    names: list[str] = []
    if "names" in z.files:
        names = [str(x) for x in z["names"]]
    else:
        stems = {k.rsplit("_", 1)[0] for k in z.files if "_" in k}
        names = sorted(stems)
    for name in names:
        edges = None
        vals = None
        for ek, vk in ((f"{name}_t_us", f"{name}_eps"), (f"{name}_edges", f"{name}_values"), (f"{name}_t", f"{name}_eps")):
            if ek in z.files and vk in z.files:
                edges, vals = np.asarray(z[ek], dtype=float), np.asarray(z[vk], dtype=float)
                break
        if edges is None and "t_us" in z.files and name in names and "eps" in z.files:
            idx = names.index(name)
            raw_t, raw_e = z["t_us"], z["eps"]
            if np.asarray(raw_t).ndim == 2:
                edges, vals = np.asarray(raw_t[idx], dtype=float), np.asarray(raw_e[idx], dtype=float)
        if edges is None or vals is None:
            continue
        snr_id = next(
            (
                r["id"]
                for r in records
                if r["id"].startswith("t2_4c.snr.td.two_mode.")
                and f".p{name}." in r["id"]
                and (r["id"].endswith("T1.0us") or r["id"].endswith("t1.0us"))
            ),
            None,
        )
        if snr_id is None:
            snr_id = next((r["id"] for r in records if r["id"].startswith("t2_4c.snr.linresp.") and f".p{name}." in r["id"]), None)
        cost_id = next((r["id"] for r in records if r["id"].startswith("t2_4c.cost.") and f".p{name}" in r["id"]), None)
        snr_rec = next((r for r in records if r["id"] == snr_id), None)
        cost_rec = next((r for r in records if r["id"] == cost_id), None)
        pulses[name] = {
            "t_us": sig6(edges.tolist()),
            "eps": sig6(vals.tolist()),
            "snr": sig6(float(snr_rec["value"])) if snr_rec else 0.0,
            "cost": sig6(float(cost_rec["value"])) if cost_rec else 0.0,
            "id": snr_id,
            "cost_id": cost_id,
            "snr_method": "td" if snr_id and ".snr.td." in snr_id else "linresp",
        }
    return pulses


def build_readout(records: list[dict], arrays_dir: str | Path) -> dict | None:
    t23 = [r for r in records if tokens(r.get("id", ""))[0] == "t2_3"]
    if not t23:
        return None
    arrays = Path(arrays_dir)
    lin_rec = next((r for r in t23 if r.get("id") == "t2_3.ring_freq.linresp.two_mode.a2.10"), None)
    if lin_rec is None:
        lin_rec = next((r for r in t23 if tokens(r["id"])[1:3] == ("ring_freq", "linresp")), t23[0])
    num = lin_rec.get("numerics") or {}
    linresp = {
        "freq_MHz": sig6(float(num.get("freq_MHz", lin_rec.get("value", 0.0)))),
        "Q": sig6(float(num.get("Q", 0.0))),
        "t5": sig6(float(num.get("t_settle_5pct_us", 0.0))),
        "t1": sig6(float(num.get("t_settle_1pct_us", 0.0))),
        "id": lin_rec.get("id"),
    }
    alpha = alpha_of(lin_rec) or 2.1
    signals = {"t_us": [], "b_plus_re": [], "b_plus_im": [], "b_minus_re": [], "b_minus_im": []}
    by_eps: list[dict] = []
    sig_path = arrays / "t2_3.ring_freq.td.two_mode.a2.10.npz"
    if sig_path.is_file():
        z = np.load(sig_path)
        t = np.asarray(z["t_us"], dtype=float)
        eps = np.asarray(z["eps_over_g2"], dtype=float)
        bp = np.asarray(z["b_plus"])
        bm = np.asarray(z["b_minus"])
        for i, e in enumerate(eps):
            by_eps.append(_signals_dict(t, bp[i], bm[i], float(e)))
        if by_eps:
            nearest = min(range(len(by_eps)), key=lambda i: abs(by_eps[i]["eps_over_g2"] - 1.0))
            signals = {k: by_eps[nearest][k] for k in ("t_us", "b_plus_re", "b_plus_im", "b_minus_re", "b_minus_im")}
            signals["eps_over_g2"] = by_eps[nearest]["eps_over_g2"]

    grid_path = arrays / "t2_4b.grid.npz"
    tradeoff = _tradeoff_from_npz(grid_path, records) if grid_path.is_file() else _tradeoff_from_records(records)
    pulses = _pulses_from_arrays(arrays, records)
    return {
        "alpha": sig6(float(alpha)),
        "linresp": linresp,
        "signals": signals,
        "signals_by_eps": by_eps,
        "tradeoff": tradeoff,
        "pulses": pulses,
    }


def _parse_junit(path: Path) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    tests = failures = errors = skipped = 0
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "testsuite" and el.get("tests") is not None:
            tests += int(el.get("tests") or 0)
            failures += int(el.get("failures") or 0)
            errors += int(el.get("errors") or 0)
            skipped += int(el.get("skipped") or 0)
    return {
        "passed": tests - failures - errors - skipped,
        "failed": failures + errors,
        "skipped": skipped,
        "source": "junit",
    }


def build_verify(records: list[dict], junit: str | Path | None = None) -> dict:
    convergence = []
    cross_checks = []
    for r in records:
        rid = r.get("id", "")
        c = r.get("convergence")
        if isinstance(c, dict):
            sweeps = c.get("sweeps") or {}
            for axis, s in sweeps.items():
                if not isinstance(s, dict):
                    continue
                convergence.append(
                    {
                        "id": rid,
                        "axis": axis,
                        "values": s.get("values") or [],
                        "results": s.get("results") or [],
                        "tol": c.get("rel_tol", 0.0),
                        "converged": c.get("converged") is True,
                    }
                )
        for xc in r.get("cross_check") or []:
            if not isinstance(xc, dict):
                continue
            cross_checks.append(
                {
                    "id": rid,
                    "method": xc.get("method", ""),
                    "rel_diff": xc.get("rel_diff", None),
                    "tol": xc.get("tol", 0.0),
                    "agree": xc.get("agree") is True,
                }
            )
    if junit and Path(junit).is_file():
        tests = _parse_junit(Path(junit))
    else:
        tests = {"passed": 0, "failed": 0, "skipped": 0, "source": None}
    out: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tests": tests,
        "convergence": convergence,
        "cross_checks": cross_checks,
    }
    try:
        from tools.check_claims import check_file  # type: ignore

        claims = {"ok": 0, "warn": 0, "fail": 0, "files": []}
        for doc in ("TECHNICAL.md", "README.md"):
            if not Path(doc).is_file():
                continue
            result = check_file(doc)
            claims["files"].append(doc)
            if isinstance(result, dict):
                claims["ok"] += int(result.get("ok", 0))
                claims["warn"] += int(result.get("warn", 0))
                claims["fail"] += int(result.get("fail", 0))
        out["claims"] = claims
    except Exception:
        pass
    return out


def _encode(name: str, data: Any) -> tuple[str, bytes]:
    text = json.dumps(data, separators=(",", ":"), allow_nan=False)
    return name, text.encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", default="results")
    p.add_argument("--out", default="site/src/data/live")
    p.add_argument("--junit", default=None)
    p.add_argument("--max-mb", type=float, default=8.0)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    results = Path(args.results)
    arrays = results / "arrays"
    records = load_records(results)
    planned: dict[str, Any | None] = {
        "records": records,
        "inflation": None,
        "errors": None,
        "readout": None,
        "verify": build_verify(records, args.junit),
    }
    omitted: list[tuple[str, str]] = []

    inf_path = arrays / "lab.inflation_wigner.npz"
    if inf_path.is_file():
        planned["inflation"] = build_inflation(records, arrays)
    else:
        omitted.append(("inflation.json", str(inf_path)))

    if any(tokens(r.get("id", ""))[0] in {"t2_1", "t2_2"} for r in records):
        planned["errors"] = build_errors(records, arrays)
    else:
        omitted.append(("errors.json", "t2_1/t2_2 records"))

    if any(tokens(r.get("id", ""))[0] == "t2_3" for r in records):
        planned["readout"] = build_readout(records, arrays)
    else:
        omitted.append(("readout.json", "t2_3 records"))

    encoded: list[tuple[str, bytes]] = []
    sizes: list[tuple[str, int]] = []
    for name in NAMES:
        data = planned[name]
        if data is None:
            if not any(o[0] == f"{name}.json" for o in omitted):
                omitted.append((f"{name}.json", "missing input"))
            continue
        fname, blob = _encode(name, data)
        encoded.append((fname, blob))
        sizes.append((f"{fname}.json", len(blob)))

    total = sum(n for _, n in sizes)
    limit = args.max_mb * 1_000_000
    for fname, n in sizes:
        print(f"{fname}  {n / 1e6:.3f} MB")
    print(f"total {total / 1e6:.3f} MB")
    if total > limit:
        print(f"total {total} bytes exceeds --max-mb {args.max_mb} ({int(limit)} bytes); writing nothing")
        return 1

    out = Path(args.out)
    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        written = set()
        for name, blob in encoded:
            dest = out / f"{name}.json"
            dest.write_bytes(blob)
            written.add(dest.name)
            print(f"wrote {dest}")
        for fname, reason in omitted:
            stale = out / fname
            if stale.exists():
                stale.unlink()
            print(f"omitted {fname} (missing {reason})")
        for leftover in out.glob("*.json"):
            if leftover.name not in written and leftover.name not in {o[0] for o in omitted}:
                leftover.unlink()
    else:
        for fname, reason in omitted:
            print(f"omitted {fname} (missing {reason})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
