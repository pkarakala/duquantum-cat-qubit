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
| 11 | 1.2 steady state vs semiclassics | 4.4026 vs 4.41 (−0.17%) | agreement to < 1%, so physical, not numerical | `task_1_2.json → summary.steady_vs_alpha2_rel` | `tasks/task_1_2.py` |
| 12 | 1.2 steady state is insensitive to truncation | converged (0.1%) at N_a = 16, N_b = 4 | buffer is empty in steady state | `task_1_2.json → summary.Na_needed_steady, Nb_needed_steady` | `tasks/task_1_2.py` |
| 13 | 1.2 peak needs N_a ≥ 24, N_b ≥ 10 | to 0.5% of the largest run | memory reaches ~6.9 photons; buffer briefly holds ~2 | `task_1_2.json → summary.Na_needed_peak, Nb_needed_peak` | `tasks/task_1_2.py` |
| 14 | 1.3a ⟨a⟩ = 0 at all times | max \|Re⟨a⟩\| = 0 | parity symmetry: no preferred well | `task_1_3a.json → max_abs_re_a` | `tasks/task_1_3a.py` |
| 15 | 1.3a parity decays at 2κ_a n̄ | fit 0.5135 /µs vs 0.5146 predicted (−0.2%) | each lost photon flips parity | `task_1_3a.json → parity_decay_fit_per_us, parity_decay_pred_per_us` | `tasks/task_1_3a.py` |
| 16 | 1.3a it is a superposition, not a mixture | at 1 µs: coherence 0.63 = parity 0.63; purity 0.69 | a mixture has coherence 0, purity 0.5 | `task_1_3a.json → at_1us` | `tasks/task_1_3a.py` |
| 17 | 1.3a cat lifetime | 1.95 µs | 1/(2κ_a α²) = 1.94 µs | `task_1_3a.json → cat_lifetime_us` | `tasks/task_1_3a.py` |
| 18 | 1.3a becomes a mixture by 6 µs | parity 0.05, coherence 0.05, purity 0.501 | expected after ~3 lifetimes | `task_1_3a.json → at_6us` | `tasks/task_1_3a.py` |

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

## 4. Task 1.3a reasoning

Memory parity P = e^{iπa†a} commutes with a²b†, a†²b, the buffer drive, and the buffer loss. Only √κ_a a changes it. The initial vacuum has P = +1, so without κ_a the memory would stay in the even-parity subspace. In the code space that subspace contains just |C₊⟩. In the code space, the coherence 2|⟨α|ρ_a|−α⟩| equals ⟨P⟩, and the data show this (0.626 vs 0.629 at 1 µs). So the state is the even cat diluted only by parity flips from photon loss, with no extra dephasing. The purity dips to ~0.6 at 0.3 µs while the memory is entangled with the filling buffer, then follows the parity-flip mixture. Fidelity with |C₊⟩ peaks at 0.85 around 0.6 µs. It's limited by the parity already lost during inflation (~0.3 µs at an elevated n̄) and by the residual overshoot deformation.

## 5. AI use

- **Claude** helped us learn the background, plan the work, and write most of `src/` and `tasks/`. We reviewed every result against a hand prediction (claims 1 to 5, 11, 15, 17) or a convergence test (claims 9, 12, 13).
- **`tools/ai_review.py`** sends the code plus a physics checklist (2π factors, signs, convergence, fits) to an independent model (Gemini or Grok) as a reviewer. Its output goes in `reviews/`, and we note here what we acted on. The reviewer never produces numbers.
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
| `tools/ai_review.py` | optional LLM code review (Gemini or Grok); `--dry-run` saves the prompt only |

## 7. Reproduce

```bash
pip install -r requirements.txt        # dynamiqs 0.3.7, double precision
python -m src.config                   # units check: kappa_2/2pi = 0.896 MHz
./run_all.sh
```
Run times on 4 CPU cores: Task 1.0 ~20 s, 1.1 ~1 min, 1.2 ~12 min, 1.3a ~2 min.

The full 49-point convergence grid (up to Na=48, Nb=18) is too slow for a laptop, so we run it on a cloud VM:
```bash
./cloud/vultr_sweep.sh                 # results/task_1_2_grid.json, figures/task_1_2_grid.png
```
