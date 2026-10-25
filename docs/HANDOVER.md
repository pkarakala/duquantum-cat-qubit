# DuQuantum 2026 handover (Oct 25 2026, ~16:55 UTC)

For a fresh Claude finishing the project. No secret values here. Keys live only in `.env` on Pranav's Mac and the VM (`/opt/academy/.env`).

## Pranav's preferences
- Ultra concise, plain English. Put notation on figure axes. Pronouns they/them.
- Pranav merges to `main` unless they say otherwise.
- `integrated`: commit directly, no PRs, no force-push, never commit `.env`. Per handover/home-page.md: no Claude co-author lines, author "Pranav Reddy <preddy@ucsb.edu>".

## Repo: github.com/pkarakala/duquantum-cat-qubit (public since 16:24 UTC)
- **main** = physics submission: Standard track 2.1–2.4 plus Task 1, notebooks 01–09, `docs/task_1.md`, `docs/task_2.md`, `docs/TECHNICAL.md`, `docs/tools-log.md`. PRs #19–#23 merged or landed. #22 = Xuanyu's XZ-main commits; we kept our submitted 2.4 tables.
- **integrated** = Cat Qubit Academy: `site/` (Vite+TS), `server/` (FastAPI+dynamiqs), `chain/` (Solana), `deploy/` (docker compose+Caddy).

## Running it
- Live: https://66-42-119-3.sslip.io (Vultr VM 66.42.119.3). Ignore VM 64.177.55.154 (firewalled).
- Mac: site http://127.0.0.1:5180, API 127.0.0.1:8001 (qubit-lab owns 8000, don't touch).
- Checkout `~/projects/duquantum-cat-qubit/duquantum-cat-qubit`; demo worktree `~/projects/duquantum-cat-qubit/demo-integrated`.
- Pranav runs `redeploy_vultr.sh` from Mac Terminal (path in handover/product-layer.md). Remote Control sessions cannot reach the VM.

## Sponsors (say it honestly)
Gemini tutor (gemini-3-flash-preview); ElevenLabs narration + Talk voice agent "Schrö" (added ~16:38 UTC, smoke test may be unfinished); Backboard memory; Tiger run log; Vultr hosting + sim batches (~$5); Solana **demo only** (signed locally, not broadcast); SpaceX/Grok + Cursor built the product.

## Presentation
- The home page is the talk: 12 sections, ←/→.
- Backup slides: https://claude.ai/artifact/Lq9XPEmzC7tNw2rasfkXoA. Scripts: `/mnt/project-files/slides/walkthrough-script.md`, `/mnt/project-files/slides/presentation-script.md` (8-min home-page talk, not yet rehearsed against a timer).

## Headline numbers (wording matters)
- Γ_X: one per ~2.6 s at α=2.1. That is a **relaxation time** (T_X = 1/Γ_X); mean wait between single switches is 2/Γ_X = 5.2 s.
- Γ_Z ≈ 2κ_a α².
- Readout ring ~3.14–3.2 MHz. Resonant readout pulse error 1.12% → 0.65% (square → cosine). **2 µs is the pulse length.**
- −23 MHz pump retune.
- Don't demo L5/L7 numbers (hand-made mocks; L5 Γ_X ~295× off main).

## TODO (priority order)
1. **Rotate ALL sponsor API keys** (pasted in chat Oct 25 15:32 UTC). Remind Pranav.
2. Verify Talk agent end to end (mic Allow, client tools set_param/run_sim/show_hint/next_level actually register; checklist in handover/research.md).
3. Ask Pranav to redeploy Vultr; live is on 8da0773, newer integrated commits (Sandbox, Talk, lab pages, README, Vultr-live flag, L6/L8/Plotly fixes) aren't live. Recheck after.
4. PR #15's results pages (#/bitflips etc.) are not on integrated.
5. 4 pre-existing failing solver tests in `site/src/sim` (not caused by recent work).
6. Full audit report unfinished; open doc fixes 1–14 listed in handover/audit.md (notebook 06 wording, TECHNICAL.md truncation claims, task_2.md sign/wording, `build_research.py` crash on deleted task_2_3_readout.md, etc.).

## Detailed handovers (/mnt/project-files/handover/)
- `product-layer.md`: integrated deploy state, redeploy script, Talk agent wiring, L5/L7 mock warning.
- `home-page.md`: where home/research/lab/leaderboard pages live; build commands; commit rules.
- `script.md`: presentation script location and what wasn't clicked through.
- `audit.md`: what's merged (PR #20, #22), secrets scan clean, 14 open fixes. `audit-critical-raw.md`: raw critical findings (several now fixed on integrated).
- `research.md`: ranked future-work lines, Talk setup checklist, learner-adaptation plan, sources.
