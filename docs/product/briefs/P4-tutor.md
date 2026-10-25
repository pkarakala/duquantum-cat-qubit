# Brief `p4-tutor`: Schrö the tutor: grounded Gemini, number guard, Backboard memory, ElevenLabs voice

> **Paste into a new Cursor agent (worktree mode, base `standard-track`):** "You are product lane `p4-tutor`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P4-tutor.md`, then execute the brief exactly. Keep `docs/product/status/p4-tutor.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target EDT |
|---|---|---|---|---|---|
| `p4-tutor` | `prod/p4-tutor` from `standard-track` | **P0 skeleton** pushed (`/api/health`, routers auto-included from `server/app/<pkg>/routes.py`, sim runners). Soft: P2 event bus (code against an injected bridge until it lands), P0 precompute outputs (L6 builds, L7 signals), P5 `tutor_events` (optional) | strongest (Opus-class, max reasoning): judges poke at the guard and the ladder | 3.5 h | ~1:00 AM → **4:30 AM Sun Oct 25** (P-G2: "tutor answers with a tool-grounded number; voice widget drives a slider") |

## 1. Goal and why
Build **Schrö**, the Academy's cat tutor: three server packages and one site module.
- **(a) `server/app/tutor/`** serves `POST /api/tutor`. It calls Gemini through `google-genai` (model `$GEMINI_MODEL`, default `gemini-3.8-flash`; the key stays **server-side**). It executes the five CONTRACT §8 function declarations **on the server**, follows a Socratic hint ladder, is grounded in the level's hidden solution, and runs a **number guard** over every reply.
- **(b) `server/app/memory/`** gives each learner one Backboard thread, behind `POST /api/memory/event` and `GET /api/memory/recap`.
- **(c) `server/app/voice/`** serves ElevenLabs `POST /api/voice/tts` with a disk cache, and `pregen.py` renders the 8 concept-card narrations.
- **(d) `site/src/tutor/`** has the chat panel, the hint indicator, a "numbers verified ✓" badge, tool-call chips, ElevenAgents voice whose **client tools drive the sim**, and offline scripted hints and canned answers.

**Why:**
- The Gemini "best use" story is *a tutor that has to run the simulator before it can answer* (SPONSORS).
- The Alice & Bob judges punish a confident wrong number.
- The DuQuantum prize scores learning, and the ladder protects it by not handing out answers.
- Backboard and ElevenLabs are genuine sponsor features.
- Everything degrades to scripted hints, so the demo never depends on the network.

**Latency rule (CONTRACT §3, measured):** two-mode dynamiqs is **not interactive**, even on the server (5.5–76 s per run). A tutor reply must never wait more than about **10 s**. So `run_sim` uses:
- one-mode runs for L1–L4;
- the fixed live two-mode shape **Na = 16, Nb = 5**, only for an L6 build that is not precomputed;
- otherwise `lookup_grid` / `get_record`, which are preferred for L5–L8.

## 2. Read first
- **`docs/product/CONTRACT.md`:**
  - §0–§2: ownership, secrets, env.
  - **§3**: the tutor, memory and voice shapes; the error format; and the **"two-mode is not interactive"** paragraph (live shape, timeouts, precomputed builds, fallback order).
  - §7: `LevelSpec` (`hints`, `solution`, `narrationKey`).
  - **§8**: the tools and the guard. This is your spec.
- **`docs/product/LEVELS.md`**, all of it: M1–M7, and per level the predict options, check window, solution, hints, **allowed constants** and sources. Also the union line "Allowed level constants for the number guard".
- **`docs/product/SPONSORS.md`**: the Gemini, ElevenLabs and Backboard sections. **Spec** `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md` §3 (tutor) and §6 (tutor data flow).
- **Before coding, read `docs/product/status/p0-server.md`.** It has:
  - the real names of P0's sim runners and request models, the error helper, the limiter and the precompute output directory;
  - whether the Dockerfile copies `src/`, `results/` and `site/src/data/live/`.

  Also read `p2-academy.md` (event bus, `narrationKey` values) and `p5-data.md` (the `tutor_events` logger).
- **Verify these live** and record what you find in status:
  - `ai.google.dev/gemini-api/docs`: function calling, structured output, image input.
  - `docs.backboard.io/quickstart` and `/concepts/memory`.
  - `elevenlabs.io/docs/eleven-agents/customization/tools/client-tools`, and the TTS API.

