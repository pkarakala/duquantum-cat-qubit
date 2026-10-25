# Task 2.4 cloud execution — 2026-10-25

Status: main campaign and independent backend check running. This is an
execution handoff, not final scientific acceptance of Task 2.4 results.

## Scope and ownership

User requested autonomous parallel Task 2.4 research on Vultr, a separate
Task 2.4 README, setup followed by leaving jobs running, and a project duration
under four hours. The dedicated entry point is `docs/task_2_4_README.md`; the
main README only links to it. Existing circuit, measurement, optimization,
spectral and capstone-helper work was already active in another session and
was preserved. This work adds isolated pulse, dephasing, semiclassical-design,
auditable-spectrum, campaign, reporting and cloud-operation modules/tests.

Frozen source: `/tmp/cat-qubit-cloud/snapshot/`, uploaded to
`/opt/duquantum/task24/`. Base Git commit:
`921505a307cd5cc1757bd42bacb020a4eb3d9d73`; uncommitted Task 2.4 additions are
identified by `SNAPSHOT.json` and the campaign's source hashes. No Git history,
SSH credentials or unrelated user files were uploaded. Changes in the current
workspace do not alter the frozen numerical code. The independent Dynamiqs
tool was added outside the frozen src/tasks hash set and records its own
supplemental source identity. The maintained run script now defaults to the
measured 12-worker layout; the original frozen bootstrap started with seven.

## Provisioning and authorization

The user approved up to $20 for the first 24 hours, including using the existing
`duquantum` key. Initial New York VX1 instance
`e7f95848-e516-4184-a9d2-524af857f77f`, 144.202.0.107, never became reachable;
its console failed and restart returned a Vultr internal error. No research
files were uploaded. The user explicitly approved permanent deletion of that
empty instance and replacement. Vultr confirmed termination.

Replacement: `4770abe8-c360-499e-85bb-f86e5f443957`, **66.42.119.3**, Chicago,
16 dedicated vCPUs / 8 physical AMD EPYC Milan cores with SMT, 64 GB RAM,
320 GB local NVMe, Ubuntu 24.04. Displayed price $0.658/hour; no paid backups,
DDoS or additional storage. The pre-existing Atlanta instance was untouched.
Its existing SSH key was selected. A normal authorized login using the
provider-issued server credential established a private local SSH control
connection; the temporary credential file was deleted and the display hidden.
No password or key was changed, and no credentials enter the source/results.

## Executed checks

- Independent circuit audit checked pump signs, drive phase, RWA coefficients,
  exact cat projectors and corrected-model idle behavior. Mean-force
  cancellation is explicitly distinguished from exact dark-state cancellation.
- Initial performance probes supported CPU hardware and serialized large sparse
  factorizations rather than an unbenchmarked GPU purchase.
- The actual cloud environment installed Python 3.12.3, NumPy 2.5.4, SciPy
  1.18.1, QuTiP 5.3.1, Dynamiqs 0.3.7, JAX 0.12.0.1 and PyMETIS 2025.2.2.
- **117 repository tests passed on the cloud** in 9.154 seconds.
- Production-cutoff 32×12 smoke completed; peak process RSS 548472 KiB.
- The supplemental Dynamiqs checker passed four local tests and an actual
  32×12 short-pulse comparison: maximum buffer-field difference 1.98e-9,
  wrong/leakage difference 1.20e-10. These smoke numbers are not a convergence
  certificate for the eventual selected protocols.
- PDF/report tests include empty and populated campaigns, executed notebooks,
  page-bound checks and visual rendering. Reports stay explicitly DRAFT.

Evidence: `/tmp/cat-qubit-cloud/` includes three independent audits, numerical
probes, local test logs, the frozen snapshot, deployment screenshots, copied
cloud bootstrap log and supplemental-check logs. Cloud environment records and
case metadata are retained with the campaign outputs.

## Campaign and timing

The main run began **08:11:40 UTC**, with an absolute compute deadline of
**11:11:40 UTC / 07:11:40 EDT**. Setup plus this maximum run duration remains
under four hours from the request. Per-case timeout is 1200 seconds; systemd
adds a bounded cleanup/report allowance. Stopping computation does not delete
the VM or stop provider billing.

The initial manifest contains 55 prioritized cases, expanded with three
semiclassical proposals and selected validation/robustness cases (106 observed
after promotion). Cases compare tuned constant, raised-cosine, Gaussian and
smooth signed build/hold/deplete pulses at fixed alpha, with exact matched
constant controls. They separately track mean-field information/SNR²=4I,
orthonormal logical populations, leakage, residual photons and matched idle
excesses. Static near-zero spectra retain modal overlaps and residuals rather
than asserting global dominance. Even-cat controls separate phase rotation,
reduced-memory coherence magnitude and leakage, with memory-loss-off controls.
Circuit/robustness cases use the same corrected idle reference.

