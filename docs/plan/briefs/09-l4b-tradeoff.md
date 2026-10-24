# Brief `l4b-tradeoff`: Task 2.4b: readout contrast vs bit-flip trade-off

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l4b-tradeoff`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/09-l4b-tradeoff.md`, then execute this brief exactly. Keep `docs/plan/status/l4b-tradeoff.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l4b-tradeoff` | `std/l4b-tradeoff` from `standard-track` | `l0-core`, `l1-spectral`, `l4a-readout` (`l5-circuit` only for optional step 9) | strongest reasoning model (Opus-class, thinking on) | 2.5 h agent time | Phase 2: lane code + time-domain production merged by **12:30 AM Sun**; eigen grid queued overnight (Phase 3); final curve by **G3 7:00 AM** |

## 1. Goal and why
Challenge Task 2.4b asks: as ε_Z grows, what happens to the readout contrast (Task 2.3) and to Γ_X (Task 2.1)? Is there a trade-off, and where does it come from physically? You produce that answer on the **two-mode** model (memory a ⊗ buffer b): SNR(T), Γ_X(ε_Z), Γ_Z(ε_Z) and leakage on one grid, plus the `t2_4b.grid.npz` table that `l4c-capstone` uses as its cost model. This is a **never-cut** deliverable.

**The physics you must reproduce and must word correctly** (RESEARCH §4.1, §4.3, §7):
- H_Z = ε_Z(a + a†) gives ȧ = −iε_Z, a push along the **imaginary** axis, which is the separatrix. Inside the code space (a + a†) ≈ 2α Z_L, so the drive is a **Z_L rotation** at Ω_Z = 4αε_Z. Confinement (κ₂) makes this **Zeno dynamics**: the in-code rotation is allowed and leakage out of the code is suppressed.
- The antiunitary symmetry U = P·e^{iπb†b}·K maps the well at +α − iδ onto the well at −α − iδ (δ = ε_Z/(2κ₂α²)). So the two one-way flip rates are **equal**, ⟨Z_L⟩_ss = 0 and **there is no "tilt" of the double well**. Parity P maps ε_Z → −ε_Z, so **Γ_X(ε_Z) is even in ε_Z**. Never write "tilt", "bias" or "the drive pushes the state over the barrier".
- The cost comes from the drive **populating out-of-code states**, which escape to the other well much faster (an e^{−2α²} barrier instead of e^{−4α²}).
- Back-action: Γ_Z rises by γ_m = 2ε_Z²/(κ₂α²) (Réglade S18). This is measurement-induced dephasing and cannot be avoided, so **the cost that matters is Γ_X**.
- Derived here, and **to be tested, not assumed**: the steady SNR rate is κ_b|Δb_ss|² = κ_b ε_Z²/(α²g₂²) = 2γ_m, and the Dubovitskii cost is ΔΓ_X = 2γ_m e^{−2α²}. Their ratio is **e^{2α²}** (7.39, 17.8, 50.4 and 6.8e3 at α = 1.0, 1.2, 1.4 and 2.1), independent of ε_Z, g₂ and κ_b (it uses κ₂ = 4g₂²/κ_b). Report whether the two-mode numbers follow it.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (allowlist), §2 (env), §3 (`two_mode`, `coherent2`), §5 (`code_projector`, `z_logical`, `fit_exp_offset`), §6 (records and IDs), §7 (convergence), §8 (spectral), §9 (linresp), §10 (`src.pulses.snr`), §12 (runq), §14 (status), §15 (tests).
- `docs/plan/RESEARCH.md` §1 (parameters), §4.1 to §4.3 (symmetries), §5 (Γ_X convention, anchors), §6 (Γ_Z), §7 (readout, S17/S18, linearization, prep protocol), §9 (deflation, cost model, acceptance).
- `docs/challenge_prompt_v4.md` Section 2, Tasks 2.3 and 2.4(b).
- The merged code and status of your dependencies: `src/spectral.py` (check exactly what `low_spectrum` returns), `src/linresp.py`, `docs/plan/status/l1-spectral.md` (measured costs, `NA_EIG_MAX`), `docs/plan/status/l4a-readout.md`.
- Style to copy: `tasks/task_1_1.py` (short module docstring, `import src.config as C` first, argparse `main`, figures via `src.plotting.save`).

