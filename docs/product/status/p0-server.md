# Status: lane `p0-server`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p0-server` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 00:26 |
| Last update (EDT) | 2026-10-25 00:57 |
| Last commit | recorded by `git log -1` on this branch |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH
- [x] Tests written first (health, caps, timeout, cache, CORS, auto-include, expr fixtures, physics)
- [x] Implementation complete
- [x] Fast and slow server tests pass
- [x] Precompute finished locally
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## Acceptance gates
| Gate | Result | Evidence |
|---|---|---|
| Fast and slow `server/tests` | pass | `pytest server/tests -q` → `21 passed` in 32.92s. The only warning is Starlette's httpx deprecation. |
| Skeleton pushed by 12:45 | not pushed | The lane prompt forbids push. Branch `prod/p0-server` is local for the integrator. |
| Warm latencies | pass | See commands. Warm one-mode 0.84 s, warm two-mode 0.84 s, both under 15 s and under the 5 s target. |
| Presets and fixtures | pass | L1–L4 (default + 3 positions), L6 (4 builds + 24×6 + 32×12), L7 (7 drives). Wigner and linresp fixtures written. |
| Docker build | not run | `docker` is not installed on this Mac (`command not found`). The Dockerfile and compose file are in the tree for P7. |
| No secrets in git | pass | `server/.env` is gitignored. `server/.env.example` has empty values. A content search of the tree found no key material. |

## What runs
From the repo root, with the shared venv:

```text
python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8000
python -m pytest server/tests -q
python -m server.precompute --levels all
```

Live smoke on port 8123 with `ACADEMY_WARMUP=0` and `server/.env` loaded:

```text
features gemini=true elevenlabs=true backboard=false tiger=true chain=false
integrations gemini=live elevenlabs=live tiger=live vultr=demo solana=demo backboard=demo
```

`POST /api/sim/one_mode` at N=4 returned `engine=dynamiqs 0.3.7`, `cached=false`, five samples. `Origin: null` received `access-control-allow-origin: null`.

## Endpoints
| Method and path | Behavior |
|---|---|
| `GET /api/health` | Contract body plus `integrations` and `demo_mode`. |
| `POST /api/sim/one_mode` | dynamiqs via `src.model.one_mode`. Caps N≤40, t≤5 µs, n_t≤400. Timeout 8 s. |
| `POST /api/sim/two_mode` | via `src.model.two_mode`. Caps Na≤20, Nb≤6, t≤3 µs, n_t fixed at 201. Timeout 15 s. |
| `POST /api/sim/expr` | Allowlisted ExprTree only. 422 `invalid_expr` when the tree is illegal or H is not Hermitian. |
| `POST /api/runs` | Persistence hook. Hands the row to registered sinks. |
| `POST /api/memory/event`, `GET /api/memory/recap` | Backboard demo until `server/app/memory/routes.py` exists. `demo_mode: true`. |
| `GET /api/chain/health`, `POST /api/chain/credential`, `POST /api/chain/anchor`, `GET /api/chain/anchors` | Solana demo until the chain service answers. `tx_sig` is null. Anchor requires `X-Admin-Token`. |

Errors are `{"error": {"code", "message"}}`: `413 too_large`, `504 sim_timeout`, `422 invalid_expr`, `422 validation_error`, `429 rate_limited` (30/min/IP on sim routes).

Tutor and voice routes are not mounted. Those call Gemini and ElevenLabs for real, and they belong to p4. This process does not fake them.

## Commands run (most recent first)
```text
pytest server/tests -q
21 passed, 1 warning in 32.92s

python -m server.precompute --levels benchmark
{"cold_one_mode_s": 3.067, "warm_one_mode_s": 0.84, "cold_two_mode_s": 2.821, "warm_two_mode_s": 0.841}

curl http://127.0.0.1:8123/api/health
features.gemini/elevenlabs/tiger true; backboard and chain false
integrations vultr/solana/backboard = demo

Tiger sink: install_tiger_sink inserted one smoke row and deleted it. tiger_ok.
```

Physics anchors from the presets:

```text
L1 coherent α=2.1 → ⟨n⟩=4.410
L3 α=2 pair loss → final ⟨n⟩=0.4998 (task 1.0b plateau 0.49983)
L4 vacuum, κ₂ nominal, κ_a off, 2 µs → final ⟨n⟩=4.409
L6 correct 16×5 → peak ⟨n_a⟩=5.412, final 4.405, length 201
starter 24×6 peak 6.1145 (committed task_1_1 starter_peak_na 6.1145)
converged 32×12 peak 6.8944 (committed peak_na 6.8944)
L7 ε_Z/g₂=0.1 → ⟨b⟩_re = ∓0.02375 (analytic ∓ε/(2αg₂)=∓0.02381)
```

