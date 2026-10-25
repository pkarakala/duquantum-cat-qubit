# Status: lane `l2a-gamma-z`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `std/l2a-gamma-z` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 09:25 |
| Last update (EDT) | 2026-10-25 10:05 |
| Last commit | results `6b19fb4`; record provenance `24782e5` |

`src/spectral.py` is **not** on this branch. Time-domain parity fits and the analytic checks are done. `--eig` and `--summary` are under Jobs to queue. That is why the state is `DONE_WITH_CONCERNS`: no even-block eigenvalues, and the slope record plus both production figures are produced by the queued `--summary`.

## Answer

Γ_Z follows 2κ_a α² coth(2α²) at every α. The largest miss is 0.54% (α=1.0); at α=2.7 it is 0.097%. Nb 6→8 changes Γ_Z by at most 3.3×10⁻⁷ (α=1.8). A straight line through the six points, weighted by 1/uncertainty², gives slope/2κ_a = **0.9861 ± 0.0069** (the number `--summary` will record). The same points unweighted give **0.9958**, which is the coth-grid value 0.9959. The weighted fit sits lower because the fit stderr is ~10⁻⁶ and does not cover a coherent 0.1–0.5% offset under the coth curve, so α=1 is over-weighted. Both ratios are inside 2% of 1 and of 0.9959. The even-block eigenvalue was not run. Réglade et al. see a slope ~25% above this model; that is outside the Hamiltonian and was not fitted.

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, runbook
- [x] Tests written first (`test_prediction_values`, `test_offset_fit_needed`, `test_ids_and_window`, `test_cat_is_dark`, `test_slope_of_predictions`, `test_small_run_alpha1`)
- [x] Implementation complete
- [x] `--quick` run passes (≤ 2 min)
- [x] Production time-domain runs done (6 alphas). Eigen and summary queued
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. Fast tests < 20 s; slow test passes | pass | `pytest tests/test_l2a_gamma_z.py -m "not slow" -q` → `5 passed in 8.01s`. Earlier cold run 15.56 s. `pytest -m slow` → `1 passed in 6.63s` |
| 2. `--quick` ≤ 2 min, quick paths only | pass | `python -m tasks.task_2_2 --quick` → `real 20.48`. Writes `results/quick/` and `figures/quick/` only. Alphas 1.0 and 1.4 |
| 3. Converged, Nb-insensitive, top Fock < 1e-6 | pass | Every td record `converged: true`. Largest Nb 6→8 relative change 3.33e-7 (α=1.8). Largest `max_top2_a` 8.36e-8 (α=1.8) |
| 4. coth and 2κ_a n̄ within 2% | coth pass; n̄ pass except α=1 | coth rel_diff 0.097%…0.545%, all `agree: true`. `analytic_2kappa_nbar` agrees for α≥1.4 (worst 0.14% at α=1.4). α=1 is 7.86%, `agree: false`. See DECISION NEEDED |
| 5. Fit quality | pass | `rel_rms_residual` ≤ 1.98e-5. `|gamma_t0_0p5/gamma − 1|` ≤ 1.2e-5. `|C_fit − 1/cosh|` is 5.0e-3 at α=1.0 and 1.4e-3 at α=1.4 |
| 6. Slope within 2% of 0.9959 and of 1 | pass on the numbers; record queued | Weighted ratio 0.9861, `|0.9861−0.9959|=0.0098` < `0.02×0.9959`, `|0.9861−1|=0.014` < 0.02. The record `t2_2.slope_over_2kappa_a.td.two_mode` is written by `--summary` |
| 7. α=2.1 vs 1.3a's 0.5135 | pass | Record cross-check `intro_1_3a_inflation_fit` rel_diff 0.205%, tol 0.02, `agree: true`, ref `t1_3a.gamma_z.td.two_mode.a2.10` |
| 8. Eigen acceptance, or queued | queued | `src/spectral.py` missing. `python -m tasks.task_2_2 --eig` prints `SKIP --eig` and does not simulate. Six eig runs plus `--summary` are below |
| 9. dirty false, figures, notebook | partial | Every td record `provenance.dirty: false`, `git_commit: 24782e5`. Figures are drawn by `--summary` (not on disk yet). Notebook `notebooks/07_task_2_2_phase_flips.ipynb` loads the six td records with `RERUN = False` and prints the table; eig, slope and both PNGs are reported as queued |
| 10. This file | pass | Answer, gates, records, jobs, decision, questions |

