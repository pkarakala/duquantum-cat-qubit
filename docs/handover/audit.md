# Audit handover (Oct 25 2026, 16:49 UTC)

Thread "Audit all code and branches". Stopped by Pranav at 16:47 UTC. No secrets in this file.

## Done and on main
- PR #20 merged (df596f3): README "Grok", Vultr line "about 4 USD", Academy live-link row, 3 broken doc links fixed.
- PR #22 merged (f454560): Xuanyu's 8 XZ-main commits (notebooks 05–09 rewrites, GitHub math fix, enlargement study). Kept the submitted headline tables in docs/TECHNICAL.md (Γ_X, Γ_Z, readout, −23 MHz, 2.4 pulse table: square 1.12%, cosine 0.65%). Added to docs/task_2.md the line deriving 1.12% / 0.65% from 𝓘 and δ_X.
- Secrets: full history, all 42+ branches, tags and PR refs are clean. No .env, keys or keypairs. The Hacker Guide PDF was never committed. Keys pasted in chat still need rotating (remind Pranav).
- Repo went public at 16:24 UTC. Side effect: branch `integrated` publicly serves docs/challenge_prompt_v4.md (organizer prompt), prep/HANDOFF.md and the tutorial notebooks. No keys or phone numbers.

## Fixed on integrated by the product thread (verify on the live Vultr site after redeploy)
- L8 "beat square" check now uses the energy cost (70bdc2a).
- L6 live run: the server sends t_us/top2_a, but the site read tUs/meta (22ab3b0).
- Plotly charts blank on the 2nd run: switched to newPlot.
- Integrated README replaced; Vultr shown live when VULTR_HOSTED=1 (e5035b7). L7 cost card labelled illustrative (7c47054).

## Open items, not done (doc fixes on main; direct commits to main are OK, no force-push)
1. notebooks/06 cell 12: "mean waiting time for a flip is 2/Γ_X = 5.2 s" vs the slides' "one flip every 2.6 s". Reword: T_X = 1/Γ_X = 2.6 s is the bit-flip time (decay of ⟨X⟩, challenge convention), and the mean wait between individual switches is 2/Γ_X = 5.2 s.
2. docs/TECHNICAL.md: cos η=0.5 cell should read "2.60% (1.50% at 1.0 g₂)". Change "2e-5" to "2.5e-5".
3. docs/TECHNICAL.md: "Every headline number is computed at two or more truncations" needs exceptions. The 2 µs pulse table is (30,8) only; 0.5 µs is checked at (32,8) vs (36,10). Driven Γ_X at 0.5 g₂ is 28×8 only. Memory top level ≤ 1e-6 holds only for ε_Z ≤ 2 g₂.
4. docs/task_2.md: "underestimates the simulated rate by 33.3%" should be "the simulated rate exceeds it by 33.3% at α=1.4". Line ~252: `\tfrac12E_J` should be `\frac{1}{2}E_J` (GitHub math).
5. TECHNICAL "XZ commit": name commit 17ef9a2 on branch XZ-codex-intro-review (keep that branch or tag it) and add an enlargement provenance line.
6. Wording: "Stronger drives flip the qubit..." needs a reword; "only the shape" should be "at fixed cat size"; "all 9 converged" should be "completed".
7. README: point the Gemini log link at reviews/gemini-20261024-1632.md.
8. reviews/submission-integration-20261025.md and reviews/task_2_4_evidence_selection.md are Codex process notes; the reviewer suggests deleting them.
9. notebooks/09: add the 1.12% / 0.65% sentence and replace "Main's".
10. docs/tools-log.md: add today's rows (Academy deployed on Vultr 66.42.119.3 at https://66-42-119-3.sslip.io; repo audit).
11. integrated: site/scripts/build_research.py DOCS still lists the deleted docs/task_2_3_readout.md, so a research-page rebuild crashes after rmtree. Drop that row before rebuilding (forwarded to the home-page thread).
12. integrated: L5/L7 presets (site/src/academy/presets/L5.json, L7.json) are hand-made mock physics, about 295× off main's Γ_X (main: 3.849e-7/µs, T_X 2.6 s, bias 1.3e6). Real dynamiqs presets exist in server/precomputed/presets/L7_eps_*.json but the site does not use them. L7 is now labelled illustrative; L5 is still off.
13. Optional code bug: tasks/task_1_2_grid.py point() mishandles run()'s tuple return. Fix: `t, e, _, wall = run(na, nb)`, then build the dict from e[0..3] and wall.
14. Branch cleanup: many stale claude/* branches remain. Tag as archive/<branch> before deleting; Pranav runs deletes.

## Caveat
The audit workflows' adversarial verify passes mostly failed on a session limit (resets 17:20 UTC). Items 1–9 were checked by me against the files; the rest are single-reviewer findings.

## Raw outputs (this session's scratchpad, lost when the container ends)
Workflow task outputs: tasks/{wik644ib5,w9hemsom1,wqncn7mz6,wb0f3ohs7,wyhny6dpk,wd1f0kbd7}.output. Critical list: scratchpad/critical-live.md. The full HTML audit report was not published.