## 3. Allowlist (touch nothing else)
- `tasks/task_2_4b.py` (new), `tests/test_l4b_tradeoff.py` (new), `docs/plan/status/l4b-tradeoff.md` (copy of `_TEMPLATE.md`).
- Production outputs you may add: `results/records/t2_4b.*.json`, `results/arrays/t2_4b.*.npz`, `figures/task_2_4b_*.png`. Quick outputs go to the git-ignored `results/quick/` and `figures/quick/`.
- **Not** `src/**`, other lanes' tasks, notebooks or CONTRACT. If something in `src/` is wrong or missing, write a DECISION NEEDED for its owner lane.

## 4. Interfaces you implement / rely on
**Rely on (frozen, CONTRACT):**
- `src.model.two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None) -> (H, jumps, (a, b))`. Always pass **eps_d = alpha**2 * C.G2** (C.EPS_D is only right for α = 2.1). `eps_z` may be a 1-D array (one batched argument per call). Also `coherent2(Na, Nb, alpha)`.
- `src.spectral.low_spectrum(H, jumps, Na, Nb, k=4, sector='full_deflated')`, `gamma_x(H, jumps, Na, Nb, k=2)`, `liouvillian`, `deflated(L, D, eta=1.0)`, `diagnostics`.
- `src.analysis.code_projector(N, alpha)`, `z_logical(N, alpha)` and `fit_exp_offset(t, y)`. `src.linresp.response(eps_t, t, g2, kappa_b, alpha, well)`.
- `src.convergence.sweep`, `convergence_block`. `src.results.record`, `std_params`, `save_arrays`. `src.plotting.save(fig, name, quick=...)`.
- Constants (rad/µs): G2 = 4.79411, KAPPA_B = 16.33628, KAPPA_A = 0.0584336, KAPPA_2 = 4g₂²/κ_b = 5.6275. `C.METHOD` (Tsit5, rtol 1e-8), `C.METHOD_LONG`, `C.trunc_for(alpha, 'eig')` (gives Na = 18, 20, 22 and 28 for α = 1.0, 1.2, 1.4 and 2.1).

**Implement in `tasks/task_2_4b.py`.** These are module-level so the tests can import them:
```python
ALPHAS = (1.0, 1.2, 1.4); ALPHA_HI = 2.1; TS = (0.5, 1.0, 2.0)
def eps_grid(alpha) -> list[float]       # eps_z/g2: [0.05,0.1,0.2,0.3,0.5,0.7,1,1.5,2,3] for ALPHAS; [0.2,0.5,1.0] at 2.1
def trunc_2_4b(alpha, x) -> tuple[int, int]   # (Na, Nb) from the table in §6 step 3
def rid(quantity, method, alpha, x, T=None, tag=None) -> str  # CONTRACT §6.3 IDs, see §7
def _snr(t, delta_b, kappa_b) -> float   # kappa_b * scipy.integrate.trapezoid(abs(delta_b)**2, t); IDENTICAL to src.pulses.snr
def gamma_m(alpha, eps) -> float         # 2 eps^2 / (KAPPA_2 alpha^2)                 (S18)
def dub_dgx(alpha, eps) -> float         # 2 * gamma_m(alpha, eps) * exp(-2 alpha^2)  (Dubovitskii x2, our convention)
def omega_z(alpha, eps) -> float         # 4 alpha eps
def leak_pred(alpha, eps) -> float       # 1 - exp(-delta^2), delta = eps / (2 KAPPA_2 alpha^2)
def pick_rates(lams, rel_imag=1e-6) -> dict  # {'gamma_x', 'gz_re', 'gz_im'}; rules in §6 step 3
def eig_point(alpha, x, Na, Nb, k=4) -> dict
def td_alpha(alpha, xs, Na, Nb, t_prep=3.0, t_end=2.0, dt=0.002) -> dict
def _steady_state(H, jumps, Na, Nb) -> np.ndarray    # solve deflated(L) vec(rho) = eta vec(I), normalize the trace
```
CLI: `--part {td,tdgx,eig,assemble}`, `--alpha <float>` (eig only), `--tier {1,2}` (eig only), `--quick`, `--force`. The default is `--part td`. `--part eig` writes one record per point **as it finishes** and skips points whose record already exists unless `--force`, so an interrupted queue job resumes.

