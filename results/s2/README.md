# Section 2 results

**Interpretation of archived names.** In the readout/pulse records, `snr` denotes the conditional-mean information $\mathcal I$, and `p_flip` is the recovered amplitude-loss proxy $\delta_X$. The historical assignment-error estimates are model-based scores, not simulated single-shot fidelities. See the [submission report](../../docs/task_2.md) and [methods](../../docs/TECHNICAL.md) for the current definitions and supported conclusions.

Every Section 2 number is in one of these JSON files. `SUMMARY.md` collects them into tables
(`python -m research.s2.summarize`). Each file records its host and UTC time under `_meta`.

| Prefix | Script | What it holds | Name pattern |
|---|---|---|---|
| `gx_` | `research/s2/gx_eig.py` | Γ_X (odd block) and Γ_Z (even block) Liouvillian eigenvalues | `gx_{one,two}_a{α}_{Na}x{Nb}_ka{κ_a scale}_nth{n_th}_ez{ε_Z/g₂}_kb{κ_b scale}` |
| `gxt_` | `research/s2/gx_time.py` | Γ_X from a time-domain fit of Re⟨a⟩(t), to cross-check `gx_` | `gxt_a{α}_{Na}x{Nb}_ez{ε_Z/g₂}_T{window µs}_rt{rtol}` |
| `readout_` | `research/s2/readout.py` | ⟨b⟩(t), ⟨a⟩(t), SNR(t), settling time and ring fit for step drives | `readout_a{α}_{Na}x{Nb}_T{µs}` |
| `pulse_` | `research/s2/pulse_eval.py` | SNR and P_flip for each pulse family and level | `pulse_a{α}_{Na}x{Nb}_T{µs}[_peak]` |
| `opt_` | `research/s2/pulse_opt.py` | gradient-optimized pulse, its SNR and P_flip, and the optimizer history (`partial: true` = checkpoint of a run cut off by a time limit) | `opt_a{α}_{Na}x{Nb}_T{µs}_pk{peak/g₂}_{init}_mu{scale}_s{seed}` |
| `circuit_` | `research/s2/circuit_sim.py` | full ATS circuit simulation (no RWA) vs the g₂ model | `circuit_na{Na}_nb{Nb}_T{µs}_dp{pump detuning MHz}` |
| `fidelity_` | `research/s2/fidelity.py` | best readout error vs α from SNR(t) and Γ_X(ε_Z) | `fidelity_eta{efficiency}` |

The `gx_` files include every truncation we ran; `SUMMARY.md` reports the largest one and the spread
across the others as the convergence check.
