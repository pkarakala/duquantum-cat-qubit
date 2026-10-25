# Start here: the Cat Qubit Academy phase (product layer)

**What it is:** "Code.org for quantum". 8 prediction-gated levels take a curious beginner from "a box of light" to designing Alice & Bob's cat-qubit readout. Learners use sliders, operator blocks and a pulse editor. Schrö, a cat tutor, runs on Gemini and has to **run the simulator** before it answers. It speaks through ElevenLabs. Live two-mode physics runs on Vultr; experiments are logged to Tiger Data; credentials and a results-provenance anchor go on Solana; Backboard gives the tutor memory. Built with Cursor agents and Grok Bot.

**Why it can win:**
- No learner tool exists for bosonic or cat qubits.
- Ours finishes on our own *verified* research results.
- Every sponsor has a real job.

**Branch:** these docs live on `product-academy`. Code lanes branch from `standard-track` as `prod/<slug>`, after the integrator merges `product-academy` into `standard-track`. That merge adds only `docs/product/**` and `docs/superpowers/**`, so it can't conflict.

## Files
| File | What |
|---|---|
| `../superpowers/specs/2026-10-24-cat-qubit-academy-design.md` | The approved design spec |
| `PLAN.md` | Lanes, waves, gates, cut order, verification |
| `CONTRACT.md` | Ownership carve-out, API, ExprTree, TS solver interface, Tiger schema, level spec format, tutor tools |
| `LEVELS.md` | The content for all 8 levels: predictions, misconceptions, checks, hints, solutions, allowed constants |
| `SPONSORS.md` | Verified sponsor facts, credits, integration recipes, and the prize submission checklist |
| `HUMAN.md` | Harshit-only: accounts and keys, Vultr deploy, think-aloud tests, submissions |
| `briefs/P0…P8-*.md` | One paste-ready Cursor prompt per lane |
| `status/` | One status file per lane |

## Launch order (EDT)
1. **11:30 PM, Harshit:** do `HUMAN.md` §1 (accounts, keys, Vultr VM). The integrator merges `product-academy` into `standard-track`.
2. **11:45 PM:** launch `P0-server`, `P1-ts-sim` and `P3-blocks`. Launch `P2-academy` too; it starts with pure modules if l6's site skeleton isn't merged yet.
3. **About 1:00 AM** (after P0 pushes its skeleton): launch `P4-tutor`, `P5-data` and `P6-chain`.
4. **4:30 AM:** `P7-integrate` (wiring, deploy, QA, demo dry run).
5. **7:30 AM:** product freeze, then `P8-docs`.

Use this prompt for every lane in Cursor (Agents window, Worktree mode, base `standard-track`):
`You are product lane <slug>. Read AGENTS.md, docs/product/CONTRACT.md, docs/product/LEVELS.md, docs/product/SPONSORS.md and docs/product/briefs/<file>, then execute the brief exactly. Keep docs/product/status/<slug>.md updated.`

**Physics first.** If a physics gate slips, pause product lanes. Never let a product lane touch physics files.
