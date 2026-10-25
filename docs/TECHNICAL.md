# Technical details

Methods, headline numbers and checks. Each task's notebook in [`notebooks/`](../notebooks/) has the figures and full captions. Reported numerical results are saved under `results/`.

**Model.** Exactly as in the prompt. Two-mode H = g₂(a²b† + a†²b) − ε_d(b + b†), jumps √κ_b b and √κ_a a, α² = ε_d/g₂. Parameters: g₂/2π = 0.763 MHz, κ_b/2π = 2.6 MHz, κ_a/2π = 9.3 kHz, α = 2.1. Units: ħ = 1, µs, rad/µs, with every 2π applied once in `src/config.py`. Numerics: dynamiqs 0.3.7, float64, Tsit5 with rtol 1e-8 to 1e-11.

## Section 2: methods and data

The [Task 2 report](task_2.md) gives the answers and selected figures. Notebooks 06–09 load saved data and perform the reported analysis. This section records the numerical methods, data locations and limits.

### Relaxation rates

`tasks/task_2_1.py` and `tasks/task_2_2.py` integrate the full two-mode Lindblad model and fit the real memory amplitude and memory parity, respectively. Rates are **observable decay exponents**: for symmetric switching at one-way rate $r$, $\Gamma_X=2r$. Consequently $1/\Gamma_X$ is an imbalance-relaxation time, not the mean waiting time between switches. The parity fit includes a free stationary offset.

The direct calculations use QuTiP BDF and independent Dynamiqs integration, with separate memory/buffer cutoff increases, fitting-window variation and tighter tolerances. `results/task_2_1.json` and `task_2_2.json` contain the settings and acceptance checks; corresponding trajectory archives retain the fitted observables.

For large cats, `research/s2/gx_eig.py` constructs the generator using `src/spectral.py`. With no memory drive, conjugation by memory parity divides the operator space into even and odd sectors. The relevant real-amplitude mode is odd; the parity-relaxation mode is even. With the drive on, the calculation uses the full generator. Shift-invert iteration returns eigenvalues near a chosen shift; a nearby eigenvalue is not automatically the physically dominant decay mode. The mode identification is checked against time evolution where decay is resolvable. Complex modes at strong drive are not reported as single-exponential rare-switching rates in notebook 09.

The undriven large-cat curve is supported by finite-cutoff comparisons through $\alpha=2.5$, with spread increasing from below 0.9% at $2.1$ to about 2.2% at $2.5$. Main's original sweep is not converged at larger amplitudes. The separately imported enlargement study uses larger dimensions and its own validation; it does not certify the original sweep.

### Buffer response and pulse comparisons

`tasks/task_2_3.py` independently evolves both initial coherent codewords. The nominal drive is $\epsilon_Z=0.05g_2$ at $(32,12)$. The complex-field settling criterion requires the entire remaining saved trajectory to stay within $0.01b_0$ of its 3–4 µs mean, with $b_0=\epsilon_Z/(2\alpha g_2)$. Independent QuTiP BDF, tighter integration, larger cutoffs and an 8-µs horizon are checked in `results/task_2_3.json`. The longer horizon checks a finite-time plateau, not an infinite-time contrast.

`research/s2/readout.py` extends the drive and cat-size sweep. It averages the last 5% of each 4-µs trajectory; this window differs from the nominal Task 2.3 analysis. `research/s2/pulse_eval.py` compares time-dependent readout pulses, including recovery after the drive ends. For the exact real-parameter symmetry $\beta_-=-\beta_+^*$, the stored `snr` is

```math
\mathcal I=\kappa_b\int[\mathrm{Re}(\beta_+-\beta_-)]^2\mathrm{d}t.
```

The stored `p_flip` is the recovered amplitude-loss proxy $\delta_X=(A_{\rm ref}-A_{\rm pulse})/(2A_{\rm ref})$, where $A=\mathrm{Re}\langle a\rangle$ and the reference has no readout pulse. Neither quantity is itself an experimentally measured assignment fidelity or a logical-projector probability. Historical `readout_error` calculations combine a coherent-Gaussian assignment estimate with this proxy; they are not used as a fidelity claim in the submission report.

