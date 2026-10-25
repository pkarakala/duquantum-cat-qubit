# Upstream the Academy can use

Fetched `origin` on 2026-10-25. Compared with `485b6e7` (Pranav's intro-track merge) and with `prod/release` at `4bdc4cf`. Nothing here was merged. Two pieces are drop-in fixes that do not touch `server/` or `site/`; they were left unapplied.

## What moved

| Branch | Tip | This fetch |
|---|---|---|
| `origin/main` | `dd52ed7` | Moved. Merge of PR #16. |
| `origin/claude/project-thread-4lnr7v` | `eb69ae0` | New. Pranav's Academy commits. Not on `main`. |
| `origin/XZ-codex-intro-review` | `4e84d40` | Moved. Philip (`xuz144`). |
| `origin/claude/project-thread-qre8s0` | `60e20d5` | New. Claude notebook 09. Already merged to `main` by Pranav. |
| `origin/claude/project-thread-bun0bw` | `5b65b82` | Moved. Claude notebooks. Already merged to `main` by Pranav. |
| `origin/intro-track-tasks` | `5531008` | Unchanged. Three Claude commits after `485b6e7`, already on `main`. |
| `origin/standard-track` | `b808ed4` | Unchanged. Same tip as `origin/product-academy`. |
| `origin/product-academy` | `b808ed4` | Unchanged. |
| `origin/prod/release` | `4bdc4cf` | Unchanged. |

Human authors after `485b6e7`: Pranav Reddy, Philip (git author `xuz144`), and Harshit Aggarwal. Harshit's seven Academy-planning commits are already ancestors of `prod/release`. Claude is the other author on these branches. No other human author pushed.

`prod/release` and `main` diverged at `485b6e7`. Release `src/` is still the core (`model`, `config`, `analysis`, `plotting`, `results`). `model.py` matches `main`. `config.py` and `analysis.py` do not.

## Useful commits

Merge means "land this on `prod/release`". `yes` is only the drop-in hunk or file named in the reason. Those were not applied.

| SHA | Branch | What it adds | Merge | Reason |
|---|---|---|---|---|
| `140a7ad9f73555b2e633b87bbec081231c2d4e19` | `origin/claude/project-thread-4lnr7v` | `src/linresp.py` (82 lines): `response`, `response_matrices`, `optimal_pulse`, `ringing`. Square-pulse SNR 0.9541, poles −4.08 ± 19.72i /µs. The same commit also rewrites the linresp fixtures so Δb = b(+α) − b(−α), defaults dev CORS to the Vite origin, and adds the `psycopg` pool extra plus vitest. | later | The commit edits `server/` and `site/` on top of a copy of the product sitting on `main`, so it will not apply onto `prod/release`. The new file `src/linresp.py` does not touch `server/` or `site/`. Release already imports it (`challenge.py` calls `response`, `response_matrices`, and `optimal_pulse`) and the file is absent. That file is a drop-in. Not applied. |
| `e500059b0d55ea833da14760570890b4e0b791e5` | `origin/main` | `settle_time` returns `inf` when the trace never stays inside the band. On `prod/release` the same function returns the last sample instead. The rest of the commit is claim text, regenerated figures, and task-script labels. | yes | Only the `src/analysis.py` hunk. That commit does not touch `server/` or `site/`, and the function body on `prod/release` matches the pre-fix version, so the hunk is a drop-in. Not applied. Do not take the figures or the claim edits. |
| `1d90427990b0e5ba580c67fa6483156205b0d038` | `origin/claude/project-thread-4lnr7v` | Replaces the four "ships with the physics lab" research placeholders with Results pages for Tasks 2.1–2.4, plotted from `results/` by `site/scripts/export_results.py`. L8 cost becomes pulse energy ∫ε²dt. Under the old ∫\|δa\|² proxy a resonant pulse scored about 5× worse than square. The shaped pulse is now cos(ω_r t), 3.35× the square SNR. Plot titles use Plotly 3's `title.text`. | later | Real L8 bug and the pages `MORNING.md` still lists as placeholders, but the commit only touches `site/` and sits on the unmerged `main` snapshot. Port it; do not merge the commit. |
| `90375a514b7ae359d12caafd4568f20b2cd75321` | `origin/XZ-codex-intro-review` | Bit-flip and phase-flip fits: new `src/rates.py` and `src/rate_solver.py` (numpy/scipy only), plus `tasks/task_2_1.py`, `tasks/task_2_2.py`, `tasks/task_2_common.py`, and `tests/test_rates.py`. | later | The two `src/` modules do not touch `server/` or `site/`, do not edit frozen `config.py` / `analysis.py` / `model.py`, and are already identical on `main`. They are a drop-in as files. Not applied: the Academy server does not import them, and the task scripts need `plotting.panel`, which `prod/release` does not have. |
| `7fd4e7ecfd7010005de158276d9c6705313b1ad5` | `origin/XZ-codex-intro-review` | Buffer readout: new `src/readout.py` and `tasks/task_2_3.py`, plus tests. Also adds `READOUT_DRIVE_RATIO = 0.05` and `EPS_Z` to `src/config.py`, and edits `src/plotting.py` and `tasks/task_1_3b.py`. | later | Does not touch `server/` or `site/`, but it is not a drop-in: it writes the frozen config and shared plotting. `src/readout.py` is already on `main` with no content diff. |
| `4e84d4054c043ddc395d180fcc82143d5551d8a2` | `origin/XZ-codex-intro-review` | Task 2.4 readout study: contrast/error tradeoff, enlargement/read/restore, `tasks/task_2_4.py` and the campaign runner, `src/spectral.py`, `src/circuit.py`, and the `src/readout_*` modules, with notebooks, figures, and 460 `results/` files. Author reports 131 tests passed. `main` has no `tasks/task_2_4.py`. | later | This is the study L8 and the Results pages describe, and it does not touch `server/` or `site/`. It is not a drop-in: it is a parallel stack (its `src/spectral.py` differs from `main`) and it depends on the earlier commits on this branch. Review against the lane contract before any of it lands on `prod/release`. |

## Looked at, do not merge

| SHA | Branch | What it is | Merge | Reason |
|---|---|---|---|---|
| `cb8d1f7c96641254dbcb4be7663f3087520b0e53` | `origin/claude/project-thread-4lnr7v` | Copies the Academy product onto `main` (289 files, parent `5605d77`). | no | Snapshot of an older product tree. `prod/release` has 36 commits that are not in that parent. Merging it back would duplicate the app and drop the later release work. |
| `eb69ae08056acd6164bd72a6f20291c017716130` | `origin/claude/project-thread-4lnr7v` | README sentence linking the Academy and crediting Grok and Cursor. | no | Challenge README only. It does not change the app. |
| `4dcceaf4070eb3bf0ade5720f70efceb56681782` | `origin/main` (Philip) | Intro-task validation, convergence write-up, figures, notebooks. | no | Already on `main`. Submission report, not the Academy app. |
| `22c5e15ecedbc953c0cc9c3065ed9b6a1fc9c6f9` | `origin/main` (Philip) | Wigner GIFs in the challenge README, plus a plotting helper. | no | Already on `main`. The site does not use those GIFs. |
| `dd52ed7dcf43de4ad3e3e60461c24f0f21533a28` | `origin/main` | Pranav merges Claude's notebook 09 (Task 2.4 walkthrough, PR #16). | no | Notebook prose on `main`. The app wants the underlying numbers, which are the Task 2.4 commit above, not this merge. |

Philip's other commits on `origin/XZ-codex-intro-review` after `485b6e7` are report wording, Wigner-marker styling, and settling-plot polish (`921505a`, `f3a5a29`, and the commits from `20ac8f2` through `ed64fd6`). Merge: no. They do not change what the Academy runs.

Pranav's other commits on `origin/main` after `485b6e7` are README edits, cloud-batch logs, and merges of Claude notebook branches (PRs #4 through #14). Merge: no. They document the challenge submission. They are not app code.

## Bug still open on `prod/release`

`server/precompute.py` stores one well's buffer amplitude as `delta_b` and integrates SNR from that. The leaderboard definition is Δb = b(+α) − b(−α) = 2 b₊, so those fixtures are low by a factor of four, and the CLEAR fixture is a zero pulse. The correction is inside `140a7ad`, which also edits `server/` and `site/`. Port that hunk onto `prod/release` in a product lane. Do not cherry-pick the commit.
