# Truncation study update — 2026-10-24

Request: show gradient-colored sweeps at N_b=6 (start) and N_a=24 (start), name the actual cutoffs, compare every pair on a two-dimensional grid with the largest pair, draw error-threshold contours, and determine adequate N_a and N_b.

Starting revision: `5531008e175c9b169c2b1ccf410d220c74633219`, branch `intro-track-tasks`; the working tree was clean. These changes are local and uncommitted. No publication or remote update was requested.

## Implemented

- Full 6×6 grid: N_a={16,20,24,28,32,40}, N_b={4,6,8,10,12,14}.
- Reference: the largest grid pair, (40,14), over 301 saved times from 0 to 3 µs.
- Maximum trace distance of the reduced memory state, embedding smaller Fock spaces with zeros and retaining the full reference. This includes coherence and avoids relative-entropy singularities at zero populations.
- Two gradient sweep columns at the actual initial cutoffs; a separate error-grid figure with trace-distance and peak-photon contours; the original peak/steady edge profiles remain available.
- Selection checks: ≤1% maximum trace distance, ≤0.5% peak-photon error, ≤0.1% steady-photon error, and ≤0.1% maximum top-level populations in both modes. Require the candidate and every larger tested neighbor to pass; then minimize N_a N_b.
- Result: minimum tested pair **(28,12)**, with maximum state distance **0.848127%** and peak error **0.042743%**. Production **(32,12)** is retained for margin and consistency with the separately validated logical-preparation runs; its maximum state distance is **0.309932%**.
- The recommendation is for vacuum inflation at the supplied parameters. Contours interpolate sampled points. The finite reference and sampled-time maximum do not establish an exact continuum bound or convergence for arbitrary preparations.

## Files and evidence

- Source: `src/analysis.py`, `tasks/task_1_2.py`; explicit cutoff labels and result keys in `tasks/task_1_1.py`; production-margin comment in `src/config.py`.
- Figures: `figures/task_1_2_cutoff_sweeps.png`, `figures/task_1_2_error_grid.png`, `figures/task_1_2_convergence.png`; Task 1.1 figures regenerated with explicit numeric labels.
- Results: `results/task_1_2.json` and `results/task_1_2_trajectories.npz`; Task 1.1 JSON regenerated with explicit initial-cutoff metadata.
- Notebooks 02 and 03 rerun from repository root. Their setup now resolves the root without cumulative directory changes. Their displayed PNG bytes were checked against the current figure files.
- Raw memory-state trajectories are cached in `results/task_1_2_cache/`, excluded from Git. Keys include parameters, time grid, method, library versions and the model source hash. The compact delivered JSON/NPZ is sufficient to redraw all Task 1.2 figures without that cache.
- README, technical methods, claim references, AI disclosure and run comments updated.

## Verification

Environment: Python 3.12.15, Dynamiqs 0.3.7, JAX 0.12.0.1; double precision and `Tsit5(rtol=1e-8, atol=1e-10)` as in the existing production model. The previously provisioned isolated validation environment was reused; no project dependency changes were needed.

- `python -m unittest discover -s tests -v`: **7 passed**. Analytic checks cover identical states, orthogonal states with different Fock dimensions, coherence at identical photon populations, the pure-state trace-distance formula, time-shape validation, and selection guards.
- `python -m tasks.task_1_2`: **36 cases completed**, followed by a compatible-cache rerun.
- An independent SVD calculation agrees with the eigenvalue-based trace distance for representative worst-time states at (16,6), (24,14), (28,12), (32,12), and the reference.
- Every archived scalar maximum agrees with its stored trajectory. Independently enumerating the acceptance mask confirms the minimum pair (28,12) and production acceptance at (32,12).
- Original edge-sweep scalar results retained within 1e-12 absolute / 1e-10 relative tolerance, excluding hardware-dependent runtimes.
- `python -m tasks.task_1_2 --plot-only`: **passed** without simulation.
- `--quick`: **passed** on 9 compatible cached cases in a separate temporary results/figures area, using its own (32,12) reference.
- Modified notebooks 02 and 03: **executed successfully** from repository root; no stale displayed figures.
- New figures visually inspected after layout adjustment; numeric grid labels, threshold lines and legend are readable.
- `git diff --check`: **passed**.

No further work is required for this request. Other findings from the earlier Introductory Track audit were outside this truncation update and remain separate work.

## Follow-up: Task 1.1 ringing debug

The user asked whether the apparent excessive oscillation was caused by timesteps. The preceding uncommitted truncation work was preserved.

