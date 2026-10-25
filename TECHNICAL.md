# Technical layer: Section 1 groundwork

We are judged on the Standard track; its technical layer is [`docs/SECTION2.md`](docs/SECTION2.md). This file covers the Section 1 tasks we ran as the setup check the prompt recommends. It is written for judges, physicists and AI reviewers. Every claim below names the number, the JSON file and key it comes from, the script that produced it, and the check we used. The short human version is [`README.md`](README.md).

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
| 11 | 1.2 steady state vs semiclassics | 4.4026 vs 4.41 (−0.17%) | agreement to < 1%, so physical, not numerical | `task_1_2.json → summary.steady_vs_alpha2_rel` | `tasks/task_1_2.py` |
| 12 | 1.2 steady state is insensitive to truncation | converged (0.1%) at N_a = 16, N_b = 4 | buffer is nearly empty in steady state | `task_1_2.json → summary.Na_needed_steady, Nb_needed_steady` | `tasks/task_1_2.py` |
| 13 | 1.2 peak needs N_a ≥ 24, N_b ≥ 10 | to 0.5% of the largest run | memory reaches ~6.9 photons; buffer briefly holds ~2 | `task_1_2.json → summary.Na_needed_peak, Nb_needed_peak` | `tasks/task_1_2.py` |
| 14 | 1.3a ⟨a⟩ = 0 at all times | max \|Re⟨a⟩\| = 0 | parity symmetry: no preferred well | `task_1_3a.json → max_abs_re_a` | `tasks/task_1_3a.py` |
| 15 | 1.3a parity decays at 2κ_a n̄ | fit 0.5135 /µs vs 0.5146 predicted (−0.2%) | each lost photon flips parity | `task_1_3a.json → parity_decay_fit_per_us, parity_decay_pred_per_us` | `tasks/task_1_3a.py` |
| 16 | 1.3a it is a superposition, not a mixture | at 1 µs: coherence 0.63 = parity 0.63; purity 0.69 | a well-separated equal mixture has C ≈ 0, purity ≈ 0.5 | `task_1_3a.json → at_1us` | `tasks/task_1_3a.py` |
| 17 | 1.3a parity-decay time | 1.95 µs | 1/(2κ_a α²) = 1.94 µs | `task_1_3a.json → cat_lifetime_us` | `tasks/task_1_3a.py` |
| 18 | 1.3a approaches a mixture by 6 µs | parity 0.05, coherence 0.05, purity 0.501 | expected after ~3 lifetimes | `task_1_3a.json → at_6us` | `tasks/task_1_3a.py` |
| 19 | 1.3a parity-decay fit is robust | 0.5135 / 0.5134 / 0.5132 / 0.5129 for fit windows starting at 0.8 / 1.0 / 2.0 / 3.0 µs; nonlinear fit on y gives 0.5139 | spread ≤ 0.12%; the fitted rate differs from the prediction by 0.2% | `task_1_3a.json → gamma_vs_fit_start_us, gamma_nonlinear_fit_per_us` | `tasks/task_1_3a.py` |
| 20 | Joint state-convergence minimum | (28, 12); max trace distance 0.8481% | 1% state, 0.5% peak, 0.1% steady and boundary thresholds; all larger tested neighbors pass | `task_1_2.json → summary.selected` | `tasks/task_1_2.py` |
| 21 | Chosen cutoff convergence margin | (32, 12); max trace distance 0.3099% | same joint checks, retained for logical-preparation margin | `task_1_2.json → summary.production` | `tasks/task_1_2.py` |
| 22 | Full (N_a, N_b) grid: the two truncations don't interact, and 32×12 is converged | peak error vs 48×18: 24×10 → 0.41% (cheapest within 0.5%), 32×12 → 0.035%; steady state within 3e-5 for every N_a ≥ 20 and 4e-6 for every N_a ≥ 24, at any N_b | rows (fixed N_b) and columns (fixed N_a) each saturate at their own error floor, so the one-at-a-time sweep was enough | `task_1_2_grid.json → summary, points` | `tasks/task_1_2_grid.py` on Vultr |

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

$$D(t)=\tfrac12\|\operatorname{embed}(\rho_a^{(N_a,N_b)}(t))-\rho_a^{(40,14)}(t)\|_1.$$

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

