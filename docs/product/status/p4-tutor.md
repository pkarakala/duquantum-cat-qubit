# Status: lane `p4-tutor`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p4-tutor` (from `product-academy-build`, as instructed; not from local `standard-track`) |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 00:34 |
| Last update (EDT) | 2026-10-25 01:05 |
| Last commit | filled after the commit |

## What Schrö does

One turn of `POST /api/tutor`:

1. Validate the level, the message (1–1000 chars) and an optional plot snapshot (≤ 300 KB).
2. Load the learner's recap (1.5 s cap) and guard it with an empty tool pool.
3. **Call the simulator contract before the model speaks.** L1–L4 and L6/L8 call `run_sim`. L5 and L7 call `lookup_grid`. At most three tool calls follow.
4. Gemini (`google-genai`, automatic function calling off, thinking level minimal) writes `{reply, hint_level}`. Tools and the JSON schema go in one call. A 400/404 on that combination switches the process to two-phase. Gemini 3 function-call parts are echoed with their `thought_signature`.
5. The ladder clamps the hint (no jump of more than one; hint 4 needs a failed check). An answer-pattern leak before two failed checks is replaced by the scripted hint.
6. The number guard keeps a quantity only when it is within 1% of a tool result, a record, the request state, or a level constant (including numbers extracted from that level's own text, CONTRACT §8). Anything else becomes `(let's check that with a sim)`.
7. If the model cites nothing, one sentence is appended from a number the tool actually returned, then guarded again.
8. On an LLM error or the 10 s deadline, the response is **200** with the scripted hint, empty tool calls, and `source: "scripted"`.

Memory: `POST /api/memory/event` and `GET /api/memory/recap`. The real client is `httpx` against `https://app.backboard.io/api` (`POST /assistants`, `POST /assistants/{id}/threads`, `POST /threads/{id}/messages` with `memory: "Auto"` or `"Readonly"`). No key and `BACKBOARD_MODE=demo` uses `DemoBackboardClient`, labeled `demo-adapter`. No key and no demo mode is 503.

Voice: `POST /api/voice/tts` (ElevenLabs `eleven_flash_v2_5`, mp3 cache). `python -m server.app.voice.pregen` wrote the eight concept narrations. The site panel speaks a Gemini reply through that endpoint. ElevenAgents client tools are `set_param`, `run_sim`, `show_hint`, `next_level`, and `ask_tutor` (on by default).

## Milestones

- [x] Read brief, CONTRACT, LEVELS, SPONSORS
- [x] Tests written (33 pytest + 7 vitest)
- [x] Implementation complete
- [x] Fast tests pass
- [x] Live Gemini, ElevenLabs, and demo-memory checks recorded below
- [x] Explain-back questions drafted

## Acceptance gates

| Gate | Result | Evidence |
|---|---|---|
| Tests green, no network | pass | `python -m pytest server/tests -q` → `33 passed`. `npx vitest run --config src/tutor/vitest.config.ts` → `7 passed`. |
| Guard table and canned answers | pass | `test_tutor_guard.py`, `test_tutor_canned.py` |
| Ladder: no leak before two failures, no hint jump | pass | `test_tutor_ladder.py` |
| Turn under 10 s; two-mode only 16×5 and only L6 | pass | fake-clock test returns scripted with wall time ≪ 10 s. `test_tutor_tools.py` asserts Na=16, Nb=5, and no two-mode start when under 8 s remain. |
| No keys → 503, TTS cache still served, site falls back | pass | API, memory, and voice tests. Site test: rejected fetch → canned "3.14 MHz" for the readout question, else hint "Predict." |
| Live grounded answer, voice, recap | partial | See live transcript. TTS and demo recap are live. The slider move is a unit test. Gemini 3.8 Flash's free-tier daily quota was already spent. |
| Clean diff | pass for this lane's files | New paths are the P4 allowlist. `standard-track...HEAD` also lists the Academy docs already on `product-academy-build`. |

## Guard table

Pool: tool `{n_final: 0.4998, parity: 1.0}`, record `3.138`, and the LEVELS allowed constants with units (`1 ms` → 1000 µs and 1). `4.08` added only for the signed case.

| Case | Result |
|---|---|
| plateau is 0.4998 | kept, source `tool:run_sim` |
| κ₂/2π = 0.896 MHz | kept, `level_constant` |
| rings at 3.14 MHz | kept |
| 56% | kept |
| 1,000 µs | kept (1 ms) |
| −4.08 with 4.08 in the pool | kept |
| ends near 0.62 | removed |
| 1.2×10⁻⁴ /µs | one token, removed |
| −0.62 | removed |
| 7 photons, 7 only in the learner message | removed |
| L3, M3, record id `t2_3.ring_freq...`, `2κ_aα² coth(2α²)` | nothing extracted |
| recap "0.62" with an empty tool pool | removed |

