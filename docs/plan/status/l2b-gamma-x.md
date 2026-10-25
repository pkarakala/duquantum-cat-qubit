# Status: lane `l2b-gamma-x`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l2b-gamma-x` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | Sun Oct 25 2026, 10:18 AM |
| Last update (EDT) | Sun Oct 25 2026, 10:45 AM |
| Last commit | pipeline commit on this branch (see `git log -1`) |

Hard stop at 10:45 AM EDT. No eigen solve and no time-domain trace was started. There are **no** `t2_1.gamma_x.*` records and no Γ_X numbers from this lane.

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Merged `std/l1-spectral` (`d5d9709`) with `--no-ff` so `src/spectral.py` is on this branch. Merge commit message starts `[l2b-gamma-x]`. No conflicts.
- [x] Tests written (`tests/test_l2b_gamma_x.py`). Pure tests were run and passed. Anchor, trap, and slow tests were **not** run.
- [x] Implementation of the five task scripts, the notebook, and the pure helpers is on the branch. Not exercised on a Liouvillian.
- [ ] `--quick` run — not started (it calls `gamma_x` / `mesolve`)
- [ ] Production runs — none. All queued below.
- [ ] Acceptance gates in brief §8 — not met, except the pure-test slice of gate 1 and this status file
- [x] Explain-back questions drafted (questions only)

## Solver cost copied from l1 (overrides the brief's cost model)
`NA_EIG_MAX = 32`, `NB_EIG_MAX = 8` (l1 recommendation; `src/config.py` is frozen and still has `None`. This lane does not edit it). Comfortable pair **24×8** (42 s, 1.45 GiB). **28×8** is 2.54 GiB and 46 s unloaded / 227 s on a busy machine. Odd-block footprint `2.54 GiB * (Na*Nb^2/1792)^2`. Unloaded wall `46 s * (Na*Nb^2/1792)^3.61`. Do not use the brief's 113 s full-L model for COLAMD on this CPU. `PERMC` stays `COLAMD`.

## Acceptance gates (brief §8)
| Gate | Result | Evidence |
|---|---|---|
| 1. fast suite, and slow tests | **partial** | `pytest tests/test_l2b_gamma_x.py -m "not slow" -k "not test_one_mode_anchors and not test_truncation_trap_flagged and not test_td_vs_eig_one_mode" -q` → **13 passed, 4 deselected, 0.07 s**. Deselected on purpose: those four call `solve` or `mesolve`. Not started. Whole-suite `pytest -m "not slow"` was not re-run. |
| 2. anchors within 1% | **not run** | No anchor table from this lane. Do not treat l1's `numerics.gamma_x` on the wall-time records as these records. |
| 3. claimed eig records | **fail** | No `t2_1.gamma_x.eig.*` files. |
| 4. td vs eig at α ∈ {0.8, 1.0, 1.2, 1.4} | **fail** | No time-domain runs. |
| 5. channels, c, κ_a exponent | **fail** | Code only. |
| 6. thermal n_th | **fail** | Code only. |
| 7. five figures, notebook, dirty=false | **fail** | No production figures. Notebook `notebooks/06_task_2_1_bit_flips.ipynb` loads records and prints a missing-file line when they are absent (`RERUN=False`). |
| 8. status + queue | **pass** | This file. Nothing was submitted to `tools.runq`. |

## Commands run
```text
# pure tests only; eigen tests deselected and not executed
$DUQ_PY -m pytest tests/test_l2b_gamma_x.py -m "not slow" \
  -k "not test_one_mode_anchors and not test_truncation_trap_flagged and not test_td_vs_eig_one_mode" -q
# 13 passed, 4 deselected in 0.07s
```

## Records produced
None. No `results/records/t2_1.gamma_x.*`, no `t2_1.gamma_fit.*`, no `t2_1.channel2_c.*`, no `t2_1.kappa_a_exponent.*`, no `t2_1.gamma_local_slope.*`.

The merge brought l1's four `t2_1.wall_s.eig.two_mode.a2.10.na*` wall-time records. They are not Γ_X claims. L2b does not own them and did not rewrite them.

## Figures / arrays produced
None from this lane.

## Jobs to queue
Not submitted. `$DUQ_PY` is `$MAIN/.venv/bin/python` with `MAIN=/Users/halokwok/Desktop/DuQuantum/duquantum-cat-qubit`. Set `XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"` and `MPLCONFIGDIR=$MAIN/.orchestrator/mplconfig`. Hold `$MAIN/.git/duq-heavy.lock` for anything over 1.5 GB or 5 min. One such job at a time. Do not start a point whose estimate is above 3 GB or 15 min on this 8 GB machine.

Run in this order. Later scripts read earlier records.

