# Task 2.4: final report and reproduction

This file is the dedicated entry point for Task 2.4(a–d).

- [Final scientific PDF](../output/pdf/task_2_4_final_report.pdf)
- [Main report in Markdown: parts (a)-(d)](task_2_4_report.md)
- [Supporting appendices in Markdown](task_2_4_appendices.md)
- [Full PDF source](task_2_4_final.md)
- [Executed synthesis notebook](../notebooks/10_task_2_4_final_synthesis.ipynb)
- [Executed detailed study](../notebooks/09_task_2_4_optimization.ipynb)
- [Evidence index with source hashes](../results/task_2_4_final_summary.json)
- [Detailed derivations and local validation](task_2_4_optimization.md)
- [Reference audit and final (a-d) storyline](../reviews/task_2_4_reference_review.md)

**Proposal: enlarge, measure, restore.** Increase the cat amplitude from 2.1 to 2.6
using the buffer drive, read at $\epsilon_Z/g_2=0.1$, then restore 2.1 and recover.
The main report follows a single argument: derive the controls, establish the
fixed-size trade-off, test enlargement, then check speed and protection separately.
Circuit refinements and alternative pulse studies are supporting appendices.

At the same ideal homodyne information target, the complete cycle takes
**47.40 µs versus 110.22 µs** for the specified weak reference. Its estimated
static logical relaxation rate is **0.529 times undriven storage**; final
wrong-logical population is $7.95\times10^{-6}$.

The complete-cycle result uses the ideal cubic two-mode model. The signal target
is not measured single-shot fidelity. Corrected-circuit full-cycle validation
remains open. The [reference review](../reviews/task_2_4_reference_review.md)
records what was borrowed from the supplied (a-b) text, corrected and excluded.

## Reconstruct the delivered analysis

Use Python 3.12 from the repository root. Key solver versions are pinned
in `requirements.txt`; detailed execution versions remain in the saved outputs.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tools/check_task_2_4_reference.py
MPLBACKEND=Agg python tools/plot_task_2_4_baseline.py
MPLBACKEND=Agg python tools/plot_task_2_4_drive_tradeoff.py
MPLBACKEND=Agg python tools/plot_task_2_4_protocol_summary.py
MPLBACKEND=Agg python tools/plot_task_2_4_campaign_synthesis.py
python tools/synthesize_task_2_4.py
python tools/export_task_2_4_markdown.py
MPLBACKEND=Agg python tools/plot_task_2_4_model_validation.py
jupyter nbconvert --execute --to notebook --inplace \
  notebooks/10_task_2_4_final_synthesis.ipynb
```

The synthesis recomputes information integrals and final logical populations
from saved trajectories, checks the authoritative spectral metadata, verifies
independent/supplemental passes and records source SHA-256 hashes. It does not
rerun the expensive quantum study. The synthesis notebook can be run from the
repository root or its notebook directory. Notebook 09 provides the deeper
curated calculation; notebook 10 assembles the final evidence and figures.

For PDF typesetting on macOS:

```bash
brew install pandoc tectonic
python -m pip install pymupdf
python tools/build_task_2_4_report.py \
  --workdir output/task_2_4_pdf_review
```

Pandoc and Tectonic provide real LaTeX equations and embedded fonts. The builder
prefers verified vector PDF figures, renders every page and checks glyphs,
page bounds and overfull boxes. Review the rendered pages as well as its
`qa.json`. The delivered build review is under
[`output/task_2_4_pdf_review/`](../output/task_2_4_pdf_review/).
These build dependencies are separate from the simulation requirements.

The original cloud source is preserved in
`results/task_2_4_campaign/source_snapshot.tar.gz`; all 66 source hashes match
the execution manifest. Extract into a separate directory to inspect or rerun
that historical implementation without replacing the maintained source.

## Rerun simulations deliberately

```bash
python -m tasks.task_2_4 --plot-only
python -m tasks.task_2_4
```

The first command redraws the curated study from delivered JSON/NPZ. The second
runs/resumes the full study using source- and parameter-qualified caches.
Long reference cycles and rare-mode solves can take substantial CPU time;
the saved outputs are sufficient for the final synthesis.

Run a new broad campaign in a **new directory** from a fixed checkout:

```bash
python -m tasks.task_2_4_campaign prepare \
  --output results/task_2_4_new_campaign --preset research
python -m tasks.task_2_4_campaign run \
  --output results/task_2_4_new_campaign --workers 12 \
  --spectral-workers 1 --cpus-per-worker 1 --hours 3 --job-timeout 1200
python -m tasks.task_2_4_campaign_report \
  --output results/task_2_4_new_campaign
```

The scheduler validates its frozen source hashes, resumes completed cases and
bounds workers and runtime. Do not relabel original outputs as executions of
later source edits. The automatic campaign report remains a historical draft;
`docs/task_2_4_final.md` is the reviewed synthesis.

## Evidence and remaining limits

The main cloud campaign records **104 completed jobs and two timeouts**. Both
selected same-cutoff independent Dynamiqs comparisons passed. Both formerly
missing joint-cutoff checks also passed in separate supplemental runs. The
original scheduler timeout records are preserved.

| Evidence | Location |
|:--|:--|
| Curated trajectories and scalar results | `results/task_2_4.json`, `task_2_4_trajectories.npz` |
| Rare-mode and raw time-domain checks | `results/task_2_4_spectral_validation.json`, `task_2_4_rate_trajectories.npz` |
| Measurement and circuit checks | `results/task_2_4_measurement_validation.json`, `task_2_4_circuit_validation.json` |
| Pulse trajectories, parameters and source hashes | `results/task_2_4_campaign/jobs/` |
| Independent integration | `results/task_2_4_campaign/independent_validation/` |
| Supplemental joint cutoffs | `results/task_2_4_campaign/supplemental_cutoffs/` |
| Final source index | `results/task_2_4_final_summary.json` |
| Independent final audits | `reviews/task_2_4_final_curated_audit.md`, `reviews/task_2_4_final_campaign_audit.md` |

Finite-cutoff increments are empirical checks, not rigorous error bounds. The
selected population-relaxation mode is physically loaded but lacks a full-spectrum
global-dominance proof. Local output-noise checks do not establish full-cycle
single-shot fidelity. The report states the circuit correction order,
calibration assumptions, asymmetry and unresolved physical-model uncertainty.
The explicitly labeled normalized legacy rate archive is historical only;
the final analysis uses the raw, unnormalized trajectory archive.

The replacement Vultr instance `66.42.119.3` (Chicago, 16 vCPUs, 64 GB RAM)
has no active study workers as checked at finalization. Results are downloaded.
**The VM remains allocated and billed at the displayed $0.658/hour until deleted.**
Its failed New York predecessor was deleted with explicit authorization.
No deletion of the result-bearing replacement is implied by stopping computation.

## AI-assistance disclosure

Codex and parallel AI agents assisted with circuit derivation, implementation,
candidate design, cloud execution, independent audits and report preparation.
Results were checked against saved trajectories, independent solvers, cutoff
changes and physical conventions. The submitting team remains responsible for
understanding and defending every result, as required by the challenge's AI policy.
