# Status: lane `l3-prep`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l3-prep` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 10:18 |
| Last update (EDT) | 2026-10-25 10:25 |
| Last commit | `47c0fd5` `[integrator] merge upstream intro-track-tasks` |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH
- [x] Tests written first: `test_eps_z_cannot_select_well`, `test_eps_x_selects_right_well`, `test_p_right_well_bounds`, `test_metrics_extra_on_coherent`, `test_pulse_displacement_analytic`, `test_lab_frames_orientation`, `test_ideal_displacement_fidelity` (slow), `test_lab_frames_npz_schema` (slow). Fast run before the implementation: 3 passed, 3 failed on the missing API.
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Acceptance gates (copy from brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1–11 | pending | tests being written |

## Commands run (most recent first)
```text
$DUQ_PY -m pytest tests/test_l3_prep.py -m "not slow" -q --tb=line
3 failed, 3 passed, 2 deselected in 8.09s
FAILED test_metrics_extra_on_coherent (no metrics_extra)
FAILED test_pulse_displacement_analytic (no run_pulse)
FAILED test_lab_frames_orientation (no tasks.task_lab_frames)
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
- Pranav's intro `tasks/task_1_3b.py` drives the memory while the pump is on (`H0 + i ε (a†−a)`). That is the stretch `pump_on` case, not method (ii). Method (ii) displaces with g₂ = ε_d = 0, then switches the stabilization on.

## DECISION NEEDED
> None yet.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. The drive ε(a+a†) visibly moves ⟨a⟩, yet it can never prepare |+α⟩ from vacuum. Which symmetry forbids it? What exactly does that symmetry force about ⟨a⟩? And why does ε_x·i(a†−a) escape it?
2. Method (ii) calibrates the pulse area to ε_x·τ = α. If the area is 20% off, or the drive phase is rotated by 30°, what final state does the stabilization produce? What kind of calibration error *would* actually ruin the preparation?
3. In method (iii), why does a weak ε_x matter so much in the first ~0.2 µs of inflation and so little afterwards? And what does leaving it on longer cost you, in terms of leakage, the well shift ≈ ε_x/(2κ₂α²), and fidelity versus p_right?

## Notes for Claude's later review
- Intro-track anchor to reproduce, not to trust: `results/task_1_3b.json` gives F(β=α, t=2 µs) = 0.9999915936048853 at 32×12. That run is method (i), an instantaneous displacement, evolved for 2 µs.