Findings:

- Large photon-number ringing is physical. The supplied challenge explicitly predicts it. Near-well linearization estimates a 0.319 µs period, consistent with observed 0.31–0.32 µs peak spacing.
- The 10-ns output grid is not the adaptive integration step. A new 1-ns-output run at the original tolerances exactly reproduces the cached 10-ns photon values at shared times.
- Tightening tolerances 100× changes photon numbers by at most 5.03e-8. Independent QuTiP BDF, with an internal step cap of 1 ns, agrees with the tight adaptive calculation to 2.44e-9 photons.
- Fixed-step Rouchon3 at 1 ns and 0.5 ns reproduces the ringing. Halving the step reduces photon error by 8.26× on their common 0–0.8 µs interval. The 1-ns case extends to 3 µs. An exploratory full-duration half-step run was deliberately stopped; the reported half-step dataset was freshly recomputed over the stated shorter interval.
- The fast log-panel tail wiggles were numerical. Old signed memory boundary values in 2–3 µs reach approximately −1.24e-7 to +1.49e-7. Tightening the solver greatly reduces these nonphysical fluctuations.

Changes:

- Task 1.1 now uses its own `INFLATION_METHOD` with rtol=1e-10, atol=1e-12. Other tasks, physical parameters, cutoffs and the original 301-point saved-output grid remain unchanged.
- The main boundary plot explicitly shades values below the conservative 1e-8 display resolution. Its raw numerical states are not altered. The separate audit plots raw signed populations rather than silently dropping their negative values on a log axis.
- Added `tasks/task_1_1_checks.py`, `results/task_1_1_checks.json`, `results/task_1_1_checks.npz`, and `figures/task_1_1_numerical_checks.png`; updated the Task 1.1 notebook, main figures/results and method documentation.
- The audit archive contains the compatible baseline trajectory from the full-grid cache and five additional trajectories computed for this debug task. They were generated through separate experiment drivers and consolidated before running the maintained audit's summarization and plot-only path. The complete recomputation command is documented; it takes several minutes.

Verification:

- All three numerical audit checks pass: output-grid invariance, independent-solver agreement, and fixed-step convergence.
- Maintained audit solver wrappers independently agree within 3.14e-11 on a fresh short 12×6 transient.
- Task 1.1 rerun with the tight solver; notebook executed successfully from repository root, including the new audit figure and check results.
- Existing 7 analytic/regression tests pass; new and updated figures visually inspected; `git diff --check` passes.
- No remaining work for this follow-up. Changes remain local and uncommitted.

## Follow-up: linear main truncation panel

The user approved a linear percentage view for the main figure, with the logarithmic view retained as a notebook diagnostic.

- The main Task 1.1 boundary panel now plots raw populations as percentages on a linear axis. Every curve has a peak marker and its maximum value annotated in the legend. A dotted line marks the 0.1% acceptance threshold.
- Added a separate `figures/task_1_1_truncation_log.png` technical diagnostic, displayed in its own section in notebook 02. It retains the conservative unresolved band and the previous log-view convention.
- Centralized the unchanged 1e-3 boundary-population acceptance value in `src/config.py`; both Task 1.1 and Task 1.2 use it. Physical parameters and solver settings are unchanged by this presentation update.
- README, technical documentation, plot metadata and notebook explanations updated. Previous descriptions of a shaded band in the main figure are superseded by this linear presentation.
- Verification: notebook 02 rerun successfully from repository root; all four displayed figures match current PNG files; main and log views visually inspected; the shared threshold matches the existing grid result; 7 tests and `git diff --check` pass.


## Follow-up: meaning and units of top-level populations

- Removed redundant “boundary” wording from Task 1.1 plot axes. Legends now name the actual Fock levels: memory 30,31 / buffer 11 for (32,12), and memory 22,23 / buffer 5 for (24,6) (start).
- The prompt asks for normalized populations; it prescribes neither fraction nor percentage formatting. The main figure uses percentages, with 0.04624 equivalent to 4.624%. Its 0.1% line is our chosen numerical tolerance, not a prompt requirement.
- Independently checked the same physical buffer level n=5 at all three cutoffs with the tight Task 1.1 method and 101 saved times over 0–0.5 µs. Maximum P(n=5): 0.0462416294 for (24,6), 0.0483514053 for (32,12), and 0.0483491043 for (40,14). The latter two agree closely: several-percent occupation of n=5 is real. A mean buffer occupation around two does not exclude occupation at five.
- The highest retained buffer level changes with cutoff. Maximum P(n=11) at (32,12) is 0.0001692121; maximum P(n=13) at (40,14) is 0.00001787784 on this short grid. Appreciable P(n=5) matters for Nb=6 because five is its artificial endpoint. These populations are indicators; the separate cutoff comparisons establish convergence.
- Updated notebook explanations and technical documentation. Re-executed notebook 02, checked all four embedded figures against current PNGs, and visually inspected the main figure.


