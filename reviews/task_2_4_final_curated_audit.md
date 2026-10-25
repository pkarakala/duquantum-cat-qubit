# Independent final audit: curated Task 2.4 study

Scope: read-only audit of the curated Markdown, main JSON/NPZ, standalone spectral/measurement/circuit validation JSON and relevant maintained source. No new simulation or cloud expenditure. Arithmetic was independently recomputed from the delivered trajectory arrays; machine-readable results are in `curated_arithmetic.json`.

## Verdict

The curated study supports a useful **ideal cubic-model design witness**, not a global optimum, exact open-circuit guarantee, single-shot fidelity certificate or rigorous infinite-Fock error bound. All four challenge parts are addressed. The numerical headline values are internally correct. The main finalization blocker is stale embedded spectral evidence in `results/task_2_4.json`; several claim qualifiers below must survive PDF synthesis.

## Verified headlines and exact evidence

| Claim | Verified value | Keys / evidence |
|---|---:|---|
| Enlarged/weak real contrast | 1.6158755569 | `tradeoff.amplified_size[0].contrast_3_4us` / `tradeoff.baseline_size[0].contrast_3_4us`: 0.03844115542 / 0.02378967567 |
| Information-rate ratio | 2.6110538154 | Same rows, `mean_field_information_rate_per_us`: 0.02414049003 / 0.009245496930 |
| Conservative static Gamma / idle | 0.5289468404 | `spectral_validation.primary_result.gamma_x_per_us` / `storage_reference.gamma_x_per_us`: 2.035116079e-7 / 3.847486974e-7 per us |
| Equal-signal total durations | 47.39965734 versus 110.22050860 us | `cycles.amplified.metrics.cycle_duration_us`, `cycles.baseline.metrics.cycle_duration_us` |
| Total speedup versus specified weak reference | 2.3253439958 | Ratio of those durations; includes ramp up, return and identical 2-us final relaxation |
| Information targets | 0.9999924592 versus 0.9999999990 | Independently integrated kappa_b*(Re Delta B)^2 through each saved readout-end timestamp; matches JSON exactly |
| Final wrong-logical population | 7.948341272e-6 | `cycles.amplified.metrics.max_wrong_logical_population`, also raw NPZ observables 6/7 |
| Matched-clock idle wrong population | 9.058799048e-6 | `matched_idle_cycle.wrong_logical_population[0]`, same total duration47.39965734 us |
| Relative population reduction | 12.25833326% | Absolute margin1.110457777e-6; not a measured classification-error improvement |
| Conservative final leakage | 8.109538013e-6 | `cycles.amplified.metrics.final_leakage`; separately reported, no postselection |

All promoted cycle metrics and information integrals agree exactly with independent recomputation from `results/task_2_4_trajectories.npz`. These initial states are coherent codewords; their initial population in the opposite exact logical basis is5.4573945e-9 at alpha2.1. That background is negligible on this comparison's scale and common to its controls, but the reported p_X is an absolute final population, not a heralded transition counter.

## Finalization blocker: duplicate spectral data are stale

At audit time, the main JSON's `spectral_validation` differs from standalone `task_2_4_spectral_validation.json`. Standalone evidence adds raw-output normalization review, updated independent trajectory hash, a physical-loading guard, and explicit `global_dominance_certified=false`. The embedded copy still points to the legacy normalized trajectory archive hash. Headline rare rates are unchanged; fit changes are negligible, but provenance and qualifications differ. Refresh the embedded copy from the standalone file without relabeling any historical execution source, or avoid duplicating the dataset. Embedded circuit and measurement JSON match their standalone files exactly.

## Comparator fairness and the actual rate budget

The2.33-fold speedup is against the **specified Task2.3 weak readout**, epsilon/g2=.05 at alpha2.1. It is not established as the best possible constant drive at a common error budget. A stronger constant alpha2.1 drive would be faster if errors were unrestricted: the .1 point has information rate.03697496 per us, exceeding the enlarged .1 point's.02414049, but Gamma2.3661e-5 per us is approximately116 times the promoted2.0351e-7 rate. This is the relevant trade-off, not a claim that every stronger constant drive is slow.

For a strict plateau budget Gamma<=the original idle value3.8475e-7, the promoted estimate is47.1% below the budget. Every tested nonzero fixed-alpha2.1 point (.05 and above) exceeds that budget; even the weak point is15.87 times idle. This supports the usefulness of changing cat separation. It does not prove that no untested phase-shaped or other constant control could satisfy a different budget. At the still stricter budget Gamma<=2.0351e-7, even original undriven storage exceeds the target. There is consequently no demonstrated nonzero-readout comparator at alpha2.1 with that same static rate.

**Use:** “At the same ideal mean-signal target, the tested enlargement cycle is2.33 times faster than the specified weak-readout reference while giving a smaller selected static relaxation exponent than undriven storage.”

**Avoid:** “The fastest/optimal readout at matched fidelity” or “2.33 times faster than all constant drives.” The supplied data contain neither an exhaustive constant-control optimization nor actual fidelity measurements.

## Numerical error and mode identification

