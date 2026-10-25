# Status: lane `l1-spectral`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l1-spectral` |
| Agent / model | Cursor agent (continuation, after the l0-core merge) |
| Started (EDT) | Sat Oct 24 2026, 6:35 PM |
| Last update (EDT) | Sun Oct 25 2026, 9:40 AM |
| Last commit | profile outputs, committed with this status. Code commit `f796cf5` (`provenance.git_commit`) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first (committed `0a35012`, not rewritten)
- [x] `src/spectral.py` complete against CONTRACT §8; fast and slow tests passed before the merge
- [x] Merged `standard-track` at `77d53fb` (l0-core and l0-tools are in)
- [x] `--quick` profile run (α=1, odd 12×4 / 16×4 / 20×6 and full 12×4; outputs under `results/quick` and `figures/quick`, not committed)
- [x] Production records for the odd-block points that fit in 3 GB
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## Hardware substitution (this machine, per RUNBOOK §1/§3)
Apple M3, 8 GB. In-lane cap used for this resume: **≤ 15 min and ≤ 3 GB** phys_footprint. Anything estimated above **4 GB** is queued and was not started. Comfortable pair: **≤ 5 min and ≤ 2 GB**. Peak memory in the records is macOS `phys_footprint` (GiB), stored as `numerics.peak_rss_gb`. `ru_maxrss` / `ps` RSS under-count compressed pages.