## Latency

One successful grounded turn (Gemini 3.6 Flash, because 3.8 Flash returned 429 free-tier daily limit 20): **2.69 s**, one-phase (tools and schema together). Not a distribution, so p50/p95 are not claimed. Failed calls before the HTTP deadline was set to the API's 10 s minimum were dominated by SDK retries, not by the sim.

Tool source on that turn: `run_sim · mock-sim`, then `get_level_state · state`.

## Live transcript

`POST /api/tutor`, L4, "why did the fringes fade?", `alpha=2.1`, `loss=x20`, misconception M5. Model `gemini-3.6-flash` (env override; code default remains `gemini-3.8-flash`).

- `source: "gemini"`, `guard.passed: true`, `removed: []`
- tools: `run_sim` source `mock-sim` (summary `n_at_1us=4.41, parity_at_1us=0.2, parity_final=0.1`), then `get_level_state`
- `numbers_cited`: `4.41` from `tool:run_sim`
- reply: "Pair processes keep parity even, starting from vacuum. But loss removes single photons one at a time. What happens to the quantum state's parity when a single photon escapes? The sim reports n_at_1us = 4.41."
- hint level stayed 1

`0.2` is the **mock** client's loss-on parity, not a dynamiqs result. Do not quote it as research.

`POST /api/voice/tts` → `200 audio/mpeg`, 54377 bytes, for "The stripes fade because losing a photon flips parity."

`POST /api/memory/event` (L4, M5) → `200 {"ok": true, "source": "demo-adapter"}`.

`GET /api/memory/recap` → "Demo memory: this learner is still carrying M5. Those ideas are still open."

Voice slider: `set_param({name:"alpha", value:9})` on L1 calls `setParam("alpha", 3)` and an unknown name never reaches the bridge (`tools.test.ts`). No `ELEVENLABS_AGENT_ID` was provided, so a live agent session was not opened.

Pregen: eight mp3s plus `manifest.json`, 1.9 MB, voice Roger (`CwhRBWXzGAHq8TQ4Fs17`), model `eleven_flash_v2_5`.

## Interfaces I rely on

- **P0 (not in this worktree):** `server.app.sim.run_one_mode` / `run_two_mode`. `simbridge.py` is the only importer. Absent, so `MockSimClient` implements the CONTRACT §3 one-mode / two-mode bodies and labels `source: "mock-sim"`. Presets would be read from `server/precomputed/presets/` (`correct`, `missing_kappa_b`, `eps_z_drive_wrong`, `a_bd2_wrong`); that directory is not here, so a named build still returns `source: "preset"` with `available: false`.
- **P1:** `site/src/sim/index.ts` is not in this worktree. The browser sim is not called. The user instruction was to mock the sim client in that case.
- **P2 (not in this worktree):** `bridge.ts` is the only file that reaches `../academy/index.ts` (`getLevelState`, `setParam`, `runSim`, `showHint`, `nextLevel`, `events.on`). The import is runtime-only. If it fails, `stubBridge()` is used. `mountTutor(root, bridge, {apiBase})` is the call site for P7.
- **P5 (not in this worktree):** `notify_p5` tries `server.app.data.db.get_store().log_tutor_event`. Import failure is ignored. A monkeypatched logger is invoked and capped at 0.5 s.

## For P0

- Volume `ACADEMY_DATA_DIR` (default `/tmp/academy`) for `memory.sqlite` and `tts/`.
- Confirm the image contains `results/records/`, `src/`, and `server/precomputed/` (presets). This worktree has no `results/records`.
- `.env.example` lines: `ELEVENLABS_TTS_MODEL=eleven_flash_v2_5`, `ACADEMY_DATA_DIR=/tmp/academy`, `BACKBOARD_MODE=` (empty; set to `demo` only for the labeled adapter).
- `run_one_mode` must accept the tutor's one-mode bodies: `alpha: 0`, `kappa2_scale: 0`, and L2 `kappa_a_scale` up to about 107 (slider top, 2π·1 MHz / κ_a). If those are rejected, L2 should fall back to `state.last_sim` rather than the tutor inventing a scale.
- Router auto-include of `server/app/{tutor,memory,voice}/routes.py` (`router = APIRouter()`).
- Do not copy `server/.env` into the image.

