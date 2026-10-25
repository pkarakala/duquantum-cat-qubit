# Review `l0-tools` round 1: PASS

| Lane | Reviewed commit | Base | Reviewer model | Start–end (EDT) | Prior rounds |
|---|---|---|---|---|---|
| `l0-tools` | `539046c` (`std/l0-tools`, detached) | review branch cut from `standard-track` `0a2040b`; lane merge-base `27a3378` | Grok 4.7 | Sat Oct 24 2026, 6:55 PM – 7:05 PM | none (prior launch died before writing a review file) |

## Verdict

PASS. Blocking findings: none. Rule: FAIL if any critical/major; PASS_WITH_NOTES if only minor; PASS if none.

Both defaults the lane flagged are acceptable for this intro-wrapper set. See Notes. The lane has nothing to change before merge.

## Stage 1 findings

| Item | Result | Evidence |
|---|---|---|
| S1-1 Allowlist | OK | `git diff --name-only standard-track...HEAD` is 17 paths: the four tools, `run_all.sh`, `.github/workflows/tests.yml`, `tests/test_l0_tools.py`, `docs/plan/status/l0-tools.md`, and the nine `results/records/t1_*.json` from brief §7. That is CONTRACT §1 ∪ the status file ∪ the lane's own records. `git diff --diff-filter=D --name-only` is empty. `git log --merges standard-track..HEAD` is empty (four commits: `8f9e31a` tests, `8367560` implementation, `fd663c6` records, `539046c` status). |
| S1-2 Completeness | OK | Brief §4 functions are present (`validate_record`, `build_index`, `count_sig_figs`, `matches`, `resolve_path`, `find_tokens`, `check_file`, `queue_dir`, `submit`, `load_jobs`, `worker`, `status_table`, `build_records`, `write_records`, each `main`). `converged_at` in `tools/wrap_intro_records.py:31-38` matches `tasks/task_1_2.py:47-53` (one comment added). Every §5 test name exists. All nine §7 ids exist. No figures, arrays, or notebooks were required. Jobs to queue: none. |
| S1-3 Nothing extra | OK | No `tools/__init__.py`, no new dependency, no extra record id, no committed `results/index.json` or `results/quick/`. `git diff 8f9e31a..HEAD -- tests/test_l0_tools.py` is empty (tests were not rewritten after they landed). Disclosed additions stay inside the specified CLIs: `--poll-s` exposes the `poll_s` argument; default-out dirty refusal is what integrator brief §4 requires; `cross_check: null` is treated as absent (`tools/build_index.py:50-52`) while `check_claims` still fails a claim on that record. |
| S1-4 Status file | OK | `docs/plan/status/l0-tools.md` on `539046c`: `State: DONE`, gates 1–6 with commands and output, records table, deviations, Jobs to queue "none", three explain-back questions and no answers. CI is marked unverified (branch not pushed). Both DECISION NEEDED blocks are copied in Notes below. |

## Stage 2 findings

Physics items are N/A for this tools lane except the wrapped intro values, which were checked against the flat JSONs and the brief §7 table. Line numbers are on `539046c`.

