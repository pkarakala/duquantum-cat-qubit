#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu VM: Python venv with the pinned requirements, then the units check.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  # a fresh VM runs cloud-init/unattended-upgrades first; wait for the apt lock instead of failing
  cloud-init status --wait >/dev/null 2>&1 || true
  apt-get -o DPkg::Lock::Timeout=600 update -qq
  apt-get -o DPkg::Lock::Timeout=600 install -y -qq python3-venv >/dev/null
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/python -m src.config     # units check
