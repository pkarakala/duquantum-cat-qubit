# Brief `integrator`: Integrator: merges, production runs, gates, freeze

> **Paste into a new Cursor agent (main checkout, NOT worktree mode):** "You are lane `integrator`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/90-integrator.md`, then execute this brief exactly. Keep `docs/plan/status/integrator.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `integrator` | `standard-track`, in the **main checkout** `D:\Brown University\duhack\duquantum-cat-qubit` (no worktree, no `std/` branch) | `setup` (venv `D:\duq-venv` + pins working) | strongest reasoning model (merge judgement) | continuous, Phase 0–5 (Sat 5:30 PM → Sun 10:45 AM) | G0 6:45 PM · G1 9:45 PM · G2 1:30 AM · G3 7:00 AM · freeze 8:00 AM · Devpost 10:45 AM · hacking ends 11:30 AM |

## 1. Goal and why
You are the **only writer of `standard-track`**. Lanes build on `std/<slug>` branches in Cursor worktrees. You turn reviewed lanes into one green, reproducible integration branch. You also run the production jobs that take longer than 15 min (lanes can't), keep the Lab's bundled data fresh, enforce the gates and the cut order, and freeze physics at 8:00 AM.
**Why:** the judged deliverable is a repo where every number in `README.md`/`TECHNICAL.md` is a committed record with `provenance.dirty == false`, a converged `convergence` block and at least one agreeing `cross_check` (CONTRACT §6.2, §11), and where a fresh clone reproduces the figures (`run_all.sh --quick`).
A wrong merge or a stale/dirty record is the most expensive failure in the project, so use judgement over speed. You may be Harshit or a Cursor agent. Either way: **no push without Harshit's explicit OK** (§6.6).

## 2. Read first
- `AGENTS.md`, `docs/plan/README.md` (phases, which brief goes when), `docs/plan/PLAN.md` §8 (timeline) and §11 (risks, cut order).
- CONTRACT §1 (lane → allowlist; **your merge check uses this table**), §2 (env, quick vs production, heavy-job limits), §6.2–§6.3 (record schema, ID regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`), §11 (claim syntax), §12 (`runq`), §13 (Lab data), §14 (status files).
- RESEARCH §9: eigen cost/RAM. The full Liouvillian at 32×12 takes ~30 min, the odd Z2 block ~4 min. This is why LU jobs need RAM accounting.
- `docs/plan/REVIEW_PROTOCOL.md` and `docs/plan/briefs/91-reviewer.md` (verdict format), `docs/plan/HUMAN_TRACK.md` (Harshit sleeps ~2:00–6:00 AM), `docs/plan/status/_TEMPLATE.md`.
- At every merge: the lane's brief §7 (records/jobs) and §12 (hand-off), and its `docs/plan/status/<slug>.md`.

## 3. Allowlist (touch nothing else)
- **Write:**
  - Merge commits on `standard-track` (main checkout only).
  - `docs/plan/status/integrator.md` (the global ledger).
  - Production outputs and derived data: `results/records/**`, `results/arrays/**`, `results/index.json`, `figures/**`, `site/src/data/live/**`.
  - **Mini-lane only (§6.4):** the single line `NA_EIG_MAX, NB_EIG_MAX = None, None` in `src/config.py`, plus, if present, the single `NA_EIG_MAX is None` assertion in `tests/test_l0_core.py`. This is the only edit to a frozen file, and it is logged.
  - The new `reviews/gemini-*.md` written by `tools/ai_review.py` at freeze.
  - The local tag `freeze-0800`.
- **Never edit:**
  - Any other file under `src/`, `tasks/`, `tools/`, `tests/`, `site/` (outside `site/src/data/live/`), or `notebooks/`.
  - CONTRACT, RESEARCH, another lane's status or review file.
  - `notes/`, `prep/`, `docs/challenge_prompt_v4.md`, `docs/handwritten/`, `docs/defense.md`.
- **Never commit:** `results/quick/**`, `figures/quick/**`, `results/logs/**`, `results/task_1_2_quick.json`, `figures/task_1_2_convergence_quick.png` (not git-ignored!), `notes/`.
- **Git rules:**
  - Stage explicit paths only. Never `git add .` or `git add -A`.
  - No rebase, no `--force`, no history rewrites. Never commit to or push `main` or `intro-track-tasks`.

## 4. Interfaces you implement / rely on
You implement no code. You rely on:
- `tools.build_index`:
  - Flags: `[--records-dir results/records] [--out results/index.json] [--quick]`.
  - Exits 1 and writes nothing if any record is invalid (bad id, id ≠ filename, missing field, not `duq.record/v2`).
  - With the default `--out` it **refuses (exit 1) while `git status --porcelain -- src tasks tools` is non-empty**, so commit before indexing.
- `tools.check_claims [--files TECHNICAL.md README.md] [--strict]`:
  - Checks every `` `rec:<id>=<disp>` `` and `` `rec:<id>#<path>=<disp>` `` token: the record exists, the value rounds to the displayed significant figures, `converged` is true (or `null` with notes), at least one `cross_check.agree` is true, and `dirty` is false.
  - Rows with `illustrative` only warn. Prints `N ok, M warn, K fail` and exits 0 only if K = 0.
- `tools.runq`:
  - `submit --name <job> --ram-gb <float> [--cwd <path>] -- <cmd...>`; `worker [--max-jobs 3] [--max-ram-gb 11]`; `status` (prints `name | state | ram_gb | exit | wall_s | log`).
  - A job with `ram-gb > 3` is "big" and runs alone among big jobs. Failed jobs are **never retried**. The worker sets `XLA_FLAGS` per job.
  - Queue dir: `results/logs/runq/` (`$env:DUQ_RUNQ_DIR` overrides). Logs: `results/logs/runq/logs/<name>.log`, so use a unique name per job.
- `tools.export_lab_data` (L6):
  - Reads `results/index.json`, `results/records/` and `results/arrays/`.
  - Writes `site/src/data/live/{records,inflation,errors,readout,verify}.json`. The total must stay < 8 MB (CONTRACT §13).
- `run_all.sh`:
  - Takes the interpreter from env `PY`. Flags: `--intro`, `--standard`, `--quick`, `--dry-run`.
  - Quick mode runs each merged Standard task with `--quick` and prints `SKIP tasks/<t>.py (not merged yet)` for missing ones.
  - It ends with `build_index` and `check_claims` (non-fatal in quick mode).
- `tools/ai_review.py --provider gemini --diff intro-track-tasks` (needs `GEMINI_API_KEY`) writes `reviews/gemini-YYYYMMDD-HHMM.md`.
- **Record fields you check:**
  - `provenance.dirty`, `provenance.git_commit`, `provenance.script`.
  - `convergence.converged`, `cross_check[*].agree`.
  - The id regex above, and the rule that the filename equals the id.
- **Reviewer verdict:** in `docs/plan/status/reviews/<slug>.md`. `PASS` or `PASS_WITH_NOTES` means you may merge. Anything else (or a missing file) means do not merge.

## 5. Tests to write FIRST (TDD)
You own no test file. Your "tests first" are checks **P1–P9**. Copy them into the ledger header at 5:30 PM and run them in order: P1–P4 on every merge, P5–P6 on every production batch, P7–P9 at the gates named.
- **P1 allowlist:** `git diff --name-only standard-track...std/<slug>` is a subset of:
  - the lane's CONTRACT §1 allowlist,
  - `docs/plan/status/<slug>.md`,
  - its own `results/records/<its ids>.json`, `results/arrays/<its ids>.npz` and `figures/task_<its task>_*.png`.

  Any other path means send back. Watch especially for `src/config.py`, `src/model.py`, `results/index.json`, `results/quick/**`, `site/src/data/live/**`, `notes/**` and the two `*_quick` intro files.
- **P2 preconditions:**
  - Status `State` is `DONE`. `DONE_WITH_CONCERNS` merges only if the verdict is `PASS_WITH_NOTES` and addresses each concern.
  - The review verdict is `PASS` or `PASS_WITH_NOTES`.
  - The reviewed sha equals `git rev-parse --short std/<slug>`. A lane commit after the review needs a re-review.
- **P3 fast suite:** `-m "not slow" -q` exits 0 in < 2 min, and the passed count does not go down from the previous ledger value. Log `N passed, M skipped`.
- **P4 index:** `build_index` exits 0, and `count` ≥ the previous count.
- **P5 dirty:** every new or modified `results/records/*.json` has `provenance.dirty == false`.
- **P6 staleness:** for every new record, `git diff --quiet <git_commit> HEAD -- src <script>` exits 0. This proves the code that produced the number is the code on HEAD. `dirty` alone misses a merge that lands mid-job.
- **P7 slow suite** (at G2 and at freeze): `-m slow` exits 0.
- **P8 claims** (after l7's draft is merged, and at freeze): `check_claims --files TECHNICAL.md README.md` exits 0.
- **P9 lab bundle:** `site/src/data/live/*.json` parse as JSON, and their total is < 8 MB.

## 6. Method, step by step
**6.0 Phase 0 (5:30–6:45 PM).**
1. Set the env vars (§9). Check that `& $env:DUQ_PY -m src.config` prints the units check and that `git branch --show-current` prints `standard-track`.
2. Create `docs/plan/status/integrator.md` with these sections:
   - **Lanes:** a table with one row per lane (`setup`, `l0-core`, `l0-tools`, `l1-spectral`, `l2a-gamma-z`, `l2b-gamma-x`, `l3-prep`, `l4a-readout`, `l5-circuit`, `l4b-tradeoff`, `l4c-capstone`, `l6-lab`, `l7-docs`, `l8-felis`). Columns: `lane | state | branch | last commit | reviewer verdict | merged commit | records produced | jobs queued`.
   - **Checks P1–P9:** last result and time.
   - **Gates:** stand-up notes.
   - **Jobs:** `name | lane | ram_gb | submitted | state | wall_s | log | record ids | committed sha`.
   - **Mini-lane edits**
   - **Upstream merges**
   - **Cuts**
   - **Sent back**
   - **PUSH REQUESTED**
   - **DECISION NEEDED**
   - **Morning brief**
   - **Freeze checklist**
3. Commit with `git add docs/plan/status/integrator.md`, message `[integrator] ledger: start`. Commit the ledger after every event below (`[integrator] ledger: <event>`).

**6.1 Merge protocol (per lane; ≈10 min each).**
1. Run `git fetch`. Local `std/*` branches from worktrees are already visible; the fetch only refreshes `origin/*`.
2. Run P1 and P2. On failure, send back (step 6).
3. Merge with `git merge --no-ff std/<slug> -m "[integrator] merge <slug>"`.
4. **If the merge conflicts**, list the files with `git diff --name-only --diff-filter=U`.
   - **Any file outside** `results/records/**`, `results/arrays/**`, `results/index.json`, `figures/**`, `site/src/data/live/**`: run `git merge --abort` and send back ("merge `standard-track` into `std/<slug>`, resolve, re-review").
   - **`results/index.json` or `site/src/data/live/**`:** run `git checkout --ours <f>` (you regenerate both below).
   - **A conflicting record:** this is an id collision (CONTRACT §6.3 forbids it). Abort and raise a DECISION NEEDED.
   - **A figure:** keep the lane's version (`--theirs`) only if the lane owns that `figures/task_<its task>_*` path. Otherwise abort.
   - Then `git add <files>` and `git commit --no-edit`.
5. Run P3. On failure, run `git revert -m 1 --no-edit HEAD` (no history rewrite), log it and send back.
6. **Send-back:**
   - Add a row to **Sent back** (`lane | time | failed check | exact output | what to do`) and commit the ledger.
   - Give the lane agent this paste: "Integrator sent you back. Run `git show standard-track:docs/plan/status/integrator.md`, read the Sent back row for your lane, fix it on `std/<slug>`, set State `DONE` again, and get a re-review."
7. Run P4 (`build_index`). Commit with `git add results/index.json`, message `[integrator] index after <slug>`. Then fill the lane row: merged sha, records, jobs.
8. **Merge order:** `l0-core` → `l0-tools` → `l1-spectral` → `l2a-gamma-z`, `l3-prep`, `l4a-readout`, `l5-circuit` (any order) → `l2b-gamma-x` → `l4b-tradeoff` → `l4c-capstone` → `l8-felis` → `l6-lab` (on real data) → `l7-docs` (drafts at G2, final in Phase 5).
   - Until `l0-tools` is merged there is no `build_index` or `runq`. Skip those steps and note "tools not merged".

**6.2 Production runs (jobs > 15 min, from merged lanes' "Jobs to queue").**
1. Start the worker **once**, in its own terminal: `& $env:DUQ_PY -m tools.runq worker --max-jobs 3 --max-ram-gb 11`.
   - The cap of 11 GB of the 15.9 GB leaves room for the OS, Cursor and the browser. If Task Manager memory goes above 90%, restart the worker with `--max-ram-gb 8`.
   - If the worker exits, restart it.
2. Before submitting, the tree must be clean: `git status --porcelain -- src tasks tools` is empty. Otherwise every record will be `dirty: true`.
3. Submit each job:
   - Copy the lane's exact line. Use `$env:DUQ_PY` as the interpreter and add `--cwd "D:\Brown University\duhack\duquantum-cat-qubit"`.
   - Name it `<lane>_<what>` (unique). Keep the lane's `--ram-gb`; raise it if the lane's profile shows a higher peak RSS.
   - Anything > 3 GB is a big LU job: one at a time, enforced by runq. Never start one by hand beside the worker.
4. **While a job runs:** do not merge a lane that changes `src/` or that job's `tasks/` script. Lanes that only touch docs, site or tests may merge. If you must merge one anyway, P6 will flag the record and the job is re-run.
5. Check `& $env:DUQ_PY -m tools.runq status` at every stand-up. **A failed job:** paste the last 20 log lines into the ledger, do not retry blindly, and send back to the lane (or apply the cut order, §6.8).
6. **When a batch is done:**
   - Run P5 and P6 on the new records.
   - Commit with explicit `git add` of `results/records/<ids>.json`, `results/arrays/<ids>.npz` and the figures, message `[integrator] production: <lane> <ids>` (for more than 4 ids: `<first id> +N`).
   - Then run P4 and commit `results/index.json`.
7. Before Harshit sleeps (~1:45 AM), make sure everything for the night is queued: the 2.4b Γ_X(ε_Z) grid, the α ≥ 2.1 large-truncation confirmations, the thermal points, and the α = 1.0 time-domain flip check. Keep the laptop plugged in and awake.

**6.3 Lab data (after each production batch, and after any merge that adds records).**
- Run `& $env:DUQ_PY -m tools.export_lab_data`, then P9.
- Commit with `git add site/src/data/live`, message `[integrator] lab data: <batch>`.

**6.4 Mini-lane: eigen basis caps (right after `l1-spectral` merges, before G1).**
1. Take `NA_EIG_MAX, NB_EIG_MAX` from `status/l1-spectral.md`: the largest Na finished at Nb = 8, and the largest Nb finished at Na ≥ 28, each within 10 min and 6 GB.
2. Edit only that one line of `src/config.py`.
3. If `tests/test_l0_core.py` asserts `NA_EIG_MAX is None`, change only that assertion to `isinstance(C.NA_EIG_MAX, int) and isinstance(C.NB_EIG_MAX, int)`.
4. Run P3. Commit with `git add src/config.py tests/test_l0_core.py`, message `[integrator] mini-lane: NA_EIG_MAX, NB_EIG_MAX = (<Na>, <Nb>) from l1-spectral`.
5. Log it under **Mini-lane edits**, including the "comfortable" pair (≤ 5 min, ≤ 3 GB). Use the comfortable pair for `--ram-gb ≤ 3` submissions.
6. Do not run while jobs are running (P6).

**6.5 Upstream (Pranav).** If `origin/intro-track-tasks` moved:
1. `git fetch origin`, then `git merge origin/intro-track-tasks -m "[integrator] merge upstream intro-track-tasks"`.
2. Resolve conflicts in shared files in favour of `standard-track` (`git checkout --ours <f>`). Keep his new intro-only files.
3. Run P3 and P4.
4. Log every file resolved `--ours` under **Upstream merges**, so Harshit can tell Pranav.

**6.6 Push requests.**
1. Never push on your own. Write `PUSH REQUESTED: <reason>` in the ledger (for example "Cursor cloud agent needs std branches", "G2 backup", "repo public by 10:30 AM") and ask Harshit in chat.
2. Only after his explicit OK, run `git push -u origin standard-track` and log the time and his OK.
3. Never push `intro-track-tasks`, `main` or tags.

**6.7 Gates.** At each gate time, tick the checklist, write a 4-line stand-up note in **Gates** (`merged · running · queued · slipped/cut · decisions`) and commit the ledger.
- **G0 6:45 PM:**
  - `setup` DONE (pins recorded).
  - `l0-core` merged; P3 green.
  - CONTRACT and claim syntax frozen: ledger line "CONTRACT frozen at `<sha>`".
  - `l0-tools` and `l6-lab` IN_PROGRESS (Lab on mock data).
- **G1 9:45 PM:**
  - `l1-spectral` merged, with the anchor table and cost profile in its status file, and §6.4 applied.
  - `l2a-gamma-z`, `l3-prep`, `l4a-readout` merged.
  - `l0-tools` merged, and the wrapped intro records `results/records/t1_*.json` are on the branch.
  - `l5-circuit` IN_PROGRESS.
  - Worker running.
- **G2 1:30 AM:**
  - `l2b-gamma-x` merged: Γ_X two ways (eig vs td) agree within their stated tolerance at small α, with the channel overlays.
  - `l4c-capstone` merged: linear-response frontier plus two-mode validation.
  - `l8-felis` merged (or cut).
  - `l5-circuit` merged.
  - The `l4b-tradeoff` grid is queued.
  - P7 slow suite passed. Submit it through runq, since it is a heavy job: `--name slow_g2 --ram-gb 4 -- $env:DUQ_PY -m pytest -m slow -q`.
  - Lab refreshed (§6.3); `l7-docs` started.
- **G3 7:00 AM:** all physics lanes merged or logged as cut. No physics job is still running, except ones that are logged as cut-if-not-done-by-7:45.
- **Freeze 8:00 AM:** §6.9 complete. **No new numbers after 8:00:** no production commits, no record changes. Docs, Lab and slides only.
- **Devpost submitted 10:45 AM** (Harshit). Hacking ends 11:30 AM.

**6.8 Cut procedure.** If any gate slips by more than 1 h:
1. Cut the next item in this order:
   1. live sandbox
   2. gradient refinement
   3. Felis
   4. thermal beyond 3 values
   5. 2.4b `extra_H` asymmetry sweep
   6. κ_b critical-damping option
   7. 1.3b method (iii)
   8. Readout designer page (replaced by a static figure)
   9. CI
2. Log it under **Cuts**: `CUT <item> at <time>: <gate> slipped <x> h; affected lanes; doc impact`.
3. Tell `l7-docs` (via the ledger) that the item must not be claimed.
4. Kill or cancel the related queued jobs.

**Never cut:** convergence records; the Γ_Z check; Γ_X two ways at small α with the channel overlays; the readout trade-off; the SVD-vs-square comparison; a reproducible README; defense prep.

**6.9 Morning brief (write by 6:30 AM in the ledger, for Harshit).**
- What landed: lanes, and records with their headline values.
- What failed: jobs and tests, each with a log pointer.
- Cuts made or recommended.
- Decisions needed, ranked, each answerable in one line.
- What he must do 6:30–8:00 (G3 check, review the final numbers, defense prep).

**Freeze procedure (7:00–8:00 AM).**
1. **7:00:** start the fresh-clone smoke in its own terminal (§9). It passes when `run_all.sh --quick` exits 0, prints no `SKIP` for any merged script, shows no traceback, and figures appear in the clone's `figures/quick/`. Log the wall time.
2. **7:05:** run the slow suite through runq (P7).
3. **After l7's draft is merged:** run P8.
   - A failing token caused by display or rounding goes to `l7-docs`.
   - A missing, unconverged or dirty record goes to its lane; if it can't be fixed by 7:45, cut the claim from the docs.
4. **If `GEMINI_API_KEY` is set:** run `ai_review.py` (§9), then commit the new `reviews/gemini-*.md` as `[integrator] gemini freeze review`.
   - In the ledger, list each finding as `finding → fixed in <sha> / footnoted / rejected (why)`.
   - Fixes after 8:00 are text only.
5. **8:00:** run `git tag freeze-0800` (local only) and log "FROZEN at `<sha>`". The 8:00–10:45 work is merging `l7-docs` and the `l6-lab` deploy, with P3, P8 and P9 after each merge.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **Ledger:** `docs/plan/status/integrator.md`, committed after every event.
- **Merge commits** on `standard-track`, `[integrator] merge <slug>`; one per lane.
- **Production outputs** from the queue: `results/records/<lane ids>.json`, `results/arrays/<ids>.npz` and `figures/task_*.png`. You create no record ids of your own; the ids are the lanes' (CONTRACT §6.3).
- **Derived files:** `results/index.json` (after every merge and batch) and `site/src/data/live/*.json` (after every batch).
- **Quick vs production:** quick outputs (`results/quick/`, `figures/quick/`) are never committed. Only production records with P5 and P6 passing are committed.
- **Jobs to queue:** you don't queue jobs for anyone else. You consume the lanes' queues (§6.2).
- **Other outputs:** `reviews/gemini-*.md` (if a key is available) and the local tag `freeze-0800`.

## 8. Acceptance gates (ALL must pass before DONE)
1. Every lane row has either a merged sha (with P1–P4 logged) or a logged CUT. No lane was merged without `PASS`/`PASS_WITH_NOTES` on its latest sha.
2. Every committed production record passes P5 and P6. `build_index` exits 0 on HEAD.
3. Fast suite (P3) and slow suite (P7) green on `freeze-0800`, with the counts logged.
4. `check_claims --files TECHNICAL.md README.md` reports 0 fail on the final docs (P8).
5. The fresh-clone smoke passed, with its wall time logged. P9 passes for the final Lab data.
6. Every queued job is `done`, or `failed`/`cut` with a disposition in the ledger.
7. The mini-lane edit and every upstream merge, cut, send-back and push are logged. No push happened without a logged OK from Harshit.
8. The morning brief was written by 6:30 AM, and the stand-up notes for G0–G3 and the freeze are present.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git fetch; git diff --name-only standard-track...std/<slug>              # P1
git merge --no-ff std/<slug> -m "[integrator] merge <slug>"
git diff --name-only --diff-filter=U                                     # conflicts?  else: git merge --abort
& $env:DUQ_PY -m pytest -m "not slow" -q                                  # P3
& $env:DUQ_PY -m tools.build_index; git add results/index.json; git commit -m "[integrator] index after <slug>"
& $env:DUQ_PY -m tools.runq worker --max-jobs 3 --max-ram-gb 11           # own terminal, once
& $env:DUQ_PY -m tools.runq submit --name <job> --ram-gb <est> --cwd "D:\Brown University\duhack\duquantum-cat-qubit" -- <command>
& $env:DUQ_PY -m tools.runq status
# P5 + P6 on new records
$new = git ls-files --others --modified --exclude-standard -- results/records
& $env:DUQ_PY -c "import json,sys; b=[p for p in sys.argv[1:] if json.load(open(p,encoding='utf-8'))['provenance']['dirty']]; print('dirty:',b); sys.exit(1 if b else 0)" $new
foreach ($p in $new) { $r = Get-Content $p -Raw | ConvertFrom-Json; git diff --quiet $r.provenance.git_commit HEAD -- src $r.provenance.script; if ($LASTEXITCODE -ne 0) { "STALE $p" } }
& $env:DUQ_PY -m tools.export_lab_data; (Get-ChildItem site/src/data/live -Recurse | Measure-Object Length -Sum).Sum / 1MB   # P9 < 8
& $env:DUQ_PY -m tools.runq submit --name slow_g2 --ram-gb 4 --cwd "D:\Brown University\duhack\duquantum-cat-qubit" -- $env:DUQ_PY -m pytest -m slow -q
git fetch origin; git merge origin/intro-track-tasks -m "[integrator] merge upstream intro-track-tasks"
# Freeze
& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md
if ($env:GEMINI_API_KEY) { & $env:DUQ_PY tools/ai_review.py --provider gemini --diff intro-track-tasks }
$smoke = "$env:TEMP\duq-smoke-$(Get-Date -Format HHmm)"; git clone --branch standard-track . $smoke
Push-Location $smoke; $env:PY = "D:/duq-venv/Scripts/python.exe"; bash run_all.sh --quick; Pop-Location
git tag freeze-0800
git push -u origin standard-track          # ONLY after Harshit's explicit OK, logged
```

## 10. Out of scope / do not
- Do not fix lane code yourself: no physics edits and no test loosening. The only exception is the §6.4 mini-lane. Send work back instead.
- Do not merge without a review verdict, or on a red P3.
- Do not hand-run heavy jobs beside the worker. Do not run more than 3 heavy jobs, or more than 1 LU job above 3 GB, at a time.
- Do not change tolerances, record ids, CONTRACT or RESEARCH.
- Do not commit quick outputs, logs or `notes/`.
- Do not push without Harshit's OK. Never push tags, `main` or `intro-track-tasks`.
- Do not add numbers after 8:00 AM.
- Do not write or answer Harshit's explain-back questions, `docs/defense.md` or `docs/handwritten/`.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write this block in the ledger and ask Harshit in chat:
> **Q:** `<lane>` <failed check, e.g. "P6: t2_1.gamma_x.eig.two_mode.a2.10.nth0 produced at abc1234, src/spectral.py changed since">. Re-run, accept, or cut?
> **Options:** A) re-queue the job now (`<wall est>`, `<ram>` GB); B) keep the old record out of the docs and footnote it; C) cut per §6.8.
> **Recommendation:** …  **Blocking?** no; meanwhile I merged/queued <x>.

**Typical triggers:**
- A conflict outside the integrator-owned paths.
- A review verdict that is missing at a gate.
- A job failed twice, or a job projected to run past 7:45 AM.
- A RAM over-commit (the machine swaps).
- `build_index` invalid.
- A record id collision.
- l1's `NA_EIG_MAX` recommendation missing or above 6 GB.
- Pranav's upstream touching `src/`.

**Fallbacks:**
- Lower the worker to `--max-ram-gb 8 --max-jobs 2`.
- Report only the converged feasible α range, with one-mode results above it (labelled).
- If `export_lab_data` breaks, the Lab ships on its last good `live/` data. If that fails too, use static figures.
- If the smoke test fails on Git Bash paths, retry with `--dry-run` and log it as "smoke partial".

**Cut line:** the §6.8 order. The never-cut list is not negotiable without Harshit's explicit decision.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE, `docs/plan/status/integrator.md` contains:
- State `DONE`, the `freeze-0800` sha, and the last commit.
- The full lane table: every lane merged (with sha) or CUT (with time and reason).
- The P1–P9 results with their last outputs: fast and slow counts, `check_claims` `N ok, M warn, 0 fail`, smoke wall time, and lab bundle size in MB.
- The jobs table, every job with a disposition and the committed sha.
- The mini-lane edit (`NA_EIG_MAX, NB_EIG_MAX` values and sha), upstream merges (`--ours` files), cuts and send-backs.
- PUSH REQUESTED entries with Harshit's OK time.
- The Gemini review file and its acted-on list.
- The morning brief, and any open DECISION NEEDED items.

Explain-back questions (write these in the ledger; Harshit answers in `docs/defense.md`):
1. A judge picks one Γ_X number in `TECHNICAL.md`: how do you prove that the code which produced it is the code on the branch, and what failure would `provenance.dirty == false` alone not catch?
2. Your fresh-clone smoke test only runs `--quick`. What evidence do you have that the production α = 2.1 eigenvalue numbers would reproduce on another machine, and how long would that take?
3. What did you cut, when and why, and why does each remaining headline claim still stand without it (for example, what backs Γ_X if Felis or the thermal sweep was cut)?