## Follow-up: show small populations without losing the full range

- Replaced the single main truncation panel with two linear percentage panels: a full-range view and a 0–0.8 µs zoom whose vertical limit is 1.25 times the second-largest population maximum. The large curve remains included and extends above the zoom. Values and colors are identical between views; there is no individual normalization.
- Shared legend retains full-trajectory maxima, actual Fock levels and the chosen tolerance. Updated README, technical explanation and notebook caption.
- Notebook 02 executed successfully; all four embedded images match current files. Main figure visually checked for readable small curves, unclipped labels and legend placement. Simulation settings and numerical conclusions are unchanged.


## Follow-up: consistent figure presentation

Request: remove the additional full-range Task 1.1 population panel, and review every task figure's legend, labels, title and caption for a concise publication style.

- Reviewed and regenerated all 15 maintained task figures. Removed task-number headings, conclusion-like titles, numerical fit/peak reports in legends, and redundant prose in axes. Adopted shared typography, restrained grid lines, a consistent color cycle, short symbolic labels and lettered panels. Necessary fixed parameters remain with their panels; definitions, protocol details and interpretation are in captions.
- Task 1.1 again has two panels: occupations and the linear small-population view. Its initial-cutoff buffer curve exceeds that view; the caption explicitly states the omitted 4.62% peak and distinguishes n_b=5 from n_b=11. No additional full-range panel, peak labels or threshold annotation is imposed on this view.
- Wigner figures now label every time, show complex phase-space coordinates and use a common normalized color scale. A known coherent state at 1+0.5i verifies orientation and normalization; Dynamiqs' W[x,y] array is transposed for imshow's row/column convention. Row spacing was checked visually.
- Cutoff sweeps retain their requested gradients with compact numeric legends. The joint error grid uses symbolic panel headings, one shared color scale, readable cell values and a short marker legend. Contour values and selection definitions are in the caption.
- Shortened state-diagnostic and control legends; moved the preparation legend away from the transient. Captions clarify that coherent-state overlap prevents an exactly zero mixture matrix element, and that scaled stabilization curves only approximately collapse with nonzero single-photon loss. The parity-decay time is not described as an exact time to an incoherent mixture.
- Added figures/CAPTIONS.md as the caption source and synchronized the corresponding README/notebook captions. The notebooks place figures before their captions and keep numerical summaries separate. Root-path setup was made consistent so notebooks execute from the repository root without changing directories.
- Added matching PDF exports with embedded TrueType fonts; raster layers and PNG exports use 300 dpi. No model, solver, cutoff or selection criterion was changed for this presentation pass.

Verification: all five task notebooks executed successfully; all 15 embedded figures match current PNG files and each has the exact maintained caption; all 15 PNG/PDF pairs exist. All figures were inspected as a set, with individual checks of the main inflation, cutoff grid, numerical audit, preparation and Wigner layouts. A representative PDF was rasterized and inspected. 177 numeric values from previously unchanged reports reproduced within rtol=1e-9/atol=1e-10, with maximum absolute change 8.16e-11; those original reports were preserved to avoid presentation-only numerical churn. Eight analytic/regression tests pass, including the new phase-space-coordinate test.

This follow-up is complete. The earlier review history records superseded plot designs; the caption file and current sources describe the final presentation. Changes remain local and uncommitted.


## Follow-up: highest-opposite-cutoff sweeps and challenge report

