#!/usr/bin/env bash
# Reproduce the main Introductory Track task figures and numbers.
# Optional integration audit: python -m tasks.task_1_1_checks (several minutes).
set -euo pipefail
python -m src.config            # prints kappa_2/2pi = 0.896 MHz as a units check
python -m tasks.task_1_0        # warm-up plots and Wigner GIFs
python -m tasks.task_1_2        # full 6x6 cutoff grid; resumes cached trajectories
python -m tasks.task_1_1        # chosen cutoff, inflation plots and Wigner GIF
python -m tasks.task_1_3a       # state diagnostics and interference-decay GIF
python -m tasks.task_1_3b       # ~13 min (1.3b/c: preparing |+alpha>)
