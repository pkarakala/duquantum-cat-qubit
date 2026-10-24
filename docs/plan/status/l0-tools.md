# Status: lane `l0-tools`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (tests written) |
| Branch | `std/l0-tools` |
| Agent / model | Cursor agent (Claude Opus) |
| Started (EDT) | Sat Oct 24, 6:35 PM |
| Last update (EDT) | Sat Oct 24, 6:40 PM |
| Last commit | `27a3378` (branch point, `standard-track`) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first: `tests/test_l0_tools.py` (test_count_sig_figs, test_matches, test_matches_zero, test_find_tokens, test_resolve_path, test_check_file_statuses, test_check_claims_exit_codes, test_build_index, test_validate_record_errors, test_build_index_default_out_refuses_when_dirty, test_wrap_intro_records, test_intro_claims_pass, test_runq_big_jobs_exclusive, test_runq_small_jobs_overlap, test_runq_failed_and_env, test_runq_lock_and_orphans, test_tools_stdlib_only, test_run_all_syntax, test_run_all_quick_dry_run). Ran before implementation: `ImportError: cannot import name 'build_index' from 'tools'` (expected).
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. tests < 20 s; full fast suite no new failures, < 2 min | | |
| 2. build_index on committed records (count ≥ 9); check_claims demo exits 0, one digit changed exits 1 | | |
| 3. runq demo: two `--ram-gb 4` jobs non-overlapping, `status` shows both `done` | | |
| 4. `bash -n run_all.sh`; `--quick --dry-run` lists every Standard task, ends with build_index + check_claims | | |
| 5. diff only §3 paths; 9 records `dirty == false`, script mapping per §4 | | |
| 6. `tests.yml` present; CI green or "CI unverified" | | |

## Commands run (most recent first)
```text
(none yet)
```

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|

## Figures / arrays produced
- none (by design)

## Jobs to queue (for the integrator; jobs > 15 min)
None. Every step in this lane takes seconds.

## Deviations from the brief (and why)
-

## DECISION NEEDED
(none yet)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. The linter accepts "0.5135" for a stored 0.51345647. What exactly does it verify, and what wrong claim could still pass it? Consider a converged but physically wrong number, or a displayed precision finer than the record's uncertainty.
2. The Intro records were wrapped after the fact from flat JSONs. What do `provenance.git_commit` and `dirty: false` actually prove about how 0.5135 /µs was produced, and what don't they prove?
3. Why can only one job above 3 GB run at a time, and why 3 jobs / 11 GB on a 15.9 GB laptop? What would fail, and how would you notice, if two sparse-LU Γ_X jobs ran together?

## Notes for Claude's later review
-
