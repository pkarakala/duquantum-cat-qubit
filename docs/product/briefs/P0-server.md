# Brief `p0-server`: Academy API server (FastAPI + dynamiqs), deploy bundle, precompute

> **Paste into a new Cursor agent (worktree mode):** "You are product lane `p0-server`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P0-server.md`, then execute the brief exactly. Keep `docs/product/status/p0-server.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p0-server` | `prod/p0-server` from `standard-track` | physics `l0-core` merged (for `src/model.py` extensions); `product-academy` docs merged into `standard-track` | strongest | 2.5 h | 11:45 PM → 2:15 AM (P-G1). **Push the skeleton by about 12:45 AM**, because P4, P5 and P6 build on it. |

## 1. Goal and why
This is the backbone of the Academy: one FastAPI service that:
- runs **real dynamiqs physics**, built only through the repo's `src/model.py`, so there is a single physics source;
- hosts every other sponsor integration as a plug-in router;
- ships as a Docker image for **Vultr**.

Two-mode simulations are **not interactive**. They measured 5–76 s per run on this laptop (CONTRACT §3). So you serve a fixed small live shape and precompute everything the levels rely on.

## 2. Read first
- `docs/product/CONTRACT.md` §0–§4 and the §3 "Two-mode is not interactive" paragraph; `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md` §4 and §6–§8.
- Root `src/config.py`, `src/model.py` (`one_mode`, `two_mode`, `coherent2`, `cat2`, `drive_ops`) and `src/analysis.py`. Import `src.config` **first**, because it sets double precision.
- `docs/plan/RESEARCH.md` §1 (parameters), §2 (dynamiqs API: no `options=`; `save_extra(t, rho)`; `Tsit5(max_steps=…)`) and §4.1 (drive quadratures).
- `docs/product/LEVELS.md` (which presets each level needs).

## 3. Allowlist (touch nothing else)
- `server/app/main.py`, `server/app/sim.py`, `server/app/expr.py`, `server/app/schemas.py`, `server/app/cache.py`, `server/app/limits.py`, `server/app/settings.py`
- Package placeholders (each with only an empty `__init__.py`): `server/app/{tutor,memory,voice,data}/__init__.py`. They are owned by P4 and P5 afterwards.
- `server/requirements.txt`, `server/Dockerfile`, `server/.env.example`, `server/precompute.py`
- `server/precomputed/**` (presets and grids)
- `server/tests/conftest.py`, `server/tests/test_sim.py`, `server/tests/test_expr.py`, `server/tests/test_api.py`, `server/tests/fixtures/expr/**`, `server/tests/fixtures/linresp/**`
- `deploy/docker-compose.yml`, `deploy/Caddyfile`, `deploy/README.md`
- `docs/product/status/p0-server.md`

## 4. Interfaces you implement
- **Router auto-include.** In `main.py`, for each package in `server/app/*/`, if `routes.py` exists, import it and `app.include_router(module.router)`. This way **P4, P5 and P6 never edit `main.py`**. Log which routers were loaded.
- **Endpoints, exactly as CONTRACT §3:**
  - `GET /api/health`. `features` is a set of booleans, derived from which env keys are present.
  - `POST /api/sim/one_mode`, `POST /api/sim/two_mode`, `POST /api/sim/expr`.
  - Typed errors are `{"error": {"code", "message"}}` with `413 too_large`, `504 sim_timeout`, `422 invalid_expr` and `429 rate_limited`.
- **`sim.py`:**
  - `run_one_mode(req) -> dict` and `run_two_mode(req) -> dict`.
  - Build H and jumps with `src.model.one_mode` / `two_mode` only. Drives map as `eps_z_over_g2·G2 → eps_z` and `eps_x_over_g2·G2 → eps_x`.
  - Outputs: ⟨n⟩, parity, Re⟨a⟩, ⟨b⟩ (Re and Im), top-level populations, and Wigner frames at the requested times via `dq.wigner(ρ_a, xmax=4, ymax=4, npixels≤81)` on the memory partial trace.
  - **Use `save_states=False`** and a `save_extra` callback for derived quantities. Save memory states only at `wigner_times`, by running a second short evolution or by saving at those times.
- **Live caps:**
  - One-mode: N ≤ 40, `t_end` ≤ 5 µs, `n_t` ≤ 400.
  - **Two-mode live is fixed at Na = 16, Nb = 5.** Accept Na ≤ 20 and Nb ≤ 6, fix `n_t` at 201, use rtol 1e-6 / atol 1e-8, and cap `t_end` at 3 µs.
  - Anything bigger returns `413`.
  - Timeouts: one-mode 8 s, two-mode 15 s. Run in a `concurrent.futures.ProcessPoolExecutor(max_workers=2)` and wrap calls in `asyncio.wait_for`.
