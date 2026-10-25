# Status: lane `p5-data`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p5-data` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | 2026-10-25 00:34 |
| Last update (EDT) | 2026-10-25 00:58 |
| Last commit | `6abadd1` `[p5-data] log experiments on a Timescale hypertable` (status file is the following commit) |

## Milestones
- [x] Read brief, CONTRACT, SPONSORS
- [x] Tests written (`test_sql_contract`, `test_sql_split`, `test_disabled`, `test_runs_validation`, `test_store_run_hook`, `test_community_shape`, `test_leaderboard_square`, `test_leaderboard_tampered`, `test_leaderboard_limits`, `test_score_anchors`, `test_recompute`, `test_progress_upsert`)
- [x] Implementation complete
- [x] Fast suite green (no network)
- [x] Live Tiger migrate + smoke done
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## Acceptance gates
| Gate | Result | Evidence |
|---|---|---|
| Tests and allowlist | pass, with two skips | `pytest server/tests -q` → `10 passed, 2 skipped` in 9.36 s. Skips are `test_leaderboard_square` and `test_leaderboard_tampered` because `src/linresp.py` is not on this branch. `git status --porcelain` on `server/app/main.py`, `cache.py`, `requirements.txt`, `src`, `site` is empty. |
| SQL | pass | `001_init.sql` starts with CONTRACT §6 verbatim, then the real-time `ALTER` and the two indexes. 9 statements. No pgai. |
| Degradation | pass | No `TIGER_DATABASE_URL`: every P5 route returns 503 `feature_disabled`. P0 sim tests are not on this branch. |
| Leaderboard trust | pass, linresp path verified out of band | Tamper, budget, bin, and amplitude checks are in the suite. `learner_id` is not returned. Server recompute runs when `src.linresp` imports; otherwise the row is unverified. Anchors reproduced against l4a's `linresp.py` (see below). |
| Live | pass | TimescaleDB 2.31.0. `tsdb.hypertable` succeeded (no `create_hypertable` fallback). 10 SMOKE rows, non-empty aggregate, one hook row. |
| No secrets | pass | `server/.env` is gitignored (`.gitignore:27`). `git grep -nE "postgres(ql)?://[^ ]*@" -- server` is empty. |

## Commands run (most recent first)
```text
.venv/bin/python -m pytest server/tests -q
10 passed, 2 skipped, 1 warning in 9.36s
SKIPPED test_leaderboard_square / test_leaderboard_tampered: No module named 'src.linresp'

# disabled server, port 8765, TIGER_DATABASE_URL unset
# (P0 server/app/main.py is not on this branch, so this mounted server.app.data.routes.build_app)
GET  /api/community/alpha?minutes=60                         503 {"error":{"code":"feature_disabled","message":"Tiger Data is not configured"}}
GET  /api/leaderboard?challenge=readout_pulse                503 {"error":{"code":"feature_disabled","message":"Tiger Data is not configured"}}
GET  /api/progress?learner_id=11111111-1111-4111-8111-111111111111  503 feature_disabled
POST /api/runs {}                                            503 feature_disabled
POST /api/leaderboard {}                                     503 feature_disabled
POST /api/progress {}                                        503 feature_disabled

.venv/bin/python -m server.app.data.migrate --env-file server/.env
timescaledb extversion=2.31.0
already exists, continuing
applied 001_init.sql

# second run
timescaledb extversion=2.31.0
001_init.sql already applied; no-op

.venv/bin/python -m server.app.data.smoke --env-file server/.env --n 10
inserted 10 sim_runs level_id=SMOKE engine=ts-cn alpha=0.5..2.5
refresh: CALL refresh_continuous_aggregate
CATALOG [{"hypertable_name": "sim_runs"}]
CATALOG [{"view_name": "alpha_choices_5m", "materialized_only": false}]
HTTP 200
{"buckets":[
  {"t":"2026-10-25T04:50:00Z","alpha_bin":3,"count":2},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":4,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":5,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":6,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":7,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":8,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":9,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":10,"count":1},
  {"t":"2026-10-25T04:50:00Z","alpha_bin":11,"count":1}
 ],"bin_edges":[0.0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.25,2.5,2.75,3.0]}

# store_run (the P0 sink), then SELECT
HOOK {"ts":"2026-10-25 04:54:17.505492+00:00","level_id":"L1","engine":"dynamiqs 0.3.7","model":"one_mode","alpha":2.1,"params":{"alpha":2.1,"source":"p5-hook"},"params_hash":"p5-hook"}
COUNTS [{"level_id":"L1","n":1},{"level_id":"SMOKE","n":10}]
```