- The conservative rate's final memory increment (38,16)->(40,16) is0.69923%; a buffer increment at fixed Na36 is0.53012%. The earlier joint (36,14)->(40,16) change is2.11707%, explicitly failing the1% joint threshold. Do not compress these into “the rate has a rigorous0.7% error bar.” These are empirical finite-cutoff increments. The47.1% static budget margin is much larger than the observed last increments, but they do not mathematically bound omitted states or model error.
- The finite-cycle wrong-population change (36,14)->(38,16) is6.1580e-8, or0.77475%; the observed advantage over idle is1.11046e-6, about18 times this increment. Tighter integration changes final p_X by5.06e-14. Idle is directly integrated at28x10 while the cycle uses38x16; the idle static-rate difference to32x12 is0.18%. This is strong empirical support, not a same-cutoff or rigorous inequality certificate.
- The promoted spectral solve returns a k=1 nearest-shift real mode. Its physical loading is5.19724 versus initial Re(a) separation5.2; right/left residuals2.03e-13 and9.66e-11 per us and conditioning11.71 support it. Representative independently integrated cases verify the rate convention. The updated standalone file explicitly says global spectral dominance is not certified.
- **Use:** “selected logical-population relaxation mode with strong codeword/observable loading, supported by independent checks.” Do not say full-spectrum or rigorous slowest-mode certification.
- Gamma_X is an observable-imbalance decay exponent. In a symmetric two-state model one-way switching rate is Gamma_X/2. Keep this factor throughout rate and finite-probability interpretations.
- The optional fast point has about4.6% last memory-cutoff variation in its static rate; its pulse population has a smaller0.57% last joint increment. Those convergence statements cannot be exchanged.

## Circuit physics and limits

The printed positive-sine ATS pump gives negative cubic exchange; the declared pi pump-phase change correctly realizes positive g2. A separate microwave memory-drive port is physically specified, and fifth-order number-dependent exchange terms are correctly distinguished from second-order off-resonant Kerr terms. The joint-cat projector is orthogonal.

The conservative complete-cycle result is **cubic-model** evidence. The corrected static phase-six rates and full-phase finite-time signals form separate evidence. The corrected field trajectories improve the same ideal4-us information reference by2.65-fold, but no full-phase switching rate or corrected full enlargement/return cycle exists. Phase-six matched-hardware switching rates have2.49% final memory and4.69% separate buffer increments, without a joint38x12 point or idle buffer sweep. Their rates are a cutoff-qualified witness. Linear shifts and Kerr compensation require real microwave/pump retuning; bath dressing, flux noise and exact open-circuit dynamics are omitted.

There is one wording contradiction in the draft: the early off-resonant section describes the all-phase diagonal-only calculation as the sensitivity model, while the later section correctly says the promoted full-phase matrix includes off-diagonal two-pump processes. Reconcile as: “The earlier diagonal-only result is retained as a restricted diagnostic. The promoted finite-time sensitivity calculation includes the full fundamental-pump van-Vleck matrix; neither gives an exact Floquet open-system certificate.”

Cancelling the coherent mean buffer force in the number-dependent model does not restore an exact coherent dark state. Circuit results must retain their corrected-model idle reference. The draft generally makes the appropriate distinction, and should not recast the correction model as preserving the exact original cat dark manifold.

## Oscillation, depletion, dephasing and output statistics

Input shaping is an honest negative result: settling .968->.666 us but I(4) decreases .0370483->.0359843, approximately2.87%. Reduced ringing is not demonstrated faster measurement at fixed information. The enlargement strategy is not the proposed fast-depletion pulse; describe those controls separately.

Raw curated traces show final buffer populations around1.75075e-5 for every cycle, rather than literal vacuum. At drive switch-off they are2.8474e-4 (weak),6.7099e-4 (conservative), and4.1125e-3 (fast). Information emitted after the readout interval, deliberately excluded, is0.0005712,0.0014587 and0.0091479 respectively. This is consistent with the stated budget and recovery design. Do not claim exact vacuum or zero residual information. Larger cats additionally incur1.53 times the leading photon-loss phase-dephasing scale on the plateau.

The reference I=kappa_b integral(Re DeltaB)^2 has SNR²=4 eta I for the unit-Wiener current convention if I is defined at ideal efficiency. For eta=1, I=1 gives coherent-Gaussian equal-prior error15.9%, not1%. The local stationary-boxcar covariance diagnostic is near vacuum (~.15% at the conservative point), but it does not establish full-cycle Gaussian records or classification fidelity. Wrong-logical population, leakage, information-induced logical dephasing and detector classification error remain different quantities.

## Challenge coverage

(a) Physical memory drive and ATS/correction derivation: addressed, with explicit phase/calibration costs and model limits.
(b) Contrast/Gamma drive sweep: addressed within the ideal two-mode model; physical mode qualification and finite-window contrast are stated.
(c) Demonstrated strategy: enlargement/read/restore, with explicit same-signal weak comparator, a strict storage-rate reference and directly integrated post-return populations. Not a universal optimized protocol.
(d) Physical justification: weak-response scaling motivates the design, full two-mode static and cycle calculations test it, cutoff and solver evidence support it, and input-shaping/circuit limitations are reported.

After refreshing the stale spectral embedding and retaining the precise comparator/model qualifiers, no arithmetic contradiction blocks a scientifically defensible report of these curated findings. Broader cloud pulse searches may add evidence, but should not be silently conflated with this curated design witness.

## Requested surgical fixes applied

At the parent's request, refreshed only `results/task_2_4.json["spectral_validation"]` from the standalone JSON, preserving every other top-level value and all historical source/execution identities. Reconciled diagonal-only versus full-phase wording in the detailed Markdown, added the non-global mode qualifier and the failed 2.117% earlier joint-cutoff increment. Strict finite JSON and `git diff --check` pass. No simulations were rerun.


## Finalization resolution

The embedded spectral evidence was refreshed from the standalone validation file, with every other top-level result asserted unchanged. The final synthesis explicitly reports the failed 2.117% earlier joint cutoff increment, non-global mode qualification, actual reference comparator and corrected-model limits. The blocker described in this historical audit is resolved.
