# Status: lane `l4b-tradeoff`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l4b-tradeoff` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | Sun Oct 25 2026, 10:18 AM |
| Last update (EDT) | Sun Oct 25 2026, 10:38 AM |
| Last commit | `9e7c000` `[l4b-tradeoff] add the tradeoff driver and queue the eigen grid` |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first (`323aa09`): `test_snr_helper_matches_formula`, `test_record_ids_match_contract`, `test_grid_and_truncation`, `test_pick_rates_synthetic`, `test_analytic_helpers`, plus four `@pytest.mark.slow` eigen/mesolve tests
- [x] Implementation complete in `tasks/task_2_4b.py` (not executed on the eigen grid)
- [ ] `--quick` run — not started (hard stop; would not be an eigen solve, but no wall-clock left)
- [x] Production eigen grid queued, not started
- [ ] Acceptance gates that need Γ_X(ε) or SNR(ε) — not measured
- [x] Explain-back questions drafted (questions only)

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| 1. Fast tests; full `-m "not slow"` < 2 min | **partial** | `pytest tests/test_l4b_tradeoff.py -m "not slow" -q` → **5 passed, 4 deselected in 1.74s**. Slow tests were **not run**: they call `low_spectrum` / `gamma_x` (sparse eigen). Full-suite timing not re-measured this session. |
| 2. Γ_X(0) full vs odd, anchors | **not run** | Needs the eigen grid. |
| 3. Evenness at α=1.2, ε=±0.5 g₂; no tilt | **not run** | Parity mirror is inside `--part eig --alpha 1.2 --tier 1`. No-tilt is the slow test, not run. |
| 4. S18 within 0.10 for ε ≤ 0.3 g₂ | **not run** | |
| 5. Time-domain Γ_X at α=1.0 | **not run** | `--part tdgx` queued. It calls `gamma_x` (sparse eigen) to set the fit window. |
| 6. TD symmetry, SNR vs linear response, truncation | **not run** | `--part td` queued. |
| 7. Eigen acceptance, cross-checks, dirty=false | **no eigen records** | No production records were written. |
| 8. 37-row grid, both figures, findings, queue | **queue only** | `assemble` builds 37 rows and both figures from whatever records exist. It was not run. Findings table is empty of numbers. Queue is below. |

No small-α points were computed. Nothing under `results/records/t2_4b*` or `results/arrays/t2_4b*`.

## Commands run
```text
$DUQ_PY -m pytest tests/test_l4b_tradeoff.py -m "not slow" -q --tb=line
# before tasks/task_2_4b.py existed:
ERROR tests/test_l4b_tradeoff.py  ModuleNotFoundError: No module named 'tasks.task_2_4b'

$DUQ_PY -m pytest tests/test_l4b_tradeoff.py -m "not slow" -q --tb=short
.....                                                                    [100%]
5 passed, 4 deselected in 1.74s

$DUQ_PY -c "from tasks.task_2_4b import snr_ids_ok, _grid_points; print(snr_ids_ok(), len(_grid_points()))"
snr_ok False
nrows 37
```

No `low_spectrum`, `gamma_x`, `eigs`, or `splu` process was started.

## Records produced
| Record id | Value | Units | Converged | Cross-check |
|---|---|---|---|---|
| (none) | | | | |

## Figures / arrays produced
- None this session. `assemble` writes `results/arrays/t2_4b.grid.npz`, `figures/task_2_4b_tradeoff.png`, `figures/task_2_4b_rates_vs_eps.png`.

## Jobs to queue
Run from the repo root **after this branch is merged**, with `src/spectral.py` and `src/linresp.py` on the tree. Hold `$MAIN/.git/duq-heavy.lock` for every command below (each is over 5 min or over 1.5 GB). Interpreter:

```sh
export MAIN=/Users/halokwok/Desktop/DuQuantum/duquantum-cat-qubit
export DUQ_PY=$MAIN/.venv/bin/python
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
export MPLCONFIGDIR=$MAIN/.orchestrator/mplconfig
```

Do not run two of these at once. Tier-2 jobs ask for 6 GB; this machine's worker admits `--max-ram-gb 5`, so tier 2 does not fit beside anything else and may not fit at all.