## 5. Tests to write FIRST (TDD)
`tests/test_l4b_tradeoff.py`, committed before the implementation exists. Use α = 1.0 and Na = 12, Nb = 4 for anything that builds a model.

**Fast (`not slow`, < 20 s total):**
1. `test_snr_helper_matches_formula`: on t = linspace(0, 1, 2001):
   - Δb ≡ 0.3 gives `_snr = KAPPA_B·0.09` (rel 1e-12).
   - Δb = 0.2·exp(19.7i t) gives `KAPPA_B·0.04` (rel 1e-12).
   - Δb = t gives `KAPPA_B/3` (rel 1e-6).
   - If `importlib.util.find_spec("src.pulses")` is not None, `_snr` equals `src.pulses.snr` on random complex data (seed 0, 500 samples) to rel 1e-12.
2. `test_record_ids_match_contract`: the IDs must be exactly these strings.
   - `rid("gamma_x","eig",1.0,0.05) == "t2_4b.gamma_x.eig.two_mode.a1.00.ez0.05g2"`
   - `rid("gamma_z","eig",1.4,1.0) == "t2_4b.gamma_z.eig.two_mode.a1.40.ez1g2"`
   - `rid("snr","td",1.2,1.5,T=0.5) == "t2_4b.snr.td.two_mode.a1.20.ez1.5g2.T0.5us"`
   - `rid("leakage","td",2.1,0.0) == "t2_4b.leakage.td.two_mode.a2.10.ez0g2"`
3. `test_grid_and_truncation`:
   - `eps_grid(1.0)` has 10 values from 0.05 to 3, and `eps_grid(2.1) == [0.2, 0.5, 1.0]`.
   - For every grid point, `trunc_2_4b` gives Nb ≥ 8 and `scipy.stats.poisson.pmf(Nb-1, (x/(2α))**2) < 1e-6`, because the buffer sits at |⟨b⟩_ss| = ε_Z/(2αg₂).
4. `test_pick_rates_synthetic`:
   - lams = [+144.0, −2.3e-3, −0.13+0.96j, −0.13−0.96j, −8.1] gives gamma_x = 2.3e-3, gz_re = 0.13 and gz_im = 0.96. The deflated eigenvalue at +η·D has Re > 0 and must be ignored.
   - With no complex pair, gz_re is None.
5. `test_analytic_helpers`: at α = 1.0 and ε = 0.1·G2:
   - `gamma_m` = 0.08168 (rel 1e-3).
   - `dub_dgx` = 0.02211 (rel 1e-3).
   - `omega_z` = 1.9176 (rel 1e-4).
   - `leak_pred` = 1 − exp(−0.04260²) (rel 1e-6).

**Slow (`@pytest.mark.slow`):**
6. `test_full_deflated_matches_odd_sector_at_zero_drive`: two_mode(12, 4, G2, 1.0·G2, KAPPA_B, KAPPA_A). Then `pick_rates(low_spectrum(..., k=4, sector='full_deflated')['lams'])['gamma_x']` equals `gamma_x(...)['gamma_x']` to rel 1e-6, and lies in (1.5e-3, 3.5e-3); the converged anchor is 2.3007e-3.
7. `test_gamma_x_even_in_eps`: at ε = ±0.3·G2, |Γ_X(+) − Γ_X(−)|/Γ_X(+) < 1e-8, and Γ_X(0.3 G2) > Γ_X(0).
8. `test_no_tilt_without_symmetry_breaking`: at ε = 0.3·G2, the steady state from `_steady_state` has |Tr((z_logical⊗I) ρ_ss)| < 1e-8 and Tr ρ_ss = 1 to 1e-12.
9. `test_td_symmetry_and_offset`: `td_alpha(1.0, [0.2], 12, 4, t_prep=1.0, t_end=0.5)` gives:
   - max|b₋ + conj(b₊)| < 1e-6;
   - Im[(b₊ + b₋)/2] at the switch-on within 25% of κ_a/(4g₂) = 3.047e-3, which is the common offset;
   - the Δb offset cancelling exactly.

