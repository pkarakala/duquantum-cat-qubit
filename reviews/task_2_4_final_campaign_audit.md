# Independent audit of executed Task 2.4 campaign

Read-only synthesis of `results/task_2_4_campaign`, 2026-10-25. All numbers below
come from saved execution outputs. Main campaign: **104 completed cases and two
preserved QuTiP40x14 timeouts**. Both independent Dynamiqs32x12 comparisons
passed, and both supplemental Dynamiqs40x14 joint-cutoff comparisons have now
passed. This audit does not convert execution completion into a convergence,
measurement-fidelity or circuit-device certificate.

## Main conclusion

The defensible finding is a **measured signal/error/termination trade-off**,
not a universally superior waveform. Smooth envelopes leave substantially fewer
buffer photons at turn-off and produce smaller recovered wrong-logical
populations at the same peak drive and duration, while collecting less signal.
There is no executed, converged, matched-SNR complete-cycle result establishing
that any shaped pulse beats a properly tuned constant pulse on every objective.
An informative negative result is that semiclassical depletion can suppress the
mean field yet leave almost entirely incoherent quantum buffer excitation.

## Five actual protocols

All use physical alpha2.1, ideal collection eta1, cubic full two-mode dynamics,
both supplied losses and two-us recovery. `I` is the conditional-mean reference;
the user's unit-vacuum-noise convention gives **SNR²=4I**, not SNR²=I.
Wrong population is the larger branch value **after recovery**. Buffer photons
are the larger value **at pulse end**, before recovery.

| Job ID | Pulse / peak epsilon/g2 | T / total cycle (us) | Cutoffs | I | Recovered wrong population | nB at turn-off |
|---|---|---:|---|---:|---:|---:|
|`pulse_b1f2b1393d0b0ff1`|Constant /.5|4 /6|32x12|3.68358128|0.00182771479|0.0270651681|
|`pulse_6f787216b4e21a6d`|Raised cosine /.5|4 /6|32x12|3.24161812|0.00157947277|0.00376371282|
|`pulse_b270049fcd119450`|Gaussian /.5|4 /6|32x12|1.30799789|0.000567907608|0.0000991781387|
|`pulse_f6cd5d8474031835`|Build/hold/deplete /.5|4 /6|24x8 discovery|1.59270236|0.000651975630|0.000165782611|
|`pulse_0b35816270623dda`|Semiclassical proposal /.491566|2 /4|24x8 discovery|1.42317690|0.000629062695|0.00361309375|

Against the32x12 constant, raised cosine changes I by **−11.9982%**, recovered
wrong population by **−13.5821%**, and turn-off photons by **−86.0939%**.
Gaussian changes these by **−64.4911%,−68.9280%,−99.6336%**. The changes are far
larger than the observed numerical variations below, but they are trade-offs.
After the common two-us recovery, all three nominal final buffer populations
are near the nonzero idle background1.75e-5. Do not claim their turn-off-photon
ratios remain the ratios of the final residual population.

Post-pulse information references are0.0565553(constant),0.000328977(raised)
and8.38982e-7(Gaussian). Thus smooth termination also strongly suppresses
information continuing to escape after the stated pulse window. This emitted
information is excluded from the on-pulse target rather than counted twice.

Reproducible synthesis figure: `tools/plot_task_2_4_campaign_synthesis.py` writes
`figures/task_2_4_campaign_synthesis.png/.pdf`; its labels explicitly separate
signal at4us, recovered population at6us and photons at4us. Its output lists
input-summary hashes in `/tmp/cat-qubit-final/synthesis_figure_evidence.json`.

## Fair matched-information evidence

There is an **executed near-matched-I constant-pulse pair** at24x8:

- `pulse_8b3e6c057c6aa358`: peak.5,T2us,total4us,I1.848384,
  recovered wrong9.101888e-4,nB(T).02703182.
- `pulse_cd2996ec315d34de`: peak.25,T8us,total10us,I1.847411,
  recovered wrong6.564355e-4,nB(T).006711198.

I differs by only0.0527%. The stronger drive gives4x shorter readout and2.5x
shorter complete cycle, but approximately38.7% more recovered wrong population
and4x more photons at turn-off. This is direct finite-time evidence of a
speed/error trade-off, with **discovery-cutoff qualification**. It is not a
converged equal-fidelity or single-shot result.

