# Brief `l3-prep`: Task 1.3b/c: prepare |+alpha> and cost it; Lab inflation frames

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l3-prep`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/06-l3-prep.md`, then execute this brief exactly. Keep `docs/plan/status/l3-prep.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l3-prep` | `std/l3-prep` (from `standard-track`) | `l0-core` | Standard (Sonnet-class). A fast model is fine for the notebook and `docs/task_1_3c.md` | 2 h | Phase 1 (6:45 to 9:45 PM Sat Oct 24). Target DONE **9:30 PM**, merged at G1 (9:45 PM) |

## 1. Goal and why
Inflation from vacuum conserves the a → −a symmetry, so it always lands in the even cat |C₊⟩ (Task 1.3a), never in the codeword |0_L⟩ = |+α⟩. Task 1.3b asks for a method that prepares |+α⟩, demonstrated numerically. Task 1.3c asks what that method costs. You deliver four methods, each measured in the **two-mode** model at α = 2.1, plus a cost table. You also deliver the inflation movie data for the Lab site (`l6-lab`).

**CRITICAL (RESEARCH §4.1, proven).** A drive ε(a + a†) **cannot** select a well. It gives ȧ = −iε, a push along the imaginary axis, which is the separatrix between the wells at ±α. The antiunitary U = P·e^{iπb†b}·K (P = memory parity, K = complex conjugation in the Fock basis) maps H → −H and every jump to minus itself, and it leaves the vacuum invariant. That forces ⟨a⟩ = −⟨a⟩*, i.e. **Re⟨a⟩ ≡ 0 for all t**. Use the real-axis drive **ε_x·i(a† − a)** (model argument `eps_x`, ȧ = +ε_x). It keeps only V = e^{iπb†b}K, which forces ⟨a⟩ to be **real**, so the state can tip into +α. The ε(a+a†) attempt is our honest "what we got wrong first" (RESEARCH §12 item 1).

## 2. Read first
- `docs/plan/CONTRACT.md`: §1 (your allowlist), §3 (`two_mode`, `one_mode`, `coherent2`, `drive_ops`), §5 (`z_logical`, `code_projector`, `leakage`, `p_right_well`), §6 (records, ID scheme §6.3), §7 (convergence), §13 (Lab data).
- `docs/plan/RESEARCH.md`: §1 (parameters), §2 (dynamiqs 0.3.7 API: `save_extra(t, rho)` takes two arguments, there is no `options=`), §4.1 and §4.2 (symmetries), §7 (settle time 1.13 µs to 1%), §12.
- Code style: `tasks/task_1_3a.py` (copy its structure: docstring, `argparse` main, `import src.config as C` first, `save_extra` with no full states) and `src/analysis.py` (`memory_extras`).
- `docs/challenge_prompt_v4.md`, Task 1.3 (b) and (c).

## 3. Allowlist (touch nothing else)
- `tasks/task_1_3b.py`, `tasks/task_lab_frames.py`, `tests/test_l3_prep.py`, `docs/task_1_3c.md`, `notebooks/05_task_1_3b_prepare_zero.ipynb`, `docs/plan/status/l3-prep.md`.
- Production outputs: `results/records/t1_3b.*.json`, `results/arrays/t1_3b.*.npz`, `results/arrays/lab.inflation_wigner.npz`, `figures/task_1_3b_*.png`. Quick outputs go to the git-ignored `results/quick/` and `figures/quick/`.
- **Never** edit `src/**` (owned by `l0-core`), another lane's files, `TECHNICAL.md`, `README.md`, `notes/` or `docs/challenge_prompt_v4.md`.

