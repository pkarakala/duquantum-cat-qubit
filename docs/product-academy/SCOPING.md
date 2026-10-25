# Product Academy scoping

Decisions below are already taken. Product lanes should follow them. This worktree does not implement the app.

## What was decided

### Branch base

**Chosen:** code lanes branch from `product-academy-build` at `b808ed4`, not from the local `standard-track` checkout.

`b808ed4` is `origin/product-academy`. It carries `docs/product/**` and the design spec. The physics checkout on `standard-track` is a different commit and does not contain those docs. Lanes that start there would not see the contract, levels, or briefs.

Each lane keeps its own worktree (`prod/p0-server`, `prod/p1-ts-sim`, `prod/p2-academy`, `prod/p3-blocks`, and later `prod/*` lanes). This worktree stays the integrator branch for scoping only. Do not edit `src/`, `tasks/`, `site/`, or any `std/*` physics worktree from here.

**Rejected:**

- Branch from local `standard-track`. The Academy docs are not in that tree yet.
- Wait for a merge of `product-academy` into `standard-track` before lanes start. That holds the demo on a docs merge.
- Build the app in this worktree. The coordinator is launching the four code lanes separately.

### Missing sponsor credentials

**Chosen:** Vultr, Solana, and Backboard are mocked behind the real interfaces in `docs/product/CONTRACT.md`, and every mocked response is labeled demo. Routes, request bodies, and response fields stay the ones the live client will use. A missing key turns that feature to demo mode. It must not crash the lesson or block the next level.

**Rejected:**

- Hide those features until accounts exist. The demo still needs a credential claim, a memory recap, and a two-mode fallback a learner can see.
- A second, simpler API “just for the demo.” Callers would have to change again when the real services are wired.
- Block later lanes until every sponsor key is present.

### Secrets

**Chosen:** the Timescale URL, the ElevenLabs API key, and the Gemini API key stay only in a gitignored env file (`.env` or `server/.env`). Root `.gitignore` already ignores `.env`, `*.env`, and `server/.env`. Commit `server/.env.example` with empty placeholders. Do not write those values into docs, status files, commits, or this note.

**Rejected:**

- Commit a filled env file.
- Paste keys into `docs/product/HUMAN.md` or a status file.
- Put real values in `server/.env.example`.

### Physics lanes

**Chosen:** do not block the Academy demo on the Standard Track physics lanes. Physics files stay untouched. Real Research numbers still come only from `results/records` when a record is already in the tree. Lessons that are waiting on later physics (live two-mode convergence, spectral Γ_X, readout grids) use the presets and analytic checks in `docs/product/LEVELS.md` and `docs/product/CONTRACT.md`, labeled as presets, until those records exist.

**Rejected:**

- Pause product work until the physics queue finishes.
- Edit `src/` or `tasks/` from a product lane to fill a missing number.
- Loosen a physics tolerance so a lesson test passes.

## What “complete” means for this pass

This integrator pass is complete when this file is the only new commit on `product-academy-build`.

The demo, built in the lane worktrees, is complete when:

- Levels 1–5 run offline on the in-browser one-mode solver.
- Levels 6–8 are playable, using a labeled preset when the Vultr two-mode path is in demo mode.
- Gemini, ElevenLabs, and Timescale are called for real when the gitignored env file is present, and the scripted or preset path is used when a call fails.
- Solana and Backboard answer on their contract routes in labeled demo mode.
- Site tests and the production build pass, and server tests pass with external services mocked.

## Options not taken for the demo cut

These stay out of the first demo, matching `docs/product/PLAN.md` cut order. They are not required to call the demo complete:

- Pyodide editor.
- Sandbox typed equation line (operator blocks stay).
- Narrated concept mp3s as a separate asset pipeline (tutor voice can still call ElevenLabs).
- Wallet connect (custodial or demo credential is enough).
- A public Vultr deploy before the local demo path works.
