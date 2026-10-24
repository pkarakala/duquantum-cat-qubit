# Status: lane `l4a-readout`

> Copied from `docs/plan/status/_TEMPLATE.md`. Updated at every milestone. Facts only: commands and real output.

| Field | Value |
|---|---|
| State | `IN_PROGRESS (paused: waiting for l0-core merge)` |
| Branch | `std/l4a-readout` |
| Agent / model | Cursor agent, Grok 4.7 (resumed after the previous agent stopped at `614132a`) |
| Started (EDT) | Sat Oct 24 2026, 18:30 |
| Last update (EDT) | 19:05 |
| Last commit | `614132a` linresp; task_2_3 + notebook land in the commit that adds this paragraph |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK (18:30; re-read 18:50)
- [x] Tests written first (18:36, commit `74787b0`): `test_poles_and_ringing`, `test_dc_gain`, `test_step_response_analytic`, `test_svd_pulse_beats_square_at_equal_energy`, `test_fit_damped_sine` (fast); `test_readout_symmetry`, `test_S17` (slow).
- [x] **linresp ready** (18:40, commit `614132a`): `src/linresp.py`. API for L4c / L4b / L6 matches CONTRACT §9.
- [x] `tasks/task_2_3.py` written against CONTRACT §3/§6/§7 (`two_mode(..., eps_z=)`, `coherent2`, `cat2`, `code_basis`, `record`, `sweep`, `convergence_block`, `trunc_for`). Not executed: those names are not on this branch yet.
- [x] Notebook `notebooks/08_task_2_3_readout.ipynb` written (linresp cell, record cells, three figures, production line commented). Not executed.
- [ ] `--quick` run — blocked on the l0-core merge
- [ ] Production run(s) — blocked on the l0-core merge
- [ ] Gates 2–7 (need the two-mode records)
- [x] Explain-back questions drafted (below; unchanged from the brief)

## Why paused
`git -C $MAIN log --oneline standard-track | grep -m1 "merge l0-core"` printed nothing (19:00 EDT). `standard-track` is at `0a2040b`. `std/l0-core` is DONE at `effc210` and is not merged. RUNBOOK §4: do not invent the l0-core APIs and do not merge `std/l0-core` myself. Two-mode `mesolve`, `record()`, and `provenance.dirty == false` outputs wait for `git merge --no-edit standard-track` after that merge commit exists.

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. Fast tests 1–5 + slow tests 6–7; full fast suite < 2 min | fast 1–5 pass; slow 6–7 not run | `"$DUQ_PY" -m pytest tests/test_l4a_readout.py -m "not slow" -q` → `5 passed, 2 deselected, 2 warnings in 1.55s`. Slowest: fit 0.03s, svd 0.02s, dc gain 0.02s, step 0.01s. Warnings: `PytestUnknownMarkWarning` on `slow` because `pytest.ini` is l0-core's and is not on this branch. `-m "not slow"` still deselected tests 6–7. |
| 2. Symmetry residual ≤ 1e-9 at production truncation | pending | needs `mesolve` |
| 3. S17 within 5% for every ε ≤ g₂, both wells; Ehrenfest ≤ 1e-3 | pending | needs `mesolve` |
| 4. Ring within 5% of 3.138 MHz; σ within 10% of κ_b/4; settle within 15% of linresp same-metric; ≥ 2 overshoots | pending (linresp side known) | same-metric settle on `linspace(0, 3, 1501)`, ε = 0.1 g₂: **0.682 µs / 1.132 µs**. Envelope 0.7335 / 1.1276. freq 3.1380 MHz. Two-mode fit not run. |
| 5. Γ_Z(0) within 2% of 0.5154; ΔΓ_Z within S18 and pointer tolerances | pending | needs `mesolve` |
| 6. Every td record converged; max top-2 memory / top buffer < 1e-6 at 28×8 | pending | needs the sweeps |
| 7. 21 production records, dirty == false; 3 figures; arrays; notebook runs | pending | 0 records. Notebook is written, not run (it calls `record` / `load_record`). |
| 8. `src/linresp.py` imports no dynamiqs; signatures match CONTRACT §9 | pass | Module imports are `numpy` and `scipy.linalg` only. Tests 1–4 lock the numbers and the signatures. |

