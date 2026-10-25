/** Linear response of the readout. Same physics as `src/linresp.py`.

dx/dt = M x + u ε, with x = (δa, b), well s = ±1,
M = [[0, −2i s g₂ α], [−2i s g₂ α, −κ_b/2]], u = [−i, 0].
Each drive bin is advanced by the exact 3×3 exponential of the affine system.
*/

import { linspace } from './util.ts';

export interface Poles {
  re: number;
  im: number;
}

export interface CVec {
  re: Float64Array;
  im: Float64Array;
}

export interface Trajectory {
  tUs: Float64Array;
  da: CVec;
  b: CVec;
}

export function poles(g2: number, kappaB: number, alpha: number): Poles[] {
  const b = kappaB / 2;
  const c = 4 * g2 * g2 * alpha * alpha;
  const disc = b * b - 4 * c;
  const re = -b / 2;
  if (disc < 0) {
    const im = Math.sqrt(-disc) / 2;
    return [
      { re, im },
      { re, im: -im },
    ];
  }
  const root = Math.sqrt(disc) / 2;
  return [
    { re: re + root, im: 0 },
    { re: re - root, im: 0 },
  ];
}

function norm1(re: Float64Array, im: Float64Array): number {
  let max = 0;
  for (let i = 0; i < 3; i++) {
    let sum = 0;
    for (let j = 0; j < 3; j++) sum += Math.hypot(re[i * 3 + j], im[i * 3 + j]);
    if (sum > max) max = sum;
  }
  return max;
}

function mul3(ar: Float64Array, ai: Float64Array, br: Float64Array, bi: Float64Array, cr: Float64Array, ci: Float64Array): void {
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      let sr = 0;
      let si = 0;
      for (let k = 0; k < 3; k++) {
        const a = i * 3 + k;
        const b = k * 3 + j;
        sr += ar[a] * br[b] - ai[a] * bi[b];
        si += ar[a] * bi[b] + ai[a] * br[b];
      }
      cr[i * 3 + j] = sr;
      ci[i * 3 + j] = si;
    }
  }
}

/** exp(A) for a 3×3 complex matrix, scaling-and-squaring Taylor. */
function expm3(aRe: Float64Array, aIm: Float64Array): { re: Float64Array; im: Float64Array } {
  let scale = 0;
  let nrm = norm1(aRe, aIm);
  const re = Float64Array.from(aRe);
  const im = Float64Array.from(aIm);
  while (nrm > 0.5 && scale < 40) {
    for (let i = 0; i < 9; i++) {
      re[i] *= 0.5;
      im[i] *= 0.5;
    }
    nrm *= 0.5;
    scale += 1;
  }
  const sumRe = new Float64Array(9);
  const sumIm = new Float64Array(9);
  const termRe = new Float64Array(9);
  const termIm = new Float64Array(9);
  for (let i = 0; i < 3; i++) {
    sumRe[i * 3 + i] = 1;
    termRe[i * 3 + i] = 1;
  }
  const nextRe = new Float64Array(9);
  const nextIm = new Float64Array(9);
  for (let k = 1; k <= 16; k++) {
    mul3(termRe, termIm, re, im, nextRe, nextIm);
    const inv = 1 / k;
    let big = 0;
    for (let i = 0; i < 9; i++) {
      termRe[i] = nextRe[i] * inv;
      termIm[i] = nextIm[i] * inv;
      sumRe[i] += termRe[i];
      sumIm[i] += termIm[i];
      const a = Math.abs(termRe[i]) + Math.abs(termIm[i]);
      if (a > big) big = a;
    }
    if (big < 1e-16) break;
  }
  const accRe = Float64Array.from(sumRe);
  const accIm = Float64Array.from(sumIm);
  const sqRe = new Float64Array(9);
  const sqIm = new Float64Array(9);
  for (let s = 0; s < scale; s++) {
    mul3(accRe, accIm, accRe, accIm, sqRe, sqIm);
    accRe.set(sqRe);
    accIm.set(sqIm);
  }
  return { re: accRe, im: accIm };
}

function apply3(eRe: Float64Array, eIm: Float64Array, vRe: number[], vIm: number[]): { re: number[]; im: number[] } {
  const re = [0, 0, 0];
  const im = [0, 0, 0];
  for (let i = 0; i < 3; i++) {
    let sr = 0;
    let si = 0;
    for (let j = 0; j < 3; j++) {
      const a = i * 3 + j;
      sr += eRe[a] * vRe[j] - eIm[a] * vIm[j];
      si += eRe[a] * vIm[j] + eIm[a] * vRe[j];
    }
    re[i] = sr;
    im[i] = si;
  }
  return { re, im };
}