## 6. Method, step by step
0. **Start.** Copy `_TEMPLATE.md` to `docs/plan/status/l4b-tradeoff.md` (STARTED). Then:
   - Confirm `src/spectral.py` and `src/linresp.py` are on `standard-track`.
   - Check what `low_spectrum` returns: whether it gives per-eigenvalue diagnostics or eigenvectors.
   - Dry-run `src.results.record(..., quick=True)` with an ID ending in `.T1.0us`. If it raises because of the uppercase `T`, write the DECISION NEEDED in §11; do **not** silently lowercase.
1. **Tests** (§5). Run them and watch them fail on ImportError. Commit `l4b: tests first`.
2. **Pure helpers** (`eps_grid`, `trunc_2_4b`, `rid`, `_snr`, `gamma_m`, `dub_dgx`, `omega_z`, `leak_pred`, `pick_rates`). Fast tests go green.
3. **Eigen point** `eig_point(alpha, x, Na, Nb, k=4)`:
   - Build `two_mode(Na, Nb, C.G2, alpha**2*C.G2, C.KAPPA_B, C.KAPPA_A, eps_z=x*C.G2)` and call `low_spectrum(..., sector='full_deflated', k=k)`. The deflation L + η|1⟩⟩⟨⟨1| moves 0 to +η·D, so σ = 0 is safe (RESEARCH §9).
   - **`pick_rates` rules.** Ignore Re λ ≥ 0.
     - Γ_X is the smallest |λ| among near-real eigenvalues (|Im λ| ≤ rel_imag·|λ|). It is isolated, so it is real; its value is −Re λ.
     - Γ_Z(ε) is the conjugate pair with the smallest |Re λ| among |Im λ| > rel_imag·|λ|. Record gz_re = −Re λ and gz_im = |Im λ|.
     - If there is no pair at k = 4 (expected for ε ≳ 1 g₂, where γ_m and Ω_Z reach the κ₂ and κ_b scale), retry with k = 8.
     - If it is still ambiguous, do not write a Γ_Z record: set NaN and write the note "code-space pair not identifiable: Zeno regime ends". That is itself a finding.
   - **Baselines at x = 0.** Compute all of these:
     - Γ_X(0) from both `full_deflated` and `gamma_x` (odd sector); they must agree to rel 1e-6.
     - Γ_Z(0) = X_L rate = `low_spectrum(sector='even', k=2)['rates'][1]`.
     - Γ_Y(0) = `low_spectrum(sector='odd', k=2)['rates'][1]`.
     - One-mode code-space values: Γ_Z(0) = 2κ_aα²coth(2α²) = 0.1212, 0.1694, 0.2292 and 0.5154 at α = 1.0, 1.2, 1.4 and 2.1; Γ_Y(0) = Γ_Z(0) − Γ_X(0), e.g. 0.1190 at α = 1.0.
   - **S18 comparison.** The Zeno rotation (Ω_Z ≫ Γ_X) averages X_L and Y_L, so compare
     ΔΓ_Z^corr(ε) = gz_re(ε) − ½[Γ_Z(0) + Γ_Y(0)] − ½[Γ_X(ε) − Γ_X(0)]
     against γ_m = 2ε²/(κ₂α²). The last term is the Pauli bookkeeping for extra X_L-type flips, which also decay Y_L. Report both the corrected and the uncorrected ratio. Also report gz_im/Ω_Z; it is expected to be ≈ 1 up to O(e^{−2α²}). That one is a finding, not a gate.
   - **Acceptance per eigenvalue** (CONTRACT §8): rel_residual < 1e-4, edge_weight < 1e-6, cond_est recorded.
     - If edge_weight ≥ 1e-6, rerun once automatically at Nb + 2. If that still fails, write the record with `converged: false` and a note; it cannot be claimed.
     - If `low_spectrum` does not expose per-eigenvalue diagnostics or vectors, use a private `_eigs_full_deflated` built from `liouvillian` + `deflated` + `scipy.sparse.linalg.eigs(sigma=0, k=k)` + `diagnostics`. Its eigenvalues must match `low_spectrum` to rel 1e-10. Also raise a DECISION NEEDED to l1 asking for `return_vecs`.
   - **Truncation table** (starting points). The buffer is displaced to |⟨b⟩| = ε/(2αg₂), which is 1.5 at α = 1, ε = 3g₂, so Nb must grow with ε:

     | α | Na (Na check) | Nb, ε/g₂ ≤ 1 | 1.5 | 2 | 3 |
     |---|---|---|---|---|---|
     | 1.0 | 18 (22) | 8 | 10 | 12 | 14 |
     | 1.2 | 20 (24) | 8 | 10 | 10 | 12 |
     | 1.4 | 22 (26) | 8 | 8 | 10 | 12 |
     | 2.1 | 28 (32) | 8 | – | – | – |

   - **Convergence.**
     - Tier 1: Na and Nb sweeps ({Na, Na+4} and {Nb, Nb+2}) at ε = 0 and at ε = 1 g₂ (α = 2.1: also at ε = 1 g₂).
     - Tier 2: the Na sweep at the largest ε = 3 g₂; Nb is covered by edge_weight and the auto-escalation.
     - rel_tol = 1e-3 for α ≤ 1.4. At α = 2.1 use 1e-2, because Nb 6 → 8 moved Γ_X by 2.6% (RESEARCH §5).
     - Intermediate ε reuse the block of the nearest checked ε at or above them (same α, Na and Nb). Say so in `notes`.
   - **Cost**, from t ≈ 113 s·(Na·Nb²/1792)³ on the full L: 18×8 ≈ 30 s, 22×8 ≈ 55 s, 28×8 ≈ 113 s, 20×12 ≈ 8 min, 18×14 ≈ 14 min, 22×14 ≈ 26 min.
     - **Tier 1** (ε ≤ 1 g₂, all α, with checks) ≈ 70 min CPU. RAM ≤ 2.5 GB per job, so 3 can run in parallel.
     - **Tier 2** (ε ∈ {1.5, 2, 3} g₂ at α ≤ 1.4, with the ε = 3 Na check) ≈ 1.8 h CPU. Use `--ram-gb 6` when Na·Nb² ≥ 3000, so runq runs those one at a time.
     - Only α = 1.0 tier 1 (≈ 10 min) may run inside the lane; everything else goes to **Jobs to queue**.
