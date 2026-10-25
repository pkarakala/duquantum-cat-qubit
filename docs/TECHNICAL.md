# Technical details

Methods, headline numbers and checks. Each task's notebook in [`notebooks/`](../notebooks/) has the figures and full captions. Every number is in a JSON under `results/`.

**Model.** Exactly as in the prompt. Two-mode H = g₂(a²b† + a†²b) − ε_d(b + b†), jumps √κ_b b and √κ_a a, α² = ε_d/g₂. Parameters: g₂/2π = 0.763 MHz, κ_b/2π = 2.6 MHz, κ_a/2π = 9.3 kHz, α = 2.1. Units: ħ = 1, µs, rad/µs, with every 2π applied once in `src/config.py`. Numerics: dynamiqs 0.3.7, float64, Tsit5 with rtol 1e-8 to 1e-11.

## Section 2 (standard track)

**Two methods.** Brute force first: `tasks/task_2_1.py` and `tasks/task_2_2.py` integrate the full model in the time domain and fit the decay (details in [`task_2_rates.md`](task_2_rates.md)). But a time domain run must last about 1/Γ to see a decay, and at α = 2.1 a bit flip takes seconds. So we also use the fact that every decay rate is a Liouvillian eigenvalue. The model is symmetric under a → −a, so the Liouvillian splits into an even block, whose slowest nonzero eigenvalue is Γ_Z, and an odd block, whose slowest eigenvalue is Γ_X. A sparse shift-invert solve (`src/spectral.py`) gives Γ_X at α = 2.1 in under a minute. Where brute force still reaches (α ≤ 1.4 for Γ_X, all α for Γ_Z), the two methods agree: to 1e-8 for Γ_X at equal truncation, and to five digits for Γ_Z.

### 2.1 Bit flips (`tasks/task_2_1.py`, `research/s2/gx_eig.py`)

| α | 1.0 | 1.4 | 1.8 | 2.1 | 2.4 |
|---|---|---|---|---|---|
| Γ_X (1/µs) | 2.30e-3 | 1.20e-4 | 4.07e-6 | 3.85e-7 | 3.12e-8 |
| time per flip | 0.43 ms | 8.3 ms | 0.25 s | 2.6 s | 32 s |

- Two escape routes. Direct: Γ ≈ 2κ_aα²e^{−4α²}. Out of the code space and back: Γ ≈ (κ_a²/κ₂)e^{−2α²}.
- Proof: sweeping κ_a gives a slope d lnΓ_X/d lnκ_a of 1.06, 1.28, 1.78, 2.00 and 2.05 at α = 1.0, 1.4, 1.8, 2.1 and 2.4. That is the handover from one photon loss to two.
- The full model flips 3.3× faster than the one-mode model at α = 2.1, because the buffer is slow.
- Thermal photons with n_th = 0.01 multiply Γ_X by 3.8.
- Converged to < 1.5% up to α = 2.4. At α = 2.6 truncations disagree by 20%, so the curve stops at 2.5.

### 2.2 Phase flips

- Γ_Z = 0.514559 per µs at α = 2.1 from both the parity-decay fit (`tasks/task_2_2.py`) and the eigenvalue.
- It sits 0.1–0.5% below 2κ_aα² coth 2α², because photon loss leaves the cat about 0.007 photons short of α². With the simulated photon number n̄, 2κ_a n̄ coth 2n̄ matches to 3e-4 for α ≥ 1.5.
- Bias at α = 2.1: Γ_Z/Γ_X = 1.3×10⁶.

### 2.3 Readout (`tasks/task_2_3.py`; drive sweep `research/s2/readout.py`)

- Contrast: Re⟨b⟩ = ∓ε_Z/(2αg₂). At ε_Z = 0.05 g₂ two independent codes give 0.9992 of it, agreeing to 3e-6.
- Linear to 1% up to ε_Z ≈ 0.6 g₂ at α = 2.1 (0.05 g₂ at α = 1.4, 1.1 g₂ at α = 2.4). Stronger drives flip the qubit, and the contrast collapses.
- The signal rings (period 0.313 µs, Q ≈ 2) and stays within 1% from 0.97 µs. Memory and buffer form a damped oscillator at 2g₂α, underdamped because κ_b < 8g₂α; it predicts 0.319 µs and Q 2.5. This is the same physics as the Task 1.1 overshoot.
- Checks: QuTiP BDF, tighter tolerances, truncations up to 40×14 and an 8 µs run all agree to 2e-5 of the signal or better.

### 2.4 Better readout

- **Circuit** (`rwa_terms.py`, `circuit_sim.py`):
  - Only the a²b† family is resonant, which needs ε_p = 0.037.
  - In the full ATS circuit without the RWA, the pump at its nominal frequency fails to pair photons, because Stark shifts detune it.
  - Retuning the pump by −23 MHz restores pairing, about 15% slower than the RWA model: the photon number mismatch drops from 0.43 to 0.07.
  - Converged at 12×5 and 14×6. 150 ns, no loss.
- **Trade-off:** SNR and P_flip both scale as ε_Z², so each pulse shape has an optimal strength and only the shape changes SNR per flip. The flip coefficient falls as e^{−2.03α²}.
- **Pulses** (`pulse_eval.py`). Readout error ε_ro = ½erfc(√(η SNR/2)) + P_flip, at α = 2.1 in a 2 µs window:

