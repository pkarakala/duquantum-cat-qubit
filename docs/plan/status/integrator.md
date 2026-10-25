# Status: lane `integrator` (global ledger)

> **macOS adaptation.** This run is on macOS 14.5 / Apple M3 arm64 / 8 GB, not the Windows laptop in the brief. The git-ignored `.orchestrator/RUNBOOK.md` overrides brief 90 on environment, hardware and process only (never physics, record IDs, tolerances, allowlists or CONTRACT). Paths write the main checkout as `$MAIN`, because the absolute path contains the username. All times are EDT.

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (Phase 0 done; next event: merge `l0-core` at G0) |
| Branch | `standard-track`, in the main checkout `$MAIN` (no worktree, no `std/` branch) |
| Agent / model | Cursor agent (integrator), resumed by the coordinator once per event |
| Started (EDT) | 18:36 Sat Oct 24 2026 |
| Last update (EDT) | 18:40 Sat Oct 24 2026 |
| Last commit | the commit that adds this file (`[integrator] ledger: start`, parent `ed67136`) |
| CONTRACT frozen at | pending (set at G0, at the `l0-core` merge) |
| `freeze-0800` | pending |

## Machine adaptations (RUNBOOK §1–§3; replace the brief's 16 GB / Windows numbers)
- **Machine:** macOS 14.5, Apple M3 (arm64), 8 cores (4P + 4E), **8 GB RAM**, CPU only. About 5 GB is realistically available to simulations.
- **Interpreter:** `$MAIN/.venv/bin/python` (CPython 3.12.13, jax/jaxlib 0.12.0.1, dynamiqs 0.3.7; setup G0-env PASSED, `.venv/.duq-ready` at 18:31). Agent shells inherit nothing, so every shell runs:
  ```sh
  export MAIN=<main checkout; RUNBOOK §2>
  export DUQ_PY=$MAIN/.venv/bin/python
  export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
  export MPLCONFIGDIR=$MAIN/.orchestrator/mplconfig
  cd $MAIN
  ```
- **runq worker:** `--max-jobs 2 --max-ram-gb 5` (brief: 3 / 11). If the machine swaps, restart it with `--max-jobs 1 --max-ram-gb 4`. The brief's fallback (`--max-ram-gb 8`) does not apply here.
- **Heavy lock** `$MAIN/.git/duq-heavy.lock` (RUNBOOK §3), shared with the lane agents: any process expected above 1.5 GB RSS or 5 min wall holds it for its whole run (atomic `mkdir`, owner line in `$LOCK/owner`). Never start a heavy job by hand beside the worker. Never delete another lane's lock; if one looks stale (owner time more than 30 min ago), log it here. How worker jobs take the lock: see DECISION NEEDED D3.
- **Big LU (> 3 GB):** one at a time (runq enforces this), and treated as infeasible unless it runs alone.
- **Mini-lane §6.4 cap:** l1-spectral computes the `NA_EIG_MAX, NB_EIG_MAX` recommendation against **4 GB / 10 min** on this machine (brief: 6 GB / 10 min). The "comfortable" pair stays ≤ 5 min / ≤ 3 GB and is used for `--ram-gb ≤ 3` submissions.
- **`gh` is not installed.** No push happens without Harshit's explicit OK anyway (see PUSH REQUESTED and D1).
- **Scratch:** `$MAIN/.orchestrator/` (git-ignored). `$TMPDIR` only works from an unsandboxed shell.
- **Phase 0 verification (18:36–18:37):** `test -f $MAIN/.venv/.duq-ready` → present. `"$DUQ_PY" -m src.config` → `kappa_2/2pi = 0.896 MHz (expect 0.896)`, `g2/kappa_b = 0.29, eps_d/kappa_b = 1.29`, `phase-flip time 1/(2 kappa_a alpha^2) = 1.94 us`. `git branch --show-current` → `standard-track`. Heavy lock: not held. `git status --porcelain` → empty.

## Lanes
Snapshot at 18:39 (lane state as reported by the coordinator; last commit from `git log -1 std/<slug>`).

