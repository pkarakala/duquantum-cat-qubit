# Brief `l4a-readout`: Task 2.3: transmon-free readout and the linear-response backbone

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l4a-readout`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/07-l4a-readout.md`, then execute this brief exactly. Keep `docs/plan/status/l4a-readout.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l4a-readout` | `std/l4a-readout` (from `standard-track`) | `l0-core` (required for the simulations); `l1-spectral` optional (one cross-check). `src/linresp.py` needs neither, so start it at once | strongest available (Opus-class, max reasoning) | 2.5 h | Phase 1, DONE by **G1, 9:45 PM Sat Oct 24** |

## 1. Goal and why
Task 2.3 of `docs/challenge_prompt_v4.md`: add H_Z = ε_Z(a + a†) to the two-mode model, simulate ⟨b⟩(t) from each codeword ±α, show opposite-sign steady values (the readout contrast; sanity check ⟨b⟩_ss ≈ ∓ε_Z/(2αg₂)), choose ε_Z well below g₂ for now, and answer **"how long until ⟨b⟩ settles, monotonic or oscillating, and why"**.
You also build `src/linresp.py`, the analytic 2×2 model that **predicts** the answer: ⟨b⟩ rings at 3.14 MHz (Q ≈ 2.5), settles to 1% in ≈1.13 µs, set by κ_b/4 alone. L4c (capstone pulse design: `optimal_pulse`, `response`), L4b (trade-off) and L6 (Lab `readout.json`) import it, so its API is frozen (CONTRACT §9). Finally you verify measurement-induced dephasing, Γ_Z(ε_Z) − Γ_Z(0) = 2ε_Z²/(κ₂α²) (Réglade Eq. S18), which validates the SNR definition SNR(T) = κ_b∫₀ᵀ|Δ⟨b⟩|²dt and shows **the readout cost that matters is Γ_X, not Γ_Z**.

## 2. Read first
- `docs/plan/CONTRACT.md` §3 (model), §5 (analysis), §6 (records, IDs §6.3), §7 (convergence), §9 (linresp, **the spec you implement**), §13 (`readout.json`), §15 (tests).
- `docs/plan/RESEARCH.md` §1 (numbers), §2 (dynamiqs 0.3.7 API), §4.3 (readout symmetry), §6 (Γ_Z), **§7 (everything in this brief)**.
- `docs/challenge_prompt_v4.md` Section 2, Task 2.3. Style models: `tasks/task_1_1.py`, `src/analysis.py` (`settle_time`), `notebooks/02_task_1_1_two_mode.ipynb`.
- Parameters (rad/µs, `src/config.py`): G2 = 4.79411, KAPPA_B = 16.33628, KAPPA_A = 0.0584336, ALPHA = 2.1, EPS_D = α²g₂ = 21.142, KAPPA_2 = 4g₂²/κ_b = 5.6276.

## 3. Allowlist (touch nothing else)
- Code you own: `src/linresp.py`, `tasks/task_2_3.py`, `notebooks/08_task_2_3_readout.ipynb`, `tests/test_l4a_readout.py`.
- Your status file `docs/plan/status/l4a-readout.md` (copy of `_TEMPLATE.md`).
- Production outputs (shared rule, CONTRACT §1): `results/records/t2_3.*.json`, `results/arrays/t2_3.*.npz`, `figures/task_2_3_*.png`.
- Anything else you think must change (e.g. a helper in `src/analysis.py`): write `DECISION NEEDED`, do not edit.

