#!/usr/bin/env bash
# Reproduce every figure in figures/ and every number in results/ (Introductory Track).
set -euo pipefail
python -m src.config            # prints kappa_2/2pi = 0.896 MHz as a units check
python -m tasks.task_1_0        # ~20 s
python -m tasks.task_1_2        # convergence sweep, ~15-30 min on a laptop (run on a cloud VM if you can)
python -m tasks.task_1_1        # ~30 s, uses the truncation chosen in Task 1.2 (src/config.py)
python -m tasks.task_1_3a       # ~1-2 min
python -m tasks.task_1_3b       # ~13 min (1.3b/c: preparing |+alpha>)