| lane | state | branch | last commit | reviewer verdict | merged commit | records produced | jobs queued |
|---|---|---|---|---|---|---|---|
| `setup` | DONE | `standard-track` (main checkout) | `ed67136` [setup] Pin working environment and record intro reproduction (G0-env) | n/a (G0-env PASSED, `status/setup.md`) | `ed67136` (committed directly on `standard-track`) | none | none |
| `l0-core` | IN_PROGRESS | `std/l0-core` | `8dee725` [l0-core] tests first: 20 brief tests + contract signature pin (failing) | | | | |
| `l0-tools` | IN_PROGRESS | `std/l0-tools` | `fd663c6` [l0-tools] wrapped intro records | | | | |
| `l1-spectral` | IN_PROGRESS (early start, pure code) | `std/l1-spectral` | `0a35012` [l1-spectral] tests first: vectorization, Z2 sectors, deflation, diagnostics, Gamma_X anchors | | | | |
| `l2a-gamma-z` | NOT_STARTED | `std/l2a-gamma-z` (not created) | | | | | |
| `l2b-gamma-x` | NOT_STARTED | `std/l2b-gamma-x` (not created) | | | | | |
| `l3-prep` | NOT_STARTED | `std/l3-prep` (not created) | | | | | |
| `l4a-readout` | IN_PROGRESS (early start, pure code) | `std/l4a-readout` | `614132a` [l4a-readout] src/linresp.py: 2x2 linear-response model (…) | | | | |
| `l5-circuit` | IN_PROGRESS (early start, pure code) | `std/l5-circuit` | `27a3378` (no lane commits yet) | | | | |
| `l4b-tradeoff` | NOT_STARTED | `std/l4b-tradeoff` (not created) | | | | | |
| `l4c-capstone` | NOT_STARTED | `std/l4c-capstone` (not created) | | | | | |
| `l6-lab` | IN_PROGRESS (Part A, mock data; merges later on real data) | `std/l6-lab` | `aaf52be` [l6-lab] tests first: schema, provenance, router, lib, export (failing) | | | | |
| `l7-docs` | NOT_STARTED | `std/l7-docs` (not created) | | | | | |
| `l8-felis` | NOT_STARTED | `std/l8-felis` (not created) | | | | | |

Merge order (brief §6.1 step 8): `l0-core` → `l0-tools` → `l1-spectral` → `l2a-gamma-z`, `l3-prep`, `l4a-readout`, `l5-circuit` (any order) → `l2b-gamma-x` → `l4b-tradeoff` → `l4c-capstone` → `l8-felis` → `l6-lab` (real data) → `l7-docs`. All lane branches are cut from `27a3378` (before the setup commit); P1 uses the three-dot merge-base diff, so the setup files do not show up.

## Checks P1–P9
P1–P4 on every merge, P5–P6 on every production batch, P7–P9 at the gates named. A lane merges together with its passing review branch `review/<slug>-r<N>` (brief 91 §4).

| Check | Definition (brief 90 §5) | Runs at |
|---|---|---|
| P1 allowlist | `git diff --name-only standard-track...std/<slug>` ⊆ the lane's CONTRACT §1 row ∪ `docs/plan/status/<slug>.md` ∪ its own `results/records/<ids>.json`, `results/arrays/<ids>.npz`, `figures/task_<its task>_*.png` (l6-lab also `docs/plan/status/l6-shots/**`). Red flags: `src/config.py`, `src/model.py`, `src/analysis.py` (except l0-core), `results/index.json`, `results/quick/**`, `figures/quick/**`, `site/src/data/live/**`, `notes/**`, the two `*_quick` intro files, any deletion. The review branch must touch only `docs/plan/status/reviews/<slug>.md`. | every merge |
| P2 preconditions | Status `State` is `DONE` (`DONE_WITH_CONCERNS` only with `PASS_WITH_NOTES` that addresses each concern); verdict `PASS`/`PASS_WITH_NOTES`; reviewed sha == `std/<slug>` head. | every merge |
| P3 fast suite | `-m "not slow" -q` exits 0 in < 2 min; passed count ≥ the previous ledger value; log `N passed, M skipped`. | every merge |
| P4 index | `build_index` exits 0 and `count` ≥ the previous count (skip with "tools not merged" until `l0-tools` lands). | every merge |
| P5 dirty | Every new or modified `results/records/*.json` has `provenance.dirty == false`. | every production batch |
| P6 staleness | For every new record, `git diff --quiet <git_commit> HEAD -- src <script>` exits 0. | every production batch |
| P7 slow suite | `-m slow` exits 0 (through runq). | G2, freeze |
| P8 claims | `check_claims --files TECHNICAL.md README.md` exits 0. | after l7's draft merges, freeze |
| P9 lab bundle | `site/src/data/live/*.json` parse as JSON; total < 8 MB. | after every lab export |

