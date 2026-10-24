#!/usr/bin/env bash
# Cursor worktree setup (macOS/Linux/WSL/cloud): a per-worktree venv, because there is no shared D:\ path.
set -euo pipefail
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt pytest sympy optax psutil
fi
.venv/bin/python -c "from src import config as C; print('[setup] OK kappa_2/2pi =', round(C.KAPPA_2 / C.TWO_PI, 3), 'MHz')"
echo "[setup] use: export DUQ_PY=\$PWD/.venv/bin/python"
