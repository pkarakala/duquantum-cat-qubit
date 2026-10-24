# Brief `l2a-gamma-z`: Task 2.2: phase-flip rate Gamma_Z

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l2a-gamma-z`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/04-l2a-gamma-z.md`, then execute this brief exactly. Keep `docs/plan/status/l2a-gamma-z.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l2a-gamma-z` | `std/l2a-gamma-z` (from `standard-track`) | `l0-core` (required); `l1-spectral` (only for the eigen cross-check) | fast | 1.5 h | Phase 1, Sat Oct 24, 8:45 PM (before G1 9:45 PM) |

## 1. Goal and why
Challenge §2, Task 2.2: start in the even cat |+⟩_L = |C+⟩, track memory parity ⟨P(t)⟩, fit its decay to get Γ_Z, sweep α and compare the slope of Γ_Z vs α² with 2κ_a. This is the "never cut" Γ_Z check of the project: it validates the two-mode model, the fit machinery (offset fit) and the convergence harness on a quantity with a closed-form prediction, and it supplies the Γ_Z(α) data the Lab site plots (`errors.json → gamma_z`). Answer in the status file: **does Γ_Z follow 2κ_aα², and what is slope/2κ_a?**

Physics you need (RESEARCH §1, §4.2, §6):
- Convention: Γ_Z = decay rate of ⟨P⟩, P = e^{iπ a†a} on the memory (the prompt's 2κ_aα²). The per-direction rate is κ_aα².
- 2κ_a = 0.116867 /µs (κ_a = 2π·9.3e-3 = 0.0584336 rad/µs, `C.KAPPA_A`).
- **Prediction:** Γ_Z = 2κ_aα²·coth(2α²). Values: α=1.0: 0.12123; 1.4: 0.22924; 1.8: 0.37865; 2.1: 0.51538; 2.4: 0.67316; 2.7: 0.85196 /µs. At α=1.0 the coth factor is +3.7% over 2κ_aα² (0.11687), i.e. larger than the 2% gate, so always compare with the coth form.
- Identity: tanh x + coth x = 2 coth 2x, so the steady photon number of the C± mixture, n̄ = (α²tanh α² + α²coth α²)/2 = α²coth(2α²), gives 2κ_a·n̄ = prediction exactly in the code space. 2κ_a·n̄ with the **measured** n̄ is therefore a dressing check (Task 1.3a: 0.5146 from n̄ vs 0.5154 coth), not an independent theory.
- **Steady parity = 1/cosh(2α²)**: 0.2658 (α=1.0), 0.03967 (1.4), 0.00307 (1.8), 3.0e-4 (2.1), ~0 above. A pure exponential on log|y| (`fit_exp_decay`) is biased (−55% at α=1.0). Fit **A·e^{−Γt} + C** with `src.analysis.fit_exp_offset`.
- |C±⟩⊗|0⟩_b is a dark state of H when ε_d = α²g₂ (g₂a²b† − ε_d b† cancels on it), and a|C±⟩ ∝ |C∓⟩. So there is no inflation transient and the buffer stays near vacuum: Γ_Z should be insensitive to Nb. Dressing by κ_a/κ₂ ≈ 1% is the only two-mode correction.
- Thermal (optional): Γ_Z = 2κ_a[(1+2n_th)·n̄ + n_th] = 0.5728 /µs at α=2.1, n_th=0.05 (n̄ = α²coth 2α²).
- Even Liouvillian block: rates = {0 (steady state), Γ_Z (X_L/parity mode), then leakage rates ~κ₂}. So `rates[1]` of the even block is Γ_Z. (Z_L, Y_L are odd: Γ_X and Γ_Z − Γ_X.)
- Existing result: Task 1.3a fitted 0.5135 /µs at α=2.1 from vacuum inflation (Na=32, Nb=12, `fit_exp_decay` after 1 µs; offset is only 3e-4 there).

## 2. Read first
- `docs/plan/CONTRACT.md` §2 (env), §3 (`two_mode`, `cat2`, `loss_jumps`), §4 (`trunc_for`, `METHOD_LONG`), §5 (`fit_exp_offset`), §6 (records, IDs), §7 (convergence), §8 (`low_spectrum`), §14 (status).
- `docs/plan/RESEARCH.md` §4.2, §6, §9 (eigen acceptance), §12 item 4.
- `docs/challenge_prompt_v4.md`, "Task 2.2".
- Style models: `tasks/task_1_3a.py` (closest existing task: parity fit after inflation), `src/analysis.py`, `src/model.py`, `notebooks/04_task_1_3a_which_state.ipynb`.

## 3. Allowlist (touch nothing else)
- `tasks/task_2_2.py` (new), `tests/test_l2a_gamma_z.py` (new), `notebooks/07_task_2_2_phase_flips.ipynb` (new).
- `docs/plan/status/l2a-gamma-z.md` (copy of `_TEMPLATE.md`).
- Your production outputs only: `results/records/t2_2.*.json`, `results/arrays/t2_2.*.npz`, `figures/task_2_2_*.png`.
- Do **not** edit `src/**` (owned by l0-core / l1-spectral). Missing or wrong helper → `DECISION NEEDED`, never a local patch.

## 4. Interfaces you implement / rely on
Rely on (CONTRACT, frozen): `src.config as C` (import first: sets double precision), `C.G2, C.KAPPA_B, C.KAPPA_A, C.METHOD_LONG, C.trunc_for`; `src.model.two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0)`, `src.model.cat2(Na, Nb, alpha, sign=+1)`; `src.analysis.fit_exp_offset(t, y, p0=None) -> {'gamma','A','C','gamma_stderr','rel_rms_residual'}`, `fit_exp_decay(t, y) -> (gamma, A)`; `src.convergence.sweep, converged_at, convergence_block`; `src.results.record, save_arrays, load_record, std_params`; `src.plotting.save(fig, name, quick=)`; `src.spectral.low_spectrum(H, jumps, Na, Nb, k=4, sector='even') -> {'rates', 'lams', 'rel_residual', 'edge_weight', 'cond_est', ...}`.

**Trap:** `two_mode` takes ε_d, not α. Always pass `eps_d = alpha**2 * C.G2`. `C.EPS_D` is for α = 2.1 only.

Implement in `tasks/task_2_2.py` (pure functions first, `main` last):
```python
ALPHAS = (1.0, 1.4, 1.8, 2.1, 2.4, 2.7); WINDOW = 2.5; N_T = 201; NB_SWEEP = (6, 8); NA_STEP = 4
def nbar_ss(alpha) -> float                       # alpha^2 coth(2 alpha^2)
def gamma_z_pred(alpha, kappa_a=C.KAPPA_A, n_th=0.0, nbar=None) -> float   # 2 ka[(1+2nth) nbar + nth]
def parity_ss(alpha) -> float                     # 1/cosh(2 alpha^2)
def t_window(alpha) -> float                      # WINDOW / gamma_z_pred(alpha)
def td_id(alpha, n_th=0.0) -> str                 # 't2_2.gamma_z.td.two_mode.a2.10' (+ '.nth0.05' if n_th)
def eig_id(alpha) -> str                          # 't2_2.gamma_z.eig.two_mode.a2.10'
def model(alpha, Na, Nb, n_th=0.0)                # two_mode(..., eps_d=alpha**2*C.G2, ...)
def run_td(alpha, Na, Nb, n_th=0.0, t_end=None, n_t=N_T, t0=0.0) -> dict
    # keys: t, parity, n_a, n_b, top2_a (arrays); gamma, gamma_stderr, A, C, rel_rms_residual,
    #       fit_window_us=[t0, t_end], gamma_t0_0p5 (refit from t0=0.5 us), nbar_meas, gamma_from_n, wall_s
def run_eig(alpha, Na, Nb) -> dict                # low_spectrum even block; gamma = rates[1]
def slope_over_2kappa_a(alpha, gamma, sigma=None) -> dict   # weighted linear fit in alpha^2: ratio, ratio_stderr, intercept
def main(alphas, quick=False, eig=False, thermal=False, summary=False)
```
CLI (argparse, like `task_1_3a.py`): `--quick`, `--alpha A [A ...]` (default all), `--eig`, `--thermal`, `--summary` (rebuild slope record, cross-check lists and figures from saved arrays and records; no simulation).

## 5. Tests to write FIRST (TDD)
`tests/test_l2a_gamma_z.py`; commit them (failing) before the implementation. Import `src.config` first (conftest does).
1. `test_prediction_values` (pure numpy): `gamma_z_pred(1.0) == approx(0.1212, rel=1e-3)`; `gamma_z_pred(2.1) == approx(0.5154, rel=1e-3)`; `2*C.KAPPA_A == approx(0.116867, rel=1e-5)`; `parity_ss(1.0) == approx(0.2658, rel=1e-3)`, `parity_ss(1.4) == approx(0.0397, rel=1e-2)`; `nbar_ss(a) == approx((a*a*tanh(a*a) + a*a/tanh(a*a))/2, rel=1e-12)` for a in ALPHAS; `gamma_z_pred(2.1, n_th=0.05) == approx(0.5728, rel=1e-3)`.
2. `test_offset_fit_needed`: Γ = `gamma_z_pred(1.0)`, C0 = 1/cosh(2), t = linspace(0, 2.5/Γ, 201), y = (1−C0)e^{−Γt} + C0. Assert `abs(fit_exp_decay(t, y)[0]/Γ − 1) > 0.02` and `abs(fit_exp_offset(t, y)['gamma']/Γ − 1) < 1e-6` and `abs(fit['C'] − C0) < 1e-6`.
3. `test_ids_and_window`: `td_id(2.1) == 't2_2.gamma_z.td.two_mode.a2.10'`, `td_id(2.1, 0.05) == 't2_2.gamma_z.td.two_mode.a2.10.nth0.05'`, `eig_id(1.0) == 't2_2.gamma_z.eig.two_mode.a1.00'`; all match `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`; `t_window(1.0) == approx(20.62, abs=0.01)`, `t_window(2.1) == approx(4.851, abs=0.01)`.
4. `test_cat_is_dark` (fast, Na=12, Nb=4, α=1.0): `H, jumps, _ = model(1.0, 12, 4)`; `norm(H @ cat2(12, 4, 1.0)) < 1e-6` (catches the ε_d trap); `expect(parity ⊗ I_b, cat2) == approx(1, abs=1e-10)`.
5. `test_slope_of_predictions`: `slope_over_2kappa_a(ALPHAS, [gamma_z_pred(a) for a in ALPHAS])['ratio'] == approx(0.9959, abs=5e-4)`; with ALPHAS[1:] it is `approx(0.9998, abs=5e-4)`.
6. `@pytest.mark.slow test_small_run_alpha1`: `r = run_td(1.0, 12, 4)`; `abs(r['gamma']/gamma_z_pred(1.0) − 1) < 0.05`; `abs(r['C'] − parity_ss(1.0)) < 0.02`; `r['rel_rms_residual'] < 1e-2`.

## 6. Method, step by step
1. Branch, status file (`State: IN_PROGRESS`), confirm `l0-core` is merged (`two_mode` has `n_th`, `cat2`, `fit_exp_offset`, `convergence`, `results.record` exist). Check whether `src/spectral.py` exists (l1-spectral merged?) and record the answer in the status file.
2. Write §5 tests; run fast tests (they fail on import); commit `test(l2a): Task 2.2 tests first`.
3. Implement pure functions; fast tests green.
4. `run_td`: `H, jumps, (a, b) = model(...)`; ρ0 = `cat2(Na, Nb, alpha, +1)`; `tsave = linspace(0, t_end or t_window(alpha), n_t)`; `dq.mesolve(H, jumps, rho0, tsave, method=C.METHOD_LONG, exp_ops=[P_a⊗I_b, a†a, b†b, top2_a⊗I_b], save_states=False)` with `P_a = dq.parity(Na)` and `top2_a = src.analysis.top_projector(Na, 2)`. Take `.real` of expects. Fit `fit_exp_offset(t[t>=t0], parity[t>=t0])` with p0 = [1−parity_ss, gamma_z_pred, parity_ss]; refit from t0 = 0.5 µs → `gamma_t0_0p5`. Fit `<n_a>` with `fit_exp_offset` as well: its C is `nbar_meas` (if its amplitude |A| < 1e-6, use the window mean of `<n_a>`); its gamma is `gamma_from_n` (informational, meaningful only for α ≤ 1.4).
5. Convergence per α (production): Na0, Nb0 = `C.trunc_for(alpha, 'steady')` (Na0 = 18, 22, 26, 28, 32, 34 for the six α; Nb0 = 8). Na sweep `[Na0−4, Na0, Na0+4]` at Nb = 8; Nb sweep `[6, 8]` at Na = Na0+4. Use `src.convergence.sweep` with an `fn` that returns floats only (`{'gamma_z': ...}`), keep traces in a side dict. Chosen truncation = (Na0+4, 8). `convergence_block({'Na': ({'Nb': 8}, rows_na), 'Nb': ({'Na': Na0+4}, rows_nb)}, key='gamma_z', rel_tol=1e-3, chosen={'Na': Na0+4, 'Nb': 8})`. Not converged → extend Na by +4 (max 2 extensions), else DECISION NEEDED.
6. Uncertainty = max(gamma_stderr, truncation spread), spread = max(|Γ(Na0+4) − Γ(Na0)|, |Γ(Nb=8) − Γ(Nb=6)|) at the chosen point.
7. Write the td record (§7) and arrays; the analytic cross-checks go in immediately, eigen and 1.3a entries are added by `--summary`.
8. `--eig` (if `src.spectral` importable): `low_spectrum(H, jumps, Na, Nb, k=4, sector='even')`, Γ = `rates[1]`; require `abs(rates[0]) < 1e-8`, `rel_residual < 1e-4`, `edge_weight < 1e-6`. Convergence: Na `[Na0, Na0+4]` at Nb 8, Nb `[6, 8]` at Na0+4. If `src.spectral` is missing: print a clear skip message, finish everything else, list the 6 eig runs plus `--summary` under "Jobs to queue", and leave the eig cross-check entries for a follow-up commit.
9. `--summary`: reload arrays and records, rebuild each td record's `cross_check` list (adding `liouvillian_eig_even` when the eig record exists, and the 1.3a entry at α=2.1), write the slope record, draw both figures.
10. Optional, last: `--thermal` (α=2.1, n_th=0.05, Na=32, Nb=8 plus Na=36 for convergence; Nb sweep 6/8), compare with 0.5728 (tol 0.02).
11. Notebook: setup cell `import os, pathlib` + `if not pathlib.Path('src').exists() and pathlib.Path('../src').exists(): os.chdir('..')` (re-run safe), then `import src.config as C`; `RERUN = False`; if RERUN call `tasks.task_2_2.main(...)`, else `load_record` every `td_id`/`eig_id`/slope id and show a table (α, Γ_td, Γ_eig, pred, rel_diff) plus the two PNGs. No physics code in the notebook.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
**Quick** (`--quick`, ≤ 2 min, `quick=True` everywhere → `results/quick/`, `figures/quick/`): α ∈ {1.0, 1.4}, Na sweep {12, 16}, Nb {4, 6}, window 1.0/Γ_pred, n_t = 81; eig at 12×4 if available.

**Production records** (CONTRACT §6.2/§6.3; `params = std_params(alpha=α)` [+ `n_th`]; `script = 'tasks/task_2_2.py'`; `task = '2.2'`; `quantity = 'Gamma_Z'`; `units = '1/us'`):
- `t2_2.gamma_z.td.two_mode.a{α:.2f}` for α in ALPHAS (`a1.00 a1.40 a1.80 a2.10 a2.40 a2.70`). `method = 'time_domain_fit_exp_offset'`, `value` = Γ at (Na0+4, 8), `uncertainty` per §6.6, `truncation`, `convergence` (§6.5). `numerics = {fit_window_us, gamma_stderr, rel_rms_residual, A, C_fit, C_pred: 1/cosh(2α²), gamma_t0_0p5, nbar_meas, gamma_from_n, max_top2_a, max_n_b, n_t, rtol: 1e-8}`. `cross_check`: `analytic_coth` (value = gamma_z_pred(α), tol 0.02); `analytic_2kappa_nbar` (2κ_a·nbar_meas, tol 0.02); `liouvillian_eig_even` (ref_id = eig id, tol 0.01; added by `--summary`); at α=2.1 also `intro_1_3a_inflation_fit` (value 0.5135, ref_id = the wrapped `t1_3a.*` record id if one exists in `results/records/`, else null; tol 0.02). `rel_diff = |value − check| / |check|`, `agree = rel_diff <= tol`. `artifacts = {figure: 'figures/task_2_2_gamma_z_vs_alpha2.png', arrays: 'results/arrays/<id>.npz'}`.
- `t2_2.gamma_z.eig.two_mode.a{α:.2f}`: `method = 'liouvillian_eig_even_sector'`, value = rates[1], `numerics = {rel_residual, edge_weight, cond_est, sector: 'even', sigma, k: 4, rate0: rates[0]}` (sigma as returned, else 0.0), convergence per §6.8, cross_check `analytic_coth` (tol 0.02) and `time_domain_fit` (ref_id = td id, tol 0.01).
- `t2_2.slope_over_2kappa_a.td.two_mode`: quantity `slope_over_2kappa_a`, units `1`, value = weighted (1/uncertainty²) linear fit of Γ_td vs α² with intercept, divided by 2κ_a; uncertainty = fit stderr / 2κ_a. Convergence: pseudo-axis `Na_offset` with values [−4, 0, 4] (slope recomputed from the Na-sweep Γ at Na0+offset for every α), fixed {Nb: 8}, chosen {Na_offset: 4}, rel_tol 1e-3; say so in `notes`. cross_check `analytic_coth_grid` (0.9959 = same fit applied to the coth predictions on ALPHAS, tol 0.02) and `prompt_linear` (1.0, tol 0.02). `numerics = {intercept, intercept_stderr, ratio_alpha_ge_1p4}`.
- Optional: `t2_2.gamma_z.td.two_mode.a2.10.nth0.05` (cross_check `analytic_thermal` 0.5728, tol 0.02).

**Arrays** `results/arrays/<td id>.npz`: `t`, and for each truncation `parity_Na{Na}_Nb{Nb}`, `n_a_...`, `n_b_...`, `top2_a_...`; plus `fit_A, fit_gamma, fit_C, wall_s`.

**Figures:** `figures/task_2_2_parity_decay.png`: panel 1, ⟨P⟩(t) for every α with dashed fit and dotted 1/cosh(2α²) offset; panel 2, (⟨P⟩−C)/A vs Γ_pred·t on a log axis (all α collapse onto e^{−x}). `figures/task_2_2_gamma_z_vs_alpha2.png`: panel 1, Γ_td vs α² (error bars), eigen points (open markers), coth prediction curve, 2κ_aα² line, slope ratio in the legend; panel 2, Γ/pred − 1 with a ±2% band.

**Jobs:** each `--alpha` production run should take minutes (D ≤ 38×8 = 304, ρ ≈ 1.5 MB, RAM < 1 GB); the α=1.0 run is the longest in time (window 20.6 µs). Time the first one. Any single invocation projected > 15 min → split per α and list under "Jobs to queue", e.g. `python -m tools.runq submit --name t2_2_a1.00 --ram-gb 1 -- <DUQ_PY> -m tasks.task_2_2 --alpha 1.0`.

## 8. Acceptance gates (ALL must pass before DONE)
1. Fast tests pass in < 20 s for this file; `test_small_run_alpha1` passes under `-m slow`.
2. `--quick` finishes in ≤ 2 min and writes only under `results/quick/` and `figures/quick/`.
3. Every td record: `convergence.converged == true` (rel_tol 1e-3), Nb 6 vs 8 rel diff ≤ 1e-3 (Nb insensitivity shown), `max_top2_a < 1e-6`.
4. Every td record: `analytic_coth` `rel_diff ≤ 0.02` (expect ≲ 1%) and `analytic_2kappa_nbar` `rel_diff ≤ 0.02`.
5. Fit quality: `rel_rms_residual < 1e-3`; |gamma_t0_0p5/gamma − 1| < 5e-3; |C_fit − 1/cosh(2α²)| < 0.01 at α = 1.0 and 1.4.
6. Slope record: `|ratio − 0.9959| ≤ 0.02·0.9959` and `|ratio − 1| ≤ 0.02`.
7. α = 2.1 td vs 1.3a's 0.5135: rel_diff ≤ 0.02 (expect ~0.4 to 1%).
8. Eigen (if l1-spectral merged): each eig record passes rel_residual < 1e-4, edge_weight < 1e-6, |rates[0]| < 1e-8, converged; td vs eig rel_diff ≤ 0.01 at every α. If not merged: runs listed under Jobs to queue, state `DONE_WITH_CONCERNS`.
9. Production records have `provenance.dirty == false` (commit code, then run, then commit outputs). Both figures exist. Notebook runs top to bottom with `RERUN = False`.
10. Status file complete (§12), including the answer to "does Γ_Z follow 2κ_aα²?" with the slope ratio ± stderr.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git switch -c std/l2a-gamma-z standard-track       # skip if the worktree already made the branch
Copy-Item docs/plan/status/_TEMPLATE.md docs/plan/status/l2a-gamma-z.md
& $env:DUQ_PY -m pytest tests/test_l2a_gamma_z.py -m "not slow" -q
& $env:DUQ_PY -m pytest tests/test_l2a_gamma_z.py -m slow -q
& $env:DUQ_PY -m tasks.task_2_2 --quick
git add tasks/task_2_2.py tests/test_l2a_gamma_z.py notebooks/07_task_2_2_phase_flips.ipynb; git commit -m "feat(l2a): Task 2.2 Gamma_Z"
git status --porcelain -- src tasks tools                  # must be empty before production
& $env:DUQ_PY -m tasks.task_2_2 --alpha 2.7               # time it first; then the rest
& $env:DUQ_PY -m tasks.task_2_2 --alpha 1.0 1.4 1.8 2.1 2.4
& $env:DUQ_PY -m tasks.task_2_2 --eig                       # only if src/spectral.py exists
& $env:DUQ_PY -m tasks.task_2_2 --summary
& $env:DUQ_PY -m tasks.task_2_2 --thermal                   # optional, last
git add results/records/t2_2.* results/arrays/t2_2.* figures/task_2_2_*.png docs/plan/status/l2a-gamma-z.md
git commit -m "results(l2a): Task 2.2 production records and figures"
```

## 10. Out of scope / do not
- No edits to `src/**`, other lanes' files, `CONTRACT.md`, `RESEARCH.md`, the challenge prompt, `notes/`.
- No readout-drive dephasing (Γ_Z(ε_Z), Réglade S18): that is lanes l4a/l4b. No Γ_X, no one-mode Γ_Z (optional only if time remains, not a deliverable).
- Do not fit with `fit_exp_decay` for the result (only in the bias test). Do not loosen any tolerance: write DECISION NEEDED.
- Do not use `C.EPS_D` for α ≠ 2.1. Do not hand-edit records or JSON. Do not run more than 3 heavy jobs at once.
- Do not claim agreement with experiment (Réglade et al. see a slope ~25% above κ_a's prediction from effects outside this model; mention it, don't fit it).

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Use the status-file block exactly:
> **Q:** Γ_Z(α=X) misses 2κ_aα²coth(2α²) by Y% after convergence (Na up to N, Nb 6/8 agree to Z). Accept as a two-mode dressing effect or investigate?
> **Options:** A) report with the measured 2κ_a·n̄ comparison as the explanation; B) block until reviewed.
> **Recommendation:** …  **Blocking?** no: finished the other α meanwhile.

Other triggers: an `l0-core` helper missing or not matching CONTRACT §3–§7 (do not patch it); not converged after two Na extensions; `C_fit` far from 1/cosh(2α²); td vs eig > 1%; any run projected > 15 min.
Fallbacks: if `fit_exp_offset` fails to converge at large α (C ≈ 0), pass the p0 of §6.4 and bound C to [−0.01, 1]; if `src.spectral` is missing, see §6.8.
**Cut line (in order):** thermal point → eig cross-check deferred to a queued follow-up → α = 2.7 (keep 5 points). Never cut α = 2.1, the Nb sweep, the offset fit or the slope record.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE the status file has: State `DONE` (or `DONE_WITH_CONCERNS` if eig deferred), last commit sha; every gate of §8 ticked with the command and its key output line; a records table (6 td + 6 eig + slope [+ thermal]) with value, converged, and every cross-check (method, rel_diff, tol, agree); figure and array paths; Jobs to queue (eig runs / long α if any) with RAM and wall estimates; the one-paragraph answer: "Γ_Z follows 2κ_aα²coth(2α²) to within X% at every α; slope/2κ_a = R ± σ (coth-grid expectation 0.9959); Nb 6→8 changes Γ_Z by ≤ Y; even-block eigenvalue agrees to Z%"; deviations; notes for review (any surprise, anything you were tempted to loosen).

Explain-back questions (write these into the status file; Harshit answers in `docs/defense.md`):
1. Why does the parity settle at 1/cosh(2α²) instead of 0, and what would a pure exponential fit have reported at α = 1.0?
2. Why is 2κ_a·n̄ with the measured n̄ an identity check rather than an independent prediction, and where does the coth(2α²) correction come from?
3. Why is Γ_Z insensitive to the buffer truncation while Γ_X at α = 2.1 needed Nb = 8, and which of your two Γ_Z methods (time-domain fit, even-block eigenvalue) would you trust at α = 2.7, and why?