**Full grid on a cloud VM (claim 22).** The one-at-a-time sweep assumes the two truncations don't interact. To test that, we ran all 49 combinations of N_a ∈ {16 … 48} and N_b ∈ {4 … 18} on a 16-vCPU Vultr VM (`cloud/vultr_run.py`). The sweep took 17 min of wall time, the whole VM session 19 min, for about $0.14; serially that is ~60 min of compute. The reference is the largest corner, 48×18, where both top-level populations are below 3e-7. Relative error of the peak ⟨n_a⟩ (`figures/task_1_2_grid.png`):

| N_b \ N_a | 16 | 20 | 24 | 28 | 32 | 40 | 48 |
|---|---|---|---|---|---|---|---|
| 6 | 13% | 11% | 11% | 11% | 11% | 11% | 11% |
| 8 | 6.9% | 2.7% | 2.3% | 2.3% | 2.3% | 2.3% | 2.3% |
| 10 | 7.3% | 1.4% | 0.41% | 0.33% | 0.33% | 0.33% | 0.33% |
| 12 | 7.6% | 1.5% | 0.20% | 0.046% | **0.035%** | 0.035% | 0.035% |
| 14 | 7.7% | 1.5% | 0.20% | 0.021% | 0.0039% | 0.0028% | 0.0028% |

Each row flattens at an error set by N_b alone, and each column at an error set by N_a alone. Where both are limiting, the errors roughly add (24×10: 0.41% against 0.33% + 0.20%). So the truncations act independently, and the one-at-a-time sweep above reached the right answer. Our production choice of 32×12 is 0.035% from the reference, ten times inside the 0.5% tolerance. The steady state is converged to 3e-5 for every N_a ≥ 20 and to 4e-6 for every N_a ≥ 24, whatever N_b is, because the buffer is empty in steady state.

## 4. Task 1.3a reasoning

Memory parity P = e^{iπa†a} commutes with a²b†, a†²b, the buffer drive, and the buffer loss. Only √κ_a a changes it. The initial vacuum has P = +1, so without κ_a the memory would stay in the even-parity subspace. In the code space that subspace contains just |C₊⟩. For well-separated coherent states and a parity-diagonal code-space state, the matrix element 2|⟨α|ρ_a|−α⟩| approximately follows the magnitude of parity (0.626 vs 0.629 at 1 µs). Finite coherent-state overlap and transient deformation prevent exact equality. The diagnostics are consistent with a parity-mixed cat state; these numbers alone do not establish the absence of other dephasing. The purity dips to ~0.6 at 0.3 µs while the memory is entangled with the filling buffer, then follows the parity-flip mixture. Fidelity with |C₊⟩ peaks at 0.85 around 0.6 µs. It's limited by the parity already lost during inflation (~0.3 µs at an elevated n̄) and by the residual overshoot deformation.

## 4b. Task 1.3(b, c): preparing |+α⟩

**Why vacuum can't work, and what must break the symmetry.** H and both dissipators are invariant under a → −a: the memory jump changes sign, but its dissipator does not. Vacuum is invariant as a density matrix, so the evolved state remains symmetric between ±α and Re⟨a⟩ = 0 at all times (claim 14). The buffer drive acts only on b, so no buffer-side control can pick a well. The push has to be odd in a and act on the memory: a displaced initial state, or a memory drive.

All runs: two-mode model, N_a = 32, N_b = 12, `Tsit5(rtol=1e-8, atol=1e-10)`, read at t = 2 µs. Script `tasks/task_1_3b.py`, results `results/task_1_3b.json`, figure `figures/task_1_3b_logical_prep.png`, notebook `notebooks/05_task_1_3b_logical_prep.ipynb`. Claims are labelled B1–B7 so they don't collide with the numbering on other branches.

