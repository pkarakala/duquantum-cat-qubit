/** Public solver types. Field names follow the product contract. */

import type { ExprTree } from './expr.ts';

export interface OneModeParams {
  N: number;
  alpha: number;
  kappa2: number;
  kappaA: number;
  nTh?: number;
  epsZ?: number;
  epsX?: number;
  H?: ExprTree;
  jumps?: ExprTree[];
}

export type OutputName = 'n' | 'parity' | 're_a' | 'wigner';

export interface SimRequest {
  params: OneModeParams;
  init: {
    kind: 'vacuum' | 'coherent' | 'cat_plus' | 'cat_minus' | 'fock';
    alpha?: number;
    n?: number;
  };
  tEndUs: number;
  nT: number;
  /** Crank–Nicolson steps. Defaults to 400 per 2 µs, and at least one per output interval. */
  nSteps?: number;
  outputs: OutputName[];
  wignerTimes?: number[];
}

export interface WignerFrame {
  tUs: number;
  /** Row-major W(x[ix], y[iy]) at ix * y.length + iy. dynamiqs layout. */
  w: Float64Array;
}

export interface SimResult {
  tUs: Float64Array;
  n?: Float64Array;
  parity?: Float64Array;
  reA?: Float64Array;
  /** Fock populations at t_end. Always filled; L1 and L3 read them as a histogram. */
  finalPops: Float64Array;
  wigner?: { x: Float64Array; y: Float64Array; frames: WignerFrame[] };
  meta: { engine: 'ts-cn'; wallMs: number; nSteps: number };
}
