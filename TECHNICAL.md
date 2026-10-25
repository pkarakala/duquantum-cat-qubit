# Technical layer

This file is written for judges, physicists and AI reviewers. Every claim below names the number, the JSON file and key it comes from, the script that produced it, and the check we used. The short human version is [`README.md`](README.md).

## 1. Model and conventions

- Units follow the prompt: ħ = 1, time in µs, rates in rad/µs, ω = 2πf. Every `2π` is applied exactly once, in [`src/config.py`](src/config.py).
- Two-mode model (prompt Section "The model"): H = g₂ a² b† + g₂ a†² b − ε_d (b + b†), jump operators √κ_b b and √κ_a a, with α² = +ε_d/g₂.
- Effective one-mode model: L₂ = √κ₂ (a² − α²) with κ₂ = 4g₂²/κ_b, plus √κ_a a.
- Parameters (Réglade et al., Table S2): g₂/2π = 0.763 MHz, κ_b/2π = 2.6 MHz, κ_a/2π = 9.3 kHz, α = 2.1. Derived values: κ₂ = 5.63 rad/µs (κ₂/2π = 0.896 MHz), ε_d = 21.1 rad/µs, g₂/κ_b = 0.29, ε_d/κ_b = 1.29.
- Numerics: dynamiqs 0.3.7, double precision. Most tasks use `Tsit5(rtol=1e-8, atol=1e-10)` (`src/config.py: METHOD`). Task 1.1 uses `Tsit5(rtol=1e-10, atol=1e-12)` (`INFLATION_METHOD`) following the numerical-tail audit below. Output save times are distinct from internal adaptive steps.
- Chosen truncation: N_a = 32, N_b = 12, chosen from the Task 1.2 study (Section 3).

## 2. Claims table

