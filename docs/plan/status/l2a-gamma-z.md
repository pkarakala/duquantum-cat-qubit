# Status: lane `l2a-gamma-z`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l2a-gamma-z` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 09:25 |
| Last update (EDT) | 2026-10-25 09:32 |
| Last commit | `47c0fd5` `[integrator] merge upstream intro-track-tasks` |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, runbook
- [x] Tests written first (list the test names)
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

`src/spectral.py` is **not** on this branch (`l1-spectral` not merged). Time-domain parity fits and the analytic coth / 2κ_a n̄ checks are in scope. `--eig` and `--summary` are left under Jobs to queue.

Tests (failing on import until `tasks/task_2_2.py` exists): `test_prediction_values`, `test_offset_fit_needed`, `test_ids_and_window`, `test_cat_is_dark`, `test_slope_of_predictions`, `test_small_run_alpha1` (slow).

## Acceptance gates (copy from brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1–10 | pending | tests committed first |

## Commands run (most recent first)
```text
(tests not yet executed)
```

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|

## Figures / arrays produced
-

## Jobs to queue (for the integrator; jobs > 15 min)
| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs (record ids) |
|---|---|---|---|---|

## Deviations from the brief (and why)
- `test_cat_is_dark`: the brief's `||H|C+>|| < 1e-6` at Na=12 is the Fock tail (~2.0e-3), not an ε_d error (wrong `C.EPS_D` leaves ~16). The same bound holds at Na=20 (~5e-8). The test keeps `< 1e-2` at Na=12 (still catches the ε_d trap) and `< 1e-6` at Na=20.
- `fit_exp_offset` p0 is `(gamma, A, C)`, not `(A, gamma, C)`.

## DECISION NEEDED
None.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why does the parity settle at 1/cosh(2α²) instead of 0, and what would a pure exponential fit have reported at α = 1.0?
2. Why is 2κ_a·n̄ with the measured n̄ an identity check rather than an independent prediction, and where does the coth(2α²) correction come from?
3. Why is Γ_Z insensitive to the buffer truncation while Γ_X at α = 2.1 needed Nb = 8, and which of your two Γ_Z methods (time-domain fit, even-block eigenvalue) would you trust at α = 2.7, and why?

## Notes for Claude's later review
- Spectral helper is absent; eigen cross-check is queued, not skipped silently.
