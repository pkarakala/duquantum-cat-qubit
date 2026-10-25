# Submission integration — 25 October 2026

Main submission: `main/`, branch `main`, initial commit `dd52ed7`. Source comparison: `fork-XZ/`, branch `XZ-codex-intro-review`, commit `17ef9a2`. Both checkouts clean at start.

User scope: retain main as submission; audit notebooks01–08 for updates/correctness, rewrite notebook09 clearly; produce Task2 docs matching Task1, selecting only complementary verified XZ evidence. No whole-branch merge or wholesale replacement of team results.

Assignments: parent notebook09, Task2.4 presentation/figures, report assembly/navigation; earlier_notebooks_audit notebooks01–08 and matching bit-rate figure annotation; task2_docs rate/readout section drafts; task24_evidence audit and minimal enlargement evidence import.

Acceptance: every headline maps to saved data and correct observable/time window; docs/notebooks consistent; executable notebooks; valid links and math; inspect revised figures; existing relevant tests pass. Keep unsupported single-shot/hardware claims out.

Status: review complete. Delivery branch: `XZ-main`, as subsequently requested by the user. Main was fast-forwarded to `b722159` during review to incorporate PR #17's new linear readout-validation figure. XZ remains unchanged.

## Submission map

- `README.md`: report entry points.
- `docs/task_1.md`: retained Task 1 report.
- `docs/task_2.md`: consolidated Task 2 answers, following Task 1's result/definition/figure-caption structure.
- `docs/TECHNICAL.md`: model, methods, source/data map and reproduction. The obsolete rate/readout redirect files were removed at the user’s request; all final Task 2 answers are in `docs/task_2.md`.
- `notebooks/01–05`: Task 1 calculations; only notebook 05's broken technical link changed.
- `notebooks/06–08`: merged Task 2.1–2.3 analyses retained, with surgical correctness/math repairs.
- `notebooks/09_task_2_4_better_readout.ipynb`: rewritten (a)–(d), executes saved evidence and regenerates its figures.
- `src/`, `tasks/`: supplied-model implementation, validated direct trajectories and rate fits.
- `research/s2/`, `results/s2/`: team's spectral, circuit, pulse and optimization studies. Original numerical records retained.
- `results/task_2_4_enlargement*`: selected XZ evidence with original execution metadata and immutable source links. No solver stack or broad exploratory campaign imported.

## Changes and scientific decisions

Main's resonant-shaping narrative remains central. It now reports conditional-mean information and recovered amplitude loss directly, including the full observation window. A compact enlargement comparison supplies the stricter undriven-storage-rate criterion and complete-cycle logical populations. Both proposals are in part (c); mechanisms and limits are in (d).

Corrected the factor-of-two distinction between observable relaxation and event waiting time; finite-window plateau claims; first-order versus higher-order circuit effects; the sign of occupation-dependent exchange corrections; the optimizer's seeded initialization and 90%-bound initial amplitude; unsupported fidelity and universal detuning claims. The matched shorter-pulse cutoff check is distinguished from the unvalidated-cutoff 2-µs examples. Removed no raw source results.

No missing XZ scientific updates were found through 2.3. Main adds two valid inflation-purity diagnostics to Task 1.3(a). Main's black Wigner-origin markers were left intact; the dark-grey difference from XZ is cosmetic.

## Verification

- Fresh saved-data execution of notebooks 06–09 passes. Notebook 09 reconstructs information and logical probabilities from raw imported observables; no new quantum simulation was run.
- Main's complete test suite: **19 tests pass** (`python -m unittest discover -s tests -v`), log `/tmp/main-submission-tests.log`.
- All four imported cycles reproduce their information budgets and final wrong-logical populations; logical populations plus leakage equal the recorded trace.
- All notebook code parses, no stored error outputs, and **60 local report/notebook links resolve**. All five notebook 09 embedded PNGs match the published figures exactly.
- GitHub Markdown API preserves **241 report, 20 technical-note, 112 notebook 09, and 59/47/35 notebook 06/07/08 formulas**. Fenced report math was also checked in equivalent display syntax; corrections remove GFM escape corruption.
- Revised plots inspected visually; legends/captions and simulation windows match. Notebook outputs provide standard PNG MIME alongside centered HTML presentation.
- `git diff --check` passes. Original Task 1 numerical data and figures are unchanged.

## Remaining scientific limits

Conditional-mean signal metrics do not establish single-shot fidelity. The 2-µs pulse examples lack a matching larger-cutoff replicate; the separate 0.5-µs comparison has one. Circuit calibration is a short, closed-system diagnostic; corrected-circuit rare switching and full protocols remain unverified. The selected imported enlargement result is an ideal cubic-model witness, not a global optimum.

The user subsequently requested publication on `XZ-main`. The reviewed changes are committed together on that branch, based on main commit `b722159`; the original XZ checkout is unchanged. Git history records the delivery commit.

## Final documentation cleanup

Removed the two obsolete redirect files after confirming that Task 2.1–2.4 are fully consolidated and no maintained links reference those files. The current reports are `docs/task_1.md` and `docs/task_2.md`.