| Item | Result | Evidence |
|---|---|---|
| S2-1 2π only in config | OK | `git grep` of `TWO_PI` and `2 * {jnp,np,math}.pi` over `tools/`, `tests/test_l0_tools.py`, `run_all.sh`, `.github/` is empty. Cross-check literals `ALPHA2 = 4.41`, `TWO_KAPPA_A = 0.116867`, `SETTLE_1PCT_LINRESP_US = 1.13` are copied numbers (`tools/wrap_intro_records.py:23-26`). |
| S2-2 Jump operators | N/A | No Hamiltonian and no jump operators. `test_tools_stdlib_only` passed: the four modules import stdlib, `tools`, or (allowed, unused) `src.convergence`. |
| S2-3 Sign of α² | N/A | No model build. The wrapper's α² reference is the positive literal 4.41. |
| S2-4 Drive quadrature | OK | `git grep -i` of `tilt`, "prepares a well", and "selects a well" over `tools/`, `tests/test_l0_tools.py`, and `run_all.sh` is empty. Wrapped params set `eps_z_over_g2` and `eps_x_over_g2` to 0 (`tools/wrap_intro_records.py:27-28`). |
| S2-5 Symmetry tests | N/A | Brief §5 has no mesolve symmetry test. This lane does not propagate states. |
| S2-6 Convergence blocks | OK | Three records carry separate Na and Nb sweeps and `converged: true`. Recomputed from `results/task_1_2.json` with an inline copy of `converged_at` (not the wrapper): `peak_na` needed {Na: 24, Nb: 10} (Na tail rel 1.027e-5, Nb tail rel 3.221e-4, rel_tol 0.005); `peak_nb` {Na: 16, Nb: 10}; `steady_na` {Na: 16, Nb: 4} (rel_tol 0.001). Na is swept at fixed Nb=14, Nb at fixed Na=40. Chosen truncation on the records is 32×12, which is ≥ needed on both axes. The other six records are `convergence: null` with notes. That default is acceptable under CONTRACT §11.4; see Notes. |
| S2-7 Eigen acceptance | N/A | No `.eig.` record and no spectral code. |
| S2-8 Fits | N/A | The wrapper does not fit. `t1_3a.gamma_z` copies the intro value and stores `numerics.fit_window_us = [1.0, 6.0]` (`results/records/t1_3a.gamma_z.td.two_mode.a2.10.json:24-28`). The note (`:43`) says the flat JSON has no stderr and that the fit is a pure exponential. Brief §7 forbids inventing a stderr. Refitting belongs to `l2a-gamma-z`. |
| S2-9 Rate conventions | N/A | No Γ_X / Γ_Z definition in this lane. The copied Γ_Z is 0.5134564726057531 /µs. Its cross-check reference is the intro JSON's 2κ_a n̄, 0.5145525434761521 (stored rel_diff 0.002130143722532739, tol 0.01). 2κ_a α² = 0.116867×4.41 = 0.51538347 is a different number; the lifetime record uses 1/(2κ_a α²) = 1.9403028, as brief §7 specifies. |
| S2-10 Units | OK | photons, us, and 1/us match brief §7. Two-mode `params` match the brief dict, including `eps_*_over_g2: 0`. `t1_0` params match the three brief dicts. |
| S2-11 Provenance | OK | Validator below: 9 ok, exit 0. Every record has `dirty: false`, `git_commit: b88747b` (last commit of each source JSON; ancestor of HEAD), `script` mapped through `INTRO`. No hostname or username in the JSON (checked `USER`, `USERNAME`, `LOGNAME`, `COMPUTERNAME`, and the machine hostname). `platform` is null, which is the brief §6 wrapper template. `wrapped_at` `2026-10-24T22:39:02Z` sits on the `fd663c6` commit (`18:39:03 -0400`), after the code commit `8367560` (`18:38:57 -0400`). Rebuilding with `build_records` matches the nine committed files aside from `wrapped_at`. |
| S2-12 Tests assert the spec | OK | Assertions are exact: sig-fig table, match and mismatch pairs, token id/path/disp, every §5 status (missing, mismatch, bad path, unparseable, converged false, null without notes, null with notes, no agree, empty cross_check, dirty, illustrative→warn), exit codes including `--strict`, index order and invalid-record refusal, exact JSON equality for nine ids, needed truncations, big-job `t_start >= t_end`, small-job overlap, failed job not retried, `XLA_FLAGS` contains `intra_op_parallelism_threads=2`. `35 passed in 3.35s`. |
| S2-13 `--quick` | OK | This lane has no physics task script. `bash run_all.sh --quick --dry-run` returned in 0.03 s, listed every Standard task as `SKIP ... (not merged yet)`, and ended with `tools.build_index --quick` then `tools.check_claims`. `build_index --quick` targets `results/quick/index.json`. Production wrap refuses a dirty `src/ tasks/ tools/` tree (`tools/wrap_intro_records.py:202-207`). |
| S2-14 No swallowed errors | OK | No `except:`, no `except Exception`, no `os.kill`. Each handler records the failure, returns nonzero, retries `os.replace`, or refuses the write. `build_index` prints a warning and continues if `git status` itself fails (`tools/build_index.py:101-103`); the wrapper refuses in that case. |
| S2-15 Figures | N/A | Brief §7: no figures. |

