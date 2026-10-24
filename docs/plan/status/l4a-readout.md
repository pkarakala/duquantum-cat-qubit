# Status: lane `l4a-readout`

> Copied from `docs/plan/status/_TEMPLATE.md`. Updated at every milestone. Facts only: commands and real output.

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l4a-readout` |
| Agent / model | Cursor agent, Claude Opus (early start, before `l0-core` merge) |
| Started (EDT) | Sat Oct 24 2026, 18:30 |
| Last update (EDT) | 18:41 |
| Last commit | (none yet) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK (18:30)
- [x] Tests written first (18:36, commit `74787b0`): `test_poles_and_ringing`, `test_dc_gain`, `test_step_response_analytic`, `test_svd_pulse_beats_square_at_equal_energy`, `test_fit_damped_sine` (fast); `test_readout_symmetry`, `test_S17` (slow). Watched them fail: `ImportError: cannot import name 'linresp' from 'src'`.
- [x] **linresp ready** (18:40): `src/linresp.py` committed; tests 1–4 green (each < 0.03 s). API for L4c / L4b / L6 matches CONTRACT §9. Test 5 (`fit_damped_sine`) lives in `tasks/task_2_3.py`.
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
$ "$DUQ_PY" - <<EOF  (linresp numbers at nominal parameters; asserts dynamiqs/jax not imported)
poles [-4.08407045+19.71655256j -4.08407045-19.71655256j]
ringing {'freq_MHz': 3.137986800482118, 'decay_per_us': 4.084070449666731, 'Q': 2.465076923076923,
         't_settle_5pct_us': 0.7335163069477534, 't_settle_1pct_us': 1.1275932290452737,
         'omega0': 20.135095635387703, 'omega_d': 19.716552558912724, 'underdamped': True}
dc_gain -0.04966452695871414
svd/square 4.494455342185724          (T = 1 us, 40 bins, 400 samples; brief prototype ≈ 4.5x)
same-metric settle 5%/1%: 0.682 1.132 (settle_time on response(), linspace(0, 3, 1501), eps = 0.1 g2)
Delta b_ss 0.0476   SNR(1us) 0.0382   (RESEARCH §7: 0.048, ≈ 0.04)
signatures: system (g2, kappa_b, alpha, well=1) · poles (g2, kappa_b, alpha) · ringing (g2, kappa_b, alpha)
            dc_gain (g2, alpha) · response (eps_t, t, g2, kappa_b, alpha, well=1)
            response_matrices (T, n_bins, n_samples, g2, kappa_b, alpha) · optimal_pulse (R_b, R_a=None, energy=1.0)

$ "$DUQ_PY" -m pytest tests/test_l4a_readout.py -q -k "not slow and not fit_damped" --durations=5
4 passed, 3 deselected   (0.02 s, 0.02 s, 0.01 s per test)
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
- linresp conventions downstream lanes should know: `R_b` is returned as a real `float64` array (Δb = 2 Re b₊), `R_a` as complex and purely imaginary. `optimal_pulse` uses the Tikhonov shift δ = 1e-9·λ_max(Re R_aᴴR_a), as this brief §4 specifies; the L4c brief's test text says "1e-9·trace", which is the same order of magnitude and does not change any inequality at the 1e-9 level.
- `ringing()` in the overdamped regime (never the case at nominal parameters) reports `decay_per_us` and the settling times from the slower real pole σ − √(σ² − ω0²), because κ_b/4 would understate the settling time there; in the underdamped case it is exactly κ_b/4 as the brief specifies.
- `freq_MHz = ω_d/(2π)` is the one place `src/linresp.py` divides by 2π: a rad/µs → MHz conversion for reporting (the module cannot import `src.config`, which imports dynamiqs).