## 4. Interfaces you implement / rely on
**Implement `src/linresp.py` exactly (numpy + scipy only, no dynamiqs import, so L4c/L6 can use it cheaply):**
```python
def system(g2, kappa_b, alpha, well=+1) -> (M, u):
    """x = (δa, b), dx/dt = M x + u ε(t). M = [[0, -2i s g2 α], [-2i s g2 α, -κ_b/2]], u = [-i, 0], s = well ∈ {+1,-1} (else ValueError)."""
def poles(g2, kappa_b, alpha) -> np.ndarray:
    """Roots of λ² + (κ_b/2)λ + 4 g2² α², sorted Im descending. Nominal [-4.0841+19.7166j, -4.0841-19.7166j] /µs."""
def ringing(g2, kappa_b, alpha) -> dict:
    """{'freq_MHz': ω_d/2π, 'decay_per_us': σ = κ_b/4, 'Q': ω0/(2σ) = 4 g2 α/κ_b, 't_settle_5pct_us': ln(20)/σ,
        't_settle_1pct_us': ln(100)/σ, 'omega0': 2 g2 α, 'omega_d': sqrt(ω0² - σ²), 'underdamped': 8 g2 α > κ_b}
    Envelope settling, prefactor ω0/ω_d ignored. freq_MHz = 0.0 if overdamped. Nominal 3.1380, 4.0841, 2.4651, 0.7335, 1.1276."""
def dc_gain(g2, alpha) -> float:      # b_ss/ε for well=+1: -1/(2 g2 α) = -0.049665 µs  (well -1: +)
def response(eps_t, t, g2, kappa_b, alpha, well=+1) -> (da_t, b_t):
    """Zero-order hold: eps_t[k] acts on [t[k], t[k+1]) (last value unused); x(t[0]) = 0; complex arrays of len(t).
    Exact step: x_{k+1} = Φ x_k + (Φ - I) M⁻¹ u ε_k with Φ = scipy.linalg.expm(M Δ_k); cache Φ when the grid is uniform."""
def response_matrices(T, n_bins, n_samples, g2, kappa_b, alpha) -> (R_b, R_a):
    """Bins of width T/n_bins; samples at t_k = (k + 1/2) T/n_samples. R_b (n_samples, n_bins): Δb(t_k) = b(+α) - b(-α) = 2 b₊;
    R_a (n_samples, n_bins): δa of the +α well (identical for both wells). R_b is real-valued, R_a purely imaginary (complex dtype)."""
def optimal_pulse(R_b, R_a=None, energy=1.0) -> (eps_bins, gain):
    """Real eps_bins with sum(eps_bins**2) == energy (DISCRETE norm; ∫ε²dt = energy·T/n_bins, the caller converts).
    R_a None : top eigvec of G = Re(R_bᴴR_b) (= top right singular vector of R_b); gain = σ_max(R_b)² = ||R_b ε||²/||ε||².
    R_a given: top generalized eigvec of (G, Re(R_aᴴR_a) + δI), δ = 1e-9·λ_max(Re(R_aᴴR_a)) (scipy.linalg.eigh(A, B));
               gain = that eigenvalue (signal per unit leakage proxy). Sign fixed so eps_bins.sum() >= 0."""
```
Physics behind it (RESEARCH §7, check the algebra yourself): Heisenberg ȧ = −i(2g₂a†b + ε_Z) − (κ_a/2)a, ḃ = −ig₂a² + iε_d − (κ_b/2)b. Linearize a = s·α + δa: δȧ = −2i s g₂α b − iε_Z, ḃ = −2i s g₂α δa − (κ_b/2)b. Steady state: **b_ss = ∓ε_Z/(2αg₂)** (minus for +α; Réglade S17); **both wells shift by δa_ss = −iε_Z/(2κ₂α²)**. Characteristic λ² + (κ_b/2)λ + 4g₂²α² = 0 ⇒ **λ = −4.08 ± 19.72i /µs**: ringing 3.14 MHz (period 0.32 µs), Q ≈ 2.46, 5% in 0.73 µs, 1% in 1.13 µs. Underdamped iff 8g₂α > κ_b (80.5 > 16.3 rad/µs; Marquet's adiabaticity-breaking criterion). The one-mode (adiabatic) model would relax in 1/(2κ₂α²) ≈ 20 ns. Transfer function H(s) = −2g₂α/(s² + (κ_b/2)s + 4g₂²α²), so b is real and δa imaginary for real ε, and b₋ = −b₊, δa₋ = δa₊.
Useful consequences: Δb = 2Re⟨b⟩₊ **exactly** (symmetry, RESEARCH §4.3); the common baseline ⟨b⟩₀ = iκ_a/(4g₂) = **0.00305i** (Ehrenfest, ε_Z = 0) cancels in Δb; at ε_Z = 0.1g₂, Δb_ss = 0.0476 and SNR(1 µs) ≈ 0.04. Prototype (numpy): at T = 1 µs, 40 bins, the SVD pulse gives **≈4.5×** the square pulse's ||R_bε||² at equal energy.

**Rely on (l0-core, CONTRACT §3–7):** `two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=..., ...)` (eps_z may be a 1-D array: batch axis), `coherent2`, `cat2`, `C.trunc_for(alpha, "steady")` (→ 28×8 at α = 2.1), `C.METHOD`, `analysis.code_basis/code_projector/top_projector/fit_exp_offset/settle_time`, `results.std_params/record/save_arrays/load_record`, `convergence.sweep/converged_at/convergence_block`, `plotting.save(fig, name, quick=)`. Optional (l1): `spectral.low_spectrum(H, jumps, Na, Nb, k=4, sector="full_deflated")`.
**`tasks/task_2_3.py` functions (tests call these):** `signals(Na, Nb, eps_over_g2, *, t_prep=3.0, t_on=3.0, n_t=1501, wells=(+1, -1)) -> dict` (keys `t`, and per well `b`, `a`, `adb`, `leak`, `top_a`, `top_b`, each shape (n_eps, n_t), complex where relevant); `steady_value(t, y, window=(2.5, 3.0))`; `fit_damped_sine(t, y, p0=None) -> dict` (`omega`, `sigma`, `A`, `phi`, `omega_stderr`, `rel_rms_residual`; model y = A e^{−σt}cos(ωt + φ)); `dephasing_traces(Na, Nb, eps_over_g2, *, t_end=6.0, n_t=3001) -> dict` (`t`, `xl`, `yl`, `parity`); `fit_dephasing(t, xl, yl, t0=1.5) -> dict`; `main(part="all", quick=False, na=None, nb=None, conv=True)`.

## 5. Tests to write FIRST (TDD)
`tests/test_l4a_readout.py`. Write all of them, watch them fail, commit, then implement. Use `C.G2, C.KAPPA_B, C.ALPHA, C.KAPPA_A, C.KAPPA_2`.
Fast (pure linear algebra, milliseconds):
1. `test_poles_and_ringing`: `poles()` allclose to `[-4.08+19.72j, -4.08-19.72j]` (rtol 1e-2); exactly `Re λ = -κ_b/4` and `|λ|² = 4g₂²α²` (rtol 1e-12). `ringing()`: freq_MHz 3.14, decay 4.08, Q 2.46, t5 0.73, t1 1.13 (all rtol 1e-2), `underdamped is True`; with `kappa_b = 10*g2*alpha` it returns `underdamped False`, `freq_MHz == 0.0`.
2. `test_dc_gain`: `dc_gain == -1/(2 g2 α)` (rtol 1e-12) and ≈ −0.04966 (rtol 1e-3); a constant ε = 0.1g₂ through `response()` to t = 10 µs gives b_end = ε·dc_gain (rtol 1e-9) and δa_end = −iε/(2κ₂α²) (rtol 1e-9).
3. `test_step_response_analytic`: t = linspace(0, 3, 1501), ε = 0.1g₂ constant; `response()` b vs closed form b_ss[1 − e^{−σt}(cos ω_d t + (σ/ω_d) sin ω_d t)]: max|diff| ≤ 1e-8·|b_ss|. Same on a sorted random non-uniform grid (`default_rng(0)`, 400 points in [0, 3], including 0). well = −1: b₋ = −b₊ and δa₋ = δa₊ (atol 1e-12·|b_ss|). max|Im b| and max|Re δa| ≤ 1e-12·|b_ss|.
4. `test_svd_pulse_beats_square_at_equal_energy`: `R_b, R_a = response_matrices(1.0, 40, 400, ...)`; shapes (400, 40); column j = 17 equals 2× `response()` of a unit bin j sampled at the midpoints (rtol 1e-10); `eps, gain = optimal_pulse(R_b)`: Σeps² = 1 (1e-12), gain = `svd(R_b)[0]**2` = ||R_b eps||² (rtol 1e-10); square = ones(40)/√40: ||R_b eps||²/||R_b sq||² > 2.0; 200 random unit vectors (`default_rng(0)`) all ≤ gain·(1 + 1e-12); `optimal_pulse(R_b, energy=4.0)[0]` = 2·eps (1e-12); with R_a: its ||R_b e||²/||R_a e||² ≥ the same ratio for the square and for the R_a-free eps (to 1e-9).
5. `test_fit_damped_sine`: fit on `response()` b(t) − b_ss (t ∈ [0.05, 2]) recovers ω_d (rtol 1e-4) and σ = κ_b/4 (rtol 1e-3).
Slow (`@pytest.mark.slow`):
6. `test_readout_symmetry`: `signals(14, 5, [0.5], t_prep=0.3, t_on=0.5, n_t=101)`: max over t of |⟨b⟩₋ + conj(⟨b⟩₊)| ≤ 1e-9 and |⟨a⟩₋ + conj(⟨a⟩₊)| ≤ 1e-9 (RESEARCH §4.3; exact at any truncation because P, e^{iπb†b} and K preserve it).
7. `test_S17`: `signals(20, 6, [0.1], t_prep=1.0, t_on=2.5)`, steady over [2.0, 2.5]: Re⟨b⟩₊ within 5% of −0.1/(2α) = −0.02381, Re⟨b⟩₋ within 5% of +0.02381; Im⟨b⟩₊ within 20% of κ_a/(4g₂) = 0.00305.

## 6. Method, step by step
1. Branch `std/l4a-readout`, copy the status template, set status "started". Write tests (§5), commit "tests first".
2. Implement `src/linresp.py` until tests 1–5 pass. Commit. Post in status: "linresp ready" (L4c waits on this).
3. `tasks/task_2_3.py` (first project import: `from src import config as C`, before any array is built). Protocol (RESEARCH §7): **prepare each well first**: `two_mode(..., eps_z=0)` from `coherent2(Na, Nb, ±α)` for t_prep = 3 µs (`tsave=[0, 3]`, use `res.final_state`); **then switch ε_Z on** with a second `mesolve` from that state, `H` batched over ε_Z/g₂ ∈ **{0.05, 0.1, 0.2, 0.5, 1, 2, 3}**, tsave = linspace(0, 3, 1501) (2 ns), `C.METHOD`, `save_states=False`, exp_ops [a⊗I, I⊗b, a†b, code_projector(Na, α)⊗I, top_projector(Na, 2)⊗I, I⊗top_projector(Nb, 1)]. Leakage = 1 − ⟨Π_code⟩. Truncation (Na, Nb) = `C.trunc_for(C.ALPHA, "steady")` = 28×8 (Nb ≥ 8 always).
4. Baseline: run ε = 0 too; ⟨b⟩₀ ≈ 0.00305i (purely imaginary by symmetry). Subtract it from ⟨b⟩ for plots and the Im parts; record values use Re⟨b⟩ (baseline-free).
5. Steady values: `steady_value` over [2.5, 3.0] µs (residual transient e^{−10} ≈ 4e-5). Per ε and well record Re⟨b⟩_ss; store Im⟨b⟩_ss − Im⟨b⟩₀, Im⟨a⟩_ss vs −ε/(2κ₂α²), leakage, symmetry residual, top-level populations, and the Ehrenfest residual |⟨a†b⟩_ss − (−ε/(2g₂) + iκ_a⟨a⟩_ss/(4g₂))|/(ε/(2g₂)) in `numerics`.
6. Linearity: plot |Re⟨b⟩_ss| vs ε against ε/(2αg₂) and the relative deviation. Expected: the well shift δa/α = ε_Z/(2κ₂α³) = 4.6% at ε_Z = g₂ (2.3% at 0.5g₂), and the leading nonlinearity of Re b_ss is O((δa/α)²) ≈ 0.2% at g₂; deviations grow at 2–3 g₂ (large-signal). Report them; gate only ε ≤ g₂.
7. Ringing and settling at the nominal **ε_Z = 0.1g₂** (well below g₂, as the prompt asks): y(t) = Re Δb(t); `fit_damped_sine` on y − y_ss over t ∈ [0.05, 2.0] with p0 from `ringing()` → f = ω/2π, σ. Also fit every ε ≤ g₂ (arrays + notes). Settling: `settle_time(t, y, y_ss, 0.05)` and `0.01`. Compare with linresp **by the same metric** (settle_time on `response()` on the same grid: t5 ≈ 0.682 µs, t1 ≈ 1.132 µs) and the envelope values (0.7335, 1.1276).
8. Dephasing (Réglade S18): start from `cat2(Na, Nb, α, +1)` with ε_Z/g₂ ∈ {0, 0.2, 0.5, 1.0} on from t = 0 (batched), tsave = linspace(0, 6, 3001). X_L = |C₊⟩⟨C₊| − |C₋⟩⟨C₋|, Y_L = i(|C₋⟩⟨C₊| − |C₊⟩⟨C₋|) from `code_basis(Na, α)`, tensored with I_b; also parity. ε_Z rotates the Bloch vector about Z_L at Ω_Z ≈ 4αε_Z (40 rad/µs at g₂), so fit the **magnitude** |z| = √(⟨X_L⟩² + ⟨Y_L⟩²) with `fit_exp_offset` on t ∈ [1.5, 6] → Γ_Z(ε). Checks: at ε = 0 the |z| fit and the parity fit agree to 1% and match 2κ_aα²coth(2α²) = **0.5154 /µs** to 2%. ΔΓ_Z(ε) = Γ_Z(ε) − Γ_Z(0); predictions 2ε²/(κ₂α²) = **0.0741, 0.4630, 1.852 /µs** at 0.2, 0.5, 1 g₂, and the pointer form (κ_b/2)|Δb_ss|² from your measured b_ss (identical in the linear regime). Store the fitted rotation rate vs 4αε_Z (informational). If l1 is merged and 28×8 full-deflated takes < 15 min: eigen cross-check, the X_L/Y_L pair is −Γ_Z ± iΩ_Z.
9. Convergence (CONTRACT §6.2/§7): sweep Na ∈ {20, 24, 28, 32} at Nb = 8 and Nb ∈ {6, 8, 10} at Na = 28, +α well only (the −α values follow by the exact symmetry, verified at 28×8 to 1e-9; say so in `notes`). rel_tol: b_ss 1e-3, ring_freq 1e-3, settle 1e-2, dephasing 1e-2 (Na ∈ {24, 28, 32}, Nb ∈ {6, 8, 10}). Chosen = {Na: 28, Nb: 8}; raise it if `converged` is false.
10. `--quick`: Na×Nb = 16×5, t_prep 1, t_on 1.5, ε ∈ {0.1, 1} g₂, dephasing ε ∈ {0, 0.5} g₂ over 3 µs, no sweeps (`convergence=None`, notes "quick"), `quick=True` everywhere. ≤ 2 min.
11. Time one 28×8 well (prep + batched ε) first; write the wall time in status; extrapolate the full production before launching it.
12. Notebook: thin wrapper like `02_task_1_1_two_mode.ipynb`: markdown with the physics and the explicit answers (§12), a cell `task_2_3.main(part="linresp")` (instant), cells loading records with `load_record` and showing the three figures; full production run as a commented line.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
Records (`record(...)`, `params=std_params(alpha=2.1, eps_z=ε)`, truncation {Na, Nb}, `script="tasks/task_2_3.py"`):

| ID | quantity / units / method | value | cross_check (tol stated) |
|---|---|---|---|
| `t2_3.b_ss.td.two_mode.a2.10.ez{x}g2.well{p\|m}`, x ∈ 0.05, 0.1, 0.2, 0.5, 1, 2, 3 (14 records, e.g. `...ez0.05g2.wellp`, `...ez1g2.wellm`) | `b_ss` / `dimensionless` / `mesolve_switch_on` | Re⟨b⟩_ss | `analytic_S17` ∓ε/(2αg₂), tol 0.05 |
| `t2_3.ring_freq.td.two_mode.a2.10` | `ring_freq` / `MHz` / `damped_sine_fit` (ε = 0.1g₂) | f | `linresp` 3.138, ref `t2_3.ring_freq.linresp.two_mode.a2.10`, tol 0.05 |
| `t2_3.settle_5pct.td.two_mode.a2.10` | `settle_5pct` / `us` | settle_time 5% | `linresp_same_metric` (≈0.682) tol 0.15; `linresp_envelope` 0.7335 tol 0.25 |
| `t2_3.settle_1pct.td.two_mode.a2.10` | `settle_1pct` / `us` | settle_time 1% | `linresp_same_metric` (≈1.132) tol 0.15; `linresp_envelope` 1.1276 tol 0.25 |
| `t2_3.dephasing.td.two_mode.a2.10.ez{x}g2`, x ∈ 0.2, 0.5, 1 | `dephasing` / `1/us` / `coherence_fit` | ΔΓ_Z | `analytic_S18` tol 0.10 (0.25 at 0.2g₂); `pointer_kappa_b_half_db2` (ref the wellp b_ss id) tol 0.10 (0.25 at 0.2g₂) |
| `t2_3.ring_freq.linresp.two_mode.a2.10` | `ring_freq` / `MHz` / `linresp` | 3.1380 | td record, tol 0.05 |

`numerics`: fits carry `fit_window_us`, `gamma_stderr` (or `omega_stderr`), `rel_rms_residual`; b_ss carries `im_b_minus_baseline`, `baseline_im`, `im_a_ss`, `pred_im_a`, `leakage_ss`, `symmetry_residual`, `ehrenfest_residual`, `max_top2_a`, `max_top_b`; dephasing carries `gamma_z_eps`, `gamma_z_0`, `omega_fit`, `omega_pred`. The linresp record: `convergence: null`, `notes` "analytic 2x2 linearization, truncation-independent", `numerics` = full `ringing()` dict + poles (Re, Im) + `dc_gain` (L6 reads `freq_MHz, Q, t_settle_5pct_us, t_settle_1pct_us` for `readout.json`).
Arrays: `results/arrays/t2_3.ring_freq.td.two_mode.a2.10.npz` (`t_us`, `eps_over_g2`, `b_plus`, `b_minus`, `a_plus`, `a_minus`, `leak_plus`, `b_baseline`, `b_lin` = linresp Δb/2 per ε; complex arrays (n_eps, n_t)); `results/arrays/t2_3.dephasing.td.two_mode.a2.10.ez{x}g2.npz` (`t_us`, `xl`, `yl`, `parity`, `z_abs`, plus the ε = 0 trace).
Figures (`plotting.save`): `figures/task_2_3_buffer_signals.png` (Re and Im−baseline of ⟨b⟩± vs t for ε ∈ {0.1, 0.5, 1}g₂ with dashed linresp overlay; panel with Δb/Δb_ss at 0.1g₂, 5%/1% bands and settle markers), `figures/task_2_3_linearity.png` (|Re b_ss| vs ε/g₂ log-log with S17 line, relative deviation, Im⟨a⟩_ss vs −ε/(2κ₂α²), leakage), `figures/task_2_3_dephasing.png` (|z(t)| semilogy per ε; ΔΓ_Z vs ε/g₂ with S18 curve and pointer points).
Quick → `results/quick/`, `figures/quick/` (git-ignored). Production ≤ 15 min: run and commit yourself. Longer: list under "Jobs to queue", e.g. `& $env:DUQ_PY -m tools.runq submit --name t2_3_signals --ram-gb 1 -- $env:DUQ_PY -m tasks.task_2_3 --part signals` (and `--part dephasing`). These are light jobs (< 1 GB).

## 8. Acceptance gates (ALL must pass before DONE)
1. Fast tests 1–5 and slow tests 6–7 pass; the whole `-m "not slow"` suite stays under 2 min.
2. Symmetry residual ≤ 1e-9 at the production truncation (both wells simulated there).
3. S17: |Re⟨b⟩_ss/(∓ε/(2αg₂)) − 1| ≤ 0.05 for every ε ≤ g₂, both wells. Ehrenfest residual ≤ 1e-3.
4. Ring frequency within 5% of 3.138 MHz; fitted σ within 10% of κ_b/4 = 4.084 /µs; settle times within 15% of linresp same-metric values. ⟨b⟩ is **oscillating**, not monotonic (≥ 2 visible overshoots).
5. Dephasing: Γ_Z(0) within 2% of 0.5154; ΔΓ_Z within the §7 tolerances of S18 and of the pointer form.
6. Every td record `convergence.converged == true`; max top-2 memory and top buffer population < 1e-6 at 28×8 (else raise the truncation).
7. All 21 production records exist with `provenance.dirty == false`; 3 figures and 3 arrays files exist; notebook runs top to bottom.
8. `src/linresp.py` imports no dynamiqs; its signatures match CONTRACT §9 character for character.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git switch -c std/l4a-readout standard-track     # skip if the worktree already is on it
Copy-Item docs/plan/status/_TEMPLATE.md docs/plan/status/l4a-readout.md
& $env:DUQ_PY -m pytest tests/test_l4a_readout.py -m "not slow" -q
& $env:DUQ_PY -m pytest tests/test_l4a_readout.py -m slow -q
& $env:DUQ_PY -m tasks.task_2_3 --quick
git status --porcelain -- src tasks tools        # must print nothing before production
& $env:DUQ_PY -m tasks.task_2_3 --part linresp
& $env:DUQ_PY -m tasks.task_2_3 --part signals   # then --part dephasing, then --part figures (re-plots from arrays)
& $env:DUQ_PY -m pytest -m "not slow" -q         # full suite before DONE
```
CLI: `--quick`, `--part {linresp,signals,dephasing,figures,all}`, `--na`, `--nb`, `--no-conv`.

## 10. Out of scope / do not
- No Γ_X(ε_Z), SNR-vs-ε trade-off or pulse shaping (L4b, L4c); no `src/pulses.py`; no Kerr/Stark `extra_H` (L5). No Γ_Z(0) record (L2a owns `t2_2.*`).
- Do not claim the drive "tilts" the double well: by symmetry both flip directions are equal (RESEARCH §4.3, §12).
- Do not use ε(a+a†) to prepare a well from vacuum (impossible, RESEARCH §4.1); prepare from `coherent2`.
- Do not tune tolerances to make a gate pass; do not edit CONTRACT, other lanes' files, `notes/`, `docs/challenge_prompt_v4.md`.
- Do not claim the 2×2 model explains Task 1.1's 56% overshoot: it explains the late ringdown (1.13 vs 1.07 µs), the overshoot is a large-signal effect of the saddle at the origin.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Wording (in the status file, then continue on what is unblocked):
```
DECISION NEEDED (l4a-readout, HH:MM): <one line>. Measured: <numbers, truncation, tolerance>. Options: (a) ... (b) ...
My default if no answer by HH:MM+30: (a).
```
- **l0-core not merged:** finish and commit `src/linresp.py` + tests 1–5 (no dependency); then wait. If `two_mode` lacks `eps_z`, DECISION NEEDED (do not add it yourself).
- **Ring frequency or settling off by > 5% / 15% at a converged truncation:** it is a finding (beyond-linear two-mode physics), not a bug to hide. DECISION NEEDED with both numbers; default: report it with the deviation.
- **S17 > 5% at ε ≤ g₂:** first check the averaging window (extend t_on to 5 µs) and the baseline; then DECISION NEEDED.
- **Symmetry residual > 1e-9 but < 1e-6:** tighten to rtol 1e-10, atol 1e-12 and rerun; > 1e-6 means a sign or operator bug: stop and fix.
- **Dephasing fit unstable at 0.2g₂:** extend t_end to 8 µs; if still bad, drop 0.2 and add 0.75 g₂ (DECISION NEEDED for the ID change).
- **Production > 15 min:** commit code, put the jobs under "Jobs to queue", deliver quick outputs + linresp record by G1.
- **Cut line (if behind at 9:00 PM):** drop ε = 2, 3 g₂ from sweeps, then the Nb = 10 sweep point, then the dephasing at 0.2g₂. **Never cut:** linresp + tests, the symmetry test, S17, ring/settle vs linresp, ΔΓ_Z at ≥ 2 ε values.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE, `docs/plan/status/l4a-readout.md` contains:
- State `DONE`, branch, final commit hash, wall times (quick, one 28×8 well, production).
- The answers: "⟨b⟩ settles to 5% in X µs and to 1% in Y µs (linresp 0.73 / 1.13); it **oscillates** at Z MHz (linresp 3.14, Q ≈ 2.5) because the buffer and the memory displacement form an underdamped 2×2 system (8g₂α = 80.5 > κ_b = 16.3); decay is κ_b/4 alone." Plus the contrast at the chosen ε_Z = 0.1g₂: Δb_ss = …, SNR(1 µs) ≈ ….
- A table of all 21 record IDs with value, cross-check rel_diff, tol, agree, converged; the linearity deviations at 2 and 3 g₂; ΔΓ_Z vs S18 and pointer.
- Gates 1–8 with pass/fail; "linresp API ready for L4c/L4b/L6"; jobs queued (if any); open DECISION NEEDED items; anything surprising.
Explain-back questions (Harshit answers in `docs/defense.md`; do not write answers):
1. Starting from the two-mode Hamiltonian, derive why ⟨b⟩ rings at ≈3.14 MHz instead of relaxing monotonically, why the decay envelope is κ_b/4 independent of g₂, and why the one-mode model gets 20 ns instead.
2. Why are the two wells' buffer signals exactly ⟨b⟩₋ = −⟨b⟩₊*, why does that make Δ⟨b⟩ purely real and the κ_a offset 0.003i irrelevant, and what kind of term would break it?
3. Why does Γ_Z(ε_Z) − Γ_Z(0) = (κ_b/2)|Δ⟨b⟩|² validate SNR = κ_b∫|Δ⟨b⟩|²dt, and if reading out *always* dephases X_L, why is Γ_X, not Γ_Z, the cost that limits how hard you can drive?
