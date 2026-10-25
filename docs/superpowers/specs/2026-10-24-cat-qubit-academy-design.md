# Cat Qubit Academy: design spec

**Status:** approved by Harshit in brainstorming, Sat Oct 24 2026, about 11 PM EDT. **Branch:** `product-academy` (docs only).
**Phase:** the product layer, built in parallel with the running Standard Track physics plan (`docs/plan/`). **Physics keeps priority**, and product lanes are cut first.
**Implementation plan:** `docs/product/PLAN.md`. Interfaces: `docs/product/CONTRACT.md`. Levels: `docs/product/LEVELS.md`. Sponsors: `docs/product/SPONSORS.md`.

## 1. Why
- **No learner tool exists for bosonic or cat qubits.** Quantum education today is gate-model (IBM Composer, Quirk, Black Opal, Katas) or discrete photons (Quantum Flytrap). Continuous-variable material exists only as developer notebooks (dynamiqs, QuTiP, Bosonic Qiskit, Alice & Bob's Felis notebooks).
- **We already own a verified physics engine** for exactly this system, with provenance-tracked results. So we can teach from zero to *the real research result*, which no other tool can do.
- **Judging fit:**
  - The DuQuantum grand prize scores "understanding, learning and growth".
  - The MLH sponsor prizes reward genuine use of their tech.
  - The Alice & Bob judges score physics correctness, so the product must reuse verified numbers and never weaken them.

## 2. Decisions (locked in brainstorming)
| Question | Decision |
|---|---|
| Audience | **Curious beginners** (high-school or early-college). Code.org style. |
| Relation to the Lab | **One site.** Academy (Learn, Sandbox, Challenge) plus the existing Lab pages as the "Real Research" wing. |
| Capacity | **Parallel track, physics first.** About 10 h of agent time; cut before physics. |
| Sponsors | **All, genuine roles.** Gemini, Vultr, ElevenLabs, Tiger Data, **Solana (core)**, **Backboard (core)**, Cursor + Grok (SpaceXSI raffle). |
| Architecture | **A: Hybrid.** In-browser TS solver for instant one-mode lessons; a Vultr FastAPI + dynamiqs service for two-mode sims, the tutor and the API hub; precomputed fallbacks. |

## 3. Product
- **Name:** Cat Qubit Academy. **Tagline:** "Code.org for quantum: from a box of light to Alice & Bob's cat qubit."
- **Learn:** 8 levels of 5 to 8 min each (`LEVELS.md`). Every level runs the same loop:
  1. A narrated concept card, voiced by ElevenLabs.
  2. **Predict:** a multiple-choice prediction, required before you can run anything. Each wrong answer maps to a misconception ID, M1 to M7.
  3. **Play:** a live sim, with few controls and an immediate visual response (PhET principles).
  4. **Check:** an auto-graded goal, Katas style: `check(output) → pass/fail`.
  5. **Aha:** a short sentence, plus a "Show the code" toggle revealing the matching dynamiqs `H` and `jump_ops`.
- **Levels:**
  1. A box of light
  2. The leaky box
  3. Two at a time
  4. The cat appears
  5. Flip vs flip
  6. Build the machine (operator blocks; two-mode on Vultr)
  7. Read the cat (it rings at 3.14 MHz)
  8. Design challenge (shape a readout pulse under a bit-flip budget; leaderboard; compare with our optimal pulse)
- **Sandbox:** free play, with operator blocks, a typed equation line and all sliders. A Pyodide Python editor is a stretch goal.
- **Challenge:** the leaderboards. They are URL-encoded, so submissions are shareable, and Tiger Data stores them.
- **Real Research:** the existing Lab pages (Inflate, Error budget, Readout designer, Verification), plus the Solana anchor of the verified-results hash.
- **Tutor "Schrö"**, a cat:
  - Gemini (`gemini-3.8-flash`) with function calling to the simulator and the records.
  - A 4-step hint ladder: (1) ask for a prediction, (2) say where to look in the plot, (3) show a contrasting case, (4) give one worked step. The full answer comes only after two attempts.
  - Every level carries a hidden step-by-step solution.
  - A **number guard** rejects any reply containing a number that is not in the tool output or the record IDs.
  - Voice: an ElevenLabs ElevenAgents widget, which uses Gemini 3.8 Flash as its LLM. Its **client tools** drive the UI: set a slider, run, show the next hint.
  - Memory: Backboard keeps a per-learner thread that remembers misconceptions across levels, and supplies the "welcome back" recap.
  - Offline: scripted hints, so the demo never depends on the network.

## 4. Architecture
```
Browser — site/ (Vite + TS; GitHub Pages and a single-file offline build)
  academy/  level engine, 8 level specs, progress map, predict/check gates, presets (precomputed fallbacks)
  sim/      TS Lindblad Crank–Nicolson + banded LU (one-mode, N ≤ 30; 180 ms measured) + Wigner (Clenshaw, 13 ms/frame, canvas) in a Web Worker; golden-tested vs dynamiqs
  blocks/   operator blocks (Blockly) + typed equation line → shared ExprTree JSON
  tutor/    chat UI, hint ladder, number guard, ElevenAgents widget + client tools, offline scripted hints
  chain/    Solana wallet connect + claim credential UI, anchor display
  (Lab pages from lane l6 = Real Research wing)
        │ HTTPS (Caddy on Vultr, <ip>.sslip.io host) — CORS: Pages origin, localhost, null (file://)
Vultr CPU-Optimized VM — docker compose
  api   (Python FastAPI; imports repo src/ so physics comes from src/model.py)
        /api/sim/one_mode, /api/sim/two_mode, /api/sim/expr   dynamiqs, warm JIT, cache by params hash, caps; two-mode live only at a fixed small shape (16×5, ≤15 s); common builds precomputed
        /api/tutor        Gemini 3.8 Flash + tools: run_sim, get_level_state, get_record, lookup_grid, check
        /api/memory/*     Backboard threads (event log + recap)
        /api/voice/tts    ElevenLabs TTS for narration (cached mp3)
        /api/runs, /api/community/alpha, /api/leaderboard, /api/progress → Tiger Data
  chain (Node + TS; Metaplex Umi + mpl-core): /api/chain/credential (soulbound Core asset, devnet), /api/chain/anchor (Memo tx with sha256)
  caddy (TLS reverse proxy)
Tiger Cloud (Postgres + TimescaleDB): sim_runs hypertable, progress, leaderboard, tutor_events; continuous aggregate for the live community view
```

**Rules:**
1. **The physics comes from one source.** Server sims import `src/model.py`. The TS solver must match dynamiqs within the golden tolerances (CONTRACT §5), and is labelled "learning sim, validated vs dynamiqs".
2. **Real Research numbers come only from `results/records`**, never from the learning sims.
3. **No server-side code execution.** Expressions are compiled from an **allowlisted ExprTree** (CONTRACT §4). Python is browser-only (a Pyodide stretch).
4. **Keys only in the server environment.** Learners are pseudonymous (a random UUID in localStorage), and no PII is collected. The Gemini free tier may use content, which is fine because there is no PII.
5. **Every network feature has an offline fallback:** presets, scripted hints, cached audio, and "badge pending" for chain calls. Levels 1 to 5 run fully offline.

## 5. Sponsor roles (details and setup in `SPONSORS.md`)
| Sponsor | Core role | Why it is genuine |
|---|---|---|
| Gemini | Tutor brain with function calling into our simulator and records. Also explains a block-built Hamiltonian in plain words. | The tutor is grounded in simulations instead of hallucinating physics. |
| Vultr | Hosts the live dynamiqs two-mode engine and the API hub, on CPU because we need fp64. | JAX can't run in the browser, so the server is necessary. |
| ElevenLabs | Voice tutor (ElevenAgents + client tools that drive the simulator) and narrated concept cards. | Lets the tutor speak and drive the sim hands-free, which helps accessibility and engagement. |
| Tiger Data | `sim_runs` hypertable of every learner experiment, a continuous aggregate behind the live "what α did everyone choose" chart, and leaderboards. | The data really is time series, and the live class dashboard is a true continuous-aggregate use. |
| Solana | Soulbound devnet credential for finishing the course (Metaplex Core), **plus a tamper-evident anchor of the verified-results hash** (Memo transaction). | It extends the project's provenance theme ("every number traceable") to a public timestamp. |
| Backboard | Per-learner persistent memory of misconceptions and progress, and the recap at level start. | Memory across levels is exactly what a tutor needs. Gemini calls for the core tutor stay direct, so the Gemini claim stays clean. |
| Cursor + Grok (SpaceXSI) | Built with Cursor agent lanes. A Grok Bot QA agent walks the deployed lessons and files issues; Grok is also the second physics reviewer (`tools/ai_review.py --provider grok`). | That is how we actually build. Opt in to the raffle at submission. |
| Alice & Bob | dynamiqs engine, Felis cross-check in Real Research, content teaching their qubit. | n/a |

## 6. Data flow (key paths)
- **Sim:**
  - Controls or blocks produce an ExprTree plus params, which are validated (allowlist, Hermitian H, caps).
  - **One-mode (N ≤ 30)** runs in a Web Worker in the browser, in under 300 ms.
  - **Two-mode** goes to `POST /api/sim/two_mode` (or `/expr`). The server computes a params hash and checks the cache (in memory, then Tiger Data). On a miss, dynamiqs runs at the fixed live shape (Na = 16, Nb = 5), with a 15 s two-mode timeout (8 s for one-mode); the client waits 3 s, or 15 s with progress for L6. The run is stored and the arrays are returned.
  - On a network error or timeout, the nearest preset JSON is used, with a banner.
- **Prediction:** a wrong choice produces a misconception ID. That ID is sent to `POST /api/memory/event` (Backboard) and to the tutor state.
- **Tutor:** `POST /api/tutor` with `{level, state, message}`.
  1. The server builds the prompt: system rules, the hint ladder, the hidden solution, misconception IDs and the Backboard recap.
  2. Gemini runs with tools, at most 3 calls.
  3. The number guard checks the reply.
  4. The server returns `{reply, hint_level, tool_calls, numbers_cited}`.
  - The voice path goes through the ElevenAgents widget, using the same tools via client-tool shims.
- **Completion:**
  - Level 8 passed leads to `POST /api/chain/credential` (wallet pubkey or a custodial fallback). The server mints a soulbound Core asset on devnet, and the UI shows the explorer link.
  - The anchor: after the physics freeze, the integrator calls `/api/chain/anchor` with `sha256(results/index.json)`, and Real Research shows the transaction link.

## 7. Error handling
- Every endpoint has a timeout, typed errors (`{error: {code, message}}`), per-IP rate limits, and size and time caps on sims.
- **Missing keys** turn the feature off with a visible "offline mode", never a crash.
- **Chain failures** show "credential pending: retry". They never block learning.
- **The frontend never blocks** on the network. Optimistic UI plus presets.

## 8. Testing
- **TS solver golden tests** against intro results:
  - The Task 1.0b plateau 0.4998323 (1e-4 rel).
  - Task 1.0a decay against 4e^{−κt} (1e-4).
  - Task 1.0c final ⟨n⟩ 4.404 (1e-3).
  - The Wigner of |α⟩ peaks at α.
  - The cat has negative fringes.
- **Parser tests:** the allowlist; rejecting unknown symbols, oversized trees and non-Hermitian H.
- **Server pytest:** sim caps and caching; tutor tool dispatch with Gemini, ElevenLabs, Backboard, Tiger and chain all **mocked**; schema conformance.
- **Contract tests:** shared JSON Schemas in `docs/product/CONTRACT.md` §3 are validated on both sides.
- **E2E smoke:** all 8 levels in the browser (desktop and 375 px), and a demo dry run **with the network off**.
- **Learning check:** 2 to 3 think-aloud sessions with non-physics hackers. Record the prediction accuracy before and after. N is small; say so.

## 9. Scope guardrails (YAGNI)
- **Out:**
  - Accounts and passwords: pseudonymous UUIDs only.
  - Teacher dashboards.
  - Mainnet anything.
  - Payments.
  - Server-side Python execution.
  - GPU instances.
  - Multi-language support.
- **Stretch, in cut order:**
  1. Pyodide editor
  2. Sandbox typed-equation line (keep blocks)
  3. Narrated cards (keep tutor voice)
  4. Community live chart (keep leaderboard)
  5. Wallet connect (keep custodial credential)

## 10. Success criteria (Sun 10:45 AM)
1. Levels 1–8 are playable at a public URL and work offline for levels 1–5.
2. The 60-second demo runs end to end, including the voice tutor answering with a simulator-grounded number.
3. Every sponsor has a working, visible feature, plus a Devpost "built with" entry and its prize submission.
4. Think-aloud results are recorded.
5. No regression to the physics deliverables: the physics lanes and their gates are untouched.