4. **Time domain** `td_alpha` (SNR and leakage; RESEARCH §7 protocol):
   - **Prepare.** For s = ±1, run `dq.mesolve` from `coherent2(Na, Nb, s*alpha)` for 3 µs with ε_Z = 0 (tsave = [0, 3], `method=C.METHOD`, keep the final state). The prepared states do not depend on ε, so do this once per α and per truncation.
   - **Switch on.** Build H with `eps_z = jnp.asarray(xs)*C.G2` (batched) and evolve each prepared state on t = arange(0, 2.0 + dt/2, 0.002). Use exp_ops [I⊗b, code_projector(Na, α)⊗I] and `save_states=False`.
   - **Δ⟨b⟩.** Δ⟨b⟩(t) = ⟨b⟩₊ − ⟨b⟩₋. The common κ_a offset ≈ +0.003i cancels exactly in Δ. For per-well plots subtract the value at switch-on.
   - **Gates in code:** max|b₋ + b₊*| < 1e-6, and leakage(+) = leakage(−) to 1e-6 absolute.
   - **SNR.** SNR(T) = `_snr(t[t <= T+1e-12], Δb[...], C.KAPPA_B)` for T ∈ {0.5, 1, 2}, and snr_rate = SNR(2) − SNR(1) per µs (settled: the 1% settle time is 1.13 µs).
   - **Leakage** = 1 − mean of Tr(Π_code ρ_a) over t ∈ [1.5, 2] µs, for the + well. The ε = 0 value comes from the end of the prep.
   - **Linear-response cross-check.** `src.linresp.response` with a constant ε gives Δb_lin and SNR_lin.
   - **Two batches per α:** ε ≤ 1 g₂ at Nb = 8, and ε ≥ 1.5 g₂ at the largest Nb from the table.
   - **TD convergence.** Rerun the largest ε of each batch at (Na+4, Nb) and (Na, Nb+2). SNR(T=1) must move < 1e-3 relative and leakage < 1e-2 relative.
   - **Wall time.** Measure it. If production `--part td` exceeds 15 min, split it per α and queue it.
