# Brief `l2b-gamma-x`: Task 2.1 centerpiece: bit-flip rate Gamma_X, two channels, two methods

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l2b-gamma-x`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/05-l2b-gamma-x.md`, then execute this brief exactly. Keep `docs/plan/status/l2b-gamma-x.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l2b-gamma-x` | `std/l2b-gamma-x` from `standard-track` | `l0-core`, `l1-spectral` | strongest available (Opus-class, max reasoning) | 3 h of lane work; long eigen jobs run overnight in the queue | Phase 2 (starts after G1, 9:45 PM Sat). **G2 1:30 AM Sun:** Γ_X two ways at small α plus the channel overlays. Large-α convergence finishes overnight (G3 7:00 AM). Physics freeze 8:00 AM |

## 1. Goal and why
Task 2.1 asks for Γ_X = 1/T_X, the decay rate of Re⟨a⟩(t) starting from |α⟩⊗|0⟩, a check that Γ_X ∝ e^{−γα²}, and (not graded) a Golden Rule discussion. We answer it **two ways**, with **two physical channels**:
- **Method 1 (centerpiece):** Γ_X = −λ₁, where λ₁ is the smallest-|λ| eigenvalue of the **odd Z₂ block** of the Liouvillian (`src.spectral.gamma_x`). It reaches α = 2.7 (one-mode) and α = 3.0 (two-mode), far past the prompt's time-domain wall at α ≈ 1.4.
- **Method 2 (cross-check):** a time-domain fit of Re⟨a⟩ at α ∈ {0.8, 1.0, 1.2, 1.4}. It must agree with Method 1 within 2% at the same model and truncation.
- **Channel 1 (code space, Golden Rule):** Γ⁽¹⁾ = κ_aα²(coth 2α² − 1) ≈ 2κ_aα²e^{−4α²}, so γ = 4.
- **Channel 2 (out of the code space and back):** Γ⁽²⁾ ≈ c·(κ_a²/κ₂)e^{−2α²}, so γ = 2. A κ_a sweep identifies the channels: the log-log slope d lnΓ_X/d lnκ_a moves from ≈1 to ≈2.
- Then thermal photons, and the two-mode/one-mode ratio (non-adiabaticity).
- **Why it matters:** the deck says "γ ≲ 2" and the prompt's REVIEW note says a thermal-free model gives γ > 2. We explain exactly why (RESEARCH §5). Every reported number is a v2 record with a convergence block and an independent cross-check (CONTRACT §6). The 20×6 truncation trap (a 20× wrong Γ_X at α = 2.1) is the cautionary tale that the edge-weight check catches.

## 2. Read first
- `AGENTS.md`; `docs/plan/CONTRACT.md` §1–§8, §11, §12, §14, §15; `docs/plan/RESEARCH.md` §1, §2, §4.2, **§5**, **§9**.
- `docs/plan/status/l1-spectral.md`: the measured cost and RAM profile, `NA_EIG_MAX`/`NB_EIG_MAX` and the anchor table. **Its measured numbers override the cost model below.**
- `src/spectral.py`, `src/convergence.py`, `src/results.py` (docstrings); `tasks/task_1_3a.py` for code style; `notebooks/04_task_1_3a_which_state.ipynb` for the notebook style.
- `docs/challenge_prompt_v4.md`, Task 2.1 (Section 2) and the REVIEW (David) note under it.
- **Conventions (RESEARCH §5):**
  - Γ_X = decay rate of Re⟨a⟩ = −λ₁ = the prompt's 1/T_X = Ferrari et al.'s Γ_bf.
  - Dubovitskii's rate is per direction, so Γ_X = 2 × Dubovitskii's rate.
  - Units: rad/µs, time in µs. κ_a = 0.0584336, κ₂ = 4g₂²/κ_b = 5.6275, g₂ = 4.79411, κ_b = 16.33628, κ_a/κ₂ = 0.010384, κ_b/g₂ = 3.41.
  - Two-mode drive: ε_d = α²g₂ at each α.

## 3. Allowlist (touch nothing else)
- **Code:** `tasks/task_2_1_eig.py`, `tasks/task_2_1_td.py`, `tasks/task_2_1_channels.py`, `tasks/task_2_1_thermal.py`, `tasks/task_2_1_figures.py`, `notebooks/06_task_2_1_bit_flips.ipynb`, `tests/test_l2b_gamma_x.py`.
- **Your outputs:** `results/records/t2_1.*.json` (only the IDs in §7), `results/arrays/t2_1.*.npz`, `figures/task_2_1_*.png`, and `docs/plan/status/l2b-gamma-x.md`.
- **Never edit** `src/**`, `docs/plan/CONTRACT.md`, other lanes' files, `notes/`, `docs/challenge_prompt_v4.md` or `docs/handwritten/`. If `src/spectral.py` is missing something, write `DECISION NEEDED`; don't patch it.