Measured CPU/RAM use justified resuming with **12 one-CPU workers**, numerical
thread caps of one and at most one spectral factorization. The original absolute
deadline was retained; completed cases were reused and only unfinished work
restarted. Final service: `duquantum-task24-fast`. At 08:22 UTC, 58 cases had
completed and 12 workers were active, with no failed cases reported then.

`duquantum-task24-crosscheck` independently runs up to two selected production
references through Dynamiqs, using CPU lanes 14–15 and a 20-minute service
limit. Its explicit wait/pending status is not a passing result. It writes
`independent_validation/` without modifying the frozen models.

## Collection, reporting and handoff

Cloud output: `/opt/duquantum/task24/results/task_2_4_campaign/`.
Local mirror: `results/task_2_4_campaign/`. A detached collector downloads every
60 seconds, bounded to 3.5 hours, and an idle-sleep hold ends with it. Local
`collection.log` records transfer outcomes. Main systemd computation survives
closing SSH or losing the local connection. Final report-marker collection
ends the collector; raw and incomplete cases remain visible.

The automated PDF and notebook under `report/` are execution drafts. Initial
drafts already exist; the service regenerates them on exit. Scientific acceptance
still requires the actual convergence comparisons, independent-reference
results, defensible rate interpretation and a fair Pareto assessment. No claim
of improved fidelity, a universal optimum or preserved physical-target bit-flip
rate has been made. Negative findings and unresolved rates remain valid outcomes.

Use the dedicated README for exact status/stop/reproduction commands. Review
and preserve the downloaded data before any later VM deletion. No commit or
push was performed by this cloud setup session.

## Progress check — 10:41 UTC, 2026-10-25

The main campaign finished at 09:00 UTC, after about 49 minutes from its initial
launch: 104 completed cases, two per-case timeouts, no active main workers.
The two timed-out cases are constant and raised-cosine pulses at ratio 0.5,
4-us duration and the largest joint cutoff (40,14). Other separate cutoff
increases, tighter integrations and robustness cases completed. No original
timeout is relabelled as a success.

Both selected (32,12) independent Dynamiqs checks completed and passed all
observable, waveform and state-health criteria. The final main PDF/notebook
generated successfully, and the collector downloaded all final main outputs
at 09:01 UTC before stopping. The VM stayed allocated and billed.

At the progress request, 30 minutes remained before the original absolute
compute deadline. Two supplementary Dynamiqs (40,14) jobs were started at
10:46 UTC, with separate 900-second systemd limits, to complete the missing
joint-cutoff evidence using the already cross-validated backend. They compare
physical observables to the completed (32,12) references, monitor the new Fock
boundaries separately, and explicitly label the comparison as combining cutoff
and backend changes. The script passed an actual short-time (32,12)→(40,14)
smoke; full-duration results are pending. Frozen src/tasks and original records
remain unchanged. A bounded supplemental collector transfers outputs every
30 seconds and stops after both results arrive or 17 minutes.

Units: `duquantum-cutoff-constant` and `duquantum-cutoff-smooth`.
Outputs: `results/task_2_4_campaign/supplemental_cutoffs/`.
The report remains DRAFT pending scientific interpretation and review.


## Final synthesis — 11:20 UTC, 2026-10-25

Both supplemental40x14 Dynamiqs comparisons completed and passed before the
original compute deadline. Relative final wrong-population differences are
about0.0172% for both selected pulses. Original104-success/two-timeout records
are preserved. Both same-cutoff independent comparisons also passed.
All study systemd units were inactive when checked at11:14 UTC; no running
research process was returned. The allocated VM remains billed; it was not deleted.

The main outputs, supplemental outputs and exact source archive are local.
All66 archived execution source files match their manifest hashes. The final
scientific synthesis is docs/task_2_4_final.md, with PDF under output/pdf/,
executed notebook10 and dedicated docs/task_2_4_README.md. Final claims retain
model, spectral, cutoff and measurement qualifications; no global optimization
or single-shot fidelity claim is made. Independent review evidence is retained
under reviews/task_2_4_final_*.md. The embedded stale spectral data were reconciled
without changing the numerical headlines or historical execution provenance.

Validation:131 repository tests pass; notebook10 executes all six code cells
without errors; PDF has12 pages, all rendered, with zero missing glyphs,
out-of-page text or overfull boxes. No commit or push was performed.


## Merged synthesis revision

The canonical final report now integrates both studies around a selected
enlargement/read/restore protocol and supporting pulse-termination evidence.
See `reviews/task_2_4_synthesis_evaluation.md` for the clarity, innovation,
presentation and selection decisions. The updated report has13 pages and7
scientific figures; notebook10 executes seven code cells. New diagnostics are
computed from saved outputs, with116 input hashes verified. No new quantum
computation or untested hybrid performance claim was introduced.
