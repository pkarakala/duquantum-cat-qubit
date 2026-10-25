"""Regenerate an explicitly draft scientific report from finished campaign jobs.

python -m tasks.task_2_4_campaign_report --output results/task_2_4_campaign

This reader never runs simulations or upgrades successful execution into a
convergence certificate. All generated files stay inside OUTPUT/report/.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


PHYSICS = ("profile", "alpha", "ratio", "duration", "idle", "edge_fraction",
           "hold_ratio", "tail_ratio", "knots", "order", "g2", "kappa_a",
           "kappa_b", "drive_scale", "phase", "efficiency", "control_g2")
PHYSICS += ("circuit_correction", "phase_order", "correction_scale", "static_cosine")
MATCHED = tuple(k for k in PHYSICS if k not in
                ("profile", "edge_fraction", "hold_ratio", "tail_ratio", "knots"))
COLORS = {"constant": "#0072B2", "raised_cosine": "#D55E00",
          "gaussian": "#009E73", "build_hold_deplete": "#CC79A7"}
COLUMNS = ["id", "profile", "alpha", "ratio", "duration", "idle", "Na", "Nb",
           "order", "effective_exchange_order", "phase", "drive_scale", "g2", "control_g2",
           "kappa_a", "kappa_b", "efficiency", "rtol", "atol", "step", "circuit_correction",
           "phase_order", "correction_scale", "static_cosine", "cycle_time_us", "information",
           "fixed_real_information", "snr_squared", "wrong_population",
           "readout_excess_wrong_population", "leakage", "excess_buffer_population",
           "buffer_population", "post_pulse_information", "max_top2_a", "max_top_b",
           "max_trace_error", "final_min_eigenvalue", "interpretation"]
ROOT = Path(__file__).resolve().parents[1]
FRONT_GROUP = ("alpha", "idle", "Na", "Nb", "order", "phase", "drive_scale", "g2",
               "control_g2", "kappa_a", "kappa_b", "efficiency", "rtol", "atol", "step",
               "circuit_correction", "phase_order", "correction_scale", "static_cosine")


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n")


def _worst(metrics, name):
    value = metrics.get(name)
    return max(value) if isinstance(value, list) and value else value


def _load_jobs(output, manifest):
    records, states = [], []
    for item in manifest.get("jobs", []):
        folder = output/"jobs"/item["id"]
        status = "pending"
        try:
            if (folder/"status.json").exists():
                status = json.loads((folder/"status.json").read_text()).get("status", "unknown")
            if (folder/"summary.json").exists():
                result = json.loads((folder/"summary.json").read_text())
                if result.get("execution_status") == "completed" and result.get("job") == item:
                    records.append({"job": item, "metrics": result["metrics"], "folder": folder})
                    status = "completed"
        except (ValueError, KeyError, OSError):
            status = "unreadable_or_incomplete_record"
        states.append({"id": item["id"], "kind": item["kind"], "status": status})
    return records, states


def _pulse_row(record):
    m, item = record["metrics"], record["job"]
    p = dict(item["parameters"], **m)
    return dict({key: p.get(key) for key in COLUMNS},
        id=item["id"], profile=p.get("profile", "constant"),
        effective_exchange_order=p.get("effective_exchange_order", p.get("order")),
        cycle_time_us=m.get("cycle_duration_us"), information=m.get("information_at_pulse_end"),
        fixed_real_information=m.get("fixed_real_quadrature_information_at_pulse_end"),
        snr_squared=m.get("snr_squared_at_pulse_end"),
        wrong_population=_worst(m, "final_wrong_population"),
        readout_excess_wrong_population=_worst(m, "readout_excess_wrong_population"),
        leakage=_worst(m, "final_leakage"),
        excess_buffer_population=_worst(m, "excess_final_buffer_population"),
        buffer_population=_worst(m, "final_buffer_population"),
        post_pulse_information=m.get("post_pulse_information_same_lo"),
        interpretation="Executed trajectory; convergence and physical review pending")


def pareto_ids(rows):
    """Exact exploratory nondominance; signed raw results are never clipped."""
    keys = ("information", "cycle_time_us", "wrong_population", "leakage", "excess_buffer_population")
    eligible = [r for r in rows if all(r.get(k) is not None and np.isfinite(r[k]) for k in keys)]
    values = np.array([[-r["information"], r["cycle_time_us"], r["wrong_population"],
                        r["leakage"], r["excess_buffer_population"]] for r in eligible])
    return [r["id"] for i, r in enumerate(eligible)
            if not any(np.all(v <= values[i]) and np.any(v < values[i])
                       for j, v in enumerate(values) if i != j)]


def _identity(record, keys):
    p = dict(record["job"]["parameters"], **record["metrics"])
    return json.dumps({k: p.get(k) for k in keys}, sort_keys=True)


def _matched_comparisons(pulses):
    comparisons = []
    for record in pulses:
        row = _pulse_row(record)
        if row["profile"] == "constant":
            continue
        matches = [other for other in pulses
                   if other["metrics"].get("profile", "constant") == "constant"
                   and _identity(other, MATCHED+("Na", "Nb")) ==
                   _identity(record, MATCHED+("Na", "Nb"))]
        result = {"candidate": row["id"], "profile": row["profile"],
                  "ratio": row["ratio"], "duration": row["duration"],
                  "cutoffs": [row["Na"], row["Nb"]], "order": row["order"],
                  "claim_status": "Unproven: convergence and physical review are required"}
        if matches:
            baseline = max(matches, key=lambda r: r["metrics"].get("information_at_pulse_end", 0))
            base = _pulse_row(baseline)
            result.update(comparator=base["id"],
                comparison="Same physical settings, elapsed time, peak bound and cutoffs",
                information_ratio=(row["information"]/base["information"]
                                   if base["information"] else None),
                wrong_population_difference=row["wrong_population"]-base["wrong_population"],
                leakage_difference=row["leakage"]-base["leakage"],
                excess_buffer_difference=row["excess_buffer_population"]-base["excess_buffer_population"])
        else:
            result.update(comparator=None, comparison="No exact matched constant comparator completed")
        comparisons.append(result)
    return comparisons


def _validation_comparisons(pulses):
    groups = {}
    for record in pulses:
        groups.setdefault(_identity(record, PHYSICS), []).append(record)
    comparisons = []
    for group in groups.values():
        if len(group) < 2:
            continue
        reference = max(group, key=lambda r: (r["metrics"].get("Na", 0)*r["metrics"].get("Nb", 0),
                                              -r["metrics"].get("rtol", 1)))
        ref = _pulse_row(reference)
        for record in group:
            if record is reference:
                continue
            row = _pulse_row(record)
            comparisons.append({"case": row["id"], "reference": ref["id"],
                "profile": row["profile"], "ratio": row["ratio"], "duration": row["duration"],
                "cutoffs": [row["Na"], row["Nb"]], "reference_cutoffs": [ref["Na"], ref["Nb"]],
                "information_relative_difference": abs(row["information"]/ref["information"]-1)
                    if ref["information"] else None,
                "wrong_population_absolute_difference": abs(row["wrong_population"]-ref["wrong_population"]),
                "leakage_absolute_difference": abs(row["leakage"]-ref["leakage"]),
                "status": "Comparison available; acceptance and physical review pending"})
    return comparisons


def _footer(fig, number):
    fig.text(.07, .025, "DRAFT - executed evidence is not a convergence certificate", size=8, color="#555555")
    fig.text(.93, .025, str(number), ha="right", size=8, color="#555555")


def _text_page(pdf, title, paragraphs, number):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(.07, .94, title, size=17, weight="bold", va="top")
    y = .885
    for text in paragraphs:
        if text.startswith("EQ:"):
            fig.text(.09, y, text[3:], size=13, va="top")
            y -= .052
        else:
            lines = textwrap.wrap(text, width=97, break_long_words=False, break_on_hyphens=False)
            fig.text(.07, y, "\n".join(lines), size=10, va="top", linespacing=1.5)
            y -= .020*len(lines)+.026
    if y < .07:
        plt.close(fig)
        raise ValueError("Draft report text exceeds its page; shorten or split the content")
    _footer(fig, number)
    pdf.savefig(fig)
    plt.close(fig)


def _plot_tradeoffs(rows, folder):
    fig, axes = plt.subplots(1, 3, figsize=(8.5, 4.5), layout="constrained")
    for profile, color in COLORS.items():
        group = [r for r in rows if r["profile"] == profile and r["information"] is not None]
        if not group:
            continue
        axes[0].scatter([r["cycle_time_us"] for r in group], [r["information"] for r in group],
                        color=color, label=profile.replace("_", " "), s=26)
        axes[1].scatter([r["information"] for r in group], [r["wrong_population"] for r in group],
                        color=color, s=26)
        axes[2].scatter([r["information"] for r in group], [r["excess_buffer_population"] for r in group],
                        color=color, s=26)
    for ax, title in zip(axes, ("Information versus elapsed time", "Stored-bit disturbance", "Residual buffer photons")):
        ax.set_title(title, size=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=.18)
    axes[0].set(xlabel="Pulse + recovery time (us)", ylabel="Mean-signal information I")
    axes[1].set(xlabel="Mean-signal information I", ylabel="Final wrong logical population")
    axes[2].set(xlabel="Mean-signal information I", ylabel="Final photons minus matched idle")
    for ax in axes:
        ax.xaxis.label.set_size(8.5)
        ax.yaxis.label.set_size(8.5)
    if rows:
        axes[0].legend(fontsize=7)
    else:
        for ax in axes:
            ax.text(.5, .5, "No completed pulse cases", transform=ax.transAxes, ha="center")
    if rows:
        r = rows[0]
        caption = f"Exploratory group: alpha={r['alpha']}, cutoff({r['Na']},{r['Nb']}), {r['effective_exchange_order']}"
    else:
        caption = "Exploratory comparisons - no completed evidence"
    fig.suptitle(caption, size=10)
    path = folder/"tradeoffs.png"
    fig.savefig(path, dpi=180)
    fig.savefig(folder/"tradeoffs.pdf")
    plt.close(fig)
    return path


def _plot_rates(rates, folder):
    fig, ax = plt.subplots(figsize=(7.6, 4), layout="constrained")
    alphas = sorted({r["metrics"].get("alpha") for r in rates})
    resolved = 0
    for alpha in alphas:
        group = [r["metrics"] for r in rates if r["metrics"].get("alpha") == alpha
                 and r["metrics"].get("candidate_decay_rate_per_us") is not None]
        if group:
            resolved += len(group)
            ax.scatter([m["ratio"] for m in group], [m["candidate_decay_rate_per_us"] for m in group],
                       label=f"alpha={alpha:g}")
    if resolved:
        ax.set_yscale("log")
        ax.legend()
    else:
        ax.text(.5, .5, "No numerically resolved candidate rates completed", transform=ax.transAxes, ha="center")
    ax.set(xlabel="Readout drive / g2", ylabel="Candidate mode decay rate (1/us)",
           title="Returned spectral candidates - not certified global switching rates")
    ax.grid(alpha=.18)
    path = folder/"candidate_rates.png"
    fig.savefig(path, dpi=180)
    fig.savefig(folder/"candidate_rates.pdf")
    plt.close(fig)
    return path


def _plot_dephasing(records, folder):
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.5), layout="constrained")
    ratios = sorted({r["metrics"].get("parameters", r["job"]["parameters"]).get("ratio", 0.)
                     for r in records})
    colors = {ratio: plt.get_cmap("tab10")(i) for i, ratio in enumerate(ratios)}
    labelled, plotted = set(), 0
    for record in records:
        p = record["metrics"].get("parameters", record["job"]["parameters"])
        ratio, ka = p.get("ratio", 0.), p.get("kappa_a", 0.)
        archive = record["folder"]/"trajectories.npz"
        if not archive.exists():
            continue
        with np.load(archive) as data:
            if not all(k in data for k in ("t", "unconditioned_coherence", "code_population")):
                continue
            times, coherence, population = (data[k] for k in
                                            ("t", "unconditioned_coherence", "code_population"))
        if (times.ndim != 1 or coherence.shape != times.shape or population.shape != times.shape
                or not np.isfinite(coherence).all() or not np.isfinite(population).all()):
            continue
        label = f"drive/g2={ratio:g}" if ratio not in labelled else None
        labelled.add(ratio)
        style = "--" if ka == 0 else "-"
        axes[0].plot(times, coherence, style, color=colors[ratio], label=label)
        axes[1].plot(times, 1-population, style, color=colors[ratio])
        plotted += 1
    axes[0].set(xlabel="Time (us)", ylabel="Unconditioned logical coherence", title="Phase-insensitive coherence")
    axes[1].set(xlabel="Time (us)", ylabel="Population outside code space", title="Leakage reported separately")
    for ax in axes:
        ax.grid(alpha=.18)
        ax.tick_params(labelsize=8)
        ax.xaxis.label.set_size(9)
        ax.yaxis.label.set_size(9)
        ax.title.set_size(10)
        if not plotted:
            ax.text(.5, .5, "No completed coherence trajectories", transform=ax.transAxes,
                    ha="center", fontsize=8)
    if plotted:
        axes[0].legend(fontsize=8)
    fig.suptitle("Solid: physical memory loss; dashed: memory-loss channel removed", size=10)
    path = folder/"logical_coherence.png"
    fig.savefig(path, dpi=180)
    fig.savefig(folder/"logical_coherence.pdf")
    plt.close(fig)
    return path


def _image_page(pdf, image, title, caption, number):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(.07, .94, title, size=17, weight="bold", va="top")
    ax = fig.add_axes([.04, .38, .92, .43])
    ax.imshow(plt.imread(image))
    ax.axis("off")
    fig.text(.07, .32, "\n".join(textwrap.wrap(caption, 96)), size=10, va="top", linespacing=1.5)
    _footer(fig, number)
    pdf.savefig(fig)
    plt.close(fig)


def _make_notebook(folder):
    import nbformat
    from nbclient import NotebookClient
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_markdown_cell(
        "# Task 2.4 - DRAFT executed campaign evidence\n\n"
        "This notebook loads completed outputs; it does not run simulations. "
        "Execution success is separate from numerical convergence and scientific acceptance. "
        "The PDF is structured around Task 2.4(a-d)."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport json\nimport pandas as pd\n"
            "from IPython.display import Image, display\n"
            "candidates = [Path.cwd(), Path.cwd()/'report', Path.cwd()/'results/task_2_4_campaign/report']\n"
            "REPORT = next(p for p in candidates if (p/'summary.json').is_file())\n"
            "s = json.loads((REPORT/'summary.json').read_text())\n"
            "display({k:s[k] for k in ['report_status','generated_utc','job_counts','physical_review_status']})"),
        nbformat.v4.new_markdown_cell(
            "## 2.4(a): circuit assumptions\n\n"
            "The memory microwave drive is a separate coupling. A pi pump-phase change fixes the positive-g2 convention. "
            "Higher-order mean-force calibration does not make coherent codewords exact dark states. "
            "Read `physics_audit.md` and the PDF for the derivation, limitations and sources."),
        nbformat.v4.new_markdown_cell(
            "## 2.4(b): information and disturbance\n\n"
            "The ideal unit-white-noise homodyne convention gives SNR²=4I. "
            "This is a conditional-mean reference, not an observed single-shot fidelity. "
            "Raw logical error, leakage and matched-idle excesses remain distinct."),
        nbformat.v4.new_code_cell(
            "pulses = pd.read_csv(REPORT/'pulse_results.csv')\n"
            "display(pulses.head(30))\ndisplay(Image(filename=str(REPORT/'tradeoffs.png')))"),
        nbformat.v4.new_markdown_cell(
            "## 2.4(c): fair comparisons\n\n"
            "Only exact matched-duration, peak-bound, physical-parameter and cutoff constant controls are compared numerically. "
            "All improvement claims remain unproven until convergence and independent physical review."),
        nbformat.v4.new_code_cell("display(pd.DataFrame(s['matched_comparisons']))\n"
                                  "display(pd.DataFrame(s['pareto_cases']))"),
        nbformat.v4.new_markdown_cell(
            "## 2.4(d): validation and unresolved rates\n\n"
            "Available cutoff/solver differences are recorded below without declaring convergence. "
            "A visible near-shift spectral mode is not a certified globally dominant switching rate."),
        nbformat.v4.new_code_cell("display(pd.DataFrame(s['validation_comparisons']))\n"
                                  "display(pd.DataFrame(s['rate_cases']))\n"
                                  "display(Image(filename=str(REPORT/'candidate_rates.png')))"),
        nbformat.v4.new_markdown_cell(
            "## 2.4(b,d): dephasing and leakage controls\n\n"
            "An initial even cat probes logical coherence. Its transverse magnitude "
            "sqrt(X²+Y²) removes deterministic Bloch-phase rotation; leakage is shown separately. "
            "Memory-loss-off controls and zero-drive controls distinguish readout-induced effects "
            "from physical memory loss. Reduced-memory coherence can also decrease from reversible "
            "entanglement with a still-occupied buffer, so its magnitude is not a pure-dephasing-rate "
            "measurement. These trajectories do not establish a switching rate."),
        nbformat.v4.new_code_cell("display(pd.DataFrame(s['dephasing_cases']))\n"
                                  "display(Image(filename=str(REPORT/'logical_coherence.png')))"),
        nbformat.v4.new_markdown_cell(
            "## Provenance and AI assistance\n\n"
            "`summary.json` preserves the manifest's source hashes, job states and the report generator hash. "
            "Codex assisted with implementation, candidate design, audits and report preparation. "
            "Numerical claims must be supported by saved trajectories and independent validation. "
            "Pending/failed cases and unsuccessful candidates are retained.")]
    client = NotebookClient(nb, timeout=120, kernel_name="python3",
                            resources={"metadata": {"path": str(folder)}})
    client.km = client.create_kernel_manager()
    client.km.kernel_spec.argv[0] = sys.executable
    client.execute()
    nbformat.write(nb, folder/"task_2_4_evidence.ipynb")


def build_report(output):
    """Create draft CSV/JSON/figures/PDF/executed notebook, even with no jobs done."""
    output = Path(output).resolve()
    manifest = json.loads((output/"manifest.json").read_text())
    folder = output/"report"
    folder.mkdir(exist_ok=True)
    records, states = _load_jobs(output, manifest)
    pulses = [r for r in records if r["job"]["kind"] == "pulse"]
    rates = [r for r in records if r["job"]["kind"] == "spectrum"]
    dephasing = [r for r in records if r["job"]["kind"] == "dephasing"]
    rows = [_pulse_row(r) for r in pulses]
    with (folder/"pulse_results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    groups = {}
    for row in rows:
        key = json.dumps({k: row.get(k) for k in FRONT_GROUP}, sort_keys=True)
        groups.setdefault(key, []).append(row)
    front = [identifier for group in groups.values() for identifier in pareto_ids(group)]
    plot_rows = max(groups.values(), key=len) if groups else []
    rate_cases = [{"id": r["job"]["id"], **{k: r["metrics"].get(k) for k in
        ("alpha", "ratio", "Na", "Nb", "candidate_status", "candidate_decay_rate_per_us",
         "candidate_is_nonoscillatory", "global_dominance_certified", "rate_interpretation")}}
        for r in rates]
    counts = {status: sum(s["status"] == status for s in states) for status in sorted({s["status"] for s in states})}
    summary = {"report_status": "DRAFT - partial executed evidence; not a final submission",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "job_counts": counts,
        "job_states": states, "physical_review_status": "Pending; no superiority or convergence certificate",
        "source_manifest_sha256": manifest.get("source_sha256", {}),
        "report_generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "measurement_convention": "dY=2sqrt(eta*kappa)Re(exp(-i*phi)B)dt+dW; SNR_squared=4I",
        "pareto_interpretation": "Exploratory exact nondominance within identical physical settings, cutoffs and solver tolerances; no uncertainty certificate",
        "pareto_grouping": list(FRONT_GROUP),
        "plot_group": {k: plot_rows[0].get(k) for k in FRONT_GROUP} if plot_rows else None,
        "pareto_cases": [r for r in rows if r["id"] in front],
        "matched_comparisons": _matched_comparisons(pulses),
        "validation_comparisons": _validation_comparisons(pulses), "rate_cases": rate_cases,
        "dephasing_cases": [{"id": r["job"]["id"], "parameters": r["job"]["parameters"],
                              "metrics": r["metrics"]} for r in dephasing]}
    _write_json(folder/"summary.json", summary)
    _write_json(folder/"pareto.json", {k: summary[k] for k in ("report_status", "pareto_interpretation", "pareto_cases")})
    _write_json(folder/"dephasing_results.json", summary["dephasing_cases"])
    audit_path = Path("/tmp/cat-qubit-cloud/circuit_audit.md")
    if audit_path.exists():
        (folder/"physics_audit.md").write_text(audit_path.read_text())
    elif not (folder/"physics_audit.md").exists():
        (folder/"physics_audit.md").write_text(
            "# Physics audit provenance\n\nThe independent full audit was not available on this host. "
            "The PDF summarizes its essential claim safeguards; inspect the preserved derivation "
            "and original source audit before final scientific acceptance.\n")
    tradeoff = _plot_tradeoffs(plot_rows, folder)
    rate_plot = _plot_rates(rates, folder)
    dephasing_plot = _plot_dephasing(dephasing, folder)
    pdf_path = folder/"task_2_4_DRAFT.pdf"
    with PdfPages(pdf_path) as pdf:
        _text_page(pdf, "Task 2.4 - DRAFT scientific evidence", [
            "Research question: how quickly can the buffer reveal the stored memory bit while limiting unwanted logical transitions, leakage and emission after the pulse? This report is regenerated from finished jobs. It is intentionally a draft until numerical and physical review are complete.",
            "Execution snapshot: "+(", ".join(f"{v} {k}" for k, v in counts.items()) or "no jobs prepared")+". Completed means the job returned saved outputs. It does not mean converged, optimized, or accepted.",
            "Task 2.4(a): derive the circuit interaction and physical memory drive. Task 2.4(b): measure output information and stored-bit disturbance separately. Task 2.4(c): compare shaped controls with tuned constant drives under common constraints. Task 2.4(d): validate an explanation against cutoffs, solvers and circuit limitations.",
            f"Available evidence: {len(pulses)} completed pulse jobs, {len(rates)} spectral jobs and {len(dephasing)} coherence-control jobs. Discovery uses reduced cutoffs; larger-cutoff and tighter-solver results are separate rows. Missing jobs remain pending or explicitly failed/timed out.",
            "Headline status: no global optimum, actual single-shot fidelity, globally certified switching rate, or validated improvement is claimed by this automated document. A final result requires matched comparisons and independent scientific acceptance.",
            "The CSV, Pareto JSON, job manifest, source hashes, complete status list and executable evidence notebook accompany this PDF. Figures show only saved outputs; empty figures mean evidence has not yet completed."], 1)
        _text_page(pdf, "2.4(a) - circuit-to-readout mechanism", [
            "At the specified ATS bias, the first pump-order potential is +2 EJ epsilon_p cos(omega_p t) sin(Phi). Its cubic two-memory/one-buffer resonant term has a negative coefficient. A pi pump-phase change gives the repository's positive-g2 convention, with the buffer-drive phase chosen consistently.",
            r"EQ:$g_2=E_J\epsilon_p\varphi_a^2\varphi_b/2,\quad \omega_p=2\omega_a-\omega_b$",
            "The memory readout drive is a separately coupled microwave force, not an automatic extra term from the two-photon ATS pump. For the pulse module's phase convention the rotating-frame drive and initial displacement are:",
            r"EQ:$H_Z=\epsilon_Z(t)(e^{i\phi}a^\dagger+e^{-i\phi}a),\quad \dot A|_Z=-i\epsilon_Ze^{i\phi}$",
            "The buffer pump and cubic exchange cancel on |+alpha,0> and |-alpha,0> in the lossless ideal model. Weak real readout drive moves the memory initially along its imaginary direction; the local two-photon response then produces opposite real buffer fields. Neglecting the small shared loss-induced background:",
            r"EQ:$\langle b\rangle_\pm\simeq\mp\epsilon_Z/(2\alpha g_2)$",
            "Higher phase orders modify exchange matrix elements. Recalibrating the buffer drive to cancel the mean force does NOT restore exact coherent-state darkness. Every corrected model therefore needs a matched no-readout evolution. The pulse jobs include such photon, logical-population and leakage baselines.",
            "First-order RWA does not produce arbitrary static Kerr terms. The sine model retains selected-channel phase corrections; circuit_correction=True additionally includes the audited compensated dispersive diagonal through the chosen phase order. These remain effective Hamiltonians, excluding a full GHz circuit and bath-dressing simulation.",
            "Primary sources: supplied challenge Task 2.4; Reglade et al., arXiv:2307.06617v2, Supplement S3-S4 and S8.5. The independent audit is included as physics_audit.md where available."], 2)
        _text_page(pdf, "2.4(b) - information is not a bit flip", [
            "Useful measurement, logical dephasing and unwanted logical population transfer are different effects. The primary reference is the full two-mode Lindblad model, retaining both supplied losses. The fast-buffer approximation is not uniformly valid at g2/kappa_b about 0.293 and epsilon_d/kappa_b about 1.295.",
            r"EQ:$dY_s=2\sqrt{\eta\kappa_b}\,\mathrm{Re}(e^{-i\phi}B_s)dt+dW$",
            r"EQ:$\mathcal{I}_\phi=\eta\kappa_b\int[\mathrm{Re}(e^{-i\phi}\Delta B)]^2dt,\quad \mathrm{SNR}^2=4\mathcal{I}_\phi$",
            "This matched-filter quantity assumes unit white measurement noise. Under coherent outputs and equal Gaussian covariance, I=1 would give 15.9% error; mean fields alone do not establish that distribution or a measured fidelity. The nominal real quadrature and optimized fixed quadrature are recorded separately, so phase recalibration is explicit. A time-varying local oscillator is not silently assumed.",
            r"EQ:$P_{\rm code}=|C_+\rangle\langle C_+|+|C_-\rangle\langle C_-|$",
            "Logical populations use the orthonormal sums/differences of normalized even and odd cats. The coherent inputs have a small finite-alpha wrong-logical offset, which is retained. Final wrong population, leakage and matched-idle-subtracted excesses are distinct; signed differences are not clipped or reinterpreted as probabilities.",
            "Pulse-end information excludes later emission. Recovery photons and the information emitted after control termination are separately saved. A small mean buffer field does not certify a small total photon population: incoherent photons must also be counted.",
            "A returned Liouvillian mode is not automatically the physical switching rate. Relevant overlaps, left/right residuals, conjugate pairs, time-domain behavior, cutoff convergence and the validity of a two-state model all require review."], 3)
        _image_page(pdf, tradeoff, "2.4(c) - executed control trade-offs",
            "Each point is a completed full two-mode pulse calculation. The largest completed group with identical physical settings, cutoffs and solver tolerances is shown; its amplitude and duration vary. All other groups remain in the CSV/JSON, with Pareto screening performed separately within each group. Compare equal-duration and peak-bound controls before judging shape effects. Apparent Pareto membership does not certify an advantage. Idle controls and signed background-subtracted residual photons are retained. The total clock includes the stated recovery interval.", 4)
        matched = summary["matched_comparisons"]
        comparison_lines = ["Matched comparisons below use the same elapsed time, peak bound, physical settings and cutoffs. Ratios are observed numerical metrics, not accepted improvements. Missing matched controls are explicitly unproven."]
        for row in matched[:6]:
            label = f"{row['profile']}, drive/g2={row['ratio']:g}, T={row['duration']:g} us, {row['cutoffs']}"
            comparison_lines.append(label+": "+(
                f"I/I_constant={row['information_ratio']:.5g}; delta wrong={row['wrong_population_difference']:.3g}; delta leakage={row['leakage_difference']:.3g}."
                if row.get("information_ratio") is not None else row["comparison"]+"."))
        if not matched:
            comparison_lines.append("No shaped/constant matched pair has completed. No waveform improvement can yet be assessed.")
        if len(matched) > 6:
            comparison_lines.append(f"{len(matched)-6} further comparisons are retained in summary.json and the notebook.")
        comparison_lines.append("A constant-drive amplitude sweep is the reference, not only the weak Task 2.3 drive. Gaussian and smooth-edge pulses pay for their turn-on/off intervals. Signed depletion is useful only if its reduced residual excitation compensates its information or time cost.")
        _text_page(pdf, "2.4(c) - matched reference comparisons", comparison_lines, 5)
        validation = summary["validation_comparisons"]
        lines = ["Successful execution is not convergence. The following comparisons record available differences; no automated physical acceptance is assigned. Separate Na/Nb increases and tighter time/solver resolution remain necessary for headline claims."]
        for row in validation[:6]:
            rel = row["information_relative_difference"]
            lines.append(f"{row['profile']}, drive/g2={row['ratio']:g}, T={row['duration']:g} us; "
                         f"{row['cutoffs']} versus {row['reference_cutoffs']}: deltaI/I="+
                         (f"{rel:.3g}" if rel is not None else "undefined at zero signal")+
                         f"; absolute delta wrong={row['wrong_population_absolute_difference']:.3g}; delta leakage={row['leakage_absolute_difference']:.3g}.")
        if not validation:
            lines.append("No matching cutoff/solver comparison has completed. Numerical validation is pending.")
        if len(validation) > 6:
            lines.append(f"{len(validation)-6} additional comparisons are retained in summary.json and the notebook.")
        lines.extend(["Discovery at 24x8 is not final physical-target evidence. Boundary populations, trace and signed eigenvalue residuals are retained, but small boundary occupancy alone does not certify an exponentially small switching rate.",
            "Robustness distinguishes fixed nominal microwave/LO calibration from recalibration. Phase/amplitude tests, no-memory-loss controls and sine-exchange cases are separate experiments. A Hamiltonian-only correction omits bath dressing, flux noise and fabrication uncertainty."])
        _text_page(pdf, "2.4(d) - validation and remaining limits", lines, 6)
        _image_page(pdf, rate_plot, "2.4(b,d) - candidate switching modes",
            "Only numerically resolved returned candidates are plotted. All case statuses and unresolved values remain in summary.json. A near-shift eigensystem is not a completeness or global-dominance proof. Complex modes or several visible contributions can invalidate a single exponential two-state interpretation. Time-domain diagnostics, shift/cutoff changes and the one-way-versus-imbalance factor of two must be reviewed separately.", 7)
        _image_page(pdf, dephasing_plot, "2.4(b,d) - dephasing and leakage controls",
            "An initial even cat probes transverse logical coherence. The magnitude sqrt(X²+Y²) removes a common deterministic Bloch phase; it does not remove leakage, shown separately. Reduced-memory coherence can also decrease from reversible entanglement with an occupied buffer. It is therefore not a pure-dephasing-rate measurement or simply the overlap of emitted pointer fields. Code-conditioned coherence is a diagnostic, not a postselected fidelity. Memory-loss-off and zero-drive controls help separate physical contributions; logical switching remains an independent measurement. No fitted dephasing rate or single-shot fidelity is inferred.", 8)
        _text_page(pdf, "Provenance, limitations and review", [
            "Every plotted value comes from a completed manifest job and its saved output. Source hashes and job IDs are retained in summary.json. Failed, timed-out and pending cases are not replaced with predictions or extrapolated measurements.",
            "This automated report stays DRAFT until a scientific reviewer checks signs and 2pi factors, circuit resonance conditions, logical definitions, measurement-noise normalization, rate identification, truncation effects and fairness of each proposed improvement.",
            "No actual single-shot fidelity, globally optimal pulse, protected long-time physical-target rate, exact full-circuit simulation or completed final submission is asserted. A negative optimization finding is acceptable if supported by matched numerical evidence.",
            "AI assistance: Codex agents assisted with circuit and numerical audits, software, experiment design and report generation. Numerical findings must be supported by executed calculations. Independent validation and unresolved disagreements are retained in the accompanying records.",
            "References: DuQuantum 2026 Alice & Bob challenge Task 2.4; Reglade et al., arxiv.org/abs/2307.06617; Dubovitskii, arxiv.org/abs/2407.17299. The latter's adiabatic expressions are qualitative checks unless validated against this full two-mode model.",
            "Rebuild this draft from the campaign snapshot: python -m tasks.task_2_4_campaign_report --output <campaign-folder>. The executable notebook reads the report directory without rerunning simulations. CSV and JSON accompany all figure exports."], 9)
    _make_notebook(folder)
    return {"pdf": str(pdf_path), "notebook": str(folder/"task_2_4_evidence.ipynb"),
            "summary": str(folder/"summary.json"), "csv": str(folder/"pulse_results.csv"),
            "pareto": str(folder/"pareto.json"), "dephasing": str(folder/"dephasing_results.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build_report(parser.parse_args().output), indent=2))
