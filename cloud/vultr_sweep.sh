#!/usr/bin/env bash
# Run the Task 1.2 (Na, Nb) grid on a Vultr cloud VM (Ubuntu 24.04, CPU-optimized, 16+ vCPU).
#
#   ssh root@<vm-ip>
#   git clone https://<github-token>@github.com/pkarakala/duquantum-cat-qubit   # private repo: use a token
#   cd duquantum-cat-qubit
#   ./cloud/vultr_sweep.sh                 # or JOBS=8 ./cloud/vultr_sweep.sh
#
# Then copy results back:  scp -r root@<vm-ip>:duquantum-cat-qubit/{results,figures} .
# Destroy the VM afterwards (Vultr bills hourly while it exists, even when idle).
set -euo pipefail
cd "$(dirname "$0")/.."

# One run uses ~2-4 cores (measured on a 4-core box), so about vCPU/4 jobs at once.
JOBS=${JOBS:-$(( $(nproc) / 4 > 0 ? $(nproc) / 4 : 1 ))}

if [ ! -d .venv ]; then
  # a fresh VM runs cloud-init/unattended-upgrades first; wait for the apt lock instead of failing
  cloud-init status --wait >/dev/null 2>&1 || true
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  apt-get -o DPkg::Lock::Timeout=600 install -y -qq python3-venv >/dev/null
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/python -m src.config     # units check

echo "$(nproc) vCPU, $JOBS jobs in parallel; log in results/grid.log"
start=$(date +%s)
mkdir -p results/grid
.venv/bin/python -m tasks.task_1_2_grid --list |
  xargs -P "$JOBS" -L 1 sh -c '[ -f results/grid/${0}x${1}.json ] || .venv/bin/python -m tasks.task_1_2_grid --point $0 $1' \
  2>&1 | tee results/grid.log
.venv/bin/python -m tasks.task_1_2_grid --merge
echo "wall time $(( $(date +%s) - start )) s on $(nproc) vCPU" | tee -a results/grid.log