| # | Claim | Value | Prediction / check | Source (`task_1_3b.json` →) |
|---|---|---|---|---|
| B1 | Method A (start in \|β⟩, β real, then pump) prepares \|+α⟩ | F = 0.978 / 0.9988 / 1.000 / 0.9977 for β = 1.0 / 1.5 / 2.1 / 3.0 | the stabilization selects the positive well; β = α starts at the target amplitude, with small memory-loss corrections | `A1_amplitude[*].F_plus_alpha_2us` |
| B2 | It is fast | F ≥ 0.99 after 0.41 µs (β = 1.5), 0.53 µs (β = 3.0) | comparable to inflation from vacuum (~1 µs) | `A1_amplitude[*].t_F_099_us` |
| B3 | Small β only partly picks a well | β = 0.5: F = 0.84, Re⟨a⟩/α = 0.69 | a weak push leaves weight in the −α basin | `A1_amplitude[1]` |
| B4 | Stabilization forgives a phase error in the pulse | F = 0.9995 / 0.9951 / 0.973 at 15° / 30° / 45° (\|β\| = α); the pulse alone gives 0.74 / 0.31 / 0.08 | pulse alone needs \|β − α\|² ≤ 0.01, i.e. ≤ 2.7° for F ≥ 0.99 | `A2_phase[*]`, `phase_window_F099_stabilized_deg` = 30 |
| B5 | Method B (drive i·ε₁(a† − a) for the first 100 ns, from vacuum) also works if strong | ε₁ = 5 / 10 / 20 rad/µs: F = 0.78 / 0.94 / 0.997 | ε₁T is the bare displacement (0.5 / 1 / 2); the drive competes with the inflation, so it is weaker than A at equal β | `B_drive[*]` |
| B6 | The other quadrature ε(a + a†) picks no well | Re⟨a⟩ = 0, F = 0.500 | ε(a + a†) generates D(−iεt), a push along the imaginary axis, at right angles to the wells, so the mirror symmetry Re⟨a⟩ → −Re⟨a⟩ survives (it is the 90° end of B4). Once the cat exists, the same drive is the Zeno Z gate | `control_wrong_quadrature` (it is not inert: a spot check at 20×6 shows it drives parity from 0.63 to 0.03 by 1 µs, the Zeno Z rotation; parity is not stored in this JSON) |
| B7 | Preparation-fidelity cutoff check | every F above agrees between 28×10 and 32×12 to ≤ 3.3e-04; max memory top-2 population ≤ 3.1e-05, buffer top level ≤ 5e-04 | scalar preparation check; the Task 1.2 state-distance bound applies to vacuum inflation | `task_1_3b_28x10.json` vs `task_1_3b.json` |
| B8 | Finer grid at 40×14 (cloud batch): the F ≥ 0.99 windows | phase: 0.9998 / 0.9989 / 0.9975 / 0.9951 / 0.9908 / 0.984 at 10 / 20 / 25 / 30 / 35 / 40°, so ±35°; amplitude (real β): 0.978 / 0.994 / 0.9988 / 0.9977 / 0.987 at β = 1.0 / 1.25 / 1.5 / 3.0 / 3.5, so β ≈ 1.25–3.0 | the 8 points shared with the 32×12 table agree to ≤ 2.4e-5 in F; max memory top-2 population 2e-7, buffer top level ≤ 1.6e-5 | `results/task_1_3b_points/*_40x14.json` → `F_plus_alpha_2us` |

**Why the full model forgives less than the effective one.** The effective one-mode model puts the F = 0.99 edge at 44.8°; the two-mode model on a 5° grid puts it at **35.5°** (`research/explore/phase_gap.py`). The gap is the slow buffer, the same cause as the 1.1 overshoot: raising κ_b at fixed κ₂ moves the edge to 37.0 / 38.3 / 40.2 / 41.4° for κ_b ×2 / 4 / 8 / 16. With κ_b < 8g₂α the exchange is underdamped, the memory swings past the well (to |a| ≈ 1.35α at 45°) and part of the state leaks permanently into the −α basin. Pre-filling the buffer makes it worse, and both models share the Re a = 0 boundary, so neither is the cause. So stabilization widens the phase tolerance about 13× (35° vs 2.7°), not the 16× the effective model suggests. The 40×14 fine grid (B8) confirms the ±35° window.

### Task 1.3(c): what the method costs

