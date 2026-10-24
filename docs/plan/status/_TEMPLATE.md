# Status: lane `<slug>`

> Copy to `docs/plan/status/<slug>.md` and update it at **every** milestone. This file is the only channel to Harshit, the integrator and Claude's later review. Keep it factual: commands and real output, not intentions.

| Field | Value |
|---|---|
| State | `NOT_STARTED` / `IN_PROGRESS` / `BLOCKED` / `DONE` / `DONE_WITH_CONCERNS` |
| Branch | `std/<slug>` |
| Agent / model | e.g. Cursor agent, <model name> |
| Started (EDT) | |
| Last update (EDT) | |
| Last commit | `<sha>` `<subject>` |

## Milestones
- [ ] Read brief, CONTRACT, RESEARCH
- [ ] Tests written first (list the test names)
- [ ] Implementation complete
- [ ] `--quick` run passes (≤ 2 min)
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [ ] Explain-back questions drafted

## Acceptance gates (copy from brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| | | |

## Commands run (most recent first)
```text
<command>
<trimmed output>
```

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|

## Figures / arrays produced
-

## Jobs to queue (for the integrator; jobs > 15 min)
| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs (record ids) |
|---|---|---|---|---|

## Deviations from the brief (and why)
-

## DECISION NEEDED
> **Q:** <one-line question>
> **Options:** A) … B) …
> **Recommendation:** …
> **Blocking?** yes/no: what I did meanwhile

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1.
2.
3.

## Notes for Claude's later review
- Anything surprising, any tolerance you were tempted to loosen, any anchor that did not reproduce.