### Findings

None.

## Commands run + results

Environment: `DUQ_PY=$MAIN/.venv/bin/python`, `XLA_FLAGS` two threads, `MPLCONFIGDIR=$MAIN/.orchestrator/mplconfig`. Working directory: `.worktrees/review-l0-tools`. `GEMINI_API_KEY` unset; Gemini was not run.

```text
git rev-parse --short HEAD          # 539046c (before the review branch was cut)
git log --oneline standard-track..HEAD
  539046c [l0-tools] status: DONE with gate evidence
  fd663c6 [l0-tools] wrapped intro records
  8367560 [l0-tools] implement tools, run_all, CI
  8f9e31a [l0-tools] tests first
git diff --diff-filter=D --name-only standard-track...HEAD   # empty

"$DUQ_PY" -m pytest tests/test_l0_tools.py -q --tb=line
  35 passed in 3.35s
"$DUQ_PY" -m pytest -m "not slow" -q --tb=line
  35 passed in 3.17s
  # tests/ on this branch contains only test_l0_tools.py (l0-core is not merged). No test file was deleted.

bash -n run_all.sh                   # ok
bash run_all.sh --quick --dry-run    # real 0.03s; intro order task_1_0, task_1_2 --quick, task_1_1, task_1_3a;
                                     # SKIP for all 9 Standard tasks; last lines build_index --quick, check_claims

"$DUQ_PY" -m tools.wrap_intro_records --dry-run
  t1_3a.gamma_z.td.two_mode.a2.10 = 0.5134564726057531 1/us
  # and the other eight ids, values identical to brief §7

"$DUQ_PY" -m tools.build_index --records-dir results/records --out $TMPDIR/duq-review/index.json
  wrote ...: 9 records
  schema duq.index/v1, count 9, ids sorted, generated_at 2026-10-24T23:03:31Z
```

Records validator (brief 91 §9 script, plus a hostname scan). Exit 0.

```text
ok    t1_0.final_n.td.one_mode.a2.10            4.403969346892005     photons
ok    t1_0.max_abs_error.td.one_mode.a2.00      9.720044213956669e-12 photons
ok    t1_0.n_plateau.td.one_mode.a2.00          0.4998322686860546    photons
ok    t1_1.peak_na.td.two_mode.a2.10            6.894411732563246     photons
ok    t1_1.peak_nb.td.two_mode.a2.10            1.9915204899995718    photons
ok    t1_1.settle_1pct.td.two_mode.a2.10        1.07                  us
ok    t1_1.steady_na.td.two_mode.a2.10          4.402615556547587     photons
ok    t1_3a.cat_lifetime.td.two_mode.a2.10      1.9475847581102153    us
ok    t1_3a.gamma_z.td.two_mode.a2.10           0.5134564726057531    1/us
```

CONTRACT §11 steps, as implemented and as exercised by `tests/test_l0_tools.py:128-168` and the spot-checks:

1. Token regex `tools/check_claims.py:14-15`; `find_tokens` is 1-based and keeps the line (`:54-60`).
2. Missing file is a warn (`:96-98`). Missing record is `"missing record"` (`:110-111`).
3. Significant figures: mantissa, drop sign and dot, strip leading zeros, trailing zeros count (`:20-24`). `matches` compares `f"{v:.{n-1}e}"` strings (`:27-34`). Displayed `0` matches only `v == 0` (`n == 0`). Unparseable disp → `"unparseable"` (`:73-74`).
4. Absent convergence, or `converged is not True`, → `"not converged"` (`:77-83`). The only pass is `convergence is None` plus a non-empty string `notes`.
5. Some `cross_check` entry must have `agree is True` (`:84-86`). Rules 4–6 run for `#path` tokens too (`_check` does not return early after a path match).
6. `provenance.dirty is False` required (`:87-89`).
7. ASCII table and `N ok, M warn, K fail` (`:129-142`). Exit 0 iff no fail; `--strict` also rejects warns (`:152-154`). A line containing `illustrative` turns a fail into a warn (`:117-118`).

