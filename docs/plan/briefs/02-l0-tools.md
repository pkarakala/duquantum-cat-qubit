# Brief `l0-tools`: Tooling: index, claims linter, intro record wrapper, run queue, run_all, CI

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l0-tools`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/02-l0-tools.md`, then execute this brief exactly. Keep `docs/plan/status/l0-tools.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l0-tools` | `std/l0-tools` from `standard-track` | none: CONTRACT text only (`l0-core` NOT required) | fast (Sonnet-class) | 75 min | Phase 0, parallel with `l0-core`; done by **7:30 PM Sat Oct 24** |

## 1. Goal and why
Build the plumbing every other lane relies on. None of it computes physics.
- `tools/check_claims.py` is the gate for deliverable **D1**: every number in `TECHNICAL.md`/`README.md` must resolve to a converged, cross-checked, clean-provenance record (CONTRACT §11).
- `tools/runq.py` lets the integrator run long jobs overnight, with no more than 3 heavy jobs and only one sparse LU above 3 GB at a time on the 15.9 GB laptop (CONTRACT §2, §12).
- `tools/wrap_intro_records.py` turns the four committed Intro JSONs into `duq.record/v2` records, so the Intro numbers can be cited with `rec:` tokens too.
- `tools/build_index.py` writes `results/index.json`, which `tools/export_lab_data.py` (L6) reads (CONTRACT §13).
- `run_all.sh` gets stage flags plus `--quick` for deliverable **D2** (a fresh clone reproduces every figure).
- `.github/workflows/tests.yml` runs the fast tests on every push.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (your allowlist), §2 (env, quick vs production), §6.2 (record schema), §6.3 (ID regex), §11 (claims), §12 (runq), §13 (index consumer), §15 (tests).
- `docs/plan/RESEARCH.md` §1 (κ_a = 0.0584336 rad/µs, α² = 4.41, 2κ_a = 0.116867 /µs), §3 (XLA_FLAGS, jax pin), §6 (Task 1.3a: 0.5135 vs 0.5146), §7 (linear-response settle time 1.13 µs vs 1.07 µs).
- `results/task_1_0.json`, `results/task_1_1.json`, `results/task_1_2.json`, `results/task_1_3a.json`, and `tasks/task_1_2.py::converged_at` (copy it verbatim; see §6).
- Current `run_all.sh`, `requirements.txt` and `.gitignore` (`results/quick/`, `results/logs/`, `figures/quick/` are already ignored).

## 3. Allowlist (touch nothing else)
- `tools/build_index.py`, `tools/check_claims.py`, `tools/wrap_intro_records.py`, `tools/runq.py`
- `run_all.sh`, `.github/workflows/tests.yml`, `tests/test_l0_tools.py`
- `docs/plan/status/l0-tools.md`
- Your own production outputs: the 9 files `results/records/t1_*.json` listed in §7.
- **Do not** add `tools/__init__.py`. `tools/` works as a namespace package with `python -m`. **Do not** edit `.gitignore`, `src/`, `tasks/`, `pytest.ini`, `tests/conftest.py`, or `requirements.txt`. **Do not** commit `results/index.json`; it is written on the integration branch only.

## 4. Interfaces you implement / rely on
**Stdlib only** in all four tools: no numpy, jax or dynamiqs, so they run in CI and in a bare Python. Every tool is run as `python -m tools.<name>` from the repo root and has a `main(argv=None) -> int`.

```python
# tools/build_index.py
SCHEMA = "duq.record/v2"; ID_RE = r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$"
REQUIRED = ("schema","id","task","quantity","value","units","method","params","provenance")
def validate_record(rec: dict, stem: str | None = None) -> list[str]   # [] if valid; one message per error
def build_index(records_dir="results/records", out="results/index.json") -> dict
# CLI: --records-dir, --out, --quick (= results/quick/records -> results/quick/index.json). Exit 1 (no write) if any record is invalid.
```
`validate_record` reports an error for each of these: a missing REQUIRED key; `schema != SCHEMA`; an id that fails `ID_RE`; `id != stem` (the filename without `.json`); a `value` that is not a finite int or float, or is a bool; `provenance` missing `script` / `git_commit` / `dirty`; `dirty` that is not a bool; `cross_check` present but not a list, or an entry missing `rel_diff` / `tol` / `agree`.