- **`cache.py`:**
  - `params_hash(req)` is the sha256 of canonical JSON (sorted keys, floats rounded to 12 significant digits).
  - An in-memory LRU of 256 entries.
  - A **hook** `store_run(row: dict)` that does nothing unless P5 registers a sink via `cache.register_sink(fn)`.
  - Responses include `meta.cached`, `meta.wall_ms`, `meta.params_hash` and `meta.engine="dynamiqs 0.3.7"`.
- **`expr.py`** (CONTRACT §4):
  - `validate(tree)`: allowlist symbols and params, depth ≤ 8, ≤ 64 nodes, integer `pow` 0–4, `sqrt` only on param or num.
  - `compile_tree(tree, modes, N|Na,Nb) -> QArray`, built from `dq.destroy` operators.
  - `is_hermitian(H)` to 1e-9.
  - `to_python(tree) -> str`, the dynamiqs snippet. It must match the fixtures **exactly**, because P3's TS printer is tested against the same files.
  - Params resolve from `src.config` (G2, EPS_D, KAPPA_B, KAPPA_A, KAPPA_2, ALPHA), or from request `params` in rad/µs.
- **Warm-up.** At startup, run tiny warm-up sims at the live shapes (one-mode N = 30; two-mode 16×5, `n_t` = 201) so the JIT compiles. Enable the persistent cache with `jax.config.update("jax_compilation_cache_dir", "/cache/jax")`, or an env path. Log warm-up times.
- **CORS:** allow `ALLOWED_ORIGINS` (comma-separated) plus the origin `null` (the `file://` single-file build).
- **Rate limits:** slowapi, 30/min/IP for sims.

## 5. Tests to write FIRST (TDD; `server/tests/`, external services never called)
- `test_health_flags`: with no keys, all features are false. Setting `GEMINI_API_KEY` in the env makes `gemini` true.
- `test_caps`:
  - two-mode Na = 32 returns 413 `too_large`;
  - one-mode N = 80 returns 413;
  - `t_end_us` = 10 returns 413.
- `test_timeout`: monkeypatch `run_two_mode` to sleep 20 s, then expect 504 `sim_timeout` within about 16 s.
- `test_cache_hit`: the same request twice gives `meta.cached` false then true, with an identical body otherwise.
- `test_one_mode_physics` (marked slow is fine): vacuum → cat at N = 30, `t_end` 2 µs, nominal κ₂ with κ_a on. The final ⟨n⟩ is within 1% of 4.404. This matches committed `results/task_1_0.json` c.final_n[1] = 4.403969.
- `test_two_mode_live_shape`: 16×5, 2 µs runs. ⟨n_a⟩ peaks above 4.41 (it overshoots), and every array has length 201.
- `test_expr_allowlist`: an unknown symbol, depth 9, a non-integer pow, a non-Hermitian H (`a` alone) and `sqrt` of an operator all return 422 `invalid_expr`.
- `test_expr_to_python_fixtures`: every `server/tests/fixtures/expr/*.json` has `{"tree":…, "python":"…"}`, and `to_python(tree) == python` exactly.
  - Create the fixtures: `h_2ph.json` (g2(a²b† + a†²b) − ε_d(b + b†)), `jump_buffer.json` (√κ_b·b), `jump_memory.json` (√κ_a·a), `kerr.json` (−K·a†²a²), and the invalid cases.
- `test_expr_matches_model`: compile `h_2ph` at 8×3. It equals the H from `src.model.two_mode(8, 3, …)` to 1e-12.
- `test_cors_null_origin`: a request with `Origin: null` gets `Access-Control-Allow-Origin: null`.
- `test_router_autoinclude`: a temporary package with `routes.py` is mounted.

## 6. Method
1. Run `git switch -c prod/p0-server`. Create the status file from `docs/plan/status/_TEMPLATE.md`. Write the tests and see them fail.
2. Write `settings.py` (pydantic-settings from env, with defaults per CONTRACT §2), `schemas.py` (pydantic v2 request and response models mirroring CONTRACT §3), `limits.py` and `cache.py`.
3. Write `sim.py` and `expr.py`, then `main.py` with auto-include, CORS, slowapi, the startup warm-up and error handlers.
4. **Push the skeleton early.** Commit and push `prod/p0-server` once `/api/health` and the routers' auto-include work, and tell the integrator, because P4, P5 and P6 branch from it.
5. **`precompute.py`** (run locally; it takes minutes) writes `server/precomputed/presets/*.json` in the same response shape as the endpoints:
   - **L1–L4:** the one-mode defaults from LEVELS.md, plus 3 slider positions each.
   - **L6:** two-mode builds at 16×5 and 2 µs: `correct.json` (H_2ph + √κ_b·b + √κ_a·a), `missing_kappa_b.json`, `eps_z_drive_wrong.json` (ε(a + a†) instead of the buffer drive: it shows the memory never forms a cat), and `a_bd2_wrong.json` (a·b†²). Also a 32×12 "converged" reference for the overshoot (peak about 6.89) and the 24×6 starter (peak about 6.11). The latter two may be copied from committed intro results where they exist.
   - **L7:** ⟨b⟩±(t) for ε_Z/g₂ ∈ {0.05, 0.1, 0.2, 0.5, 1, 2, 3}. Prefer the physics lane l4a's arrays (`results/arrays/t2_3.ring_freq.td.two_mode.a2.10.npz`) when merged; otherwise compute at 16×5 and label it.
   - **Wigner fixtures** `server/tests/fixtures/wigner/{vacuum,coherent2,catplus2}.json`: N = 30, `dq.wigner` on an 81×81 grid with xmax = ymax = 4. P1 uses them to match the dynamiqs convention, where vacuum is W(0,0) = 2/π.
   - **linresp fixtures** `server/tests/fixtures/linresp/{square,cosramp,clear}.json` with keys `edges_us`, `eps`, `t_us`, `delta_b_re`, `delta_b_im` and `snr`. Use root `src/linresp.py` if merged; otherwise a local reference 2×2 matrix-exponential implementation marked `"reference_impl": true`.
