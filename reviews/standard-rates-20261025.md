# Tasks 2.1 and 2.2 — rate extraction and validation

Status: implementation, report and local verification complete; publication pending. Starting revision: `c7d3ef2` on `XZ-codex-intro-review`; working tree was clean. This continues the existing task implementation and evidence record. Maintained code is in `src/` and `tasks/`; deliverable numerical evidence is in `results/`, figures in `figures/`, walkthroughs in `notebooks/`, and the report in `README.md` / `TECHNICAL.md`.

## Requirements and acceptance evidence

- Task 2.1: initialize a coherent memory state and vacuum buffer; fit the decay of real mean amplitude at several small cat amplitudes; fit the exponential suppression against squared amplitude; compare its exponent with the challenge's approximate experimental benchmark without changing the supplied zero-temperature model.
- Explain the direct-matrix-element / Golden-Rule estimate, its prefactor and exponent, and the limits of that approximation for dissipative dynamics.
- Task 2.2: initialize an even cat and vacuum buffer, including the physical target amplitude 2.1; fit parity decay and sweep cat amplitude; compare the fitted slope with twice the supplied memory loss rate. Resolve finite-overlap steady-parity offsets before fitting small cats.
- Check Fock cutoffs for the extracted rates at each cat size, solver accuracy, fitting-window sensitivity and exponential residuals. Cross-check time-domain fits against independent integration / decay eigenvalues where practical.
- Deliver reproducible task scripts, saved trajectories and fit metrics, meaningful regression tests, publication-quality figures with complete captions, executable notebook walkthroughs, and concise professional challenge answers in the README.
- Preserve the completed introductory results. Commit and push to the existing authorized branch after verification.

## Initial numerical and literature investigation

The supplied two-mode model has no photon-gain or thermal excitation channel. Rate conventions must follow the prompt: the reported Gamma values are observable relaxation rates (inverse decay times), which are twice symmetric one-way Poisson switching rates. Literature prefactors are converted accordingly.

Pilot scripts and temporary timings: `/tmp/cat-qubit-standard-rates/`. Validated Python environment: `/var/folders/yp/fj5wbkqd3xqbc_jzqkb817wr0000gn/T/cat-qubit-validation-_hd1lpmm/venv/bin/python` (Dynamiqs 0.3.7, JAX 0.12.0.1, SciPy 1.18.1, QuTiP 5.3.1).