- Changed the time-resolved Task 1.2 sweeps to fix N_b=14 while varying N_a, and N_a=40 while varying N_b. The trajectory and peak/steady plots now use exactly the same grid slices. The full grid, reference, selection criteria and saved numerical results are unchanged.
- Updated the maintained sweep caption, notebook 03 and technical methods; regenerated all three Task 1.2 PNG/PDF pairs from the delivered trajectory archive.
- Rewrote README.md as direct answers to completed Introductory Track Tasks 1.0(a–c), 1.1, 1.2 and 1.3(a–c). It reports the analytic checks, two-mode transient and buffer-response explanation, separate steady/peak cutoff minima, joint state criterion, parity/fidelity/purity/coherence evidence, logical preparation and its control/calibration/time cost. Figures and numerical tables are placed with their corresponding answers.
- The report distinguishes 0.99 threshold-crossing time from fidelity at 2 µs, and excludes the idealized displacement pulse from that clock. Corrected matching technical prose: parity invariance concerns dissipators (the memory jump changes sign), and coherent-state photon loss causes amplitude damping. Removed the superseded one-mode phase estimate and unsupported queued-work statement from the current technical summary.
- Validation: compared all 12 memory/buffer curve pairs in the new sweeps with the exact archived trajectories and their reported peak/steady values. Every comparison passed; the fixed-cutoff panel labels are 14/40 and the results JSON stayed byte-identical. Notebook 03 executed successfully. All 15 notebook figures and maintained captions remain synchronized. README relative links, all five table structures and 15 key numerical claims were checked against saved results; sources parse and git diff --check passes. No new simulations or changes to physical parameters were needed.

This follow-up is complete; changes remain local and uncommitted.


## Follow-up: one smooth state-convergence map

- Replaced the two-panel error grid with a single maximum reduced-memory trace-distance map. This metric includes populations and coherence. The separate peak-error map is removed; scalar peak/steady convergence plots and every numerical selection criterion are retained.
- Adopted a sequential light-to-dark blue scale, logarithmic in percent from 0.1% to 100%. The display floor does not alter raw zero/reference values. Small circles identify the 36 computed pairs; an orange square identifies selected (28,12), a black ring production (32,12), and a black star reference (40,14).
- Used shape-preserving PCHIP interpolation in probability values, along N_a then N_b, to draw the background and contour from the same fine field. The black contour is directly labelled D_max=1%. Cutoff selection still uses only computed rows.
- Added the map inline in README and explained every element: axes, metric, color scale/floor, sample markers, threshold, selected/production/reference symbols, interpolation and the saved-time interval. Updated the caption catalog, notebook 03 and technical method. README also states the parity-fit function explicitly.
- Validation: all 36 original values are preserved at their coordinates within 1e-12; the interpolated field stays within the sampled range. The rendered mesh matches that field, and the contour matches the 1% level to within 7.85e-9 percentage points (the inline-label endpoint uses polyline interpolation). The result JSON stayed byte-identical. Notebook 03 executed successfully; all 15 notebook images and captions match current exports. Sources parse, README links resolve, and git diff --check passes. PNG and PDF were visually checked.

This follow-up is complete; no physical parameters, solvers or numerical selection results changed.


## Follow-up: full-range inflation truncation check

- Restored the main Task 1.1 top-level population panel to the full 0–3 µs interval and a linear percentage range containing the complete 4.62% initial-cutoff buffer peak. Kept the two-panel figure; no additional zoom/inset.
- Restored the dotted 0.1% chosen-tolerance line. Both production monitors at (32,12) remain below it throughout inflation, while the (24,6) (start) buffer transient exceeds it. This is the intended visual cutoff check; Task 1.2 retains the independent state/observable convergence comparisons.
- Updated the README, maintained caption, notebook 02 and technical presentation notes. Regenerated PNG/PDF and executed notebook 02 successfully. Its numerical report reproduced within 1e-12 and the original report bytes were preserved. All 15 notebook images and captions match the current files; the main figure was visually checked, source/link checks pass, and git diff --check passes.

This follow-up is complete; no physical or numerical-analysis parameters changed.


## Follow-up: one chosen cutoff and non-overlapping diagnostic legend

- Standardized the reporting on chosen cutoff (32,12), consistent with Tasks 1.1 and 1.3. The map now highlights only the chosen cutoff and (40,14) reference; (28,12) is retained as the minimum tested passing result in the text/table, without a competing selected marker. Updated README, maintained caption, technical prose, notebook row label and configuration comment. Existing result-schema keys remain unchanged for compatibility.
- Moved the Task 1.1 log-view legend above the axes in two columns; it no longer crosses the tolerance line or any trajectory. Both main and logarithmic legends state the numerical tolerance explicitly in their respective units.
- Regenerated PNG/PDF exports and executed notebooks 02 and 03 successfully. Map legend entries were checked against Sampled / Chosen (32,12) / Reference (40,14). Main/log/map layouts were visually inspected. The Task 1.1 numerical report reproduced within 1e-12 and its original bytes were preserved; the Task 1.2 report stayed byte-identical. All 15 embedded notebook figures and captions match current files; source parsing, README links and git diff --check pass.

This follow-up is complete; physical parameters and numerical criteria/results are unchanged.