| Name | RAM est. | Wall est. | Command |
|---|---|---|---|
| l2b_eig_1m | 1 GB | a few minutes (unmeasured; one-mode N≤80) | `$DUQ_PY -m tasks.task_2_1_eig --model one_mode` |
| l2b_eig_2m_small | 2.5 GB | ~5–15 min unloaded | `$DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 0.8 1.0 1.2 1.4 --nb-list 6,8` |
| l2b_eig_2m_a1.6_a2.1 | 2.6 GB peak at 28×8; **converged may be false** because chosen Nb is `nb[-2]=6` while 6→8 moves α=2.1 by 2.6% | 28×8 is 46 s unloaded, ~4 min if the machine is busy, times several α | `$DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 1.6 1.8 2.1 --nb-list 6,8` |
| l2b_anchors | 2.6 GB | 4×28×8: ~3 min unloaded, up to ~15 min busy | `$DUQ_PY -m pytest tests/test_l2b_gamma_x.py -m slow -q` and `$DUQ_PY -m tasks.task_2_1_eig --anchors` |
| l2b_td_1m | unmeasured, one-mode | 4 traces × 2 tolerances; queue if one trace exceeds 15 min | `$DUQ_PY -m tasks.task_2_1_td --model one_mode` |
| l2b_td_2m_g2 | unmeasured | α=1.0 and 1.4 first | `$DUQ_PY -m tasks.task_2_1_td --model two_mode --alpha 1.0 1.4` |
| l2b_td_2m_rest | unmeasured | α=0.8 and 1.2 | `$DUQ_PY -m tasks.task_2_1_td --model two_mode --alpha 0.8 1.2` |
| l2b_channels | 1 GB (one-mode κ sweep) | after one-mode eig; the κ sweep is 4×5×2 one-mode solves | `$DUQ_PY -m tasks.task_2_1_channels` |
| l2b_thermal_1m | 1 GB | 3 × n_th × the one-mode grid | `$DUQ_PY -m tasks.task_2_1_thermal --model one_mode` |
| l2b_figures | 1 GB without `--committor` | reads records | `$DUQ_PY -m tasks.task_2_1_figures` |
| l2b_committor | one-mode small; two-mode panel uses the α=2.1 record's truncation | after both eig records exist | `$DUQ_PY -m tasks.task_2_1_figures --committor` |

These need more than 3 GB (l1 formula or l1 measurement). Not on this laptop. The worker's `--max-ram-gb 5` cannot admit the larger ones; run them alone or not at all.

| Name | RAM est. | Wall est. (unloaded odd block) | Why |
|---|---|---|---|
| l2b_eig_2m_brief_nb | up to ~5 GB at α=1.4 with Nb=10 | several minutes | Brief default `--nb-list` is 6,8,10 (α≤1.4) or 8,10,12 (above). Nb=10 at the crossing Na exceeds 3 GB. |
| l2b_eig_2m_a2.0 | ~2–4 GB | ~7 min | Brief queue row. Na 26,30,34 × Nb 8,10,12. |
| l2b_eig_2m_a2.2 | ~3–6 GB | ~10 min | Na 30,34,38 × Nb 8,10,12. |
| l2b_eig_2m_a2.4 | ~4 GB+ | ~12 min | Na 32,36,40 × Nb 8,10,12. |
| l2b_eig_2m_a2.6 | ~5 GB | ~14 min | Na 34,38,42 × Nb 8,10,12. |
| l2b_eig_2m_a2.8 | ~6 GB | ~17 min | Na 36,40,44 × Nb 8,10,12. |
| l2b_eig_2m_a3.0 | ~7 GB | ~19 min | Na 38,42,46 × Nb 8,10,12. |
| l2b_full_l | ~4× the odd footprint | ~3–8× the odd wall | Every `--full-l-check`, including α=1.0 and 1.4. Full 28×8 was estimated ~6 GB by l1. |
| l2b_thermal_2m | same as the two-mode eig at that α | after two-mode nth0 records exist | `$DUQ_PY -m tasks.task_2_1_thermal --model two_mode` |

