# Status: lane `l3-prep`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l3-prep` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 10:18 |
| Last update (EDT) | 2026-10-25 10:40 |
| Last commit | (this commit) cutoff before production |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH
- [x] Tests written first: `test_eps_z_cannot_select_well`, `test_eps_x_selects_right_well`, `test_p_right_well_bounds`, `test_metrics_extra_on_coherent`, `test_pulse_displacement_analytic`, `test_lab_frames_orientation`, `test_ideal_displacement_fidelity` (slow), `test_lab_frames_npz_schema` (slow)
- [x] Runners implemented: `metrics_extra`, `run_ideal`, `run_pulse` (pump off), `run_biased`, `tasks/task_lab_frames.py`
- [ ] `--quick` run — not started (would be a mesolve; stopped for the 10:45 cap)
- [ ] Production run(s) — not started
- [ ] Acceptance gates — only the fast symmetry / metric / pulse / Wigner-layout checks were eligible
- [x] Explain-back questions drafted (brief §12, unanswered)

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| 1 fast tests | see Commands | slow tests not run |
| 2 ε_Z max\|Re⟨a⟩\| < 1e-12 | pass on the fast test | `test_eps_z_cannot_select_well` (12×4, 0.5 µs). Printed max not copied from a production trace; the test asserts < 1e-12 |
| 3 r = 0 control and Im⟨a⟩ | not run | needs method (iii) |
| 4 analytic ⟨a⟩(τ) | fast test only, one (ε_x, τ) | `test_pulse_displacement_analytic`, τ = 0.05 µs, ε_x = 20, 16×2, pump off. The four production τ values were not run |
| 5 F and p_right at 3 µs | not run | |
| 6 biased p_right grows with r | not run | |
| 7 truncation, convergence, dirty=false | no v2 records | |
| 8 lab npz 39×81×81 | not run | `main` is implemented; `as_iy_ix` is tested |
| 9 figures | absent | |
| 10 cost table + check_claims | doc written, table empty on purpose | no `rec:` tokens, so there is nothing to mismatch |
| 11 notebook | executed | `jupyter nbconvert --execute --inplace notebooks/05_task_1_3b_prepare_zero.ipynb` reads `results/task_1_3b.json` only. It does not show the missing production figures |

## Commands run (most recent first)
```text
$DUQ_PY -m pytest tests/test_l3_prep.py -m "not slow" -q --tb=short
6 passed, 2 deselected in 23.21s
# includes test_eps_z_cannot_select_well (max|Re<a>| < 1e-12) and
# test_pulse_displacement_analytic (pump off, relative 1e-6)
# Slow tests were not started (24×8 for 3 µs, and the lab-frame mesolve).
```

## Records produced
| Record id | Value | Units | Converged | Cross-check |
|---|---|---|---|---|
| none | | | | |

Intro anchor, not a v2 record: `results/task_1_3b.json` F(β=α, t=2 µs) = 0.9999915936048853 at Na=32, Nb=12. That is method (i) run for 2 µs. Our `run_ideal` was not executed, so it was not reproduced.

## Figures / arrays produced
- None new. Do not treat `results/task_1_3b.json` as a v2 record.

## Jobs to queue
| Name | Command (from the worktree root) | RAM est. (GB) | Wall est. | Outputs |
|---|---|---|---|---|
| t1_3b_ideal_pulse | `python -m tasks.task_1_3b --methods ideal,pulse` | 2 | not measured; brief estimate 15–17 min on the Windows laptop. `main` currently returns without solving | traces, 10 records |
| t1_3b_biased | `python -m tasks.task_1_3b --methods biased` | 2 | brief estimate 30–40 min | 24 records |
| lab frames | `python -m tasks.task_lab_frames` | 2 | brief ~1 min | `results/arrays/lab.inflation_wigner.npz` |

`main` does **not** solve. Wiring records, convergence blocks, figures and `--write-table` is still to do. Do not fill `docs/task_1_3c.md` from a quick run.

## Deviations from the brief
- Hard stop at 10:45 EDT. No mesolve longer than the fast tests.
- Method (ii) is pump-off. `pump_on=True` is implemented and is not the reported protocol. Pranav's intro drive was pump-on.
- `main(Na, Nb)` from `notebooks/05_task_1_3b_logical_prep.ipynb` now raises. That notebook is not on this lane's allowlist. Its JSON result is untouched.
- No stretch (`pumpon` record, `area0.5`).

## DECISION NEEDED
None. The missing pieces are runtime, not a physics choice.

## Explain-back for Harshit (questions only)
1. The drive ε(a+a†) visibly moves ⟨a⟩, yet it can never prepare |+α⟩ from vacuum. Which symmetry forbids it? What exactly does that symmetry force about ⟨a⟩? And why does ε_x·i(a†−a) escape it?
2. Method (ii) calibrates the pulse area to ε_x·τ = α. If the area is 20% off, or the drive phase is rotated by 30°, what final state does the stabilization produce? What kind of calibration error *would* actually ruin the preparation?
3. In method (iii), why does a weak ε_x matter so much in the first ~0.2 µs of inflation and so little afterwards? And what does leaving it on longer cost you, in terms of leakage, the well shift ≈ ε_x/(2κ₂α²), and fidelity versus p_right?

## Notes for Claude's later review
- Do not loosen 1e-12 on Re⟨a⟩ under ε_Z.
- Do not quote quick numbers in `docs/task_1_3c.md`.
- Chosen truncation stays (32, 12) unless a sweep fails. If the vacuum-inflation `top_b` exceeds 1e-4 (intro Task 1.1 saw 1.69e-4 at 32×12), report it; do not move the truncation silently.
- **Note for l6-lab:** npz not written. The writer is `tasks/task_lab_frames.py`. Contract: `frames[k, iy, ix]`, `x = Re α` (dynamiqs ħ = 1/2), 39 frames, keys in brief §4.
- **Note for l7-docs:** the 1.3c text and the "got wrong first" section are in `docs/task_1_3c.md`. The auto table is intentionally empty.