## Commands run (most recent first)
```text
"$DUQ_PY" -m tasks.task_2_2 --alpha 2.7   # then 2.4, 2.1, 1.8, 1.4, 1.0, each its own process
td t2_2.gamma_z.td.two_mode.a2.70 ... gamma=0.851138 pred=0.851962 rel=-0.0967% ... converged=True wall=40.4s   real 55.24
td ...a2.40 gamma=0.672329 pred=0.673155 rel=-0.1227% converged=True wall=45.6s   real 62.18
td ...a2.10 gamma=0.514553 pred=0.515385 rel=-0.1613% converged=True wall=36.1s   real 50.85
td ...a1.80 gamma=0.377810 pred=0.378652 rel=-0.2223% converged=True wall=36.0s   real 52.36
td ...a1.40 gamma=0.228381 pred=0.229240 rel=-0.3750% converged=True wall=34.9s   real 49.97
td ...a1.00 gamma=0.120568 pred=0.121228 rel=-0.5447% converged=True wall=35.8s   real 51.86
DECISION NEEDED printed for alpha=1.0 (nbar check only)

"$DUQ_PY" -m pytest tests/test_l2a_gamma_z.py -m "not slow" -q
5 passed, 1 deselected in 8.01s

"$DUQ_PY" -m tasks.task_2_2 --quick
real 20.48
td ...a1.00 gamma=0.120566 rel=-0.5465% converged=True
td ...a1.40 gamma=0.228374 rel=-0.3777% converged=True
saved figures/quick/task_2_2_parity_decay.png
saved figures/quick/task_2_2_gamma_z_vs_alpha2.png

"$DUQ_PY" -m tasks.task_2_2 --eig
SKIP --eig: src/spectral.py is not on this branch (l1-spectral is not merged).

"$DUQ_PY" -m pytest tests/test_l2a_gamma_z.py -m slow -q
1 passed, 5 deselected in 6.63s
```

