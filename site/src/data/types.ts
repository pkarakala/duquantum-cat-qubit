// Data shapes of the Lab bundle: CONTRACT §6.2 (records) and §13 (lab files).
// Keys marked optional are additive extensions from brief 11 §4; no §13 key is renamed or removed.

export type Source = "live" | "mock";
export type DataName = "records" | "inflation" | "errors" | "readout" | "verify";
export const DATA_NAMES: readonly DataName[] = ["records", "inflation", "errors", "readout", "verify"];

export const ID_RE = /^[a-z0-9_]+(\.[a-z0-9_\-]+)*$/;

// ---- records.json (duq.record/v2) ----

export interface ConvergenceSweep {
  fixed?: Record<string, number> | null;
  values: number[];
  results: (number | null)[];
}

export interface Convergence {
  key?: string;
  rel_tol: number;
  sweeps: Record<string, ConvergenceSweep>;
  needed?: Record<string, number | null> | null;
  converged: boolean;
}

export interface CrossCheck {
  method: string;
  ref_id?: string | null;
  value?: number | null;
  rel_diff: number | null;
  tol: number;
  agree: boolean;
}

export interface Provenance {
  script: string;
  git_commit: string | null;
  git_branch?: string | null;
  dirty: boolean;
  dynamiqs?: string | null;
  jax?: string | null;
  numpy?: string | null;
  scipy?: string | null;
  python?: string | null;
  platform?: string | null;
  cpu_count?: number | null;
  wall_s?: number | null;
  timestamp?: string | null;
  wrapped_by?: string | null;
  wrapped_at?: string | null;
}

export interface DuqRecord {
  schema: string;
  id: string;
  task: string;
  quantity: string;
  value: number;
  uncertainty?: number | null;
  units: string;
  method: string;
  params: Record<string, unknown>;
  truncation?: Record<string, number> | null;
  convergence?: Convergence | null;
  numerics?: Record<string, unknown> | null;
  cross_check?: CrossCheck[] | null;
  artifacts?: Record<string, string | null> | null;
  notes?: string | null;
  // Required by the schema; optional here so the UI can render (amber) a malformed record.
  provenance?: Provenance | null;
}

// ---- inflation.json ----

export interface WignerFrame {
  t_us: number;
  w: number[][]; // w[iy][ix]
}

export interface InflationData {
  t_us: number[];
  na: number[];
  nb: number[];
  top2_a: number[];
  top_b: number[];
  effective: { t_us: number[]; na: number[] };
  wigner: { x: number[]; y: number[]; frames: WignerFrame[] };
  record_ids: string[];
  alpha?: number; // optional: drawn as the alpha^2 reference line
}

// ---- errors.json ----

export interface RatePoint {
  alpha2: number;
  value: number;
  unc: number | null;
  id: string;
  model?: string; // optional: which model a time-domain point belongs to
}

export interface ErrorsData {
  gamma_x: {
    one_mode: RatePoint[];
    two_mode: RatePoint[];
    td: RatePoint[];
    analytic: { alpha2: number[]; ch1: number[]; ch2: number[]; total: number[]; source?: string };
    thermal: Record<string, RatePoint[]>;
    thermal_model?: string; // optional: "one_mode" | "two_mode"
    local_slope: { alpha2: number[]; one_mode: (number | null)[]; two_mode: (number | null)[]; source?: string };
  };
  gamma_z: {
    td: RatePoint[];
    eig: RatePoint[];
    pred: { alpha2: number[]; value: number[] };
  };
}

// ---- readout.json ----

export interface Signals {
  t_us: number[];
  b_plus_re: number[];
  b_plus_im: number[];
  b_minus_re: number[];
  b_minus_im: number[];
  eps_over_g2?: number;
}

export interface SignalsAtEps extends Signals {
  eps_over_g2: number;
}

export interface TradeoffPoint {
  eps_over_g2: number;
  snr_T1us: number;
  gamma_x_rel: number;
  id: string | null;
  alpha?: number;
  ok?: boolean; // optional: false = unconverged grid point (shown greyed)
}

export interface Pulse {
  t_us: number[]; // bin edges, length n + 1
  eps: number[]; // bin values, length n
  snr: number;
  cost: number;
  id: string | null; // the SNR record
  cost_id?: string | null;
  snr_method?: string; // "td" or "linresp"
  signal?: { t_us: number[]; db_abs: number[] };
}

export interface ReadoutData {
  alpha: number;
  linresp: { freq_MHz: number; Q: number; t5: number; t1: number; id?: string | null };
  signals: Signals;
  signals_by_eps?: SignalsAtEps[];
  tradeoff: TradeoffPoint[];
  pulses: Record<string, Pulse>;
}

// ---- verify.json ----

export interface VerifyData {
  generated_at: string;
  tests: { passed: number; failed: number; skipped: number; source?: string | null };
  convergence: { id: string; axis: string; values: number[]; results: (number | null)[]; tol: number; converged: boolean }[];
  cross_checks: { id: string; method: string; rel_diff: number | null; tol: number; agree: boolean }[];
  claims?: { ok: number; warn: number; fail: number; files: string[] };
}

// ---- the bundle the pages read ----

export interface Bundle {
  records: DuqRecord[];
  inflation: InflationData;
  errors: ErrorsData;
  readout: ReadoutData;
  verify: VerifyData;
  sources: Record<DataName, Source>;
  notes: string[]; // e.g. why a live file fell back to mock
  byId: Map<string, DuqRecord>;
}
