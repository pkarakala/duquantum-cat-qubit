# Tools log

Every external tool or sponsor service we used, when, for what, and where the evidence is.
Judges and Devpost categories are answered from this file, so add a row **when** a tool is
used, not afterwards. Newest first. Never put keys, tokens or card details here.

| When (EDT) | Tool | What we used it for | Settings / cost | Evidence in repo | Outcome |
|---|---|---|---|---|---|
| Oct 24 17:28 | Vultr (API v2) | Task 1.2 convergence grid, 49 (Na, Nb) points up to 48×18, via `cloud/vultr_run.py` | `voc-c-16c-32gb-300s-amd`, 16 vCPU, region ewr, ~$0.44/h, 90-min hard stop; VM auto-deleted | `results/grid.log`, `results/task_1_2_grid.json`, `figures/task_1_2_grid.png` | running |
| Oct 24 16:32 | Gemini API (`gemini-3.8-flash`) | Independent physics/numerics code review of `src/` and `tasks/`, with the challenge prompt and TECHNICAL.md as context (`tools/ai_review.py`) | one text request, ~17k tokens | `reviews/gemini-20261024-1632.md`; triage in TECHNICAL.md §5 | no bugs found; 6 points checked by re-running fits (claim 19) |
| Oct 24 (all day) | Claude (Anthropic) | Learning the physics, planning, writing most of `src/` and `tasks/`, reviewing results | n/a | README "How we used AI", TECHNICAL.md §5 | every number checked against a hand prediction or a convergence test |

Planned, not yet used (move up into the table once used): Gemini multimodal figure check
(`tools/ai_review.py --figures`), Cursor + Grok (SpaceXSI raffle), ElevenLabs voice-over,
DEV post after the event.
