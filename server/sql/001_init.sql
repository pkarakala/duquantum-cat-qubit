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
-- real-time: include rows newer than the last refresh
ALTER MATERIALIZED VIEW alpha_choices_5m SET (timescaledb.materialized_only = false);
CREATE INDEX IF NOT EXISTS leaderboard_challenge_score ON leaderboard (challenge, score DESC);
CREATE INDEX IF NOT EXISTS sim_runs_learner_ts ON sim_runs (learner_id, ts DESC);
