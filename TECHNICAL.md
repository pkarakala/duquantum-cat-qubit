# Technical layer

This file is written for judges, physicists and AI reviewers. Every claim below names the number, the JSON file and key it comes from, the script that produced it, and the check we used. The short human version is [`README.md`](README.md).

## 1. Model and conventions

- Units follow the prompt: ħ = 1, time in µs, rates in rad/µs, ω = 2πf. Every `2π` is applied exactly once, in [`src/config.py`](src/config.py).
- Two-mode model (prompt Section "The model"): H = g₂ a² b† + g₂ a†² b − ε_d (b + b†), jump operators √κ_b b and √κ_a a, with α² = +ε_d/g₂.
- Effective one-mode model: L₂ = √κ₂ (a² − α²) with κ₂ = 4g₂²/κ_b, plus √κ_a a.
- Parameters (Réglade et al., Table S2): g₂/2π = 0.763 MHz, κ_b/2π = 2.6 MHz, κ_a/2π = 9.3 kHz, α = 2.1. Derived values: κ₂ = 5.63 rad/µs (κ₂/2π = 0.896 MHz), ε_d = 21.1 rad/µs, g₂/κ_b = 0.29, ε_d/κ_b = 1.29.
- Numerics: dynamiqs 0.3.7, double precision, `Tsit5(rtol=1e-8, atol=1e-10)`. The default tolerance left ~1e-4 noise in the truncation monitors and biased the steady buffer population, so we tightened it everywhere (`src/config.py: METHOD`).
- Production truncation: N_a = 32, N_b = 12, chosen from the Task 1.2 study (Section 3).

## 2. Claims table