## Commands run (most recent first)
```text
$ git -C $MAIN log --oneline standard-track | grep -m1 "merge l0-core" || echo NO_L0_MERGE
NO_L0_MERGE
standard-track: 0a2040b [integrator] ledger: start
std/l0-core:    effc210 [l0-core] status: DONE (not merged)

$ "$DUQ_PY" -m pytest tests/test_l4a_readout.py -m "not slow" -q --durations=10
5 passed, 2 deselected, 2 warnings in 1.55s
(test_fit_damped_sine 0.03s — imports tasks.task_2_3; l0-core names are imported only when signals/dephasing/record run)

$ "$DUQ_PY" - <<PY   # linresp only, no mesolve
delta_b_ss at t=1us (not fully settled) -0.04697
snr_1us = kappa_b * trapz(|Delta b|^2) = 0.03816
Delta b_ss (window [2.5, 3]) = -0.047619
same-metric settle 5%/1% = 0.682 / 1.132 us
8 g2 alpha = 80.540 > kappa_b = 16.336, underdamped True
freq_MHz 3.137987, Q 2.46508, envelope t5/t1 0.73352 / 1.12759
```

## Records produced
None. `src.results.record` is not on this branch. The 21 ids the script will write after the merge:

| Record id | Value | Units | Converged | Cross-check |
|---|---|---|---|---|
| `t2_3.b_ss.td.two_mode.a2.10.ez{0.05,0.1,0.2,0.5,1,2,3}g2.well{p,m}` (14) | Re⟨b⟩_ss | dimensionless | — | analytic_S17, tol 0.05 |
| `t2_3.ring_freq.td.two_mode.a2.10` | f | MHz | — | linresp 3.138, tol 0.05 |
| `t2_3.settle_5pct.td.two_mode.a2.10` | settle_time 5% | us | — | same-metric ≈0.682 tol 0.15; envelope 0.7335 tol 0.25 |
| `t2_3.settle_1pct.td.two_mode.a2.10` | settle_time 1% | us | — | same-metric ≈1.132 tol 0.15; envelope 1.1276 tol 0.25 |
| `t2_3.dephasing.td.two_mode.a2.10.ez{0.2,0.5,1}g2` (3) | ΔΓ_Z | 1/us | — | S18 tol 0.10 (0.25 at 0.2); pointer tol the same |
| `t2_3.ring_freq.linresp.two_mode.a2.10` | 3.137987 | MHz | null (analytic) | td record once it exists, tol 0.05 |

