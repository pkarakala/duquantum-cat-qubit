# Task 2.4: submission evidence selection

This review compares submission `main` at `dd52ed7` with XZ at
`17ef9a24fa1b501ee3421e5dd251209f88d395bc`. The numerical simulations were not
rerun. Main's resonant-control study remains the central short-pulse result;
XZ contributes a separate, tested way to preserve the storage relaxation rate.
The selection avoids importing the full exploratory campaign into the submission.

## Retained evidence

| Material | Submission role | Evidence and qualification |
|---|---|---|
| Main circuit expansion and short-time non-RWA calculation | Physical basis and calibration sensitivity | `research/s2/circuit_sim.py`, `results/s2/circuit_na14_nb6_T0.15_dp{0,-23}.json`; 150 ns, no loss, initial amplitude1. The −23MHz adjustment is specific to this calculation. |
| Main drive sweep | Fixed-cat signal/disturbance trade-off | `results/s2/readout_a2.10_32x8_T4.json` and `gx_two_*.json`; preserve cutoff and finite-window qualifications. |
| Main resonant pulses | Improve conditional-mean signal at lower recovered amplitude loss | `results/s2/pulse_a2.10_30x8_T2_peak.json`; pulse2µs plus2.5µs collection/recovery, not a2µs complete measurement. |
| Main linear response and optimizer | Explain why resonance is useful | `research/s2/linresp.py`, `pulse_opt.py`, saved `opt_*.json`. Linear SVD optimum is under its quadratic model; nonlinear optimization starts from a resonant waveform and is local. |
| XZ conservative enlargement cycle | Complementary protection criterion | Selected raw data and source links in `results/task_2_4_enlargement.json` and `task_2_4_enlargement_trajectories.npz`. Complete enlarge/read/restore/recover sequence, ideal cubic model. |
| XZ fifth-order derivation | Correct sign and occupation dependence | Negative fifth-order correction relative to positive leading exchange; distinguish first-order RWA terms from second-order off-resonant shifts/Kerr. |

Do not promote XZ's fast enlarged point, extensive pulse-family search, junction
imbalance proposal, incomplete corrected-device validation or mean-field
reset experiments into competing main results. They remain available at the
frozen XZ revision. No combined resonant-plus-enlargement pulse was simulated.

## Scientific corrections required in the main narrative

- **Rate convention:** ΓX is population-imbalance relaxation. In a symmetric
  two-state model each one-way transition rate is ΓX/2. The table's inverse
  rate must be called a relaxation time, not a mean time between flips.
- **Measurement observable:** the archive's `snr` is
  I=κb∫[Re(β+−β−)]²dt. Under a unit-Wiener homodyne convention, squared
  separation/noise is4ηI. The equal-prior coherent Gaussian error is
  Φ(−√(ηI)), matching the existing erfc expression. Calling I “SNR” obscures
  the convention. It is a conditional-mean signal functional, not a measured
  assignment fidelity.
- **Pulse disturbance:** main `p_flip` is the final Re⟨a⟩ loss relative to an
  idle calculation, divided by twice the idle mean. It estimates excess
  switching after recovery only if the states remain well localized. Main
  does not measure a logical projector or photon-counted transition events.
  Label this quantity as a recovered amplitude-loss proxy, δX. Adding it to
  Gaussian misclassification is a heuristic, not a simulated total error.
- **Timing:** pulse2µs, collection and recovery4.5µs. The2µs saved dataset has
  no matched higher-cutoff repetition. The36×10 convergence run hasT=.5µs
  and cannot certify the2µs result.
- **Circuit scope:** first-order RWA corrections reduce the leading exchange
  coefficient; “grows by4.5% per buffer photon” has the wrong sign. The
  −23MHz pump calibration is a finite-window closed-system test; it is not
  a universal device correction. Small first-order corrections do not bound
  the effect of omitted terms on exponentially small rates.
- **High-drive spectrum:** α1.0 and1.4 atεZ/g2=2 have selected complex modes.
  Their real parts should not be presented as a single-exponential rare
  switching process. Restrict that interpretation to the verified regime.
- **Optimization:** J=I−μδX is the implemented objective, rather than the
  ratioI/δX itself. Resonant initialization and incomplete local convergence
  preclude a claim of independent or global rediscovery of resonance.

## Independently checked numerical values

Direct reading of `pulse_a2.10_30x8_T2_peak.json` gives:

| Pulse | Peak εZ/g2 | I through4.5µs | δX after4.5µs |
|---|---:|---:|---:|
| Constant | 1.00 | 7.4689550234 | 0.008104423225 |
| Resonant cosine | 0.75 | 8.1777030704 | 0.004381266632 |

The Gaussian-plus-disturbance proxy is1.1243% versus0.6502% under ideal
collection, but the direct I/δX comparison is the defensible central result.
Across the nine saved optimizer settings, I/δX relative to the constant is
1.261–1.715; relative to the starting waveform it is0.985–1.158.

The enlarged protocol hasαro2.6,εZ/g2=.1, two2µs ramps, read duration
41.3996573393µs and2µs recovery. Its total duration47.3996573393µs compares
with110.2205085982µs for the specified weakα2.1,εZ/g2=.05 reference, a
2.32534-fold reduction. Both targetI=1; this is15.9% coherent Gaussian
classification error atη1, not a high-fidelity demonstration.

The recovered wrong-logical populations are7.9483412716e−6 and
3.3062566910e−4. UnlikeδX, these are absolute orthogonal logical-projector
populations; they must not be placed on a shared quantitative axis as though
identical. The enlarged readout plateau's selectedΓX is2.0351160787e−7/µs,
compared with3.8474869743e−7/µs for undriven storage: ratio0.52894684.
All these claims are limited to the cubic two-mode Lindblad model.

## Local bundle and provenance

`task_2_4_enlargement.json` stores configuration, full retained execution
metadata, logical and signal definitions, the two primary cycles, the36×14
cycle and its tighter integration check, relevant rare-mode certificates,
cutoff records, equal-duration idle control, model limitations and immutable
source links. Original execution hashes and cache-import history are retained
without relabeling them as the hash of the current implementation.

The NPZ preserves original complex arrays and time grids. Prefixes are
`baseline`, `amplified`, `conservative_36_14`,
`conservative_tight_36_14`, and `idle`. Each has `_t` and `_expects`;
all except idle also have freshly recomputed `_information`. Axis order is
(initial branch, observable, time), with branches(+α,−α) and observables:

0. a
1. b
2. a†a
3. b†b
4. Memory top-two population
5. Buffer top population
6. Negative logical projector
7. Positive logical projector
8. Leakage outside the orthonormal cat code
9. Trace

For each two-branch run, the wrong populations are
`e[0,6,-1].real` and `e[1,7,-1].real`. Recompute I by trapezoidal integration of
`kappa_b * (e[1,1].real-e[0,1].real)**2` on the original time grid. The budget
stops at the exactly saved time`ramp+read_time`; later emission is excluded.
Raw data are not clipped, normalized or postselected. The preserved sum of
both logical populations and leakage equals the recorded trace.

The bundle was assembled with`/tmp/select_task24_evidence.py` (hash recorded
in provenance). Original primary arrays come from the committed XZ trajectory
archive. Additional36×14 validation trajectories came from preserved local
execution caches and exactly match their previously published raw-array
hashes. They are now included in the submission bundle. All bundled file and
array hashes are recorded. Simulation reproduction uses the linked immutable
XZ source revision; no duplicate solver implementation is added to main.

Numerical acceptance: all four cycle information integrals and final
projector populations reproduce their source JSON values; all arrays are
finite; code-population closure holds within1e−12; source spectral embedding
matches the standalone validation file. The final cycle cutoff change is
0.775%; separate static-rate increments are0.699% and0.530%, while an earlier
joint increment is2.117%. These are empirical cutoff comparisons, not rigorous
bounds. No new physics execution or new131-test suite run is claimed.

## Literature checked for context

- [Dubovitskii, Physical Review A111,012617(2025)](https://arxiv.org/abs/2407.17299):
  second-order perturbative bit flips and exponential suppression, including
  loss and coherentZ-drive perturbations. Supports the physical interpretation,
  not the numerical coefficient fitted in this two-mode study.
- [Réglade etal., Nature629,778–783(2024)](https://arxiv.org/abs/2307.06617):
  experimental protected cat control and the ATS implementation context.
- [Gautier, Mirrahimi and Sarlette, PRX Quantum4,040316(2023)](https://arxiv.org/abs/2303.00760):
  reservoir-mode dynamics in dissipative cat-gate design. Relevant precedent
  for retaining the buffer dynamics; not a source for the present pulse result.

No literature-priority or hardware-fidelity claim follows from these citations.