| # | Claim | Value | Prediction / check | Source (results file → key) | Script |
|---|---|---|---|---|---|
| 1 | 1.0a simulation equals the analytic decay | max abs error 1e-11 | n̄ = 4e^(−κt) | `task_1_0.json → a.max_abs_error_vs_analytic` | `tasks/task_1_0.py` |
| 2 | 1.0b pure two-photon loss plateau | 0.499832 | ½(1 − e^(−8)) = 0.499832, rel. error 1e-14 | `task_1_0.json → b.final_n_sim, b.rel_error` | `tasks/task_1_0.py` |
| 3 | 1.0b final state only in \|0⟩, \|1⟩ | p₀ = 0.50017, p₁ = 0.49983 | parity frozen by pair processes | `task_1_0.json → b.pop_0, b.pop_1` | `tasks/task_1_0.py` |
| 4 | 1.0c settles near α² for all κ₂ | 4.387, 4.404, 4.408 | α² = 4.41, small κ_a shift | `task_1_0.json → c.final_n` | `tasks/task_1_0.py` |
| 5 | 1.0c speed ∝ κ₂ | κ₂·t₉₀ = 0.86, 0.87, 0.90 | exact collapse when κ_a = 0 (τ = κ₂t removes all parameters); residual spread from κ_a and the 5 ns time grid | `task_1_0.json → c.t90_times_kappa2` | `tasks/task_1_0.py` |
| 6 | 1.1 memory overshoots | peak 6.894 at 0.23 µs (1.56 α²) | buffer too slow: ε_d/κ_b = 1.29 violates κ_b ≫ ε_d | `task_1_1.json → peak_na, t_peak_us, overshoot_over_alpha2` | `tasks/task_1_1.py` |
| 7 | 1.1 settles to α² | within 1% after 1.07 µs; steady 4.4026 | b = 0 in steady state forces a² = α² | `task_1_1.json → settle_1pct_us, steady_na` | `tasks/task_1_1.py` |
| 8 | 1.1 buffer transient | peak ⟨n_b⟩ = 1.99 at 0.13 µs | "of order a couple of photons" (prompt) | `task_1_1.json → peak_nb` | `tasks/task_1_1.py` |
| 9 | 1.1 truncation monitors at 32×12 | max top-2 memory 1.4e-5, max top buffer 1.7e-4 | both ≪ 1e-3 at all times | `task_1_1.json → max_top2_a, max_top_b` | `tasks/task_1_1.py` |
| 10 | Starter 24×6 underestimates the peak | 6.115 (−11.3%) | its buffer top level reaches 4.6% | `task_1_1.json → starter_peak_na, starter_max_top_b` | `tasks/task_1_1.py` |
| 11 | 1.2 steady state vs semiclassics | 4.4026 vs 4.41 (−0.17%) | agreement to < 1%, so physical, not numerical; the effective model gives 4.404 (−0.14%), so the offset is mostly the κ_a shift both models share | `task_1_2.json → summary.steady_vs_alpha2_rel`, `task_1_0.json → c.final_n[1]` | `tasks/task_1_2.py` |
| 12 | 1.2 steady state is insensitive to truncation | converged (0.1%) at N_a = 16, N_b = 4 | buffer is empty in steady state | `task_1_2.json → summary.Na_needed_steady, Nb_needed_steady` | `tasks/task_1_2.py` |
| 13 | 1.2 peak needs N_a ≥ 24, N_b ≥ 10 | to 0.5% of the largest run | memory reaches ~6.9 photons; buffer briefly holds ~2 | `task_1_2.json → summary.Na_needed_peak, Nb_needed_peak` | `tasks/task_1_2.py` |
| 14 | 1.3a ⟨a⟩ = 0 at all times | max \|Re⟨a⟩\| = 0 | parity symmetry: no preferred well | `task_1_3a.json → max_abs_re_a` | `tasks/task_1_3a.py` |
| 15 | 1.3a parity decays at 2κ_a n̄ | fit 0.5135 /µs vs 0.5146 predicted (−0.2%) | each lost photon flips parity | `task_1_3a.json → parity_decay_fit_per_us, parity_decay_pred_per_us` | `tasks/task_1_3a.py` |
| 16 | 1.3a it is a superposition, not a mixture | at 1 µs: coherence 0.63 = parity 0.63; purity 0.69 | a mixture has coherence 0, purity 0.5 | `task_1_3a.json → at_1us` (coherence here = 2 × `coherence`) | `tasks/task_1_3a.py` |
| 17 | 1.3a cat lifetime | 1.95 µs | 1/(2κ_a α²) = 1.94 µs | `task_1_3a.json → cat_lifetime_us` | `tasks/task_1_3a.py` |
| 18 | 1.3a becomes a mixture by 6 µs | parity 0.05, coherence 0.05, purity 0.501 | expected after ~3 lifetimes | `task_1_3a.json → at_6us` (coherence = 2 × `coherence`) | `tasks/task_1_3a.py` |
| 19 | 1.3a parity-decay fit is robust | 0.5135 / 0.5134 / 0.5132 / 0.5129 for fit windows starting at 0.8 / 1.0 / 2.0 / 3.0 µs; nonlinear fit on y gives 0.5139 | spread ≤ 0.12%, well below the 0.2% gap to the prediction | `task_1_3a.json → gamma_vs_fit_start_us, gamma_nonlinear_fit_per_us` | `tasks/task_1_3a.py` |
| 20 | Full (N_a, N_b) grid: the two truncations don't interact, and 32×12 is converged | peak error vs 48×18: 24×10 → 0.41% (cheapest within 0.5%), 32×12 → 0.035%; steady state within 3e-5 for every N_a ≥ 20 and 4e-6 for every N_a ≥ 24, at any N_b | rows (fixed N_b) and columns (fixed N_a) each saturate at their own error floor, so the one-at-a-time sweep was enough | `task_1_2_grid.json → summary, points` | `tasks/task_1_2_grid.py` on Vultr |

## 3. Convergence study (Task 1.2)

