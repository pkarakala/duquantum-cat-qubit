# Product contract: interfaces, ownership, schemas (frozen at product gate P-G0)

Product lanes read this together with the root `AGENTS.md`. Its physics rules still apply: units, drives, one physics source. Spec: `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md`.

## 0. Rules specific to product lanes
- **Code branches:** `prod/<slug>`, created from `standard-track`. First ask the integrator to merge `product-academy` (docs only) into `standard-track`.
- **Priority:** physics lanes win every conflict for CPU, review or merge time. Product lanes are cut first.
- **Ownership carve-out:**
  - Lane `l6-lab` owns `site/**`, **except** the product folders in §1, which this contract carves out.
  - `site/package.json`, `site/src/main.ts`, `site/index.html` and `site/vite*.config.ts` stay with l6 until l6 merges. After that, **only P7** edits them.
  - Product lanes list the npm deps and routes they need in their status file, and P7 applies them.
- **Secrets:** keys live only in the server's `.env` on Vultr and a local `server/.env`, which is git-ignored. Commit only `server/.env.example`.
- **Learners are pseudonymous:** `learner_id` is a UUID v4 from localStorage, plus an optional chosen alias. Never collect email or name.
- **The physics source of truth is `src/model.py`.** The server imports it. The TS solver mirrors the one-mode model and is golden-tested (§5).
- **Exception to the root `AGENTS.md` rule 9 ("no physics in readers"):** learning sims may compute in the browser, in `site/src/sim/**` (P1) and `site/src/academy/**` (P2, e.g. `formulas.ts`). They are validated against dynamiqs, and they **never** supply Real Research numbers, which still come only from `results/records`. P7 narrows the l6 lab's "no physics in `site/src`" grep gate to exclude these two folders.