## 4. Interfaces you implement / rely on
**Rely on (CONTRACT, frozen):**
- `src.model.one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, ...) -> (H, jumps, a)`.
- `src.model.two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, ...) -> (H, jumps, (a, b))`, plus `coherent2(Na, Nb, alpha)`. The thermal jumps come from `loss_jumps`: √(κ_a(1+n_th))·a and √(κ_a·n_th)·a†.
- `src.config as C` (**import it first**): `G2, KAPPA_B, KAPPA_A, KAPPA_2, METHOD_LONG` (Tsit5 rtol 1e-8, atol 1e-10, max_steps 1e7), `NA_EIG_MAX, NB_EIG_MAX`, `trunc_for(alpha, "eig")`.
- `src.spectral`:
  - `gamma_x(H, jumps, Na, Nb, k=2)` returns `{'gamma_x', 'lams', 'rel_residual', 'edge_weight', 'cond_est', 'wall_s', 'sector', 'dim'}`. It raises if κ_a = 0.
  - `low_spectrum(H, jumps, Na, Nb, k=4, sector="full_deflated")`.
  - `left_eigvec_operator(H, jumps, Na, Nb, sector="odd")`.
  - `liouvillian`, `sector_indices`, `unvec`.
  - For one-mode, pass `Nb=1`.
- `src.analysis.fit_exp_decay(t, y) -> (gamma, A)` (log-linear).
- `src.convergence`: `sweep`, `converged_at`, `convergence_block(sweeps, key, rel_tol, chosen)`.
- `src.results`: `std_params`, `record(...)`, `save_arrays`, `load_record`.
- `src.plotting.save(fig, name, dpi=200, quick=False)`.