5. **Time-domain Γ_X cross-check** (`--part tdgx`) at α = 1.0, ε ∈ {0.1, 0.3} g₂, Na×Nb = 16×6 with a 20×6 check:
   - Prepare +α as in step 4, switch on, then run `C.METHOD_LONG` with exp_ops [a⊗I], saving every 0.05 µs.
   - Fit `fit_exp_offset` to Re⟨a⟩ on [3 µs, 3 µs + W], with W = min(100, 4/(Γ_X(0) + dub_dgx)) µs.
   - Tolerance against the eigen value: 0.02.
6. **Assemble** (`--part assemble`). Read every `t2_4b.*` record, then build `t2_4b.grid.npz` (§7) with NaN where an eigen record is still pending, write both figures, and print the findings table into the status file:
   - per α: Γ_X(ε)/Γ_X(0);
   - ΔΓ_X/dub_dgx;
   - ΔΓ_Z^corr/γ_m;
   - gz_im/Ω_Z;
   - snr_rate/ΔΓ_X against e^{2α²};
   - (leakage − leakage(0))/leak_pred.

   Assemble must work on a partial grid, so `l4c` can start early.
7. **Production.** Commit the code with a clean `src tasks tools` (provenance.dirty must be false). Then run `--part td`, `--part tdgx` and `--part eig --alpha 1.0 --tier 1`, then `--part assemble`, and commit the outputs. Put every other eigen job in "Jobs to queue".
8. **Parity check at production truncation:** α = 1.2, ε = ±0.5 g₂ at 20×8, equal to rel 1e-8. It becomes a `cross_check` entry on `t2_4b.gamma_x.eig.two_mode.a1.20.ez0.5g2` (method `parity_mirror_eps`, tol 1e-8).
9. *(Optional, cut line 5)* **`extra_H` asymmetry** at α = 1.2, ε ∈ {0.2, 0.5} g₂:
   - Build `extra_H` from the l5 records `t2_4a.kerr_a/kerr_b/chi_ab/stark_a/stark_b.*`, with signs and normalization from `docs/derivation_2_4a.md`. If those are ambiguous, write a DECISION NEEDED.
   - Kerr and Stark terms break the antiunitary U but **not** P. So predict, and test, that Γ_X(+ε) = Γ_X(−ε) **still holds**, while ⟨Z_L⟩_ss ≠ 0 (a real tilt).
   - One-way rates: Γ_{±→∓} = Γ_X(1 ∓ ⟨Z_L⟩_ss)/2.
   - Records use the tag `xh`, e.g. `t2_4b.gamma_x.eig.two_mode.a1.20.ez0.5g2.xh`.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
**Records** (CONTRACT §6.3). `x` is formatted with `{x:.3g}` (`0.05`, `1`, `1.5`, `0` at baseline), α with `{alpha:.2f}`. `params = std_params(alpha=α, eps_z=x*G2)`, plus `T_us` for SNR.
- `t2_4b.gamma_x.eig.two_mode.a{α:.2f}.ez{x}g2`: units `1/us`, method `liouvillian_eig_full_deflated`. `numerics`: rel_residual, edge_weight, cond_est, sector `full_deflated`, sigma 0.0, k. `cross_check`:
  - at ε = 0: odd-sector `gamma_x` (tol 1e-6);
  - at ε ≠ 0: `dubovitskii_overlay` = Γ_X(0) + dub_dgx (tol 0.3; a finding, so it may disagree);
  - `time_domain_fit` (tol 0.02) where step 5 ran;
  - `parity_mirror_eps` (tol 1e-8) at step 8.
- `t2_4b.gamma_z.eig.two_mode.a{α:.2f}.ez{x}g2`: value = gz_re (at ε = 0, the X_L rate). Put `gz_im`, `omega_z` and `dGZ_corr` in `notes` or `numerics`. cross_check `S18_corrected`, value ½[Γ_Z(0) + Γ_Y(0)] + γ_m + ½ΔΓ_X, tol 0.10.
- `t2_4b.snr.td.two_mode.a{α:.2f}.ez{x}g2.T{T:.1f}us`: dimensionless, method `two_mode_mesolve_trapz`, cross_check `linear_response` (SNR_lin, tol 0.10).
- `t2_4b.leakage.td.two_mode.a{α:.2f}.ez{x}g2`: probability, cross_check `analytic_displacement` = leakage(0) + leak_pred (tol 0.2).
- `t2_4b.gamma_x.td.two_mode.a1.00.ez0.1g2` and `.ez0.3g2` (step 5): `numerics` has fit_window_us, gamma_stderr and rel_rms_residual.