## 4. Interfaces you implement / rely on
**Rely on (l0-core, CONTRACT §3 to §7):** `two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None) -> (H, jumps, (a, b))`; `one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0) -> (H, jumps, a)`; `vacuum2`, `coherent2(Na, Nb, alpha)`; `src.analysis.{memory_state, code_basis, z_logical, code_projector, leakage, p_right_well}`; `src.results.{std_params, record, save_arrays, load_record}`; `src.convergence.{converged_at, convergence_block}`; `src.plotting.save(fig, name, dpi=200, quick=False)`; `C.G2 = 4.79411`, `C.EPS_D = 21.142`, `C.KAPPA_B = 16.33628`, `C.KAPPA_A = 0.0584336`, `C.KAPPA_2 = 5.6276` (rad/µs), `C.ALPHA = 2.1`, `C.METHOD` (Tsit5, rtol 1e-8, atol 1e-10).

**Implement in `tasks/task_1_3b.py`:**
```python
T_EVAL = 3.0                                   # µs of stabilization after switch-on
TAUS_NS = (20, 50, 100, 200); EX_RATIOS = (0.02, 0.05, 0.1, 0.2); T_OFFS = (0.1, 0.2, 0.4)
def metrics_extra(Na, Nb, alpha):   # save_extra(t, rho) -> {re_a, im_a, fid, p_right, parity, purity, leakage,
                                    #   n_a, n_b, top2_a, top_b, rho_a}. rho_a is Na x Na; NEVER return the full state.
def run_ideal(Na, Nb, alpha, t_eval) -> dict                       # method (i): traces, t_us
def run_pulse(Na, Nb, alpha, tau_us, t_eval, pump_on=False) -> dict  # method (ii)
def run_biased(Na, Nb, alpha, ratios, t_off, t_eval, drive="x") -> dict  # method (iii), batched over ratios; drive="z" = forbidden demo
def main(quick=False, methods=("ideal", "pulse", "biased"), na=32, nb=12, conv=True, write_table=False)
```
`metrics_extra` definitions (all on ρ_a = Tr_b ρ; ρ_b = Tr_a ρ): `fid` = ⟨α|ρ_a|α⟩ with `dq.coherent(Na, alpha)`; `p_right` = (1 + Tr(Z_L ρ_a))/2 with `Z_L = z_logical(Na, alpha)` (the same formula as `p_right_well`, written in jnp so it traces under JAX); `leakage` = 1 − Tr(code_projector ρ_a); `parity` = Tr(e^{iπa†a} ρ_a); `purity` = Tr ρ_a²; `top2_a` = ρ_a[−1,−1] + ρ_a[−2,−2]; `top_b` = ρ_b[−1,−1]. Convert operators with `dq.asqarray(x).to_jax()`.

