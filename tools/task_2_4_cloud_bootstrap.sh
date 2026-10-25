#!/usr/bin/env bash
# Run inside an uploaded, frozen source snapshot on Ubuntu 24.04.
set -euo pipefail
task_root="${1:-/opt/duquantum/task24}"
cd "$task_root"
export MPLBACKEND=Agg OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv python3-pip rsync time
if ! test -x .venv/bin/python; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
mkdir -p results/cloud_environment
mkdir -p /tmp/cat-qubit-cloud
if test -f audits/circuit_audit.md; then
    cp audits/circuit_audit.md /tmp/cat-qubit-cloud/circuit_audit.md
fi
.venv/bin/python -m pip freeze > results/cloud_environment/requirements.lock
lscpu > results/cloud_environment/lscpu.txt
free -h > results/cloud_environment/memory.txt
df -h > results/cloud_environment/storage.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tasks.task_2_4_campaign prepare --preset smoke --output results/cloud_smoke
# The production-size smoke is deliberately short, not a convergence claim.
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from tasks.task_2_4_campaign import atomic_json, job
p = Path('results/cloud_smoke/manifest.json')
m = json.loads(p.read_text())
m['jobs'] = [job('pulse', {'Na':32,'Nb':12,'alpha':2.1,'ratio':.05,
                         'duration':.10,'idle':.02,'step':.01},
                 'Production-size resource and solver smoke, not physics validation', 0)]
atomic_json(p,m)
PY
/usr/bin/time -v .venv/bin/python -m tasks.task_2_4_campaign run --output results/cloud_smoke --workers 1 --cpus-per-worker 2 --hours .05 --job-timeout 120
.venv/bin/python - <<'PY'
import json
from pathlib import Path
s=json.loads(Path('results/cloud_smoke/status.json').read_text())
assert s['counts']=={'completed':1},s
PY
.venv/bin/python -m tasks.task_2_4_campaign prepare --output results/task_2_4_campaign --preset research
systemd-run --unit=duquantum-task24 --service-type=exec \
    --property="WorkingDirectory=$task_root" --property=RuntimeMaxSec=11100 \
    --property=KillMode=control-group --property=Nice=5 \
    /bin/bash "$task_root/tools/task_2_4_cloud_run.sh" "$task_root"
systemctl status duquantum-task24 --no-pager
