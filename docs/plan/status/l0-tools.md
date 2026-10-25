# Status: lane `l0-tools`

| Field | Value |
|---|---|
| State | `DONE` |
| Branch | `std/l0-tools` |
| Agent / model | Cursor agent (Claude Opus) |
| Started (EDT) | Sat Oct 24, 6:35 PM |
| Last update (EDT) | Sat Oct 24, 6:45 PM |
| Last commit | tests `8f9e31a` · implementation `8367560` · records `fd663c6` · this status file is the commit after `fd663c6` |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first: `tests/test_l0_tools.py` (test_count_sig_figs, test_matches, test_matches_zero, test_find_tokens, test_resolve_path, test_check_file_statuses, test_check_claims_exit_codes, test_build_index, test_validate_record_errors, test_build_index_default_out_refuses_when_dirty, test_wrap_intro_records, test_intro_claims_pass, test_runq_big_jobs_exclusive, test_runq_small_jobs_overlap, test_runq_failed_and_env, test_runq_lock_and_orphans, test_tools_stdlib_only, test_run_all_syntax, test_run_all_quick_dry_run). Ran before implementation: `ImportError: cannot import name 'build_index' from 'tools'` (expected). Commit `8f9e31a`.
- [x] Implementation complete (`8367560`): `tools/build_index.py`, `tools/check_claims.py`, `tools/wrap_intro_records.py`, `tools/runq.py`, `run_all.sh`, `.github/workflows/tests.yml`
- [x] `--quick` equivalent: `wrap_intro_records --out results/quick/records`, `build_index`/`check_claims` on quick dirs, `run_all.sh --quick --dry-run` (all seconds)
- [x] Production run done: `python -m tools.wrap_intro_records` on a clean tree → 9 records committed in `fd663c6`
- [x] All acceptance gates in brief §8 checked, with evidence below
- [x] Explain-back questions drafted (copied from brief §12; answers are Harshit's)

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. tests < 20 s; full fast suite no new failures, < 2 min | ✅ | `pytest tests/test_l0_tools.py -q` → `35 passed in 3.25s`; `pytest -m "not slow" -q` → `35 passed in 3.39s` (only this lane's tests exist on the branch; 0 skipped, so the git and bash checks ran too) |
| 2. build_index on committed records (count ≥ 9); claims demo exits 0; one digit changed exits 1 | ✅ | `build_index --records-dir results/records --out results/quick/index.json` → `wrote ...: 9 records`, exit 0. `check_claims --files results/quick/claims_demo.md --records-dir results/records` → `10 ok, 0 warn, 0 fail`, exit 0 (9 tokens + `#cross_check.0.value=0.5146`). `0.5135`→`0.5134` → `FAIL ... mismatch (record=0.5134564726057531)`, `9 ok, 0 warn, 1 fail`, exit 1 |
| 3. runq demo: two `--ram-gb 4` jobs non-overlapping, `status` both `done` | ✅ | `DUQ_RUNQ_DIR=results/quick/runq`, two `sleep(3)` jobs, `worker --once` → demo1 t_start 1792881562.366, t_end 1792881566.379; demo2 t_start 1792881566.380 (≥ demo1 t_end); `status` → `demo1 \| done \| 4 \| 0 \| 4.0`, `demo2 \| done \| 4 \| 0 \| 4.0` |
| 4. `bash -n run_all.sh`; `--quick --dry-run` lists every Standard task; ends with build_index + check_claims | ✅ | `bash -n` OK under macOS `/bin/bash` 3.2.57. `PY=$DUQ_PY bash run_all.sh --quick --dry-run` → intro commands, then `SKIP tasks/<t>.py (not merged yet)` for all 9 Standard tasks, last two lines `... -m tools.build_index --quick`, `... -m tools.check_claims`; exit 0 |
| 5. diff only §3 paths; 9 records `dirty == false`, script mapping per §4 | ✅ | `git diff --name-only standard-track...HEAD` → `.github/workflows/tests.yml`, `docs/plan/status/l0-tools.md`, 9× `results/records/t1_*.json`, `run_all.sh`, `tests/test_l0_tools.py`, `tools/{build_index,check_claims,runq,wrap_intro_records}.py`. All 9: `dirty=False`; scripts `tasks/task_1_0.py` (t1_0), `tasks/task_1_1.py` (t1_1), `tasks/task_1_3a.py` (t1_3a); `git_commit=b88747b` |
| 6. `tests.yml` present; CI green or "CI unverified" | ✅ | `.github/workflows/tests.yml` present (YAML parses: push to `main`/`standard-track`/`std/**` + `pull_request`, timeout 20). **CI unverified**: branch not pushed (`gh` not installed; lanes never push) |

## Commands run (most recent first)
```text
$ export DUQ_PY=$MAIN/.venv/bin/python XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
$ git diff --name-only standard-track...HEAD           # gate 5 list above
$ "$DUQ_PY" -m pytest -m "not slow" -q                 # 35 passed in 3.39s
$ bash -n run_all.sh && PY="$DUQ_PY" bash run_all.sh --quick --dry-run | tail -3
SKIP tasks/task_2_4c_pulses.py (not merged yet)
.../.venv/bin/python -m tools.build_index --quick
.../.venv/bin/python -m tools.check_claims
$ touch tools/_scratch_dirty.py; "$DUQ_PY" -m tools.wrap_intro_records; rm tools/_scratch_dirty.py
refusing to write production records to results/records: uncommitted changes in src/ tasks/ tools/   (exit 1)
$ DUQ_RUNQ_DIR=results/quick/runq2: submit eig6 --ram-gb 6, small --ram-gb 1; worker --max-jobs 2 --max-ram-gb 5 --once
runq: eig6 needs 6 GB > --max-ram-gb 5: left pending
runq: started small (pid 73693, 1 GB) / runq: small done (exit 0, 0.2 s)        (exit 1: a pending job can never fit)
$ DUQ_RUNQ_DIR=results/quick/runq: submit demo1/demo2 --ram-gb 4 -- "$DUQ_PY" -c "import time; time.sleep(3)"; worker --once; status
runq: started demo1 (pid 73588, 4 GB) / demo1 done (exit 0, 4.0 s) / started demo2 (pid 73616, 4 GB) / demo2 done (exit 0, 4.0 s)
non-overlapping: True (gap 0.001 s)
$ python3 (system 3.13, no numpy) -m tools.check_claims --files results/quick/claims_demo.md --records-dir results/records
10 ok, 0 warn, 0 fail   (exit 0)  -- tools really are stdlib-only
$ "$DUQ_PY" -m tools.check_claims --files results/quick/claims_demo_bad.md --records-dir results/records   # 0.5135 -> 0.5134
9 ok, 0 warn, 1 fail    (exit 1)
$ "$DUQ_PY" -m tools.check_claims --files results/quick/claims_demo.md --records-dir results/records
10 ok, 0 warn, 0 fail   (exit 0)
$ "$DUQ_PY" -m tools.build_index --records-dir results/records --out results/quick/index.json
wrote results/quick/index.json: 9 records   (duq.index/v1, count 9)
$ git status --porcelain -- src tasks tools   # empty
$ "$DUQ_PY" -m tools.wrap_intro_records        # production -> results/records/t1_*.json, committed fd663c6
$ "$DUQ_PY" -m tools.wrap_intro_records --out results/quick/records   # cross-check numbers match brief §7 table
$ "$DUQ_PY" -m tools.wrap_intro_records --dry-run   # 9 ids, values identical to the flat JSONs
```

## Records produced
All `dirty: false`, `git_commit: b88747b` (last commit touching the source JSONs), `wrapped_by: tools/wrap_intro_records.py`.

| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|
| `t1_0.max_abs_error.td.one_mode.a2.00` | 9.720044213956669e-12 | photons | null + notes | analytic (ref 0; rel_diff = err/4), 2.43e-12, 1e-6, true |
| `t1_0.n_plateau.td.one_mode.a2.00` | 0.4998322686860546 | photons | null + notes | analytic 0.49983226868604874, 1.18e-14, 1e-9, true |
| `t1_0.final_n.td.one_mode.a2.10` | 4.403969346892005 | photons | null + notes | semiclassical_alpha2 4.41, 1.37e-3, 0.01, true |
| `t1_1.peak_na.td.two_mode.a2.10` | 6.894411732563246 | photons | true (needed Na 24, Nb 10) | larger_truncation_same_solver 6.896651439612382, 3.25e-4, 0.005, true |
| `t1_1.steady_na.td.two_mode.a2.10` | 4.402615556547587 | photons | true (needed Na 16, Nb 4) | semiclassical_alpha2 4.41, 1.67e-3, 0.01, true |
| `t1_1.settle_1pct.td.two_mode.a2.10` | 1.07 | us | null + notes | linresp_analytic 1.13, 0.0531, 0.1, true |
| `t1_1.peak_nb.td.two_mode.a2.10` | 1.9915204899995718 | photons | true (needed Na 16, Nb 10) | larger_truncation_same_solver 1.991554993015615, 1.73e-5, 0.005, true |
| `t1_3a.gamma_z.td.two_mode.a2.10` | 0.5134564726057531 | 1/us | null + notes | analytic_2kappa_a_n 0.5145525434761521, 2.13e-3, 0.01, true |
| `t1_3a.cat_lifetime.td.two_mode.a2.10` | 1.9475847581102153 | us | null + notes | analytic_inverse_2kappa_a_alpha2 1.9403028, 3.75e-3, 0.01, true |

Claim displays that pass `check_claims` (for L7): `9.7e-12`, `0.49983`, `4.404`, `6.8944`, `4.4026`, `1.07`, `1.99`, `0.5135`, `1.95`, plus `rec:t1_3a.gamma_z.td.two_mode.a2.10#cross_check.0.value=0.5146`.

## Figures / arrays produced
- none (by design)

## For the integrator
- **Index:** `"$DUQ_PY" -m tools.build_index` (writes `results/index.json`; refuses with exit 1 while `git status --porcelain -- src tasks tools` is non-empty, and writes nothing if any record is invalid). Quick: `--quick` (→ `results/quick/index.json`).
- **Claims:** `"$DUQ_PY" -m tools.check_claims --files TECHNICAL.md README.md [--strict]`. Exit 0 iff no fail (`--strict`: no warn either).
- **Worker:** brief says `--max-jobs 3 --max-ram-gb 11`; **on this 8 GB Mac use `"$DUQ_PY" -m tools.runq worker --max-jobs 2 --max-ram-gb 5`** (RUNBOOK §3). Submit: `"$DUQ_PY" -m tools.runq submit --name <job> --ram-gb <est> [--cwd <repo>] -- <cmd ...>`; status: `"$DUQ_PY" -m tools.runq status`.
- **RAM defaults printed by `run_all.sh` (full mode):** `task_2_1_eig` 6 GB, every other Standard task 2 GB, `task_1_2` 2 GB. With `--max-ram-gb 5` a 6 GB job is never started: the worker prints `needs 6 GB > --max-ram-gb 5: left pending` and leaves it pending (`--once` then returns 1). Resubmit at ≤ 5 GB, or run that worker with a higher cap while nothing else runs.
- **`task_1_2 --quick`** (run by `run_all.sh --quick`) writes `results/task_1_2_quick.json` and `figures/task_1_2_convergence_quick.png` into **tracked** directories (not git-ignored). Never commit them.
- `run_all.sh` full mode ends with `build_index` on the default output, so it exits 1 on a tree with uncommitted `src/ tasks/ tools/` changes (by design). `check_claims`'s exit code is the script's exit code in full mode; in `--quick` mode it is printed and ignored.
- Job wall times are quantised by the worker poll interval (default 2 s): a 3 s job shows `wall_s` 4.0.

## Jobs to queue (for the integrator; jobs > 15 min)
None. Every step in this lane takes seconds.

## Deviations from the brief (and why)
- `build_index` refuses (exit 1) to write the **default** `results/index.json` while `src/ tasks/ tools/` are dirty. My brief does not list this, but the integrator brief §4 relies on it ("With the default `--out` it refuses (exit 1) while `git status --porcelain -- src tasks tools` is non-empty"). Explicit `--out` and `--quick` are never blocked. Tested by `test_build_index_default_out_refuses_when_dirty`.
- `validate_record` treats `"cross_check": null` as absent (valid), so a record written by `src.results.record(cross_check=None)` is not rejected by the index. `check_claims` still fails any claim on such a record ("no agreeing cross_check").
- `runq worker`: a pending job whose `ram_gb` exceeds `--max-ram-gb` can never start; it stays `pending` with a one-time warning instead of blocking `--once` forever (`--once` returns 1 in that case, 0 when the queue is empty). Added a `--force` flag (ignore a stale `worker.lock`), as the brief's lock rule mentions. `--poll-s` is also exposed on the CLI.
- `runq submit` records `cwd` as the absolute submit-time directory when `--cwd` is not given, and `log` as an absolute path, so a worker started elsewhere still runs the job in the right place.
- `run_all.sh` `cd`s to its own directory first and prints `SKIP tasks/<t>.py (not merged yet)` in full mode too (not only `--quick`).
- Cross-check references that need κ_a or κ_b use literal RESEARCH values (`2κ_a = 0.116867 /µs`, settle 1% = 1.13 µs, α² = 4.41) so `tools/` never applies the 2π.

## DECISION NEEDED
Both are non-blocking; the brief's defaults are applied and committed.

> DECISION NEEDED (l0-tools): 6 intro records carry `convergence: null` although CONTRACT §6.2 reserves null for truncation-independent quantities (settle_1pct, gamma_z, cat_lifetime and the three one-mode N=30 records; none was swept). Options: A) keep null + notes (each note says why and, for gamma_z/cat_lifetime, that `t2_2.gamma_z.td.two_mode.a2.10` supersedes them) B) L7 marks claims on those 6 records `illustrative`. Default if no answer by G1: A. Blocking: nothing (records committed with A; `check_claims` passes them because notes are non-empty).

