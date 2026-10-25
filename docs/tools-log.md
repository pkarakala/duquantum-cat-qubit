# Tools log

Every external tool or sponsor service we used, when, for what, and where the evidence is.
Judges and Devpost categories are answered from this file, so add a row **when** a tool is
used, not afterwards. Newest first. Never put keys, tokens or card details here.

| When (EDT) | Tool | What we used it for | Settings / cost | Evidence in repo | Outcome |
|---|---|---|---|---|---|
| Oct 24 22:59 | Vultr (API v2, batch) | `cloud/s2_batch2.txt` (origin/claude/project-thread-ukumv1): 10 jobs via `cloud/vultr_batch.py` | 3 x `voc-c-16c-32gb-300s-amd`, 25 min, ~$0.55 of $5 cap; VMs deleted | `results/batch-vm*.log` + job outputs | VM error or stopped early; partial results kept; 1 job(s) exited non-zero, see batch logs |
| Oct 24 22:20 | Claude (Claude Code, Section 2 thread) | Section 2 physics: Liouvillian spectral solver, readout/pulse/circuit simulations, gradient pulse optimizer, write-up | sandbox CPU (4 cores) for prototypes and re-runs; no API cost beyond the subscription | `src/spectral.py`, `research/s2/`, `docs/SECTION2.md`, `results/s2/` | every headline number checked at ≥2 truncations and, where feasible, by a second method |
| Oct 24 22:07 | Vultr (API v2, batch) | `cloud/s2_batch1b.txt` (origin/claude/project-thread-ukumv1): 189 jobs via `cloud/vultr_batch.py` | 3 x `voc-c-16c-32gb-300s-amd`, 41 min, ~$0.90 of $10 cap; VMs deleted | `results/batch-vm*.log` + job outputs | VM error or stopped early; partial results kept; 3 job(s) exited non-zero, see batch logs |
| Oct 24 21:24 | Vultr (API v2, batch) | `cloud/s2_batch1b.txt` (origin/claude/project-thread-ukumv1): 189 jobs via `cloud/vultr_batch.py` | 3 x `voc-c-16c-32gb-300s-amd`, 4 min, ~$0.09 of $10 cap; VMs deleted | `results/batch-vm*.log` + job outputs | completed; 61 job(s) exited non-zero, see batch logs |
| Oct 24 20:32 | Vultr (API v2, batch) | `cloud/s2_batch1.txt`: 248 jobs, stopped by hand after ~50 min because the heavy jobs were mis-sized (only 1 finished) | 3 x `voc-c-16c-32gb-300s-amd`, ~$1.0; VMs deleted | none (results not pushed) | replaced by the lean `cloud/s2_batch1b.txt` |
| Oct 24 19:27 | Vultr (API v2, batch) | `cloud/research_jobs.txt` (origin/research-runs): 41 jobs via `cloud/vultr_batch.py` | 3 x `voc-c-16c-32gb-300s-amd`, 45 min, ~$0.99 of $40 cap; VMs deleted | `results/batch-vm*.log` + job outputs | completed; all jobs exit 0 |
| Oct 24 19:01 | Claude (Claude Code, this machine) | Figure check (all 12 figures read as images vs TECHNICAL.md claims and results JSON) and physics/numerics code review of src/ and tasks/, in place of the Gemini --figures run that hit the free-tier daily quota | no API cost beyond the Claude subscription; nothing re-run | `reviews/claude-figures-20261024-1900.md`, `reviews/claude-code-20261024-1900.md` | claim 20 steady-state bound wrong (2.9e-5 at N_a = 20, not 1e-5); B7 bound 3.1e-5; 6 presentation issues; no physics bugs; triage pending |
| Oct 24 17:28 | Vultr (API v2) | Task 1.2 convergence grid, 49 (N_a, N_b) points up to 48×18, via `cloud/vultr_run.py` | `voc-c-16c-32gb-300s-amd`, 16 vCPU, region ewr, ~$0.44/h; 19.1 min VM time (17 min sweep, ~60 min serial compute), ~$0.14; VM auto-deleted | `results/grid.log`, `results/task_1_2_grid.json`, `figures/task_1_2_grid.png` | completed; claim 20 (truncations independent, 32×12 within 0.035%) |
| Oct 24 16:32 | Gemini API (`gemini-3.8-flash`) | Independent physics/numerics code review of `src/` and `tasks/`, with the challenge prompt and TECHNICAL.md as context (`tools/ai_review.py`) | one text request, ~17k tokens | `reviews/gemini-20261024-1632.md`; triage in TECHNICAL.md §5 | no bugs found; 6 points checked by re-running fits (claim 19) |
| Oct 24 15:45–16:30 | Claude (Claude Code, research thread) | Literature survey on cat-qubit control; prototypes for stretch goals (overshoot theory, shaped ε_d ramps, Heisenberg basin map for \|+α⟩ prep, robustness test, jax.grad pulse optimization, moon cats) | dynamiqs 0.3.7 on a 4-CPU sandbox, default mesolve tolerances; no sponsor tools | `research/` on branch claude/project-thread-80xv97 (its README lists each script and result); workbook Research tab | 4 techniques kept; GRAPE helps only with a weak drive; moon cats set aside; numbers to re-run with PR #2 tolerances before they go in the README |
| Oct 24 (all day) | Claude (Anthropic) | Learning the physics, planning, writing most of `src/` and `tasks/`, reviewing results | n/a | README "How we used AI", TECHNICAL.md §5 | every number checked against a hand prediction or a convergence test |

Rows are added automatically by `tools/ai_review.py` and `cloud/vultr_run.py`; add others
(Cursor, Grok chat, ElevenLabs, notable Claude work) by hand in the commit that uses them.

Planned, not yet used (move up into the table once used): Gemini multimodal figure check
(`tools/ai_review.py --figures`), Cursor + Grok (SpaceXSI raffle), ElevenLabs voice-over,
DEV post after the event.