`runq`: a job with `ram_gb > 3` starts only when no other big job is running (`tools/runq.py:151-160`). `test_runq_big_jobs_exclusive` asserts the later `t_start >=` the earlier `t_end` even though 8 GB ≤ 11 GB. Only `state == "pending"` jobs are started (`:148`); a nonzero exit stays `failed` (`:108-115`) and is not queued again. No `os.kill`. Lock is `O_CREAT|O_EXCL`, exit 2 if held, removed in `finally` (`:124-133`, `:167-168`). Orphans become `failed` / `orphaned (worker restarted)` (`:137-141`).

## Independent spot-checks

| Quantity | Lane value (record id) | Independent value | Method | rel_diff | tol | OK |
|---|---|---|---|---|---|---|
| Γ_Z intro fit | 0.5134564726057531 (`t1_3a.gamma_z.td.two_mode.a2.10`) | 0.5134564726057531 (`results/task_1_3a.json` field `parity_decay_fit_per_us`) | exact copy of the committed flat JSON | 0 | 0 | OK |
| Claim token at 4 sig figs | same record | `=0.5135` exit 0 (`1 ok, 0 warn, 0 fail`); `=0.5134` exit 1, reason `mismatch (record=0.5134564726057531)` | `python -m tools.check_claims` on scratch files under `$TMPDIR/duq-review`, `--records-dir results/records` | string match `5.135e-01` vs `5.134e-01` | exact | OK |
| Nine brief displays plus `#cross_check.0.value=0.5146` | the nine committed records | `10 ok, 0 warn, 0 fail`, `--strict` exit 0 | same linter | — | exact | OK |
| Plateau analytic | cross-check ref 0.49983226868604874 (`t1_0.n_plateau.td.one_mode.a2.00`) | 0.5(1−e^{−8}) = 0.49983226868604874 | `math.exp` | 0 | 0 | OK |
| `peak_na` needed | {Na: 24, Nb: 10}, converged true | same numbers from `results/task_1_2.json` | inline `converged_at` on the sweep rows | 0 | exact | OK |

The same JSON-copy check was done for all nine values (`wrap --dry-run` and `build_records` vs the committed files). Γ_Z stored rel_diff 0.002130143722532739 equals `|0.5134564726057531 − 0.5145525434761521| / 0.5145525434761521`.

## Notes for Claude's later review

- Abbreviated: no. Stage 1, the validator, fast tests, the 2π grep, the drive-quadrature grep, the dirty check, and both required spot-checks were run. Physics propagation (S2-2, S2-3, S2-5, S2-7, S2-8, S2-9) is N/A because this lane does not build a Liouvillian or fit a trace. The wrapped numbers were checked.
- `l0-core` is not merged. Expected: this lane's brief depends on CONTRACT text only. `standard-track` has since gained `ed67136` (setup) and `0a2040b` (integrator). The lane does not contain those commits. Its merge-base is `27a3378`.
- Code defaults stay on CONTRACT §12: worker `--max-jobs 3 --max-ram-gb 11`, big job `ram_gb > 3`, `task_2_1_eig` printed at 6 GB. The lane status tells this 8 GB machine to invoke `--max-jobs 2 --max-ram-gb 5`. Under that cap a 6 GB job stays pending and `--once` returns 1. That is the right split (contract defaults in code, machine cap on the command line).
- `t1_3a.gamma_z` is the intro pure-exponential parity fit. RESEARCH §6 calls that fit biased (steady parity is 1/cosh(2α²)). The record note says so and points at `t2_2.gamma_z.td.two_mode.a2.10`. The wrapper was required to copy the value. L7 should keep that caveat when it cites `0.5135`.
- `provenance.dirty: false` and `git_commit: b88747b` mean the wrapper ran against the intro JSON commit while `src/ tasks/ tools/` were clean. They do not record the interpreter that produced the intro number. The status file already says this.
- CI was not run (no push). Status says "CI unverified". `.github/workflows/tests.yml` matches brief §6 step 7 (push branches, `pull_request`, `ubuntu-latest`, timeout 20, checkout `fetch-depth: 0`, Python 3.12, the jax comment, `python -m pytest -m "not slow" -q`).