> DECISION NEEDED (l0-tools): `t1_1.peak_na` / `t1_1.peak_nb` have no independent cross-check, only the same solver at a larger truncation (Na=40, Nb=14). Options: A) keep `larger_truncation_same_solver` (notes say "not fully independent") and let the reviewer judge B) L7 cites those two numbers as `illustrative` C) add an independent check later (no analytic prediction exists for the transient peak; the 56% overshoot is a large-signal effect, RESEARCH §7). Default if no answer by G1: A. Blocking: nothing.

Index shape (brief §11 b): implemented exactly as the brief defines (`duq.index/v1`, `generated_at`, `count`, `records` sorted by id); the L6 brief already reads this shape, so no decision is open.

Nothing was cut.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. The linter accepts "0.5135" for a stored 0.51345647. What exactly does it verify, and what wrong claim could still pass it? Consider a converged but physically wrong number, or a displayed precision finer than the record's uncertainty.
2. The Intro records were wrapped after the fact from flat JSONs. What do `provenance.git_commit` and `dirty: false` actually prove about how 0.5135 /µs was produced, and what don't they prove?
3. Why can only one job above 3 GB run at a time, and why 3 jobs / 11 GB on a 15.9 GB laptop? What would fail, and how would you notice, if two sparse-LU Γ_X jobs ran together?

## Notes for Claude's later review
- `check_claims` compares strings at the displayed significant figures, exactly per brief (`f"{v:.{n-1}e}"`). It does **not** compare the displayed precision with `uncertainty`; a claim shown with more digits than the record supports still passes (question 1 above).
- The wrapped `dirty: false` is asserted by the wrapper (it refuses to write `results/records` on a dirty tree), not measured at the time the intro numbers were produced. `git_commit` is the last commit that touched each source JSON (`b88747b`), not the commit of the code that ran (question 2).
- `t1_3a.gamma_z` comes from a pure-exponential parity fit (no offset), which RESEARCH §6 calls biased; the record's notes say so and point to the l2a superseding record. The wrapper copies the value unchanged by design.
- No tolerance was loosened; every cross-check value and rel_diff matches the brief §7 table.
- `run_all.sh` was checked with macOS `/bin/bash` 3.2 (no arrays, so the `set -u` empty-array pitfall does not apply).
