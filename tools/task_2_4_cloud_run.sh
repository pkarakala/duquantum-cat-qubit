#!/usr/bin/env bash
# systemd owns this process group; closing SSH does not stop the campaign.
set -uo pipefail
task_root="${1:-/opt/duquantum/task24}"
cd "$task_root" || exit 1
export MPLBACKEND=Agg OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
.venv/bin/python -u -m tasks.task_2_4_campaign run \
    --output results/task_2_4_campaign --workers 12 --spectral-workers 1 \
    --cpus-per-worker 1 --hours 3 --job-timeout 1200
run_result=$?
.venv/bin/python -m tasks.task_2_4_campaign_report --output results/task_2_4_campaign
report_result=$?
.venv/bin/python - "$run_result" "$report_result" <<'PY'
import sys
from datetime import datetime, timezone
from pathlib import Path
from tasks.task_2_4_campaign import atomic_json
atomic_json(Path('results/task_2_4_campaign/report_done.json'),
            {'utc':datetime.now(timezone.utc).isoformat(),
             'scheduler_exit_code':int(sys.argv[1]), 'report_exit_code':int(sys.argv[2])})
PY
if test "$run_result" -ne 0; then
    exit "$run_result"
fi
exit "$report_result"
