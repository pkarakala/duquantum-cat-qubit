# Status: lane `l1-spectral`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (paused: waiting for l0-core merge) |
| Branch | `std/l1-spectral` |
| Agent / model | Cursor agent (continuation) |
| Started (EDT) | Sat Oct 24 2026, 6:35 PM |
| Last update (EDT) | Sat Oct 24 2026, 7:20 PM |
| Last commit | `7a3b374` sparse Liouvillian and COLAMD shift-invert Gamma_X |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first (committed `0a35012`, not rewritten)
- [x] `src/spectral.py` complete against CONTRACT §8; fast and slow tests pass
- [ ] `--quick` profile run (needs `src.results.record` / `std_params` / `plotting.save(..., quick=)`)
- [ ] Production profile records, or queued
- [ ] All acceptance gates in brief §8 checked
- [x] Explain-back questions drafted

## Hardware substitution (this machine, per RUNBOOK §1/§3)
Apple M3, 8 GB. Feasibility cap used here: **≤ 10 min and ≤ 4 GB** physical footprint. Comfortable pair: **≤ 5 min and ≤ 2 GB**. A run expected above 1.5 GB or 5 min held `$MAIN/.git/duq-heavy.lock`. Peak memory is `footprint` `phys_footprint_peak` (macOS `ru_maxrss` / `ps` RSS under-count compressed pages: the killed MMD run showed ~0.8 GB RSS and **5.5 GB** footprint).

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| 1. 11 fast tests ≤ 40 s; full fast suite | **pass** | `pytest tests/test_l1_spectral.py -m "not slow" -q` → 12 passed, 1 skipped, 6.96 s. Skip is `test_trace_preservation[two_nth]` (`two_mode` has no `n_th` until l0-core). No other test modules exist on this branch, so this is the whole fast suite. |
| 2. 3 slow tests | **pass** | `pytest tests/test_l1_spectral.py -m slow -q` → 6 passed, 90.43 s (4 parametrized anchors + one-mode + trap). Slowest: 28×8 α=1.4 41.8 s, 28×8 α=2.1 41.0 s. |
| 3. Odd-block acceptance; 20×6 trap flagged | **pass** on every measured odd solve below | rel_residual < 1e-4, edge_weight < 1e-6 except the trap (edge = 1.97e-6). cond_est finite, between 3.5 and 6.8. |
| 4. Full-L 28×8 vs odd, to 1e-3; time ratio | **not run** (RAM) | Proxy: 20×6 α=1 `full_deflated` vs odd γ agree to **1.6e-15**. Full/odd wall ratio **3.0** (4.87 s / 1.64 s), lu_nnz ratio **2.14**. Outside the brief's 4–16 band because COLAMD fill on the full matrix is only ~2× the odd block, not 8×. 28×8 full is estimated ~6 GB (see Jobs). |
| 5. Records, dirty == false, arrays, figure | **blocked on l0-core** | `src.results.record`, `std_params`, and `plotting.save(fig, name, quick=)` are not on `standard-track`. No production outputs. |
| 6. Anchor table, profile table, exponent, permc, NA/NB | **in this file** | Profile records themselves are not written. |
| 7. diff vs `standard-track` ⊆ allowlist | **pass** for committed paths | `tests/test_l1_spectral.py`, `src/spectral.py`, `docs/plan/status/l1-spectral.md`. |

## Anchor table (COLAMD, reproduce-don't-trust)
| Case | Anchor | Measured | Rel diff | rel_residual | edge_weight |
|---|---|---|---|---|---|
| two 20×6 α=1.0 | 2.3007e-3 | 2.30065581e-3 | 1.9e-5 | 1.5e-12 | 4.6e-11 |
| two 20×6 α=1.4 | 1.2020e-4 | 1.20200050e-4 | 4e-7 | 9.4e-11 | 1.8e-9 |
| two 28×8 α=1.4 | 1.2021e-4 | 1.20205148e-4 | 4.0e-5 | 1.3e-10 | 1.7e-11 |
| two 28×8 α=2.1 | 3.8831e-7 | 3.88312242e-7 | 5.8e-6 | 4.4e-7 | 1.6e-10 |
| one N=40 α=2.1 | 1.1699e-7 | 1.16990582e-7 | 5.0e-6 | 4.4e-7 | 1.5e-22 |
| trap two 20×6 α=2.1 | 7.6070e-6 | 7.60695055e-6 | 6.5e-6 | 6.3e-9 | **1.97e-6** (flagged) |

Trap ratio γ(28×8)/γ(20×6) at α=2.1 = 0.051 < 0.1. Code-space rates at one-mode N=40, α=1 (fast test): Γ_X within 1% of 2.2819e-3, odd rates[1] within 2% of 0.1190, even rates[0] within 2% of 0.1212, and odd[1]+odd[0] = even[0] within 2%.

## Ordering (permc)
Default in `gamma_x` / `_shift_invert` is **`COLAMD`**. At the 20×6 odd block (α=1, factorization only):