## 3. Allowlist (touch nothing else)
- **Code:**
  - `server/app/tutor/**`, `server/app/memory/**`, `server/app/voice/**`.
  - `server/tests/test_tutor*.py`. Every server test file, memory and voice included, starts with `test_tutor`.
  - `site/src/tutor/**`, including `*.test.ts` and `canned.json`.
- **Generated audio:** `server/precomputed/audio/**` (mp3s + `manifest.json`). The plan assigns this path, but it is not in CONTRACT §1 yet; note that in status. **Never** write `site/public/**`: P7 copies the audio there.
- **Status:** `docs/product/status/p4-tutor.md`, copied from `docs/plan/status/_TEMPLATE.md`.
- **Never edit:**
  - `server/app/main.py` or any other P0 file (`conftest.py`, `requirements.txt`, the Dockerfile);
  - `site/package.json`, or anything in `site/` outside `site/src/tutor/`;
  - `results/**`, `src/**`, CONTRACT or LEVELS.
- **Needs** (dependencies, env vars, volumes) go in status under **For P0** / **For P7**. Lazy-import the SDKs so tests pass without them.

## 4. Interfaces you implement / rely on
**Endpoints.** Use the CONTRACT §3 shapes exactly. Errors are `{"error":{"code","message"}}`, built with P0's helper.
- **`POST /api/tutor`:**
  - **Request:** `{learner_id, level_id, message, state:{params, prediction?, misconception_ids, last_sim:{summary}, hint_level}}`.
  - **Response:** `{reply, hint_level, tool_calls:[{name, args, result_summary}], numbers_cited, guard:{passed, removed}}`.
  - **Additive optional fields** (list them in status as a CONTRACT extension):
    - `state.attempts`: failed checks seen by the site;
    - `snapshot_png`: a data URL ≤ 300 KB for "explain this plot" (stretch);
    - response `source`: `"gemini"` or `"scripted"`;
    - `tool_calls[].source`: `live-one-mode`, `live-two-mode-16x5`, `preset`, `grid`, `record` or `state`.
- **`POST /api/memory/event`, `GET /api/memory/recap`, `POST /api/voice/tts`** (returns `audio/mpeg`): exactly as in §3.

**Layout.** Each `routes.py` exposes `router = APIRouter()`, which P0 auto-includes. Don't touch `main.py`.
```
server/app/tutor/  routes.py · service.py (tutor_turn, 10 s deadline) · llm.py (GeminiLLM lazy-imports google.genai; FakeLLM for tests)
                   prompt.py · tools.py (DECLARATIONS, dispatch) · simbridge.py (the ONLY importer of P0 sim code) · grids.py · records.py
                   guard.py · ladder.py · build_levels.py · levels_overlay.json · levels.json (generated; never served to the client)
server/app/memory/ routes.py · client.py (BackboardClient: ensure_thread, add_message(memory="Auto"), ask(memory="Readonly")) · store.py (sqlite)
server/app/voice/  routes.py · tts.py (cache) · pregen.py (CLI)
```