Index shape (CONTRACT does not fix it, so it is defined here; L6 reads it): `{"schema": "duq.index/v1", "generated_at": "YYYY-MM-DDTHH:MM:SSZ" (UTC), "count": n, "records": [full record, ...]}`, with `records` sorted by `id`.

```python
# tools/check_claims.py
TOKEN_RE = re.compile(r"`rec:(?P<id>[a-z0-9_]+(?:\.[a-z0-9_\-]+)*)(?:#(?P<path>[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*))?=(?P<disp>[^`\s]+)`")
NUM_RE = r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$"
def count_sig_figs(s: str) -> int
def matches(displayed: str, value: float) -> bool
def resolve_path(rec: dict, path: str | None)        # None -> rec["value"]; "cross_check.0.rel_diff" walks dicts, int segments index lists; KeyError/IndexError if missing
def find_tokens(text: str) -> list[dict]             # {"line": int (1-based), "text": the full line, "id", "path", "disp"}
def check_file(md_path, records_dir="results/records") -> list[dict]   # {"file","line","id","path","disp","actual","status": "ok"|"warn"|"fail","reason"}
# CLI: --files (default TECHNICAL.md README.md), --records-dir, --strict. A missing --file is a warn. Exit 0 iff no "fail" (with --strict: no "fail" and no "warn").
```
**Significant-figure rules:**
- Take the mantissa (the part before `e`/`E`), drop the sign and the `.`, then strip leading zeros. The count is the number of remaining digits. Trailing zeros count.
- So `1.20e-4` → 3, `0.5135` → 4, `0.00120` → 3, `28` → 2, `100` → 3, `-0.17` → 2.
- `matches(d, v)` is `f"{v:.{n-1}e}" == f"{float(d):.{n-1}e}"`, with n = `count_sig_figs(d)`. It compares strings, not floats. A displayed `0` matches iff `v == 0`. A `disp` that fails `NUM_RE` fails with `reason="unparseable"`.

**Rules per token, applied in this order. The first failure wins:**
1. The record `<records_dir>/<id>.json` is missing → `"missing record"`.
2. The path does not resolve → `"bad path"`.
3. The value does not match at the displayed precision → `"mismatch (record=<repr>)"`.
4. `convergence` is absent, or `converged` is not true → `"not converged"`. The only exception is `convergence is None` with a non-empty `notes`.
5. No `cross_check` entry has `agree is True` → `"no agreeing cross_check"`.
6. `provenance.dirty` is not `False` → `"dirty provenance"`.

Rules 4–6 check the record even when `#path` is used. If the line contains `illustrative` (case-insensitive), any fail becomes a warn. Print an ASCII table with the columns `STATUS | file:line | id[#path] | displayed | record | reason`, followed by the line `N ok, M warn, K fail`. Read the input as UTF-8 and print ASCII only (the Windows console is cp1252).

```python
# tools/runq.py  (CONTRACT §12)
BIG_GB = 3.0; XLA = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
def queue_dir() -> Path                     # $DUQ_RUNQ_DIR or results/logs/runq
def submit(root, name, ram_gb, cmd: list[str], cwd=None) -> Path       # writes jobs/<UTC %Y%m%dT%H%M%S_%f>_<name>.json
def load_jobs(root) -> list[dict]            # sorted by filename (FIFO)
def worker(root, max_jobs=3, max_ram_gb=11.0, poll_s=2.0, once=False) -> int
def status_table(root) -> str
```
**Job JSON:** `{"name","cmd","cwd","ram_gb","state": "pending"|"running"|"done"|"failed","submitted_at","started_at","ended_at" (ISO UTC),"t_start","t_end" (epoch floats),"pid","exit_code","wall_s","log": "<dir>/logs/<name>.log","reason"}`.

**`submit`:**
- Raises `ValueError` on a name that fails `^[A-Za-z0-9_.\-]+$`, a name already present in any state, `ram_gb <= 0`, or an empty `cmd`.
- The CLI takes the command as `argparse.REMAINDER` and strips a leading `--` if one is present. Windows PowerShell 5.1 can swallow `--`, so both forms must work.

**`worker`:**
- Takes `<dir>/worker.lock` with `os.open(O_CREAT|O_EXCL)`. If the lock is held it refuses with exit 2, unless `--force`. The lock is removed in `finally`.
- On start, any job left in `running` is set to `failed` with `reason="orphaned (worker restarted)"`. Do not use `os.kill(pid, 0)`, because it terminates the process on Windows.
- Each poll scans pending jobs FIFO and starts every job that fits. A job fits when running count < `max_jobs`, the running RAM sum plus the job's RAM is ≤ `max_ram_gb`, and, if the job is big (`ram_gb > 3`), no other big job is running.
- Starting a job runs `subprocess.Popen(cmd, cwd=cwd, env={**os.environ, "XLA_FLAGS": XLA, "PYTHONUNBUFFERED": "1"}, stdout=log, stderr=STDOUT, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))`.
- `proc.poll()` sets `done` on exit 0 and `failed` otherwise, and records `exit_code` and `wall_s`. Failed jobs are never retried.
- Every state write goes to a `.tmp` file followed by `os.replace`, retried 5× at 0.1 s (Windows sharing violations).
- The worker sleeps `poll_s` (default 2 s) between polls. With `once`, it returns 0 when nothing is pending or running.

**`status`:** prints `name | state | ram_gb | exit | wall_s | log`.

```python
# tools/wrap_intro_records.py
INTRO = {"task_1_0": "tasks/task_1_0.py", "task_1_1": "tasks/task_1_1.py",
         "task_1_2": "tasks/task_1_2.py", "task_1_3a": "tasks/task_1_3a.py"}
def build_records(results_dir="results") -> list[dict]   # pure: reads the 4 JSONs, returns 9 v2 records
def write_records(records, out_dir="results/records") -> list[Path]
# CLI: --out (default results/records), --dry-run (print the ids and values).
```
- Validate every record with `tools.build_index.validate_record` before writing.
- **Keep the local JSON writer permanently. Do not switch to `src.results.record`:** it would stamp this wrapper, not the original task script, as `provenance.script`.
- Use `converged_at`, copied verbatim from `tasks/task_1_2.py` with a comment saying so. You may `try: from src.convergence import converged_at` once `l0-core` is merged.
- When `--out` is the default `results/records`, refuse with exit 1 if `git status --porcelain -- src tasks tools` is non-empty.

## 5. Tests to write FIRST (TDD)
Write `tests/test_l0_tools.py` and commit it before any implementation. Build every fixture under `tmp_path` with a helper `_rec(id, value, **over)`, which writes a valid record: `convergence={"converged": True, ...}`, one cross_check with `agree: True`, and `dirty: False`. The file must not mark anything slow, and the whole file must run in < 20 s.
- `test_count_sig_figs`: parametrized over `("1.20e-4",3) ("0.5135",4) ("4.4026",5) ("1.07",3) ("0.00120",3) ("28",2) ("100",3) ("1.2E+03",2) ("-0.17",2)`.
- `test_matches`: parametrized over the following cases.
  - Pass: `("1.20e-4",1.2021e-4)`, `("0.5135",0.51346)`, `("0.5135",0.5134564726057531)`, `("1.95",1.9475847581102153)`, `("6.8944",6.894411732563246)`, `("4.40",4.402615556547587)`.
  - Fail: `("1.21e-4",1.2021e-4)`, `("0.5136",0.51346)`, `("4.41",4.402615556547587)`.
- `test_find_tokens`: the line ``| Γ_Z | 0.5135 /µs `rec:t2_2.gamma_z.td.two_mode.a2.10=0.5135` |`` gives id `t2_2.gamma_z.td.two_mode.a2.10`, path None and disp `0.5135`. A `#cross_check.0.rel_diff` suffix gives path `cross_check.0.rel_diff`.
- `test_resolve_path`: `{"cross_check":[{"rel_diff":0.009}]}` with `"cross_check.0.rel_diff"` returns 0.009. `"cross_check.3.rel_diff"` raises.
- `test_check_file_statuses`: one markdown file with one line per case. Expected statuses:
  - valid → ok; missing record → fail "missing record"; mismatch → fail; nested path ok → ok.
  - `converged: False` → fail; `convergence: None` without notes → fail; `None` with notes → ok.
  - all `agree: False` → fail; `cross_check: []` → fail; `dirty: True` → fail.
  - a line containing `illustrative` with a missing record → warn.
- `test_check_claims_exit_codes`: `main(["--files", f, "--records-dir", d])` returns 0 for a file of only ok and warn lines, 1 with `--strict` added, and 1 for any file containing a fail.
- `test_build_index`: two valid records written out of order give `count == 2`, ids sorted, and `generated_at` that matches `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$`. Each of these makes `main` return 1 and leaves no index file: a third record missing `units`; a record whose id differs from its filename; `schema: "duq.record/v1"`.
- `test_wrap_intro_records`: `build_records("results")` gives exactly the 9 ids in §7, and each `value ==` (exact equality) the JSON field listed there. Every record passes `validate_record` and has at least one `agree is True` cross_check. `peak_na`'s `convergence["needed"] == {"Na": 24, "Nb": 10}`, `steady_na`'s is `{"Na": 16, "Nb": 4}`, and both are `converged is True`. `provenance.git_commit` equals `git log -1 --format=%h -- results/task_1_1.json` (skip if `shutil.which("git")` is None).
- `test_intro_claims_pass`: write the 9 records to `tmp_path`, then a markdown file with the 9 tokens using the displayed values in §7, plus ``rec:t1_3a.gamma_z.td.two_mode.a2.10#cross_check.0.value=0.5146``. `check_claims.main` must return 0. Change `0.5135` to `0.5137` and it must return 1.
- `test_runq_big_jobs_exclusive` (monkeypatch `DUQ_RUNQ_DIR=tmp_path`):
  - Submit `big1` and `big2` with `ram_gb=4` and the command `[sys.executable, "-c", "import time; time.sleep(0.8)"]`, then call `worker(root, max_jobs=3, max_ram_gb=11, poll_s=0.1, once=True)`.
  - Both jobs end `done` with `exit_code == 0`, and the later `t_start` is ≥ the earlier `t_end`. The RAM sum, 8 ≤ 11, would allow overlap, so this tests the big-job rule.
- `test_runq_small_jobs_overlap`: two jobs with `ram_gb=1` and the same sleep do overlap, i.e. `t_start(2) < t_end(1)`.
- `test_runq_failed_and_env`: a job that runs `import os,sys; print(os.environ['XLA_FLAGS']); sys.exit(3)` ends `failed` with `exit_code == 3` and `wall_s > 0`, and its log contains `intra_op_parallelism_threads=2`. A duplicate name raises `ValueError`. `runq.main(["submit","--name","x","--ram-gb","1",sys.executable,"-c","pass"])` (without the `--`) works.
- `test_tools_stdlib_only`: `ast`-parse the four tools. Every top-level import is in `sys.stdlib_module_names`, or is `tools` / `src.convergence`.
- `test_run_all_syntax`: if `shutil.which("bash")`, run `subprocess.run(["bash","-n"], input=Path("run_all.sh").read_text())` and require returncode 0. Also `@pytest.mark.skipif(sys.platform=="win32")`: `PY=sys.executable bash run_all.sh --quick --dry-run` prints `tools.build_index` and either `task_2_2` or `SKIP tasks/task_2_2.py`.

## 6. Method, step by step
1. (5 min) `git switch -c std/l0-tools standard-track` (Cursor worktree mode may do this for you). Copy `docs/plan/status/_TEMPLATE.md` to `docs/plan/status/l0-tools.md` and mark it "started".
2. (15 min) Write all of §5 and run it: everything fails on ImportError. Commit `l0-tools: tests first`. Status: "tests written".
3. (8 min) `build_index.py`. Then (12 min) `check_claims.py`; it reuses nothing from `src`.
4. (10 min) `wrap_intro_records.py` with the exact mapping in §7.
   - `provenance = {"script": INTRO[...], "git_commit": git log -1 --format=%h -- <json>, "git_branch": null, "dirty": false, "dynamiqs": null, "jax": null, "numpy": null, "scipy": null, "python": null, "platform": null, "cpu_count": null, "wall_s": null, "timestamp": the commit's date (git log -1 --format=%cI -- <json>, converted to UTC Z), "wrapped_by": "tools/wrap_intro_records.py", "wrapped_at": now UTC Z}`.
   - Every record's `notes` starts with `"wrapped from flat JSON results/<file>"`.
   - The `rel_diff` convention throughout is `|value − ref| / |ref|`, with `agree = rel_diff <= tol`.
5. (12 min) `runq.py`, as specified in §4.
6. (8 min) Restructure `run_all.sh`:
   - Shebang plus `set -euo pipefail`; `PY=${PY:-python}`; `export XLA_FLAGS="${XLA_FLAGS:---xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2}"`.
   - Flags: `--intro`, `--standard` (no stage flag means both), the modifier `--quick`, and `--dry-run` (echo instead of run).
   - Always start with `$PY -m src.config` (the units check).
   - **Intro, full mode:** `task_1_0`, then *print* the runq command for `task_1_2` (15–30 min, heavy), then `task_1_1` and `task_1_3a`. This is the current order: 1.0, 1.2, 1.1, 1.3a.
   - **Intro with `--quick`:** `task_1_0`, `task_1_2 --quick`, `task_1_1`, `task_1_3a`. The intro scripts have no `--quick` except 1.2, and each of the other three is ≤ 2 min.
   - **Standard with `--quick`:** in order `task_1_3b task_2_2 task_2_1_eig task_2_1_td task_2_1_channels task_2_3 task_2_4a task_2_4b task_2_4c_pulses`, each run as `$PY -m tasks.<t> --quick`. If `tasks/<t>.py` does not exist, echo `SKIP tasks/<t>.py (not merged yet)` and continue.
   - **Standard, full mode:** run no Standard script. Print one line per existing script: `$PY -m tools.runq submit --name <t> --ram-gb <g> -- $PY -m tasks.<t>`, with `g = 6` for `task_2_1_eig` and `2` for the others (the integrator adjusts these).
   - **End:** `$PY -m tools.build_index` (with `--quick` in quick mode), then `$PY -m tools.check_claims`. In quick mode check_claims is non-fatal: capture its status and print it. In full mode its exit code is the script's exit code.
7. (5 min) `.github/workflows/tests.yml`:
   - `on: push: branches: [main, standard-track, 'std/**']` and `pull_request`; `runs-on: ubuntu-latest`; `timeout-minutes: 20`.
   - Steps: `actions/checkout@v4` with `fetch-depth: 0` (the wrapper test needs `git log`), then `actions/setup-python@v5` with `python-version: "3.12"` and `cache: pip`.
   - env: `JAX_PLATFORMS: cpu`, `MPLBACKEND: Agg`, `XLA_FLAGS` (two threads).
   - Run `pip install -r requirements.txt pytest scipy`, then `python -m pytest -m "not slow" -q`. Use `python -m`, not bare `pytest`, so the repo root is on `sys.path` for `src`/`tools`/`tasks`.
   - Add the comment: `# jax==0.12.0.1 pulls jaxlib automatically on Linux; if resolution fails, replace with pip install "jax[cpu]==0.12.0.1" (RESEARCH §3).`
8. Run every test, then commit `l0-tools: implement tools, run_all, CI`.
9. Confirm the tree is clean, then run `& $env:DUQ_PY -m tools.wrap_intro_records`, and commit `results/records/t1_*.json` as `l0-tools: wrapped intro records`. Status: DONE (§12).

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
**Production records:** 9 files, `results/records/<id>.json`, all with `task` as shown and `dirty: false`. No figures, no arrays.

| id | value ← JSON field | units | truncation | convergence | cross_check (value, rel_diff, tol) | claim display |
|---|---|---|---|---|---|---|
| `t1_0.max_abs_error.td.one_mode.a2.00` (task "1.0") | `task_1_0.a.max_abs_error_vs_analytic` 9.720044213956669e-12 | photons | `{"N":30}` | null + notes "single mode N=30, checked against analytic 4e^{-κt}" | analytic: value 0.0, rel_diff = err/4 = 2.43e-12, tol 1e-6 | `9.7e-12` |
| `t1_0.n_plateau.td.one_mode.a2.00` | `task_1_0.b.final_n_sim` 0.4998322686860546 | photons | `{"N":30}` | null + notes | analytic 0.5(1−e⁻⁸) = 0.49983226868604874, rel_diff 1.18e-14, tol 1e-9 | `0.49983` |
| `t1_0.final_n.td.one_mode.a2.10` | `task_1_0.c.final_n[1]` 4.403969346892005 (nominal κ₂) | photons | `{"N":30}` | null + notes | α² = 4.41, rel_diff 1.37e-3, tol 0.01 | `4.404` |
| `t1_1.peak_na.td.two_mode.a2.10` (task "1.1") | `task_1_1.peak_na` 6.894411732563246 | photons | `{"Na":32,"Nb":12}` | key `peak_na`, rel_tol 0.005, Na sweep (fixed Nb=14) and Nb sweep (fixed Na=40) from `task_1_2.json`; needed {Na 24, Nb 10}; converged true | `larger_truncation_same_solver` (Na40/Nb14) 6.896651439612382, rel_diff 3.25e-4, tol 0.005 | `6.8944` |
| `t1_1.steady_na.td.two_mode.a2.10` | `task_1_1.steady_na` 4.402615556547587 | photons | 32/12 | key `steady_na`, rel_tol 0.001; needed {Na 16, Nb 4}; true | α² = 4.41, rel_diff 1.67e-3 (−0.17 %), tol 0.01 | `4.4026` |
| `t1_1.settle_1pct.td.two_mode.a2.10` | `task_1_1.settle_1pct_us` 1.07 | us | 32/12 | null + notes "not swept in task_1_2; same run as converged peak/steady" | `linresp_analytic` 1.13 µs (RESEARCH §7), rel_diff 0.053, tol 0.1 | `1.07` |
| `t1_1.peak_nb.td.two_mode.a2.10` | `task_1_1.peak_nb` 1.9915204899995718 | photons | 32/12 | key `peak_nb`, rel_tol 0.005, the same two sweeps; needed {Na 16, Nb 10}; true | larger truncation 1.991554993015615, rel_diff 1.7e-5, tol 0.005 | `1.99` |
| `t1_3a.gamma_z.td.two_mode.a2.10` (task "1.3a") | `task_1_3a.parity_decay_fit_per_us` 0.5134564726057531 | 1/us | 32/12 | null + notes "single truncation ≥ task_1_2 needed; superseded by t2_2.gamma_z.td.two_mode.a2.10" | `analytic_2kappa_a_n` 0.5145525434761521, rel_diff 2.13e-3, tol 0.01 | `0.5135` |
| `t1_3a.cat_lifetime.td.two_mode.a2.10` | `task_1_3a.cat_lifetime_us` 1.9475847581102153 | us | 32/12 | null + notes | 1/(2κ_a α²) = 1.940302, rel_diff 3.75e-3, tol 0.01 | `1.95` |

**Field values:**
- `quantity`: the second id token (e.g. `gamma_z`).
- `method` values: `mesolve_vs_analytic`, `mesolve_final_value`, `mesolve_peak`, `mesolve_settle`, `mesolve_parity_fit`, `inverse_parity_fit`.
- `params` for two-mode records: `{"g2_MHz":0.763,"kappa_b_MHz":2.6,"kappa_a_kHz":9.3,"alpha":2.1,"n_th":0.0,"eps_z_over_g2":0.0,"eps_x_over_g2":0.0}`.
- `params` for t1_0: `a` `{"delta_over_2pi_MHz":1.0,"kappa_over_2pi_MHz":1.0,"alpha0":2.0}`; `b` `{"kappa_2_over_2pi_MHz":0.8957,"alpha0":2.0}`; `c` the two-mode dict plus `"kappa_2_scale":1.0`.
- `numerics` for gamma_z: `{"fit_window_us":[1.0,6.0]}`. The flat JSON has no stderr; say so in `notes`.
- Each convergence `converged` = chosen ≥ needed on both axes **and** the two largest sweep values agree within rel_tol.

**Quick vs production:**
- Quick: `--out results/quick/records` (git-ignored).
- `build_index` is run by the integrator only. Never commit `results/index.json` or `results/quick/**`.
- `task_1_2 --quick` writes `results/task_1_2_quick.json` and `figures/task_1_2_convergence_quick.png`, which are **not** git-ignored. Never commit them, and mention this in your status file.

**Jobs to queue:** none. Every step here takes seconds.

## 8. Acceptance gates (ALL must pass before DONE)
1. `tests/test_l0_tools.py` passes in < 20 s, and the full `-m "not slow"` suite has no new failures and stays < 2 min.
2. On the committed records: `build_index --records-dir results/records --out results/quick/index.json` exits 0 with `count` ≥ 9, and `check_claims` on a scratch `results/quick/claims_demo.md` holding the 9 tokens from §7 exits 0. Change one digit and it exits 1.
3. The runq demo in §9 shows two `--ram-gb 4` jobs with non-overlapping start/end times, and `status` lists both as `done`.
4. `bash -n` on `run_all.sh` succeeds. `--quick --dry-run` lists every Standard task as either a command or a `SKIP`, and ends with build_index and check_claims.
5. `git diff --name-only standard-track...HEAD` lists only §3 paths. Each of the 9 records has `provenance.dirty == false` and the script mapping from §4.
6. `tests.yml` is present. If the branch gets pushed, its Actions run is green. Otherwise write "CI unverified" in the status file.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
& $env:DUQ_PY -m pytest tests/test_l0_tools.py -q
& $env:DUQ_PY -m pytest -m "not slow" -q
& $env:DUQ_PY -m tools.wrap_intro_records --dry-run
& $env:DUQ_PY -m tools.wrap_intro_records --out results/quick/records
& $env:DUQ_PY -m tools.build_index --records-dir results/quick/records --out results/quick/index.json
& $env:DUQ_PY -m tools.check_claims --files results/quick/claims_demo.md --records-dir results/quick/records
$env:DUQ_RUNQ_DIR = "results/quick/runq"
& $env:DUQ_PY -m tools.runq submit --name demo1 --ram-gb 4 -- $env:DUQ_PY -c "import time; time.sleep(3)"
& $env:DUQ_PY -m tools.runq submit --name demo2 --ram-gb 4 -- $env:DUQ_PY -c "import time; time.sleep(3)"
& $env:DUQ_PY -m tools.runq worker --once ; & $env:DUQ_PY -m tools.runq status
Remove-Item Env:DUQ_RUNQ_DIR
$env:PY = "D:/duq-venv/Scripts/python.exe"; & "C:\Program Files\Git\bin\bash.exe" run_all.sh --quick --dry-run
git status --porcelain -- src tasks tools   # must be empty before the production wrap
& $env:DUQ_PY -m tools.wrap_intro_records    # production: results/records/t1_*.json
```

## 10. Out of scope / do not
- Do not compute physics, rerun intro tasks for production, or change any intro number. The wrapper copies values exactly.
- Do not write `tools/export_lab_data.py` (L6), `docs/results_contract.md` (not in CONTRACT §1), `pytest.ini` or `conftest.py` (l0-core), or `TECHNICAL.md` (L7).
- Do not add retries, priorities, remote execution or a PID-liveness check to runq.
- Do not import numpy, jax or dynamiqs in `tools/`.
- Do not loosen a check_claims rule to make a claim pass. A failing claim is L7's problem to fix, or to label `illustrative`.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write this in `docs/plan/status/l0-tools.md`, then continue with the next item:
```
DECISION NEEDED (l0-tools): <one line>. Options: A) <...> B) <...>. Default if no answer by <time>: A. Blocking: <what>.
```
Likely decisions:
- (a) CONTRACT §6.2 says `convergence: null` is only for truncation-independent quantities, but 5 intro records (settle_1pct, gamma_z, cat_lifetime, and the 3 one-mode N=30 records) have no sweep. Default: null + notes. The alternative is that L7 marks those claims `illustrative`.
- (b) The index shape in §4, if L6 wants something different. Default: as written here.
- (c) peak_na/peak_nb have no independent cross-check, only a larger truncation. Default: keep `larger_truncation_same_solver` and let the reviewer judge.

**Fallbacks:**
- If `git` is unavailable in a test, skip only the commit assertion.
- If `os.replace` keeps failing on Windows, write to the file directly.
- If CI cannot install jax, use the `jax[cpu]` line. If that also fails, set the job to `continue-on-error: true` and report it.

**Cut line at 7:30 PM**, in priority order: `check_claims` + `build_index` + `wrap_intro_records` (D1) > `runq` (needed for the first queued jobs, before G1 at 9:45 PM) > `run_all.sh` flags > CI. Drop `--dry-run` and the CI step first, and record what was cut.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE, `docs/plan/status/l0-tools.md` contains:
- **State:** DONE, with the commits (tests, implementation, records) as short hashes.
- **Gates:** §8, items 1–6, each ✅ or ❌ with a one-line note. Include the test count and runtime.
- **Records:** the 9 ids with their values and their `convergence` status (true or null).
- **For the integrator:** exact commands for `build_index`, `check_claims`, and `runq worker` (with `--max-jobs 3 --max-ram-gb 11`); the RAM defaults used in `run_all.sh`; the note that `task_1_2 --quick` writes untracked files into tracked dirs.
- **Open DECISION NEEDED items**, and anything cut.

Questions for Harshit (answer them yourself; the agent must not write answers):
1. The linter accepts "0.5135" for a stored 0.51345647. What exactly does it verify, and what wrong claim could still pass it? Consider a converged but physically wrong number, or a displayed precision finer than the record's uncertainty.
2. The Intro records were wrapped after the fact from flat JSONs. What do `provenance.git_commit` and `dirty: false` actually prove about how 0.5135 /µs was produced, and what don't they prove?
3. Why can only one job above 3 GB run at a time, and why 3 jobs / 11 GB on a 15.9 GB laptop? What would fail, and how would you notice, if two sparse-LU Γ_X jobs ran together?
