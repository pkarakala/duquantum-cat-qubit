# Brief `p5-data`: Tiger Data runs, the live community aggregate, a verified leaderboard and progress

> **Paste into a new Cursor agent (worktree mode, base `standard-track`):** "You are product lane `p5-data`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P5-data.md`, then execute the brief exactly. Keep `docs/product/status/p5-data.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p5-data` | `prod/p5-data` (from `standard-track`) | The P0 skeleton merged: router auto-include of `server/app/<pkg>/routes.py`, `cache.register_sink` / `cache.store_run`, the empty `server/app/data/__init__.py`. `src/linresp.py` (l4a) is optional and import-guarded. Harshit's `TIGER_DATABASE_URL` is needed only for the live check. | standard (Sonnet-class) | 2 h | about 1:00 AM → **3:00 AM Sun** (before P-G2 at 4:30 AM: "Tiger logs runs") |

## 1. Goal and why
Tiger Data is a sponsor prize, and its "best use" (SPONSORS.md) is real time series plus a live dashboard backed by a **continuous aggregate**. You build the data layer on Tiger Cloud (Postgres with TimescaleDB):
- **`sim_runs`:** every learner experiment (server sims through P0's hook, browser sims through `POST /api/runs`) becomes a row in this **hypertable**.
- **`alpha_choices_5m`:** a continuous aggregate that feeds the live "what cat size is the room choosing" chart.
- **Leaderboard:** for the L8 readout-pulse challenge. **The server recomputes the score**, so it never trusts the client.
- **Progress:** per pseudonymous learner.

Everything degrades gracefully:
- With no DB URL, your endpoints return 503 `feature_disabled` and the site hides the community chart.
- A slow or dead DB never slows a sim. Run logging happens in the background with a 2 s statement timeout.
- No PII is ever stored.

## 2. Read first
- `docs/product/CONTRACT.md`:
  - §0: pseudonymous learners, secrets.
  - §1: your ownership.
  - §2: `TIGER_DATABASE_URL`.
  - §3: the P5 rows and the error shape `{"error":{"code","message"}}`.
  - **§6: the schema, verbatim.** Don't use pgai (it was archived); there is a `create_hypertable` fallback.
  - §5: linresp parity fixtures.
- `docs/product/briefs/P0-server.md` §4: the router auto-include, `cache.register_sink(fn)` / `store_run(row)`, slowapi in `server/app/limits.py`, settings. `docs/product/LEVELS.md` L8 (the challenge) and the misconception IDs. `docs/product/SPONSORS.md` (Tiger Data).
- Physics `docs/plan/CONTRACT.md` §9 (the `src/linresp.py` API: `response(eps_t, t, g2, kappa_b, alpha, well=+1) -> (da_t, b_t)`, zero-order hold, x(t₀) = 0). `docs/plan/RESEARCH.md` §7 (SNR = κ_b∫|Δ⟨b⟩|²dt, with Δb = b(+α) − b(−α) = 2b₊). `src/config.py`.
- TimescaleDB docs:
  - `CREATE TABLE … WITH (tsdb.hypertable, tsdb.partition_column=…)`;
  - `add_continuous_aggregate_policy`;
  - `refresh_continuous_aggregate`;
  - `timescaledb.materialized_only` (real-time aggregates).

## 3. Allowlist (touch nothing else)
- **`server/app/data/**`:** `__init__.py` (P0's empty placeholder, now yours), `db.py`, `fake.py`, `routes.py`, `challenge.py`, `migrate.py`, `smoke.py`, `recompute.py`.
- **`server/sql/**`:** `001_init.sql` and `001a_sim_runs_fallback.sql`.
- **Tests:** `server/tests/test_data_sql.py`, `test_data_api.py`, `test_data_leaderboard.py`.
- **Status:** `docs/product/status/p5-data.md`.
- **Never edit:** `server/app/main.py`, `cache.py`, `limits.py`, `server/requirements.txt` or `server/tests/conftest.py` (all P0's); `src/**`; `site/**`; CONTRACT.
  - If `psycopg[binary,pool]` is missing from `server/requirements.txt`, write it in status for P0/P7, and `pip install` it locally into the shared venv only (§9).

## 4. Interfaces you implement / rely on

### Endpoints
All are in `routes.py` as `router = APIRouter()` with absolute `/api/...` paths. P0 auto-includes them.

**`POST /api/runs`**
- Body: a run row with the §6 `sim_runs` columns. Pydantic, `extra="forbid"`; any extra field (`email`, `name`, …) gets 422.
- Field rules:
  - `learner_id`: UUID v4 or null.
  - `level_id`: `L1`–`L8`, `sandbox` or null.
  - `engine`: `"dynamiqs 0.3.7"` or `"ts-rk4"`.
  - `model`: one of `one_mode | two_mode | expr_one | expr_two | ts_one_mode`.
  - `params`: JSON of at most 4 KB.
  - `alpha` and `eps_z_over_g2`: in [0, 3] or null; all floats finite.
  - A client `ts` is **ignored**: the server time is the time axis.
- Response `{ok: true}`. Rate limit 60/minute/IP using P0's slowapi limiter from `server.app.limits` (check its exported name; never create a second limiter).

**`store_run(row: dict) -> None`**
- This is the in-process sink. At import time `routes.py` calls `cache.register_sink(store_run)`; if P0 named it differently, use `getattr` and note it.
- It is lenient: it keeps only the §6 columns, and skips (with a log) rows that lack the NOT NULL fields `engine`, `model`, `params` and `params_hash`.
- It never raises, and it is a no-op when the feature is disabled.

**`GET /api/community/alpha?minutes=60`** → `{buckets:[{t, alpha_bin, count}]}`
- `minutes` must be in [5, 1440]; otherwise 422.
- SQL: `SELECT t, alpha_bin, count FROM alpha_choices_5m WHERE t >= now() - make_interval(mins => %s) AND alpha_bin IS NOT NULL ORDER BY t, alpha_bin`.
- *Additive:* `bin_edges = [0, 0.25, …, 3.0]`. `width_bucket(alpha, 0, 3, 12)` gives bin k = [0.25(k−1), 0.25k). Bin 13 is α ≥ 3; L1's slider reaches exactly 3.0, so say so in status for P2.

**`GET /api/leaderboard?challenge=readout_pulse`** → `{rows:[{alias, score, payload_hash, ts}]}`
- The top 20 by score, best row per learner (`DISTINCT ON (learner_id)`), excluding rejected rows.
- *Additive:* `verified` on each row.
- **Never return `learner_id`.**

**`POST /api/leaderboard`** `{challenge, learner_id, alias, score, payload}` → `{rank}`
- *Additive:* `verified` and `server_score`.
- Rate limit 10/minute/IP.
- `rank` = 1 + the number of non-rejected rows in this challenge with a higher score.

**Progress**
- `POST /api/progress` `{learner_id, level_id, passed, prediction_correct, attempts}` upserts, then returns `{levels:[{level_id, passed, prediction_correct, attempts, ts}]}`.
- `GET /api/progress?learner_id=` returns the same shape, sorted L1 → L8.
- Upsert rule: `passed` is monotone (`progress.passed OR EXCLUDED.passed`), and the latest `prediction_correct` and `attempts` win.

**Shared rules**
- Every `ts` is serialized as ISO-8601 UTC with `Z`.
- The alias is optional, stripped, and must match `^[A-Za-z0-9 _.\-]{1,24}$`; the default is `"anon"`. A small profanity blocklist that maps to `"anon"` is optional.
- With no `TIGER_DATABASE_URL`, every endpoint above returns **503 `feature_disabled`**. A DB error or timeout returns 503 `db_unavailable`.
- `/api/health`'s `tiger` flag is P0's (derived from env).

### Store layer (`db.py`, `fake.py`)
- `class Store(Protocol)` with: `insert_run`, `community_alpha(minutes)`, `insert_leaderboard`, `top_leaderboard(challenge, limit)`, `rank(challenge, score)`, `upsert_progress`, `get_progress(learner_id)`, `log_tutor_event(row)`.
- `log_tutor_event` is an optional helper for P4's `tutor_events` table, with the same never-raise behaviour.
- `PgStore(url)` uses `psycopg_pool.ConnectionPool(url, min_size=1, max_size=4, open=False, timeout=3, kwargs={"autocommit": True, "connect_timeout": 5, "options": "-c statement_timeout=2000"})`.
  - The pool opens **lazily, on first use**. A dead DB must never crash startup.
- `get_store()` is a FastAPI dependency. It reads env at call time and returns the singleton `PgStore`, or `None` when disabled.
- `FakeStore` (in `fake.py`) implements the same protocol in memory, including a Python aggregate: a 5-min floor and `width_bucket` semantics. Tests use `app.dependency_overrides[get_store] = lambda: fake`.

### SQL (`server/sql/001_init.sql`)
First the **CONTRACT §6 DDL, copied character for character**. Then these additions:
```sql
SELECT add_continuous_aggregate_policy('alpha_choices_5m',
  start_offset => INTERVAL '2 hours', end_offset => INTERVAL '1 minute', schedule_interval => INTERVAL '1 minute');
ALTER MATERIALIZED VIEW alpha_choices_5m SET (timescaledb.materialized_only = false);  -- real-time: include rows newer than the last refresh
CREATE INDEX IF NOT EXISTS leaderboard_challenge_score ON leaderboard (challenge, score DESC);
CREATE INDEX IF NOT EXISTS sim_runs_learner_ts ON sim_runs (learner_id, ts DESC);
```
- `001a_sim_runs_fallback.sql` holds the same `sim_runs` CREATE TABLE without the `WITH (...)` clause, followed by `SELECT create_hypertable('sim_runs', 'ts');`. It runs only if the `tsdb.hypertable` form fails.

### Migration runner (`python -m server.app.data.migrate --env-file server/.env`)
- It **must use autocommit**: `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)` (which materializes on creation) and `refresh_continuous_aggregate` cannot run inside a transaction block.
- It runs `CREATE EXTENSION IF NOT EXISTS timescaledb` first, and prints `extversion`.
- It splits statements on `;` at a line end (the DDL contains no inner `;`).
- It records applied files in `duq_migrations(name text PRIMARY KEY, applied_at timestamptz DEFAULT now())`, so a second run is a no-op.
- If the `sim_runs` statement fails with a syntax or feature error, it runs the fallback and prints `FALLBACK create_hypertable used`. Record that in status.
- `--env-file` parses `KEY=VALUE` lines. **Never print the URL.**

### Challenge scoring (`challenge.py`)
P2's L8 must mirror these constants. Post them in status.

| Constant | Value |
|---|---|
| `CHALLENGE` | `"readout_pulse"` |
| `T_US` | 1.0 |
| `N_BINS` | 20 (default; accept 1–50) |
| `MAX_AMP_OVER_G2` | 3.0 |
| `SQUARE_REF_OVER_G2` | 0.5 |
| `ENERGY_BUDGET` | `0.5**2 * 1.0 = 0.25` (units of g₂²·µs) |
| `SAMPLES_PER_BIN` | 10 |

**Payload:** `{"T_us": 1.0, "eps_over_g2": [x_0 … x_{n−1}]}`.
- `n` must be in [1, 50], and each `x` finite with `|x| ≤ 3`; otherwise 422 `bad_request`.
- `T_us` must be 1.0, or 422.
- Energy `Σx²·(T/n)` must not exceed `0.25·(1 + 1e-9)`, or 422 `over_budget`.

**Score (SNR):**
- Grid: `t = linspace(0, T, 10n + 1)` and `eps_t[k] = x[min(k // 10, n − 1)]·C.G2`. The rule is index-based, with no float comparison.
- `_, b = linresp.response(eps_t, t, C.G2, C.KAPPA_B, C.ALPHA, well=+1)`; `Δb = 2b`.
- `snr = C.KAPPA_B·trapz(|Δb|², t)`.
- Also expose `snr_for(eps_rad, edges_us, t_us)`, which maps each sample to its bin with `searchsorted(edges, t + 1e-12, "right") − 1` clipped to [0, n−1]. It is used for the fixture parity test.

**Recompute policy** (CONTRACT: "never trust the client"):
- **`src.linresp` imports:** compute `server_score`.
  - If `|score − server_score| > 1e-6·max(1, |server_score|)`, return 422 `score_mismatch` and store nothing.
  - Otherwise store `score = server_score` with `verified = true`.
- **`src.linresp` does not import yet** (l4a not merged):
  - Store the client score with `verified = false` and `server_score = null`. The site shows it as "unverified" (PLAN cut #7).
  - Later, `python -m server.app.data.recompute` re-scores every unverified row. Matches become `verified = true`; mismatches are marked `rejected = true` and drop out of GET.
- The leaderboard table has no `verified` column (CONTRACT §6 is fixed). Store `{"T_us","eps_over_g2","verified","rejected","client_score","source"}` in `payload` jsonb.
- `payload_hash` = sha256 of `json.dumps({"T_us","eps_over_g2"}, sort_keys=True, separators=(",",":"))`.

**Prototype anchors** (numpy, from this brief's author; ZOH linresp at nominal parameters, 20 bins, 1 µs):

| Pulse | Definition | SNR | Energy (g₂²·µs) |
|---|---|---|---|
| square | 0.5 g₂ | **0.9541** | 0.25 |
| cos ramp | `0.5·½(1 − cos(2π(k+½)/20))` | 0.3695 | 0.0938 |
| CLEAR | `[1.0]×2 + [0.5]×14 + [−0.5]×2 + [0]×2` | n/a | **0.30, so `over_budget`** |
| SVD-optimal | at energy 0.25 | ≈ 4.06 (≈ 4.26× the square) | 0.25 |

## 5. Tests to write FIRST (TDD; fake DB, no network)
P0 owns `conftest.py`, so define your fixtures in your own test files: a `client` with `get_store` overridden to `FakeStore`, and env monkeypatched. Commit the tests failing ("tests first").
1. `test_sql_contract` (in `test_data_sql.py`):
   - Extract the §6 SQL block from `docs/product/CONTRACT.md`, split it into statements and normalize whitespace. Every statement must appear in `001_init.sql`.
   - `001_init.sql` also contains `add_continuous_aggregate_policy('alpha_choices_5m'` with `schedule_interval => INTERVAL '1 minute'`, and `materialized_only = false`.
   - The fallback file contains `create_hypertable('sim_runs', 'ts')`.
   - Neither file mentions `pgai` or `CREATE EXTENSION ai`.
2. `test_sql_split`: the splitter yields exactly 9 statements for `001_init.sql`, and the continuous-aggregate statement is flagged as needing autocommit. Optionally (`pytest.importorskip("sqlglot")`), the three plain `CREATE TABLE` statements parse with dialect `postgres`.
3. `test_disabled` (`test_data_api.py`):
   - With `TIGER_DATABASE_URL` unset, every endpoint returns 503 `feature_disabled` with the error shape.
   - `store_run({...})` returns `None` and raises nothing.
4. `test_runs_validation`:
   - A valid browser row (`engine "ts-rk4"`, `model "ts_one_mode"`) is stored with a server `ts`, and a client `ts` is ignored.
   - A bad UUID, `alpha=3.5`, `params` over 4 KB, or an extra `email` field each return 422.
5. `test_store_run_hook`:
   - Importing `server.app.data.routes` registers the sink, so `cache.store_run(row)` reaches `FakeStore`.
   - A `FakeStore` whose insert raises causes no exception.
   - A row missing `params_hash` is skipped.
6. `test_community_shape`:
   - With fake rows at α = 2.1 (×3) and α = 1.0 (×1) in the last 5 min, `buckets` holds `alpha_bin` 9 (count 3) and 5 (count 1).
   - `t` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$`.
   - `minutes=0` and `minutes=2000` return 422.
7. `test_leaderboard_square` (`test_data_leaderboard.py`; skip if `src.linresp` is absent):
   - The square payload with the client score equal to the server score gives 200, `rank == 1` and `verified: true`.
   - GET rows contain no `learner_id`.
8. `test_leaderboard_tampered`: the same payload with the score ×1.5 gives 422 `score_mismatch`, and the fake store stays empty.
9. `test_leaderboard_limits`: each of these returns 422 with the code in brackets:
   - 51 bins; an amplitude of 3.01; `T_us = 2` [`bad_request`];
   - the CLEAR payload [`over_budget`];
   - a 25-character alias.
10. `test_score_anchors`:
    - The square SNR is 0.9541 and the cos ramp 0.3695 (rtol 1e-3).
    - With `src.linresp` present: the SVD-optimal pulse beats 4× the square at equal energy, and `snr_for` reproduces `server/tests/fixtures/linresp/*.json` `snr` to 1e-9. Convert the fixture's `eps` and `edges_us`; skip if the fixtures are absent.
    - With `src.linresp` hidden (monkeypatch the import): the row is stored with `verified: false`, `server_score: null`, and GET still lists it.
11. `test_recompute`: after `src.linresp` becomes importable, `recompute.run(store)` flips matching rows to `verified` and marks a tampered row `rejected`.
12. `test_progress_upsert`:
    - POST with `passed=true`, then `passed=false`: the stored `passed` stays true, and `attempts` and `prediction_correct` take the latest values.
    - GET is sorted.
    - `level_id "L9"` returns 422.

## 6. Method, step by step
1. **Set up.** Create the branch and the status file ("started"). Check that the P0 skeleton is on `standard-track`, i.e. that `server/app/main.py` auto-includes routers and that `cache.register_sink` exists.
   - If it isn't merged yet, develop against those documented names anyway. Your files never overlap with P0's.
2. **Tests.** Write the §5 tests and commit "tests first".
3. **SQL and runner.** Write `001_init.sql`, the fallback file and `migrate.py`. Tests 1–2 go green.
4. **Data layer.** `db.py`, `fake.py` and `routes.py` for runs, community and progress, plus the disabled path. Tests 3–6 and 12 go green.
5. **Leaderboard.** `challenge.py`, the leaderboard routes and `recompute.py`. Tests 7–11 go green.
6. **Full suite and live server.**
   - Run `& $env:DUQ_PY -m pytest server/tests -q` to prove you broke nothing of P0's.
   - Start uvicorn with no DB URL and curl each endpoint; you should see 503 `feature_disabled`.
7. **Live check** (only once Harshit has put `TIGER_DATABASE_URL` in `server/.env`; never print it or commit it):
   1. `migrate` (record the TimescaleDB version, and whether the fallback was used).
   2. `smoke --n 10`: it inserts 10 synthetic runs directly through the store (`level_id "SMOKE"`, `engine "ts-rk4"`, α spread over 0.5–2.5), runs `CALL refresh_continuous_aggregate('alpha_choices_5m', NULL, NULL)` in autocommit, then prints the aggregate rows and the `/api/community/alpha` response.
   3. Paste both (no URL) into status.
   4. Then run uvicorn with the env file, run one sim through P0's endpoint, and confirm a new `sim_runs` row exists.
   - The 10 smoke rows stay; they age out of the 60-min window. Don't delete data.

## 7. Outputs
- **Code:** `server/sql/001_init.sql`, `server/sql/001a_sim_runs_fallback.sql`, and `server/app/data/{__init__,db,fake,routes,challenge,migrate,smoke,recompute}.py`.
- **Tests:** the three `test_data_*.py` files.
- **Status:** the live-check transcript; the challenge constants for P2; the run-row contract for P2 (the browser posts TS runs to `/api/runs` with `engine "ts-rk4"`, `model "ts_one_mode"`, and optional `learner_id`/`level_id`); `log_tutor_event` for P4; dependency notes for P0/P7.

## 8. Acceptance gates
1. **Tests and allowlist.**
   - `& $env:DUQ_PY -m pytest server/tests -q` is all green, and your tests take under 10 s with no network.
   - `git status --porcelain -- server/app/main.py server/app/cache.py server/requirements.txt src site` prints nothing.
2. **SQL.**
   - `001_init.sql` contains the CONTRACT §6 DDL verbatim, plus the refresh policy (1-minute schedule) and real-time mode.
   - There is no pgai.
3. **Degradation.** With no DB URL, every P5 endpoint returns 503 `feature_disabled` and sims are unaffected (P0's sim tests still pass).
4. **Leaderboard trust.**
   - The server recomputes (or marks rows unverified when `src.linresp` is absent).
   - A tampered score is rejected.
   - Budget, bin and amplitude limits are enforced.
   - `learner_id` is never returned.
5. **Live** (once the URL exists): migrate succeeded, 10 smoke rows are in `sim_runs`, the aggregate returns non-empty buckets, and one real sim run was logged through P0's hook. If the URL never arrives, write "LIVE CHECK PENDING" in status.
6. **No secrets:** `git grep -nE "postgres(ql)?://[^ ]*@" -- server` prints nothing.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c prod/p5-data standard-track
Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p5-data.md
& $env:DUQ_PY -c "import fastapi, psycopg, psycopg_pool; print(psycopg.__version__)"   # if missing: pip install "psycopg[binary,pool]" (note it in status)
& $env:DUQ_PY -m pytest server/tests/test_data_sql.py server/tests/test_data_api.py server/tests/test_data_leaderboard.py -q
& $env:DUQ_PY -m pytest server/tests -q
& $env:DUQ_PY -m uvicorn server.app.main:app --port 8000                                # no DB: expect 503 feature_disabled
Invoke-RestMethod "http://localhost:8000/api/community/alpha?minutes=60"
& $env:DUQ_PY -m server.app.data.migrate --env-file server/.env
& $env:DUQ_PY -m server.app.data.smoke --env-file server/.env --n 10
& $env:DUQ_PY -m uvicorn server.app.main:app --port 8000 --env-file server/.env
& $env:DUQ_PY -m server.app.data.recompute --env-file server/.env                      # after l4a's src/linresp.py merges
git add <explicit paths>; git commit -m "[p5-data] <what>"                              # never `git add .`, never push or merge
```

## 10. Out of scope / do not
- **Don't use pgai** (archived May 2026). No vector search, no Tiger MCP and no extra extensions.
- **No PII:** no emails, names, IP addresses or user agents in any table. Learners are UUID v4 plus an optional alias.
- **Other lanes' files:** don't edit P0's files (`main.py`, `cache.py`, `limits.py`, `requirements.txt`, `conftest.py`) or the site's chart UI (P2/P7 own it).
- **Data deletion:** don't delete or `TRUNCATE` production data, and don't drop tables on Tiger. A schema change is a new `server/sql/00N_*.sql` file plus a DECISION NEEDED.
- **Request path:** never block a sim response on the DB, and never trust a client score.

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
Wording (in status; then carry on with whatever is unblocked):
```
DECISION NEEDED (p5-data, HH:MM): <one line>. Measured: <error text, versions>. Options: (a) ... (b) ...
My default if no answer by HH:MM+30: (a).
```
- **The P0 skeleton isn't merged.**
  - Build against the documented hook names, and test `routes.py` by mounting `router` on a bare `FastAPI()` inside your tests.
  - If P0's hook has another name, use `getattr` and note it.
- **`tsdb.hypertable` syntax fails.** Use the fallback (automatic in `migrate`) and record it.
- **The continuous aggregate fails.**
  - Check the TimescaleDB version, and that the statement ran in autocommit.
  - Fallback: a plain `GROUP BY time_bucket` query in `community_alpha`, with DECISION NEEDED, because the sponsor story needs the continuous aggregate.
- **`src.linresp` isn't merged by 3:00 AM.** Ship the `verified=false` path, and put `recompute` in "Jobs to queue" for the integrator after l4a merges.
- **No Tiger URL by 3:00 AM.** Mark "LIVE CHECK PENDING"; P7 runs `migrate` and `smoke` on the VM.
- **L8 constants conflict with P2's L8 spec.** P2 owns the level. Adopt P2's values in `challenge.py`, re-derive the anchors and note it.
- **Cut line**, following PLAN §3:
  1. the community endpoint's *chart* (keep the SQL aggregate, the endpoint and run logging);
  2. `recompute.py`;
  3. server-side recompute (keep "unverified" local scores).

  **Never cut:** the schema with the hypertable and continuous aggregate, `store_run` and `POST /api/runs`, the progress endpoints, the disabled-feature path, and the leaderboard storage.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer: QUESTIONS ONLY)
At DONE, `docs/product/status/p5-data.md` contains:
- **Basics:** state, branch, last commit; the test output; the curl transcript of the disabled path.
- **Live check:** the TimescaleDB version, whether the fallback was used, the smoke aggregate rows and the logged real sim row (or "LIVE CHECK PENDING").
- **Interfaces:** the challenge constants and anchors for P2; the browser run-row contract; `log_tutor_event` for P4; dependency notes (`psycopg[binary,pool]`) for P0/P7; the `cache.register_sink` name actually used.
- **Additive fields:** `verified`, `server_score`, `bin_edges`.
- **Open items:** any open DECISION NEEDED, and any job to queue (`recompute` after l4a merges).

Explain-back questions (Harshit answers them himself; don't write answers):
1. Why is `sim_runs` a hypertable and `alpha_choices_5m` a continuous aggregate, rather than running a plain `GROUP BY` on every chart refresh? With a 1-minute schedule, a 2-hour start offset and `materialized_only = false`, how stale can the live chart be?
2. How does the leaderboard stop someone from posting a fake score? What exactly does the server recompute (signal, grid, budget)? Why is a 0.5 g₂ square pulse a sensible reference, and what happens to rows submitted before `src/linresp.py` merged?
3. What do we store about a learner, and why is that not PII? What does each P5 endpoint, and the sim API, do when Tiger is unreachable?