function advance(
  daRe: number,
  daIm: number,
  bRe: number,
  bIm: number,
  h: number,
  eps: number,
  cRe: number,
  cIm: number,
  gamma: number,
): { daRe: number; daIm: number; bRe: number; bIm: number } {
  if (h === 0) return { daRe, daIm, bRe, bIm };
  const aRe = new Float64Array(9);
  const aIm = new Float64Array(9);
  aRe[1] = cRe * h;
  aIm[1] = cIm * h;
  aRe[3] = cRe * h;
  aIm[3] = cIm * h;
  aRe[4] = -gamma * h;
  aIm[2] = -eps * h;
  const e = expm3(aRe, aIm);
  const v = apply3(e.re, e.im, [daRe, bRe, 1], [daIm, bIm, 0]);
  return { daRe: v.re[0], daIm: v.im[0], bRe: v.re[1], bIm: v.im[1] };
}

function sampleTimes(edges: ArrayLike<number>, nSamples: number | ArrayLike<number>): Float64Array {
  if (typeof nSamples === 'number') {
    return linspace(edges[0], edges[edges.length - 1], nSamples);
  }
  return Float64Array.from(nSamples);
}

/**
 * Piecewise-constant drive. `nSamples` is either a count (uniform grid on the
 * edges) or the sample times themselves, which is how the P0 parity fixtures
 * are checked.
 */
export function response(
  epsBins: ArrayLike<number>,
  edgesUs: ArrayLike<number>,
  g2: number,
  kappaB: number,
  alpha: number,
  well: number,
  nSamples: number | ArrayLike<number>,
): Trajectory {
  if (well !== 1 && well !== -1) throw new Error('well must be +1 or -1');
  if (edgesUs.length !== epsBins.length + 1) throw new Error('edgesUs must be one longer than epsBins');
  const times = sampleTimes(edgesUs, nSamples);
  const cRe = 0;
  const cIm = -2 * well * g2 * alpha;
  const gamma = kappaB / 2;
  const daRe = new Float64Array(times.length);
  const daIm = new Float64Array(times.length);
  const bRe = new Float64Array(times.length);
  const bIm = new Float64Array(times.length);
  let state = { daRe: 0, daIm: 0, bRe: 0, bIm: 0 };
  let t = edgesUs[0];
  for (let s = 0; s < times.length; s++) {
    const target = times[s];
    if (target + 1e-12 < t) throw new Error('sample times must be nondecreasing and inside the edges');
    while (t < target - 1e-15) {
      let bin = 0;
      while (bin < epsBins.length - 1 && edgesUs[bin + 1] <= t + 1e-15) bin += 1;
      const boundary = edgesUs[bin + 1];
      const tNext = target < boundary ? target : boundary;
      state = advance(state.daRe, state.daIm, state.bRe, state.bIm, tNext - t, epsBins[bin], cRe, cIm, gamma);
      t = tNext;
    }
    daRe[s] = state.daRe;
    daIm[s] = state.daIm;
    bRe[s] = state.bRe;
    bIm[s] = state.bIm;
  }
  return { tUs: times, da: { re: daRe, im: daIm }, b: { re: bRe, im: bIm } };
}

export function trapz(t: ArrayLike<number>, y: ArrayLike<number>): number {
  let acc = 0;
  for (let i = 0; i < t.length - 1; i++) {
    acc += 0.5 * (y[i] + y[i + 1]) * (t[i + 1] - t[i]);
  }
  return acc;
}

/** κ_b ∫ |Δb|² dt. */
export function snr(tUs: ArrayLike<number>, deltaB: { re: ArrayLike<number>; im: ArrayLike<number> }, kappaB: number): number {
  const y = new Float64Array(tUs.length);
  for (let i = 0; i < y.length; i++) y[i] = deltaB.re[i] * deltaB.re[i] + deltaB.im[i] * deltaB.im[i];
  return kappaB * trapz(tUs, y);
}

/** ∫ |δa|² dt. */
export function leakageProxy(tUs: ArrayLike<number>, da: { re: ArrayLike<number>; im: ArrayLike<number> }): number {
  const y = new Float64Array(tUs.length);
  for (let i = 0; i < y.length; i++) y[i] = da.re[i] * da.re[i] + da.im[i] * da.im[i];
  return trapz(tUs, y);
}