| # | Claim | Value | Prediction / check | Source (results file → key) | Script |
|---|---|---|---|---|---|
| 1 | 1.0a simulation equals the analytic decay | max abs error 1e-11 | n̄ = 4e^(−κt) | `task_1_0.json → a.max_abs_error_vs_analytic` | `tasks/task_1_0.py` |
| 2 | 1.0b pure two-photon loss plateau | 0.499832 | ½(1 − e^(−8)) = 0.499832, rel. error 1e-14 | `task_1_0.json → b.final_n_sim, b.rel_error` | `tasks/task_1_0.py` |
| 3 | 1.0b final state only in \|0⟩, \|1⟩ | p₀ = 0.50017, p₁ = 0.49983 | parity frozen by pair processes | `task_1_0.json → b.pop_0, b.pop_1` | `tasks/task_1_0.py` |
| 4 | 1.0c settles near α² for all κ₂ | 4.387, 4.404, 4.408 | α² = 4.41, small κ_a shift | `task_1_0.json → c.final_n` | `tasks/task_1_0.py` |
| 5 | 1.0c speed ∝ κ₂ | κ₂·t₉₀ = 0.86, 0.87, 0.90 | exact collapse when κ_a = 0 (τ = κ₂t removes all parameters); residual spread from κ_a and the 5 ns time grid | `task_1_0.json → c.t90_times_kappa2` | `tasks/task_1_0.py` |
| 6 | 1.1 memory overshoots | peak 6.894 at 0.23 µs (1.56 α²) | buffer too slow: ε_d/κ_b = 1.29 violates κ_b ≫ ε_d | `task_1_1.json → peak_na, t_peak_us, overshoot_over_alpha2` | `tasks/task_1_1.py` |
| 7 | 1.1 settles to α² | within 1% after 1.07 µs; steady 4.4026 | nearly empty buffer; semiclassical a² ≈ α², with memory-loss corrections | `task_1_1.json → settle_1pct_us, steady_na` | `tasks/task_1_1.py` |
| 8 | 1.1 buffer transient | peak ⟨n_b⟩ = 1.99 at 0.13 µs | "of order a couple of photons" (prompt) | `task_1_1.json → peak_nb` | `tasks/task_1_1.py` |
| 9 | 1.1 truncation monitors at 32×12 | max top-2 memory 1.4e-5, max top buffer 1.7e-4 | both ≪ 1e-3 at all times | `task_1_1.json → max_top2_a, max_top_b` | `tasks/task_1_1.py` |
| 10 | (24, 6) (start) underestimates the peak | 6.115 (−11.3%) | its buffer top level reaches 4.6% | `task_1_1.json → initial_peak_na, initial_max_top_b` | `tasks/task_1_1.py` |
| 11 | 1.2 steady state vs semiclassics | 4.4026 vs 4.41 (−0.17%) | the small offset persists as cutoffs increase, consistent with the finite-loss model | `task_1_2.json → summary.steady_vs_alpha2_rel` | `tasks/task_1_2.py` |
| 12 | 1.2 steady state is insensitive to truncation | passes 0.1% at N_a = 16 or N_b = 4 in separate sweeps with the other cutoff at its reference value | buffer is nearly empty in steady state | `task_1_2.json → summary.Na_needed_steady, Nb_needed_steady` | `tasks/task_1_2.py` |
| 13 | 1.2 peak needs N_a ≥ 24, N_b ≥ 10 | to 0.5% of the largest run | memory reaches ~6.9 photons; buffer briefly holds ~2 | `task_1_2.json → summary.Na_needed_peak, Nb_needed_peak` | `tasks/task_1_2.py` |
| 14 | 1.3a ⟨a⟩ = 0 at all times | max \|Re⟨a⟩\| = 0 | parity symmetry: no preferred well | `task_1_3a.json → max_abs_re_a` | `tasks/task_1_3a.py` |
| 15 | 1.3a parity decays at 2κ_a n̄ | fit 0.5135 /µs vs 0.5146 predicted (−0.2%) | each lost photon flips parity | `task_1_3a.json → parity_decay_fit_per_us, parity_decay_pred_per_us` | `tasks/task_1_3a.py` |
| 16 | 1.3a it is a superposition, not a mixture | at 1 µs: coherence 0.626 ≈ parity 0.629; purity 0.692 | a well-separated equal mixture has C ≈ 0, purity ≈ 0.5 | `task_1_3a.json → at_1us` | `tasks/task_1_3a.py` |
| 17 | 1.3a parity-decay time | 1.95 µs | 1/(2κ_a α²) = 1.94 µs | `task_1_3a.json → cat_lifetime_us` | `tasks/task_1_3a.py` |
| 18 | 1.3a approaches a mixture by 6 µs | parity 0.05, coherence 0.05, purity 0.501 | expected after ~3 lifetimes | `task_1_3a.json → at_6us` | `tasks/task_1_3a.py` |
| 19 | 1.3a parity-decay fit is robust | 0.5135 / 0.5134 / 0.5132 / 0.5129 for fit windows starting at 0.8 / 1.0 / 2.0 / 3.0 µs; nonlinear fit on y gives 0.5139 | spread ≤ 0.12%; the fitted rate differs from the prediction by 0.2% | `task_1_3a.json → gamma_vs_fit_start_us, gamma_nonlinear_fit_per_us` | `tasks/task_1_3a.py` |
| 20 | Joint state-convergence minimum | (28, 12); max trace distance 0.8481% | 1% state, 0.5% peak, 0.1% steady and boundary thresholds; all larger tested neighbors pass | `task_1_2.json → summary.selected` | `tasks/task_1_2.py` |
| 21 | Chosen cutoff convergence margin | (32, 12); max trace distance 0.3099% | same joint checks, retained for logical-preparation margin | `task_1_2.json → summary.production` | `tasks/task_1_2.py` |

For Task 1.1, “top” means a different Fock level at each cutoff: buffer N_b=6 monitors n_b=5, while N_b=12 monitors n_b=11. Their maximum probabilities are 0.04624 (4.624%) and 0.0001692 (0.01692%), respectively. These are probabilities, not photon counts. A transient mean near two photons can still have several-percent probability at n_b=5. The large value is a valid result of the insufficient 6-level model; its precise value is not a converged physical estimate. A direct same-level check gives max P(n_b=5)=4.83514% at (32,12) and 4.83491% at (40,14), confirming that several-percent occupation of level 5 is genuine. The large occupation is problematic because level 5 is the artificial endpoint when N_b=6. The prompt specifies the monitored populations but does not require fractions or percentages. Percent is presentation formatting, and the 0.1% tolerance is our stated numerical criterion, not a threshold supplied by the prompt.

### Task 1.1: output sampling, integration and numerical tails

The left-panel overshoot and ringdown are **physical**, while the rapid late-time wiggles in the log-scale boundary monitors at the previous tolerances were **numerical**. The prompt explicitly predicts overshoot and ringdown for the full two-mode model. The memory exchanges photon pairs coherently with the buffer before they decay; the supplied rates do not justify an instantaneously relaxing buffer.

