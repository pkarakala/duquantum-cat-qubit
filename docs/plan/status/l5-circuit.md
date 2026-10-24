# Status: lane `l5-circuit`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l5-circuit` |
| Agent / model | Cursor agent, Claude (Opus class) |
| Started (EDT) | Sat Oct 24 2026, 6:35 PM |
| Last update (EDT) | Sat Oct 24 2026, 6:45 PM |
| Last commit | (none yet) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK (early start: l0-core not merged, venv `.duq-ready` absent)
- [ ] Tests written first (list the test names)
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Acceptance gates (brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. §5 tests pass; fast suite < 2 min | pending | |
| 2. g₂.sym = −0.7214 MHz; ε_p(0.763) = 0.0370; ε_p\* reported; sign/gauge in doc | pending | |
| 3. Resonant count = 12 through order 7, list in notes and doc | pending | |
| 4. Displaced static linear terms < 1e-9 MHz; five ratios; stark_b(ε_p\*) ∈ [20, 32] MHz | pending | |
| 5. V1: tdsim \|g₂\| within 3% of \|g₂,disp\|; no-½ excluded > 20σ; bare max P₀₁ < 0.05; retuned ≥ 0.95; rtol change < 1e-4; Na/Nb converged | pending | |
| 6. V2: E1 max\|Δn_a\| ≤ 0.03; E2 error ≥ 5× E1; Re⟨a²⟩_tdsim < 0 | pending | |
| 7. Production records: dirty false, cross_check agree, convergence per table | pending | |
| 8. `docs/derivation_2_4a.md` complete (term table + extra_H recipe); status DONE | pending | |

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
-

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Your g₂ has an extra e^{−(φ_a²+φ_b²)/2} and a ½ that a public tutorial leaves out. Where does each factor come from, and how did your simulation decide between them?
2. The pump shifts the buffer by about 26 MHz, roughly 35 times g₂. Why does that not destroy the cat, what exactly has to be retuned, and what would you see in the lab if it were not?
3. If the readout drive is applied through the ATS flux instead of capacitively, which new terms appear, why is one of them exactly resonant, and how would it change Γ_X or Γ_Z?

## Notes for Claude's later review
-
