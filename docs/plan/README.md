# Start here: running the Standard Track plan with Cursor agents

**Branch:** `standard-track` (cut from `intro-track-tasks@485b6e7`). **Owner:** Harshit.
**Executed by:** Cursor agents, one per lane, each in its own worktree. **Reviewed later by:** Claude, using `REVIEW_PROTOCOL.md`.
**Hard deadline:** Sun Oct 25, 11:30 AM EDT (Devpost repo + video ≤4 min). Talk ≤8 min at 12:00, Wilkinson 132.
**Internal deadlines:** physics freeze **8:00 AM**, Devpost submitted **10:45 AM**.

## What's in this package

| File | What it is |
|---|---|
| `../../AGENTS.md` | Rules every agent follows: units, drives, records, allowlists, git, escalation |
| `../../.cursor/rules/*.mdc` | Always-on Cursor rules: physics conventions, lane discipline, Python style |
| `../../.cursor/worktrees.json` | Worktree setup: checks the shared venv `D:\duq-venv` |
| `PLAN.md` | The master plan: why, scope, architecture, lanes, timeline, risks |
| `CONTRACT.md` | **Frozen interfaces:** file ownership, function signatures, record schema and IDs, claim syntax, run queue, Lab data |
| `RESEARCH.md` | Verified physics facts, formulas, anchors and sources, plus "what we got wrong first" |
| `briefs/NN-<slug>.md` | One paste-ready prompt per lane |
| `status/<slug>.md` | One live status file per lane (from `status/_TEMPLATE.md`) |
| `status/reviews/<slug>.md` | Reviewer verdicts (from `briefs/91-reviewer.md`) |
| `REVIEW_PROTOCOL.md` | How Claude reviews and decides on the finished work |
| `HUMAN_TRACK.md` | Harshit-only tasks: comms, mentors, derivations, defense, talk, video, Devpost, publishing |

## How to launch a lane in Cursor
1. Open the repo in Cursor on branch `standard-track`.
2. **Agents window → New Agent → Worktree mode.** Use `standard-track` as the base and pick the model the brief suggests.
   - Cursor runs `.cursor/worktrees.json`, which checks that `D:\duq-venv` imports this worktree's `src`.
3. Paste the prompt from the top of the brief:
   `You are lane <slug>. Read AGENTS.md, docs/plan/CONTRACT.md, docs/plan/RESEARCH.md and docs/plan/briefs/<NN>-<slug>.md, then execute this brief exactly. Keep docs/plan/status/<slug>.md updated.`
4. As its first step, the agent runs `git switch -c std/<slug>` inside the worktree. All its commits go there.
5. When the status says `DONE`, launch a **reviewer** agent: "You are the reviewer for lane `<slug>`. Read `docs/plan/briefs/91-reviewer.md` and execute it."
6. On `PASS`, the **integrator** merges (see `briefs/90-integrator.md`). That can be you, or one long-lived agent in the **main** checkout.

Run at most about 6 lane agents at once. Heavy compute is capped separately: at most 3 jobs, and only one LU larger than 3 GB.

## Phases and what to launch when (EDT)

| When | Launch / do | Gate |
|---|---|---|
| **Now to 6:15 PM** | `00-setup` (you, or one agent in the main checkout). Message Pranav and the mentors (`HUMAN_TRACK.md`). | venv works; intro reproduces |
| **6:00 PM** | `01-l0-core` (strongest model), plus `02-l0-tools` and `11-l6-lab` in parallel (mock data) | |
| **6:45 PM: G0** | Merge `l0-core`. CONTRACT is frozen. | tests green |
| **6:45 PM** | `03-l1-spectral`, `04-l2a-gamma-z`, `06-l3-prep`, `07-l4a-readout`, `08-l5-circuit` | |
| **9:45 PM: G1** | Merge l1, l2a, l3, l4a (l5 may still be running) | anchors reproduce; Γ_Z validated |
| **9:45 PM** | `05-l2b-gamma-x`, `10-l4c-capstone` (you're awake for both), `09-l4b-tradeoff`, `13-l8-felis`; `12-l7-docs` drafting | |
| **1:30 AM: G2** | Merge l2b, l4c, l8. Queue the l4b grid and the large-α confirmations overnight. | Γ_X two ways; capstone beats square |
| **~2:00 to 6:00 AM** | **Sleep.** The run queue keeps going. | |
| **7:00 AM: G3** | All physics merged or cut; read the morning brief in `status/integrator.md` | |
| **7:00 to 8:00 AM** | Freeze: `check_claims`, Gemini review, fresh-clone smoke | **no new numbers after 8:00** |
| **8:00 to 10:45 AM** | `12-l7-docs` final pass; Lab deploy; record video by 10:00; submit by 10:45 | Devpost done |
| **10:45 to 11:45 AM** | Two timed rehearsals plus the defense drill | |

## Dependency graph
```
00-setup ─► 01-l0-core ─┬─► 03-l1-spectral ─┬─► 05-l2b-gamma-x ─► 13-l8-felis
                         │                   ├─► 09-l4b-tradeoff ◄─┐
                         ├─► 04-l2a-gamma-z ◄┘(eig cross-check)    │
                         ├─► 06-l3-prep ──────────► 11-l6-lab (frames)
                         ├─► 07-l4a-readout ─┬─────────────────────┘
                         │                   └─► 10-l4c-capstone ◄── (09 grid, optional)
                         └─► 08-l5-circuit ──► 09-l4b-tradeoff (extra_H, optional)
02-l0-tools (parallel from the start) ─► integrator, 12-l7-docs (check_claims)
11-l6-lab (mock data from the start) ─► live data after records exist
12-l7-docs ◄── every merged lane
```

## Monitoring
- **Lane state:** `docs/plan/status/*.md`. The ledger is `docs/plan/status/integrator.md`.
- **Branches:** `git log --all --oneline --graph -30`.
- **Queue:** `& $env:DUQ_PY -m tools.runq status`.
- **Claims:** `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md`.

## Rules of thumb
- If a lane says `DECISION NEEDED`, answer it in its status file, or ask Claude in a new session with "review per docs/plan/REVIEW_PROTOCOL.md".
- Never present a number you can't explain. Every merged physics lane comes with 3 explain-back questions. Answer them yourself in `docs/defense.md`.
- Cut by the order in `PLAN.md` §8 when a gate slips by more than 1 h. Never cut the "never cut" list.