- **Hardware.** One resonant memory drive. This adds a control channel or reuses an existing memory-drive line, depending on the device.
- **Calibration.** The pump fixes the wells only up to a sign (α² = ε_d/g₂), so the pulse phase must be locked to half the pump phase. Thanks to the stabilization this lock is loose: ±35° (B8) instead of ±2.7° without it. The amplitude is also loose: anything from β ≈ 1.25 to 3.0 gives F ≥ 0.99; at β = 3.5 it plateaus at 0.987 with Re⟨a⟩/α = 0.974, i.e. about 1.3% of the weight ends in the −α well while the excess photons are pumped out (B8).
- **Interaction with the stabilization.** A memory drive applied *while* pumping competes with the dissipation. The wrong quadrature is a Z rotation that leaves Re⟨a⟩ = 0 (B6). The right quadrature also deepens the overshoot (peak ⟨n_a⟩ 8.5 for ε₁ = 20, vs 6.9 from vacuum), which needs a larger simulation and, in hardware, more photons in the memory. So the clean recipe is push first, then pump (method A), the order used by Réglade et al.
- **Time and errors.** For β = 1.5, F remains at least 0.99 from 0.41 µs through the 2-µs simulation, and reaches 0.99878 at 2 µs. This clock excludes the idealized initial displacement pulse. Single-photon loss causes amplitude damping of a coherent state; stabilization counteracts that damping. All reported preparations include the finite memory-loss channel.

## 5. AI use

- **Codex** implemented the full cutoff grid, trace-distance comparisons, gradient plots, threshold contours, cached trajectories, and analytic validation tests.
- **Claude** helped us learn the background, plan the work, and write most of `src/` and `tasks/`. We reviewed every result against a hand prediction (claims 1 to 5, 11, 15, 17) or a convergence test (claims 9, 12, 13).
- **`tools/ai_review.py`** sends the code plus a physics checklist (2π factors, signs, convergence, fits) to an independent model (Gemini or Grok) as a reviewer. Its output goes in `reviews/`, and we note here what we acted on. The reviewer never produces numbers.
- **Gemini review log** ([`reviews/gemini-20261024-1632.md`](reviews/gemini-20261024-1632.md), `gemini-3.8-flash`, run on the full code plus the prompt and this file). It found no issues with the 2π conversions, the √rate jump operators, the α² = +ε_d/g₂ sign, the truncation monitors, or the analytic checks. Gemini *asserts* things without running anything, so we tested each claim it made that can be tested:

  | Gemini said | We checked | Outcome |
  |---|---|---|
  | The fit window starts at 1.0 µs, before the 1.07 µs settle time; the effect is < 0.1% | Moved the window start from 0.8 to 3.0 µs: Γ changes by at most 0.12% (claim 19) | Confirmed; window kept |
  | At 1.0 µs, ⟨n_a⟩ is within 1.5% of steady state | It is 1.0% below | Minor misread; no effect |
  | A log-linear fit weights small values more | Added a nonlinear fit on y: 0.5139 vs 0.5135 /µs (claim 19) | Confirmed negligible |
  | Parity rate 2κ_a⟨nP⟩ ≈ 2κ_a⟨n⟩⟨P⟩ | d⟨P⟩/dt = −2κ_a⟨nP⟩ exactly. The local rate −d ln P/dt drifts from 0.5141 (2 µs) to 0.5112 (6 µs) while 2κ_a⟨n⟩ stays 0.5146 | Explains claim 15's −0.2% residual: it is the ⟨nP⟩ ≈ ⟨n⟩⟨P⟩ step, which worsens as P → 0, not fit noise |
  | Coherence normalization: 2\|⟨α\|ρ\|−α⟩\| = 1 − O(e^(−2α²)) for \|C₊⟩ | Exactly 1 + e^(−2α²) ≈ 1 + 1.5e-4 for \|C₊⟩, and 2e^(−2α²) ≈ 3e-4 (not 0) for the equal mixture | Sign corrected; finite-overlap corrections are negligible |
  | Scope: 1.3(b)/(c) not implemented | True at review time | Done afterwards: Task 1.3b |