Primary theory reference: [Dubovitskii, Phys. Rev. A 111, 012617 (2025)](https://arxiv.org/html/2407.17299v2). The direct loss matrix element gives an exponential with coefficient four; a second-order leakage-and-return contribution can give coefficient two even at zero temperature. This is a qualitative guide, not a replacement for fitting the full two-mode model. The reference uses half the observable decay rate as its bit-flip rate.

Next action: benchmark time-domain integration, establish stable rate extraction, then run cutoff and amplitude sweeps.

## Implementation checkpoint

Owned files: `src/rates.py`, `src/rate_solver.py`, `tasks/task_2_common.py`, `tasks/task_2_1.py`, `tasks/task_2_2.py`, `tests/test_rates.py`, notebooks 06 and 07, the Task 2.1/2.2 result archives and figure pairs, the two Task 2.1/2.2 caption sections, and the cache entry in `.gitignore`. Concurrent Task 2.3 work appeared in the shared tree after this goal started. Preserve `src/readout.py`, `tasks/task_2_3.py`, `tests/test_readout.py`, notebook 08, its review/report/results/figures, and its edits to requirements/config/run_all. Shared README/TECHNICAL/caption edits must preserve that work and be reviewed by hunk before staging.

The new sparse solver changes the buffer basis by U=exp(i*pi*n_b/2), making H=iK and the density matrix real symmetric for the real coherent/even-cat inputs. Upper-triangle storage is exact. The operator-even sector used for parity includes both even-even and odd-odd memory blocks; it does not impose conservation of physical memory parity. Radau is L-stable and resolves the long lifetime without following every fast buffer oscillation. Direct sparse BDF and high-order BDF pilots were slower because their stability constraints kept timesteps small; these pilots were not adopted.

Nine targeted tests pass: known amplitude decay; parity offset and the bias of fitting zero offset; suppression regression; unresolved-decay rejection; finite-overlap projected cat rates; factor-of-two convention; dense complex versus rotated/packed generator; preservation of physical parity flips in the operator-even sector; and sparse integration versus a full complex matrix exponential.

Task 2.1 completed its six amplitudes (0.7, 0.85, 1.0, 1.15, 1.3, 1.4), full trajectories, cutoff eigenvalue studies, independent full Dynamiqs checks, fit-window checks and tighter-tolerance endpoint runs. Working cutoff (20,6), reference (24,8), maximum rate change 0.0042412%. The full generator and all Fock states remain in the calculation. Primary fit starts at 2 us. At alpha=1.4, the full trajectory extends to 10,000 us and has a fitted lifetime of 8,319.46 us.

Numerical scaling: gamma=2.9940654, C=0.04382113 per us, R²=0.9994566. Fitting the direct estimate 2*kappa_a*alpha²*exp(-4*alpha²) over the same interval gives gamma=3.0867396. The direct estimate at alpha=1.4 is 9.01738e-5 per us; the full fitted rate is 1.2020005e-4 per us (33.30% higher). A four-point loss-strength eigenvalue check at alpha=1.4 gives a linear coefficient 0.00154307 versus ideal first-order 0.00154379, with a positive quadratic contribution. This supports a finite-loss correction without introducing thermal photons.

Task 2.1 results: `results/task_2_1.json`, `results/task_2_1_trajectories.npz`, and `figures/task_2_1_bit_flips.{png,pdf}`. PNG visually inspected: labels/legends clear, fit and direct estimate distinguishable, log-time display spans the measured lifetimes. Command log `/tmp/cat-qubit-standard-rates/task_2_1-final.log`. Current process finished successfully.

Task 2.2 is running in exec session 97195, command `python -m tasks.task_2_2`, log `/tmp/cat-qubit-standard-rates/task_2_2.log`. Check that live handle before restarting. Amplitudes 1.2, 1.5 and 1.8 have passed all checks. At alpha=1.2, fitted offset is 0.114962 and Gamma_Z=0.1685354 per us. Planned remaining amplitudes: 2.1 and 2.4, including tighter tolerances. The task source gained derived diagnostics (zero-offset comparison and library versions) after this process loaded; rerun the command after it finishes to reuse caches and write the final analysis fields without repeating integration.

Next: complete Task 2.2, execute notebooks 06/07, finish the numerical report and README answers, render-check math, inspect both new figures, run the full applicable test suite, inspect preservation of introductory artifacts, then commit/push owned changes only. No claim of goal completion yet.


## Final verification

Both amplitude sweeps completed successfully. Task 2.2 covers alpha=1.2, 1.5, 1.8, 2.1 and 2.4 at (24,8), checked against (28,10) with separate mode increases. Gamma_Z at alpha=2.1 is 0.514558928 per us, T_Z=1.943412 us. The fitted slope is 0.116685393 per us versus 2*kappa_a=0.116867247, a relative difference of 0.156%. The largest cutoff rate change is 0.00025137%. At alpha=1.2, a forced-zero-offset fit underestimates the rate by 44.96%; the final analysis fits its nonzero offset.

The initial independent check at alpha=2.4 correctly rejected a 1.03e-6 observable discrepancy. It came from different finite-cutoff initial states: Dynamiqs' finite displacement exponential versus a normalized Fock expansion, with an initial mean-photon difference of 9.92e-7. The Dynamiqs check now uses exactly the same normalized Fock expansion. All independent trajectory differences are then below the 2e-7 acceptance criterion. The long sparse trajectories and their physical initial states were unchanged. A metadata-only cache-identity migration retained all 16 sparse trajectories byte-for-byte, verified by array hashes and an unchanged sparse-solver source hash; old fingerprints remain in metadata. Manifest and scripts are in `/tmp/cat-qubit-standard-rates/`. Cache identity now includes SciPy/NumPy versions and the relevant dynamics source, excluding unrelated analysis changes.

`python -m unittest discover -s tests -v` passes 29 tests in the shared worktree, including the 19 introductory/rate tests and 10 concurrent readout tests. Log: `/tmp/cat-qubit-standard-rates/tests.log`. The two new notebooks executed successfully with their default saved-data path; their embedded PNG bytes match the exported figures. Both PNG figures were visually inspected: axes, colors, fitting curves, legends and captions are legible and consistent.

`/tmp/cat-qubit-standard-rates/verify_delivery.py` verifies all rate data and checks, recalculates the two scaling regressions, matches reported tables to JSON, checks executed notebooks, matches canonical captions, and resolves 52 local links. All 48 protected introductory numerical/figure/notebook artifacts are byte-identical to c7d3ef2. GitHub's actual Markdown renderer preserves all 223 README formulas, 68 rate-report formulas, 152 caption formulas and 51 rate-walkthrough formulas. Two range expressions and adjacent tolerance expressions were rewritten to avoid Markdown's delimiter ambiguity. A thin-space escape in the concurrent readout paragraph was corrected without changing its equation.

Deliverables: the two task scripts and shared integration/check helper; fit and sparse-generator modules; nine new tests; JSON and NPZ result archives; two PNG/PDF figure pairs; executed notebooks 06/07; README challenge answers; `docs/task_2_rates.md`; technical index and canonical captions. The report explicitly discusses the rate/event factor of two, finite-range exponent, Golden-Rule prefactor, finite-confinement correction, parity offset and limits of finite-cutoff references.

The authorized destination is the existing origin/XZ-codex-intro-review branch. Commit only owned files and owned portions of shared README/TECHNICAL/captions; leave the separate Task 2.3 work intact.
