#!/usr/bin/env bash
# Reproduce every figure in figures/ and every number in results/ (Intro + Standard Track).
#   bash run_all.sh                 # full: intro tasks, plus runq commands for the heavy jobs
#   bash run_all.sh --quick         # smoke run (<= 2 min per task) into results/quick/ and figures/quick/
#   bash run_all.sh --intro | --standard   # one stage only (default: both)
#   bash run_all.sh --dry-run       # print the commands instead of running them
# The interpreter comes from $PY (default: python), e.g. PY=.venv/bin/python bash run_all.sh --quick
set -euo pipefail
cd "$(dirname "$0")"

PY=${PY:-python}
export XLA_FLAGS="${XLA_FLAGS:---xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2}"

INTRO=0; STANDARD=0; QUICK=0; DRY=0
for arg in "$@"; do
  case "$arg" in
    --intro) INTRO=1 ;;
    --standard) STANDARD=1 ;;
    --quick) QUICK=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "run_all.sh: unknown flag '$arg' (see --help)" >&2; exit 2 ;;
  esac
done
if [ "$INTRO" -eq 0 ] && [ "$STANDARD" -eq 0 ]; then INTRO=1; STANDARD=1; fi

run() {
  if [ "$DRY" -eq 1 ]; then echo "$*"; else echo "+ $*"; "$@"; fi
}

# Standard Track scripts in dependency order; missing ones are skipped until their lane is merged.
STANDARD_TASKS="task_1_3b task_2_2 task_2_1_eig task_2_1_td task_2_1_channels task_2_3 task_2_4a task_2_4b task_2_4c_pulses"

run "$PY" -m src.config            # prints kappa_2/2pi = 0.896 MHz as a units check

if [ "$INTRO" -eq 1 ]; then
  run "$PY" -m tasks.task_1_0      # ~20 s
  if [ "$QUICK" -eq 1 ]; then
    # writes results/task_1_2_quick.json + figures/task_1_2_convergence_quick.png (tracked dirs: never commit)
    run "$PY" -m tasks.task_1_2 --quick
  else
    echo "HEAVY (15-30 min), queue it instead of running inline:"
    echo "  $PY -m tools.runq submit --name task_1_2 --ram-gb 2 -- $PY -m tasks.task_1_2"
  fi
  run "$PY" -m tasks.task_1_1      # ~30 s, uses the truncation chosen in Task 1.2 (src/config.py)
  run "$PY" -m tasks.task_1_3a     # ~1-2 min
fi

if [ "$STANDARD" -eq 1 ]; then
  [ "$QUICK" -eq 1 ] || echo "Standard Track production runs go through the queue (RAM estimates: adjust as needed):"
  for t in $STANDARD_TASKS; do
    if [ ! -f "tasks/$t.py" ]; then
      echo "SKIP tasks/$t.py (not merged yet)"
    elif [ "$QUICK" -eq 1 ]; then
      run "$PY" -m "tasks.$t" --quick
    else
      ram=2
      [ "$t" = "task_2_1_eig" ] && ram=6
      echo "  $PY -m tools.runq submit --name $t --ram-gb $ram -- $PY -m tasks.$t"
    fi
  done
fi

if [ "$QUICK" -eq 1 ]; then
  run "$PY" -m tools.build_index --quick
  rc=0
  run "$PY" -m tools.check_claims || rc=$?
  [ "$DRY" -eq 1 ] || echo "check_claims exit code $rc (non-fatal with --quick)"
else
  run "$PY" -m tools.build_index
  rc=0
  run "$PY" -m tools.check_claims || rc=$?
  exit "$rc"
fi
