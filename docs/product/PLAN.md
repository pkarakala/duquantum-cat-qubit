# Cat Qubit Academy: implementation plan (Cursor lanes)

**Spec:** `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md` · **Interfaces:** `CONTRACT.md` · **Content:** `LEVELS.md` · **Sponsors:** `SPONSORS.md` · **Human tasks:** `HUMAN.md`
**Written:** Sat Oct 24, about 11:20 PM EDT. **Hard stops:**
- Product freeze **7:30 AM**.
- Physics freeze 8:00 AM.
- Devpost **10:45 AM**.
- Hacking ends 11:30 AM.

**Priority rule:** the Standard Track physics lanes (`docs/plan/`) always win CPU, review and merge time. If a physics gate slips, product lanes pause before any physics lane does.

## 1. Lanes
Each lane has a brief in `briefs/` and branches from `standard-track` as `prod/<slug>`.

| Lane | What | Model | Cap | Starts | Target |
|---|---|---|---|---|---|
| **p0-server** | FastAPI app: `/api/health`, `/api/sim/{one_mode,two_mode,expr}` on dynamiqs via `src/model.py`; params-hash cache; caps and timeout; `server/app/expr.py` (ExprTree → dynamiqs, allowlist); schemas; Dockerfile; `deploy/` compose with Caddy; `server/precompute.py` (level presets + linresp fixtures) | strongest | 2.5 h | 11:45 PM | 2:15 AM |
| **p1-ts-sim** | `site/src/sim/`: TS Lindblad solver (one-mode, N ≤ 30), Wigner (Clenshaw), Web Worker, `linresp.ts`, golden tests | strongest | 2 h | 11:45 PM | 1:45 AM |
| **p2-academy** | `site/src/academy/`: level engine, 8 levels from `LEVELS.md`, predict and check gates, misconception IDs, progress map, presets, scripted hints, "Show the code" | standard | 4 h | 12:00 AM | 4:00 AM |
| **p3-blocks** | `site/src/blocks/`: Blockly operator blocks → ExprTree, the typed equation line (stretch), `toLatex` and `toPython`, validation | standard | 2 h | 12:00 AM | 2:00 AM |
| **p4-tutor** | Gemini tutor with tools and number guard; Backboard memory and recap; ElevenLabs TTS narration cache plus the ElevenAgents widget with client tools; tutor UI | strongest | 3.5 h | 1:00 AM (after p0 skeleton) | 4:30 AM |
| **p5-data** | Tiger Data schema, run logging, community continuous aggregate, leaderboard (server recomputes the score), progress | standard | 2 h | 1:00 AM | 3:00 AM |
| **p6-chain** | Node chain service: Metaplex Core soulbound credential (wallet or custodial), Memo anchor of the results hash, anchors list; site claim UI | standard | 3 h | 1:00 AM | 4:00 AM |
| **p7-integrate** | Route and dependency wiring after l6 merges; Vultr deploy; CORS and TLS; offline single-file check; Grok Bot QA pass; demo dry run with the network off | strongest | 3 h | 4:30 AM | 7:30 AM |
| **p8-docs** | Devpost text, sponsor write-ups, demo script, video segment, DEV post draft; README Academy section text **handed to l7** | fast | 2 h | 7:30 AM | 9:30 AM |

**Parallel waves:**
- **Wave 1 (start together):** p0, p1, p3. p2 joins when l6's site skeleton is merged; until then it builds pure modules and level data.
- **Wave 2:** p4, p5 and p6 start once p0 has pushed its skeleton (`/api/health` plus the router layout), around 1 AM.
- **Wave 3:** p7 at 4:30 AM, then p8 at 7:30 AM.

Product lanes are light on CPU. The heavy two-mode sims run on **Vultr**, not the laptop, so they don't compete with the physics queue.

## 2. Gates (EDT)
| Gate | When | Must be true |
|---|---|---|
| **P-G0** | 11:45 PM | `product-academy` merged into `standard-track` (docs only); Harshit has the accounts and keys (`HUMAN.md` §1); Vultr VM created |
| **P-G1** | 2:15 AM | p1 golden tests green; p3 ExprTree fixtures green; p0 sim endpoints pass tests locally; L1–L4 playable locally on the TS solver |
| **P-G2** | 4:30 AM | p0 deployed on Vultr with HTTPS; tutor answers with a tool-grounded number; voice widget drives a slider; Tiger logs runs; a devnet credential is minted (or custodially); the results-hash anchor transaction exists |
| **P-G3 (product freeze)** | 7:30 AM | All 8 levels playable at the public URL; L1–L5 work offline; the demo dry run passes with the network off (presets and scripted hints); Grok Bot QA issues triaged; think-aloud results recorded |

## 3. Cut order (if a product gate slips > 45 min)
1. Pyodide editor.
2. Typed equation line (keep the blocks).
3. Narrated concept mp3s (keep the tutor voice).
4. Community live chart (keep runs logging and the leaderboard).
5. Wallet connect (keep the custodial credential).
6. Grok Bot QA (keep Cursor + Grok described for the raffle).
7. Server-side leaderboard recompute (keep the local score, marked "unverified").
8. Level 8 (keep L1–L7; Real Research shows our optimal pulse).

**Never cut:**
- L1–L5 working offline.
- The tutor with sim tools and the number guard (scripted fallback hints).
- The Vultr two-mode endpoint with preset fallback.
- A minimal visible feature per core sponsor: Gemini tutor, Vultr engine, ElevenLabs voice, Tiger runs, Solana credential **or** anchor, Backboard recap.
- **Any physics deliverable.**

## 4. Verification (product)
1. **Site:** `npm test` in `site/` (vitest: solver golden tests, linresp, ExprTree, level checks), plus `npm run build` and `npm run build:single`.
2. **Server:** `& $env:DUQ_PY -m pytest server/tests -q` (all external services mocked). Live smoke against the deploy: `curl https://<ip>.sslip.io/api/health`.
3. **Cross-language parity:** ExprTree `toPython` and linresp fixtures are identical between TS and Python.
4. **E2E:**
   - Browser smoke of all 8 levels at desktop and 375 px.
   - Voice: ask "why did the fringes fade?" and get a sim-grounded answer.
   - Claim a credential.
   - See your run in the community chart.
5. **Offline:** the single-file build from `file://` with Wi-Fi off. L1–L5 work, and L6–L8 show presets with banners.
6. **Learning:** 2–3 think-aloud sessions. Log the prediction accuracy before and after in `docs/product/status/p7-integrate.md`.

## 5. Process (same discipline as the physics plan)
- Each lane: TDD, its allowlist from `CONTRACT.md` §1, and the status file `docs/product/status/<slug>.md` (using `docs/plan/status/_TEMPLATE.md`).
- Reviewer: run `docs/plan/briefs/91-reviewer.md` adapted to product. Stage 1 is the allowlist and spec; Stage 2 replaces the physics checklist with: secrets not committed, ExprTree allowlist enforced, number guard present, offline fallbacks present, the TS solver matching its golden values.
- The integrator merges `prod/<slug>` into `standard-track` with the same protocol as `docs/plan/briefs/90-integrator.md`.
- Claude reviews later using `docs/plan/REVIEW_PROTOCOL.md` plus the product checks above.