For the three32x12 finalists, the executed trajectories first reach I1 at
1.07838us(constant),1.34998us(raised),2.43327us(Gaussian). At those prefixes,
the in-code wrong populations are2.92651e-4,2.88616e-4 and2.86543e-4, while
transient leakage is1.2449%,1.2391% and1.0282%. These are prefix diagnostics,
not recovered errors for counterfactually stopped pulses. A stop/reset protocol
at those crossing times was not executed. Do not compare these prefix values
as though they were complete-cycle matched-SNR certificates.

The18 nominal T4 discovery cases are all nondominated in the three-objective
sampled space (maximize I, minimize recovered wrong population, minimize
turn-off photons). This is a sparse sampled trade-off set, not proof that18
protocols are globally optimal. Selection froze one throughput constant, one
throughput shape and a depleted shape above a25%-of-shape-information floor;
it selected Gaussian rather than a build/hold/deplete proposal.

## Why the model-informed depletion did not establish superiority

The high-information semiclassical proposal above uses hold.970244 and
termination−.716104. Its classical prediction is I1.46713260 and
|B(T)|²1.03321784e-4. Full quantum evolution gives I1.42317690 (3.0% lower),
so integrated mean-signal prediction is reasonably close. However:

- Actual full buffer photon population is **0.00361309375**, about35x the
  semiclassical mean-field population prediction.
- Actual quantum coherent contribution |<b>|² is only1.93000004e-5.
- Its incoherent contribution nB−|<b>|² is **0.00359379375**, or **99.47%**
  of the residual photons.

The middle proposal `pulse_836f82196b0002e5` similarly has full nB3.17004e-4,
versus classical |B|²2.09332e-5, about15x lower. This is a real limitation of
using mean-field buffer depletion as the quantum optimization objective.
It supports reporting an honest negative result and retaining simple smooth
controls as the demonstrated low-residual alternatives. The proposals only
have discovery-cutoff simulations; do not present their precise error values
as fully converged finalists.

## Quantitative numerical reliability

These are observed numerical variations, not statistical confidence intervals
or rigorous infinite-cutoff bounds.

| Nominal32x12 base | Larger case/backend | Max complex buffer difference / predicted amplitude | Final wrong population absolute change | Relative final wrong change |
|---|---|---:|---:|---:|
|Constant|40x12 QuTiP `pulse_3c540025950a8060`|3.781e-7|3.599e-8|0.00197%|
|Constant|32x14 QuTiP `pulse_7def789618bfcb8d`|5.437e-6|2.731e-7|0.01494%|
|Constant|40x14 supplemental Dynamiqs|5.407e-6|3.143e-7|0.01719%|
|Raised|40x12 QuTiP `pulse_a5b8e7695895865f`|3.516e-7|3.089e-8|0.00196%|
|Raised|32x14 QuTiP `pulse_fcc62fa25ee2b3a1`|4.389e-6|2.367e-7|0.01499%|
|Raised|40x14 supplemental Dynamiqs|4.233e-6|2.720e-7|0.01722%|
|Gaussian|40x14 QuTiP `pulse_5ac874019af068b3`|3.522e-6|5.782e-8|0.01018%|

The supplemental comparisons are explicitly **combined cutoff and backend
changes**. They do not replace the original timeout statuses or serve as new
same-cutoff solver checks. Supplemental maximum ALL-TIME wrong/leakage
absolute differences are3.627e-7/1.688e-7(constant) and3.185e-7/1.103e-7(raised),
within prechosen1e-6 criteria. Their full trajectory archives retain signed
residuals; final minimum eigenvalues are about−6.5e-9, above the−1e-7 floor.
Supplemental40x14 I changes are−5.24e-7 and−4.37e-7 relative to32x12.

Independent SAME-cutoff Dynamiqs comparisons give maximum buffer differences
1.2445e-8(constant) and2.2598e-8(raised). Final wrong differences are1.02e-13
and5.90e-12; final leakage differences7.12e-13 and2.37e-16. Both certificates
pass. Tighter QuTiP checks `pulse_9433f4ab71ee838b`, `pulse_13a613390d28f057`,
`pulse_d7eef2c07bba17a9` retain the reported conclusions. The0.01→0.005us grid
change contributes a relative I change1.38e-7 for raised cosine; integration
and quadrature differences must not be confused.

## Information, dephasing and switching are visibly different

At4us, an initially even-cat reduced-memory logical coherence is:

| Static drive ratio | Supplied memory loss | Memory loss turned off |
|---:|---:|---:|
|0|0.127957914|1.000000000|
|.25|0.068061116|0.534610833|
|.5|0.010225340|0.085651306|

Case IDs: `dephasing_32bb5b3b5d8b82ef`, `dephasing_8b37c58f927445e6`,
`dephasing_309a9bca27f1eac6`, `dephasing_91943cca505fffb1`,
`dephasing_bc3927569d08644b`, `dephasing_482eec3aab79b10b`.
The substantial coherence attenuation with kappa_a0 is distinct from physical
memory photon loss and from recovered wrong populations of order1e-4–1e-3.
Reduced-memory coherence also includes buffer entanglement and temporary
leakage; it is not uniquely pure measurement dephasing. Its oscillatory Bloch
phase is a deterministic logical rotation, not itself decoherence.
Turning off kappa_a in the nominal pulse tests only reduces recovered wrong
population by2.08%,2.11%,2.58% for constant,raised,Gaussian, respectively;
readout-associated wrong population remains. No complete noisy single-shot
classification or full-cycle covariance calculation was executed. Local
stationary covariance checks from earlier weak-drive cases do not certify the
strong0.5-drive pulse distributions.

## Static rates: useful evidence, retain candidate qualification

At alpha2.1, returned memory-visible candidate rates are3.84748741e-7(idle),
1.62149885e-4(drive.25),9.25129976e-4(drive.5), all perus. Jobs:
`spectrum_901a773f41ca4bc9`,`spectrum_ff9f21f0a6f5ccda`,
`spectrum_9fc41669a0343782`. Memory modal coefficients are0.99920,0.99889,
0.99804 and logical-imbalance coefficients0.99999,0.99697,0.98800. A shift
1e-8→1e-9 repeats the.25 rate to about1e-11 relative
(`spectrum_b6312ff4cbad7a2f`). Four returned near-shift modes with validated
left/right coefficients are stronger evidence than an unlabelled k1 result,
but **global_dominance_certified remains false**. Physical-target rate Fock
convergence is not supplied by pulse-field cutoff convergence.

Small-system time-domain checks `spectrum_1cc5e94e8d4f8b5b` and
`spectrum_2e809c1f1a86428b` reproduce both memory and logical-imbalance candidate
rates over three late fit windows (max relative discrepancy<4e-11 within those
same12x4 generators). At alpha1.4,16x6→20x8 changes the driven.25 rate by0.0178%
(`spectrum_6adf1b5ada8352b9`,`spectrum_e9b69cebd7ca45aa`), while the12x4
rate differs by0.1677% from20x8. Numerical self-consistency at one cutoff is not
a physical precision claim. Report rates as observable relaxation exponents,
not individual one-way switching rates, and not extrapolated physical lifetimes.

## Robustness and circuit corrections

- ±5% microwave amplitude changes I approximately−9.7%/+10.2%, and recovered
  wrong population approximately−13%/+15%. Small phase errors±0.05rad leave
  optimized-LO I almost unchanged but increase the worst wrong branch~10–11%.
  Fixed-real-LO signal is also stored and should accompany any phase claim.
- ±5% uncalibrated coupling changes worst wrong population by roughly−34%/+45%
  and creates total leakage~0.0027. Nearly all that leakage already occurs in
  matched no-readout controls because the buffer pump is held fixed. Do not
  attribute it to readout alone or call it a robustly recalibrated cat.
- Calibrated sixth-order circuit-correction cases exist for all three32x12
  pulses: `pulse_d1b0e6a67e06d350`, `pulse_61f55c6303528a2b`,
  `pulse_598de0989ffbdd2d`. They preserve the qualitative smooth-turn-off
  trade-off but change quantitative values. Constant versus raised gives
  I4.10174/3.62159, worst wrong0.00215430/0.00185746. Constant branch wrong
  populations are unequal [0.00167633,0.00215430]; use the worst branch.
  Total final leakage~0.0001668 is mostly corrected-model idle background,
  not readout-excess leakage. These Hamiltonian-only corrections are a
  sensitivity calculation, not a full GHz open-system device certificate.

Machine-readable audit numbers and interpolation calculations are reproducible
with `/tmp/cat-qubit-final/analyze_campaign.py` and its JSON output. Parent may
use the synthesis script and figures directly. No core source or execution
results were modified for this audit.
