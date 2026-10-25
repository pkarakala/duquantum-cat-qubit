# Task 2.4 — circuit-aware readout optimization

Status: curated Task 2.4(a–d) study complete locally. The separate broader
cloud search remains under its own campaign record. User requested a deep, exploratory and rigorous completion of all
four capstone parts. Starting revision: `b1c331a` on `XZ-codex-intro-review`; working
tree was clean. Preserve all prior numerical deliverables and figure conventions.

Maintained implementation belongs in `src/` and `tasks/`; deliver results,
figures, an executed notebook, concise README answers and a detailed report.
Exploration, intermediate inputs and verification logs continue in
`/tmp/cat-qubit-capstone/`. Use the existing validated Python 3.12 environment.

Acceptance criteria:

- Derive the lab-frame memory drive and its rotating-frame quadrature; audit pump
  phase/sign conventions. Identify resonant higher-order circuit terms and the
  chosen approximation's domain. Do not silently invent first-order Kerr terms.
- Sweep drive strength and compute full two-mode contrast and observable bit-flip
  relaxation. Check physical target alpha=2.1 and smaller cats where independent
  time-domain validation is tractable. Recheck cutoffs, eigenmode residuals,
  integration and source/configuration provenance.
- Explore and demonstrate a control/parameter strategy with an explicit comparator,
  improvement criterion and bit-flip disturbance check. Distinguish static rates,
  pulse errors, field settling and actual measurement performance.
- Use independent calculations and meaningful tests, show unsuccessful alternatives
  when they clarify the trade-off, and state limitations of the circuit and
  measurement models. Never claim a numerical resolution or fidelity not supported
  by the saved evidence. Delivery state remains separate from completion.

During the exploration, a concurrent session committed Wigner-origin styling
(`999257d`) and continued modifying its assets. Those changes are outside this
work's ownership and are preserved. No previous Wigner plot is regenerated here.
The initial dense Hamiltonian implementation was stopped and replaced by an
exact sparse-diagonal representation before production calculations; this
changes storage/performance, not the quantum model. Early small-cutoff rates
are exploratory only: the nominal alpha=2.1 driven rate changes by 1.9% between
(24,8) and (32,12), requiring stricter buffer-cutoff checks before conclusions.

Parallel numerical audit (user explicitly authorized all resources): circuit,
rate and measurement agents own distinct source/test/evidence files. The
reference environment is Python 3.12 with PyMETIS 2025.2.2 installed. METIS
nested dissection substantially reduces sparse LU fill; both original-matrix
eigenpair residuals and independent COLAMD comparisons remain required.

Current candidate distinction: alpha_ro=2.6, epsilon_Z/g2=0.1 is compared with
undriven alpha0=2.1 storage. The optional 0.25 fast point is compared with weak
readout and must never be described as preserving undriven storage Gamma_X.
Full-cycle comparisons include both ramps and final relaxation. The information
functional is a conditional-mean shot-noise reference, not measured fidelity.

The two obsolete parent COLAMD 34x14 jobs were stopped after launch-time, cwd
and parent-process matching: PID42325/session22813 and PID43011/session5694
both returned exit143. Completed METIS results supersede them. No completed
evidence was removed. This freed over30GB of compressed/swapped working memory.

A concurrent session has added a separate bounded/cloud campaign and dedicated
Task2.4 overview. Preserve those sources and their ownership. The present
scientific study is tasks/task_2_4.py, report docs/task_2_4_optimization.md,
notebook09 and the task_2_4 numerical archives. The complete shared test suite
passed112 tests before the last circuit parity test/independent-rate CLI edits;
a fresh final run remains required after source stabilizes.

Final acceptance (2026-10-25): all four scientific parts are answered in
`docs/task_2_4_optimization.md`; notebook09 is executed from a fresh validated
kernel. `tasks/task_2_4.py` has a working study CLI and plot-only CLI. The main
JSON/43MB NPZ, independent rate and measurement traces, three validation JSONs,
six PNG/PDF pairs and 304-frame Wigner GIF are delivered. README, dedicated
2.4 overview, caption catalog and technical record are updated. Previous-task
figures/data and the concurrent cloud campaign are preserved.