Each production process was 50–62 s, under the 5 min / 1.5 GB heavy-lock bar (α=2.7 is the largest basis, 38×8, and the brief's RAM estimate is < 1 GB). The machine lock was held the whole time by `l4a-readout 09:42 task_2_3 production 40x18`. It was not stale and was not removed. These sweeps did not take it.

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|
| `t2_2.gamma_z.td.two_mode.a1.00` | 0.120568 | 1/us | true (Na 22, Nb 8) | analytic_coth 0.545% / 0.02 / yes; analytic_2kappa_nbar 7.86% / 0.02 / **no** |
| `t2_2.gamma_z.td.two_mode.a1.40` | 0.228381 | 1/us | true (26, 8) | analytic_coth 0.375% / 0.02 / yes; analytic_2kappa_nbar 0.143% / 0.02 / yes |
| `t2_2.gamma_z.td.two_mode.a1.80` | 0.377810 | 1/us | true (30, 8) | analytic_coth 0.222% / 0.02 / yes; analytic_2kappa_nbar 0.0002% / 0.02 / yes |
| `t2_2.gamma_z.td.two_mode.a2.10` | 0.514553 | 1/us | true (32, 8) | analytic_coth 0.161% / 0.02 / yes; analytic_2kappa_nbar 0.0035% / 0.02 / yes; intro_1_3a_inflation_fit 0.205% / 0.02 / yes |
| `t2_2.gamma_z.td.two_mode.a2.40` | 0.672329 | 1/us | true (36, 8) | analytic_coth 0.123% / 0.02 / yes; analytic_2kappa_nbar 0.0011% / 0.02 / yes |
| `t2_2.gamma_z.td.two_mode.a2.70` | 0.851138 | 1/us | true (38, 8) | analytic_coth 0.0967% / 0.02 / yes; analytic_2kappa_nbar 0.0009% / 0.02 / yes |
| `t2_2.gamma_z.eig.two_mode.a*.**` | — | — | — | queued |
| `t2_2.slope_over_2kappa_a.td.two_mode` | 0.9861 ± 0.0069 (computed, not yet a record) | 1 | — | queued with `--summary`. Unweighted on the same points: 0.9958. coth-grid anchor 0.9959 |

Uncertainty on each Γ_Z is max(fit stderr, Na spread, Nb spread), which here is the fit stderr (7.9×10⁻⁷ at α=1 up to 7.5×10⁻⁶ at α=2.7). Truncation spread is far smaller.

## Figures / arrays produced
- Arrays: `results/arrays/t2_2.gamma_z.td.two_mode.a{1.00,1.40,1.80,2.10,2.40,2.70}.npz`
- Production figures `figures/task_2_2_parity_decay.png` and `figures/task_2_2_gamma_z_vs_alpha2.png` are drawn by `--summary` (queued).
- Quick smoke figures: `figures/quick/task_2_2_parity_decay.png`, `figures/quick/task_2_2_gamma_z_vs_alpha2.png` (not committed).

## Jobs to queue (for the integrator)
Run from the repo root after this lane is merged. `$DUQ_PY` is `/Users/halokwok/Desktop/DuQuantum/duquantum-cat-qubit/.venv/bin/python`. Wall times are the RESEARCH §9 full-L cost model scaled by ~1/8 for the even block, not measurements. The largest factorization is Na=38, Nb=8.

| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs (record ids) |
|---|---|---|---|---|
| `t2_2_eig_a1.00` | `python -m tools.runq submit --name t2_2_eig_a1.00 --ram-gb 1 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 1.0` | 1 | 2 min | `t2_2.gamma_z.eig.two_mode.a1.00` |
| `t2_2_eig_a1.40` | `python -m tools.runq submit --name t2_2_eig_a1.40 --ram-gb 1 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 1.4` | 1 | 2 min | `t2_2.gamma_z.eig.two_mode.a1.40` |
| `t2_2_eig_a1.80` | `python -m tools.runq submit --name t2_2_eig_a1.80 --ram-gb 1.5 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 1.8` | 1.5 | 3 min | `t2_2.gamma_z.eig.two_mode.a1.80` |
| `t2_2_eig_a2.10` | `python -m tools.runq submit --name t2_2_eig_a2.10 --ram-gb 1.5 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 2.1` | 1.5 | 4 min | `t2_2.gamma_z.eig.two_mode.a2.10` |
| `t2_2_eig_a2.40` | `python -m tools.runq submit --name t2_2_eig_a2.40 --ram-gb 2 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 2.4` | 2 | 5 min | `t2_2.gamma_z.eig.two_mode.a2.40` |
| `t2_2_eig_a2.70` | `python -m tools.runq submit --name t2_2_eig_a2.70 --ram-gb 2 -- $DUQ_PY -m tasks.task_2_2 --eig --alpha 2.7` | 2 | 6 min | `t2_2.gamma_z.eig.two_mode.a2.70` |
| `t2_2_summary` | `python -m tools.runq submit --name t2_2_summary --ram-gb 1 -- $DUQ_PY -m tasks.task_2_2 --summary` | 1 | 1 min | slope record, eig cross-checks on the td records, both PNGs. Run after the eig jobs if the figure should include eigenvalues; it is safe before them too |

Thermal (α=2.1, n_th=0.05) was not run. It is optional and first on the brief's cut line.

## Deviations from the brief (and why)
- `test_cat_is_dark`: `||H|C+⟩||` at Na=12, Nb=4, α=1 is 2.02×10⁻³, the Fock tail of the cat. The same residual with the α=2.1 drive `C.EPS_D` is 16.3, so the ε_d trap is still caught. The brief's 1e-6 bound holds at Na=20 (4.8×10⁻⁸). The test asserts `< 1e-2` at Na=12 and `< 1e-6` at Na=20. Parity of the cat is 1 at both.
- `fit_exp_offset` p0 is `(gamma, A, C)`. The call uses `(gamma_z_pred, 1 − parity_ss, parity_ss)`.
- `--quick` with no `--alpha` runs α=1.0 and 1.4 only, as §7 specifies.
- `gamma_from_n` is 0 at α=2.7: ⟨n⟩ does not move enough to identify a rate, and a raw fit returned ~7000 /µs. The steady offset is kept. At α=2.1 and 2.4 the stored `gamma_from_n` (1.15 and 5.87) is still not the parity rate; the brief already says that quantity is meaningful only for α≤1.4. It is not used as Γ_Z.
- Eigen cross-check and the slope record are not in this commit. `--summary` adds them. The 1.3a comparison at α=2.1 is already on the td record (the wrapped intro record exists).

## DECISION NEEDED
> **Q:** Γ_Z(α=1.0) matches 2κ_aα²coth(2α²) to 0.54% (0.120568 vs 0.121228) after convergence (Na=22, Nb=8; Nb 6→8 relative change 2.6×10⁻⁹), but 2κ_a·n̄_meas misses Γ_Z by 7.86% (n̄_meas=0.957). Accept as the parity-weighted steady state, or investigate a two-mode error?
> **Options:** A) report `analytic_2kappa_nbar` with `agree: false` at α=1 only; the coth check stays the rate test. B) block until reviewed.
> **Recommendation:** A. The equal C+/C− mixture has n_eq=α²coth(2α²)=1.037, and Γ_Z=2κ_a n_eq. The parity steady state is not that mixture: ⟨n⟩_ss = n_eq + P_ss (n_+ − n_-)/2 with P_ss=1/cosh(2α²)=0.266, which lowers ⟨n⟩ by 7.6% to 0.964. The simulated asymptote is 0.957. At α≥1.4 the same shift is ≤0.16% and the check agrees. This is not the κ_a/κ₂ dressing.
> **Blocking?** no: the other five alphas are finished and agree on both checks.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why does the parity settle at 1/cosh(2α²) instead of 0, and what would a pure exponential fit have reported at α = 1.0?
2. Why is 2κ_a·n̄ with the measured n̄ an identity check rather than an independent prediction, and where does the coth(2α²) correction come from?
3. Why is Γ_Z insensitive to the buffer truncation while Γ_X at α = 2.1 needed Nb = 8, and which of your two Γ_Z methods (time-domain fit, even-block eigenvalue) would you trust at α = 2.7, and why?

## Notes for Claude's later review
- Do not loosen the α=1 n̄ tolerance. The 7.86% is the parity weight, and the rate itself is 0.54% from the coth law. `|C_fit − 1/cosh|` at α=1 is 5.0×10⁻³, inside the 0.01 gate, and it is the tightest margin on that gate (2.5 lifetimes is not infinity).
- Na and Nb sweeps agree far inside 10⁻³. No truncation was extended.
- `gamma_from_n` above α≈1.8 is not a second measurement of Γ_Z.
- The weighted slope 0.986 versus the unweighted 0.996 is the fit-stderr weighting, not a different data set. `--summary` records the weighted one, as the brief specifies.
- Heavy lock: held by l4a the whole time; these jobs were left outside it on purpose because each process was ~1 min.