| pulse (best peak) | SNR | P_flip | ε_ro (η = 1) | ε_ro (η = 0.5) |
|---|---|---|---|---|
| square, 1.0 g₂ | 7.5 | 8.1e-3 | 1.12% | 3.48% |
| sgn(cos ω_r t), 0.75 g₂ | 12.8 | 9.2e-3 | 0.94% | 1.49% |
| cos ω_r t, 0.75 g₂ | 8.2 | 4.4e-3 | **0.65%** | 1.50% |

- Why the resonant drive wins: it drives the 3.2 MHz oscillator in step, so the buffer amplifies it. Smoothing the pulse edges alone gains only 8–14%.
- **Optimizer** (`pulse_opt.py`, jax.grad through dynamiqs, started from sgn(cos ω_r t), objective SNR − μ P_flip). It beats a square pulse by 1.26–1.71× in SNR per flip in all 9 converged settings (α 1.4 to 2.1, T 0.5 to 1 µs). Most of that comes from the resonant start; over its start it gains 0.98–1.16×. It lowers ε_ro against its start at α ≤ 1.8 but not at α = 2.1.

### Checks

- Every headline number is computed at two or more truncations. Top Fock-level population is ≤ 1e-6 in the readout and pulse runs.
- Eigenvalues are cross-checked against time domain fits: Γ_X at 4 values of α, Γ_X with the drive on at 4 points, and Γ_Z at 6 values of α.
- Limits: Γ_X is not converged at α ≥ 2.6. The circuit simulation covers 150 ns without loss.

## Section 1 (groundwork)

Full write-up with figures: [task_1.md](task_1.md).

| Task | Result | Check |
|---|---|---|
| 1.0a | photon loss matches 4e^{−κt} to 1e-11 | analytic |
| 1.0b | two-photon loss plateau 0.499832 | ½(1 − e^{−8}), rel. error 1e-14 |
| 1.0c | settles at 4.39–4.41 photons; κ₂·t₉₀ = 0.86–0.90 | α² = 4.41; time scales as 1/κ₂ |
| 1.1 | memory overshoots to 6.91 photons at 0.23 µs, settles in 1.07 µs | buffer too slow (ε_d/κ_b = 1.29); ring period 0.319 µs predicted, 0.31–0.32 measured |
| 1.1 | 24×6 under-estimates the peak by 11% | its top buffer level holds 4.6% |
| 1.1 | ringing is physical | 100× tighter tolerance changes ⟨n⟩ by 5e-8; independent QuTiP BDF solver agrees to 2e-9 |
| 1.2 | smallest converged truncation 28×12; we use 32×12 | 36-pair grid vs 40×14: trace distance 0.31%, peak error 0.03% |
| 1.2 | the two truncations act independently | full 49-point grid to 48×18 on Vultr |
| 1.3a | vacuum gives ⟨a⟩ = 0; parity decays at 0.5135 per µs | symmetry; 2κ_an̄ = 0.5146 |
| 1.3a | superposition, not mixture: coherence 0.63 = parity 0.63 at 1 µs | becomes a mixture by 6 µs |
| 1.3b | push to \|β⟩ then pump: F = 0.9988 at β = 1.5, F ≥ 0.99 after 0.41 µs | 28×10 vs 32×12 agree to 3e-4 |
| 1.3b | tolerates ±35° phase error and β from 1.25 to 3.0 (F ≥ 0.99) | without stabilization only ±2.7°; 40×14 grid |
| 1.3b | drive along the other quadrature picks no well | Re⟨a⟩ = 0 by symmetry |

Why ±35° and not the one-mode model's ±45°: the slow buffer makes the memory swing past the well, and part of the state leaks into the wrong one (`research/explore/phase_gap.py`).

## AI use

- **Claude Code** wrote most of `src/`, `tasks/` and `research/s2/` under our direction.
- **Codex** built the Task 1.2 grid, the trace-distance metric, the brute force Task 2.1/2.2 runs and their tests.
- **Gemini** (`tools/ai_review.py`, log in [`reviews/`](../reviews/)) reviewed the physics in the code and checked the plots against our claims. It found no bugs. We re-ran the six points it raised; one corrected a coherence normalization to 1 + e^{−2α²}.
- No AI output was accepted unchecked. Every number has a hand prediction, a second method or a convergence test.
- One catch of our own: the default solver tolerance put about 1e-4 of noise into the truncation monitors, which could have hidden a real truncation problem.

## Reproduce

```bash
pip install -r requirements.txt
./run_all.sh                                          # Section 1 (~30 min), then Section 2 tables and figures from saved JSON
python -m research.s2.gx_eig --alpha 2.1 --na 28 --nb 8 --model two   # one Gamma_X point, about a minute
python -m research.s2.circuit_sim --na 12 --nb 5 --T 0.15 --dp -23    # full circuit, retuned pump
```

Big sweeps ran on Vultr with `cloud/vultr_batch.py` and the job lists in `cloud/s2_batch*.txt`. Costs are in [`tools-log.md`](tools-log.md). `results/s2/SUMMARY.md` has every Section 2 table.