We varied each truncation separately (N_a ∈ {16, 20, 24, 28, 32, 40} at N_b = 14; N_b ∈ {4, 6, 8, 10, 12, 14} at N_a = 40). We tracked two quantities: the steady-state ⟨n_a⟩ (the mean over the last 0.2 µs of a 3 µs run) and the transient peak of ⟨n_a⟩. The tolerances, stated in advance, were 0.1% for the steady state and 0.5% for the peak. Full tables are in `results/task_1_2.json` and `notebooks/03_task_1_2_convergence.ipynb`.

| N_b (N_a = 40) | 4 | 6 | 8 | 10 | 12 | 14 |
|---|---|---|---|---|---|---|
| peak ⟨n_a⟩ | 4.462 | 6.114 | 6.738 | 6.874 | 6.894 | 6.897 |
| max buffer top-level population | 0.19 | 0.046 | 0.0086 | 0.0013 | 1.7e-4 | 1.8e-5 |

| N_a (N_b = 14) | 16 | 20 | 24 | 28 | 32 | 40 |
|---|---|---|---|---|---|---|
| peak ⟨n_a⟩ | 6.363 | 6.793 | 6.883 | 6.895 | 6.897 | 6.897 |
| max memory top-2 population | 0.057 | 0.013 | 0.0020 | 2.5e-4 | 2.3e-5 | 1.3e-7 |

**Answer to the prompt's question.** The steady state and the transient are not equally sensitive. The steady state barely depends on either truncation: the buffer is empty, and the memory sits at α² = 4.4 with a narrow photon distribution. The transient peak depends strongly on **N_b**. The buffer briefly holds ~2 photons with a long tail, and cutting that tail at N_b = 6 removes the photons that drive the overshoot, so the peak comes out 11% low. The memory needs N_a ≳ 24 because the overshoot reaches ~6.9 photons. **The starter N_a = 24 was adequate; the starter N_b = 6 was too small.** One 40×14 run takes ~3 min on 4 CPU cores, which is why `tasks/task_1_2.py` is the job we send to a cloud machine.

**Full grid on a cloud VM (claim 20).** The one-at-a-time sweep assumes the two truncations don't interact. To test that, we ran all 49 combinations of N_a ∈ {16 … 48} and N_b ∈ {4 … 18} on a 16-vCPU Vultr VM (`cloud/vultr_run.py`). The sweep took 17 min of wall time, the whole VM session 19 min, for about $0.14; serially that is ~60 min of compute. The reference is the largest corner, 48×18, where both top-level populations are below 3e-7. Relative error of the peak ⟨n_a⟩ (`figures/task_1_2_grid.png`):

| N_b \ N_a | 16 | 20 | 24 | 28 | 32 | 40 | 48 |
|---|---|---|---|---|---|---|---|
| 6 | 13% | 11% | 11% | 11% | 11% | 11% | 11% |
| 8 | 6.9% | 2.7% | 2.3% | 2.3% | 2.3% | 2.3% | 2.3% |
| 10 | 7.3% | 1.4% | 0.41% | 0.33% | 0.33% | 0.33% | 0.33% |
| 12 | 7.6% | 1.5% | 0.20% | 0.046% | **0.035%** | 0.035% | 0.035% |
| 14 | 7.7% | 1.5% | 0.20% | 0.021% | 0.0039% | 0.0028% | 0.0028% |

Each row flattens at an error set by N_b alone, and each column at an error set by N_a alone. Where both are limiting, the errors roughly add (24×10: 0.41% against 0.33% + 0.20%). So the truncations act independently, and the one-at-a-time sweep above reached the right answer. Our production choice of 32×12 is 0.035% from the reference, ten times inside the 0.5% tolerance. The steady state is converged to 3e-5 for every N_a ≥ 20 and to 4e-6 for every N_a ≥ 24, whatever N_b is, because the buffer is empty in steady state.

## 4. Task 1.3a reasoning

