# Status: lane `l1-spectral`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (early start, before the `l0-core` merge; RUNBOOK §4) |
| Branch | `std/l1-spectral` |
| Agent / model | Cursor agent, Claude Opus |
| Started (EDT) | Sat Oct 24 2026, 6:35 PM |
| Last update (EDT) | Sat Oct 24 2026, 6:40 PM |
| Last commit | (none yet) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [ ] Tests written first (list the test names)
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Hardware substitution (this machine, per RUNBOOK §1/§3 and the coordinator)
This lane runs on an Apple M3, 8 cores, **8 GB RAM** (not the 16 GB Windows laptop in the brief).
- Feasibility cap for `NA_EIG_MAX, NB_EIG_MAX`: **≤ 10 min and ≤ 4 GB peak RSS** (brief says 10 min / 6 GB).
- "Comfortable" pair: **≤ 5 min and ≤ 2 GB** (brief says 5 min / 3 GB).
- The profiler kills a child at > 600 s or > 4 GB (brief default 6 GB), and every run expected above 1.5 GB or 5 min holds the machine-wide heavy lock (RUNBOOK §3).

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. 11 fast tests pass in ≤ 40 s; full fast suite passes | pending | |
| 2. 3 slow tests pass (or DECISION NEEDED) | pending | |
| 3. Production odd-block γ: rel_residual < 1e-4, edge_weight < 1e-6, finite cond_est; 20×6 trap flagged | pending | |
| 4. Full-L 28×8 γ agrees with odd block to 1e-3; full/odd time ratio reported | pending | |
| 5. Records validate, IDs per §7, dirty == false, arrays + figure exist | pending | |
| 6. Status file has anchor table, profile table, exponent, permc, NA/NB_EIG_MAX | pending | |
| 7. `git diff --name-only standard-track...HEAD` ⊆ allowlist | pending | |

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
- Early start before `l0-core` merged (RUNBOOK §4): tests and `src/spectral.py` are written against the current `src/model.py` (`one_mode(N, kappa_2, alpha, kappa_a)`, `two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a)`).
- Hardware limits substituted as above (8 GB machine).

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why is Γ_X exactly the smallest-|λ| eigenvalue of the odd parity block, and what quantity becomes conserved (making that block singular) when κ_a = 0?
2. At 20×6 the solver returns 7.6e-6 at α = 2.1 with a tiny residual; how do you know it is a truncation artifact, and why is a relative residual meaningful when λ ~ 4e-7 while ‖L‖ is ~1e2 or larger?
3. Why does Y_L decay at Γ_Z − Γ_X rather than Γ_Z + Γ_X, and once ε_Z ≠ 0 breaks the Z2 symmetry, why must you deflate (or shift by a small positive σ) instead of shift-inverting the full L at σ = 0?

## Notes for Claude's later review
-