### Commands (zsh translation of brief §9; env from Machine adaptations)
```sh
slug=<lane>                                           # e.g. l0-core
git fetch origin                                      # std/* are local (worktrees); this only refreshes origin/*
# P1 allowlist
git diff --name-only standard-track...std/$slug
git diff --name-status --diff-filter=D standard-track...std/$slug                 # any deletion: send back
git diff --name-only standard-track...std/$slug | grep -E '^(src/(config|model|analysis)\.py|results/index\.json|results/quick/|figures/quick/|site/src/data/live/|notes/|results/task_1_2_quick\.json|figures/task_1_2_convergence_quick\.png)' \
  && echo "P1 RED FLAG (src/config|model|analysis allowed only for l0-core)"
# P2 preconditions
git show std/$slug:docs/plan/status/$slug.md | grep -m1 '^| State'
git branch --list "review/$slug-r*"                                                # take the highest round N
N=<n>; git show review/$slug-r$N:docs/plan/status/reviews/$slug.md | sed -n '1,8p'  # verdict line + reviewed commit
git diff --name-only standard-track...review/$slug-r$N                             # exactly docs/plan/status/reviews/$slug.md
rev=<reviewed sha>; [[ $(git rev-parse std/$slug) == $rev* ]] && echo "P2 sha OK" || echo "P2 FAIL: lane moved after review"
# merge: lane, then its review branch
git merge --no-ff std/$slug -m "[integrator] merge $slug" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
git diff --name-only --diff-filter=U                  # conflicts outside integrator-owned paths: git merge --abort, send back
git merge --no-ff review/$slug-r$N -m "[integrator] merge review/$slug-r$N" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
# P3 fast suite
time "$DUQ_PY" -m pytest -m "not slow" -q > .orchestrator/p3.log 2>&1; echo "P3 exit=$?"; tail -3 .orchestrator/p3.log
git revert -m 1 --no-edit HEAD                        # only if P3 fails after a merge; no history rewrite
# P4 index
"$DUQ_PY" -m tools.build_index; echo "P4 exit=$?"
"$DUQ_PY" -c "import json; print('count', json.load(open('results/index.json'))['count'])"
git add results/index.json && git commit -m "[integrator] index after $slug" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
# P5 dirty (production batch: uncommitted records; after a merge use: new=($(git diff --name-only --diff-filter=AM HEAD^1 HEAD -- results/records)))
new=($(git ls-files --others --modified --exclude-standard -- results/records))
"$DUQ_PY" -c "import json,sys; b=[p for p in sys.argv[1:] if json.load(open(p,encoding='utf-8'))['provenance']['dirty']]; print('dirty:',b); sys.exit(1 if b else 0)" $new
# P6 staleness
for p in $new; do
  read c s <<<"$("$DUQ_PY" -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8"))["provenance"]; print(v["git_commit"], v["script"])' $p)"
  git diff --quiet $c HEAD -- src $s || echo "STALE $p ($c)"
done
# P7 slow suite (a > 3 GB job is "big" and runs alone)
"$DUQ_PY" -m tools.runq submit --name slow_g2 --ram-gb 4 --cwd "$MAIN" -- "$DUQ_PY" -m pytest -m slow -q
# P8 claims
"$DUQ_PY" -m tools.check_claims --files TECHNICAL.md README.md; echo "P8 exit=$?"
# P9 lab bundle
"$DUQ_PY" -m tools.export_lab_data
"$DUQ_PY" -c "import json,glob,os; fs=[f for f in glob.glob('site/src/data/live/**/*',recursive=True) if os.path.isfile(f)]; [json.load(open(f,encoding='utf-8')) for f in fs if f.endswith('.json')]; mb=sum(map(os.path.getsize,fs))/2**20; print(len(fs),'files',round(mb,3),'MB'); raise SystemExit(0 if mb<8 else 1)"
git add site/src/data/live && git commit -m "[integrator] lab data: <batch>" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"

# runq (after l0-tools merges). Worker once, in the background:
nohup "$DUQ_PY" -m tools.runq worker --max-jobs 2 --max-ram-gb 5 > .orchestrator/runq-worker.log 2>&1 &
"$DUQ_PY" -m tools.runq status
[[ -z $(git status --porcelain -- src tasks tools) ]] || echo "TREE DIRTY: do not submit"
# submit, heavy-lock wrapped (proposal, D3 option A). wall_s then includes the lock wait.
# If a wrapped job is killed, check $MAIN/.git/duq-heavy.lock/owner and release it by hand.
J=<lane>_<what>; CMD="$DUQ_PY -m tasks.<script> <args>"
"$DUQ_PY" -m tools.runq submit --name $J --ram-gb <est> --cwd "$MAIN" -- /bin/zsh -c \
  "L=$MAIN/.git/duq-heavy.lock; until mkdir \$L 2>/dev/null; do sleep 30; done; echo \"integrator runq $J \$(date +%H:%M)\" > \$L/owner; trap 'rm -rf \$L' EXIT; $CMD"

# mini-lane §6.4: edit only the NA_EIG_MAX line (and, if present, the one assertion)
git diff -- src/config.py tests/test_l0_core.py
git add src/config.py tests/test_l0_core.py && git commit -m "[integrator] mini-lane: NA_EIG_MAX, NB_EIG_MAX = (<Na>, <Nb>) from l1-spectral" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
# upstream §6.5
git fetch origin; git log --oneline 485b6e7..origin/intro-track-tasks
git merge origin/intro-track-tasks -m "[integrator] merge upstream intro-track-tasks" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
# freeze
smoke=$MAIN/.orchestrator/smoke-$(date +%H%M)         # or $TMPDIR/duq-smoke-HHMM from an unsandboxed shell
git clone --branch standard-track "$MAIN" $smoke
(cd $smoke && time PY="$DUQ_PY" bash run_all.sh --quick) 2>&1 | tee $smoke.log
[[ -n $GEMINI_API_KEY ]] && "$DUQ_PY" tools/ai_review.py --provider gemini --diff intro-track-tasks
git tag freeze-0800                                   # local only
git push -u origin standard-track                     # ONLY after Harshit's explicit OK, logged (see D1)
# ledger after every event
git add docs/plan/status/integrator.md && git commit -m "[integrator] ledger: <event>" -m "Co-Authored-By: Cursor Agent <cursoragent@cursor.com>"
```