export function pulseEnergy(edgesUs: ArrayLike<number>, epsBins: ArrayLike<number>): number {
  let e = 0;
  for (let i = 0; i < epsBins.length; i++) {
    e += epsBins[i] * epsBins[i] * (edgesUs[i + 1] - edgesUs[i]);
  }
  return e;
}

export interface ResponseMatrices {
  tUs: Float64Array;
  edgesUs: Float64Array;
  /** Row-major nSamples × nBins. Column j is the unit-bin Δb = b(+α) − b(−α). */
  rbRe: Float64Array;
  rbIm: Float64Array;
  /** δa of the +α well, same layout. */
  raRe: Float64Array;
  raIm: Float64Array;
}

export function responseMatrices(T: number, nBins: number, nSamples: number, g2: number, kappaB: number, alpha: number): ResponseMatrices {
  const edgesUs = linspace(0, T, nBins + 1);
  const rbRe = new Float64Array(nSamples * nBins);
  const rbIm = new Float64Array(nSamples * nBins);
  const raRe = new Float64Array(nSamples * nBins);
  const raIm = new Float64Array(nSamples * nBins);
  const eps = new Float64Array(nBins);
  let tUs: Float64Array | null = null;
  for (let j = 0; j < nBins; j++) {
    eps.fill(0);
    eps[j] = 1;
    const plus = response(eps, edgesUs, g2, kappaB, alpha, 1, nSamples);
    const minus = response(eps, edgesUs, g2, kappaB, alpha, -1, nSamples);
    tUs = plus.tUs;
    for (let s = 0; s < nSamples; s++) {
      const idx = s * nBins + j;
      rbRe[idx] = plus.b.re[s] - minus.b.re[s];
      rbIm[idx] = plus.b.im[s] - minus.b.im[s];
      raRe[idx] = plus.da.re[s];
      raIm[idx] = plus.da.im[s];
    }
  }
  return { tUs: tUs!, edgesUs, rbRe, rbIm, raRe, raIm };
}

function applyR(rbRe: Float64Array, rbIm: Float64Array, nS: number, nBins: number, v: Float64Array): CVec {
  const re = new Float64Array(nS);
  const im = new Float64Array(nS);
  for (let s = 0; s < nS; s++) {
    let sr = 0;
    let si = 0;
    const row = s * nBins;
    for (let j = 0; j < nBins; j++) {
      sr += rbRe[row + j] * v[j];
      si += rbIm[row + j] * v[j];
    }
    re[s] = sr;
    im[s] = si;
  }
  return { re, im };
}

/**
 * Top right singular vector of R_b, scaled so ∫ε² dt = 1.
 * `gain` is the SNR of that unit-energy pulse.
 */
export function optimalPulse(
  nBins: number,
  T: number,
  g2: number,
  kappaB: number,
  alpha: number,
): { epsBins: Float64Array; gain: number } {
  const nSamples = Math.max(201, nBins * 8);
  const mats = responseMatrices(T, nBins, nSamples, g2, kappaB, alpha);
  let v = new Float64Array(nBins);
  for (let j = 0; j < nBins; j++) v[j] = 1;
  const normalize = (u: Float64Array): void => {
    let n2 = 0;
    for (let j = 0; j < u.length; j++) n2 += u[j] * u[j];
    const s = 1 / Math.sqrt(n2);
    for (let j = 0; j < u.length; j++) u[j] *= s;
  };
  normalize(v);
  for (let iter = 0; iter < 40; iter++) {
    const y = applyR(mats.rbRe, mats.rbIm, nSamples, nBins, v);
    const w = new Float64Array(nBins);
    for (let j = 0; j < nBins; j++) {
      let s = 0;
      for (let i = 0; i < nSamples; i++) {
        const idx = i * nBins + j;
        s += mats.rbRe[idx] * y.re[i] + mats.rbIm[idx] * y.im[i];
      }
      w[j] = s;
    }
    normalize(w);
    v = w;
  }
  let sum = 0;
  for (let j = 0; j < nBins; j++) sum += v[j];
  if (sum < 0) for (let j = 0; j < nBins; j++) v[j] = -v[j];
  const dt = T / nBins;
  let energy = 0;
  for (let j = 0; j < nBins; j++) energy += v[j] * v[j] * dt;
  const scale = 1 / Math.sqrt(energy);
  for (let j = 0; j < nBins; j++) v[j] *= scale;
  const delta = applyR(mats.rbRe, mats.rbIm, nSamples, nBins, v);
  return { epsBins: v, gain: snr(mats.tUs, delta, kappaB) };
}