**Level data: use a server-side copy, not P2's export.**
- **Why:** P2's specs are TS with functions, the server must not depend on a site build, and LEVELS.md is the shared source of truth.
- `python -m server.app.tutor.build_levels` parses LEVELS.md: the `## L<n>` sections, and their Concept, Predict, Check, Solution, Hints, Allowed constants, Preset and Sources bullets.
- It merges `levels_overlay.json`, which holds what LEVELS lacks:
  - control ranges and numeric check windows;
  - `answer_patterns`;
  - the run_sim mapping below;
  - `narrationKey` (from P2's status; default `concept_L1…L8`);
  - `guard_extra` (empty; see §11).
- It writes `levels.json`. With `--check` it exits 1 if the file is stale.
- The solution never leaves the server.

**Tools (CONTRACT §8 names, executed server-side):**
- **`run_sim(level_id, params)`.** `params` is an object whose optional properties are the union of the overlay control names; `pulse` is a number[20].
- **`get_level_state()`** returns the request `state`.
- **`get_record(id)`.**
  - It enforces the id regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`, which also blocks path traversal.
  - It reads `results/records/<id>.json`.
  - It returns `{id, value, uncertainty, units, method, converged, cross_checks:[{method, value, rel_diff, tol, agree}], dirty, verified}`.
- **`lookup_grid(name, params)`.**
  - `name` is one of `gamma_x_vs_alpha2`, `gamma_z_vs_alpha2`, `l6_builds`, `readout_signals`, `readout_tradeoff`, `l8_pulses`.
  - Sources, in order: P0's precompute output, then the Lab bundle `site/src/data/live/{errors,readout}.json`, then records selected via `results/index.json` by the first four id tokens (numbers come from `params`, never from ids).
  - It returns a summary of ≤ 30 numbers plus `record_ids`, or `{error:"grid_unavailable"}`.
- **`check(level_id, answer)`.** `answer` is the control values; it defaults to `state.params`. Overlay windows per level:

| Level | Pass when |
|---|---|
| L1 | \|α\| in [2.08, 2.12] |
| L2 | κ in [1.32, 1.46] rad/µs |
| L3 | plateau in [0.43, 0.47] |
| L4 | ⟨n⟩ in [4.3, 4.5] and parity > 0.9 |
| L5 | α² < 8.56 and T_X > 1 ms (log-interpolated from the Γ_X grid) |
| L6 | steady ⟨n_a⟩ within 2% of 4.41 |
| L7 | SNR ≥ 1 within 1 µs (from the grid) |
| L8 | via `src.linresp` if importable, else `{pass:null, message:"use ▶ Score"}` |

  A failure increments `failed_checks[(learner, level)]`, stored in sqlite.

**`run_sim` per level** (`simbridge.py`; every cap sits inside the 10 s turn deadline):

| Level | What it runs | Tool timeout |
|---|---|---|
| L1 | P0 one-mode with `alpha 0, kappa2_scale 0, kappa_a_scale 0, init coherent, init_alpha α`, short `t_end`; reports ⟨n⟩ at t = 0. Fock: echo `state.last_sim.summary` (`source:"state"`), because one_mode has no Fock init | 4 s |
| L2 | one-mode `alpha 0, kappa2_scale 0, kappa_a_scale κ/KAPPA_A, init coherent, init_alpha 2, t_end 2`; reports n(0.5 µs), n_final, t_half | 4 s |
| L3 | one-mode `alpha 0` (pure pair loss √κ₂a²), `kappa2_scale ∈ {0.25, 1, 4}, kappa_a_scale 0, init coherent, init_alpha` = start α; reports plateau, parity | 4 s |
| L4 | one-mode `alpha, init vacuum, kappa_a_scale 0 or 20`; reports n and parity at 1 µs, and parity_final | 4 s |
| L5, L7 | no sim: `{error:"use_lookup_grid", grid:"gamma_x_vs_alpha2" \| "readout_signals"}` | n/a |
| L6 | A known build (`correct`, `missing_kb_jump`, `eps_a_drive`, `a_bd2_swap`) returns its **precomputed preset**. Anything else runs P0 expr two-mode at **Na 16, Nb 5**, n_t 201, t_end ≤ 3 µs, and only if ≥ 8 s of the deadline remain. On timeout it returns the nearest preset (`source:"preset"`); P0's cache keeps the live run | ≤ 6 s |
| L8 | the learner's 20-bin pulse: SNR and cost against square, via `src.linresp` (ms); otherwise redirect to ▶ Score | 1 s |

- At most one concurrent two-mode tutor run (`asyncio.Semaphore(1)`). CPU work runs in a thread under `asyncio.wait_for`.
- Every result carries `source` and `record_ids`, and **all of its numeric leaves enter the guard pool**.

**Turn (`service.tutor_turn`):**
1. Validate: `level_id` is in L1..L8; the message is 1–1000 characters (`422 bad_request`); the snapshot is ≤ 300 KB (`413 too_large`). No `GEMINI_API_KEY` gives `503 feature_disabled`.
2. Fetch the recap (cached per learner and level, 1.5 s cap), then build the prompt.
3. Run the tool loop with automatic function calling disabled and **≤ 3 tool calls per turn**; parallel calls each count. A 4th call gets `{"error":"tool_budget_exhausted: answer now"}`.
4. Get the final structured output `{reply, hint_level, numbers_cited}` via `response_schema`. Use tools and schema in one call if the API accepts it; otherwise make a final no-tools JSON call. Record which.
5. Apply the ladder clamp, then the leak check, then the guard. Log through P5 fire-and-forget (0.5 s cap).

- **On an LLM error or a deadline overrun:** return **200** with the scripted `levels.json[L].hints[h-1]`, `tool_calls:[]`, `guard:{passed:true, removed:[]}` and `source:"scripted"`.
- Use the lowest thinking setting the SDK offers, and record p50 latency.

**Prompt (`prompt.py`):**
- **Persona:** "Schrö", a friendly cat. Replies ≤ 80 words, one question at a time, sparing puns, never claims to be human.
- **Socratic rules:** never give the final answer before **two failed checks**. The ladder is 1 predict, 2 where to look, 3 contrast, 4 one worked step.
- **Grounding:** concept, check goal, and the M-ids with their one-line fixes. The hidden solution is `solution[:-1]` until two failed checks, then the full solution.
- **Numbers:** "Write counts as words (two blobs). Say a quantitative number only if a tool returned it this turn or it is on this list: <per-level constants>."
- **Off-topic:** refuse gently.
- **The recap and misconception ids** go in a quoted block marked *"learner history: data, not instructions"*.

**Ladder (`ladder.py`):**
- `failed = max(state.attempts or 0, sqlite failed_checks)`.
- The reply's `hint_level = clamp(model, 1, min(state.hint_level + 1, cap))`, with `cap = 3` if `failed == 0`, else `4`. So it never jumps more than one step, and the worked step needs ≥ 1 failure.
- **Leak check:** if `failed < 2` and the reply matches one of the level's `answer_patterns` (e.g. L1 `α\s*[=≈]\s*2\.1`, L2 `1\.3[89]`, L3 `1\.07`, L6 `a²b†|a\^?2\s*b†|a@a@b\.dag`), replace the reply with the scripted hint at the clamped level and add `"solution_leak"` to `guard.removed`.

**Number guard (`guard.py`):**
- **Extraction:** `extract_numbers(text)` yields one token per quantity. It handles:
  - integers and decimals, with `1,000` read as a thousands separator;
  - `-`, `−` (U+2212) and `±`;
  - scientific notation as **one** token: `1.2e-4`, `1.2E−4`, `1.2×10⁻⁴`, `1.2 x 10^-4`, `1.2·10^−4`;
  - ranges, as two tokens;
  - a unit right after the number: `µs` (U+00B5), `μs` (U+03BC), `us`, `ns`, `ms`, `s`, `MHz`, `kHz`, `GHz`, `Hz`, `%`, `/µs`, `rad/µs`.
- **Ignored:**
  - digits inside identifiers (`L3`, `M5`, `g2`, `t2_3`);
  - record ids (an id-regex token containing `_`);
  - unicode super- and subscripts (`α²`, `κ₂`);
  - **formula coefficients:** a number directly followed, with no space, by a non-unit Latin or Greek letter (`2κ_aα²`, `4e^{−κt}`, `2π`).
- **Normalization:** times to µs (ns ×1e-3, ms ×1e3), frequencies to MHz. `%` keeps its number. Comparison uses absolute values.
- **Pool:**
  - the numeric leaves of this turn's tool results, plus the numbers inside their summaries;
  - record values from this turn;
  - `state.params` and `state.last_sim.summary`;
  - the LEVELS **union** of allowed constants, keeping units (`1 ms` gives 1000 µs and 1);
  - `guard_extra`.
  - **Never** numbers from the learner message, the recap or an image.
- **Decision:** a number is kept if it is within **1% relative** of a pool value (1e-12 absolute for 0). Otherwise the number and its unit are replaced by `(let's check that with a sim)` and listed in `guard.removed`, and `guard.passed = removed == []`.
- **`numbers_cited`** is recomputed on the server as `[{text, value, unit, source: tool:<name> | record:<id> | level_constant | state}]`.
- The guard also cleans the recap before it is shown (with an empty tool pool).

**Memory:**
- **Client:** `backboard-sdk`, or `httpx` against `https://app.backboard.io/api` with the `X-API-Key` header. Verify the assistant, thread and message endpoints in the docs, record them, and wrap them in `BackboardClient`.
- **Storage:** one thread per `learner_id`, mapped in sqlite at `${ACADEMY_DATA_DIR:-/tmp/academy}/memory.sqlite`. `failed_checks` lives in the same file (use a Tiger table instead only if P5 offers one).
- **Event:** a `memory:"Auto"` message such as `"L3: wrong prediction, M3: thought pair-loss empties the box"`: the level, the kind, the M-id with its LEVELS text, and the `detail` (≤ 200 characters).
- **Recap:**
  - It uses `memory:"Readonly"` and asks: "In ≤ 2 sentences, recap this learner's misconceptions; then list ids".
  - It parses `M[1-7]`, keeps only library ids, truncates to 2 sentences or 300 characters, and strips numbers.
  - The model is BYOK Gemini via `llm_provider` + `model_name` if supported, else Backboard's default. **The core tutor's Gemini calls stay direct**, which keeps the Gemini prize claim clean.
- **Errors:** no key gives `503 feature_disabled`; a Backboard error or a 3 s timeout gives `502 upstream_error`. The site ignores both.

**Voice:**
- **TTS call:** `ElevenLabs(api_key).text_to_speech.convert(voice_id, text, model_id, output_format="mp3_44100_128")`, lazily imported.
  - Model: `$ELEVENLABS_TTS_MODEL`, default `eleven_flash_v2_5` for latency (`eleven_v4` for quality).
  - Voice: `voice_id` or `$ELEVENLABS_VOICE_ID`.
  - Text ≤ 800 characters, else `413`.
- **Cache:** `${ACADEMY_DATA_DIR}/tts/<sha256(voice_id+"\n"+text)>.mp3`.
  - A cache hit is served **even without a key**.
  - A miss without a key gives `503 feature_disabled`.
- **Pregen:** `python -m server.app.voice.pregen [--out server/precomputed/audio] [--force]`.
  - It writes `<narrationKey>.mp3` for the 8 concept texts from `levels.json`, plus `manifest.json` (`{key: {sha256, chars, voice_id, model}}`).
  - It skips existing files unless `--force`.

**Site (`site/src/tutor/`):**
- **Mount:** `mountTutor(root, bridge: AcademyBridge, opts:{apiBase})`.
  - `AcademyBridge = {getLevel(), getState(), setParam(name, value), run(): Promise<summary>, showHint(level), nextLevel(), on(event, cb)}`.
  - `bridge.ts` adapts P2's bus and is the only file that imports P2.
- **Memory hooks:** on the bus's wrong-prediction event, `POST /api/memory/event`. At level start, `GET /api/memory/recap` and show "Welcome back…".
- **Panel:**
  - messages;
  - "Hint k of 4";
  - the ✓ "numbers verified" badge, **only** when `guard.passed` is true and `numbers_cited` is non-empty;
  - chips such as `run_sim · live-one-mode`;
  - an "offline" label on scripted replies.
- **Offline (fetch fails, 12 s timeout, or a 503):**
  - Use `canned.json` for the 3 demo questions, matched by keywords: "why did the fringes fade?" (L4), "why does it overshoot?" (L6), "why does the readout ring?" (L7).
  - Each entry is `{level_id, keywords, reply, numbers:[{value, record_id | "level_constant"}]}`.
  - Otherwise use P2's scripted `hints[hint_level-1]`.
- **Voice:**
  - `voice.ts` takes an injected `startSession`.
  - `voice-sdk.ts` is the **only** importer of `@elevenlabs/client`: `Conversation.startSession({agentId: import.meta.env.VITE_ELEVENLABS_AGENT_ID, clientTools})`.
  - The fallback is the `<elevenlabs-convai agent-id>` widget (`@elevenlabs/convai-widget-embed`), with tools set in its `elevenlabs-convai:call` event.
- **Client tools** (they return short strings for the agent to say):
  - `set_param(name, value)` clamps to the control range; an unknown name returns an error string;
  - `run_sim()` returns the summary and its source;
  - `show_hint(level)`;
  - `next_level()`, which respects P2's gating.

## 5. Tests to write FIRST (TDD)
Write all of these, watch them fail, and commit `[p4-tutor] tests first`. All external APIs are mocked: no network, and the SDKs are absent.
1. **`test_tutor_guard.py`** (table-driven). Pool: tool `{n_final: 0.4998, parity: 1.0}`, record 3.138, and the LEVELS union.
   - **Kept:** "plateau is 0.4998"; "κ₂/2π = 0.896 MHz"; "rings at 3.14 MHz"; "56%"; "1,000 µs" (that is 1 ms); "−4.08" when 4.08 is in the pool.
   - **Removed, with the phrase inserted:** "ends near 0.62"; "1.2×10⁻⁴ /µs" (one token); "−0.62"; "7 photons" when the 7 appears only in the learner message.
   - **Not extracted at all:** "level L3, misconception M3"; "record t2_3.ring_freq.td.two_mode.a2.10"; "2κ_aα² coth(2α²)".
   - Also: recap numbers are removed; the `{passed, removed}` shape; the `numbers_cited` sources.
2. **`test_tutor_ladder.py`:**
   - **Clamping:** with failed = 0, a model hint of 4 becomes ≤ `state.hint_level + 1` and ≤ 3. With failed = 1, 4 is allowed.
   - **Leaks:** for **each level**, an answer-pattern reply with failed < 2 is replaced and adds `"solution_leak"`. With failed ≥ 2 it is kept.
   - **Prompt:** it has `solution[:-1]` vs the full solution at failed < 2 vs ≥ 2. It contains "Schrö", the ladder, the off-topic rule, the per-level constants, the M fixes, and the recap inside the data block.
   - **Data:** `build_levels --check` passes; the union in levels.json equals the LEVELS union line; no route returns solution text.
3. **`test_tutor_tools.py`:**
   - `DECLARATIONS` has exactly the 5 names and their params.
   - **run_sim:** L3 builds a one-mode request with `alpha 0, kappa_a_scale 0, init coherent` (simbridge mocked) and gets `source live-one-mode`. L5 and L7 redirect.
   - **L6:** the known build `missing_kb_jump` returns its preset. An unknown build calls two-mode with **Na == 16 and Nb == 5**. A fake 20 s sim returns the preset (`source:"preset"`) within the tool timeout. With < 8 s remaining, no two-mode run starts.
   - **Limits:** a 4th tool call gets the budget error. A level_id mismatch and an out-of-range param are rejected.
   - **get_record** rejects `../x` and reads a fixture record. **lookup_grid** works on fixtures and returns `grid_unavailable` when nothing matches.
   - **check:** L1 at 2.10 passes and at 2.2 fails; L3 at 0.45 passes; a failure increments `failed_checks`.
4. **`test_tutor_api.py`** (TestClient, with FakeLLM scripted as one function call and then the final JSON):
   - The CONTRACT §3 keys are present, and `tool_calls[0].name == "run_sim"`.
   - No key gives 503 `feature_disabled`. A 1001-character message gives 422. A FakeLLM exception gives 200 with `source:"scripted"`.
   - The P5 logger is called when monkeypatched; a missing P5 is harmless.
   - With a fake clock and slow tools, the turn takes < 10 s.
5. **`test_tutor_memory.py`:**
   - An event posts `memory:"Auto"` with the format above. A second event reuses the thread (sqlite in tmp).
   - The recap uses `"Readonly"`, is ≤ 2 sentences, keeps only M1–M7 and strips numbers.
   - No key gives 503; an upstream timeout gives 502.
6. **`test_tutor_voice.py`:**
   - The first TTS call calls the mock once and writes `<sha>.mp3`. The second is a hit: 0 calls, `audio/mpeg`. A different voice is a miss.
   - No key: a hit is still served; a miss gives 503. 801 characters gives 413.
   - With the mock, pregen writes 8 files plus the manifest into tmp and skips existing ones.
7. **`test_tutor_canned.py`:** every number in `site/src/tutor/canned.json` passes the Python guard against the union plus its cited record values. Skip the record part if `results/records` is absent.
8. **Site** (`site/src/tutor/*.test.ts`, vitest + jsdom, with a fake bridge and a fake `startSession`):
   - Each client tool calls the right bridge method; `set_param` clamps; an unknown name never reaches the bridge.
   - The badge shows only when the guard passed and numbers were cited; chips and hint text render.
   - A rejected fetch gives the canned answer for "why does the readout ring?", and the scripted hint otherwise.
   - A wrong-prediction bus event posts a memory event.

## 6. Method, step by step
1. **(5 min)** Create `prod/p4-tutor` and the status file (`IN_PROGRESS`). Copy P0's interface names into status under **Interfaces I rely on**.
2. **(20 min)** `levels_overlay.json` and `build_levels.py`. Generate `levels.json` and get test 2's data checks green.
3. **(35 min)** The guard, until test 1 is green. This is the core: never loosen a case to get it to pass.
4. **(30 min)** `simbridge.py` (one adapter, so a P0 rename touches one file), `records.py`, `grids.py` and `tools.py`, until test 3 is green.
5. **(30 min)** `llm.py`, `prompt.py`, `ladder.py`, `service.py` and `routes.py`, until tests 2 and 4 are green.
6. **(20 min)** Memory, until test 5 is green. **(15 min)** Voice and pregen, until test 6 is green.
7. **(30 min)** The site module and `canned.json`, until tests 7 and 8 are green. For local dev only, run `npm --prefix site install --no-save @elevenlabs/client`. Never commit `package.json`; list the dep in status for P7.
8. **(15 min) Live checks, once Harshit's keys are in `server/.env`.**
   - Run uvicorn locally and ask L4 "why did the fringes fade?". You should see a `run_sim` chip, `guard.passed`, and a reply in under 10 s. Paste it into status.
   - Run pregen to get the 8 mp3s.
   - Voice: say "make the cat bigger", and the α slider should move.
   - Backboard: send one event, then fetch the recap.
9. **(10 min)** Finish the status file (§12), set `DONE`, and commit with explicit paths.

## 7. Outputs
- The code and tests listed in §3, the generated `server/app/tutor/levels.json`, and `site/src/tutor/canned.json`.
- `server/precomputed/audio/{concept_L1..L8}.mp3` plus `manifest.json`. Commit them if they total ≤ 5 MB; otherwise list them as a P7 copy job.
- **Status sections:**
  - **Interfaces I rely on:** the P0, P2 and P5 names as found.
  - **For P7:** exact-version npm deps (`@elevenlabs/client`, plus `@elevenlabs/convai-widget-embed` if used), the `mountTutor` call site, the build env `VITE_ELEVENLABS_AGENT_ID`, and the audio copy.
  - **For P0:** an `ACADEMY_DATA_DIR` volume; `results/`, `src/` and `site/src/data/live/` in the image; and the `.env.example` lines `ELEVENLABS_TTS_MODEL` and `ACADEMY_DATA_DIR`.
  - **ElevenLabs dashboard config**, paste-ready for Harshit: LLM Gemini 3.8 Flash; the agent public with auth off; the shortest max call duration; the system prompt; and the 4 client tools (5 with `ask_tutor`, §11) with JSON param schemas, each set to "wait for response".
  - **Measurements:** p50 and p95 turn latency, and the live transcripts.
- No records, figures or physics outputs.

## 8. Acceptance gates
1. `& $env:DUQ_PY -m pytest server/tests -q` is green (yours plus P0's), and `cd site; npm test` is green for `site/src/tutor/**`. No external calls are made.
2. The test 1 guard table passes in full. Every canned answer passes the guard.
3. With failed < 2, no solution leaks on any level (test 2), and hints never jump more than one step.
4. No turn takes more than 10 s on the fake clock. The tutor's two-mode run is only ever 16 × 5, and only for L6.
5. With no keys:
   - `/api/tutor`, `/api/memory/*` and TTS return `503 feature_disabled`; TTS still serves cache hits.
   - The site shows scripted or canned replies, with no console errors.
6. **Live, once keys exist**, with evidence pasted:
   - one grounded L4 answer, with a `run_sim` call and the ✓ badge;
   - voice moves a slider;
   - the Backboard recap returns.
7. **Clean diff:**
   - `git diff --name-only standard-track...HEAD` ⊆ §3.
   - `git grep -n "API_KEY" -- site/src` shows no values.
   - `levels.json` holds no key.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c prod/p4-tutor standard-track
Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p4-tutor.md
& $env:DUQ_PY -m server.app.tutor.build_levels; & $env:DUQ_PY -m server.app.tutor.build_levels --check
& $env:DUQ_PY -m pytest server/tests -q -k tutor          # your tests
& $env:DUQ_PY -m pytest server/tests -q                   # full server suite before DONE
cd site; npm test; cd ..
& $env:DUQ_PY -m uvicorn server.app.main:app --reload --port 8000     # live checks (keys in server/.env)
$b = @{learner_id=[guid]::NewGuid().ToString(); level_id="L4"; message="why did the fringes fade?"; state=@{params=@{alpha=2.1; loss="x20"}; misconception_ids=@(); last_sim=@{summary=""}; hint_level=1}} | ConvertTo-Json -Depth 5
Measure-Command { Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/tutor -ContentType application/json -Body $b | ConvertTo-Json -Depth 6 | Out-Host }
& $env:DUQ_PY -m server.app.voice.pregen --out server/precomputed/audio
git diff --name-only standard-track...HEAD
```

## 10. Out of scope / do not
- **No physics of your own.** Sims go through P0's runners via `simbridge.py`, and Real Research numbers come only from `results/records`.
  - No two-mode shape other than 16 × 5 from the tutor.
  - No direct dynamiqs calls.
- **Never send a key or the solution to the browser.** Never collect PII.
- **Files and checks:** don't edit `main.py`, `package.json`, the Dockerfile, `conftest.py`, CONTRACT or LEVELS. Don't loosen guard cases.
- **Out of the toolset:**
  - Gemini code execution (SPONSORS: no dynamiqs, 30 s limit);
  - the Gemini Live API (voice runs in ElevenLabs);
  - accounts and streaming (SSE is P0's stretch).

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
Write each one in status, then keep going with anything that doesn't depend on it.
> **Q:** The voice agent's LLM answers inside ElevenLabs, so spoken numbers never pass the guard, and CONTRACT §8's four client tools give it no guarded answer path. Add a fifth client tool, `ask_tutor(question)`, which calls `/api/tutor` and returns the guarded `reply` for the agent to read verbatim? **Options:** A) add it (additive; P4 code plus one dashboard line) B) keep four, and have the agent prompt cite only `run_sim()` output. **Recommendation:** A. **Blocking?** no: build A behind `opts.askTutor = true`.

> **Q:** The LEVELS allowed constants omit numbers that the levels' own hints, solutions and check windows use. Examples: L1 hint 3 "α = 1 and α = 2"; L3 window 0.43–0.47; L7 aha "about 1.1 µs" vs the constant 1.13; L7 solution −4.08 ± 19.7i; L6 "6 buffer levels". A strict guard strips them. **Options:** A) fill `guard_extra` per level from those LEVELS lines, each tagged with its source line B) stay strict. **Recommendation:** A. **Blocking?** no: `guard_extra` stays empty (strict CONTRACT reading) until Harshit answers.

**Other triggers:**
- **P0's one_mode rejects** `alpha 0`, `kappa2_scale 0` or the L2 `kappa_a_scale` of about 107: file a For P0 request, and meanwhile L2 returns `state.last_sim`.
- **P0 precompute** has no L6 builds or L7 signals: `lookup_grid` returns `grid_unavailable`, and the tutor answers from records.
- **Gemini rejects tools plus a schema:** use the two-phase approach.
- **No Backboard BYOK:** use its default model. Log every one of these.

**Fallbacks:**
- **No P2 bus yet:** ship an `AcademyBridge` stub and document the shape.
- **The SDK is blocked:** use the widget.
- **Gemini is down at the demo:** scripted hints plus `canned.json`.

**Cut line (if behind at 3:45 AM), in this order:**
1. `snapshot_png`.
2. Pregen narration (keep the TTS endpoint).
3. The widget fallback.
4. The recap UI (keep `/api/memory/event`).

**Never cut:** the guard; the ladder and the leak check; server-side tools with the 10 s deadline; the scripted and canned offline path; the voice client tools; one Backboard write plus one recap.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer — questions only)
**Status file at DONE:**
- State, branch, last sha, and the server and site test counts.
- The guard table, with each case's result.
- p50 and p95 latency per level, with the tool sources used.
- The live transcripts: an L4 grounded answer with its tool call and guard report, the voice slider moving, and the recap.
- The Interfaces, For P0 and For P7 sections, and the ElevenLabs dashboard config.
- The verified Backboard endpoints, and the Gemini mode (one-phase or two-phase).
- Open DECISION NEEDED items and deviations, including the additive CONTRACT fields.

**Explain-back questions** (Harshit answers in `docs/defense.md`; do not write answers):
1. A learner asks Schrö "how fast does the cat lose parity?" Which tool runs, where does its number come from, and what exactly does the guard do if Gemini writes a value that is 3% off?
2. Why can't the tutor run the learner's level 6 Hamiltonian live at a converged truncation, and how does it still give a correct, sourced answer about the 56% overshoot within 10 seconds?
3. What stops Schrö from handing out the level 3 answer on the first question? And what does Backboard memory change about the next level's conversation, without having any say over the physics numbers?
