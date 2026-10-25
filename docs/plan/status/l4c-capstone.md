# Status: lane `l4c-capstone`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l4c-capstone` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 10:18 |
| Last update (EDT) | 2026-10-25 10:40 |
| Last commit | code `247af45`; outputs in the following commit |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, runbook
- [x] Tests written first (`test_pulse_shapes_and_energy`, `test_snr_known_signal`, `test_svd_gain_ge_square_gain_equal_energy`, `test_generalized_pulse_ratio_ge_square`, `test_svd_pulse_spectrum_reported`; slow tests written, not run)
- [x] `src/pulses.py` and `tasks/task_2_4c_pulses.py` (linear response)
- [x] `--quick` run passes (≤ 2 min)
- [x] Production linear-response records (`provenance.dirty == false`, commit `247af45`)
- [ ] Two-mode validation — not started (hard stop)
- [x] Explain-back questions drafted

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| Fast tests | PASS | `pytest tests/test_l4c_capstone.py -q -m "not slow"` → `5 passed, 2 deselected in 1.26s`. First run, before `src/pulses.py` existed: 4 failed with `No module named 'src.pulses'`, 1 passed. |
| Slow two-mode tests | NOT RUN | They are two-mode mesolves. Hard stop: do not start a two-mode simulation. Not claimed as passing. |
| SVD / gen beat square in linear response | PASS | α=2.1, T=1 µs, amp=0.1 g₂. SVD gain at matched ∫ε² dt = **4.494**. Gen gain at matched ∫\|δa\|² dt = **1.319**. Fast tests also enforce the Rayleigh identity. |
| Two-mode SNR within 10% | NOT RUN | No `t2_4c.snr.td.*` records. No two-mode win claimed. |
| Matched cost (iii) | PASS, illustrative | l4b grid absent. Analytic Dubovitskii proxy, notes contain `illustrative: analytic cost proxy until l4b grid lands`. Proxy ∝ ε², so gain_C = gain_E = **4.494** for SVD. C_X of the matched pulse at α=2.1 is **5.473e-6** (dimensionless). |
| Flip check | NOT RUN | Would be a 40 µs train. Queued below. `tasks/task_2_4c_verify.py` was not written, so the command is not runnable yet. |
| Verdict | concerns | No two-mode win is claimed. In linear response the SVD pulse beats the square by 4.494× in SNR at equal analytic C_X. |
| dirty, figures, notebook, quick | partial | Notebook, pulse figure, and comparison figure exist. Validation figure does not. `--quick` script wall 3.66 s. Production `t2_4c.snr.linresp.two_mode.a2.10.psvd.t1.0us` has `provenance.dirty == false` and `git_commit == 247af45`. |

## Square versus SVD (linear response, α = 2.1, T = 1 µs)

Reference square amplitude 0.1 g₂ = 0.4794 rad/µs. Every SNR below is after scaling onto that square's drive energy. Plant pole from `linresp.ringing` is 3.138 MHz.

| Pulse | SNR | gain vs square at equal ∫ε² (i) and equal analytic C_X (iii) | gain at equal ∫\|δa\|² (ii) | FFT peak |
|---|---|---|---|---|
| square | 0.038163 | 1 | 1 | 1 MHz bin |
| ramp_cos_tau0.1 | 0.038365 | 1.005 | 1.022 | 1 MHz bin |
| ramp_lin_tau0.1 | 0.038275 | 1.003 | 1.040 | 1 MHz bin |
| clear_k3_t0.16 | 0.052337 | 1.371 | 0.475 | 1 MHz bin |
| **svd** | **0.171507** | **4.494** | 0.236 | 3 MHz bin |
| gen | 0.038011 | 0.996 | **1.319** | 1 MHz bin |

The square SNR 0.0382 sits next to the RESEARCH §7 anchor ≈ 0.04 at ε = 0.1 g₂. The FFT grid is 1/T = 1 MHz, so "3 MHz" is the bin next to the 3.138 MHz pole, not a resolved frequency. SVD is worse than square on the leakage proxy; the generalized pulse is the one that wins that ratio, and it does not beat square on drive energy.

**Verdict sentence:** No candidate is claimed to beat square on the two-mode model. In linear response, the SVD pulse beats the square by 4.494× in SNR at equal drive energy and at equal analytic C_X; the full-model check was not run.

## Commands run (most recent first)
```text
"$DUQ_PY" -m tasks.task_2_4c_pulses
# after commit 247af45; wall_s 4.89; dirty false on t2_4c.snr.linresp.two_mode.a2.10.psvd.t1.0us
# SQUARE_SNR 0.03816329 SVD_SNR 0.17150701 GAIN_E 4.494031 GAIN_C 4.494031

"$DUQ_PY" -m tasks.task_2_4c_pulses --quick
# wall_s 3.66 inside the script; /usr/bin/time real 22.78
# SQUARE_SNR 0.03816329 SVD_SNR 0.17150701 GAIN_E 4.494031 GAIN_L 0.235748 GAIN_C 4.494031
# SVD FFT peak 3.0000 MHz; plant pole 3.1380 MHz
# finalists: square, ramp_cos_tau0.1, ramp_lin_tau0.1, clear_k3_t0.16, svd, gen

"$DUQ_PY" -m pytest tests/test_l4c_capstone.py -q -m "not slow"
# 5 passed, 2 deselected in 1.26s
```