### Results
| Check | Last result | Time (EDT) | Baseline for the next comparison |
|---|---|---|---|
| P1 | not run yet (no merge) | | |
| P2 | not run yet (no merge) | | |
| P3 | `"$DUQ_PY" -m pytest -m "not slow" -q` → `no tests ran in 0.01s`, pytest exit 5 (nothing collected: `tests/` and `pytest.ini` arrive with `l0-core`); 0.35 s wall | 18:37 | 0 passed, 0 skipped |
| P4 | tools not merged (`tools/` on `standard-track` has only `ai_review.py`; no `results/records/`) | 18:37 | count n/a |
| P5 | no records yet | | |
| P6 | no records yet | | |
| P7 | not run (G2) | | |
| P8 | not run (no `tools/check_claims.py` yet) | | |
| P9 | not run (`site/` absent on `standard-track`) | | |

## Gates
**G0 6:45 PM**
- [x] `setup` DONE, pins recorded (`ed67136`; G0-env PASSED 18:31)
- [ ] `l0-core` merged; P3 green
- [ ] Ledger line "CONTRACT frozen at `<sha>`"
- [x] `l0-tools` and `l6-lab` IN_PROGRESS (Lab on mock data), as of 18:39

**G1 9:45 PM**
- [ ] `l1-spectral` merged (anchor table + cost profile in its status), §6.4 mini-lane applied
- [ ] `l2a-gamma-z`, `l3-prep`, `l4a-readout` merged
- [ ] `l0-tools` merged; wrapped intro records `results/records/t1_*.json` on the branch
- [ ] `l5-circuit` IN_PROGRESS
- [ ] Worker running

**G2 1:30 AM**
- [ ] `l2b-gamma-x` merged (Γ_X eig vs td within tolerance at small α, with channel overlays)
- [ ] `l4c-capstone` merged (linear-response frontier + two-mode validation)
- [ ] `l8-felis` merged or cut
- [ ] `l5-circuit` merged
- [ ] `l4b-tradeoff` grid queued
- [ ] P7 slow suite passed (`slow_g2` through runq)
- [ ] Lab refreshed (§6.3); `l7-docs` started