```text
python -m tools.runq submit --name l2b_eig_1m --ram-gb 1 -- $DUQ_PY -m tasks.task_2_1_eig --model one_mode
python -m tools.runq submit --name l2b_eig_2m_small --ram-gb 2.5 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 0.8 1.0 1.2 1.4 --nb-list 6,8
python -m tools.runq submit --name l2b_eig_2m_a1.6_a2.1 --ram-gb 2.6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 1.6 1.8 2.1 --nb-list 6,8
python -m tools.runq submit --name l2b_anchors --ram-gb 2.6 -- $DUQ_PY -m tasks.task_2_1_eig --anchors
python -m tools.runq submit --name l2b_td_1m --ram-gb 1 -- $DUQ_PY -m tasks.task_2_1_td --model one_mode
python -m tools.runq submit --name l2b_td_2m_g2 --ram-gb 2.5 -- $DUQ_PY -m tasks.task_2_1_td --model two_mode --alpha 1.0 1.4
python -m tools.runq submit --name l2b_td_2m_rest --ram-gb 2.5 -- $DUQ_PY -m tasks.task_2_1_td --model two_mode --alpha 0.8 1.2
python -m tools.runq submit --name l2b_channels --ram-gb 1 -- $DUQ_PY -m tasks.task_2_1_channels
python -m tools.runq submit --name l2b_thermal_1m --ram-gb 1 -- $DUQ_PY -m tasks.task_2_1_thermal --model one_mode
python -m tools.runq submit --name l2b_figures --ram-gb 1 -- $DUQ_PY -m tasks.task_2_1_figures
python -m tools.runq submit --name l2b_committor --ram-gb 3 -- $DUQ_PY -m tasks.task_2_1_figures --committor
python -m tools.runq submit --name l2b_eig_2m_a2.0 --ram-gb 4 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 2.0 --na-list 26,30,34 --nb-list 8,10,12
python -m tools.runq submit --name l2b_eig_2m_a2.2 --ram-gb 6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 2.2 --na-list 30,34,38 --nb-list 8,10,12
python -m tools.runq submit --name l2b_eig_2m_a2.4 --ram-gb 6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 2.4 --na-list 32,36,40 --nb-list 8,10,12
python -m tools.runq submit --name l2b_eig_2m_a2.6 --ram-gb 6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 2.6 --na-list 34,38,42 --nb-list 8,10,12
python -m tools.runq submit --name l2b_eig_2m_a2.8 --ram-gb 7 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 2.8 --na-list 36,40,44 --nb-list 8,10,12
python -m tools.runq submit --name l2b_eig_2m_a3.0 --ram-gb 8 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 3.0 --na-list 38,42,46 --nb-list 8,10,12
python -m tools.runq submit --name l2b_full_l_a1.0 --ram-gb 6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 1.0 --full-l-check
python -m tools.runq submit --name l2b_full_l_a1.4 --ram-gb 6 -- $DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 1.4 --full-l-check
python -m tools.runq submit --name l2b_thermal_2m --ram-gb 3 -- $DUQ_PY -m tasks.task_2_1_thermal --model two_mode
```

Laptop-safe two-mode commands pass `--nb-list 6,8`. Chosen Nb is then `nb[-2] = 6`, not 8. That is a smaller truncation than the brief's crossing point. At α=2.1 the 6→8 shift is 2.6%, so `convergence.converged` can be false. Do not claim those rows. The 20×6 block at α=2.1 remains the trap (about 7.6e-6, edge weight above 1e-6). The code does not loosen that cut.

## Deviations from the brief
- No production Γ_X, because of the 10:45 hard stop. Every physics job is queued, including the small-α ones the brief calls never-cut.
- `--nb-list 6,8` on the laptop-safe two-mode jobs, so Nb=10/12 is not allocated on an 8 GB machine. Explicit lists are not clipped; auto-extend stops at `NA_CAP=32`, `NB_CAP=8`.
- `--quick` on channels skips the κ_a eigen sweep and only reads records. Production `task_2_1_channels` does the sweep.
- Committor Wigner runs only with `--committor`, so a record-only figure job cannot start an eigen solve.
- `std/l1-spectral` is merged, so this branch also contains l1's files (`src/spectral.py`, `tests/test_l1_spectral.py`, `tasks/task_spectral_profile.py`, l1 status, l1 wall-time records and the cost figure). Those were not edited here. `src/model.py`, `src/config.py`, and `src/analysis.py` were not edited.
- TDD red commit was skipped: the hard stop left one commit with tests and implementation together. Pure tests were green before that commit. The four eigen/trace tests were not executed, red or green.

## DECISION NEEDED
None. No anchor was compared, and no fit for `c` or `c_th` exists, so there is nothing to escalate. If a queued anchor job misses by more than 1%, stop and escalate; do not edit the anchors.

## Explain-back for Harshit (questions only)
1. Your Γ_X is an eigenvalue of a matrix you built yourself. How do you know it is the decay rate of Re⟨a⟩ the prompt asks for, and not a truncation artefact like the 20×6 value at α = 2.1?
2. The deck says γ ≲ 2, the Golden Rule says 4, and your fit gives about 2.5 to 2.9. Which is right at α = 2.1, and which numerical experiment in your repo proves which mechanism dominates there?
3. Why does keeping the buffer mode explicit make bit flips about 3× faster at α = 2.1, and what does that imply for hardware with κ_b/g₂ ≈ 3.4?

## Notes for Claude's later review
- Do not grade this lane as having produced Γ_X. The pipeline is in the tree; the numbers are not.
- Tolerances in the tests are the brief's. They were not loosened. The four tests that would check anchors and the 20×6 trap were not run.
- l1 already reproduced those anchors on this solver (`d5d9709`). That is l1's evidence, not a substitute for this lane's records.