**Implement in `tasks/task_lab_frames.py`:** `frame_times(quick) -> np.ndarray` and `main(quick=False, na=32, nb=12)`. **Output contract (consumed by `l6-lab`, CONTRACT §13):** `results/arrays/lab.inflation_wigner.npz` with keys `t_us, na, nb, top2_a, top_b` (dense, length n_t), `eff_t_us, eff_na` (effective model), `x, y` (length 81), `frames` (n × 81 × 81, indexed **`frames[k, iy, ix]`**) and **`frame_t_us`** (length n; the time of each frame, needed for §13's `frames:[{t_us, w}]`).

## 5. Tests to write FIRST (TDD)
Write `tests/test_l3_prep.py`, run it, and see it fail. Commit it before the implementation. Use `import src.config as C` first. The fast tests in this file must take < 40 s in total.
1. `test_eps_z_cannot_select_well`: `two_mode(12, 4, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=0.2*C.G2)`, `rho0 = vacuum2(12, 4)`, `tsave = linspace(0, 0.5, 51)`, `exp_ops=[a]`. Assert `max|Re⟨a⟩| < 1e-12`, **and** `max|Im⟨a⟩| > 1e-3` (the drive does act, only along the separatrix). **Never loosen 1e-12**: the symmetry is exact up to roundoff.
2. `test_eps_x_selects_right_well`: same setup with `eps_x=0.1*C.G2` instead. Assert `Re⟨a⟩(0.5 µs) > 0.01` and `max|Im⟨a⟩| < 1e-12` (the V symmetry makes ⟨a⟩ real).
3. `test_p_right_well_bounds` (N = 24, α = 2.1): `p_right_well(|α⟩⟨α|) > 1 − 1e-6` (analytic: (1 + √(1 − e^{−4α²}))/2 = 1 − 5.4e-9); `p_right_well(|−α⟩⟨−α|) < 1e-6`; |C₊⟩, vacuum, and the mixture ½(|α⟩⟨α| + |−α⟩⟨−α|) all give `0.5 ± 1e-8`; for 5 random density matrices (seed 0), `-1e-12 ≤ p ≤ 1 + 1e-12`.
4. `test_metrics_extra_on_coherent` (Na = 24, Nb = 4): apply `metrics_extra(24, 4, 2.1)` to `coherent2(24, 4, 2.1)`. Assert `fid = 1 ± 1e-10`, `re_a = 2.1 ± 1e-6`, `im_a = 0 ± 1e-12`, `leakage < 1e-6`, `top_b < 1e-12`, and callback `p_right` == `p_right_well(rho_a, 2.1)` within 1e-12.
5. `test_pulse_displacement_analytic`: `two_mode(16, 2, 0.0, 0.0, C.KAPPA_B, C.KAPPA_A, eps_x=1.0/0.05)` from vacuum for τ = 0.05 µs. Assert `Re⟨a⟩(τ)` equals `(2ε_x/κ_a)(1 − e^{−κ_aτ/2})` to relative 1e-6.
6. `test_lab_frames_orientation`: `x, y, w = dq.wigner(dq.coherent(16, 2.0), xmax=4, ymax=4, npixels=81)`. Find the peak `(iy, ix)` in the layout `task_lab_frames` stores, and assert `|x[ix] − 2.0| < 0.1` and `|y[iy]| < 0.1`. If dynamiqs returns `w[ix, iy]`, the script must transpose; this test pins the convention for `l6-lab`.
7. `@pytest.mark.slow test_ideal_displacement_fidelity`: `coherent2(24, 8, C.ALPHA)` under the nominal `two_mode(24, 8, ...)` for 3 µs. Assert fidelity with `dq.coherent(24, α)` > 0.9 and `p_right > 0.99`.
8. `@pytest.mark.slow test_lab_frames_npz_schema`: run `task_lab_frames.main(quick=True)`, load the quick npz, and check every key in §4, `frames.shape == (len(frame_t_us), 81, 81)`, `x[0] == -4`, `x[-1] == 4`.

## 6. Method, step by step
0. **Setup (5 min).** Copy `docs/plan/status/_TEMPLATE.md` to `docs/plan/status/l3-prep.md` and set State = IN_PROGRESS. Check that `l0-core` is merged: `two_mode` accepts `eps_x`, and `src/analysis.py` has `p_right_well`. If either is missing, see §11.
1. **Tests (20 min).** Write §5, confirm that they fail, and commit (`l3-prep: tests first`).
2. **`metrics_extra`.** Follow `memory_extras` in `src/analysis.py`. Make tests 1 to 6 pass.
3. **Method (i), ideal displacement then stabilization (Réglade's protocol).** Start from `coherent2(Na, Nb, α)`. Evolve under the nominal `two_mode(Na, Nb, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A)` with `tsave = linspace(0, T_EVAL, 301)`, `save_states=False` and `save_extra=metrics_extra(...)`. Note: |α⟩⊗|0⟩ is an exact dark state of H and √κ_b b, because ε_d = g₂α². Only κ_a perturbs it, so expect F ≈ 1. The method is idealized because the displacement is instantaneous; (ii) is the physical version of it.
4. **Method (ii), finite displacement pulse BEFORE stabilization.** Pulse phase: from `vacuum2`, use `two_mode(Na, Nb, 0.0, 0.0, C.KAPPA_B, C.KAPPA_A, eps_x=α/τ)`, so g₂ and ε_d are **off**, for duration τ ∈ {20, 50, 100, 200} ns. That gives ε_x = 105.0, 42.0, 21.0, 10.5 rad/µs (ε_x/g₂ = 21.9, 8.76, 4.38, 2.19), with ε_x·τ = α. Check the analytic result ⟨a⟩(τ) = (2ε_x/κ_a)(1 − e^{−κ_aτ/2}), which falls short of α by κ_aτ/4 (0.03% to 0.29%). Stabilization phase: a **second `mesolve`** from `res.final_state` under the nominal H for T_EVAL. Report times relative to the stabilization switch-on, with the pulse plotted at negative t.
5. **Method (iii), symmetry-biased inflation.** From `vacuum2` with stabilization **on** and `eps_x = r·g₂`, r ∈ {0, 0.02, 0.05, 0.1, 0.2}. Batch over r (one batched argument per call), and treat r = 0 as the **control**. Use two sequential `mesolve` calls: [0, t_off] with eps_x on, then [t_off, 3.0] from the batched final states with eps_x = 0, for t_off ∈ {0.1, 0.2, 0.4} µs. Prefer this over `dq.pwc`, because it avoids a step across the discontinuity. The time origin is the start of inflation, and you evaluate at t = 3.0 µs. Also run the **forbidden demo** `drive="z"` (eps_z = 0.1 g₂, t_off = 0.4) once, for the figure only.
6. **Method (iv), measure and postselect: discussion only** in `docs/task_1_3c.md`. Inflate to |C₊⟩, then read Z_L with the Task 2.3 readout (ε_Z drive plus buffer heterodyne). You get |+α⟩ with **50%** probability, at the cost of the readout time; postselection discards the other half. A deterministic version needs feed-forward and an X_L gate (a pump-phase rotation; not simulated here).
7. **Convergence (per record, CONTRACT §6.2, §7).** Chosen (Na, Nb) = (32, 12). This is ≥ `trunc_for(2.1, 'inflation')` = (30, 12). Sweeps: `Na ∈ [32, 36]` at Nb = 12, and `Nb ∈ [12, 14]` at Na = 32. Keys `fidelity` and `p_right`, `rel_tol = 1e-3`. Build the blocks with `convergence_block`. If a record is not converged, write a DECISION NEEDED and do not move the chosen truncation silently.
8. **Cross-checks (stated tolerance, CONTRACT §6.2).**
   - Every `p_right` record: `{"method": "re_a_estimator", "value": (1 + Re⟨a⟩/√⟨n_a⟩)/2 at t_eval, "tol": 0.01}`. Since a ≈ αZ_L in the code space, this is an independent observable.
   - Every `fidelity` record: `{"method": "p_right_upper_bound", "value": p_right, "rel_diff": max(0, F − p_right)/p_right, "tol": 1e-3}`. F cannot exceed the right-well population.
   - (i) and (ii) also get `{"method": "one_mode_effective", tol 0.02}`: the same protocol on `one_mode(Na, C.KAPPA_2, α, C.KAPPA_A, eps_x=...)`.
   - (ii) also gets `{"method": "vs_ideal_disp", "ref_id": "t1_3b.fidelity.ideal_disp.two_mode.a2.10", tol 0.005}`.
   - (iii) gets `one_mode_effective` with tol 0.15, **informational**. It may disagree, because the two-mode inflation is non-adiabatic (RESEARCH §1, §7). Report `agree` honestly; a disagreement is a finding.
9. **Records** (§7), each with `params=R.std_params(alpha=C.ALPHA, eps_x=<rad/µs>, tau_ns=..., t_off_us=..., t_eval_us=3.0)` and `units="1"`. `numerics` holds `{re_a_over_alpha, leakage, purity, parity, max_top2_a, max_top_b, t_eval_us}`. `artifacts` points to the figure and the traces npz.
10. **Figures** (step 7 of §7), then **`tasks/task_lab_frames.py`**:
    - Evolve `two_mode(32, 12, nominal)` from `vacuum2` for 3 µs, `tsave = linspace(0, 3, 301)`. `save_extra` returns `n_a, n_b, top2_a, top_b, rho_a`.
    - Frames: t = 0, 0.02, …, 0.50 (26 frames, dense through the overshoot), then 0.6, 0.8, …, 3.0 (13 frames), 39 in total. Compute them with `dq.wigner(rho_a[idx], xmax=4, ymax=4, npixels=81)` (loop if it does not batch), and store them as `frames[k, iy, ix]`.
    - `eff_t_us, eff_na = np.load("results/task_1_0c_nominal.npy")`, a (2, n_t) array of t (µs) and ⟨n⟩.
    - Write with `R.save_arrays("lab.inflation_wigner", quick=quick, ...)`. This takes about 1 min.
11. **Timing decision.** Time one production config with `--methods pulse --no-conv` (it writes to `results/quick/`), then extrapolate. Anything above 15 min goes to "Jobs to queue" (§7).
12. **Commit the code**, then run production, then commit the outputs (`provenance.dirty` must be false). Then write `docs/task_1_3c.md` and the notebook, and set the status to DONE.
13. **Stretch (only if ahead at 9:00 PM; cut first):** (a) `pump_on=True` for τ = 50 ns, tag `.pumpon`: displacing while pumping, which the confinement fights; (b) pulse area 0.5α at τ = 50 ns, tag `.area0.5`: is the stabilization forgiving of amplitude errors?

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
**Record IDs (exact, CONTRACT §6.3; `a2.10` = f"a{α:.2f}", `ex{r:.3g}g2`, `toff{t:g}us`, `tau{ns}ns`):**
- `t1_3b.fidelity.ideal_disp.two_mode.a2.10`, `t1_3b.p_right.ideal_disp.two_mode.a2.10`
- `t1_3b.{fidelity|p_right}.pulse_disp.two_mode.a2.10.tau{20|50|100|200}ns`: 8 records
- `t1_3b.{fidelity|p_right}.biased_inflation.two_mode.a2.10.ex{0.02|0.05|0.1|0.2}g2.toff{0.1|0.2|0.4}us`: 24 records, e.g. `t1_3b.p_right.biased_inflation.two_mode.a2.10.ex0.1g2.toff0.2us`. The r = 0 control and the ε_Z demo get **no** record.
- Stretch only: `...pulse_disp.two_mode.a2.10.tau50ns.pumpon`, `...tau50ns.area0.5`.
- `task="1.3b"`, `quantity` ∈ {`fidelity`, `p_right`}, `method` field ∈ {`mesolve_ideal_displacement`, `mesolve_pulse_displacement`, `mesolve_biased_inflation`}, `script="tasks/task_1_3b.py"`.

**Arrays:**
- `results/arrays/t1_3b.traces.all.two_mode.a2.10.npz`, with keys `<run>__<metric>` for every run (e.g. `biased_ex0.1g2_toff0.2us__p_right`) plus `<run>__t_us`.
- `results/arrays/lab.inflation_wigner.npz` (§4).

**Figures:**
- `figures/task_1_3b_methods.png` (2×2):
  - (a) Re⟨a⟩/α vs t for ideal, pulse τ = 50 ns, biased ex0.1g2/toff0.2us, the r = 0 control, and the ε_Z demo, dashed and labelled "ε(a+a†): forbidden by symmetry";
  - (b) p_right vs t for the same runs;
  - (c) p_right(3 µs) vs ε_x/g₂ (log x), one line per t_off;
  - (d) F(3 µs) and max leakage vs τ, with the ideal value as a dashed line.
- `figures/task_1_3b_wigner.png`: rows ideal / pulse τ = 50 ns / biased with the largest p_right; columns t = 0, 0.2, 1.0, 3.0 µs; `xmax = 4`, a shared symmetric color scale.

**Quick (`--quick`, ≤ 2 min, `results/quick/` + `figures/quick/`):** Na = 16, Nb = 6, T_EVAL = 1.0, τ = 50 ns only, r ∈ {0, 0.1}, t_off = 0.2, convergence over Na [12, 16] and Nb [4, 6]. `task_lab_frames --quick`: Na = 16, Nb = 6, 1 µs, 10 frames, npixels still 81.

**Production split:** run `task_lab_frames` yourself (about 1 min). The estimate for `--methods ideal,pulse` is about 15 to 17 min (5 configs × 3 truncations at about 1 min each), and for `--methods biased` about 30 to 40 min. Run whatever measures ≤ 15 min; queue the rest:
```powershell
& $env:DUQ_PY -m tools.runq submit --name t1_3b_ideal_pulse --ram-gb 2 -- D:\duq-venv\Scripts\python.exe -m tasks.task_1_3b --methods ideal,pulse --write-table
& $env:DUQ_PY -m tools.runq submit --name t1_3b_biased --ram-gb 2 -- D:\duq-venv\Scripts\python.exe -m tasks.task_1_3b --methods biased --write-table
```
`--write-table` regenerates **only** the region between `<!-- BEGIN AUTO TABLE -->` and `<!-- END AUTO TABLE -->` in `docs/task_1_3c.md`, from the records on disk, with `rec:` tokens. That way the queued job also fills the doc. All queued jobs must finish before the 8:00 AM physics freeze.

## 8. Acceptance gates (ALL must pass before DONE)
1. Every test in §5 passes (fast and slow); this file's fast tests take < 40 s; `& $env:DUQ_PY -m pytest -m "not slow" -q` is green for the whole suite.
2. Symmetry: the printed max|Re⟨a⟩| for the ε_Z run is < 1e-12, and the number is copied into the status file.
3. The r = 0 control: p_right(t) = 0.5 within 1e-9 and |Re⟨a⟩| < 1e-12 for all t. For every r > 0, max|Im⟨a⟩| < 1e-10.
4. (ii): the analytic ⟨a⟩(τ) matches to relative 1e-6 for all four τ.
5. (i): F(3 µs) ≥ 0.99 and p_right ≥ 0.999. (ii): |F_pulse − F_ideal| ≤ 0.005 for every τ. If either fails, write a DECISION NEEDED; never tune the protocol to pass.
6. (iii): p_right(3 µs) > 0.5 for every r > 0, and it does not decrease with r at fixed t_off. A violation gets reported, not hidden.
7. Truncation, for every production run: max_t top2_a < 1e-4 and max_t top_b < 1e-4. Every record has `convergence.converged == true` at rel_tol 1e-3, ≥ 1 `cross_check` with `agree == true`, and `provenance.dirty == false`.
8. Lab npz: all §4 keys; `frames.shape == (39, 81, 81)`; `na[-1]` within 1% of α² = 4.41; `max(na) > 4.41` (the overshoot); `sum(W)·dx·dy` constant across frames to 1e-3 relative; test 6 passes.
9. Both figures exist, in `figures/` if production ran here, otherwise in `figures/quick/`, with the job queued.
10. `docs/task_1_3c.md` has the cost table, every number carries a `rec:` token, and it has a "What we got wrong first" section. `& $env:DUQ_PY -m tools.check_claims --files docs/task_1_3c.md` exits 0 for the rows whose records exist (if `l0-tools` is not merged yet, say so in the status file).
11. The notebook runs top to bottom without rerunning production: `& $env:DUQ_PY -m jupyter nbconvert --to notebook --execute --inplace notebooks/05_task_1_3b_prepare_zero.ipynb`.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -m pytest tests/test_l3_prep.py -m "not slow" -q        # TDD loop
& $env:DUQ_PY -m pytest tests/test_l3_prep.py -m slow -q
& $env:DUQ_PY -m tasks.task_1_3b --quick
& $env:DUQ_PY -m tasks.task_lab_frames --quick
& $env:DUQ_PY -m tasks.task_1_3b --methods pulse --no-conv            # timing probe (writes to results/quick)
git status --porcelain -- src tasks tools                             # must be EMPTY before production
& $env:DUQ_PY -m tasks.task_lab_frames
& $env:DUQ_PY -m tasks.task_1_3b --methods ideal,pulse --write-table  # only if the probe says <= 15 min
& $env:DUQ_PY -m pytest -m "not slow" -q
```
Run one heavy job at a time from this lane; there are at most 3 heavy jobs laptop-wide.

## 10. Out of scope / do not
- No edits to `src/**`. If a helper is missing or wrong, write a DECISION NEEDED (§11).
- No Γ_X or Γ_Z extraction (lanes `l2a`, `l2b`), no readout simulation for (iv) (`l4a`), no circuit model, no Lab site code, no `TECHNICAL.md` or `README.md` edits.
- Do not use ε(a+a†) as a preparation method. It appears only in the symmetry test and the forbidden demo.
- Do not compute the odd-block committor (the left eigenvector). If `src.spectral.left_eigvec_operator` is already merged, you *may* add it as an extra `cross_check` on the `p_right` records (method `committor`, tol 0.01); otherwise skip it.
- Never save full two-mode states (`save_states=False`); ρ_a (Na × Na) is fine.
- Never put quick-run numbers in `docs/task_1_3c.md`.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write this block in `docs/plan/status/l3-prep.md`, set State = BLOCKED if you cannot continue, and keep working on whatever is unblocked:
```text
DECISION NEEDED (l3-prep, <EDT time>): <one-line question>
Evidence: <command> -> <key numbers>
Options: A) <...>  B) <...>   My recommendation: <A/B, one line why>
Blocking: <what is waiting on it>
```
- **`two_mode` has no `eps_x`, or it misbehaves:** build the drive locally in `tasks/task_1_3b.py`, `H = H + eps_x * 1j * (a.dag() - a)` using the returned `a`, flag it in the status file, and switch back once `l0-core` is fixed.
- **`p_right_well`, `z_logical` or `code_projector` is missing:** implement private `_z_logical` and `_p_right` in your task file with the CONTRACT §5 formulas, and write a DECISION NEEDED for `l0-core`.
- **Test 1 fails** (max|Re⟨a⟩| ≥ 1e-12): this signals a drive sign or quadrature error in `src/model.py`. **Stop**, report the number, and do not change the tolerance.
- **Test 2 or gate 6 fails** (p_right ≤ 0.5 with eps_x > 0): check the sign of ȧ = +ε_x on a one-mode run, then report it.
- **A convergence sweep fails at (32, 12):** report both values and propose (36, 14) as the chosen truncation, but queue it rather than run it yourself.
- **Cut line** (global cut item 7 is method (iii)): if you are not at step 10 by 9:00 PM, ship (i) + (ii) + lab frames + `docs/task_1_3c.md` + the notebook, and leave (iii) as the queued job `t1_3b_biased`. If that job cannot run before 8:00 AM, (iii) appears only as quick figures labelled "illustrative, not converged".

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
**`docs/plan/status/l3-prep.md` at DONE:**
- State DONE (or DONE_WITH_CONCERNS) and the last commit SHA.
- The gate table from §8, with evidence (command → key number), including the max|Re⟨a⟩| from the symmetry test.
- The records table (id, value, converged, cross-check agree).
- Figures and arrays produced.
- Jobs to queue: the exact runq lines from §7 that you did not run, with RAM 2 GB and measured wall times.
- **Note for `l6-lab`:** the npz path, the keys, `frames[k, iy, ix]`, `x = Re α` (dynamiqs g = 2), 39 frames.
- **Note for `l7-docs`:** where the 1.3c table and the "got wrong first" text live.
- Any open DECISION NEEDED.

**Explain-back questions for Harshit (do not answer them here):**
1. The drive ε(a+a†) visibly moves ⟨a⟩, yet it can never prepare |+α⟩ from vacuum. Which symmetry forbids it? What exactly does that symmetry force about ⟨a⟩? And why does ε_x·i(a†−a) escape it?
2. Method (ii) calibrates the pulse area to ε_x·τ = α. If the area is 20% off, or the drive phase is rotated by 30°, what final state does the stabilization produce? What kind of calibration error *would* actually ruin the preparation?
3. In method (iii), why does a weak ε_x matter so much in the first ~0.2 µs of inflation and so little afterwards? And what does leaving it on longer cost you, in terms of leakage, the well shift ≈ ε_x/(2κ₂α²), and fidelity versus p_right?