Primary alpha_ro2.6/epsilon_Z/g2=.1: Gamma_X40x16=2.03511607865e-7/us;
last static memory/buffer increments 0.6992%/0.5301%. Full 47.3996573-µs cycle38x16
has Pwrong 7.94834127158e-6, versus matched idle 9.05879904840e-6. Cycle increment
36x14→38x16 changes Pwrong 0.7748%; tightening integration changes Pwrong 5.06e-14
absolute. The same mean-signal target takes 2.32534× less total time than weak
readout. The optional .25 cycle is 10.3944× faster but does not preserve undriven
storage Gamma; its static-rate cutoff qualification remains explicit.

All 124 shared repository tests pass. Independent physics and rate reviews clear
signs, factors, rate conventions and numerical claims. Raw arrays, logical
projector partition, information integration, strict finite JSON and artifact
links pass. GitHub's renderer preserves 198 report formulas, 46 notebook formulas,
11 overview formulas, 3 new README formulas and 52 new caption formulas. Figures
were visually inspected; a late mathtext-brace issue was corrected before final
export. Final protocol time is linear; final validation uses point estimates and
shared physical times. Density matrices are never interpolated for animations.

Metadata declarations were completed for alpha_storage, corrected-model losses,
and shaper configuration/dependencies. Compatible earlier numerical caches were
imported with original executed metadata and file/array hashes preserved, rather
than falsely attributing execution to later reporting source. Public cache hits
were verified with numerical solvers blocked; the complete cached study finishes
without a numerical solve. The redraw branch is separately verified against
simulation calls. All parent/child scientific numerical workers are complete;
the concurrent remote pulse-search campaign is a separate ongoing exploration.

Model limits remain material: the information functional is a conditional-mean
shot-noise reference, not single-shot fidelity; corrected-circuit static rates
retain 2.49%/4.69% cutoff variations; full-phase signal sensitivity is computed,
while full-phase Gamma, corrected full cycles and dressed-bath GHz validation
are not claimed. No commit or push was requested for this capstone work.

Post-delivery recheck requested by user (“check”):

- Reproduced all headline cycle metrics and the matched idle comparison directly
  from raw NPZs. No headline numerical discrepancy was found.
- Found and fixed normalized trace diagnostics in the independent rate helper.
  Three raw-output BDF reruns retain the original normalized archive separately;
  raw trace drift is at most1.16e-14 and fitted rates change below9.1e-13 relative.
  Supplied-spectrum configurations are now validated before integration.
- Found an invisible nearest-shift eigenmode counterexample. Certified queries
  now reject negligible memory-observable loading, and all APIs disclose that
  a single Ritz candidate does not prove global spectral dominance. All five
  blue sweep points were freshly certified; their rates agree within1.45e-9
  relative. Stored headline-mode loading passes the new guard.
- Strengthened cache source identities with numerical module dependencies.
  Regression tests cover exchange assembly, operators and inverse/certificate
  helpers. Compatible original numerical caches retain native execution hashes
  and arrays; all nine certified spectrum lookups and the full refreshed study
  were verified with numerical solvers blocked.
- Found a material model-scope gap: mixed ATS-pump/microwave counter-rotating
  commutators yield terms of the retained combined order. They are now derived
  explicitly in the report and identified as omitted in the pump-only model.
  Their effect on rare Gamma_X is untested. The ideal cubic strategy remains
  numerically supported; preservation for a complete circuit/control model is
  NOT established. Source/report/overview/notebook/captions state this scope.
- Defined both ATS flux biases explicitly and defined A_s in notebook captions.
  Corrected stale cloud status: downloaded record09:00UTC has104 completed cases,
  two timeouts and no active workers; draft interpretation remains separate.
- Fresh complete suite:131 tests pass. Refreshed metrics, saved data, figure
  pairs/GIF and executed notebook retain the same headline ideal-model values.


## Merged synthesis revision

The canonical final report now integrates both studies around a selected
enlargement/read/restore protocol and supporting pulse-termination evidence.
See `reviews/task_2_4_synthesis_evaluation.md` for the clarity, innovation,
presentation and selection decisions. The updated report has13 pages and7
scientific figures; notebook10 executes seven code cells. New diagnostics are
computed from saved outputs, with116 input hashes verified. No new quantum
computation or untested hybrid performance claim was introduced.