- **Figure check and second code review** ([`reviews/claude-figures-20261024-1900.md`](reviews/claude-figures-20261024-1900.md), [`reviews/claude-code-20261024-1900.md`](reviews/claude-code-20261024-1900.md)). The planned Gemini multimodal check (`ai_review.py --figures`) stopped on the free-tier daily quota, so Claude read all 12 figures as images against this table and the results JSON, and re-read `src/` and `tasks/` against the same checklist. No physics or convention errors. It found one wrong bound (the grid claim, now 22, said 1e-5 at N_a = 20; the grid has 2.9e-5) and one rounded-down bound (B7), both corrected above; we also labelled the doubled coherence in claims 16 and 18, saved the inflation purity dip, made `settle_time` report "never" instead of the run length, and fixed figure labels (Wigner times, one unit in the grid, the solver-noise floor in the 1.1 monitors). Every task was then re-run on a second machine (Apple M2 laptop, ~10 min for 1.0–1.3b): every reported quantity reproduced to ≤ 1e-10 relative, and the solver-noise-level ones (truncation monitors, the 1e-11 error in claim 1) to ≤ 2e-6.
- **Section 2.** Claude wrote most of `research/s2/` and `src/spectral.py` and drafted `docs/SECTION2.md` from our direction. Every rate there is computed two independent ways (Liouvillian eigenvalue and time-domain fit), every headline number at two or more truncations and, for time-domain runs, two solver tolerances. A final pass checked each number in the write-up against its JSON; it corrected a pulse-table row that mixed two drive amplitudes, the γ fit range, and the precision quoted for the time-domain agreement.
- What we caught ourselves that an AI would easily miss: the default ODE tolerance produced ~1e-4 noise in the truncation monitors, which would have hidden a real truncation problem. We tightened the tolerance and confirmed the results didn't change beyond it.

## 6. File map

| Path | Role |
|---|---|
| `src/config.py` | all parameters, solver settings, chosen truncations |
| `src/model.py` | `one_mode()`, `two_mode()`, `vacuum2()` |
| `src/analysis.py` | partial trace, projectors, cat state, `memory_extras` (parity, fidelity, purity, coherence, Re⟨a⟩ at every time step without storing the full ρ), fits |
| `tasks/task_1_*.py` | task scripts and the optional Task 1.1 numerical audit; write reproducible figures and results |
| `notebooks/0*_task_*.ipynb` | one notebook per task: plain-language explanation, the task code, and its outputs |
| `run_all.sh` | reproduces everything in order |
| `tasks/task_1_2_grid.py` | full (Na, Nb) convergence grid, one process per point |
| `cloud/vultr_sweep.sh` | runs the grid in parallel on a Vultr VM and merges it |
| `cloud/vultr_batch.py` | any job list split across N Vultr VMs, hard dollar and time caps, per-job timings for cost estimates |
| `cloud/setup_vm.sh` | one-time Python setup on a fresh VM |
| `cloud/vultr_run.py` | Vultr API: creates the VM, uploads the code, runs the sweep, downloads results, deletes the VM |
| `docs/tools-log.md` | every external tool and sponsor service used: when, what for, cost, evidence |
| `tools/ai_review.py` | optional LLM code review (Gemini or Grok); `--dry-run` saves the prompt only |
| `src/spectral.py` | Section 2: sparse Liouvillian, parity sectors, shift-invert eigensolver |
| `research/s2/*.py` | Section 2 scripts, one JSON per run in `results/s2/` (prefixes in `results/s2/README.md`) |
| `research/s2/summarize.py` | rebuilds `results/s2/SUMMARY.md` and `figures/s2/` from the saved JSON, in seconds |
| `tasks/task_2_2.py` | Γ_Z from the time-domain parity decay of \|C₊⟩, the cross-check of the eigenvalue result |
| `cloud/s2_batch*.txt` | the Section 2 job lists run on Vultr |

## 7. Reproduce

```bash
pip install -r requirements.txt        # dynamiqs 0.3.7, double precision
python -m src.config                   # units check: kappa_2/2pi = 0.896 MHz
./run_all.sh
```
Run times on 4 CPU cores: Task 1.0 ~20 s, 1.1 ~1 min, 1.2 ~12 min, 1.3a ~2 min, 1.3b ~13 min.

The full 49-point convergence grid (up to Na=48, Nb=18) is too slow for a laptop, so we run it on a cloud VM:
```bash
python cloud/vultr_run.py --plan <id>  # VULTR_API_KEY set; VM is deleted at the end
# or, on a VM you created yourself:  ./cloud/vultr_sweep.sh
```

## Figure presentation

The 15 maintained task figures use shared sans-serif typography, consistent symbols and units, concise panel labels, and short legends. Definitions, protocol details and interpretation are collected in [figures/CAPTIONS.md](figures/CAPTIONS.md), reproduced beside the corresponding notebook figures. Wigner panels show individual times, complex phase-space axes and a fixed shared color scale. All figures have 300-dpi PNG and PDF exports. The PDF line plots retain vector paths and embedded TrueType fonts; Wigner images remain raster layers.
