#!/usr/bin/env bash
# Reproduce every Section 1 figure and number, then the Section 2 tables from results/s2/.
# Optional integration audit: python -m tasks.task_1_1_checks (several minutes).
set -euo pipefail
python -m src.config            # prints kappa_2/2pi = 0.896 MHz as a units check
python -m tasks.task_1_0        # ~20 s
python -m tasks.task_1_2        # full 6x6 cutoff grid; resumes cached trajectories
python -m tasks.task_1_1        # ~30 s, uses the truncation chosen in Task 1.2 (src/config.py)
python -m tasks.task_1_3a       # ~1-2 min
python -m tasks.task_1_3b       # ~13 min (1.3b/c: preparing |+alpha>)
python -m research.s2.summarize # seconds: Section 2 tables and figures from the saved runs (raw runs: cloud/s2_batch*.txt)