## What is stored on Tiger (not deleted)
| Table | Rows written by this lane |
|---|---|
| `sim_runs` | 10 rows, `level_id=SMOKE`, `engine=ts-cn`, `model=ts_one_mode`, α from 0.5 to 2.5. 1 row, `level_id=L1`, `engine=dynamiqs 0.3.7`, `model=one_mode`, α=2.1, `params.source=p5-hook`. |
| `alpha_choices_5m` | Real-time continuous aggregate. Bucket `2026-10-25T04:50:00Z`, bins 3 (count 2) and 4–11 (count 1). |
| `progress`, `leaderboard`, `tutor_events` | Schema only. No learner rows. |
| `duq_migrations` | `001_init.sql` applied at 2026-10-25 04:53:05+00. |

Catalog after migrate: `sim_runs` is a hypertable (1 dimension). `alpha_choices_5m.materialized_only = false`. Refresh policy `policy_refresh_continuous_aggregate`, `schedule_interval 00:01:00`, `start_offset 02:00:00`, `end_offset 00:01:00`. Indexes `leaderboard_challenge_score`, `sim_runs_learner_ts`, plus Timescale's `sim_runs_ts_idx`.

`psycopg` 3.3.6 and `psycopg-pool` 3.3.0 were installed into the shared repo `.venv`. `server/requirements.txt` does not exist yet.

## Interfaces

### Challenge constants for P2
| Constant | Value |
|---|---|
| `CHALLENGE` | `readout_pulse` |
| `T_US` | 1.0 |
| `N_BINS` | 20 (accept 1–50) |
| `MAX_AMP_OVER_G2` | 3.0 |
| `SQUARE_REF_OVER_G2` | 0.5 |
| `ENERGY_BUDGET` | 0.25 g₂²·µs |
| `SAMPLES_PER_BIN` | 10 |

Anchors, checked by loading l4a-readout's `src/linresp.py` (not copied into this branch) and calling `server_score`:

| Pulse | SNR | Energy |
|---|---|---|
| square 0.5 g₂, 20 bins | 0.954082 (target 0.9541, rel 1.9e-5) | 0.25 |
| cos ramp `0.5·½(1−cos(2π(k+½)/20))` | 0.369547 (target 0.3695, rel 1.3e-4) | 0.09375 |
| SVD-optimal at energy 0.25 | 4.06047 (4.256× the square) | 0.25 |
| CLEAR `[1]×2+[0.5]×14+[−0.5]×2+[0]×2` | not scored | 0.30 → `over_budget` |

NumPy 2.5 has no `np.trapz`. The integral is `np.trapezoid`, which is the same trapezoid rule. The anchors above used that.

### Browser run row (P2 → `POST /api/runs`)
`engine` `"ts-cn"`, `model` `"ts_one_mode"`, `params` JSON ≤ 4 KB, `params_hash` required. Optional `learner_id` (UUID v4 or null) and `level_id` (`L1`–`L8`, `sandbox`, or null). Optional `alpha` and `eps_z_over_g2` in `[0, 3]`. A client `ts` is ignored. Extra fields such as `email` are 422. Response `{ok: true}`.