## For P7

npm deps, exact versions not pinned here (installed with `--no-save`, `package.json` not committed):

- `@elevenlabs/client`
- `@elevenlabs/convai-widget-embed` (widget fallback; dynamic import)

Dev-only, already expected: `vitest`, `jsdom`.

- Call site: `mountTutor(root, bridge, { apiBase, askTutor: true, learnerId })` from `site/src/tutor/index.ts`.
- Build env: `VITE_ELEVENLABS_AGENT_ID` (public agent, auth off). `VITE_API_BASE` for the API.
- Copy `server/precomputed/audio/*.mp3` and use them as `site/public/audio/<narrationKey>.mp3`. Do not edit `site/package.json` in this lane.
- `ask_tutor` is on unless `opts.askTutor === false`.

## ElevenLabs dashboard config

- LLM: Gemini 3.8 Flash (or whichever model still has quota; 3.8 Flash free tier was exhausted on this key).
- Agent: public, auth off, shortest max call duration.
- System prompt: "You are Schrö, a cat tutor. For any physics explanation or number, call `ask_tutor` and speak its reply verbatim. Use `set_param`, `run_sim`, `show_hint`, and `next_level` to drive the lesson. Do not invent quantities."
- Client tools, all "wait for response":
  - `set_param` `{name: string, value: number}`
  - `run_sim` `{}`
  - `show_hint` `{level: number}`
  - `next_level` `{}`
  - `ask_tutor` `{question: string}`

## Backboard and Gemini mode

Verified from docs.backboard.io (Oct 2026), not from a live key (none was provided):

- `POST https://app.backboard.io/api/assistants`
- `POST https://app.backboard.io/api/assistants/{assistant_id}/threads`
- `POST https://app.backboard.io/api/threads/{thread_id}/messages` with `memory: "Auto" | "Readonly"`, optional `llm_provider` + `model_name` (BYOK Gemini). A 4xx on those model fields retries once on Backboard's default.

Gemini mode on the successful live turn: **one-phase**.

## Additive CONTRACT fields

- Request: `state.attempts`, `snapshot_png` (data URL, ≤ 300 KB).
- Response: `source` (`gemini` or `scripted`). Memory responses add `source: "demo-adapter"` when the demo adapter is on.
- `tool_calls[].source`: `live-one-mode`, `live-two-mode-16x5`, `preset`, `grid`, `record`, `state`, or `mock-sim`.

`guard_extra` in the overlay is empty. Level-text numbers are extracted at build time into `text_constants` (CONTRACT §8), separate from `guard_extra`.

## Deviations

- Branch base is `product-academy-build`, per the task, not `standard-track`.
- `server/.env` holds the keys and is gitignored. It is not in the commit.
- `site/package.json` was created only to run vitest and then deleted.

## DECISION NEEDED

> **Q:** Gemini 3.8 Flash's free tier on this key is exhausted (20 requests/day, retry about 2 h). The live transcript used `gemini-3.6-flash`.
> **Options:** A) keep the code default `gemini-3.8-flash` and set `GEMINI_MODEL` in the server env when quota allows. B) change the default to `gemini-3.6-flash`.
> **Recommendation:** A. The code default is unchanged.
> **Blocking?** no.

> **Q:** P0's runners and P1's TS solver are not in this worktree. `run_sim` uses `MockSimClient` (`source: "mock-sim"`), closed forms already written in LEVELS.md.
> **Options:** A) leave the mock until P0 merges; `simbridge` switches to `run_one_mode` automatically when that module imports. B) block the tutor on a real dynamiqs run.
> **Recommendation:** A.
> **Blocking?** no.

## Explain-back for Harshit (questions only)

1. A learner asks Schrö "how fast does the cat lose parity?" Which tool runs, where does its number come from, and what exactly does the guard do if Gemini writes a value that is 3% off?
2. Why can't the tutor run the learner's level 6 Hamiltonian live at a converged truncation? And how does it still give a correct, sourced answer about the 56% overshoot within 10 seconds?
3. What stops Schrö from handing out the level 3 answer on the first question? And what does Backboard memory change about the next level's conversation, without having any say over the physics numbers?

## Notes for Claude's later review

- The guard cases were not loosened. Decimals failed to extract until `Pattern.match(pos)` was used without a `^` anchor.
- `1 ms` is stored as both 1 and 1000 µs so "1,000 µs" stays legal.
- Do not quote `parity_at_1us=0.2` from the live turn. That is the mock.
- `levels.json` is server-side and includes solutions. No route returns it.