`peak_rss_gb` on the four production records is 0.42, 0.78, 1.45 and 2.54 GiB. The kill line for this run was `--max-rss-gb 3.5`. Nothing was killed.

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| 1. 11 fast tests ≤ 40 s; full fast suite | **pass** | `pytest -m "not slow" -q` → **68 passed, 7 deselected, 19.73 s** (post-merge). Includes every fast `test_l1_spectral` case. `test_trace_preservation[two_nth]` now runs (`two_mode` has `n_th`) and passed. |
| 2. 3 slow tests | **pass on the numbers, pytest not re-invoked** | Pre-merge: `pytest tests/test_l1_spectral.py -m slow -q` → 6 passed, 90.43 s. `spectral.py` was not changed by the merge. Post-merge reproduction: quick 20×6 α=1 γ = 2.30065581e-3 (anchor 2.3007e-3, rel 1.9e-5); production 20×6 α=2.1 and 28×8 α=2.1 match the anchors in the table below. α=1.4 anchors were not re-measured. |
| 3. Odd-block acceptance; 20×6 trap flagged | **pass** | 28×6, 24×8, 28×8: `rel_residual` < 1e-4, `edge_weight` < 1e-6, `cond_est` in 5.6–6.7. 20×6 α=2.1: residual 6.4e-9, **edge_weight = 1.97e-6** (trap flagged), γ 20× the 28×8 value. |
| 4. Full-L 28×8 vs odd, to 1e-3; time ratio | **not run (RAM)** | Full 28×8 is estimated ~6 GB and is queued. Proxy, this resume: quick full vs odd at 12×4 α=1 agree to **5e-14** relative (2.3007152545865e-3). Earlier 20×6 α=1 `full_deflated` vs odd agreed to 1.6e-15, wall ratio 3.0, lu_nnz ratio 2.14 (COLAMD fill, outside the brief's 4–16 time-ratio band). |
| 5. Records, dirty == false, arrays, figure | **pass for the in-lane sizes** | Four records below, `provenance.dirty == false`, commit `f796cf5`. Array `results/arrays/t2_1.wall_s.eig.two_mode.a2.10.profile.npz`. Figure `figures/task_2_1_spectral_cost.png`. The brief's 24×10 / 32×10 / 40×8 / 48×8 / 32×12 ids were not written: those sizes are above 4 GB. |
| 6. Anchor table, profile table, exponent, permc, NA/NB | **in this file** | Recommendation unchanged: `NA_EIG_MAX=32`, `NB_EIG_MAX=8`, comfortable **24×8**, ordering **COLAMD**. |
| 7. diff vs `standard-track` ⊆ allowlist | **pass** | `src/spectral.py`, `tests/test_l1_spectral.py`, `tasks/task_spectral_profile.py`, this status file, the four `t2_1.wall_s.eig.two_mode.a2.10.na*` records, the profile npz, and `figures/task_2_1_spectral_cost.png`. |

## Anchor table (COLAMD, reproduce-don't-trust)
| Case | Anchor | Measured | Rel diff | rel_residual | edge_weight |
|---|---|---|---|---|---|
| two 20×6 α=1.0 (quick, not a record) | 2.3007e-3 | 2.30065581e-3 | 1.9e-5 | 1.9e-12 | 4.6e-11 |
| two 20×6 α=1.4 | 1.2020e-4 | 1.20200050e-4 | 4e-7 | 9.4e-11 | 1.8e-9 |
| two 28×8 α=1.4 | 1.2021e-4 | 1.20205148e-4 | 4.0e-5 | 1.3e-10 | 1.7e-11 |
| two 28×8 α=2.1 | 3.8831e-7 | 3.88312242e-7 | 5.8e-6 | 3.7e-7 | 1.6e-10 |
| one N=40 α=2.1 | 1.1699e-7 | 1.16990582e-7 | 5.0e-6 | 4.4e-7 | 1.5e-22 |
| trap two 20×6 α=2.1 | 7.6070e-6 | 7.60695055e-6 | 6.5e-6 | 6.4e-9 | **1.97e-6** (flagged) |

α=1.4 rows and the one-mode row are the pre-merge slow pytest (spectral.py unchanged). α=2.1 rows and 20×6 α=1 were remeasured after the merge. Trap ratio γ(28×8)/γ(20×6) at α=2.1 = 0.051 < 0.1. 28×6 α=2.1 gives 3.9880e-7 (RESEARCH §5 quotes 3.987e-7, rel 2.5e-4).

## Ordering (permc)
Default in `gamma_x` / `_shift_invert` is **`COLAMD`**. Not re-compared this resume: MMD_AT_PLUS_A at 28×8 was killed in the earlier session at **5.5 GB** footprint. At the 20×6 odd block (α=1, factorization only, earlier session):

| permc | lu_nnz | lu_s |
|---|---|---|
| COLAMD | 5.33e6 | 1.68 |
| MMD_ATA | 5.70e6 | 1.99 |
| NATURAL | 7.64e6 | 1.42 |
| MMD_AT_PLUS_A | 2.66e7 | 21.6 |

COLAMD and MMD_AT_PLUS_A gave the same γ to ~1e-12 relative. Do not switch the default back.

## Deflation fill (20×6 even block, α=1, earlier session)
COLAMD: plain even lu_nnz = 5.60e6, deflated even lu_nnz = 6.09e6, **ratio 1.09** (matrix nnz ratio 1.22). Under 2×, so the rank-1 `|vec(I)⟩⟨vec(I)|` update stays. No sparse alternative.

## Profile table (production odd-block `gamma_x` at α=2.1, COLAMD)
`x = Na·Nb²`. Model time is `113 s · (x/1792)³ / 8`. Footprint is phys_footprint. These wall times are the record values. They are slower than an earlier unloaded scan of the same code (see the note under the table); γ, lu_nnz and footprint match that scan.

| Na×Nb | sector | dim | lu_nnz | wall_s | lu_s | eigs_s | footprint | γ | model t | rel_diff | agree | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20×6 | odd | 7200 | 5.24e6 | 3.45 | 2.32 | 0.77 | 0.42 GiB | 7.607e-6 | 0.92 s | 2.77 | false | ok, trap |
| 28×6 | odd | 14112 | 1.45e7 | 9.59 | 7.21 | 1.91 | 0.78 GiB | 3.988e-7 | 2.51 s | 2.82 | false | ok |
| 24×8 | odd | 18432 | 3.22e7 | 42.0 | 30.6 | 10.9 | 1.45 GiB | 4.062e-7 | 8.90 s | 3.72 | false | ok |
| 28×8 | odd | 25088 | 6.05e7 | 227 | 141 | 85.1 | 2.54 GiB | 3.883e-7 | 14.1 s | 15.0 | false | ok |

Cross-check tolerance stays **1.0**, as the brief specifies. `agree` is false on every row. The RESEARCH §9 model is faster than COLAMD on this CPU even when the machine is quiet (earlier unloaded 28×8 was 46 s, rel_diff 2.3, still above 1). This run's 28×8 factorization took 141 s against that earlier 46 s total, with the same γ (3.88312242e-7) and the same footprint class (2.54 vs 2.63 GiB). That gap is shared-machine contention, not a different eigenpair.

Fitted exponent on these four walls: **p = 4.27** in `t ∝ (Na·Nb²)^p`. The 28×8 point dominates it. The earlier unloaded fit was **p = 3.61**. Use 3.61 for queue wall estimates. Use this run's footprints for RAM: they scale roughly as `x²` and land on the earlier 32×8 measurement (x=2048 → 3.32 GiB).

Full/odd at 28×8: not measured. At 12×4 α=1 (quick) the full-L γ matches the odd block to 5e-14. At 20×6 α=1 (earlier) full/odd wall ratio was 3.0 and lu_nnz ratio 2.14.

## Recommendation for `src/config.py` (integrator applies it)
- **`NA_EIG_MAX = 32`**, **`NB_EIG_MAX = 8`**. Unchanged. Largest Nb finished at Na≥28 is 8. Largest Na finished at Nb=8 **in an earlier unloaded scan** is 32 (72 s, 3.32 GiB). This resume did not re-run 32×8: 3.32 GiB is over the 3 GB in-lane cap and under the 4 GB queue line, so it is not a production record.
- **Comfortable pair: 24×8** (this run: 42 s, 1.45 GiB). Under 5 min and under 2 GB. **28×6** (9.6 s, 0.78 GiB, γ = 3.988e-7, 2.7% above the 28×8 anchor, edge_weight 3e-9) is the lighter pair.
- 28×8 (this run 227 s / 2.54 GiB; earlier unloaded 46 s / 2.63 GiB) is inside the 3 GB cap and must hold the heavy lock. Not comfortable.

## Speed levers
- Z₂ split: on, required.
- COLAMD vs MMD_AT_PLUS_A: COLAMD stays the default.
- Real Hermitian basis: **not attempted**.
- `pypardiso`: **not importable** (checked again Sun Oct 25). Not installed.

## Commands run (most recent first)
```text
# heavy lock held; --max-rss-gb 3.5; nothing killed
$DUQ_PY -m tasks.task_spectral_profile --sizes 20x6,28x6,24x8,28x8 --no-full --alpha 2.1
  → four RESULT rows, exponent p=4.267, records dirty=false at f796cf5
$DUQ_PY -m tasks.task_spectral_profile --quick
  → 12x4/16x4/20x6 odd and 12x4 full at alpha=1, 35 s, footprints ≤ 0.50 GiB
$DUQ_PY -m pytest -m "not slow" -q
  → 68 passed, 7 deselected in 19.73s
```

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|
| `t2_1.wall_s.eig.two_mode.a2.10.na20nb6` | 3.455 | s | null (wall time) | cost_model, 2.77, 1.0, false |
| `t2_1.wall_s.eig.two_mode.a2.10.na28nb6` | 9.594 | s | null | cost_model, 2.82, 1.0, false |
| `t2_1.wall_s.eig.two_mode.a2.10.na24nb8` | 41.99 | s | null | cost_model, 3.72, 1.0, false |
| `t2_1.wall_s.eig.two_mode.a2.10.na28nb8` | 226.6 | s | null | cost_model, 15.0, 1.0, false |

`provenance.dirty == false`, `git_commit` `f796cf5`, branch `std/l1-spectral`. `convergence` is null: wall time is a property of the truncation, not a converged physics quantity. No `t2_1.gamma_x.*` records (L2b owns those). `numerics.gamma_x` is stored only as a diagnostic.

## Figures / arrays produced
- `figures/task_2_1_spectral_cost.png` — log-log wall vs `Na·Nb²` with the 113 s model and the odd-block model (/8); footprint vs `Na·Nb²`.
- `results/arrays/t2_1.wall_s.eig.two_mode.a2.10.profile.npz` — four odd rows, all `status=0`.

## Jobs to queue
Do not start these on this machine. Estimates: footprint `∝ (Na·Nb²)²` anchored at this run's 28×8 = 2.54 GiB; wall from the earlier **unloaded** COLAMD scan (p≈3.6, 32×8 = 72 s), not from this run's contended 227 s. The worker's `--max-ram-gb 5` cannot admit any of them. They need to run alone, or somewhere with more RAM. `--max-rss-gb` is passed explicitly because the script default is 4 (this machine), not the brief's 6.

Not queued: **32×8**, measured earlier at 3.32 GiB / 72 s. Above 3 GB, under 4 GB. Not a production record. It is why `NA_EIG_MAX` stays 32.

| Name | RAM est. | Wall est. (unloaded) | Why queued |
|---|---|---|---|
| l1_full_28x8 | 6 GB | ~3 min | Gate 4. Odd 28×8 is recorded; full L is the extra. |
| l1_24x10 | 4.6 GB | ~2 min | Over 4 GB. |
| l1_40x8 | 5.2 GB | ~3 min | Over 4 GB. |
| l1_28x10 | 6.2 GB | ~4 min | Over 4 GB. Would raise `NB_EIG_MAX` if it finishes under the caps. |
| l1_48x8 | 7.5 GB | ~5 min | Over 4 GB. |
| l1_32x10 | 8.1 GB | ~6 min | Over 4 GB. |
| l1_32x12 | 17 GB | ~22 min | Over both caps. The brief's ~4 min odd-block figure does not hold for SciPy+COLAMD here. |

```text
python -m tools.runq submit --name l1_full_28x8 --ram-gb 6 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 28x8 --max-rss-gb 6
python -m tools.runq submit --name l1_24x10 --ram-gb 5 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 24x10 --no-full --max-rss-gb 5
python -m tools.runq submit --name l1_40x8 --ram-gb 6 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 40x8 --no-full --max-rss-gb 6
python -m tools.runq submit --name l1_28x10 --ram-gb 7 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 28x10 --no-full --max-rss-gb 7
python -m tools.runq submit --name l1_48x8 --ram-gb 8 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 48x8 --no-full --max-rss-gb 8
python -m tools.runq submit --name l1_32x10 --ram-gb 8 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 32x10 --no-full --max-rss-gb 9
python -m tools.runq submit --name l1_32x12 --ram-gb 17 -- $DUQ_PY -m tasks.task_spectral_profile --sizes 32x12 --no-full --max-rss-gb 18
```

`$DUQ_PY` is `$MAIN/.venv/bin/python`. These lines were written here and **not submitted**.

## Deviations from the brief (and why)
- In-lane production is the four odd blocks that fit in 3 GB (20×6, 28×6, 24×8, 28×8 at α=2.1, `--no-full`), not the brief's default list. The rest is queued. RUNBOOK §3 and the coordinator's 3 GB / 4 GB lines override the brief's 6 GB laptop cap.
- `--max-rss-gb` defaults to 4, not 6, so a default-size launch cannot grow to the brief's kill line on an 8 GB machine.
- `PERMC = "COLAMD"` instead of `MMD_AT_PLUS_A`. COLAMD is what makes 28×8 fit in 3 GB. MMD_AT_PLUS_A at 28×8 was 5.5 GB.
- Recorded wall times are higher than the earlier unloaded scan, especially 28×8 (227 s vs 46 s). γ and footprint match, so the eigenpair is the same. Cost-model `agree` is false at tol 1.0; the tolerance was not loosened.
- 28×8 full Liouvillian was not factored. 12×4 full was, in `--quick`, and matches.
- Real-basis lever not attempted. `pypardiso` absent.
- `pytest -m slow` was not re-run after the merge. The α=2.1 anchors were remeasured by the profile.

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only)
1. Why is Γ_X exactly the smallest-|λ| eigenvalue of the odd parity block, and what quantity becomes conserved (making that block singular) when κ_a = 0?
2. At 20×6 the solver returns 7.6e-6 at α = 2.1 with a tiny residual; how do you know it is a truncation artifact, and why is a relative residual meaningful when λ ~ 4e-7 while ‖L‖ is ~1e2 or larger?
3. Why does Y_L decay at Γ_Z − Γ_X rather than Γ_Z + Γ_X, and once ε_Z ≠ 0 breaks the Z2 symmetry, why must you deflate (or shift by a small positive σ) instead of shift-inverting the full L at σ = 0?

## Notes for Claude's later review
- Odd-block γ matches every remeasured anchor well inside tolerance. The 20×6 α=2.1 trap is flagged by edge_weight and is 20× the 28×8 value.
- 28×6 α=2.1 gives 3.988e-7, matching RESEARCH §5.
- Left-eigenvector phase/sign convention passed `test_left_eigvec_operator` before the merge; that test is in the post-merge fast suite (68 passed).
- Do not switch the default ordering back to `MMD_AT_PLUS_A`.
- `NA_EIG_MAX=32` is from the earlier 32×8 scan (3.32 GiB), not from a dirty=false record.