The 2-µs pulse examples collect output through 4.5 µs and use $(30,8)$. A separate 0.5-µs pulse comparison, collected through 3 µs, has matching $(32,8)$ and $(36,10)$ calculations. Only the latter comparison has that joint-cutoff check. `research/s2/pulse_opt.py` optimizes $\mathcal I-\mu\delta_X$ with 40 bounded bins using automatic differentiation; the reported runs start from resonant alternating-sign pulses. Completed optimization iterations do not establish a global optimum or numerical convergence of every setting.

### Circuit approximation

`research/s2/circuit_sim.py` evaluates the exact sine interaction with padded displacement operators over 150 ns. It includes a 20-ns pump ramp but omits loss, buffer drive and readout. The pump amplitude matches the full-sine normal-ordered leading exchange coefficient. A detuning near −23 MHz reduces the short-time pair-conversion mismatch for these illustrative parameters. This is a calibration diagnostic; it does not validate rare switching or complete driven cycles under circuit corrections.

The notebook enumerates first-order resonant normal-ordered terms through degree seven. Higher-order virtual processes can also generate effective detunings, Kerr interactions and mixed pump/control corrections. Small coefficients alone do not bound their effect on an exponentially small switching rate. The protocol simulations retain the leading cubic model.

### Selected enlargement evidence

`results/task_2_4_enlargement.json` and `task_2_4_enlargement_trajectories.npz` contain the selected weak reference, conservative enlargement cycle and relevant convergence checks from XZ commit `17ef9a24fa1b501ee3421e5dd251209f88d395bc`. The JSON preserves original execution metadata, source hashes and immutable links to the simulation implementation. It records the distinction between original execution hashes and later cache-lookup changes.

Notebook 09 recomputes the counted information and recovered wrong-logical populations from the retained raw observables. The readout information budget ends at the exact drive-end sample; the complete-cycle duration includes return and recovery. Populations use orthonormal combinations of the even and odd cats at the original storage amplitude, with leakage reported separately and no postselection.

The selected enlarged cycle uses $(38,16)$ and its plateau-rate estimate $(40,16)$. The final tested cycle increment changes the wrong-logical population by 0.78%; separate last memory and buffer increments change the rate by 0.70% and 0.53%. Original solver and independent-implementation comparisons accompany the bundle. These are empirical checks, not a proof of infinite-cutoff convergence or global spectral dominance. The source commit contains the full simulation workflow; the submission imports only the evidence needed for this complementary result.

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
- **Codex** built the Task 1.2 grid, the trace-distance metric, the time-domain Task 2.1/2.2 runs, the enlargement study, and the selective submission integration.
- **Gemini** (`tools/ai_review.py`, log in [`reviews/`](../reviews/)) reviewed the physics in the code and checked the plots against our claims. Its review prompted additional checks, including a corrected coherence normalization to 1 + e^{−2α²}. Subsequent submission review corrected rate terminology and measurement-performance claims.
- No AI output was accepted unchecked. The task reports distinguish analytic comparisons, independent methods, cutoff checks and unverified extrapolations.
- One catch of our own: the default solver tolerance put about 1e-4 of noise into the truncation monitors, which could have hidden a real truncation problem.

## Reproduce

```bash
pip install -r requirements.txt
./run_all.sh                                          # Section 1 (~30 min), then Section 2 tables and figures from saved JSON
python -m research.s2.gx_eig --alpha 2.1 --na 28 --nb 8 --model two   # one Gamma_X point, about a minute
python -m research.s2.circuit_sim --na 12 --nb 5 --T 0.15 --dp -23    # full circuit, retuned pump
```

To regenerate notebook 09's tables and figures from the selected saved data, run:

```bash
jupyter nbconvert --execute --to notebook --inplace notebooks/09_task_2_4_better_readout.ipynb
```

Big sweeps ran on Vultr with `cloud/vultr_batch.py` and the job lists in `cloud/s2_batch*.txt`. Costs are in [`tools-log.md`](tools-log.md). `results/s2/SUMMARY.md` has every Section 2 table.