We tested output sampling, solver accuracy, fixed integration timesteps and an independent implementation at (N_a,N_b)=(32,12):

| Check | Result |
|---|---|
| Change output spacing from 10 ns to 1 ns, same adaptive tolerances | identical photon numbers at the 301 shared output times |
| Tighten both relative and absolute tolerances by 100× | maximum photon-number change 5.03e-8 |
| Independent QuTiP BDF, rtol=1e-10, atol=1e-12, internal step cap 1 ns | maximum photon-number difference from tight Dynamiqs 2.44e-9 |
| Fixed-step Rouchon3, 1 ns versus 0.5 ns, common window 0–0.8 µs | error against BDF falls from 3.42e-4 to 4.14e-5 photons (8.26×), while ringing persists |
| Signed memory boundary population at the previous tolerance, 2–3 µs | swings from −1.24e-7 to +1.49e-7; negative populations expose numerical error |
| Tight adaptive signed boundary values | numerical fluctuations are far smaller; boundary differences from BDF at shared times are below 1.8e-10 |

The original-tolerance dense-output run took 1,688 accepted adaptive steps across 3 µs, despite saving 3,001 states/expectations. Saving every 10 ns or 1 ns does not set a fixed integration step. Dense sampling refines the peak to **6.90843 photons at 0.235 µs**. The main Task 1.1 and Task 1.2 tables retain their explicitly sampled 10-ns-grid peaks (about 6.894 and 6.897 photons, respectively); that roughly 0.2% sampling difference does not create the ringdown.

For an independent physical sanity check, linearize the mean-field amplitudes near a≈α, b≈0, neglecting the small loss-induced shift. With G=2g₂α, the approximate eigenvalues are

$$\lambda_\pm\simeq-\frac{\kappa_a+\kappa_b}{4}\pm\sqrt{\left(\frac{\kappa_b-\kappa_a}{4}\right)^2-G^2}.$$

Here G=20.14 rad/µs, giving λ≈−4.10±19.72i per µs: an oscillation period of **0.319 µs** and amplitude decay time of **0.244 µs**. Numerically measured peak separations are 0.31–0.32 µs. This estimate explains the physical ringing; it is not an exact solution of the quantum inflation transient.

**Presentation update.** Task 1.1 retains the tighter solver. Its main figure has two panels: photon occupations and full-range top-level probabilities on a linear percentage axis, both over 0–3 µs. No zoom or inset is used. The (24,6) (start) buffer peak is visible at 4.62%; the two monitors at the chosen (32,12) cutoff remain below the chosen 0.1% tolerance throughout inflation. The dotted line marks this tolerance. Legends identify quantities and cutoffs; definitions and interpretation are in the caption. Task 1.2 supplies the separate cutoff-convergence comparisons. The supplementary logarithmic diagnostic retains the unresolved band below 1e-8; its legend sits above the axes to avoid covering the tolerance line or curves. Raw values are not smoothed or individually normalized.

- Figure: `figures/task_1_1_numerical_checks.png`.
- Numerical values and six trajectories: `results/task_1_1_checks.json` and `results/task_1_1_checks.npz`.
- Recompute: `python -m tasks.task_1_1_checks` (the fixed-step checks take several minutes).
- Redraw the recorded audit: `python -m tasks.task_1_1_checks --plot-only`.
- The 1-ns fixed-step run covers 0–3 µs; its half-step counterpart covers 0–0.8 µs to test convergence through the first overshoot and subsequent ringing. The fixed-step error ratio uses only that common interval.

## 3. Convergence study (Task 1.2)

We now simulate **all 36 pairs** with N_a ∈ {16, 20, 24, 28, 32, 40} and N_b ∈ {4, 6, 8, 10, 12, 14}. The largest grid pair **(40, 14)** is the reference. Every run uses the same supplied parameters, vacuum in both modes, solver settings from `src/config.py`, and 301 saved times over 0–3 µs.

### Gradient plots at fixed reference cutoffs

`figures/task_1_2_cutoff_sweeps.png` holds **N_b = 14** and varies every N_a in the left column; it holds **N_a = 40** and varies every N_b in the right column. These are the same grid slices used for the peak and steady-occupation convergence plot. Each varied cutoff has a color from a sequential gradient. Both memory and buffer populations are plotted, with the (40, 14) reference in black dashes. The axes zoom into the first 1.2 µs so the inflation differences are visible; the full 3 µs trajectories remain in the results archive.