6. **Dockerfile:**
   - Base `python:3.12-slim`. Install root `requirements.txt` + `server/requirements.txt`.
   - Copy `src/`, `server/` and `results/records/` (needed by the tutor's `get_record`).
   - Run as a non-root user, with `HEALTHCHECK` on `/api/health`.
   - `CMD uvicorn server.app.main:app --host 0.0.0.0 --port 8000 --workers 1`. One worker, because the process pool handles parallelism.
7. **`deploy/`:**
   - `docker-compose.yml` has services `api` (build `..` with `server/Dockerfile`, env_file `/opt/academy/.env`, volume for the JAX cache), `chain` (build `../chain`, P6), and `caddy` (`caddy:2`, ports 80 and 443).
   - `Caddyfile`: `{$API_HOST} { reverse_proxy /api/chain/* chain:8100  reverse_proxy /api/* api:8000 }`, where `API_HOST=<ip-with-dashes>.sslip.io` (automatic TLS).
   - `README.md` is the runbook, using HUMAN.md §2 commands: smoke curl, logs, and how to warm the server after a restart.
8. Record measured latencies in the status file: warm one-mode N = 30 at 2 µs; warm two-mode 16×5 at 2 µs; cold start.

## 7. Outputs
- The running service locally (`uvicorn server.app.main:app --port 8000` from the repo root).
- Presets in `server/precomputed/presets/`. **P2 copies them** into `site/src/academy/presets/`.
- Expr and linresp fixtures for P3 and P1.
- The deploy bundle.

## 8. Acceptance gates
- [ ] All `server/tests` fast tests pass, and the slow ones pass or are documented.
- [ ] The skeleton is pushed by about 12:45 AM, and P4, P5 and P6 are notified via the status file.
- [ ] Warm latencies are recorded. Two-mode 16×5 at 2 µs comes in under 15 s (target under 5 s).
- [ ] Presets exist for L1–L4, L6 (4 builds + 2 references) and L7 (7 drive values). Fixtures exist.
- [ ] `docker build -f server/Dockerfile .` succeeds. If Docker isn't available on Windows, say so; P7 builds on the VM.
- [ ] No secrets in git; only `.env.example` is committed.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c prod/p0-server
& $env:DUQ_PY -m pip install fastapi "uvicorn[standard]" "pydantic>=2" pydantic-settings httpx slowapi   # into the shared venv (record in status)
& $env:DUQ_PY -m pytest server/tests -q -m "not slow"
& $env:DUQ_PY -m uvicorn server.app.main:app --port 8000
& $env:DUQ_PY -m server.precompute --levels all
curl.exe -s http://localhost:8000/api/health
```

## 10. Out of scope / do not
- Do not implement the tutor, memory, voice, data or chain logic (P4, P5, P6).
- Do not edit `src/**` (physics files).
- **Never execute user-provided code.** Compile ExprTrees only.
- No GPU code, and no large live two-mode shapes.

## 11. If blocked
- **`l0-core` not merged** (no `eps_x`/`coherent2` in `src/model.py`): add a local adapter `server/app/sim.py::_two_mode_compat` that builds the extra drive terms itself, and log a `DECISION NEEDED` to remove it after the merge.
- **The JAX persistent cache fails on CPU:** skip it and rely on the startup warm-up. Note it.
- **Live latency over 15 s on the VM:** make L6 presets-only, and keep the endpoint for one-mode plus the `/expr` one-mode path.
- **Cut line:** the SSE stream endpoint is a stretch; skip it.

## 12. Hand-off
At DONE, the status file has: endpoints and tests, measured latencies, the preset inventory, the fixture list, docker build results, and the needed env vars.

**Questions Harshit should be able to answer:**
1. Why does the server build physics only through `src/model.py`, and how does that keep the Academy consistent with the verified research?
2. Why can't two-mode runs be live, and what does the site show instead?
3. Why is it safe to let learners send Hamiltonians to the server?