**Array** `results/arrays/t2_4b.grid.npz` (`save_arrays("t2_4b.grid", **cols)`). Pass the keys through a dict, since they contain dots. It has one row per (α, ε), ε = 0 rows included: 4 + 33 = **37 rows**, sorted by α and then ε.
- Required keys: `alpha`, `eps_over_g2`, `gamma_x`, `gamma_z_re`, `snr_T0.5`, `snr_T1.0`, `snr_T2.0`, `leakage`.
- Extra keys: `gamma_x_rel`, `gamma_z_im`, `snr_rate`, `gamma_x_ok` (bool: converged and acceptance passed).

**Figures:**
- `figures/task_2_4b_tradeoff.png`:
  - SNR(T = 1 µs) (log y) against Γ_X(ε)/Γ_X(0) (log x), one series per α, with points labelled by ε/g₂.
  - Dashed analytic overlay per α: (1 + dub_dgx/Γ_X(0), SNR_lin(T=1)) over ε ∈ [0.05, 3] g₂.
  - A gray line at SNR = 1. Points where the eigen record is still pending are listed in the caption.
- `figures/task_2_4b_rates_vs_eps.png` (2×2):
  - (a) ΔΓ_X against ε/g₂ (log-log) with the Dubovitskii lines;
  - (b) ΔΓ_Z^corr and the uncorrected value against γ_m (S18);
  - (c) snr_rate/ΔΓ_X against ε with e^{2α²} lines;
  - (d) leakage − leakage(0) against leak_pred.

**Quick** (`--quick`, ≤ 2 min): α = 1.0, x ∈ {0.1, 0.5}, 12×4, t_prep 1 µs, t_end 1 µs, T ∈ {0.5, 1}. It writes to `results/quick/` and `figures/quick/` only.

**Jobs to queue** (copy into the status file; run on `standard-track` after the merge; `<py>` = `D:\duq-venv\Scripts\python.exe`):

| Name | `--ram-gb` | Command | Est. wall |
|---|---|---|---|
| `t2_4b_eig_a1.20_t1` | 2 | `<py> -m tasks.task_2_4b --part eig --alpha 1.2 --tier 1` | 14 min |
| `t2_4b_eig_a1.40_t1` | 2 | `... --alpha 1.4 --tier 1` | 18 min |
| `t2_4b_eig_a2.10_t1` | 2.5 | `... --alpha 2.1 --tier 1` | 28 min |
| `t2_4b_eig_a1.00_t2` / `a1.20_t2` / `a1.40_t2` | 6 | `... --alpha <α> --tier 2` | 48 / 27 / 32 min |
| `t2_4b_assemble` | 1 | `<py> -m tasks.task_2_4b --part assemble` (after all of the above are done) | 1 min |

