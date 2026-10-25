/** Level spec types from CONTRACT §7, plus the extras named in the P2 brief. */

export type LevelId = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6' | 'L7' | 'L8';

export type MisconceptionId = 'M1' | 'M2' | 'M3' | 'M4' | 'M5' | 'M6' | 'M7';

export type Phase = 'concept' | 'predict' | 'play' | 'check' | 'aha';

export type SimEngine = 'ts' | 'server-two-mode' | 'server-expr' | 'records';

export type SimSource = 'ts' | 'server' | 'preset' | 'records' | 'in-browser-fallback';

export interface PredictOption {
  id: string;
  text: string;
  correct: boolean;
  misconception?: MisconceptionId;
  feedback: string;
}

export interface Control {
  name: string;
  /** 1–3 words, PhET style. */
  label: string;
  type: 'range' | 'select' | 'toggle' | 'choice';
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  options?: { value: string; label: string }[];
  initial?: number | string | boolean;
  /** Stay hidden until the learner has opened this hint. */
  revealAtHint?: number;
  visibleWhen?: string;
  visibleValue?: string;
  /** Snap a range to these values (L7 readout grid). */
  snap?: number[];
}

export type ViewKind =
  | 'histogram'
  | 'wigner'
  | 'n_t'
  | 'parity'
  | 'rates_log'
  | 'bias'
  | 'double_well'
  | 'blocks'
  | 'truncation'
  | 'b_iq'
  | 'snr'
  | 'pulse'
  | 'leaderboard';

export interface View {
  kind: ViewKind;
  label?: string;
}

export interface CheckResult {
  pass: boolean;
  message: string;
}

export interface RatePoint {
  alpha2: number;
  gamma: number;
  id?: string;
}

export interface RateGrid {
  gammaX: RatePoint[];
  gammaZ: RatePoint[];
}

export interface SimResultLike {
  tUs?: ArrayLike<number>;
  n?: ArrayLike<number>;
  na?: ArrayLike<number>;
  nb?: ArrayLike<number>;
  parity?: ArrayLike<number>;
  reA?: ArrayLike<number>;
  wigner?: {
    x: ArrayLike<number>;
    y: ArrayLike<number>;
    frames: { tUs: number; w: ArrayLike<number> }[];
  };
  mixtureW?: ArrayLike<number>;
  summary?: string;
  meta?: Record<string, unknown>;
  records?: RateGrid;
  tradeoff?: { eps: number; snr: number; alpha?: number; gammaXRel?: number; id?: string }[];
  signals?: {
    tUs: ArrayLike<number>;
    bPlusRe: ArrayLike<number>;
    bPlusIm: ArrayLike<number>;
    bMinusRe: ArrayLike<number>;
    bMinusIm: ArrayLike<number>;
  };
  detectKeys?: string[];
  snr?: number;
  cost?: number;
  snrSquare?: number;
  costSquare?: number;
  squareBins?: number[];
  squareSnr?: number;
  [key: string]: unknown;
}

export interface LevelState {
  params: Record<string, number | string | boolean>;
  detectKeys?: string[];
  records?: RateGrid;
  snr?: number;
  cost?: number;
  snrSquare?: number;
  costSquare?: number;
  tradeoff?: SimResultLike['tradeoff'];
  build?: string;
  tree?: unknown;
  python?: string;
  bins?: number[];
  [key: string]: unknown;
}

export interface FollowUp {
  question: string;
  options: PredictOption[];
  fn?: (answer: string) => CheckResult;
}

export interface LevelSpec {
  id: LevelId;
  title: string;
  minutes: number;
  concept: { text: string; narrationKey: string };
  predict: { question: string; options: PredictOption[] };
  controls: Control[];
  sim: { engine: SimEngine; request: (state: LevelState) => unknown };
  views: View[];
  check: { goal: string; fn: (result: SimResultLike, state: LevelState) => CheckResult };
  predictFollowUp?: FollowUp;
  /** L4 part 2. Named in the P2 brief; CONTRACT §7 calls the same idea checkParts. */
  checkFollowUp?: FollowUp;
  checkParts?: { goal: string; fn: (result: SimResultLike, state: LevelState) => CheckResult }[];
  aha: string;
  showCode: (state: LevelState) => string;
  /** Static snippet when blocks / toPython are absent. */
  codeFallback: string;
  allowedConstants: number[];
  solution: string[];
  hints: [string, string, string, string];
  preset: string;
  sources: string[];
}

export interface PresetEntry {
  id: string;
  levelId: string;
  source?: 'mock' | 'precomputed';
  params: Record<string, number | string | boolean>;
  ranges?: Record<string, [number, number]>;
  result: SimResultLike;
  note?: string;
}

export interface RunOutcome {
  result: SimResultLike;
  source: SimSource;
  badge: string;
  banner?: string;
  presetId?: string;
}