| permc | lu_nnz | lu_s |
|---|---|---|
| COLAMD | 5.33e6 | 1.68 |
| MMD_ATA | 5.70e6 | 1.99 |
| NATURAL | 7.64e6 | 1.42 |
| MMD_AT_PLUS_A | 2.66e7 | 21.6 |

COLAMD and MMD_AT_PLUS_A give the same γ to ~1e-12 relative. MMD_AT_PLUS_A at 28×8 was killed still inside SuperLU after 18 min at **5.5 GB** physical footprint. Do not use it on this machine.

## Deflation fill (20×6 even block, α=1)
COLAMD: plain even lu_nnz = 5.60e6, deflated even lu_nnz = 6.09e6, **ratio 1.09** (matrix nnz ratio 1.22). MMD_AT_PLUS_A ratio was 1.01. Neither exceeds 2×, so the rank-1 `|vec(I)⟩⟨vec(I)|` update stays. No sparse alternative.

## Profile table (measured odd-block `gamma_x` at α=2.1 unless noted; not records)
`x = Na·Nb²`. Model time is the RESEARCH §9 odd-block estimate `113 s · (x/1792)³ / 8`. Footprint is `phys_footprint_peak`.

| Na×Nb | sector | dim | lu_nnz | wall_s | footprint | γ | model t | status |
|---|---|---|---|---|---|---|---|---|
| 20×6 α=1.0 | odd | 7200 | 5.33e6 | 1.64 | ~0.4 GB | 2.301e-3 | 0.91 s | ok |
| 20×6 α=2.1 | odd | 7200 | 5.24e6 | 1.51 | ~0.6 GB | 7.607e-6 | 0.91 s | ok, trap |
| 28×6 | odd | 14112 | 1.45e7 | 5.07 | 0.82 GB | 3.988e-7 | 2.5 s | ok |
| 24×8 | odd | 18432 | 3.22e7 | 18.4 | 1.53 GB | 4.062e-7 | 8.9 s | ok |
| 28×8 | odd | 25088 | 6.06e7 | 46.4 | 2.63 GB | 3.883e-7 | 14 s | ok |
| 32×8 | odd | 32768 | 7.63e7 | 71.9 | 3.32 GB | 3.882e-7 | 21 s | ok, stopped here |
| 20×6 α=1.0 | full_deflated | 14400 | 1.14e7 | 4.87 | < 1.6 GB | 2.301e-3 | 7.3 s | agrees with odd to 1.6e-15 |
| 28×8 | full | — | — | — | ~6 GB est. | — | 113 s | not run |

Fitted exponent on the five odd COLAMD wall times: **p = 3.61** in `t ∝ (Na·Nb²)^p` (scatter up to 22% at 24×8). Steeper than the model's 3, and our COLAMD times are 2–3× the model, so the model is not a safe RAM predictor here. Footprint scales roughly as `x²` (28×8 → 32×8: 2.63 → 3.32 GB).

Full/odd at 20×6: time ratio 3.0, lu_nnz ratio 2.14. The Z₂ split is still worth it; it is not an 8× win once COLAMD is used.

## Recommendation for `src/config.py` (integrator applies it)
- **`NA_EIG_MAX = 32`**, **`NB_EIG_MAX = 8`**. Largest Na finished at Nb=8 is 32 (72 s, 3.32 GB). Largest Nb finished at Na≥28 is 8. 36×8 is estimated ~4.2 GB and was not started. 28×10 is estimated ~6 GB and was not started.
- **Comfortable pair: 24×8** (18 s, 1.53 GB footprint). Under 5 min and under 2 GB, so it can sit beside other work; it is still just over the 1.5 GB lock line. **28×6** (5 s, 0.82 GB, γ = 3.988e-7, 2.7% above the 28×8 anchor, edge_weight 3e-9) is the lighter pair and does not need the lock.
- 28×8 (46 s, 2.63 GB) and 32×8 (72 s, 3.32 GB) are feasible but each must hold the heavy lock. Not comfortable.

## Speed levers
- Z₂ split: on, required.
- COLAMD vs MMD_AT_PLUS_A: adopted COLAMD (table above).
- Real Hermitian basis: **not attempted**. COLAMD already makes 28×8 and 32×8 fit.
- `pypardiso`: **not importable**. Not installed.

## Commands run (most recent first)
```text
pytest tests/test_l1_spectral.py -m slow -q --durations=8
  → 6 passed in 90.43s
pytest tests/test_l1_spectral.py -m "not slow" -q
  → 12 passed, 1 skipped in 6.96s
# COLAMD gamma_x scans (α=2.1 unless noted), heavy lock held, killed if footprint > 3.8 GB:
#   20x6, 28x6, 24x8, one N=40, full_deflated 20x6 α=1, 32x8. None killed.
# Earlier MMD_AT_PLUS_A 28x8 (a leftover process) was killed at 5.5 GB footprint.
```

## Records produced
None. `src.results.record` is not on this branch. Do not treat the table above as `results/records/`.

