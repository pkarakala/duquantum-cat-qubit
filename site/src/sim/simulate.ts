/** Crank–Nicolson on the vectorized one-mode Lindbladian.

The right-hand side keeps the full N² matrix. Re-Hermitianizing after every
step is required: a ρ = ρ† shortcut lets round-off grow like e^{+κ₂ n² t}
and the trace blows up near 0.3 µs.
*/

import { factorShifted, solveBand, type BandFactor } from './banded.ts';
import { zeros, type ComplexMatrix } from './complex.ts';
import { evalExpr, hermitianResidual, paramTable } from './expr.ts';
import {
  cat,
  coherent,
  displacementHamiltonian,
  expectations,
  fock,
  hermitizeVec,
  ketToRho,
  lossJump,
  rhoToVec,
  twoPhotonJump,
  vecToRho,
  type Amplitude,
} from './ops.ts';
import { bandMatvec, lindbladian, type Banded } from './superop.ts';
import type { OneModeParams, SimRequest, SimResult } from './types.ts';
import { linspace } from './util.ts';
import { wigner } from './wigner.ts';

const WIGNER_PIXELS = 81;
const WIGNER_XMAX = 4;

export interface DetailedResult extends SimResult {
  imA: Float64Array;
  finalRho: ComplexMatrix;
  maxTraceError: number;
  finalHermAbs: number;
}

export function defaultSteps(tEndUs: number, nT: number): number {
  if (!(tEndUs > 0)) return 0;
  const byDuration = Math.max(1, Math.round((400 * tEndUs) / 2));
  const byGrid = Math.max(1, nT - 1);
  return Math.max(byDuration, byGrid);
}

function standardModel(p: OneModeParams): { H: ComplexMatrix; jumps: ComplexMatrix[] } {
  const H = displacementHamiltonian(p.N, p.epsZ ?? 0, p.epsX ?? 0);
  const jumps: ComplexMatrix[] = [];
  if (p.kappa2 !== 0) jumps.push(twoPhotonJump(p.N, p.kappa2, p.alpha));
  const nth = p.nTh ?? 0;
  const down = p.kappaA * (nth + 1);
  if (down > 0) jumps.push(lossJump(p.N, down, false));
  const up = p.kappaA * nth;
  if (up > 0) jumps.push(lossJump(p.N, up, true));
  return { H, jumps };
}

export function modelOf(p: OneModeParams): { H: ComplexMatrix; jumps: ComplexMatrix[] } {
  if (p.H === undefined && p.jumps === undefined) return standardModel(p);
  const table = paramTable(p);
  const H = p.H ? evalExpr(p.H, p.N, table) : zeros(p.N);
  if (p.H) {
    const residual = hermitianResidual(H);
    if (residual > 1e-9) throw new Error(`H is not Hermitian (max |H-H†| = ${residual})`);
  }
  const jumps = (p.jumps ?? []).map((j) => evalExpr(j, p.N, table));
  return { H, jumps };
}

function initialAmps(req: SimRequest): Amplitude {
  const n = req.params.N;
  const alpha = req.init.alpha ?? req.params.alpha;
  switch (req.init.kind) {
    case 'vacuum':
      return fock(n, 0);
    case 'coherent':
      return coherent(n, alpha, 0);
    case 'cat_plus':
      return cat(n, alpha, 1);
    case 'cat_minus':
      return cat(n, alpha, -1);
    case 'fock':
      return fock(n, req.init.n ?? 0);
    default:
      throw new Error(`unknown init kind`);
  }
}

function validate(req: SimRequest, nSteps: number): void {
  const { N } = req.params;
  if (!Number.isInteger(N) || N < 1 || N > 60) throw new Error(`N=${N} is outside 1..60`);
  if (!Number.isInteger(req.nT) || req.nT < 1) throw new Error('nT must be a positive integer');
  if (!(req.tEndUs >= 0)) throw new Error('tEndUs must be ≥ 0');
  if (!Number.isInteger(nSteps) || nSteps < 0) throw new Error('nSteps must be a nonnegative integer');
  if (req.tEndUs === 0 && nSteps !== 0) throw new Error('tEndUs = 0 cannot take steps');
  if (req.tEndUs > 0 && nSteps === 0) throw new Error('tEndUs > 0 needs at least one step');
  for (const name of req.outputs) {
    if (name !== 'n' && name !== 'parity' && name !== 're_a' && name !== 'wigner') {
      throw new Error(`unknown output '${name}'`);
    }
  }
}

