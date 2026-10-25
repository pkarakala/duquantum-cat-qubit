CREATE TABLE sim_runs (
  ts timestamptz NOT NULL DEFAULT now(), learner_id uuid, level_id text, engine text NOT NULL,
  model text NOT NULL, params jsonb NOT NULL, params_hash text NOT NULL,
  alpha double precision, kappa2_scale double precision, eps_z_over_g2 double precision,
  na_final double precision, t_x_us double precision, t_z_us double precision, snr double precision,
  wall_ms integer, cached boolean
);
SELECT create_hypertable('sim_runs', 'ts');