## Figures / arrays produced
None.

## Jobs to queue
Profile script `tasks/task_spectral_profile.py` is **not written**: it has to call `record()` / `std_params` / `plotting.save(..., quick=)`, which arrive with the l0-core merge. After that script exists, run in-lane (under the heavy lock, peak ~3.3 GB, ~2.5 min):

```text
$DUQ_PY -m tasks.task_spectral_profile --sizes 24x8,28x8,32x8 --no-full
```

Queue the rest. Estimates use the measured COLAMD scaling (p≈3.6, footprint ∝ x² anchored at 32×8 = 72 s / 3.32 GB), not the 16 GB-laptop model. `--ram-gb` is that estimate. The worker's `--max-ram-gb 5` cannot admit the larger ones; they need to run alone or elsewhere.

| Name | Command | RAM est. | Wall est. | Why queued |
|---|---|---|---|---|
| l1_full_28x8 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 28x8` (includes the full-L compare) | 6 GB | 3 min | Gate 4. Odd 28×8 is done; full is the extra. |
| l1_24x10 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 24x10 --no-full` | 4.6 GB | 2 min | Over the 4 GB cap. |
| l1_40x8 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 40x8 --no-full` | 5.2 GB | 3 min | Over the cap. |
| l1_28x10 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 28x10 --no-full` | 6.2 GB | 4 min | Over the cap. Would set a higher `NB_EIG_MAX` if it finishes. |
| l1_48x8 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 48x8 --no-full` | 7.5 GB | 5 min | Over the cap. |
| l1_32x10 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 32x10 --no-full` | 8 GB | 6 min | Over the cap. |
| l1_32x12 | `$DUQ_PY -m tasks.task_spectral_profile --sizes 32x12 --no-full` | 17 GB | 22 min | Over both caps. Brief's 4 min / ~1 GB odd-block figure does not hold for SciPy+COLAMD on this CPU. |

`tools/runq` is not on this branch yet (l0-tools / integrator). Exact submit lines, once `runq` exists:

```text
python -m tools.runq submit --name l1_full_28x8 --ram-gb 6 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 28x8
python -m tools.runq submit --name l1_24x10 --ram-gb 5 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 24x10 --no-full
python -m tools.runq submit --name l1_40x8 --ram-gb 6 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 40x8 --no-full
python -m tools.runq submit --name l1_28x10 --ram-gb 7 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 28x10 --no-full
python -m tools.runq submit --name l1_48x8 --ram-gb 8 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 48x8 --no-full
python -m tools.runq submit --name l1_32x10 --ram-gb 8 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 32x10 --no-full
python -m tools.runq submit --name l1_32x12 --ram-gb 17 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 32x12 --no-full
```

## Deviations from the brief (and why)
- Paused before `l0-core` merged (RUNBOOK §4). `git -C $MAIN log standard-track` has no `merge l0-core`. Solver and tests do not need the new APIs; the profile does.
- `PERMC = "COLAMD"` instead of `MMD_AT_PLUS_A`. The brief says to keep the faster of those two. COLAMD is ~13× faster and ~5× less fill at 20×6, and it is what makes 28×8 and 32×8 fit in 4 GB.
- Feasibility numbers are physical footprint on an 8 GB Mac, not the brief's 6 GB / 16 GB laptop.
- 28×8 full Liouvillian was not factored. 20×6 `full_deflated` was, and matches.
- Real-basis lever not attempted. `pypardiso` absent.
- `pytest.ini` is absent, so `@pytest.mark.slow` warns. Filter still works. Do not add `pytest.ini` (l0-core owns it).

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only)
1. Why is Γ_X exactly the smallest-|λ| eigenvalue of the odd parity block, and what quantity becomes conserved (making that block singular) when κ_a = 0?
2. At 20×6 the solver returns 7.6e-6 at α = 2.1 with a tiny residual; how do you know it is a truncation artifact, and why is a relative residual meaningful when λ ~ 4e-7 while ‖L‖ is ~1e2 or larger?
3. Why does Y_L decay at Γ_Z − Γ_X rather than Γ_Z + Γ_X, and once ε_Z ≠ 0 breaks the Z2 symmetry, why must you deflate (or shift by a small positive σ) instead of shift-inverting the full L at σ = 0?

## Notes for Claude's later review
- Odd-block γ matches every anchor well inside tolerance. The 20×6 α=2.1 trap is flagged by edge_weight and is 20× larger than the 28×8 value.
- 28×6 α=2.1 gives 3.988e-7, matching RESEARCH §5 ("Na=28, Nb=6 → 3.987e-7").
- Left-eigenvector phase/sign convention passed `test_left_eigvec_operator` (Hermitian, odd support, positive on |+α⟩).
- On resume: merge `standard-track`, re-run the skipped `n_th` trace test, write `tasks/task_spectral_profile.py`, record the feasible sizes, queue the table above. Do not switch the default ordering back to `MMD_AT_PLUS_A`.
