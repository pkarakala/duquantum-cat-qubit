# Research log

Every research run is listed here with its command, where it ran, and what it found. Results are in `results/research/` and figures in `figures/research/`. Unless noted, the solver is dynamiqs 0.3.7 Tsit5 (rtol 1e-8, atol 1e-10), α = 2.1, and the parameters come from `src/config.py`.

## Cloud batch, Oct 24 2026, 6:42 to 7:27 PM EDT

`cloud/vultr_batch.py` ran `cloud/research_jobs.txt` with 41 jobs on 3 VMs (voc-c-16c-32gb-300s-amd). Wall time was 45 min and the cost about $0.99. All jobs exited 0. The VM logs were in `results/batch-vm{0,1,2}.log` (overwritten by later batches; `results/logs/` keeps the last Section 2 batch). Summaries come from `python -m research.merge_cloud`.

| Study | Command (module) | Truncation (convergence pair) | Result |
|---|---|---|---|
| Overshoot as a damped pendulum, α sweep | `research.alpha_sweep --alpha A` | 30×16 to 44×16 (vs 24×12 to 38×12) | The predicted ringing period 2π/√((2g₂α)²−(κ_b/4)²) matches the simulation to within 2.5% at every α: 0.456/0.467, 0.375/0.370, 0.319/0.315, 0.277/0.276 µs at α = 1.5, 1.8, 2.1, 2.4. The envelope decay is 3.5 to 4.9 /µs against κ_b/4 = 4.08 (±20%). The overshoot grows with α (peak/final 1.21, 1.38, 1.57, 1.76). Truncation pair differences are ≤ 4e-4 for α ≤ 2.1, and 7e-3 in the peak at α = 2.4. |
| Shaped ε_d turn-on | `research.schedules --shape S` | 40×14 | Step: settles (1%) in 1.06 µs, peak n_a 6.91. Two-step (70% at t = 0, then 100% at 0.26 µs): 0.70 µs, peak 4.74, which is 34% faster and gives 31% less overshoot. Linear 0.6 µs ramp: 0.87 µs, peak 4.45. The sin² ramps and the 0.4 µs linear ramp are slower than the step. |
| 1.3b fine grid | `tasks.task_1_3b --phase/--beta` | 40×14 (vs 32×12) | F ≥ 0.99 for phase error ≤ 35° (0.9908) but not 40° (0.9838), and for β between 1.25 and 3.0. β = 3.5 plateaus at 0.987. The 40×14 and 32×12 runs agree to ≤ 3e-5 at the shared points. This is claim B8 in TECHNICAL.md. |
| GRAPE for \|+α⟩ prep | `research.grape --na 36 --nb 10 --iters 60 --init I --seed S` | 36×10 | T = 0.4 µs, 16 bins, memory-drive cap 5 MHz, ε_d shaped too. The best seed reaches min F_hold 0.99974 over the hold window 0.4 to 0.7 µs (loss 1.3e-4). The best on/off pulse at the same cap (3 bins on) reaches 0.9954 (loss 2.8e-3), so GRAPE has about 20× lower infidelity. Three seeds give losses of 1.3e-4 to 2.2e-4, and a cold start gives 3.4e-4. The optimizer saturates the cap along i(a†−a) and front-loads ε_d. |
| Heisenberg basin map | `research.heis` | one mode N = 30 | F(β) at T = 1 µs: 0.50, 0.85, 0.981, 0.9992 at β = 0, 0.5, 1, 1.5. F ≥ 0.99 needs β ≥ 1.12, and F ≥ 0.999 needs β ≥ 1.48. The best {0,1}-photon seed gives 0.912. Forward and Heisenberg runs agree to 1e-14. |
| Robustness of the displaced start | `research.robust` | one mode N = 30 | F ≥ 0.99 for phase error ≤ 44.5° (2.5° without stabilization) and for β from 1.12 to ≥ 4. The two-mode values are smaller (35°, β 1.25 to 3.0): see the phase-gap study below. |
| Moon cats (a² + λa†a) | `research.moon` | 28×7 | Negative result: no gain in inflation speed or prep fidelity. |
| Inflation GIF | `research.wigner_gif` | 32×12 | `figures/inflation.gif` |

## Local explorations (this sandbox, 4 cores)

| Study | Command | Result |
|---|---|---|
| Why two-mode tolerates less phase error than one-mode | `python -m research.explore.phase_gap` | The F = 0.99 edge is 44.8° in the one-mode model and 35.5° in the two-mode model. Holding κ₂ fixed and making the buffer 2, 4, 8, 16× faster moves it to 37.0, 38.3, 40.2, 41.4°. The cause is the slow buffer (κ_b < 8g₂α): the exchange is underdamped, the memory overshoots past +α, and part of it leaks into −α. Pre-filling the buffer makes it worse, and the basin boundary is the same in both models. See `research/explore/FINDINGS_phase_gap.md`. |
| Fastest robust prep | `python -m research.explore.fast_prep` | Push straight to β = α, then switch ε_d on as a step. Worst case over ±20° phase and ×0.7 to ×1.3 amplitude reaches F ≥ 0.99 in 0.48 µs, with F(1 µs) ≥ 0.9983. Ramping ε_d hurts here. 0.999 is not robust. 24×8 and 32×12 agree to 3 ns and 1e-4. See `research/explore/FINDINGS_fast_prep.md`. |

## How the results fit together

The buffer is too slow for the adiabatic elimination (κ_b/(8g₂α) ≈ 0.2). That one fact explains the 1.1 overshoot, the pendulum period at every α, why the two-step ε_d turn-on works, why the two-mode phase and amplitude windows are smaller than the one-mode ones, and why β = 3.5 fails in two modes but not in one. The same 2×2 exchange dynamics sets the buffer ringing in the Standard-track readout (Task 2.3).
