The latest presentation revision is documented in [the reference audit](task_2_4_reference_review.md). It separates the main answer covering(a)-(d) from the additional material retained in appendices. This file records the earlier merge assessment.

# Task 2.4: synthesis and editorial evaluation

This evaluation selects evidence from the local enlargement study and frozen cloud pulse campaign. It assesses the delivered work within the challenge; it is not a claim of new experimental physics, a literature-priority determination or human scientific approval. No additional quantum simulation was launched for this revision.

## Decision

Use **enlarge, measure, restore** as the main Task 2.4(c) answer. Use the fixed-size pulse campaign to explain termination trade-offs, distinguish dephasing from population transfer, and demonstrate the failure of a classical reset objective. Keep circuit corrections as separately qualified evidence. Do not claim an enlargement-plus-depletion hybrid that has never been executed.

The scientific report is `docs/task_2_4_final.md` and its PDF. The dedicated README is the single task entry point. Notebook 10 is the executable final synthesis; notebook 09 is the deeper enlargement-study record. The original cloud PDF is a historical automatic draft, not a competing final report. Independent source implementations and execution identities are preserved.

## Clarity

The earlier report already contained both studies, but their presentation was largely sequential. A reader could miss why one protocol was selected or assume that cloud robustness and depletion results also validated the enlargement cycle. Several metrics had to be inferred from separate tables.

The revision makes three distinctions explicit:

1. **Protection:** static logical-imbalance relaxation and complete-cycle wrong population.
2. **Information:** conditional-mean homodyne information, with SNR²=4I and I=1 corresponding to 15.9% ideal Gaussian classification error.
3. **Termination:** total remaining photon population, which is not determined by the mean buffer amplitude.

The added diagnostic Gamma_X/(2 information_rate) connects the independent studies in a symmetric, rare-switching plateau approximation. It is named and qualified where introduced. Its 78.3-fold reduction is distinct from the actual 41.6-fold complete-cycle wrong-population reduction. A local static-rate prediction and independently executed cloud constant pulse agree at approximately1%, with different cutoffs and recovery assumptions clearly stated. That diagnostic is not promoted as an independent convergence certificate.

The Gaussian normal CDF now has a separate symbol from the ATS phase operator. Infrastructure details have been removed from the core physics argument. The repository front page routes readers to the dedicated guide rather than repeating stale scientific-review status.

## Innovation

The useful challenge-level contribution is a quantitatively tested combination of known physical ideas: change the cat separation to improve bit disturbance per information, count ramp/recovery costs, and validate termination using the full quantum photon population. The selected operating point is stronger than simply increasing readout amplitude or displaying a larger buffer signal.

The most instructive additional observation is the failed mean-field depletion prediction. For one executed candidate, integrated information differs by only 3%, while quantum residual photons exceed the classical mean-field prediction by about 35 times. Fluctuation energy accounts for 99.47% of the final buffer photons. The variance identity is standard; the new evidence here is its quantitative consequence for the tested candidate. The discovery cutoff limits the precision and generality of that observation.

Do not market differential evolution, Gaussian smoothing, cat-size-dependent protection or buffer-mediated logical information as new inventions. Prior buffer/gate analysis includes [Gautier, Mirrahimi and Sarlette, PRX Quantum 4, 040316 (2023)](https://arxiv.org/abs/2303.00760). No exhaustive priority search supports a first-in-literature claim for this submission. The short bounded optimizer run is an interpretable pilot search, not a demonstrated state-of-the-art global quantum-control optimizer.

## Presentation and merge decisions

| Material | Final role | Reason |
|:--|:--|:--|
| Local circuit derivation and full two-mode baseline | Retain in(a) and(b) | Necessary physical foundation and sign/unit checks |
| Local conservative enlargement cycle | Main result in(c) | Equal-information execution, static-rate test, return/recovery and convergence evidence |
| Local fast enlargement cycle | Optional trade-off | Fast finite cycle, but static storage-rate budget is exceeded |
| Cloud fixed-time constant/raised/Gaussian comparison | Supporting result in(c) | Shows signal/error/termination costs under a common duration and peak |
| Cloud matched-information constant-pulse pair | Qualified diagnostic | Executed near-matched information, but discovery cutoff only |
| Cloud mean-field depletion candidate | Prominent negative result and new figure | Reveals the objective's failure to predict total photon energy |
| Cloud coherence and no-memory-loss cases | Mechanism evidence in(b) | Distinguishes superposition dephasing from much smaller population transfer |
| Corrected circuit/hardware calculations | Qualified feasibility and sensitivity | No corrected complete enlargement cycle or exact device guarantee |
| Unexecuted combined enlargement/depletion tail | Exclude from performance claims | Composing two independently studied controls changes the quantum dynamics |
| Automatic cloud report and normalized legacy traces | Historical evidence only | Preserve execution history without confusing the canonical result |

The new model-validation figure compares the same candidate's classical and quantum information and residual energy. It answers a physics question rather than adding another decorative overview. Captions state cutoffs, evaluation times and the limits of comparisons. Report and notebook use the same computed evidence index.

## Material concerns retained

- **Physical-model transfer:** the headline full cycle uses the ideal cubic model. Corrected-circuit static witnesses and short-time signal calculations do not validate that full cycle.
- **Readout claim:** mean-signal information is not measured single-shot assignment fidelity. I=1 is a modest reference target, not a high-fidelity demonstration.
- **Optimization fairness:**2.33× is relative to the specified weak reference. Fixed-time shaping comparisons have different information, and different cat-control resources preclude an unqualified universal ranking.
- **Rare-mode interpretation:** the selected mode has strong physical loading and numerical checks, but no full global-dominance proof. The final separate cutoff increments below 1% do not erase the earlier 2.117% joint change or form a rigorous error bound.
- **Robustness coverage:** the cloud amplitude/phase/coupling/damping tests are at fixed alpha 2.1. They cannot be transferred to the enlarged cycle without executing those cases.
- **Finite-time comparison:** the equal-clock idle uses smaller cutoffs than the enlargement cycle. The reported 12.3% advantage is empirical evidence, not a same-cutoff inequality certificate.

These limits do not invalidate the demonstrated ideal-model protocol. They define what the submission can defend and what would require further work. The defensible final assessment is a clear, reproducible computational capstone with a useful protocol and an informative negative result, rather than a finished device-level readout solution.

## Verification

The final synthesis recomputes the new metrics from delivered results and raw trajectories, checks the matching classical/quantum candidate parameters, verifies photon-population consistency and records source hashes. The revised notebook executes those computations and reproduces the new figure. The PDF build renders every page and checks glyphs, bounds and overfull boxes; the delivery review records the latest PDF/notebook hashes. The existing 131-test simulation-suite result is retained as its historical check, not falsely described as a new physics execution.