`test_one_mode_physics`: final ⟨n⟩ within 1% of 4.403969. `test_two_mode_live_shape`: peak ⟨n_a⟩>4.41 and every series length 201.

## Preset inventory
`server/precomputed/presets/`: L1 (4 files), L2 (4), L3 (4), L4 (4), `correct.json`, `missing_kappa_b.json`, `eps_z_drive_wrong.json`, `a_bd2_wrong.json`, `starter_24x6.json`, `converged_32x12.json`, L7 index plus `L7_eps_{0p05,0p1,0p2,0p5,1p0,2p0,3p0}.json`, `index.json`.

Fixtures: `server/tests/fixtures/expr/*.json` (including the invalid cases), `wigner/{vacuum,coherent2,catplus2}.json` (vacuum W(0,0)=2/π), `linresp/{square,cosramp,clear}.json` with `reference_impl: true`. Poles of the reference are −4.08 ± 19.72i /µs.

## Env vars
Live when set: `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, `TIGER_DATABASE_URL`. Also `GEMINI_MODEL`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_AGENT_ID`, `ALLOWED_ORIGINS`, `SIM_TIMEOUT_ONE_MODE_S`, `SIM_TIMEOUT_TWO_MODE_S`, `JAX_COMPILATION_CACHE_DIR`, `CHAIN_HEALTH_URL`, `ADMIN_TOKEN`.

Demo until provided: `BACKBOARD_API_KEY`, Vultr (no key; the interface is `deploy/docker-compose.yml`), Solana (`SOLANA_SECRET_KEY_B58` belongs in `chain.env`, not the api env).

`ACADEMY_WARMUP=0` skips the startup compile. `ACADEMY_SKIP_TIGER=1` and `ACADEMY_SKIP_CHAIN=1` are for tests.

## Deviations
- `src.model` on this branch has no `eps_z` / `eps_x` / `coherent2` / `cat2`. `server.app.sim._two_mode_compat` adds the drive terms. See DECISION NEEDED.
- `/cache/jax` is not writable here, so the persistent cache is skipped unless `JAX_COMPILATION_CACHE_DIR` points at a writable directory. The image creates `/cache/jax` for the `academy` user.
- `.dockerignore` is outside the brief's file list. It keeps `server/.env` out of the image.
- Package `__init__.py` files and `server/__init__.py` are required for imports. `tutor`, `memory`, `voice`, and `data` stay empty of routes.
- LEVELS says the 16×5 peak is about 6.4. This run peaks at 5.412. The 24×6 and 32×12 presets match the committed task 1.1 peaks, and the live test only requires a peak above 4.41.
- Docker was not built. P7 builds it on the VM.
- Not pushed.

## Jobs to queue
None. Precompute finished in about 60 s. The 32×12 reference was included.

## DECISION NEEDED
> **Q:** Remove `server.app.sim._two_mode_compat` after `l0-core` merges `eps_z`, `eps_x`, `coherent2`, and `cat2` into `src/model.py`?
> **Options:** A) Delete the adapter once those signatures exist. B) Keep it as a fallback for older checkouts.
> **Recommendation:** A. The adapter already calls the model functions when the parameters exist.
> **Blocking?** no

## Explain-back for Harshit
1. Why does the server build physics only through `src/model.py`, and how does that keep the Academy consistent with the verified research?
2. Why can't two-mode runs be live, and what does the site show instead?
3. Why is it safe to let learners send Hamiltonians to the server?

## Notes for Claude's later review
- ExprTree `to_python` is locked to `server/tests/fixtures/expr/*.json`. P3 must match those strings, including `1j*eps_x*(a.dag() - a)` and `g2*a@a@b.dag() + g2*a.dag()@a.dag()@b - eps_d*(b + b.dag())`.
- `h_2ph` compiled at 8×3 matches `src.model.two_mode` to 1e-12.
- Sims run in a spawn process pool of 2. A monkeypatched runner is executed in-process so the timeout test can see it. Timeouts do not kill the worker.
- The Tiger writer creates `sim_runs` if needed and tries `create_hypertable`. P5 should use `IF NOT EXISTS`.
- Demo chain and memory routes are skipped automatically once `memory/routes.py` exists or the chain health probe succeeds.
- No tolerance was loosened. The one-mode physics assertion is the brief's 1% window around 4.403969.