### Community bins for P2
`GET /api/community/alpha` returns `{buckets:[{t, alpha_bin, count}], bin_edges}`. `bin_edges = [0, 0.25, …, 3.0]`. `width_bucket(alpha, 0, 3, 12)` bin k is `[0.25(k−1), 0.25k)`. Raw bin 13 would be α ≥ 3, but the view uses `LEAST(..., 12)`, so a slider sitting on exactly 3.0 is counted in bin 12, not a 13th bucket.

### `log_tutor_event` for P4
`server.app.data.db.log_tutor_event(row)` never raises. It is a no-op when `TIGER_DATABASE_URL` is unset, and it drops the row on a database error. Columns: `ts`, `learner_id`, `level_id`, `kind`, `misconception_id`, `hint_level`, `tool_calls`, `guard_removed`.

### Sink name
`routes.py` calls `cache.register_sink(store_run)` when `server.app.cache.register_sink` exists. That module is not on this branch, so nothing was registered at import. `store_run` is the sink P0 should call from `cache.store_run`.

### Rate limits
`POST /api/runs` is `60/minute` and `POST /api/leaderboard` is `10/minute`, applied only if P0 exports `server.app.limits.limiter` (also tried `app_limiter`, `LIMITER`). This lane does not construct a second limiter. With P0 absent, the decorators are no-ops.

### Additive response fields
- Leaderboard GET rows include `verified`. `learner_id` is never returned.
- Leaderboard POST returns `{rank, verified, server_score}`.
- Community response includes `bin_edges`.
- CONTRACT §6 already has `leaderboard.verified`. The brief's recompute details (`verified`, `rejected`, `client_score`, `source`, plus `T_us` and `eps_over_g2`) are stored in `payload` jsonb as well. The column and the payload flag are written together.

## Deviations from the brief (and why)
- Base is `product-academy-build` (the requested worktree base), not `standard-track`. P0's skeleton is not in that tree.
- Disabled curl used `build_app()` on port 8765 because `server.app.main:app` does not exist here.
- The live "sim" row was inserted by calling `store_run` directly, which is the function the P0 hook invokes. There is no `/api/sim` on this branch.
- `np.trapezoid` replaces removed `np.trapz`. Anchors still match.
- First migrate logged `already exists, continuing` once, without naming the statement (the logger now includes the statement text). The catalog after that run has every required object, and the hypertable form was used. Fallback was not used.

## Jobs to queue
| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs |
|---|---|---|---|---|
| recompute unverified L8 rows after `src/linresp.py` merges | `.venv/bin/python -m server.app.data.recompute --env-file server/.env` | < 1 | < 1 min | flips `verified` / `rejected` on `leaderboard` |

## DECISION NEEDED
None open. The continuous aggregate exists and is what `/api/community/alpha` reads. No GROUP BY fallback was used.

## Explain-back for Harshit (questions only)
1. Why is `sim_runs` a hypertable and `alpha_choices_5m` a continuous aggregate, rather than running a plain `GROUP BY` on every chart refresh? With a 1-minute schedule, a 2-hour start offset and `materialized_only = false`, how stale can the live chart be?
2. How does the leaderboard stop someone from posting a fake score? What exactly does the server recompute (signal, grid, budget)? Why is a 0.5 g₂ square pulse a sensible reference, and what happens to rows submitted before `src/linresp.py` merged?
3. What do we store about a learner, and why is that not PII? What does each P5 endpoint, and the sim API, do when Tiger is unreachable?

## Notes for Claude's later review
- Do not loosen the anchor tolerances. The square and cosine numbers matched l4a's zero-order-hold `response` to well inside 1e-3.
- `001a_sim_runs_fallback.sql` is not its own migration. `migrate` runs it only if the `tsdb.hypertable` statement fails with a syntax or feature error.
- Pool is constructed with `open=False` and opened on first use with `wait=False`. `wait=True` closes the pool on timeout, and a closed psycopg pool cannot be reopened.
- SMOKE rows and the one L1 hook row were left in place.