**G3 7:00 AM**
- [ ] All physics lanes merged or logged as cut; no physics job running except logged cut-if-not-done-by-7:45

**Freeze 8:00 AM:** see Freeze checklist.

### Stand-up notes (`merged · running · queued · slipped/cut · decisions`)
- **Phase 0, 18:40:** merged: `setup` (`ed67136`). Running: `l0-core`, `l0-tools`, `l1-spectral`, `l4a-readout`, `l5-circuit`, `l6-lab`. Queued: nothing (tools not merged). Slipped/cut: none; `l0-core` is at "tests first" (`8dee725`), 5 min before the G0 target. Decisions: D1 (`gh` / workflow scope), D2 (upstream `intro-track-tasks` moved, overlaps `l3-prep`), D3 (runq and the heavy lock); none blocking.

## Jobs
| name | lane | ram_gb | submitted | state | wall_s | log | record ids | committed sha |
|---|---|---|---|---|---|---|---|---|

None yet (tools not merged; worker not started).

## Mini-lane edits
None yet. Plan: right after `l1-spectral` merges and before G1, with no job running. Take `NA_EIG_MAX, NB_EIG_MAX` from `status/l1-spectral.md`, computed against the **4 GB / 10 min** cap on this machine, and log the comfortable pair (≤ 5 min, ≤ 3 GB).

## Upstream merges
None yet. Baseline after `git fetch origin` at 18:38: `origin/intro-track-tasks` = `5531008`, which is 3 commits past the `485b6e7` cut point (`5b3200a`, `1965bd2`, `5531008`; commits dated 16:37–18:00). It does not touch `src/`. It is not merged; see D2.

## Cuts
None.

## Sent back
| lane | time | failed check | exact output | what to do |
|---|---|---|---|---|

None.

## PUSH REQUESTED
- None requested yet.
- **Standing note (18:40):** `gh` is not installed on this machine, and git credentials and token scopes are unverified. `standard-track` will carry `.github/workflows/tests.yml` (l0-tools) and `.github/workflows/pages.yml` (l6-lab). GitHub rejects a push that adds or changes workflow files unless the credential has the `workflow` scope. See D1. Non-blocking.

## DECISION NEEDED
**D1 (18:40): `gh` is absent, and pushing workflow files needs the `workflow` scope.**
> **Q:** `gh` is not installed and the push credential is unverified. Who pushes `standard-track` (which will contain `.github/workflows/*`), and with what credential?
> **Options:** A) Harshit pushes from a session with `gh auth login` plus `gh auth refresh -s workflow` (or a PAT with the `workflow` scope). B) Push without the workflow files (cut item 9, CI; Pages deploy then needs a manual setup). C) Install `gh` on this machine at push time.
> **Recommendation:** A, settled before the first push request (the G2 backup around 1:30 AM; at the latest the 10:30 AM public-repo deadline).
> **Blocking?** no. Nothing is pushed without Harshit's explicit OK anyway.

**D2 (18:40): upstream `intro-track-tasks` moved and overlaps lane-owned files.**
> **Q:** `origin/intro-track-tasks` is at `5531008`, 3 commits past the `485b6e7` cut point. It adds Task 1.3b/c: `tasks/task_1_3b.py` (a path CONTRACT §1 gives to `l3-prep`), `notebooks/05_task_1_3b_logical_prep.ipynb` (l3-prep will write `05_task_1_3b_prepare_zero.ipynb`), `results/task_1_3b.json` and `figures/task_1_3b_logical_prep.png`. It also edits `run_all.sh` (owned by `l0-tools`), `README.md` and `TECHNICAL.md` (owned by `l7-docs`), `tasks/task_1_3a.py`, `notebooks/04_task_1_3a_which_state.ipynb` and `results/task_1_3a.json`. The `task_1_3a.json` change is additive only (`gamma_vs_fit_start_us`, `gamma_nonlinear_fit_per_us`); `parity_decay_fit_per_us = 0.5134564726057531` is unchanged, so l0-tools' wrapped `t1_3a` value is unaffected. No `src/` changes. When and how do we merge it?
> **Options:** A) Merge it into `standard-track` right after `l0-core` (G0), before the `l3-prep` worktree is cut. `l3-prep` then starts from this script and turns it into records (its allowlist already covers `tasks/task_1_3b.py`), and `l0-tools` merges `standard-track` to resolve `run_all.sh` before its review. B) Defer until `l3-prep` has merged, resolve `tasks/task_1_3b.py`, `run_all.sh`, `README.md` and `TECHNICAL.md` `--ours`, and keep the upstream notebook, results and figure as intro-only files. That leaves two notebook 05s and two 1.3b implementations. C) Do not merge; cite the upstream branch in the docs.
> **Recommendation:** A. It is one merge with no duplicated 1.3b work, and `l3-prep` gets a working starting point. Harshit should tell `l3-prep` whether to extend or replace the upstream script, and remind Pranav that README/TECHNICAL belong to the docs lane (HUMAN_TRACK message).
> **Blocking?** not yet; it needs an answer before `l3-prep` launches (around G0). Nothing merged meanwhile.