export function simulateDetailed(req: SimRequest): DetailedResult {
  const t0 = performance.now();
  const nSteps = req.nSteps ?? defaultSteps(req.tEndUs, req.nT);
  validate(req, nSteps);
  const N = req.params.N;
  const want = new Set(req.outputs);
  const v = rhoToVec(ketToRho(initialAmps(req)));
  const tUs = new Float64Array(req.nT);
  const nArr = want.has('n') ? new Float64Array(req.nT) : undefined;
  const parityArr = want.has('parity') ? new Float64Array(req.nT) : undefined;
  const reA = want.has('re_a') ? new Float64Array(req.nT) : undefined;
  const imA = new Float64Array(req.nT);
  const recordAt = new Uint8Array(nSteps + 1);
  const outStep = new Int32Array(req.nT);
  if (nSteps === 0) {
    tUs[0] = 0;
    recordAt[0] = 1;
    outStep[0] = 0;
  } else {
    const dt = req.tEndUs / nSteps;
    for (let i = 0; i < req.nT; i++) {
      const target = req.nT === 1 ? req.tEndUs : (i * req.tEndUs) / (req.nT - 1);
      const step = Math.round(target / dt);
      const clamped = step < 0 ? 0 : step > nSteps ? nSteps : step;
      outStep[i] = clamped;
      recordAt[clamped] = 1;
      tUs[i] = clamped * dt;
    }
  }
  const wignerTimes = want.has('wigner') ? (req.wignerTimes ?? [req.tEndUs]) : [];
  const wignerStep: number[] = [];
  const x = linspace(-WIGNER_XMAX, WIGNER_XMAX, WIGNER_PIXELS);
  const y = linspace(-WIGNER_XMAX, WIGNER_XMAX, WIGNER_PIXELS);
  const frames: { tUs: number; w: Float64Array }[] = [];
  if (wignerTimes.length) {
    const dt = nSteps === 0 ? 1 : req.tEndUs / nSteps;
    for (const time of wignerTimes) {
      if (time < -1e-12 || time > req.tEndUs + 1e-12) throw new Error(`wigner time ${time} is outside [0, tEnd]`);
      const step = nSteps === 0 ? 0 : Math.round(time / dt);
      const clamped = step < 0 ? 0 : step > nSteps ? nSteps : step;
      wignerStep.push(clamped);
      recordAt[clamped] = 1;
    }
  }
  let factor: BandFactor | null = null;
  let band: Banded | null = null;
  let yBuf: Float64Array | null = null;
  let bRe: Float64Array | null = null;
  let bIm: Float64Array | null = null;
  if (nSteps > 0) {
    const model = modelOf(req.params);
    band = lindbladian(model.H, model.jumps);
    const dt = req.tEndUs / nSteps;
    factor = factorShifted(band.re, band.im, band.n, band.kl, band.ku, band.mm, dt);
    yBuf = new Float64Array(2 * band.n);
    bRe = new Float64Array(band.n);
    bIm = new Float64Array(band.n);
  }
  let maxTraceError = 0;
  let written = 0;
  const capture = (step: number): void => {
    if (!recordAt[step]) return;
    const ex = expectations(v, N);
    maxTraceError = Math.max(maxTraceError, Math.abs(ex.trace - 1));
    for (let i = 0; i < req.nT; i++) {
      if (outStep[i] !== step) continue;
      if (nArr) nArr[i] = ex.n;
      if (parityArr) parityArr[i] = ex.parity;
      if (reA) reA[i] = ex.reA;
      imA[i] = ex.imA;
      written += 1;
    }
    for (let f = 0; f < wignerStep.length; f++) {
      if (wignerStep[f] !== step || frames[f]) continue;
      const rho = vecToRho(v, N);
      frames[f] = { tUs: nSteps === 0 ? 0 : (step * req.tEndUs) / nSteps, w: wigner(rho, x, y) };
    }
  };
  capture(0);
  if (nSteps > 0 && band && factor && yBuf && bRe && bIm) {
    const dt = req.tEndUs / nSteps;
    const half = 0.5 * dt;
    for (let step = 1; step <= nSteps; step++) {
      bandMatvec(band, v, yBuf);
      for (let i = 0; i < band.n; i++) {
        bRe[i] = v[2 * i] + half * yBuf[2 * i];
        bIm[i] = v[2 * i + 1] + half * yBuf[2 * i + 1];
      }
      solveBand(factor, bRe, bIm);
      for (let i = 0; i < band.n; i++) {
        v[2 * i] = bRe[i];
        v[2 * i + 1] = bIm[i];
      }
      hermitizeVec(v, N);
      capture(step);
    }
  }
  if (written < req.nT) throw new Error('internal error: an output time was not recorded');
  const final = expectations(v, N);
  const wallMs = performance.now() - t0;
  return {
    tUs,
    n: nArr,
    parity: parityArr,
    reA,
    imA,
    finalPops: final.pops,
    finalRho: vecToRho(v, N),
    maxTraceError,
    finalHermAbs: final.hermAbs,
    wigner: want.has('wigner') ? { x, y, frames } : undefined,
    meta: { engine: 'ts-cn', wallMs, nSteps },
  };
}

export function simulate(req: SimRequest): SimResult {
  const detailed = simulateDetailed(req);
  return {
    tUs: detailed.tUs,
    n: detailed.n,
    parity: detailed.parity,
    reA: detailed.reA,
    finalPops: detailed.finalPops,
    wigner: detailed.wigner,
    meta: detailed.meta,
  };
}
