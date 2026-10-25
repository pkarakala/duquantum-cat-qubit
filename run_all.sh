#!/usr/bin/env bash
# Reproduce every Section 1 figure and number, then the Section 2 tables from results/s2/.
# Optional integration audit: python -m tasks.task_1_1_checks (several minutes).
set -euo pipefail
python -m src.config            # prints kappa_2/2pi = 0.896 MHz as a units check
python -m tasks.task_1_0        # warm-up plots and Wigner GIFs
python -m tasks.task_1_2        # full 6x6 cutoff grid; resumes cached trajectories
python -m tasks.task_1_1        # chosen cutoff, inflation plots and Wigner GIF
python -m tasks.task_1_3a       # state diagnostics and interference-decay GIF
python -m tasks.task_1_3b       # ~13 min (1.3b/c: preparing |+alpha>)
# python -m tasks.task_2_1; python -m tasks.task_2_2   # brute force Section 2 rates (slow; results saved)
python -m research.s2.summarize # seconds: Section 2 tables (results/s2/SUMMARY.md) from the saved runs (raw runs: cloud/s2_batch*.txt)
python -m research.s2.notebook_figs # seconds: the Section 2 notebook figures (figures/s2/task_2_*)