Increasing N_a cannot repair an insufficient N_b. Conversely, a large buffer cutoff alone does not guarantee that the memory state is converged. The initial (24, 6) (start) pair underestimates the memory peak by 11.3%.

### Joint state comparison and threshold contours

The metric is **trace distance of the reduced memory density matrices**,

```math
D(t)=\frac12\left\lVert\operatorname{embed}(\rho_a^{(N_a,N_b)}(t))-\rho_a^{(40,14)}(t)\right\rVert_1.
```

The smaller state is embedded into the reference's 40-level Fock basis by adding zero rows and columns. We retain the entire reference rather than projecting and renormalizing it into the smaller space. For each pair, record the largest D(t) over all saved times, including the transient. The trace norm is the sum of absolute eigenvalues of the Hermitian difference. Solver noise is retained, not clipped away.

Trace distance includes off-diagonal coherence and bounds the difference in any memory measurement probability. A 0.01 distance corresponds to at most a one-percentage-point probability difference, up to numerical error. KL divergence of Fock populations would omit coherence, and zeros can make relative entropy singular. See the [trace-distance discussion in this primary reference](https://www.nature.com/articles/s41598-019-50309-7).

`figures/task_1_2_error_grid.png` shows one metric: maximum reduced-memory trace distance, which retains both population and coherence information. The sequential blue color scale is logarithmic in percent, with a display floor of 0.1%. Small circles identify the 36 computed cutoff pairs. The black contour is explicitly labelled **D_max = 1%**; its upper-right side satisfies the state-distance criterion. The black ring marks the chosen cutoff (32,12), used in Tasks 1.1 and 1.3; the star marks reference (40,14), whose self-distance is exactly zero. The minimum passing pair (28,12) is reported in the table, without a second highlighted choice on the map.

For display, use shape-preserving cubic Hermite interpolation (PCHIP) first along N_a, then N_b, on the original probability values. The fine display grid has 481 by 401 coordinates within the sampled domain. The heatmap and contour use this same interpolated field. Interpolation passes through the original values and avoids range overshoot; it supplies a smooth visual guide between integer cutoff samples. All numerical selection checks still use the original computed rows. The peak-error heatmap has been removed; peak and steady convergence remain in their scalar plot and result tables.

The **minimum passing pair is (28, 12)**. Selection requires all of these checks for the candidate and every tested pair with both cutoffs at least as large:

| Check against (40, 14) | Threshold | (28, 12) | Chosen (32, 12) |
|---|---:|---:|---:|
| Maximum memory-state trace distance over saved times | ≤ 1% | 0.848127% | 0.3099% |
| Relative error in peak memory photons | ≤ 0.5% | 0.042743% | 0.0325% |
| Relative error in steady memory photons | ≤ 0.1% | 0.00000151% | < 0.000001% |
| Maximum population in the top two memory levels | ≤ 0.1% | 0.022173% | 0.001362% |
| Maximum population in the top buffer level | ≤ 0.1% | 0.018090% | 0.016921% |

Among candidates passing those checks, minimize the Hilbert-space dimension N_a N_b. Thus (28, 12), dimension 336, is the smallest tested pair satisfying this inflation study. The **chosen cutoff is (32, 12)**, dimension 384, used consistently in Tasks 1.1 and 1.3 with additional convergence margin. The map highlights this chosen cutoff and the reference; (28,12) remains the minimum-passing result in the table.

This is a reference-based, saved-time result for **inflation from vacuum**. It is not a proof of convergence for all times, all initial states or all drives. The finite (40, 14) reference is not an exact solution. Recheck both cutoffs for larger cats, different pulses, or tighter thresholds. In particular, photon-number agreement alone does not certify the quantum state: N_a=24 with N_b=14 has only 0.198% peak error but **2.996% maximum state error**, above the 1% threshold. Even N_a=40 with N_b=10 has **1.156% maximum state error**, despite only 0.328% peak error.

### The prompt's separate-cutoff observable study

The outer edges of the same grid reproduce the original separate sweeps: vary N_a at fixed N_b=14, and vary N_b at fixed N_a=40. Track the final-0.2-µs mean photon number and the transient peak. Their tolerances remain 0.1% and 0.5%, respectively. Full tables are in `results/task_1_2.json`; `figures/task_1_2_convergence.png` retains these observable profiles.

| N_b (N_a = 40) | 4 | 6 | 8 | 10 | 12 | 14 |
|---|---|---|---|---|---|---|
| peak ⟨n_a⟩ | 4.462 | 6.114 | 6.738 | 6.874 | 6.894 | 6.897 |
| max buffer top-level population | 0.19 | 0.046 | 0.0086 | 0.0013 | 1.7e-4 | 1.8e-5 |

| N_a (N_b = 14) | 16 | 20 | 24 | 28 | 32 | 40 |
|---|---|---|---|---|---|---|
| peak ⟨n_a⟩ | 6.363 | 6.793 | 6.883 | 6.895 | 6.897 | 6.897 |
| max memory top-2 population | 0.057 | 0.013 | 0.0020 | 2.5e-4 | 2.3e-5 | 1.3e-7 |

For these two scalar observables, steady photons pass at N_a=16 or N_b=4 in their separate sweeps, while the peak requires N_a≥24 and N_b≥10. These are not joint state-convergence recommendations. The nearly empty steady buffer makes the final photon number insensitive to cutoff; during inflation it briefly holds about two photons with a significant tail. The state comparison also detects coherence lost at an insufficient memory cutoff.

### Results, cache and reproduction

- `results/task_1_2.json`: physical parameters, solver/version/model fingerprint, reference pair, all 36 metrics, the two edge slices, thresholds, the minimum passing pair (`summary.selected`) and chosen-cutoff metrics (`summary.production`).
- `results/task_1_2_trajectories.npz`: save times, both mode populations and boundary monitors for every pair, and their trace-distance time series. It is sufficient to redraw the figures without simulation.
- `results/task_1_2_cache/`: local compressed reduced-memory trajectories, ignored by Git. Cache keys include parameters, time grid, solver settings, Dynamiqs/JAX versions and the model source hash.
- `python -m tasks.task_1_2`: compute the full grid, resuming compatible cached cases.
- `python -m tasks.task_1_2 --plot-only`: redraw from the saved JSON/NPZ.
- `python -m tasks.task_1_2 --rerun`: recompute every case.
- `python -m tasks.task_1_2 --quick`: a separate 3×3 smoke study, with its own files and its own largest-pair reference.
- `python -m unittest discover -s tests -v`: analytic trace-distance and cutoff-selection checks.

## 4. Task 1.3a reasoning

Memory parity P = e^{iπa†a} commutes with a²b†, a†²b, the buffer drive, and the buffer loss. Only √κ_a a changes it. The initial vacuum has P = +1, so without κ_a the memory would stay in the even-parity subspace. In the code space that subspace contains just |C₊⟩. For well-separated coherent states and a parity-diagonal code-space state, the matrix element 2|⟨α|ρ_a|−α⟩| approximately follows the magnitude of parity (0.626 vs 0.629 at 1 µs). Finite coherent-state overlap and transient deformation prevent exact equality. The diagnostics are consistent with a parity-mixed cat state; these numbers alone do not establish the absence of other dephasing. The purity dips to ~0.6 at 0.3 µs while the memory is entangled with the filling buffer, then follows the parity-flip mixture. Fidelity with |C₊⟩ peaks at 0.85 around 0.6 µs. It's limited by the parity already lost during inflation (~0.3 µs at an elevated n̄) and by the residual overshoot deformation.

## 4b. Task 1.3(b, c): preparing |+α⟩

**Why vacuum can't work, and what must break the symmetry.** H and both dissipators are invariant under a → −a: the memory jump changes sign, but its dissipator does not. Vacuum is invariant as a density matrix, so the evolved state remains symmetric between ±α and Re⟨a⟩ = 0 at all times (claim 14). The buffer drive acts only on b, so no buffer-side control can pick a well. We break this symmetry by displacing the memory before stabilization, or by applying a memory drive odd in a. Here β denotes the dimensionless initial coherent-state amplitude (mean photon number |β|²); α = 2.1 is the target amplitude. In method B, ε₁ is the memory-drive amplitude in rad/µs.

All runs: two-mode model, N_a = 32, N_b = 12, `Tsit5(rtol=1e-8, atol=1e-10)`, read at t = 2 µs. Script `tasks/task_1_3b.py`, results `results/task_1_3b.json`, figure `figures/task_1_3b_logical_prep.png`, notebook `notebooks/05_task_1_3b_logical_prep.ipynb`. Claims are labelled B1–B7 so they don't collide with the numbering on other branches.

| # | Claim | Value | Prediction / check | Source (`task_1_3b.json` →) |
|---|---|---|---|---|
| B1 | Method A (start in \|β⟩, β real, then pump) prepares \|+α⟩ | F = 0.978 / 0.9988 / 1.000 / 0.9977 for β = 1.0 / 1.5 / 2.1 / 3.0 | the stabilization selects the positive well; β = α starts at the target amplitude, with small memory-loss corrections | `A1_amplitude[*].F_plus_alpha_2us` |
| B2 | It is fast | F ≥ 0.99 after 0.41 µs (β = 1.5), 0.53 µs (β = 3.0) | comparable to inflation from vacuum (~1 µs) | `A1_amplitude[*].t_F_099_us` |
| B3 | Small β only partly picks a well | β = 0.5: F = 0.84, Re⟨a⟩/α = 0.69 | a weak push leaves weight in the −α basin | `A1_amplitude[1]` |
| B4 | Stabilization forgives a phase error in the pulse | F = 0.9995 / 0.9951 / 0.973 at 15° / 30° / 45° (\|β\| = α); the initial state has fidelity 0.74 / 0.31 / 0.08 | initial-state fidelity ≥ 0.99 requires \|β − α\|² ≤ −ln(0.99) ≈ 0.01005, i.e. phase error ≤ 2.7° at \|β\| = α | `A2_phase[*]`, `phase_window_F099_stabilized_deg` = 30 |
| B5 | Method B (drive i·ε₁(a† − a) for the first 100 ns, from vacuum) also works if strong | ε₁ = 5 / 10 / 20 rad/µs: F = 0.78 / 0.94 / 0.997 | ε₁T is the bare displacement (0.5 / 1 / 2); the drive competes with the inflation, so it is weaker than A at equal β | `B_drive[*]` |
| B6 | The other quadrature ε(a + a†) picks no well | Re⟨a⟩ = 0, F = 0.500 | ε(a + a†) generates D(−iεt), a push along the imaginary axis, at right angles to the wells, so the mirror symmetry Re⟨a⟩ → −Re⟨a⟩ survives (it is the 90° end of B4). Once the cat exists, the same drive is the Zeno Z gate | `control_wrong_quadrature` |
| B7 | Preparation-fidelity cutoff check | every F above agrees between 28×10 and 32×12 to ≤ 3e-4; peak memory top-2 probability 3.11e-5, peak buffer top probability 4.85e-4 | scalar preparation check; the Task 1.2 state-distance bound applies to vacuum inflation | run with `--na 28 --nb 10` |

### Task 1.3(c): what the method costs

- **Hardware.** One resonant memory drive. This adds a control channel or reuses an existing memory-drive line, depending on the device.
- **Calibration.** The pump fixes the wells only up to a sign (α² = ε_d/g₂), so the pulse phase must be locked to half the pump phase. At the tested 30° phase error, F = 0.9951 after stabilization, versus 0.3068 initially; at 45°, F = 0.9727. The tested real amplitudes β = 1.5, 2.1 and 3.0 all give F ≥ 0.99 at 2 µs (B1).
- **Interaction with the stabilization.** A memory drive applied *while* pumping competes with the dissipation. The wrong quadrature is a Z rotation that leaves Re⟨a⟩ = 0 (B6). The right quadrature also deepens the overshoot (peak ⟨n_a⟩ 8.5 for ε₁ = 20, vs 6.9 from vacuum), which needs a larger simulation and, in hardware, more photons in the memory. So the clean recipe is push first, then pump (method A), the order used by Réglade et al.
- **Time and errors.** For β = 1.5, F remains at least 0.99 from 0.41 µs through the 2-µs simulation, and reaches 0.99878 at 2 µs. This clock excludes the idealized initial displacement pulse. Single-photon loss causes amplitude damping of a coherent state; stabilization counteracts that damping. All reported preparations include the finite memory-loss channel.

## 5. AI use

- **Codex** implemented the full cutoff grid, trace-distance comparisons, gradient plots, threshold contours, cached trajectories, and analytic validation tests.
- **Codex** implemented Tasks 2.1 and 2.2, including sparse full-model rate dynamics, independent Dynamiqs checks, cutoff studies, rate fits, figures, notebook walkthroughs and the rate report.
- **Codex** implemented Task 2.3, including both codeword evolutions, drive controls, complex-field settling, independent matched-cutoff BDF validation and the readout report. Numerical results come from integrations, with analytic symmetry and local-response checks.
- **Claude** helped us learn the background, plan the work, and write most of `src/` and `tasks/`. We reviewed every result against a hand prediction (claims 1 to 5, 11, 15, 17) or a convergence test (claims 9, 12, 13).
- **`tools/ai_review.py`** sends the code plus a physics checklist (2π factors, signs, convergence, fits) to an independent model (Gemini or Grok) as a reviewer. Its output goes in `reviews/`, and we note here what we acted on. The reviewer never produces numbers.
- **Gemini review log** (`reviews/gemini-20261024-1632.md`, gemini-3.8-flash, run on the full code plus the prompt and this file):
  - 2π conversions, √rate jump operators, the α² = +ε_d/g₂ sign, the truncation monitors, and the analytic checks: no issues found.
  - Possible challenge 1, "the fit window starts at 1.0 µs, before the 1.07 µs settle time": Gemini *asserted* the effect was < 0.1% without running anything. **We checked it**: moving the start from 0.8 to 3.0 µs changes Γ by at most 0.12% (claim 19).
  - Possible challenge 2, "the coherence normalization": confirmed. For an exact |C₊⟩ the metric is 1 + e^{−2α²}; for the equal incoherent mixture it is 2e^{−2α²}. These finite-overlap corrections are small, but the metric is not exactly zero for a mixture.
  - Possible challenge 3, "a log-linear fit weights small values more": **we added a nonlinear fit on y**, which gives 0.5139 vs 0.5135 (claim 19).
- What we caught ourselves that an AI would easily miss: the default ODE tolerance produced ~1e-4 noise in the truncation monitors, which would have hidden a real truncation problem. We tightened the tolerance and confirmed the results didn't change beyond it.

## 6. File map

| Path | Role |
|---|---|
| `src/config.py` | all parameters, solver settings, chosen truncations |
| `src/model.py` | `one_mode()`, `two_mode()`, `vacuum2()` |
| `src/analysis.py` | partial trace, projectors, cat state, `memory_extras` (parity, fidelity, purity, coherence, Re⟨a⟩ at every time step without storing the full ρ), fits |
| `tasks/task_1_*.py` | task scripts and the optional Task 1.1 numerical audit; write reproducible figures and results |
| `src/rates.py`, `src/rate_solver.py`, `tasks/task_2_common.py` | rate extraction, sparse full-model dynamics and numerical checks for Tasks 2.1/2.2 |
| `src/readout.py`, `tasks/task_2_3.py` | local response, finite-window settling, full readout simulation and numerical validation |
| `notebooks/0*_task_*.ipynb` | one notebook per task: plain-language explanation, the task code, and its outputs |
| `run_all.sh` | introductory tasks and readout; rate commands are listed below |
| `tools/ai_review.py` | optional LLM code review (Gemini or Grok) |

## 7. Reproduce

```bash
pip install -r requirements.txt        # dynamiqs 0.3.7, double precision
python -m src.config                   # units check: kappa_2/2pi = 0.896 MHz
./run_all.sh
python -m tasks.task_2_1
python -m tasks.task_2_2
```
Run times on 4 CPU cores: Task 1.0 ~20 s, 1.1 ~1 min, 1.2 ~12 min, 1.3a ~2 min, 1.3b ~13 min.


## Figure presentation

The maintained task figures use shared sans-serif typography, consistent symbols and units, concise panel labels, and short legends. Definitions, protocol details and interpretation are collected in [figures/CAPTIONS.md](figures/CAPTIONS.md), reproduced beside the corresponding notebook figures. Wigner panels show individual times, complex phase-space axes and a fixed shared color scale. A small cross marks the phase-space origin in every static panel and animation frame. All figures have 300-dpi PNG and PDF exports. The PDF line plots retain vector paths and embedded TrueType fonts; Wigner images remain raster layers.


### Wigner animations

The task scripts export five GIFs alongside the static Wigner panels. Single-photon loss uses all 201 solved states at 5-ns spacing; effective stabilization uses 201 states at 10-ns spacing; two-mode inflation uses all 301 reduced-memory states at 10-ns spacing; interference decay uses the 201 states from 1–6 µs at 25-ns spacing. Task 1.3(b) adds 201 reduced-memory states over 0–2 µs at 10-ns spacing for stabilization from the proposed real displacement $\beta=1.5$. This additional trajectory uses the same tight Tsit5 tolerances as Task 1.1 ($10^{-10}/10^{-12}$); the original preparation sweeps are unchanged.

`python -m tasks.task_1_3b --wigner-only` regenerates the logical-preparation snapshots and GIF without repeating the amplitude and phase sweeps. It saves the reduced states, physical time grid and parameters in `results/task_1_3b_wigner.npz`. The full task command also generates these exports. Notebook 05 displays both static snapshots and the animation at the end of 1.3(b). Time starts after the idealized displacement, rather than including an unsimulated pulse.

`src.plotting.wigner_gif` computes Wigner functions in batches of 16 on a 151×151 spatial grid. Every frame uses actual saved states, fixed axes, the shared normalized range ±2/π, and a fixed 256-color palette. The display clock reports simulated time to 1 ns. Playback is 25 frames/s with 0.8-s endpoint holds; playback speed is a viewing choice. Physical frame times and display durations are embedded in GIF comments for verification. The README embeds GIFs using relative image paths, supported by [GitHub's image renderer](https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files), and links the static snapshots as alternatives.

## Tasks 2.1 and 2.2: rate characterization

[The rate report](docs/task_2_rates.md) defines the observable-rate convention, derives the direct-overlap and finite-cat predictions, and records the amplitude sweeps, fits, cutoff changes, solver comparisons and loss-strength check. The maintained scripts are `tasks/task_2_1.py` and `tasks/task_2_2.py`; `src/rates.py` handles fits and `src/rate_solver.py` integrates the full two-mode generator in a sparse representation. Walkthroughs are notebooks 06 and 07. The introductory results remain unchanged.

## Task 2.3: conditional buffer readout

The [readout report](docs/task_2_3_readout.md) derives the drive convention,
codeword conjugation symmetry, memory-loss common field and local transient.
`tasks/task_2_3.py` adds the real drive $\epsilon_Z(a+a^\dagger)$ to the supplied
full two-mode Hamiltonian. Both coherent codewords are independently evolved
with the buffer in vacuum, both supplied loss channels, $(32,12)$ cutoffs and
Tsit5 tolerances $10^{-10}/10^{-12}$. The nominal drive is $0.05g_2$.

In `results/task_2_3.json`, `drive_summaries` records both complex fields and
the 3–4 µs real separation, **0.02378968**, compared with **0.02380952** from
$\epsilon_Z/(\alpha g_2)$. It also records the **0.968-µs** sustained complex-field
settling time and its [0.966, 0.968] µs sampled bracket, **44.3%** contrast
overshoot and **0.313-µs** ring period. Settling uses 1% of the predicted half
contrast, at every remaining saved time through 4 µs. The positive and negative
branches have opposite real fields and the same imaginary component, as
required by $\beta_-=-\beta_+^*$.

`validation` contains all 15 acceptance results and numerical thresholds.
The full complex fields are checked against separate memory/buffer increases,
a joint $(40,14)$ increase, tighter integration with 1-ns saves, an 8-µs run,
and independent QuTiP BDF at the **same production cutoff**. The latter differs
by at most $1.31\times10^{-7}$ of the predicted half contrast; the extended
plateau differs by $2.44\times10^{-5}$. `state_health` retains the small signed
final eigenvalue residual. The NPZ stores all comparison trajectories and
reference cutoff/version metadata; JSON preserves simulation and analysis
source hashes. Fresh analysis and `--reanalyze` use the same calculation to
refresh the plateau-window metadata, summaries, derived flux and numerical
checks. Comparison references must cover the full required interval, including
0–8 µs for the horizon check; interpolation never extends a reference by
holding its endpoint. `--plot-only` redraws using archived physical parameters.

Tests check the drive quadrature, the full Lindblad generator's antiunitary
symmetry, the local solution against matrix exponentials, last-excursion
settling, zero-drive behavior, incomplete-reference rejection and reanalysis
consistency. The executed [notebook](notebooks/08_task_2_3_readout.ipynb)
loads the saved data by default. Mean-field contrast and settling do not specify
single-shot fidelity, integration time or the drive-induced bit-flip rate.
Those need a measurement model and the separate Task 2.4 trade-off analysis.
