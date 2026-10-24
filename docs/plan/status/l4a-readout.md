# Status: lane `l4a-readout`

> Copied from `docs/plan/status/_TEMPLATE.md`. Updated at every milestone. Facts only: commands and real output.

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l4a-readout` |
| Agent / model | Cursor agent, Claude Opus (early start, before `l0-core` merge) |
| Started (EDT) | Sat Oct 24 2026, 18:30 |
| Last update (EDT) | 18:35 |
| Last commit | (none yet) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK (18:30)
- [ ] Tests written first (list the test names)
- [ ] `src/linresp.py` complete ("linresp ready" for L4c / L4b / L6)
- [ ] `tasks/task_2_3.py` complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Acceptance gates (brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. Fast tests 1–5 + slow tests 6–7 pass; full fast suite < 2 min | pending | |
| 2. Symmetry residual ≤ 1e-9 at production truncation | pending | |
| 3. S17 within 5% for every ε ≤ g₂, both wells; Ehrenfest residual ≤ 1e-3 | pending | |
| 4. Ring freq within 5% of 3.138 MHz; σ within 10% of κ_b/4; settle within 15% of linresp same-metric; oscillating (≥ 2 overshoots) | pending | |
| 5. Γ_Z(0) within 2% of 0.5154; ΔΓ_Z within tolerances of S18 and pointer form | pending | |
| 6. Every td record converged; max top-2 memory / top buffer < 1e-6 at 28×8 | pending | |
| 7. 21 production records, dirty == false; 3 figures, 3 array files; notebook runs | pending | |
| 8. `src/linresp.py` imports no dynamiqs; signatures match CONTRACT §9 | pending | |

## Commands run (most recent first)
```text
(none yet)
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
- Machine is the macOS M3 / 8 GB of `.orchestrator/RUNBOOK.md`, not the Windows laptop; commands translated to zsh.

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Starting from the two-mode Hamiltonian, derive why ⟨b⟩ rings at ≈3.14 MHz instead of relaxing monotonically, why the decay envelope is κ_b/4 independent of g₂, and why the one-mode model gets 20 ns instead.
2. Why are the two wells' buffer signals exactly ⟨b⟩₋ = −⟨b⟩₊*, why does that make Δ⟨b⟩ purely real and the κ_a offset 0.003i irrelevant, and what kind of term would break it?
3. Why does Γ_Z(ε_Z) − Γ_Z(0) = (κ_b/2)|Δ⟨b⟩|² validate SNR = κ_b∫|Δ⟨b⟩|²dt, and if reading out *always* dephases X_L, why is Γ_X, not Γ_Z, the cost that limits how hard you can drive?

## Notes for Claude's later review
-