## Records produced
Production ids (same values as the quick run at α=2.1, T=1; other α and T are filled by the production run). Cross-check is null: there is no two-mode record.

| Record id | Value | Units | Converged | Cross-check |
|---|---|---|---|---|
| `t2_4c.snr.linresp.two_mode.a2.10.psquare.t1.0us` | 0.038163 | 1 | n/a (linear response) | null, two-mode not run |
| `t2_4c.snr.linresp.two_mode.a2.10.psvd.t1.0us` | 0.171507 | 1 | n/a | null |
| `t2_4c.snr.linresp.two_mode.a2.10.pgen.t1.0us` | 0.038011 | 1 | n/a | null |
| `t2_4c.cost.linresp.two_mode.a2.10.psvd` | 5.473e-6 | 1 | n/a | analytic proxy, illustrative |

Finalist tokens: `square`, `ramp_cos_tau0.1`, `ramp_lin_tau0.1`, `clear_k3_t0.16`, `svd`, `gen`.
Record ids use `t1.0us` rather than `T1.0us` because CONTRACT §6.3 rejects uppercase.

## Figures / arrays produced
- `figures/task_2_4c_pulses.png`
- `figures/task_2_4c_comparison.png`
- `results/arrays/t2_4c.frontier.npz`
- `results/arrays/t2_4c.pulses.npz`
- `figures/task_2_4c_validation.png` was not produced.

## Jobs to queue (for the integrator; jobs > 15 min or not run here)

`tasks/task_2_4c_verify.py` was **not written**. Do not launch the commands below until that module exists; a missing module fails immediately and produces no record. Intended commands, from the repo root after this lane is merged, with `DUQ_PY`, `XLA_FLAGS`, and `MPLCONFIGDIR` set as in the runbook:

| Name | Command | RAM est. (GB) | Wall est. | Outputs |
|---|---|---|---|---|
| Two-mode square vs SVD (and the other finalists) at α=2.1, T=1 µs, trunc_for(2.1)+one larger Na and Nb | `"$DUQ_PY" -m tasks.task_2_4c_verify --stage validate` | < 3 | 10–15 min | `t2_4c.snr.td.two_mode.a2.10.p{square,svd,...}.t1.0us` |
| Flip-check trains, square and svd, α=1, Na=16 Nb=6, N=20, T=1 µs, 1 µs gaps, plus rtol 1e-10 repeat | `"$DUQ_PY" -m tasks.task_2_4c_verify --stage flipcheck` | < 1 | 10–30 min each, several runs | `t2_4c.flip_prob.td.two_mode.a1.00.p{square,svd}` |
| Gradient refinement, 2 h cap, warm-started from SVD | `"$DUQ_PY" -m tasks.task_2_4c_verify --stage gradient` | ~2 | 2 h cap | optional `pgrad` |
| κ_b sweep (needs `src/spectral.py` from l1) | `"$DUQ_PY" -m tasks.task_2_4c_verify --stage kappa_b` | eigen-limited | unknown | discussion only |
| Re-run cost (iii) when `results/arrays/t2_4b.grid.npz` exists | `"$DUQ_PY" -m tasks.task_2_4c_pulses` then the validate stage | < 3 | minutes + the validate | cost records, no longer marked illustrative |

Hold `$MAIN/.git/duq-heavy.lock` for validate and flipcheck. It was held at 10:22 by `l4a-readout 09:42 task_2_3 production 40x18` (older than 30 min). This lane did not delete it and did not take it.

## Deviations from the brief (and why)
- Hard stop 10:45 EDT. No two-mode mesolve was started. Linear-response SVD-versus-square is what shipped.
- `src/linresp.py` copied verbatim from `a1e8192` (`prod/linresp` / `prod/release`) and not edited. `std/l4a-readout` was dirty; that worktree was not touched.
- l4b grid missing, so cost (iii) is the analytic proxy. Under that proxy it is the same comparison as matched drive energy.
- `tasks/task_2_4c_verify.py` and `figures/task_2_4c_validation.png` are absent.
- Slow tests were not run.

## DECISION NEEDED
> None. The missing two-mode check is a stopped job, not an open physics question.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why is the top singular vector of the response matrix the best pulse at fixed drive energy, and what does "matched cost" mean in your comparison?
2. Why does the optimal pulse put its energy near 3.14 MHz, and why does a square pulse waste drive?
3. How do you know the winning pulse doesn't hurt bit flips more than the proxy says? What did the direct flip check at α = 1.0 show?

## Notes for Claude's later review
- Do not promote the 4.494× factor to a two-mode claim. SVD loses to square on the leakage proxy (gain 0.236). Gen wins leakage (1.319×) and is tied with square on energy (0.996×).
- FFT peak 3.00 MHz is one bin wide (Δf = 1 MHz). The pole is 3.138 MHz.
- Square SNR 0.0382 versus the §7 anchor ≈ 0.04 is a sanity check only.
- Tolerances were not loosened. The two-mode 10% gate was not opened, because the simulation was not run.
- Heavy lock was not deleted.