## 8. Acceptance gates (ALL must pass before DONE)
1. All fast and slow tests in `tests/test_l4b_tradeoff.py` pass, and the full `-m "not slow"` suite stays under 2 min.
2. At every α run, Γ_X(0) from `full_deflated` equals the odd-sector `gamma_x` to **rel 1e-6**. α = 1.0 and 1.4 are within 1% of the anchors 2.3007e-3 and 1.2021e-4 /µs.
3. Evenness: Γ_X(+0.5 g₂) = Γ_X(−0.5 g₂) at α = 1.2 to **rel 1e-8**. No tilt: |⟨Z_L⟩_ss| < 1e-8 without `extra_H`.
4. S18: |ΔΓ_Z^corr/γ_m − 1| ≤ **0.10** for every ε ≤ 0.3 g₂ at α ∈ {1.0, 1.2, 1.4}.
5. Time-domain Γ_X at α = 1.0 (ε = 0.1 and 0.3 g₂) agrees with the eigen value to **0.02**.
6. Time domain: max|b₋ + b₊*| < 1e-6; SNR within 10% of linear response for ε ≤ 0.3 g₂; TD truncation checks pass.
7. Every eigen record has rel_residual < 1e-4 and edge_weight < 1e-6, with `converged: true` (tier-2 failures are flagged false and listed). Every record has ≥ 1 cross_check with a stated tol, and production records have `provenance.dirty == false`.
8. `t2_4b.grid.npz` has the 8 required keys with 37 rows; both figures exist; the status file has the findings table and the queue table.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -m pytest tests/test_l4b_tradeoff.py -m "not slow" -q
& $env:DUQ_PY -m pytest tests/test_l4b_tradeoff.py -m slow -q
& $env:DUQ_PY -m tasks.task_2_4b --quick
git status --porcelain -- src tasks tools        # must be empty before production
& $env:DUQ_PY -m tasks.task_2_4b --part td
& $env:DUQ_PY -m tasks.task_2_4b --part tdgx
& $env:DUQ_PY -m tasks.task_2_4b --part eig --alpha 1.0 --tier 1
& $env:DUQ_PY -m tasks.task_2_4b --part assemble
& $env:DUQ_PY -m pytest -m "not slow" -q
```

## 10. Out of scope / do not
- No pulse shaping, SVD pulses or CLEAR pulses (that is `l4c`). No circuit derivation (`l5`). No thermal photons (n_th = 0 everywhere). No α outside {1.0, 1.2, 1.4, 2.1}.
- Do not edit `src/**`. Do not use `dq.slindbladian` (it is dense). Do not use the Z₂ sectors at ε ≠ 0: the symmetry is broken.
- Do not sweep negative ε except the parity check and the optional step 9.
- Do not loosen a tolerance to pass a gate. Do not run more than 3 heavy jobs, or more than one sparse LU above 3 GB.
- Do not write README or TECHNICAL text, notebooks or Lab data.
- Never describe the cost as a "tilt" or a "bias" of the double well.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Put this in the status file and keep working on whatever is unblocked:
```
### DECISION NEEDED (l4b-tradeoff, <HH:MM EDT>)
Question: <one line>
Evidence: <numbers, record ids, file:line>
Options: A) <...>  B) <...>
Default if no answer by <HH:MM>: <A or B>
```
**Likely blocks:**
- `record()` rejects the `T{T:.1f}us` tag. CONTRACT's §6.3 regex is lowercase-only, but the tag has an uppercase `T`. Ask the integrator to allow `T` in tags; the default is to wait.
- `low_spectrum` gives no vectors or diagnostics. Use the fallback in step 3.
- S18 fails only at α = 1.0. Report both ratios; do not retune.
- The pair cannot be identified at large ε. Use NaN plus the note.
- TD > 15 min. Queue it.
- `src/linresp.py` is not merged. Implement the 2×2 model from CONTRACT §9 privately with `scipy.linalg.expm`, and say so.

**Cut line**, cut in this order if G3 is at risk:
1. Optional step 9 (`extra_H`).
2. Tier 2 eigen points (ε ≥ 1.5 g₂ become TD-only, marked on the figure).
3. α = 1.2 eigen.
4. α = 2.1 eigen.

**Never cut:** tier 1 eigen at α = 1.0 and 1.4, gates 2 to 5, and `t2_4b.grid.npz`.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
**Status file at DONE** must contain:
- State `DONE`, the branch, the last commit hash, and the test counts (fast and slow).
- Records written, counted per family, and the IDs still pending in the queue.
- The gate table with the measured numbers: rel diffs for gates 2 to 6, and the S18 ratios per α.
- The findings table from step 6:
  - Γ_X(ε)/Γ_X(0) at ε = 0.1, 0.3 and 1 g₂;
  - ΔΓ_X/Dubovitskii (agreement or departure, which signals two-mode non-adiabatic physics);
  - snr_rate/ΔΓ_X against e^{2α²};
  - gz_im/Ω_Z;
  - leakage/leak_pred.
- The "Jobs to queue" table, open DECISION NEEDED items, and known limitations (inherited convergence blocks, any `converged: false` points).

**Questions for Harshit (do not answer them here):**
1. The readout drive cannot tilt the double well. So where does the extra bit-flip rate come from, and why does it carry e^{−2α²} rather than the e^{−4α²} of the undriven code-space channel?
2. Γ_Z rises by exactly 2ε_Z²/(κ₂α²). Why is that unavoidable for any readout, and how is it tied to the SNR rate you measured (and to the e^{2α²} figure of merit)?
3. Without the Z₂ split, how did you know which eigenvalue of the deflated Liouvillian is Γ_X, and why should anyone trust the number at ε_Z = 3g₂, where the buffer holds about 2 photons?
