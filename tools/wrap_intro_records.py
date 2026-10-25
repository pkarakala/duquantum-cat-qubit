"""Wrap the four committed Intro flat JSONs (results/task_1_*.json) as nine duq.record/v2 records,
so Intro numbers can be cited with `rec:` tokens. Values are copied exactly; nothing is recomputed.

Uses its own JSON writer on purpose: src.results.record would stamp this wrapper, not the task script
that produced the number, as provenance.script.

    python -m tools.wrap_intro_records --dry-run
    python -m tools.wrap_intro_records [--out results/records]
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.build_index import SCHEMA, validate_record

INTRO = {"task_1_0": "tasks/task_1_0.py", "task_1_1": "tasks/task_1_1.py",
         "task_1_2": "tasks/task_1_2.py", "task_1_3a": "tasks/task_1_3a.py"}
DEFAULT_OUT = "results/records"

# Independent references, copied as literals (RESEARCH §1, §7) so tools/ never applies the 2*pi.
ALPHA2 = 4.41                 # alpha^2 = eps_d / g2
TWO_KAPPA_A = 0.116867        # 1/us
SETTLE_1PCT_LINRESP_US = 1.13  # ln(100) / (kappa_b / 4), linearised 2x2 response
TWO_MODE_PARAMS = {"g2_MHz": 0.763, "kappa_b_MHz": 2.6, "kappa_a_kHz": 9.3, "alpha": 2.1, "n_th": 0.0,
                   "eps_z_over_g2": 0.0, "eps_x_over_g2": 0.0}


def converged_at(rows, key, var, tol):
    """Smallest value of `var` whose result is within tol of the largest-N result."""
    # Copied verbatim from tasks/task_1_2.py::converged_at (tools/ stays stdlib-only).
    ref = rows[-1][key]
    for r in rows:
        if all(abs(s[key] - ref) <= tol * abs(ref) for s in rows if s[var] >= r[var]):
            return r[var]
    return rows[-1][var]


def _rel(value, ref):
    return abs(value - ref) / abs(ref)


def _xcheck(method, value, ref, tol, rel_diff=None):
    rd = _rel(value, ref) if rel_diff is None else rel_diff
    return {"method": method, "ref_id": None, "value": ref, "rel_diff": rd, "tol": tol, "agree": rd <= tol}


def _convergence(sweeps, key, rel_tol, chosen):
    """CONTRACT §6.2 block from the task_1_2 sweeps: Na swept at fixed Nb, Nb swept at fixed Na."""
    block = {"key": key, "rel_tol": rel_tol, "sweeps": {}, "needed": {}, "converged": True}
    for axis, other, rows in (("Na", "Nb", sweeps["sweep_Na"]), ("Nb", "Na", sweeps["sweep_Nb"])):
        results = [r[key] for r in rows]
        block["sweeps"][axis] = {"fixed": {other: rows[0][other]}, "values": [r[axis] for r in rows],
                                 "results": results}
        block["needed"][axis] = converged_at(rows, key, axis, rel_tol)
        axis_ok = chosen[axis] >= block["needed"][axis] and _rel(results[-2], results[-1]) <= rel_tol
        block["converged"] = block["converged"] and axis_ok
    return block


def _git(fmt, json_path):
    p = Path(json_path).resolve()
    try:
        r = subprocess.run(["git", "-C", str(p.parent), "log", "-1", f"--format={fmt}", "--", p.name],
                           capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return r.stdout.strip() or None


def _utc_z(iso):
    if iso is None:
        return None
    return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _provenance(stem, json_path, wrapped_at):
    return {"script": INTRO[stem], "git_commit": _git("%h", json_path), "git_branch": None, "dirty": False,
            "dynamiqs": None, "jax": None, "numpy": None, "scipy": None, "python": None, "platform": None,
            "cpu_count": None, "wall_s": None, "timestamp": _utc_z(_git("%cI", json_path)),
            "wrapped_by": "tools/wrap_intro_records.py", "wrapped_at": wrapped_at}


def build_records(results_dir="results") -> list[dict]:
    """Read the four flat JSONs and return the nine v2 records (no files are written)."""
    rd = Path(results_dir)
    src = {stem: json.loads((rd / f"{stem}.json").read_text(encoding="utf-8")) for stem in INTRO}
    t0, t1, t2, t3 = src["task_1_0"], src["task_1_1"], src["task_1_2"], src["task_1_3a"]
    wrapped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    two_mode_trunc = {"Na": t1["Na"], "Nb": t1["Nb"]}

    def rec(rid, task, stem, value, units, method, params, truncation, convergence, cross_check,
            note, numerics=None):
        return {
            "schema": SCHEMA, "id": rid, "task": task, "quantity": rid.split(".")[1], "value": value,
            "uncertainty": None, "units": units, "method": method, "params": params, "truncation": truncation,
            "convergence": convergence, "numerics": numerics, "cross_check": cross_check,
            "artifacts": {"source_json": f"results/{stem}.json"},
            "notes": f"wrapped from flat JSON results/{stem}.json; {note}",
            "provenance": _provenance(stem, rd / f"{stem}.json", wrapped_at),
        }

    one_mode_note = ("convergence null: single mode N=30 (one-mode effective model), checked against "
                     "the analytic prediction instead of a truncation sweep")
    gz_fit, gz_pred = t3["parity_decay_fit_per_us"], t3["parity_decay_pred_per_us"]
    peak_na, peak_nb = t1["peak_na"], t1["peak_nb"]
    big = t2["sweep_Na"][-1]   # Na=40, Nb=14: the largest truncation task_1_2 ran
    return [
        rec("t1_0.max_abs_error.td.one_mode.a2.00", "1.0", "task_1_0", t0["a"]["max_abs_error_vs_analytic"],
            "photons", "mesolve_vs_analytic",
            {"delta_over_2pi_MHz": 1.0, "kappa_over_2pi_MHz": 1.0, "alpha0": 2.0}, {"N": 30}, None,
            [_xcheck("analytic", t0["a"]["max_abs_error_vs_analytic"], 0.0, 1e-6,
                     rel_diff=t0["a"]["max_abs_error_vs_analytic"] / 4.0)],
            "max |<n>(t) - 4 exp(-kappa t)| over t in [0, 1] us. The analytic error is 0, so rel_diff is the "
            "error relative to the initial <n> = |alpha0|^2 = 4. convergence null: single mode N=30, "
            "checked against analytic 4e^{-kappa t}"),
        rec("t1_0.n_plateau.td.one_mode.a2.00", "1.0", "task_1_0", t0["b"]["final_n_sim"], "photons",
            "mesolve_final_value", {"kappa_2_over_2pi_MHz": 0.8957, "alpha0": 2.0}, {"N": 30}, None,
            [_xcheck("analytic", t0["b"]["final_n_sim"], t0["b"]["final_n_pred"], 1e-9)],
            "<n> at t = 3 us under pure two-photon loss from |alpha0 = 2>; parity is conserved, so the "
            "plateau is P_odd = 0.5 (1 - e^-8). " + one_mode_note),
        rec("t1_0.final_n.td.one_mode.a2.10", "1.0", "task_1_0", t0["c"]["final_n"][1], "photons",
            "mesolve_final_value", {**TWO_MODE_PARAMS, "kappa_2_scale": 1.0}, {"N": 30}, None,
            [_xcheck("semiclassical_alpha2", t0["c"]["final_n"][1], ALPHA2, 0.01)],
            "<n> at t = 2 us from vacuum, one-mode model at nominal kappa_2 (final_n[1] of the kappa_2/4, "
            "kappa_2, 4 kappa_2 batch). " + one_mode_note),
        rec("t1_1.peak_na.td.two_mode.a2.10", "1.1", "task_1_1", peak_na, "photons", "mesolve_peak",
            dict(TWO_MODE_PARAMS), two_mode_trunc,
            _convergence(t2, "peak_na", 0.005, two_mode_trunc),
            [_xcheck("larger_truncation_same_solver", peak_na, big["peak_na"], 0.005)],
            "transient peak of <n_a> during inflation from vacuum. Sweeps from results/task_1_2.json. "
            "The cross-check is the same solver at Na=40, Nb=14 (not fully independent)"),
        rec("t1_1.steady_na.td.two_mode.a2.10", "1.1", "task_1_1", t1["steady_na"], "photons",
            "mesolve_final_value", dict(TWO_MODE_PARAMS), two_mode_trunc,
            _convergence(t2, "steady_na", 0.001, two_mode_trunc),
            [_xcheck("semiclassical_alpha2", t1["steady_na"], ALPHA2, 0.01)],
            "mean <n_a> over the last 20 saved points of the 3 us trace. Sweeps from results/task_1_2.json"),
        rec("t1_1.settle_1pct.td.two_mode.a2.10", "1.1", "task_1_1", t1["settle_1pct_us"], "us",
            "mesolve_settle", dict(TWO_MODE_PARAMS), two_mode_trunc, None,
            [_xcheck("linresp_analytic", t1["settle_1pct_us"], SETTLE_1PCT_LINRESP_US, 0.1)],
            "time after which <n_a> stays within 1% of alpha^2 (10 ns save grid). convergence null: not "
            "swept in task_1_2; same run as converged peak/steady"),
        rec("t1_1.peak_nb.td.two_mode.a2.10", "1.1", "task_1_1", peak_nb, "photons", "mesolve_peak",
            dict(TWO_MODE_PARAMS), two_mode_trunc,
            _convergence(t2, "peak_nb", 0.005, two_mode_trunc),
            [_xcheck("larger_truncation_same_solver", peak_nb, big["peak_nb"], 0.005)],
            "transient peak of <n_b> during inflation from vacuum. Sweeps from results/task_1_2.json. "
            "The cross-check is the same solver at Na=40, Nb=14 (not fully independent)"),
        rec("t1_3a.gamma_z.td.two_mode.a2.10", "1.3a", "task_1_3a", gz_fit, "1/us", "mesolve_parity_fit",
            dict(TWO_MODE_PARAMS), {"Na": t3["Na"], "Nb": t3["Nb"]}, None,
            [_xcheck("analytic_2kappa_a_n", gz_fit, gz_pred, 0.01)],
            "parity decay rate from a pure-exponential fit (no offset) over t in [1, 6] us after inflation "
            "from vacuum; the flat JSON stores no fit stderr. convergence null: single truncation >= "
            "task_1_2 needed; superseded by t2_2.gamma_z.td.two_mode.a2.10",
            numerics={"fit_window_us": [1.0, 6.0]}),
        rec("t1_3a.cat_lifetime.td.two_mode.a2.10", "1.3a", "task_1_3a", t3["cat_lifetime_us"], "us",
            "inverse_parity_fit", dict(TWO_MODE_PARAMS), {"Na": t3["Na"], "Nb": t3["Nb"]}, None,
            [_xcheck("analytic_inverse_2kappa_a_alpha2", t3["cat_lifetime_us"], 1.0 / (TWO_KAPPA_A * ALPHA2),
                     0.01)],
            "1 / parity_decay_fit_per_us. convergence null: single truncation >= task_1_2 needed; "
            "superseded by t2_2.gamma_z.td.two_mode.a2.10"),
    ]


def write_records(records, out_dir=DEFAULT_OUT) -> list[Path]:
    """Validate every record, then write <out_dir>/<id>.json. Raises ValueError before writing anything."""
    for r in records:
        errs = validate_record(r, r["id"])
        if errs:
            raise ValueError(f"{r['id']}: " + "; ".join(errs))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for r in records:
        p = out / f"{r['id']}.json"
        p.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
        paths.append(p)
    return paths


def _git_dirty() -> bool | None:
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "src", "tasks", "tools"],
                           capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(r.stdout.strip())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Wrap the Intro flat JSONs as duq.record/v2 records.")
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--dry-run", action="store_true", help="print ids and values, write nothing")
    args = p.parse_args(argv)
    records = build_records("results")
    if args.dry_run:
        for r in records:
            print(f"{r['id']} = {r['value']!r} {r['units']}")
        return 0
    if Path(args.out).resolve() == Path(DEFAULT_OUT).resolve():
        dirty = _git_dirty()
        if dirty is not False:
            why = "uncommitted changes in src/ tasks/ tools/" if dirty else "git status unavailable"
            print(f"refusing to write production records to {DEFAULT_OUT}: {why}", file=sys.stderr)
            return 1
    try:
        paths = write_records(records, args.out)
    except ValueError as e:
        print(f"wrap_intro_records: {e}", file=sys.stderr)
        return 1
    for path in paths:
        print("wrote", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