## 1. Lanes and ownership
| Slug | Brief | Owns | Depends on |
|---|---|---|---|
| `p0-server` | `briefs/P0-server.md` | `server/app/**` (FastAPI app, sim endpoints, cache, schemas), `server/Dockerfile`, `server/requirements.txt`, `server/.env.example`, `server/tests/**` (except tutor, data and chain tests), `deploy/docker-compose.yml`, `deploy/Caddyfile`, `deploy/README.md`, `server/precompute.py`, `server/precomputed/**` | `l0-core` merged |
| `p1-ts-sim` | `briefs/P1-ts-sim.md` | `site/src/sim/**` | none (pure TS) |
| `p2-academy` | `briefs/P2-academy.md` | `site/src/academy/**` (engine, level specs, UI, presets, scripted hints) **except `site/src/academy/routes.ts`** (P7) | P1 interface; l6 skeleton |
| `p3-blocks` | `briefs/P3-blocks.md` | `site/src/blocks/**` | §4 ExprTree |
| `p4-tutor` | `briefs/P4-tutor.md` | `server/app/tutor/**`, `server/app/memory/**`, `server/app/voice/**`, `server/tests/test_tutor*.py`, `site/src/tutor/**` | P0 skeleton |
| `p5-data` | `briefs/P5-data.md` | `server/app/data/**`, `server/sql/**`, `server/tests/test_data*.py` | P0 skeleton |
| `p6-chain` | `briefs/P6-chain.md` | `chain/**` (Node service), `site/src/chain/**` | P0 compose |
| `p7-integrate` | `briefs/P7-integrate.md` | `site/package.json`, `site/src/main.ts`, `site/index.html` and `site/vite*.config.ts` (after l6 merges); `site/src/academy/routes.ts` wiring; `deploy/**` runbook updates; `docs/product/status/p7-integrate.md` | all of the above |
| `p8-docs` | `briefs/P8-docs.md` | `docs/product/devpost.md`, `docs/product/sponsor_writeups.md`, `docs/product/dev_post.md`, `docs/product/demo_script.md`, and the README "Academy" section **via l7-docs** (send text to l7; don't edit README directly) | all |

Every lane owns `docs/product/status/<slug>.md`. Use `docs/plan/status/_TEMPLATE.md` as the template.

## 2. Environment
- **Server (Vultr):** Ubuntu 24.04 on a CPU-Optimized instance with 4 vCPU or more and 8 GB RAM or more. Docker and docker compose.
  - Python 3.12 image, with `dynamiqs==0.3.7` and the jax pin from root `requirements.txt`, plus `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `httpx`, `slowapi`, `psycopg[binary]`, `google-genai`, `backboard-sdk`, `elevenlabs`.
- **Chain service:** Node 22 with `@metaplex-foundation/umi`, `@metaplex-foundation/umi-bundle-defaults`, `@metaplex-foundation/mpl-core`, `@solana/web3.js`, and `hono` (or `express`).
- **Local dev:** `server` runs with `uvicorn server.app.main:app --reload --port 8000` from the repo root, so `src/` is importable. The site runs with `npm run dev` in `site/`, with `VITE_API_BASE=http://localhost:8000`.
- **Env vars** (`server/.env.example`): `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.8-flash`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_AGENT_ID`, `BACKBOARD_API_KEY`, `TIGER_DATABASE_URL`, `SOLANA_RPC_URL=https://api.devnet.solana.com`, `SOLANA_SECRET_KEY_B58` (chain service only), `ADMIN_TOKEN`, `ALLOWED_ORIGINS`, `SIM_TIMEOUT_ONE_MODE_S=8`, `SIM_TIMEOUT_TWO_MODE_S=15`.
- **Client timeouts:** 3 s for normal server calls; up to 15 s with a progress state for the L6 live run. After that, fall back to a preset.
- **`API_HOST`**, e.g. `45-76-1-2.sslip.io`, is used by Caddy and by the chain service's metadata URLs.
- **Secret isolation:**
  - The api container reads `/opt/academy/.env`, which does **not** contain `SOLANA_SECRET_KEY_B58`.
  - The chain container reads `/opt/academy/chain.env` (`SOLANA_SECRET_KEY_B58`, `SOLANA_RPC_URL`, `ADMIN_TOKEN`, `API_HOST`).
  - The api's `features.chain` comes from probing `GET /api/chain/health`, not from env.
- **Deploy:** `docker compose --env-file /opt/academy/.env up -d --build`, run from `deploy/`.
- **`.env` files are git-ignored by root `.gitignore`.** Only `*.env.example` is committed.

## 3. HTTP API (JSON; all errors are `{"error": {"code": str, "message": str}}`)
Base: `https://<vultr-ip>.sslip.io` in production, `http://localhost:8000` in development. CORS allows `ALLOWED_ORIGINS`, plus `null` for the `file://` build.

| Method and path | Request | Response | Owner |
|---|---|---|---|
| `GET /api/health` | n/a | `{ok, version, engine:"dynamiqs 0.3.7", features:{gemini, elevenlabs, backboard, tiger, chain}}` | P0 |
| `POST /api/sim/one_mode` | `{alpha, kappa2_scale=1, kappa_a_scale=1, n_th=0, eps_z_over_g2=0, eps_x_over_g2=0, N=30, t_end_us=2, n_t=200, init:"vacuum"\|"coherent"\|"cat_plus"\|"cat_minus", init_alpha?, outputs:["n","parity","re_a","wigner"], wigner_times?:[us], learner_id?, level_id?}` (the last two are used only for Tiger logging) | `{t_us[], n[], parity[], re_a[], wigner?:{x[], y[], frames:[{t_us, w:[[...]]}]}, meta:{engine, cached, wall_ms, params_hash}}` | P0 |
| `POST /api/sim/two_mode` | `{alpha, g2_scale=1, kappa_b_scale=1, kappa_a_scale=1, n_th=0, eps_z_over_g2=0, eps_x_over_g2=0, Na=16, Nb=5, t_end_us≤3, init, learner_id?, level_id?, outputs}`. κ₂ is derived from g₂ and κ_b, so there's no `kappa2_scale` here. **Live caps:** Na ≤ 20, Nb ≤ 6, `n_t` fixed at 201. `outputs` ⊆ `["na","nb","b_re","b_im","top2_a","top_b","parity","wigner"]` | `{t_us[], na[], nb[], b_re[], b_im[], top2_a[], top_b[], parity[], wigner?, meta}` | P0 |
| `POST /api/sim/expr` | `{H: ExprTree, jumps: [ExprTree], params:{name: number}, modes:"one"\|"two", N\|Na,Nb, init, t_end_us, n_t, outputs}` | as above, plus `meta.compiled:"<human-readable H>"` | P0 |
| `POST /api/tutor` | `{learner_id, level_id, message, state:{params, prediction?, misconception_ids:[], last_sim:{summary}, hint_level}}` | `{reply, hint_level, tool_calls:[{name, args, result_summary}], numbers_cited:[...], guard:{passed, removed:[...]}}` | P4 |
| `POST /api/memory/event` | `{learner_id, level_id, kind:"wrong_prediction"\|"pass"\|"hint", misconception_id?, detail?}` | `{ok}` | P4 |
| `GET /api/memory/recap?learner_id=&level_id=` | n/a | `{recap: str, misconceptions:[ids]}` | P4 |
| `POST /api/voice/tts` | `{text, voice_id?}` | `audio/mpeg` (cached by sha256 of text+voice) | P4 |
| `POST /api/runs` (server-internal, also used by sims) | a run row (§6) | `{ok}` | P5 |
| `GET /api/community/alpha?minutes=60` | n/a | `{buckets:[{t, alpha_bin, count}]}` (from a continuous aggregate) | P5 |
| `GET /api/leaderboard?challenge=readout_pulse` | n/a | `{rows:[{alias, score, payload_hash, ts}]}` | P5 |
| `POST /api/leaderboard` | `{challenge, learner_id, alias, score, payload}` (the server recomputes the score; never trust the client) | `{rank}` | P5 |
| `POST /api/progress` / `GET /api/progress?learner_id=` | `{learner_id, level_id, passed, prediction_correct, attempts}` | `{levels:[...]}` | P5 |
| `POST /api/chain/credential` | `{learner_id, alias, wallet_pubkey?, levels_passed:[...], score?, l8_payload_hash?}` | `{asset_address, tx_sig, explorer_url, custodial: bool}` | P6 |
| `POST /api/chain/anchor` (header `X-Admin-Token`) | `{sha256, label}` | `{tx_sig, explorer_url}` | P6 |
| `GET /api/chain/anchors` | n/a | `{anchors:[{label, sha256, tx_sig, explorer_url, ts}]}` | P6 |

**Caps:** sims are rejected when they exceed the size or time caps (`413` with code `too_large`). The server timeout gives `504 sim_timeout`, and the client then falls back to a preset.

**Two-mode is not interactive, even on the server.** On this laptop (3 µs, 301 saves, rtol 1e-8, JIT included) a run takes 5.5 s at 40×4, 11.5 s at 16×14, 14.5 s at 40×6 and 76 s at 32×14. So:
- **The live shape is fixed at Na = 16, Nb = 5**, with live caps Na ≤ 20, Nb ≤ 6, a fixed `n_t` of 201, rtol 1e-6 / atol 1e-8, and `t_end` ≤ 3 µs.
- **Warm-up:** these shapes are compiled at startup, with the JAX persistent compilation cache enabled.
- **Timeouts:** 15 s for two-mode and 8 s for one-mode.
- **Precomputed builds:** the common level 6 block builds (correct H; missing √κ_b·b; ε(a+a†) instead of the buffer drive; a·b†² instead of a²b†) and the level 7 readout signals are **precomputed** by `server/precompute.py`, so the site never depends on a live two-mode run.
- **Client fallback order:** server (3 s, or up to 15 s with a progress indicator for L6), then the nearest precomputed preset, then the in-browser one-mode solver. A badge shows which source is active.
- **Stretch:** `GET /api/sim/stream/<job_id>` streams SSE in 0.5 µs chunks (same shape, so it never recompiles).
- **Hosting:** keep one Vultr instance always on and warm. The image is about 1–1.5 GB with a 30–60 s cold start.

## 4. ExprTree (shared by blocks, the TS solver and the server)
```json
{"op": "add", "args": [
  {"op": "mul", "args": [{"op": "param", "name": "g2"}, {"op": "pow", "base": {"op": "sym", "name": "a"}, "exp": 2}, {"op": "sym", "name": "bd"}]},
  {"op": "mul", "args": [{"op": "num", "value": -1}, {"op": "param", "name": "eps_d"}, {"op": "add", "args": [{"op": "sym", "name": "b"}, {"op": "sym", "name": "bd"}]}]}
]}
```
*The example above is abbreviated. A Hermitian H must also contain the h.c. term g₂·a†²·b, as in fixture `h_2ph.json`, and the validator rejects the abbreviated form.*
- **Symbols (allowlist):**
  - `a` (memory annihilation), `ad` (a†), `b`, `bd` (buffer; two-mode only), `I` (identity), `n_a` (= ad·a).
  - **The complete op list, with shapes:**
    - `{"op":"num","value":<real>,"imag":<real, default 0>}`: a complex literal. `imag` lets the real-axis drive ε_x·i(a†−a) be written.
    - `{"op":"param","name":<allowlisted>}`
    - `{"op":"sym","name":<allowlisted>}`
    - `{"op":"add","args":[...]}`
    - `{"op":"mul","args":[...]}`: non-commutative, left to right.
    - `{"op":"pow","base":<tree>,"exp":<int 0–4>}`
    - `{"op":"dag","arg":<tree>}`
    - `{"op":"sqrt","arg":<param|num>}`
  - **Number formatting in `toPython` / `to_python`:**
    - Integers print without `.0`.
    - Other reals print with the shortest round-trip decimal, never in exponent form; fixtures only use values with ≤ 6 decimals.
    - A pure imaginary prints as `1j*` (e.g. `1j*eps_x*(a.dag() - a)`), and a general complex as `(re+imj)`.
    - Products use `@`, powers are expanded (`a@a`, never `**`), and sums are joined with ` + ` / ` - `.
  - `param` names are restricted to `g2`, `eps_d`, `kappa_b`, `kappa_a`, `kappa2`, `alpha`, `eps_z`, `eps_x`, `K` and `chi`.
- **Jump operators** are ExprTrees whose coefficient is wrapped as `{"op":"sqrt","arg":{"op":"param",...}}`. `sqrt` applies only to params or nums.
- **Validation:**
  - Depth ≤ 8; node count ≤ 64.
  - H must be Hermitian. Check it numerically at small N, to within 1e-9.
  - Units: params are in rad/µs, and come only from `src/config.py` scalings on the server or from `config.ts` constants on the client.
- **Pretty printer:** `toLatex(tree)` and `toPython(tree)`, where the Python form is the dynamiqs snippet used by "Show the code". Both are implemented in TS (`site/src/blocks/expr.ts`) and Python (`server/app/expr.py`). They must produce identical strings for the fixtures in `server/tests/fixtures/expr/*.json`.

## 5. TS solver interface (`site/src/sim/`)
```ts
export interface OneModeParams { N: number; alpha: number; kappa2: number; kappaA: number; nTh?: number; epsZ?: number; epsX?: number; H?: ExprTree; jumps?: ExprTree[] }
export interface SimRequest { params: OneModeParams; init: { kind: 'vacuum' | 'coherent' | 'cat_plus' | 'cat_minus' | 'fock'; alpha?: number; n?: number }; tEndUs: number; nT: number; outputs: ('n' | 'parity' | 're_a' | 'wigner')[]; wignerTimes?: number[] }
export interface SimResult { tUs: Float64Array; n?: Float64Array; parity?: Float64Array; reA?: Float64Array; finalPops?: Float64Array /* Fock populations at t_end (L1/L3 histograms) */; wigner?: { x: Float64Array; y: Float64Array; frames: { tUs: number; w: Float64Array /* row-major */ }[] }; meta: { engine: 'ts-cn'; wallMs: number; nSteps: number } }
export function simulate(req: SimRequest): SimResult           // pure, deterministic
export function runInWorker(req: SimRequest): Promise<SimResult> // Web Worker wrapper
export function wigner(rho: ComplexMatrix, x: Float64Array, y: Float64Array): Float64Array // Clenshaw (QuTiP-style)
```
- **Constants** (`site/src/sim/config.ts`) mirror `src/config.py`: `G2 = 2π·0.763`, `KAPPA_B = 2π·2.6`, `KAPPA_A = 2π·9.3e-3`, `ALPHA = 2.1`, `KAPPA_2 = 4·G2²/KAPPA_B`. All rates are in rad/µs.
- **Golden tests** (vitest), against values in committed `results/task_1_0.json`:
  - 1.0b plateau `0.4998322686860546` to 1e-4 relative, at N = 30.
  - 1.0a ⟨n⟩ against 4e^{−κt} to 1e-4, with Δ/2π = κ/2π = 1 MHz.
  - 1.0c final ⟨n⟩ for κ₂/4, κ₂ and 4κ₂: `4.387, 4.404, 4.408` to 1e-3.
  - **Wigner convention = dynamiqs (QuTiP `g = 2`):** x = Re α and y = Im α. Vacuum gives **W(0,0) = 2/π**, |α=2⟩ peaks at x = 2, and C₊ has min W < −0.2. Verify numerically against `dq.wigner` output that P0 exports to `server/tests/fixtures/wigner/*.json` (vacuum, coherent with α = 2, and cat C₊ with α = 2, all at N = 30). A test is skipped until that fixture exists.
- **Solver** (measured on the target laptop): **Crank–Nicolson on the vectorized superoperator with a banded LU** (bandwidth 2N+2, no pivoting).
  - CN is A-stable, so κ₂ changes don't force a smaller dt. Explicit RK4 is stiff here (dt ≲ 2.8/(κ₂N²)) and takes 1.5 s at N = 30, so don't use it.
  - Measured CN timings: N = 30 with 200 steps takes 180 ms; N = 20 takes 130 ms; N = 40 takes 530 ms.
  - The steady state matches RK4 to 5 digits. The transient n̄ error is about 1e-2 at 200 steps and 7e-4 at 800.
  - **Interactive default: 400 steps over 2 µs.** Golden tests may use finer steps (e.g. 4000) to meet their tolerances. Document the error at the interactive setting.
  - **Bug trap:** if the right-hand side uses the ρ = ρ† shortcut, re-Hermitize every step. Otherwise round-off grows like e^{+κ₂n²t} and the run diverges near 0.3 µs.
- **Wigner:** port QuTiP's Clenshaw method and precompute the position-independent coefficients. Measured: 13 ms per 81×81 frame at N = 30. Use the dynamiqs convention described below, where vacuum is W(0,0) = 2/π; QuTiP's default `g = √2` would give 1/π. Draw frames on a raw `<canvas>` (ImageData), not as Plotly heatmaps.
- **Performance target:** N = 30, 2 µs, **400 CN steps in ≤ 400 ms** (measured 180 ms per 200 steps), off the main thread.
- **Linear response** (`site/src/sim/linresp.ts`; level 8 scoring, offline): a TS port of root `src/linresp.py` (physics CONTRACT §9).
  - **TS signatures.** This is a TS-specific API; the physics is identical to the Python modules but the argument shapes differ.
    - `poles(g2, kappaB, alpha): {re, im}[]`
    - `response(epsBins, edgesUs, g2, kappaB, alpha, well, nSamples): {tUs, da, b}`: exact 2×2 complex matrix-exponential stepping per bin.
    - `snr(tUs, deltaB, kappaB): number`, computing κ_b∫|Δb|²dt.
    - `leakageProxy(tUs, da): number`, computing ∫|δa|²dt.
    - `optimalPulse(nBins, T, g2, kappaB, alpha): {epsBins, gain}`: the top singular vector of R_b, by power iteration on R_bᴴR_b.
  - **Python counterparts:** `poles`, `response` and `optimalPulse` correspond to root `src/linresp.py` (physics lane l4a). `snr` and `leakageProxy` correspond to `src/pulses.py` (physics lane l4c). Until those merge, P0 builds the parity fixtures from its marked reference implementation.
  - Golden test: poles = −4.08 ± 19.72i /µs at nominal parameters.
  - Parity test: it must match the Python `src/linresp.py` on 3 fixture pulses to 1e-9, using fixtures exported by P0 into `server/tests/fixtures/linresp/*.json`.

## 6. Tiger Data schema (`server/sql/001_init.sql`, owned by P5)
```sql
CREATE TABLE sim_runs (
  ts timestamptz NOT NULL DEFAULT now(), learner_id uuid, level_id text, engine text NOT NULL,
  model text NOT NULL, params jsonb NOT NULL, params_hash text NOT NULL,
  alpha double precision, kappa2_scale double precision, eps_z_over_g2 double precision,
  na_final double precision, t_x_us double precision, t_z_us double precision, snr double precision,
  wall_ms integer, cached boolean
) WITH (tsdb.hypertable, tsdb.partition_column = 'ts');
CREATE TABLE progress (learner_id uuid, level_id text, passed boolean, prediction_correct boolean, attempts int, ts timestamptz DEFAULT now(), PRIMARY KEY (learner_id, level_id));
CREATE TABLE leaderboard (challenge text, learner_id uuid, alias text, score double precision, verified boolean DEFAULT false, payload jsonb, payload_hash text, ts timestamptz DEFAULT now());
CREATE TABLE tutor_events (ts timestamptz DEFAULT now(), learner_id uuid, level_id text, kind text, misconception_id text, hint_level int, tool_calls int, guard_removed int);
CREATE MATERIALIZED VIEW alpha_choices_5m WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
  SELECT time_bucket('5 minutes', ts) AS t, LEAST(width_bucket(alpha, 0, 3, 12), 12) AS alpha_bin, count(*) FROM sim_runs GROUP BY 1, 2
  WITH NO DATA;
SELECT add_continuous_aggregate_policy('alpha_choices_5m', start_offset => INTERVAL '2 hours', end_offset => INTERVAL '1 minute', schedule_interval => INTERVAL '1 minute');
```
- `timestamptz` values are serialized as ISO-8601 UTC.
- **Run the continuous-aggregate creation in autocommit mode**, not inside a transaction. `LEAST(…, 12)` keeps α = 3.0 in the top bin.
- **Level 8 challenge constants** (P5 recomputes the score with them, and P2 mirrors them):
  - T = 1 µs, 20 bins (≤ 50 accepted), amplitude ≤ 3·g₂.
  - The reference is a square pulse at 0.5·g₂.
  - Energy budget: 0.25·g₂²·µs.
  - Prototype values, to be verified by P5 and P1: square SNR ≈ 0.95, SVD-optimal ≈ 4.06.
- **Don't use pgai** (archived May 2026).
- If `tsdb.hypertable` syntax fails on the provisioned version, fall back to `SELECT create_hypertable('sim_runs', 'ts');` and record it.

## 7. Level spec format (`site/src/academy/levels/L<n>.ts`, owned by P2; content in `docs/product/LEVELS.md`)
```ts
export interface LevelSpec {
  id: 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6' | 'L7' | 'L8'; title: string; minutes: number;
  concept: { text: string; narrationKey: string /* cached mp3 id */ };
  predict: { question: string; options: { id: string; text: string; correct: boolean; misconception?: MisconceptionId; feedback: string }[] };
  controls: Control[];            // ≤ 3 visible controls (PhET "productive constraint")
  sim: { engine: 'ts' | 'server-two-mode' | 'server-expr' | 'records'; request: (state) => SimRequest | object };
  views: View[];                  // linked representations, e.g. 'n_t' | 'wigner' | 'parity' | 'b_iq' | 'rates_log' | 'pulse'
  check: { goal: string; fn: (result, state) => { pass: boolean; message: string } };
  predictFollowUp?: { question: string; options: { id: string; text: string; correct: boolean; misconception?: MisconceptionId; feedback: string }[] }; // e.g. L5 "…and phase flips?"
  checkParts?: { goal: string; fn: (result, state) => { pass: boolean; message: string } }[]; // e.g. L4 part 2
  aha: string; showCode: (state) => string /* dynamiqs snippet via toPython */;
  allowedConstants: number[];     // the tutor's number guard whitelist for this level (from LEVELS.md)
  solution: string[];             // hidden step-by-step (tutor grounding)
  hints: [string, string, string, string]; // scripted offline hint ladder
  preset: string;                 // precomputed fallback JSON id
  sources: string[];              // record ids / task refs shown in "where this comes from"
}
type MisconceptionId = 'M1' | 'M2' | 'M3' | 'M4' | 'M5' | 'M6' | 'M7';
```

## 8. Tutor tools (Gemini function declarations, owned by P4)
- `run_sim(level_id, params)`: calls the sim endpoints with caps and returns a summary: final ⟨n⟩, parity, settle time, SNR.
- `get_level_state()`: the current controls, prediction and last result summary.
- `get_record(id)`: a verified record from `results/records` (value, units, convergence, cross-check).
- `lookup_grid(name, params)`: a precomputed grid lookup, for example the Γ_X(α) curve or the readout trade-off.
- `check(level_id, answer)`: runs the level's check.
- **Guard:** after generation, every number in the reply must appear in a tool result or record within 1% (or be a level constant listed in `LEVELS.md`). Otherwise strip the number and add "(let's check that with a sim)".
- ElevenAgents **client tools** (browser): `set_param(name, value)`, `run_sim()`, `show_hint(level)`, `next_level()`. They call the same functions the UI uses.