Memory parity P = e^{iπa†a} commutes with a²b†, a†²b, the buffer drive, and the buffer loss. Only √κ_a a changes it. The initial vacuum has P = +1, so without κ_a the memory would stay in the even-parity subspace. In the code space that subspace contains just |C₊⟩. In the code space, the coherence 2|⟨α|ρ_a|−α⟩| equals ⟨P⟩, and the data show this (0.626 vs 0.629 at 1 µs). So the state is the even cat diluted only by parity flips from photon loss, with no extra dephasing. The purity dips to 0.59 at 0.3 µs (`task_1_3a.json → min_purity_inflation`) while the memory is entangled with the filling buffer, then follows the parity-flip mixture. Fidelity with |C₊⟩ peaks at 0.85 around 0.6 µs. It's limited by the parity already lost during inflation (~0.3 µs at an elevated n̄) and by the residual overshoot deformation.

## 4b. Task 1.3(b, c): preparing |+α⟩

**Why vacuum can't work, and what must break the symmetry.** H and both jump operators are unchanged by a → −a, and so is |0⟩, so the evolved state is symmetric between ±α and Re⟨a⟩ = 0 at all times (claim 14). The buffer drive acts only on b, so no buffer-side control can pick a well. The push has to be odd in a and act on the memory: a displaced initial state, or a memory drive.

All runs: two-mode model, N_a = 32, N_b = 12, `Tsit5(rtol=1e-8, atol=1e-10)`, read at t = 2 µs. Script `tasks/task_1_3b.py`, results `results/task_1_3b.json`, figure `figures/task_1_3b_logical_prep.png`, notebook `notebooks/05_task_1_3b_logical_prep.ipynb`. Claims are labelled B1–B7 so they don't collide with the numbering on other branches.

| # | Claim | Value | Prediction / check | Source (`task_1_3b.json` →) |
|---|---|---|---|---|
| B1 | Method A (start in \|β⟩, β real, then pump) prepares \|+α⟩ | F = 0.978 / 0.9988 / 1.000 / 0.9977 for β = 1.0 / 1.5 / 2.1 / 3.0 | the dissipation pulls \|β⟩ into the nearest well; β = α is already a dark state | `A1_amplitude[*].F_plus_alpha_2us` |
| B2 | It is fast | F ≥ 0.99 after 0.41 µs (β = 1.5), 0.53 µs (β = 3.0) | comparable to inflation from vacuum (~1 µs) | `A1_amplitude[*].t_F_099_us` |
| B3 | Small β only partly picks a well | β = 0.5: F = 0.84, Re⟨a⟩/α = 0.69 | a weak push leaves weight in the −α basin | `A1_amplitude[1]` |
| B4 | Stabilization forgives a phase error in the pulse | F = 0.9995 / 0.9951 / 0.973 at 15° / 30° / 45° (\|β\| = α); the pulse alone gives 0.74 / 0.31 / 0.08 | pulse alone needs \|β − α\|² ≤ 0.01, i.e. ≤ 2.7° for F ≥ 0.99 | `A2_phase[*]`, `phase_window_F099_stabilized_deg` = 30 |
| B5 | Method B (drive i·ε₁(a† − a) for the first 100 ns, from vacuum) also works if strong | ε₁ = 5 / 10 / 20 rad/µs: F = 0.78 / 0.94 / 0.997 | ε₁T is the bare displacement (0.5 / 1 / 2); the drive competes with the inflation, so it is weaker than A at equal β | `B_drive[*]` |
| B6 | The other quadrature ε(a + a†) picks no well | Re⟨a⟩ = 0, F = 0.500 | ε(a + a†) generates D(−iεt), a push along the imaginary axis, at right angles to the wells, so the mirror symmetry Re⟨a⟩ → −Re⟨a⟩ survives (it is the 90° end of B4). Once the cat exists, the same drive is the Zeno Z gate | `control_wrong_quadrature` |
| B7 | Converged | every F above agrees between 28×10 and 32×12 to ≤ 3e-4; max memory top-2 population ≤ 3.1e-5, buffer top level ≤ 5e-4 | Task 1.2 rule | run with `--na 28 --nb 10` |
| B8 | Finer grid at 40×14 (cloud batch): the F ≥ 0.99 windows | phase: 0.9998 / 0.9989 / 0.9975 / 0.9951 / 0.9908 / 0.984 at 10 / 20 / 25 / 30 / 35 / 40°, so ±35°; amplitude (real β): 0.978 / 0.994 / 0.9988 / 0.9977 / 0.987 at β = 1.0 / 1.25 / 1.5 / 3.0 / 3.5, so β ≈ 1.25–3.0 | the 8 points shared with the 32×12 table agree to ≤ 2.4e-5 in F; max memory top-2 population 2e-7, buffer top level ≤ 1.6e-5 | `results/task_1_3b_points/*_40x14.json` → `F_plus_alpha_2us` |