**Implement (your own modules; the other scripts import these):**
```python
# tasks/task_2_1_channels.py: pure numpy helpers + main()
def gamma_ch1(alpha, kappa_a)                    # kappa_a*alpha^2*(coth(2 alpha^2) - 1)   (exact code-space rate)
def gamma_ch1_approx(alpha, kappa_a)             # 2*kappa_a*alpha^2*exp(-4 alpha^2)
def gamma_ch2(alpha, kappa_a, kappa_2, c=1.0)    # c*kappa_a**2/kappa_2*exp(-2 alpha^2)
def gamma_thermal_extra(alpha, kappa_a, n_th, c_th=1.0)   # c_th*kappa_a*n_th*exp(-2 alpha^2)
def crossover_alpha2(kappa_a, kappa_2)           # naive ln(kappa_2/kappa_a)/2 = 2.284
def crossover_alpha2_exact(kappa_a, kappa_2, c=1.0)       # root of gamma_ch1 = gamma_ch2(c) (brentq on alpha^2 in [1, 6])
def local_slope(alpha2, gamma) -> np.ndarray     # gamma_local = -np.gradient(np.log(gamma), alpha2)  (POSITIVE number)
def global_gamma(alpha2, gamma, window) -> dict  # LSQ of ln gamma vs alpha2 on window=(a_lo, a_hi) in ALPHA: {'gamma','gamma_stderr','intercept','window'}
def kappa_a_exponent(kappas, gammas) -> dict     # {'slope': polyfit(ln k, ln G, 1)[0], 'local': np.gradient(ln G, ln k)}
def fit_c(alpha, lam1, kappa_a, kappa_2, window=(1.6, 2.7)) -> dict   # c = exp(mean ln((lam1-gamma_ch1)/gamma_ch2(c=1))) on window; {'c','c_min','c_max'}
def load_any(rid, quick=False) -> dict           # load_record(rid), or results/quick/records/<rid>.json when quick
# tasks/task_2_1_eig.py
def build(model, alpha, Na, Nb, kappa_a=C.KAPPA_A, n_th=0.0) -> (H, jumps)   # one_mode(Na, C.KAPPA_2, alpha, ...) | two_mode(Na, Nb, C.G2, alpha**2*C.G2, C.KAPPA_B, kappa_a, n_th)
def solve(model, alpha, Na, Nb, kappa_a=C.KAPPA_A, n_th=0.0) -> dict  # gamma_x(...) + 'passes' = rel_residual<1e-4 and edge_weight<1e-6
def run_alpha(model, alpha, na_list, nb_list, n_th=0.0, quick=False, full_l_check=False) -> Path
def record_id(kind, model, alpha=None, n_th=0.0) -> str
def attach_cross_check(rid, entry, quick=False)  # load, replace the entry with the same 'method' (or append), re-write via record()
# tasks/task_2_1_td.py
def fit_window(t, y, t0=3.0, window=100.0) -> dict  # gamma from fit_exp_decay on t0<=t<=t0+window; plus np.polyfit(cov=True)
                                                     # -> {'gamma','A','gamma_stderr','rel_rms_residual','fit_window_us':[t0, t0+window]}
def simulate(model, alpha, Na, Nb, T, method) -> (t, re_a, parity)
```
`record_id` kinds (CONTRACT §6.3; regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`):

| kind | ID |
|---|---|
| eig | `t2_1.gamma_x.eig.{model}.a{α:.2f}.nth{n_th:g}` |
| td | `t2_1.gamma_x.td.{model}.a{α:.2f}` |
| slope | `t2_1.gamma_local_slope.eig.{model}.a{α:.2f}` |
| kexp | `t2_1.kappa_a_exponent.eig.one_mode.a{α:.2f}` |
| fit | `t2_1.gamma_fit.eig.{model}.nth{n_th:g}` |
| fit_td | `t2_1.gamma_fit.td.{model}.nth0` |
| c2 | `t2_1.channel2_c.eig.one_mode.nth0` |

## 5. Tests to write FIRST (TDD)
In `tests/test_l2b_gamma_x.py`, written and committed failing before any implementation. Fast tests must total under 30 s.
- **`test_ch1_alpha1`:** `gamma_ch1(1.0, C.KAPPA_A) == approx(2.1804e-3, rel=1e-3)`, and it equals `C.KAPPA_A*(1/np.tanh(2)-1)` to rel 1e-12.
- **`test_ch1_approx`:** the ratio `gamma_ch1/gamma_ch1_approx` is `1/(1-e^{-4}) = 1.01866` (rel 1e-4) at α = 1.0, and differs from 1 by less than 1e-6 at α = 2.1.
- **`test_ch2_alpha1`:** `gamma_ch2(1.0, C.KAPPA_A, C.KAPPA_2) == approx(8.2115e-5, rel=1e-3)`.
- **`test_crossover`:** `crossover_alpha2(...) == approx(2.284, abs=2e-3)` and `crossover_alpha2_exact(..., c=1.0) == approx(3.214, abs=5e-3)`.
- **`test_ch1_share_of_anchors`:** `gamma_ch1(α)/anchor` for the one-mode anchors {1.0: 2.2819e-3, 1.4: 1.0744e-4, 1.8: 2.0693e-6, 2.1: 1.1699e-7} equals [0.956, 0.840, 0.430, 0.096] within abs 0.005.
- **`test_local_slope_pure_exp`:** Γ = 3e-2·e^{−3.1α²} on α = 0.8..2.7 (step 0.1) gives `local_slope == 3.1` within abs 1e-9 everywhere.
- **`test_local_slope_ch1_analytic`:** on α ∈ [1.0, 2.7] (step 0.01), `local_slope(α², gamma_ch1)` matches 4 − 1/α² + 4e^{−4α²}/(1 − e^{−4α²}) within abs 1e-3 at interior points.
- **`test_local_slope_two_channel_shape`:** Γ = ch1 + ch2(c=1) on α = 0.8..2.7. The maximum γ_local is in [3.2, 3.4], at α ∈ [1.3, 1.5]; γ_local(2.7) = 2.00 ± 0.05; γ_local(0.8) is in [2.7, 2.95]. The local slope is **not** monotone, because of the α² prefactor of channel 1.
- **`test_kappa_a_exponent`:** Γ = 7κ^{1.5} gives slope 1.5 (abs 1e-12). Γ = κ + 1e3κ² on κ ∈ geomspace(1e-5, 1e-1) gives a `local` that increases monotonically from below 1.05 to above 1.95.
- **`test_fit_c_recovers`:** the synthetic λ₁ = ch1 + 1.25·ch2(c=1) on α ∈ [1.6, 2.7] gives `fit_c == approx(1.25, rel=1e-9)`.
- **`test_global_gamma_window`:** Γ = 5e-2·e^{−2.55α²} gives 2.55 (abs 1e-9) on the window (1.0, 2.1). Multiplying the α = 2.5 point by 10 leaves the result unchanged.
- **`test_fit_window_synthetic`:** use t = linspace(0, 103, 2061), y = 1.4e^{−Γt} + 0.3e^{−5t}cos(19.7t), for Γ ∈ {2.28e-3, 1.2e-4}.
  - Γ is recovered within rel 1e-4, `rel_rms_residual < 1e-6`, and `fit_window_us == [3.0, 103.0]`.
  - Repeat with multiplicative noise (1 + 1e-7·N(0,1), seed 0): the error is within 2%, and `gamma_stderr > 0`.
- **`test_record_ids`:**
  - `record_id("eig", "one_mode", 2.1, 0.0) == "t2_1.gamma_x.eig.one_mode.a2.10.nth0"`.
  - With n_th = 0.03 the ID ends in `.nth0.03`.
  - The td ID is `"t2_1.gamma_x.td.two_mode.a1.40"`.
  - Every kind matches the regex.
- **`test_one_mode_anchors`** (fast; D² ≤ 1600): `solve("one_mode", α, 40, 1)` reproduces the four one-mode anchors at rel 1e-3, with `passes` True.
- **`test_truncation_trap_flagged`** (fast, about 1 s; mark it slow if it takes over 10 s): `solve("two_mode", 2.1, 20, 6)` gives about 7.6e-6 and `edge_weight > 1e-6`, so `passes` is False.
- **`@pytest.mark.slow test_two_mode_anchors`:** at 28×8, α ∈ {1.0, 1.4, 1.8, 2.1} gives {2.3007e-3, 1.2021e-4, 4.0696e-6, 3.8831e-7} at rel 1e-3, all passing.
- **`@pytest.mark.slow test_td_vs_eig_one_mode`:** α = 1.0, N = 30, window [3, 103] µs with `C.METHOD_LONG`. Then |Γ_td − Γ_eig|/Γ_eig < 0.02, and both are within 1% of 2.2819e-3.

If an anchor test fails: **don't edit the anchor.** Write a `DECISION NEEDED` (anchors are reproduce-don't-trust; one side is wrong).

## 6. Method, step by step
1. **Setup.** Create the branch, copy `docs/plan/status/_TEMPLATE.md` to `status/l2b-gamma-x.md`, and mark it "started". Copy `NA_EIG_MAX`/`NB_EIG_MAX` and the measured odd-block cost from l1's status file into yours.
2. **Tests (§5).** Commit them failing. Then implement `task_2_1_channels.py` helpers until the pure tests pass.
3. **`task_2_1_eig.py`.**
   - **CLI:** `--model {one_mode,two_mode}`, `--alpha A [A ...]` (default: the full grid of that model), `--na-list 28,32,36`, `--nb-list 8,10,12`, `--nth 0`, `--full-l-check`, `--anchors` (prints the anchor table, writes nothing), `--quick`.
   - **One-mode:** grid α = 0.8..2.7, step 0.1.
     - N-list default [N0, N0+8, N0+16], with N0 = `C.trunc_for(α, "eig")[0]` (16 at α = 0.8, 28 at 2.1, 34 at 2.7).
     - Chosen N = `converged_at(rows, "Gamma_X", "Na", 1e-3)`, the **smallest** converged N, because the precision floor ε·‖L‖ grows like κ₂N².
     - If not converged, extend by +8, up to N = 80.
     - **Cap at α = 2.7** (floor ≈ ε·κ₂N², about 1e-11 at N = 80). If `rel_residual ≥ 1e-4` below 2.7, cap lower and state the floor.
     - Truncation `{"Na": N, "Nb": 1}`; only the `Na` axis is swept.
   - **Two-mode:** grid α ∈ {0.8, 1.0, …, 3.0 (step 0.2)} ∪ {2.1}. **2.1 is the target and the anchor; the step-0.2 grid skips it.**
     - Na-list default [Na0, Na0+4, Na0+8], with Na0 = `trunc_for(α, "eig")[0]`.
     - Nb-list default [6, 8, 10] for α ≤ 1.4 and [8, 10, 12] above.
     - Run the Na sweep at Nb = nb[−2] (≥3 values), and the Nb sweep at Na = na[−2] (≥2 values, 3 by default), **at every α, separately**.
     - Chosen truncation = (na[−2], nb[−2]), the crossing point of the two sweeps. If it is below `needed` on either axis, extend that axis once (+4 Na or +2 Nb), within `NA_EIG_MAX`/`NB_EIG_MAX`.
     - If that still fails, write the record with `converged: false`, flag it in the status file, and don't claim it.
   - **Acceptance (CONTRACT §8)** for the chosen eigenvalue: `rel_residual < 1e-4`, `edge_weight < 1e-6`, and stable across two truncations (`converged: true`).
   - **Record fields:**
     - value = Γ at the chosen truncation.
     - uncertainty = max over axes of |Γ(largest) − Γ(second largest)|.
     - `numerics = {rel_residual, edge_weight, cond_est, sector: "odd", sigma: 0.0, k: 2}`.
     - `method = "liouvillian_eig_odd_sector"`, `units = "1/us"`, `quantity = "Gamma_X"`.
     - `params = std_params(alpha=α, n_th=n_th, model=model)`.
     - Arrays: `lams` and the sweep tables.
   - **`--full-l-check` (two-mode):** reuse the chosen truncation of an existing record, run `low_spectrum(..., k=4, sector="full_deflated")`, and attach the cross-check `{"method": "full_deflated_liouvillian", "value": rates[0], "tol": 1e-3}`. The full L costs about 8× the odd block, so queue it when it is over 15 min.
   - **Anchors first (`--anchors`):**
     - One-mode N = 40; two-mode 28×8 at α ∈ {1.0, 1.4, 1.8, 2.1}.
     - At α = 2.1, Nb = 6: Na = 28/32/36 → 3.987e-7. Nb 6 → 8 moves the result 2.6%. 20×6 → 7.607e-6, and it is flagged.
     - Put the table in the status file. If any value is more than 1% off at the same truncation, stop and write `DECISION NEEDED`.
   - **Who runs what:** the lane runs one-mode (all α; seconds each) and two-mode α ≤ 1.8 plus 2.1. α ∈ {2.0, 2.2, 2.4, 2.6, 2.8, 3.0} and every full-L check above 15 min go to **Jobs to queue** (§7).
4. **`task_2_1_td.py`** at α ∈ {0.8, 1.0, 1.2, 1.4}. **Exclude 0.6**: it is not a double well (overlap e^{−2α²} = 0.49).
   - **Initial states:** one-mode `dq.coherent(N, α)`; two-mode `coherent2(Na, Nb, α)`.
   - `mesolve(H, jumps, ψ0, tsave, exp_ops=[(a+a.dag())/2, P_mem], method=C.METHOD_LONG, save_states=False)`.
     - P_mem = `dq.parity(N)`, or `dq.tensor(dq.parity(Na), dq.eye(Nb))` for two-mode.
     - tsave = `jnp.linspace(0, 103, 1031)`, which is sparse; there is no `options=` argument.
   - **Fit** Re⟨a⟩ with `fit_window` for t ≥ t₀ = 3 µs over 100 µs.
     - It is a single exponential: the ringdown has decayed at κ_b/4 by t₀, and the Z₂ plus antiunitary symmetry keeps Y_L unexcited.
     - At α = 1.4 the trace decays only about 1.2% over the window, which is why the drift check matters.
   - **Drift bound:** repeat at `dq.method.Tsit5(rtol=1e-10, atol=1e-12, max_steps=10_000_000)`.
     - value = the tight result; drift_rel = |Γ_loose − Γ_tight|/Γ_tight, which must be < 0.5%.
     - uncertainty = √(stderr² + (Γ_loose − Γ_tight)²).
   - **Truncation:** use the smallest (Na, Nb) in the eig sweeps whose Γ is within 1e-3 of the chosen value. A two-mode run costs roughly ∝ D³, so measure α = 0.8 first. Solve the eig at **exactly** that truncation for the gate.
     - The td convergence block sweeps Na ∈ {Na_td, Na_td+4} at Nb_td, and Nb ∈ {Nb_td, Nb_td+2} at Na_td, with rel_tol 5e-3.
   - **Gate:** |Γ_td − λ₁(same model, same truncation)|/λ₁ ≤ 0.02.
   - **Records:** `t2_1.gamma_x.td.{model}.a{α:.2f}`, with `method = "time_domain_fit_re_a"`.
     - `numerics = {fit_window_us, gamma_stderr, rel_rms_residual, rtol, drift_rel}`.
     - `cross_check` = the eig value at the same truncation, tol 0.02.
     - Then `attach_cross_check(eig_id, {"method": "time_domain_fit", "ref_id": td_id, "value", "rel_diff", "tol": 0.02, "agree"})`.
   - **Also write** `t2_1.gamma_fit.td.{model}.nth0`, the γ fitted over α ∈ [0.8, 1.4] (the prompt's log-linear fit). Its cross-check is the eig γ over the same window, tol 0.05.
   - **Order:** one-mode × 4 and two-mode α ∈ {1.0, 1.4} first (the G2 minimum), then two-mode 0.8 and 1.2. Any single run over 15 min goes to the queue.
5. **`task_2_1_channels.py` main()** reads the nth0 eig records (via `load_any`).
   - **(a) Overlays:** ch1 (exact), ch2 with c = 1 (Dubovitskii's per-direction (κ₁²/2κ₂)e^{−2α²} × 2), and ch1 + c·ch2 with the fitted c.
     - `fit_c` on the one-mode λ₁ − Γ⁽¹⁾ over α ∈ [1.6, 2.7]. The anchors imply c ≈ 1.2–1.4 (RESEARCH quotes ≈ 1.3).
     - Outside [0.8, 2.0], write `DECISION NEEDED`.
     - Record `t2_1.channel2_c.eig.one_mode.nth0` with cross-check vs c = 1, tol 0.5. State why that tolerance: higher orders in κ_a/κ₂ are missing from the second-order estimate.
     - Arrays: `alpha2, ch1, ch2, total`; L6 builds `errors.json → analytic` from them.
   - **Crossover:** report both. The naive estimate is α² ≈ ln(κ₂/κ_a)/2 ≈ 2.28, which drops the 2α² prefactor. The exact root of Γ⁽¹⁾ = cΓ⁽²⁾ is α² ≈ 3.21 (c = 1) or ≈ 3.08 (c = 1.25), i.e. α ≈ 1.76–1.79. That is consistent with channel 1 carrying 43% of λ₁ at α = 1.8. Mark the exact one on the figure.
   - **(b) Analytic cross-check.** `attach_cross_check` on **one-mode** eig records with method `"analytic_channels"`, value Γ⁽¹⁾ + Γ⁽²⁾(c = 1) (**parameter-free**, not the fitted c), tol 0.3. The expected rel_diff is ≈ 0.01, 0.05, 0.12 and 0.14 at α = 1.0, 1.4, 1.8, 2.1.
     - On two-mode records, add the same entry honestly; it is expected to fail above α ≈ 1.4, because the two-mode model is ×2 at 1.8 and ×3 at 2.1.
   - **(c) κ_a sweep (identification experiment).** One-mode, κ_a × {0.25, 0.5, 1, 2, 4} at α ∈ {1.0, 1.4, 1.8, 2.1}, at the chosen N and at N+8.
     - Record `t2_1.kappa_a_exponent.eig.one_mode.a{α:.2f}` = the slope. Expected ≈ 1.06, 1.17, 1.56, 1.89.
     - Cross-check = the same polyfit on ch1 + ch2(c = 1), tol 0.1.
   - **(d) Local slope** γ_local = −d lnΓ_X/d(α²) for both models, via `local_slope` on the converged grid. Record `t2_1.gamma_local_slope.eig.{model}.a{α:.2f}` (positive number).
     - Anchor secants: one-mode 3.18 (1.0–1.4), 3.09 (1.4–1.8), 2.46 (1.8–2.1); two-mode 3.07, 2.65, 2.01. The ≈2.0 in RESEARCH is the two-mode value.
     - Channel model: peak ≈ 3.3 at α ≈ 1.4, then 2.0 by α ≈ 2.4.
   - **(e) Global γ:** `t2_1.gamma_fit.eig.{model}.nth0` on the primary window α ∈ [1.0, 2.1]. Anchors imply ≈ 2.91 (one-mode) and ≈ 2.55 (two-mode).
     - Store `numerics.alt_windows` for [0.8, 1.4] and [1.8, max].
     - Compare with the deck's "γ ≲ 2" and the experimental γ ≈ ln 4.2 ≈ 1.44 (Réglade et al.).
   - **Derived-record convergence** (c2, kexp, slope, fit): use `convergence_block({"trunc_level": ({}, rows)}, key, rel_tol=1e-2, chosen={"trunc_level": 0})`.
     - Level 0 uses the chosen values. Level 1 recomputes from, per α, the largest-truncation sweep value that differs most from the chosen one.
     - Cross-checks recompute the same quantity from an independent source with the tol stated: td values (α ≤ 1.4), `full_deflated` values (two-mode), or the c = 1 channel model (one-mode).
     - If no independent source exists, write the entry with `agree: false`; that record is then not claimable.
6. **`task_2_1_thermal.py`.** n_th ∈ {0.01, 0.03, 0.05}, reusing `run_alpha(..., n_th=n)`. One-mode uses the full grid; two-mode uses α ∈ {1.0, 1.4, 1.8, 2.1}.
   - **Never write the n_th = 0 records:** they are the eig records, and the IDs would collide. Read those instead.
   - **Records:** `t2_1.gamma_x.eig.{model}.a{α:.2f}.nth{n:g}` and `t2_1.gamma_fit.eig.{model}.nth{n:g}` (same window, [1.0, 2.1]).
   - **Prediction (Gautier et al., Eq. 4):** an extra ≈ κ_a·n_th·e^{−2α²}. This is first order in κ_a, so it matters even at n_th = 0.01 (κ_a·n_th ≈ κ_a²/κ₂).
     - Fit c_th from ΔΓ − 2n_th·Γ⁽¹⁾ against κ_a·n_th·e^{−2α²} on α ∈ [1.6, 2.7], and store it in `numerics.c_th`.
     - **The prefactor is uncertain by ×2:** Gautier's first term κ₁α²e^{−4α²} is half our channel 1, which suggests per-direction rates. Report the fitted c_th; don't assume it.
   - **Expected:** the crossover moves earlier (exact roots α² ≈ 2.75, 2.38, 2.16 with c_th = 1) and γ falls. **Do not promise** γ reaches 1.44; Ferrari et al. attribute the saturation to cross-Kerr plus dephasing.
7. **`task_2_1_figures.py`** reads records only (`--quick` reads the quick ones). Save via `src.plotting.save`.
   - **`task_2_1_gamma_x`:** log Γ_X against α².
     - One-mode eig (line + markers), two-mode eig (markers with error bars), td points (open markers).
     - ch1 dashed, ch2 dotted, ch1 + c·ch2 solid thin.
     - Vertical lines at the exact crossover and at α = 2.1.
     - Unconverged points are hollow grey and labelled.
     - **Inset:** two-mode/one-mode ratio (anchors ×1.01, 1.12, 1.97, 3.32 at α = 1.0, 1.4, 1.8, 2.1), labelled non-adiabaticity, with the caption "κ_b/g₂ = 3.4 here vs 3 in Ferrari et al. 2026, *Bit flips, saturation, and quantum chaos in dissipative cat qubits*, arXiv:2605.24100: non-adiabaticity always raises Γ_bf".
   - **`task_2_1_local_slope`:** both models plus the channel curve; reference lines at 4, 2 and 1.44, and the deck's "≲ 2".
   - **`task_2_1_kappa_a_sweep`:** left, Γ_X vs κ_a/κ_a0 (log-log) at 4 α with guide slopes 1 and 2; right, the exponent vs α² with (Γ⁽¹⁾ + 2cΓ⁽²⁾)/(Γ⁽¹⁾ + cΓ⁽²⁾).
   - **`task_2_1_thermal`:** Γ_X vs α² per n_th, plus ΔΓ against the c_th·κ_a·n_th·e^{−2α²} fit.
   - **`task_2_1_committor_wigner`:** at α = 2.1.
     - (i) One-mode **right** odd eigenvector, from `scipy.sparse.linalg.eigs` at σ = 0 on `L[idx][:, idx]` with `idx = sector_indices(N, 1, 1)`, then `unvec`. It shows just two opposite-sign blobs at ±α.
     - (ii) One-mode **left** eigenvector, from `left_eigvec_operator`, Hermitian part (W + W†)/2. This is the which-well indicator, about sign(Re β).
     - (iii) Two-mode left eigenvector at the chosen truncation: Hermitian part, then `dq.ptrace(W, 0, (Na, Nb))`, then `dq.wigner`.
     - These operators are **traceless**. If `dq.wigner` normalizes by the trace, compute the Weyl symbol directly as (2/π)Tr[D(β)†WD(β)P] on an 81×81 grid. Use a symmetric colour scale.
8. **Notebook `06_task_2_1_bit_flips.ipynb`.** Follow the style of notebook 04: `os.chdir('..')`, `show`, and `RERUN = False`.
   - `RERUN=True` runs the five scripts with `--quick` (via `subprocess`). Otherwise it loads the records with `load_record`, shows the 5 figures, and prints a table: α, one-mode, two-mode, td, rel_diff, and the ch1 share.
   - **Markdown cells:**
     - Conventions.
     - The two channels.
     - The **Golden Rule discussion (not graded):** ⟨−α|α⟩ = e^{−2α²}, so |⟨−α|a|α⟩|² = α²e^{−4α²} and γ_FGR = 4, which is exactly channel 1. It fails above α² ≈ 3 (naive estimate 2.3), where channel 2 dominates: one photon loss leaves the code space, and the confinement returns the state to the *other* well, which costs only e^{−2α²}.
     - The thermal result.
9. **Finish.** Commit the code, run production (records then have `dirty: false`), commit the outputs, and update the status file at every milestone.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **Records** (all `task="2.1"`, plus arrays with the same ID):
  - eig: one-mode × 20 α, two-mode × 13 α (nth0).
  - td: × 4 α × 2 models.
  - Thermal eig: 3 n_th × (20 one-mode + 4 two-mode).
  - kexp × 4.
  - slope: one per converged α per model.
  - gamma_fit: eig × 2 models × 4 n_th, plus td × 2.
  - channel2_c × 1.
- **Figures:** `figures/task_2_1_{gamma_x,local_slope,kappa_a_sweep,thermal,committor_wigner}.png`.
- **Quick (`--quick`, ≤ 2 min each; output to the git-ignored `results/quick/`, `figures/quick/`):**
  - eig: one-mode α ∈ {1.0, 1.4}, N ∈ {20, 24, 28}; two-mode α = 1.0, Na ∈ {14, 16, 18}, Nb ∈ {4, 6}.
  - td: one-mode α = 1.0, N = 20, a 30 µs window.
  - channels/thermal/figures run on the quick records.
- **Jobs to queue** (status-file section; the integrator submits these after the merge). Estimates use t_full ≈ 113 s·(Na·Nb²/1792)³ with the odd block ≈ 1/8 of the time and 1/4 of the RAM. RAM ≈ 1.25 GB·(Na·Nb²/4608)² is rough; replace both with l1's measured profile.

| α (two-mode) | Na-list | Nb-list | est. sweep (odd) | est. peak RAM | full-L check |
|---|---|---|---|---|---|
| 2.0 | 26,30,34 | 8,10,12 | 7 min | 1.1 GB | 9 min |
| 2.2 | 30,34,38 | 8,10,12 | 10 min | 1.4 GB | 13 min |
| 2.4 | 32,36,40 | 8,10,12 | 12 min | 1.6 GB | 15 min |
| 2.6 | 34,38,42 | 8,10,12 | 14 min | 1.8 GB | 18 min |
| 2.8 | 36,40,44 | 8,10,12 | 17 min | 2.0 GB | 21 min |
| 3.0 | 38,42,46 | 8,10,12 | 19 min | 2.2 GB | 24 min (≈4–5 GB: big job, one at a time) |

- **Queue mechanics:**
  - Command form: `& $env:DUQ_PY -m tools.runq submit --name l2b_eig2m_a2.40 --ram-gb 1.6 -- D:\duq-venv\Scripts\python.exe -m tasks.task_2_1_eig --model two_mode --alpha 2.4 --na-list 32,36,40 --nb-list 8,10,12`.
  - Each full-L check is a separate job (`--full-l-check --alpha 2.4`, `--ram-gb 5`).
  - Follow-ups, in order, after the queue finishes: `tasks.task_2_1_thermal --model two_mode`, then `tasks.task_2_1_channels`, then `tasks.task_2_1_figures`.

## 8. Acceptance gates (ALL must pass before DONE)
1. `pytest -m "not slow"` is green, and `tests/test_l2b_gamma_x.py -m slow` is green.
2. Every anchor reproduces within 1% at the same truncation, or has a resolved `DECISION NEEDED`. 20×6 at α = 2.1 is flagged by edge weight.
3. Every claimed eig record has `rel_residual < 1e-4`, `edge_weight < 1e-6` and `convergence.converged == true`, with Na swept over ≥3 values and Nb over ≥2.
4. **Two ways:** for α ∈ {0.8, 1.0, 1.2, 1.4}, td vs eig (same model, same truncation) rel_diff ≤ 0.02 for one-mode, and for two-mode at least at 1.0 and 1.4. Drift_rel < 0.5%.
5. **Channels:** c is fitted and lies in [0.8, 2.0]. κ_a exponents rise from ≈1 (α = 1.0, within 0.1) to > 1.7 (α = 2.1). The one-mode analytic cross-check (c = 1) agrees within 0.3 at all α ≤ 2.1.
6. Thermal records exist for n_th ∈ {0.01, 0.03, 0.05} (one-mode at minimum), with c_th and the γ change reported.
7. All 5 figures exist in production. The notebook runs with `RERUN=False`. Every production record has `provenance.dirty == false`.
8. The status file is complete (§12), and Jobs to queue lists every pending job with its command, RAM and time.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -m pytest tests/test_l2b_gamma_x.py -m "not slow" -q
& $env:DUQ_PY -m pytest tests/test_l2b_gamma_x.py -m slow -q
& $env:DUQ_PY -m tasks.task_2_1_eig --anchors
& $env:DUQ_PY -m tasks.task_2_1_eig --quick ; & $env:DUQ_PY -m tasks.task_2_1_td --quick
& $env:DUQ_PY -m tasks.task_2_1_eig --model one_mode
& $env:DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 0.8 1.0 1.2 1.4 1.6 1.8 2.1
& $env:DUQ_PY -m tasks.task_2_1_eig --model two_mode --alpha 1.0 1.4 --full-l-check
& $env:DUQ_PY -m tasks.task_2_1_td --model one_mode ; & $env:DUQ_PY -m tasks.task_2_1_td --model two_mode --alpha 1.0 1.4
& $env:DUQ_PY -m tasks.task_2_1_channels ; & $env:DUQ_PY -m tasks.task_2_1_thermal --model one_mode
& $env:DUQ_PY -m tasks.task_2_1_figures
& $env:DUQ_PY -m pytest -m "not slow" -q        # whole suite before DONE
```
Run at most 3 heavy processes at once, and only one sparse LU above 3 GB at a time.

## 10. Out of scope / do not
- No Γ_X(ε_Z) (that is l4b), no Γ_Z fits (l2a), no Felis (l8), no Kerr or dephasing terms. Don't claim to reproduce the experimental saturation.
- No `dq.slindbladian(...).to_numpy()`: it is dense, about 348 GB at 32×12. No time-domain runs at α > 1.4 (T_X reaches seconds). Don't include α = 0.6 in any fit.
- Don't fit c and then use that same c as the "independent" cross-check. Don't edit anchors to make tests pass.
- Don't write `docs/defense.md` or `docs/handwritten/`. Harshit answers the judge questions himself.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
- **Wording** (in the status file):
  ```
  DECISION NEEDED (l2b-gamma-x, <time>): <one-line problem>.
  Evidence: <numbers, IDs, truncations>.
  Options: A) … B) …
  Default if no answer by <time+45 min>: <option>.
  ```
  Keep working on the other items.
- **Anchor mismatch over 1%:** check the ε_d = α²g₂ scaling, the κ_a units and the odd-sector index. Report both numbers; don't pick one silently.
- **Odd solve over 10 min or LU over 6 GB:** apply the speed levers (RESEARCH §9: real Hermitian form, `MMD_AT_PLUS_A`, `pypardiso`) as a `DECISION NEEDED` to l1. Quote only the feasible converged two-mode range, with one-mode above it (labelled).
- **Precision floor** (rel_residual ≥ 1e-4): cap the curve there and state the floor.
- **td gate missed by 2–5%:** lengthen the window to 150 µs, move t₀ to 5 µs, then tighten the tolerance. If it still fails, report honestly and mark the record not claimable.
- **Cut line**, in order: thermal two-mode → thermal n_th = 0.03 → two-mode td at 0.8 and 1.2 → two-mode α ≥ 2.6 → the committor two-mode panel.
- **Never cut:** one-mode eig, two-mode eig at α ≤ 2.1 with convergence, td at α = 1.0 and 1.4 (both models), the channel overlays, c, and the κ_a sweep.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
**Status file at DONE:**
- Branch, commit SHAs, and test counts (fast and slow).
- Anchor table (anchor, ours, rel_diff, truncation).
- Per-α table: one-mode Γ_X, two-mode Γ_X, td, chosen truncation, rel_residual, edge_weight, converged.
- The fitted c, c_th per n_th, both crossovers, κ_a exponents, γ_fit per model/window/n_th, and the two-mode/one-mode ratios.
- The list of record IDs written, and Jobs to queue (submitted / pending, command, RAM, time).
- Deviations, and open or closed `DECISION NEEDED` items.
- **Notes for L6:** where the analytic arrays and the thermal grids are. **For L7:** the claim-ready IDs. **For L8:** one-mode and two-mode Γ_X at α = 2.1.

**Judge questions for Harshit (do not answer them here):**
1. Your Γ_X is an eigenvalue of a matrix you built yourself. How do you know it is the decay rate of Re⟨a⟩ the prompt asks for, and not a truncation artefact like the 20×6 value at α = 2.1?
2. The deck says γ ≲ 2, the Golden Rule says 4, and your fit gives about 2.5 to 2.9. Which is right at α = 2.1, and which numerical experiment in your repo proves which mechanism dominates there?
3. Why does keeping the buffer mode explicit make bit flips about 3× faster at α = 2.1, and what does that imply for hardware with κ_b/g₂ ≈ 3.4?
