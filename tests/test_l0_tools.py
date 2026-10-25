"""Lane l0-tools: index builder, claims linter, intro-record wrapper, run queue, run_all.sh.

All four tools are stdlib-only, so nothing here touches jax/dynamiqs and the file runs in seconds.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools import build_index, check_claims, runq, wrap_intro_records

ROOT = Path(__file__).resolve().parents[1]
SLEEP = [sys.executable, "-c", "import time; time.sleep(0.8)"]

INTRO_IDS = {
    "t1_0.max_abs_error.td.one_mode.a2.00": ("task_1_0", ("a", "max_abs_error_vs_analytic")),
    "t1_0.n_plateau.td.one_mode.a2.00": ("task_1_0", ("b", "final_n_sim")),
    "t1_0.final_n.td.one_mode.a2.10": ("task_1_0", ("c", "final_n", 1)),
    "t1_1.peak_na.td.two_mode.a2.10": ("task_1_1", ("peak_na",)),
    "t1_1.steady_na.td.two_mode.a2.10": ("task_1_1", ("steady_na",)),
    "t1_1.settle_1pct.td.two_mode.a2.10": ("task_1_1", ("settle_1pct_us",)),
    "t1_1.peak_nb.td.two_mode.a2.10": ("task_1_1", ("peak_nb",)),
    "t1_3a.gamma_z.td.two_mode.a2.10": ("task_1_3a", ("parity_decay_fit_per_us",)),
    "t1_3a.cat_lifetime.td.two_mode.a2.10": ("task_1_3a", ("cat_lifetime_us",)),
}
INTRO_DISPLAY = {
    "t1_0.max_abs_error.td.one_mode.a2.00": "9.7e-12",
    "t1_0.n_plateau.td.one_mode.a2.00": "0.49983",
    "t1_0.final_n.td.one_mode.a2.10": "4.404",
    "t1_1.peak_na.td.two_mode.a2.10": "6.8944",
    "t1_1.steady_na.td.two_mode.a2.10": "4.4026",
    "t1_1.settle_1pct.td.two_mode.a2.10": "1.07",
    "t1_1.peak_nb.td.two_mode.a2.10": "1.99",
    "t1_3a.gamma_z.td.two_mode.a2.10": "0.5135",
    "t1_3a.cat_lifetime.td.two_mode.a2.10": "1.95",
}
GZ = "t2_2.gamma_z.td.two_mode.a2.10"


def _rec(id, value, d=None, **over):
    """A valid duq.record/v2 dict (converged, one agreeing cross-check, clean); written to d/<id>.json if d."""
    rec = {
        "schema": "duq.record/v2", "id": id, "task": "2.2", "quantity": id.split(".")[1],
        "value": value, "uncertainty": None, "units": "1/us", "method": "td_fit",
        "params": {"alpha": 2.1}, "truncation": {"Na": 32, "Nb": 12},
        "convergence": {"key": "gamma_z", "rel_tol": 1e-3, "converged": True},
        "numerics": None,
        "cross_check": [{"method": "analytic", "ref_id": None, "value": value,
                         "rel_diff": 0.009, "tol": 0.02, "agree": True}],
        "artifacts": None, "notes": None,
        "provenance": {"script": "tasks/task_2_2.py", "git_commit": "abc1234", "dirty": False},
    }
    rec.update(over)
    if d is not None:
        Path(d).mkdir(parents=True, exist_ok=True)
        (Path(d) / f"{id}.json").write_text(json.dumps(rec), encoding="utf-8")
    return rec


def _dig(data, keys):
    for k in keys:
        data = data[k]
    return data


# ---------------------------------------------------------------- check_claims

@pytest.mark.parametrize("s, n", [("1.20e-4", 3), ("0.5135", 4), ("4.4026", 5), ("1.07", 3), ("0.00120", 3),
                                  ("28", 2), ("100", 3), ("1.2E+03", 2), ("-0.17", 2)])
def test_count_sig_figs(s, n):
    assert check_claims.count_sig_figs(s) == n


@pytest.mark.parametrize("disp, value, ok", [
    ("1.20e-4", 1.2021e-4, True), ("0.5135", 0.51346, True), ("0.5135", 0.5134564726057531, True),
    ("1.95", 1.9475847581102153, True), ("6.8944", 6.894411732563246, True), ("4.40", 4.402615556547587, True),
    ("1.21e-4", 1.2021e-4, False), ("0.5136", 0.51346, False), ("4.41", 4.402615556547587, False),
])
def test_matches(disp, value, ok):
    assert check_claims.matches(disp, value) is ok


def test_matches_zero():
    assert check_claims.matches("0", 0.0)
    assert not check_claims.matches("0", 1e-12)


def test_find_tokens():
    line = f"| Γ_Z | 0.5135 /µs `rec:{GZ}=0.5135` |"
    toks = check_claims.find_tokens("intro\n" + line + "\n")
    assert len(toks) == 1
    t = toks[0]
    assert (t["line"], t["id"], t["path"], t["disp"]) == (2, GZ, None, "0.5135")
    assert t["text"] == line
    toks = check_claims.find_tokens(f"x `rec:{GZ}#cross_check.0.rel_diff=0.009` y")
    assert toks[0]["path"] == "cross_check.0.rel_diff" and toks[0]["disp"] == "0.009"


def test_resolve_path():
    rec = {"value": 1.5, "cross_check": [{"rel_diff": 0.009}]}
    assert check_claims.resolve_path(rec, None) == 1.5
    assert check_claims.resolve_path(rec, "cross_check.0.rel_diff") == 0.009
    with pytest.raises((KeyError, IndexError)):
        check_claims.resolve_path(rec, "cross_check.3.rel_diff")
    with pytest.raises((KeyError, IndexError)):
        check_claims.resolve_path(rec, "numerics.rel_residual")


def _claims_fixture(tmp_path):
    d = tmp_path / "records"
    _rec(GZ, 0.51346, d)
    _rec("t2_2.c_false.td.x", 1.0, d, convergence={"converged": False})
    _rec("t2_2.c_none.td.x", 1.0, d, convergence=None)
    _rec("t2_2.c_none_notes.td.x", 1.0, d, convergence=None, notes="analytic: truncation-independent")
    _rec("t2_2.no_agree.td.x", 1.0, d, cross_check=[{"method": "m", "ref_id": None, "value": 2.0,
                                                    "rel_diff": 1.0, "tol": 0.1, "agree": False}])
    _rec("t2_2.cc_empty.td.x", 1.0, d, cross_check=[])
    _rec("t2_2.dirty.td.x", 1.0, d, provenance={"script": "tasks/x.py", "git_commit": "abc", "dirty": True})
    return d


def test_check_file_statuses(tmp_path):
    d = _claims_fixture(tmp_path)
    cases = [
        (f"valid `rec:{GZ}=0.5135`", "ok", None),
        ("missing `rec:t2_9.nothing.td.x=1.0`", "fail", "missing record"),
        (f"mismatch `rec:{GZ}=0.5136`", "fail", "mismatch"),
        (f"nested `rec:{GZ}#cross_check.0.rel_diff=0.009`", "ok", None),
        (f"bad path `rec:{GZ}#cross_check.3.rel_diff=0.009`", "fail", "bad path"),
        (f"unparseable `rec:{GZ}=0.51x`", "fail", "unparseable"),
        ("not converged `rec:t2_2.c_false.td.x=1.0`", "fail", "not converged"),
        ("null conv, no notes `rec:t2_2.c_none.td.x=1.0`", "fail", "not converged"),
        ("null conv + notes `rec:t2_2.c_none_notes.td.x=1.0`", "ok", None),
        ("no agree `rec:t2_2.no_agree.td.x=1.0`", "fail", "no agreeing cross_check"),
        ("empty cc `rec:t2_2.cc_empty.td.x=1.0`", "fail", "no agreeing cross_check"),
        ("dirty `rec:t2_2.dirty.td.x=1.0`", "fail", "dirty provenance"),
        ("Illustrative row `rec:t2_9.nothing.td.x=1.0`", "warn", "missing record"),
    ]
    md = tmp_path / "doc.md"
    md.write_text("\n".join(c[0] for c in cases) + "\n", encoding="utf-8")
    rows = check_claims.check_file(md, records_dir=d)
    assert [r["status"] for r in rows] == [c[1] for c in cases]
    for r, (_, _, reason) in zip(rows, cases):
        if reason is not None:
            assert r["reason"].startswith(reason), (r["line"], r["reason"])
    assert [r["line"] for r in rows] == list(range(1, len(cases) + 1))
    assert rows[0]["actual"] == 0.51346
    assert rows[2]["reason"] == "mismatch (record=0.51346)"


def test_check_claims_exit_codes(tmp_path):
    d = _claims_fixture(tmp_path)
    good = tmp_path / "good.md"
    good.write_text(f"`rec:{GZ}=0.5135`\nillustrative `rec:t2_9.nothing.td.x=1`\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text(f"`rec:{GZ}=0.5135`\n`rec:t2_2.dirty.td.x=1.0`\n", encoding="utf-8")
    assert check_claims.main(["--files", str(good), "--records-dir", str(d)]) == 0
    assert check_claims.main(["--files", str(good), "--records-dir", str(d), "--strict"]) == 1
    assert check_claims.main(["--files", str(bad), "--records-dir", str(d)]) == 1
    # a missing --file is a warning, not a failure
    assert check_claims.main(["--files", str(tmp_path / "nope.md"), "--records-dir", str(d)]) == 0
    assert check_claims.main(["--files", str(tmp_path / "nope.md"), "--records-dir", str(d), "--strict"]) == 1


# ---------------------------------------------------------------- build_index

def test_build_index(tmp_path):
    d, out = tmp_path / "records", tmp_path / "index.json"
    _rec("t2_2.zeta.td.two_mode", 2.0, d)
    _rec("t2_1.alpha.eig.two_mode.a1.40", 1.0, d)
    idx = build_index.build_index(d, out)
    assert idx["schema"] == "duq.index/v1" and idx["count"] == 2
    assert [r["id"] for r in idx["records"]] == ["t2_1.alpha.eig.two_mode.a1.40", "t2_2.zeta.td.two_mode"]
    assert re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", idx["generated_at"])
    assert json.loads(out.read_text(encoding="utf-8")) == idx

    bad_cases = {
        "missing_units": lambda dd: (dd / "t2_2.nounits.td.x.json").write_text(
            json.dumps({k: v for k, v in _rec("t2_2.nounits.td.x", 1.0).items() if k != "units"})),
        "id_ne_stem": lambda dd: (dd / "t2_2.other.td.x.json").write_text(json.dumps(_rec("t2_2.thing.td.x", 1.0))),
        "schema_v1": lambda dd: _rec("t2_2.old.td.x", 1.0, dd, schema="duq.record/v1"),
    }
    for name, make in bad_cases.items():
        dd, oo = tmp_path / name, tmp_path / f"{name}.json"
        _rec("t2_2.zeta.td.two_mode", 2.0, dd)
        _rec("t2_1.alpha.eig.two_mode.a1.40", 1.0, dd)
        make(dd)
        assert build_index.main(["--records-dir", str(dd), "--out", str(oo)]) == 1, name
        assert not oo.exists(), name


def test_validate_record_errors():
    assert build_index.validate_record(_rec("t2_2.ok.td.x", 1.0), "t2_2.ok.td.x") == []
    assert build_index.validate_record(_rec("T2.Bad", 1.0))
    for v in (float("nan"), float("inf"), True, "1.0", None):
        assert build_index.validate_record(_rec("t2_2.v.td.x", v)), v
    assert build_index.validate_record(_rec("t2_2.p.td.x", 1.0, provenance={"script": "s", "git_commit": "c"}))
    assert build_index.validate_record(_rec("t2_2.p.td.x", 1.0,
                                            provenance={"script": "s", "git_commit": "c", "dirty": "no"}))
    assert build_index.validate_record(_rec("t2_2.c.td.x", 1.0, cross_check={"agree": True}))
    assert build_index.validate_record(_rec("t2_2.c.td.x", 1.0, cross_check=[{"agree": True, "tol": 0.1}]))


def test_build_index_default_out_refuses_when_dirty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _rec("t2_2.zeta.td.two_mode", 2.0, tmp_path / "results" / "records")
    monkeypatch.setattr(build_index, "_git_dirty", lambda: True)
    assert build_index.main([]) == 1
    assert not (tmp_path / "results" / "index.json").exists()
    monkeypatch.setattr(build_index, "_git_dirty", lambda: False)
    assert build_index.main([]) == 0
    assert (tmp_path / "results" / "index.json").exists()


# ---------------------------------------------------------------- wrap_intro_records

def test_wrap_intro_records():
    recs = wrap_intro_records.build_records(ROOT / "results")
    by_id = {r["id"]: r for r in recs}
    assert len(recs) == 9 and set(by_id) == set(INTRO_IDS)
    for rid, (stem, keys) in INTRO_IDS.items():
        src = json.loads((ROOT / "results" / f"{stem}.json").read_text(encoding="utf-8"))
        r = by_id[rid]
        assert r["value"] == _dig(src, keys), rid
        assert build_index.validate_record(r, rid) == [], rid
        assert any(c["agree"] is True for c in r["cross_check"]), rid
        assert r["provenance"]["dirty"] is False
        assert r["provenance"]["script"] == wrap_intro_records.INTRO[stem]
        assert r["notes"].startswith(f"wrapped from flat JSON results/{stem}.json"), rid
        if r["convergence"] is None:
            assert r["notes"], rid
    for rid, needed in [("t1_1.peak_na.td.two_mode.a2.10", {"Na": 24, "Nb": 10}),
                        ("t1_1.steady_na.td.two_mode.a2.10", {"Na": 16, "Nb": 4}),
                        ("t1_1.peak_nb.td.two_mode.a2.10", {"Na": 16, "Nb": 10})]:
        conv = by_id[rid]["convergence"]
        assert conv["needed"] == needed and conv["converged"] is True, rid
    gz = by_id["t1_3a.gamma_z.td.two_mode.a2.10"]
    assert gz["cross_check"][0]["value"] == 0.5145525434761521
    assert gz["numerics"] == {"fit_window_us": [1.0, 6.0]}
    if shutil.which("git") is None:
        pytest.skip("git not available: commit assertion skipped")
    sha = subprocess.run(["git", "log", "-1", "--format=%h", "--", "results/task_1_1.json"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    assert by_id["t1_1.peak_na.td.two_mode.a2.10"]["provenance"]["git_commit"] == sha


def test_intro_claims_pass(tmp_path):
    d = tmp_path / "records"
    paths = wrap_intro_records.write_records(wrap_intro_records.build_records(ROOT / "results"), d)
    assert len(paths) == 9
    lines = [f"| {rid} | `rec:{rid}={disp}` |" for rid, disp in INTRO_DISPLAY.items()]
    lines.append("| fit vs 2 kappa_a n | `rec:t1_3a.gamma_z.td.two_mode.a2.10#cross_check.0.value=0.5146` |")
    md = tmp_path / "claims.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert check_claims.main(["--files", str(md), "--records-dir", str(d), "--strict"]) == 0
    md.write_text(md.read_text(encoding="utf-8").replace("a2.10=0.5135`", "a2.10=0.5137`"), encoding="utf-8")
    assert check_claims.main(["--files", str(md), "--records-dir", str(d)]) == 1


# ---------------------------------------------------------------- runq

def _jobs(root):
    return {j["name"]: j for j in runq.load_jobs(root)}


def test_runq_big_jobs_exclusive(tmp_path, monkeypatch):
    monkeypatch.setenv("DUQ_RUNQ_DIR", str(tmp_path))
    root = runq.queue_dir()
    assert root == tmp_path
    runq.submit(root, "big1", 4, SLEEP)
    runq.submit(root, "big2", 4, SLEEP)
    assert runq.worker(root, max_jobs=3, max_ram_gb=11, poll_s=0.1, once=True) == 0
    j = _jobs(root)
    assert all(j[n]["state"] == "done" and j[n]["exit_code"] == 0 for n in ("big1", "big2"))
    first, second = sorted(j.values(), key=lambda x: x["t_start"])
    assert second["t_start"] >= first["t_end"]
    assert not (root / "worker.lock").exists()


def test_runq_small_jobs_overlap(tmp_path, monkeypatch):
    monkeypatch.setenv("DUQ_RUNQ_DIR", str(tmp_path))
    root = runq.queue_dir()
    runq.submit(root, "small1", 1, SLEEP)
    runq.submit(root, "small2", 1, SLEEP)
    assert runq.worker(root, max_jobs=3, max_ram_gb=11, poll_s=0.1, once=True) == 0
    j = _jobs(root)
    assert j["small1"]["state"] == j["small2"]["state"] == "done"
    assert j["small2"]["t_start"] < j["small1"]["t_end"]
    table = runq.status_table(root)
    assert "small1" in table and "small2" in table and "done" in table


def test_runq_failed_and_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DUQ_RUNQ_DIR", str(tmp_path))
    monkeypatch.setenv("XLA_FLAGS", "not-the-worker-value")
    root = runq.queue_dir()
    runq.submit(root, "fail3", 1, [sys.executable, "-c",
                                   "import os,sys; print(os.environ['XLA_FLAGS']); sys.exit(3)"])
    with pytest.raises(ValueError):
        runq.submit(root, "fail3", 1, SLEEP)
    for bad in [dict(name="bad name", ram_gb=1, cmd=SLEEP), dict(name="ok", ram_gb=0, cmd=SLEEP),
                dict(name="ok", ram_gb=1, cmd=[])]:
        with pytest.raises(ValueError):
            runq.submit(root, **bad)
    assert runq.worker(root, max_jobs=3, max_ram_gb=11, poll_s=0.1, once=True) == 0
    j = _jobs(root)["fail3"]
    assert j["state"] == "failed" and j["exit_code"] == 3 and j["wall_s"] > 0
    assert "intra_op_parallelism_threads=2" in Path(j["log"]).read_text()
    assert runq.main(["submit", "--name", "x", "--ram-gb", "1", sys.executable, "-c", "pass"]) == 0
    assert runq.main(["submit", "--name", "y", "--ram-gb", "1", "--", sys.executable, "-c", "pass"]) == 0
    j = _jobs(root)
    assert j["x"]["cmd"] == j["y"]["cmd"] == [sys.executable, "-c", "pass"]
    assert j["x"]["state"] == "pending"


def test_runq_lock_and_orphans(tmp_path, monkeypatch):
    monkeypatch.setenv("DUQ_RUNQ_DIR", str(tmp_path))
    root = runq.queue_dir()
    p = runq.submit(root, "orphan", 1, SLEEP)
    job = json.loads(p.read_text())
    job["state"] = "running"
    p.write_text(json.dumps(job))
    (root / "worker.lock").write_text("12345")
    assert runq.worker(root, poll_s=0.1, once=True) == 2
    assert _jobs(root)["orphan"]["state"] == "running"
    (root / "worker.lock").unlink()
    assert runq.worker(root, poll_s=0.1, once=True) == 0
    j = _jobs(root)["orphan"]
    assert j["state"] == "failed" and j["reason"] == "orphaned (worker restarted)"


# ---------------------------------------------------------------- stdlib-only + run_all.sh

def test_tools_stdlib_only():
    allowed = set(sys.stdlib_module_names)
    for name in ("build_index", "check_claims", "wrap_intro_records", "runq"):
        tree = ast.parse((ROOT / "tools" / f"{name}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, name
                mods = [node.module]
            else:
                continue
            for m in mods:
                ok = m.split(".")[0] in allowed or m == "tools" or m.startswith("tools.") or m == "src.convergence"
                assert ok, f"{name}: non-stdlib import {m}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_run_all_syntax():
    r = subprocess.run(["bash", "-n"], input=(ROOT / "run_all.sh").read_text(), text=True, capture_output=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None, reason="POSIX bash only")
def test_run_all_quick_dry_run():
    r = subprocess.run(["bash", "run_all.sh", "--quick", "--dry-run"], cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PY": sys.executable}, timeout=60)
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "tools.build_index" in out
    for t in ("task_1_3b", "task_2_2", "task_2_1_eig", "task_2_1_td", "task_2_1_channels", "task_2_3",
              "task_2_4a", "task_2_4b", "task_2_4c_pulses"):
        assert f"-m tasks.{t} --quick" in out or f"SKIP tasks/{t}.py" in out, t
    last = [ln for ln in out.splitlines() if ln.strip()][-2:]
    assert "tools.build_index --quick" in last[0] and "tools.check_claims" in last[1]