**Note on the one-mode research estimate.** An earlier one-mode (effective model) calculation gave F ≥ 0.99 up to a ~45° phase error. The two-mode model is less forgiving: F ≥ 0.99 holds up to 35° but not at 40° (B8, 40×14 grid run on Vultr). We quote the two-mode number.

### Task 1.3(c): what the method costs

- **Hardware.** One resonant drive on the memory. Alice & Bob already need it for the Zeno Z gate, so it is reused rather than added.
- **Calibration.** The pump fixes the wells only up to a sign (α² = ε_d/g₂), so the pulse phase must be locked to half the pump phase. Thanks to the stabilization this lock is loose: ±35° (B8) instead of ±2.7° without it. The amplitude is also loose: anything from β ≈ 1.25 to 3.0 gives F ≥ 0.99; at β = 3.5 it plateaus at 0.987 with Re⟨a⟩/α = 0.974, i.e. about 1.3% of the weight ends in the −α well while the excess photons are pumped out (B8).
- **Interaction with the stabilization.** A memory drive applied *while* pumping competes with the dissipation. The wrong quadrature is a Z rotation that leaves Re⟨a⟩ = 0 (B6). The right quadrature also deepens the overshoot (peak ⟨n_a⟩ 8.5 for ε₁ = 20, vs 6.9 from vacuum), which needs a larger simulation and, in hardware, more photons in the memory. So the clean recipe is push first, then pump (method A), the order used by Réglade et al.
- **Time and errors.** About 0.4–0.5 µs to F ≥ 0.99. During that time single-photon loss still acts, but on a coherent state it only causes a slow phase drift, not a bit flip, so it barely affects F.

## 5. AI use

- **Claude** helped us learn the background, plan the work, and write most of `src/` and `tasks/`. We reviewed every result against a hand prediction (claims 1 to 5, 11, 15, 17) or a convergence test (claims 9, 12, 13).
- **`tools/ai_review.py`** sends the code plus a physics checklist (2π factors, signs, convergence, fits) to an independent model (Gemini or Grok) as a reviewer. Its output goes in `reviews/`, and we note here what we acted on. The reviewer never produces numbers.
- **Gemini review log** ([`reviews/gemini-20261024-1632.md`](reviews/gemini-20261024-1632.md), `gemini-3.8-flash`, run on the full code plus the prompt and this file). It found no issues with the 2π conversions, the √rate jump operators, the α² = +ε_d/g₂ sign, the truncation monitors, or the analytic checks. Gemini *asserts* things without running anything, so we tested each claim it made that can be tested:

  | Gemini said | We checked | Outcome |
  |---|---|---|
  | The fit window starts at 1.0 µs, before the 1.07 µs settle time; the effect is < 0.1% | Moved the window start from 0.8 to 3.0 µs: Γ changes by at most 0.12% (claim 19) | Confirmed; window kept |
  | At 1.0 µs, ⟨n_a⟩ is within 1.5% of steady state | It is 1.0% below | Minor misread; no effect |
  | A log-linear fit weights small values more | Added a nonlinear fit on y: 0.5139 vs 0.5135 /µs (claim 19) | Confirmed negligible |
  | Parity rate 2κ_a⟨nP⟩ ≈ 2κ_a⟨n⟩⟨P⟩ | d⟨P⟩/dt = −2κ_a⟨nP⟩ exactly. The local rate −d ln P/dt drifts from 0.5141 (2 µs) to 0.5112 (6 µs) while 2κ_a⟨n⟩ stays 0.5146 | Explains claim 15's −0.2% residual: it is the ⟨nP⟩ ≈ ⟨n⟩⟨P⟩ step, which worsens as P → 0, not fit noise |
  | Coherence normalization: 2\|⟨α\|ρ\|−α⟩\| = 1 − O(e^(−2α²)) for \|C₊⟩ | ≈ 1 − 1.5e-4, agrees with our derivation | No change |
  | Scope: 1.3(b)/(c) not implemented | True at review time | Done afterwards: Task 1.3b |