**D3 (18:40): how runq worker jobs take the shared heavy lock.**
> **Q:** Every runq job runs longer than 15 min, so under RUNBOOK §3 each one must hold the heavy lock. That serializes the worker to one heavy job at a time, and `--max-jobs 2` then only helps light jobs. Which protocol?
> **Options:** A) Wrap each submitted command in the lock (template under Commands). Lanes and the worker interleave, with at most one heavy process on the machine. B) The integrator holds the lock for a whole batch (owner `integrator runq-batch`), and the worker runs up to 2 jobs within 5 GB; lanes cannot start heavy in-lane runs until the batch drains. C) No lock for worker jobs; rely on `--max-ram-gb 5` (risk: a lane's 3 GB run plus 5 GB of worker jobs swaps an 8 GB machine).
> **Recommendation:** A while lanes are active; B overnight (from about 2:00 AM, once lanes are idle), to use both worker slots.
> **Blocking?** no; it matters from the first production batch (after `l0-tools` merges).

## Morning brief
Due by 6:30 AM Sun Oct 25 (brief §6.9): what landed (lanes, records with headline values), what failed (with log pointers), cuts, ranked one-line decisions, and Harshit's 6:30–8:00 to-do.

## Freeze checklist
- [ ] 7:00: fresh-clone smoke started (`run_all.sh --quick` exits 0, no `SKIP` for merged scripts, no traceback, figures in the clone's `figures/quick/`); wall time logged
- [ ] 7:05: slow suite through runq (P7), counts logged
- [ ] After l7's draft merges: P8 `check_claims` 0 fail; failing tokens routed (display or rounding → `l7-docs`; missing, unconverged or dirty record → its lane, else cut the claim by 7:45)
- [ ] If `GEMINI_API_KEY` is set: `ai_review.py` run, `reviews/gemini-*.md` committed, each finding dispositioned (`fixed in <sha>` / `footnoted` / `rejected (why)`)
- [ ] 8:00: `git tag freeze-0800` (local); "FROZEN at `<sha>`" logged
- [ ] 8:00–10:45: only `l7-docs` and the `l6-lab` deploy merge, each followed by P3, P8 and P9

## Acceptance gates (brief §8)
- [ ] Every lane row has a merged sha (with P1–P4 logged) or a logged CUT; no merge without `PASS`/`PASS_WITH_NOTES` on its latest sha
- [ ] Every committed production record passes P5 and P6; `build_index` exits 0 on HEAD
- [ ] P3 and P7 green on `freeze-0800`, with counts
- [ ] P8: 0 fail on the final docs
- [ ] Fresh-clone smoke passed (wall time logged); P9 passes on the final Lab data
- [ ] Every queued job `done`, or `failed`/`cut` with a disposition
- [ ] Mini-lane edit, upstream merges, cuts, send-backs and pushes logged; no push without a logged OK
- [ ] Morning brief by 6:30 AM; stand-up notes for G0–G3 and the freeze

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. A judge picks one Γ_X number in `TECHNICAL.md`: how do you prove that the code which produced it is the code on the branch, and what failure would `provenance.dirty == false` alone not catch?
2. Your fresh-clone smoke test only runs `--quick`. What evidence do you have that the production α = 2.1 eigenvalue numbers would reproduce on another machine, and how long would that take?
3. What did you cut, when and why, and why does each remaining headline claim still stand without it (for example, what backs Γ_X if Felis or the thermal sweep was cut)?

## Event log
- **18:36–18:40 Phase 0:** env set and verified, ledger created, P3 baseline taken (0 passed; no tests on `standard-track` yet), upstream baseline recorded, D1–D3 raised (none blocking). Committed as `[integrator] ledger: start`.
