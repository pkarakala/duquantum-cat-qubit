# Status: lane `l4b-tradeoff`

> Copy to `docs/plan/status/<slug>.md` and update it at **every** milestone. This file is the only channel to Harshit, the integrator and Claude's later review. Keep it factual: commands and real output, not intentions.

| Field | Value |
|---|---|
| State | `IN_PROGRESS` |
| Branch | `std/l4b-tradeoff` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | Sun Oct 25 2026, 10:18 AM |
| Last update (EDT) | Sun Oct 25 2026, 10:24 AM |
| Last commit | tests not committed yet |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH
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
- `src/spectral.py` copied from `std/l1-spectral` at `d5d9709` and `src/linresp.py` copied from `prod/linresp`. Neither file is on this branch's `standard-track` base. `std/l4a-readout` is dirty (untracked `results/records/t2_3.ring_freq.linresp.two_mode.a2.10.json`), so linresp was not taken from that worktree. Frozen `src/model.py`, `src/config.py`, `src/analysis.py` were not edited.
- Heavy lock `$MAIN/.git/duq-heavy.lock` is held by a live `l4a-readout` process (`task_2_3 --part all`, owner stamp 09:42). Not deleted.

## DECISION NEEDED
> **Q:** pending the uppercase-`T` dry-run
> **Options:** A) … B) …
> **Recommendation:** …
> **Blocking?** 

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. The readout drive cannot tilt the double well. So where does the extra bit-flip rate come from, and why does it carry e^{−2α²} rather than the e^{−4α²} of the undriven code-space channel?
2. Γ_Z rises by exactly 2ε_Z²/(κ₂α²). Why is that unavoidable for any readout, and how is it tied to the SNR rate you measured (and to the e^{2α²} figure of merit)?
3. Without the Z₂ split, how did you know which eigenvalue of the deflated Liouvillian is Γ_X, and why should anyone trust the number at ε_Z = 3g₂, where the buffer holds about 2 photons?

## Notes for Claude's later review
- Machine is an 8 GB M3. In-lane cap is 15 min and 3 GB, and any job above 1.5 GB or 5 min must hold the heavy lock.