- **Figure check and second code review** ([`reviews/claude-figures-20261024-1900.md`](reviews/claude-figures-20261024-1900.md), [`reviews/claude-code-20261024-1900.md`](reviews/claude-code-20261024-1900.md)). The planned Gemini multimodal check (`ai_review.py --figures`) stopped on the free-tier daily quota, so Claude read all 12 figures as images against this table and the results JSON, and re-read `src/` and `tasks/` against the same checklist. No physics or convention errors. It found one wrong bound (claim 20 said 1e-5 at N_a = 20; the grid has 2.9e-5) and one rounded-down bound (B7), both corrected above; we also labelled the doubled coherence in claims 16 and 18, saved the inflation purity dip, made `settle_time` report "never" instead of the run length, and fixed figure labels (Wigner times, one unit in the grid, the solver-noise floor in the 1.1 monitors). Every task was then re-run on a second machine (Apple M2 laptop, ~10 min for 1.0–1.3b): every reported quantity reproduced to ≤ 1e-10 relative, and the solver-noise-level ones (truncation monitors, the 1e-11 error in claim 1) to ≤ 2e-6.
- What we caught ourselves that an AI would easily miss: the default ODE tolerance produced ~1e-4 noise in the truncation monitors, which would have hidden a real truncation problem. We tightened the tolerance and confirmed the results didn't change beyond it.

## 6. File map

| Path | Role |
|---|---|
| `src/config.py` | all parameters, solver settings, chosen truncations |
| `src/model.py` | `one_mode()`, `two_mode()`, `vacuum2()` |
| `src/analysis.py` | partial trace, projectors, cat state, `memory_extras` (parity, fidelity, purity, coherence, Re⟨a⟩ at every time step without storing the full ρ), fits |
| `tasks/task_1_*.py` | one script per task; each writes `figures/*.png` and `results/*.json` |
| `notebooks/0*_task_*.ipynb` | one notebook per task: plain-language explanation, the task code, and its outputs |
| `run_all.sh` | reproduces everything in order |
| `tasks/task_1_2_grid.py` | full (Na, Nb) convergence grid, one process per point |
| `cloud/vultr_sweep.sh` | runs the grid in parallel on a Vultr VM and merges it |
| `cloud/vultr_batch.py` | any job list split across N Vultr VMs, hard dollar and time caps, per-job timings for cost estimates |
| `cloud/setup_vm.sh` | one-time Python setup on a fresh VM |
| `cloud/vultr_run.py` | Vultr API: creates the VM, uploads the code, runs the sweep, downloads results, deletes the VM |
| `docs/tools-log.md` | every external tool and sponsor service used: when, what for, cost, evidence |
| `tools/ai_review.py` | optional LLM code review (Gemini or Grok); `--dry-run` saves the prompt only |

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