| Name | RAM est. | Wall est. | Command |
|---|---|---|---|
| `t2_4b_td_a1.00` | 2 GB | 8 min | `"$DUQ_PY" -m tasks.task_2_4b --part td --alpha 1.0` |
| `t2_4b_td_a1.20` | 2 GB | 10 min | `"$DUQ_PY" -m tasks.task_2_4b --part td --alpha 1.2` |
| `t2_4b_td_a1.40` | 2.5 GB | 12 min | `"$DUQ_PY" -m tasks.task_2_4b --part td --alpha 1.4` |
| `t2_4b_td_a2.10` | 3 GB | 15 min | `"$DUQ_PY" -m tasks.task_2_4b --part td --alpha 2.1` |
| `t2_4b_tdgx` | 2 GB | 15 min | `"$DUQ_PY" -m tasks.task_2_4b --part tdgx` |
| `t2_4b_eig_a1.00_t1` | 2.5 GB | 15 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.0 --tier 1` |
| `t2_4b_eig_a1.20_t1` | 2.5 GB | 14 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.2 --tier 1` |
| `t2_4b_eig_a1.40_t1` | 2.5 GB | 18 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.4 --tier 1` |
| `t2_4b_eig_a2.10_t1` | 3 GB | 28 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 2.1 --tier 1` |
| `t2_4b_eig_a1.00_t2` | 6 GB | 48 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.0 --tier 2` |
| `t2_4b_eig_a1.20_t2` | 6 GB | 27 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.2 --tier 2` |
| `t2_4b_eig_a1.40_t2` | 6 GB | 32 min | `"$DUQ_PY" -m tasks.task_2_4b --part eig --alpha 1.4 --tier 2` |
| `t2_4b_assemble` | 1 GB | 1 min | `"$DUQ_PY" -m tasks.task_2_4b --part assemble` |

`--part eig` skips a point whose `t2_4b.gamma_x.eig...` record already exists, so an interrupted job resumes. Tier 1 is ε/g₂ ≤ 1, including 0. Tier 2 is ε/g₂ ∈ {1.5, 2, 3}. The α=1.2 tier-1 job also evaluates ε = −0.5 g₂ once, as the parity cross-check, and does not add a grid row for it.

Pending record families, one id per (α, ε) on the 37-row grid (4 zeros + 30 + 3): `t2_4b.gamma_x.eig.*`, `t2_4b.gamma_z.eig.*`, `t2_4b.leakage.td.*`, `t2_4b.snr.td.*.T*us` (blocked, see decision), `t2_4b.gamma_x.td.two_mode.a1.00.ez0.1g2` and `.ez0.3g2`.

## Deviations from the brief
- `src/spectral.py` is `std/l1-spectral` at `d5d9709`. `src/linresp.py` is `prod/linresp` (`response` and the 2×2 model). `std/l4a-readout` was dirty (`?? results/records/t2_3.ring_freq.linresp.two_mode.a2.10.json`), so that worktree was not touched. Frozen `src/model.py`, `src/config.py`, `src/analysis.py` were not edited. `prod/release` was not merged.
- `--alpha` also limits `--part td` to one α, so the time-domain job can be split. Default `--part td` still runs every α.
- Even-sector X_L is the rate nearest 2 κ_a α² coth(2α²). `low_spectrum` in `d5d9709` drops the deflated eigenvalue, and the l1 brief's own test says that rate is `rates[0]`, not `rates[1]`. The chosen index is written into the γ_Z notes. This was not remeasured here.
- No eigen solve and no mesolve were started. Hard stop 10:45 EDT, and the heavy lock was held by a live `l4a-readout` `task_2_3 --part all` (owner stamp 09:42). The lock was not deleted.
- Tier 2 at 6 GB is listed because the brief requires it. It is above the 5 GB worker cap on this 8 GB machine.

## DECISION NEEDED

### DECISION NEEDED (l4b-tradeoff, 10:38 EDT)
Question: `record()` rejects the SNR id because the tag `T{T:.1f}us` has an uppercase `T`.
Evidence: `src/results.py` `ID_RE = ^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`; probe id `t2_4b.snr.td.two_mode.a1.00.ez1g2.T1.0us` raises `ValueError`; `snr_ids_ok()` printed `False`. The brief's id `t2_4b.snr.td.two_mode.a1.20.ez1.5g2.T0.5us` is the same pattern. `tasks/task_2_4b.py` `snr_ids_ok`.
Options: A) Integrator allows `T` in tags (CONTRACT §6.3 already writes the tag that way). B) Change the tag to a lowercase `t` (forbidden to do silently).
Default if no answer by 12:00 EDT: A. Wait. Do not lowercase. When `--part td` runs, SNR values still go into `results/arrays/t2_4b.td.npz` and `t2_4b.grid.npz`. JSON SNR records are not written until `record()` accepts the id.

## Explain-back for Harshit (questions only)
1. The readout drive cannot tilt the double well. So where does the extra bit-flip rate come from, and why does it carry e^{−2α²} rather than the e^{−4α²} of the undriven code-space channel?
2. Γ_Z rises by exactly 2ε_Z²/(κ₂α²). Why is that unavoidable for any readout, and how is it tied to the SNR rate you measured (and to the e^{2α²} figure of merit)?
3. Without the Z₂ split, how did you know which eigenvalue of the deflated Liouvillian is Γ_X, and why should anyone trust the number at ε_Z = 3g₂, where the buffer holds about 2 photons?

## Notes for Claude's later review
- Tolerances were not loosened. Gates 2–8 have no numbers because the solves were not started.
- `low_spectrum` already returns per-eigenvalue `rel_residual`, `edge_weight`, and `cond_est` lists, and no eigenvectors. The private eigensolver fallback was not added.
- There is no tilt term in this lane. Γ_X is treated as even in ε_Z. Negative ε is computed only for the α=1.2, ε=0.5 parity check.
- Optional step 9 (`extra_H`) was cut, first on the brief's cut line.