## Figures / arrays produced
None yet. The script writes, after the merge:
- `figures/task_2_3_buffer_signals.png`
- `figures/task_2_3_linearity.png`
- `figures/task_2_3_dephasing.png`
- `results/arrays/t2_3.ring_freq.td.two_mode.a2.10.npz`
- `results/arrays/t2_3.dephasing.td.two_mode.a2.10.ez{0.2,0.5,1}g2.npz` (3 files; the brief's "3 array files" plus this signals file is 4, matching the filename list in brief §7)

## Jobs to queue (for the integrator; jobs > 15 min)
None. No wall time has been measured, so nothing is known to exceed 15 min. Do not queue speculatively.

**First command after `git merge --no-edit standard-track`** (one +α well, 7 values of ε_Z, prep 3 µs + on 3 µs, no sweep). Hold `$MAIN/.git/duq-heavy.lock` if it looks like more than 5 min or 1.5 GB (RUNBOOK §3). Task 1.1 was ~19 s and ~0.54 GB, so this is probably a few minutes and under 1 GB, but measure:

```sh
export MAIN=/Users/halokwok/Desktop/DuQuantum/duquantum-cat-qubit
export DUQ_PY=$MAIN/.venv/bin/python
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
export MPLCONFIGDIR=$MAIN/.orchestrator/mplconfig
cd $MAIN/.worktrees/l4a-readout
"$DUQ_PY" -c "import time; from tasks.task_2_3 import signals, EPS_GRID; t=time.time(); signals(28, 8, EPS_GRID, wells=(+1,)); print('one +alpha well', time.time()-t)"
```

Extrapolate before `--part signals` (both wells, ε including 0, then Na ∈ {20,24,28,32} and Nb ∈ {6,8,10}) and `--part dephasing` (ε ∈ {0, 0.2, 0.5, 1}, 6 µs, Na ∈ {24,28,32}, Nb ∈ {6,8,10}). If either part extrapolates past 15 min or 3 GB, commit the code (already committed) and queue:

```sh
"$DUQ_PY" -m tools.runq submit --name t2_3_signals --ram-gb 1 -- "$DUQ_PY" -m tasks.task_2_3 --part signals
"$DUQ_PY" -m tools.runq submit --name t2_3_dephasing --ram-gb 1 -- "$DUQ_PY" -m tasks.task_2_3 --part dephasing
```

(`tools/runq.py` arrives with l0-tools, not this lane.) Then `"$DUQ_PY" -m tasks.task_2_3 --part figures`. Quick smoke, ≤ 2 min, is `"$DUQ_PY" -m tasks.task_2_3 --quick`.

## Deviations from the brief (and why)
- Machine is the macOS M3 / 8 GB of `.orchestrator/RUNBOOK.md`. Commands are zsh, not PowerShell.
- l0-core is not merged, so there are no two-mode records or figures. The script calls the CONTRACT signatures; it does not stub them.
- `signals` saves 31 expectation samples during the 3 µs preparation, not only `[0, t_prep]`. The final state is still the state at `t_prep`. The extra samples exist so `max_top2_a` / `max_top_b` see the peak during preparation, which is what gate 6 asks for.
- `coherent2`, `cat2`, `code_basis`, `fit_exp_offset`, `sweep` and `convergence_block` are imported on first use (`_l0`), not at module import. Otherwise `test_fit_damped_sine` cannot import `fit_damped_sine` until the merge. After the merge the call sites are the CONTRACT functions.
- Array count is 4 files (1 signals + 3 dephasing), as the filename list in brief §7 specifies. Gate 7's "3 array files" is one short of that list.

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Starting from the two-mode Hamiltonian, derive why ⟨b⟩ rings at ≈3.14 MHz instead of relaxing monotonically, why the decay envelope is κ_b/4 independent of g₂, and why the one-mode model gets 20 ns instead.
2. Why are the two wells' buffer signals exactly ⟨b⟩₋ = −⟨b⟩₊*, why does that make Δ⟨b⟩ purely real and the κ_a offset 0.003i irrelevant, and what kind of term would break it?
3. Why does Γ_Z(ε_Z) − Γ_Z(0) = (κ_b/2)|Δ⟨b⟩|² validate SNR = κ_b∫|Δ⟨b⟩|²dt, and if reading out *always* dephases X_L, why is Γ_X, not Γ_Z, the cost that limits how hard you can drive?

## Notes for Claude's later review
- linresp is unchanged since `614132a`. Do not treat this commit as a second implementation of it.
- `R_b` is real float64 (Δb = 2 Re b₊). `R_a` is complex and purely imaginary. `optimal_pulse` uses δ = 1e-9·λ_max(Re R_aᴴR_a), as brief §4 specifies.
- Readout `mesolve` uses dynamiqs' default `cartesian_batching=True`: expects shape is `(n_eps, n_wells, n_ops, n_t)` because the Hamiltonian carries the ε batch and the state carries the well batch. `signals` raises if that shape is wrong.
- The −α convergence block is the +α sweep with the sign flipped. Both wells are still simulated at the production truncation; `symmetry_residual` is stored on every `b_ss` record.
- `freq_MHz = ω_d/(2π)` inside `src/linresp.py` is a rad/µs → MHz conversion. The module cannot import `src.config` (that imports dynamiqs).
- Analytic answer already fixed, for the resume that fills X, Y, Z from the two-mode fit: linresp says oscillate at 3.138 MHz, Q 2.465, envelope 0.734 / 1.128 µs, same-metric 0.682 / 1.132 µs, Δb_ss(0.1 g₂) = −0.04762, SNR(1 µs) = 0.0382.