### Decision (a): `convergence: null` on six intro records — acceptable

Records: `t1_0.max_abs_error`, `t1_0.n_plateau`, `t1_0.final_n` (one-mode N=30), `t1_1.settle_1pct`, `t1_3a.gamma_z`, `t1_3a.cat_lifetime`. The brief's "5" is a miscount; the §7 table and the status file list these six.

CONTRACT §6.2 says to use null for quantities that do not depend on truncation, with notes that say so. CONTRACT §11.4 says a claim passes when `converged == true`, or when convergence is null and notes justify it. The linter implements §11.4 (`tools/check_claims.py:77-81`).

**Judgment: acceptable. Ship option A. Blocking merge: no.**

- Each note is non-empty and states the real reason (single N=30 checked against an analytic formula; settle time not swept in `task_1_2`; gamma_z and lifetime are one truncation and are superseded by `t2_2.gamma_z.td.two_mode.a2.10`).
- `--strict` on the nine brief display tokens exits 0, including those six.
- The intro runs are already committed. Brief §10 forbids rerunning them, so there is no sweep to store. Writing `converged: true` without a sweep would be a false convergence flag.
- These six are unswept mesolve outputs, so they are outside §6.2's examples (analytic values, Felis). The notes do not call them truncation-independent. §11.4 still allows them, and the brief §7 table requires this shape. The acceptance is only for these six wrapped intro records. A later lane that publishes a truncation-dependent rate still needs a real convergence block.
- Each of the six has an agreeing cross-check with a stated tolerance (analytic plateau, α², linear-response 1.13 µs, 2κ_a n̄, 1/(2κ_a α²)).

### Decision (b): `peak_na` / `peak_nb` cross-check is a larger truncation of the same solver — acceptable

**Judgment: acceptable. Ship option A. Blocking merge: no.**

- §11.5 and the validator require an agreeing cross-check whose `agree` equals `rel_diff <= tol`. Both records meet that: `larger_truncation_same_solver`, rel_diff 3.2475e-4 (`peak_na`) and 1.733e-5 (`peak_nb`), tol 0.005, `agree: true`. The reference is the `task_1_2` corner Na=40, Nb=14 (`6.896651439612382` and `1.991554993015615`).
- That corner is the same mesolve, and it is already the last point of both sweeps. The notes say "not fully independent" (`results/records/t1_1.peak_na.td.two_mode.a2.10.json:90` and the `peak_nb` twin).
- Truncation support is the convergence block, recomputed above, with Na and Nb swept separately and `converged: true` at rel_tol 0.005. That block is what L7 should cite.
- RESEARCH §7: the inflation overshoot is a large-signal effect and has no linear-response formula. Brief §10 forbids a new physics run, so an independent solver check is outside this lane.
- L7 should describe the method as a larger truncation of the same solver. The `illustrative` label is not required for these two records to be merged.

Claude still logs the confirmation in `docs/plan/status/integrator.md` (REVIEW_PROTOCOL §3). Recommendation: accept A for both. Nothing in this review is waiting on that log.

### Explain-back questions (questions only; Harshit answers in `docs/defense.md`)

1. The linter accepts `0.5135` for a stored 0.51345647. What exactly does it verify, and what wrong claim could still pass it? Consider a converged but physically wrong number, or a displayed precision finer than the record's uncertainty.
2. The Intro records were wrapped after the fact from flat JSONs. What do `provenance.git_commit` and `dirty: false` actually prove about how 0.5135 /µs was produced, and what don't they prove?
3. Why can only one job above 3 GB run at a time, and why 3 jobs / 11 GB on a 15.9 GB laptop? What would fail, and how would you notice, if two sparse-LU Γ_X jobs ran together?
