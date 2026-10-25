/** Fock-space operators and states for one bosonic mode. */

import { adjoint, eye, mul, scale, sub, zeros, type Complex, type ComplexMatrix } from './complex.ts';

/** Annihilation operator. ⟨n|a|n+1⟩ = √(n+1). Stored dense; the only nonzeros are the superdiagonal. */
export function destroy(n: number): ComplexMatrix {
  const a = zeros(n);
  for (let k = 0; k < n - 1; k++) {
    a.data[2 * (k * n + (k + 1))] = Math.sqrt(k + 1);
  }
  return a;
}

export function numberOp(n: number): ComplexMatrix {
  const m = zeros(n);
  for (let k = 0; k < n; k++) m.data[2 * (k * n + k)] = k;
  return m;
}

export function parityOp(n: number): ComplexMatrix {
  const m = zeros(n);
  for (let k = 0; k < n; k++) m.data[2 * (k * n + k)] = k % 2 === 0 ? 1 : -1;
  return m;
}

export interface Amplitude {
  re: Float64Array;
  im: Float64Array;
}

/** Unnormalized coherent amplitudes via log Γ(n+1) = Σ log k. */
export function coherentAmps(n: number, alphaRe: number, alphaIm: number): Amplitude {
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  const r2 = alphaRe * alphaRe + alphaIm * alphaIm;
  if (r2 === 0) {
    re[0] = 1;
    return { re, im };
  }
  const logR = 0.5 * Math.log(r2);
  const arg = Math.atan2(alphaIm, alphaRe);
  let logFact = 0;
  for (let k = 0; k < n; k++) {
    const logC = -r2 / 2 + k * logR - 0.5 * logFact;
    const mag = Math.exp(logC);
    const phase = k * arg;
    re[k] = mag * Math.cos(phase);
    im[k] = mag * Math.sin(phase);
    logFact += Math.log(k + 1);
  }
  return { re, im };
}

export function normalizeAmps(amps: Amplitude): Amplitude {
  let norm = 0;
  for (let i = 0; i < amps.re.length; i++) norm += amps.re[i] * amps.re[i] + amps.im[i] * amps.im[i];
  const s = 1 / Math.sqrt(norm);
  const re = new Float64Array(amps.re.length);
  const im = new Float64Array(amps.im.length);
  for (let i = 0; i < re.length; i++) {
    re[i] = amps.re[i] * s;
    im[i] = amps.im[i] * s;
  }
  return { re, im };
}

export function coherent(n: number, alphaRe: number, alphaIm = 0): Amplitude {
  return normalizeAmps(coherentAmps(n, alphaRe, alphaIm));
}

/** Even (sign +1) or odd (sign −1) cat, normalized in the truncated space. */
export function cat(n: number, alphaRe: number, sign: 1 | -1, alphaIm = 0): Amplitude {
  const plus = coherentAmps(n, alphaRe, alphaIm);
  const minus = coherentAmps(n, -alphaRe, -alphaIm);
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    re[i] = plus.re[i] + sign * minus.re[i];
    im[i] = plus.im[i] + sign * minus.im[i];
  }
  return normalizeAmps({ re, im });
}

export function fock(n: number, level: number): Amplitude {
  if (level < 0 || level >= n) throw new Error(`fock level ${level} is outside 0..${n - 1}`);
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  re[level] = 1;
  return { re, im };
}

export function ketToRho(amps: Amplitude): ComplexMatrix {
  const n = amps.re.length;
  const rho = zeros(n);
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const k = 2 * (r * n + c);
      rho.data[k] = amps.re[r] * amps.re[c] + amps.im[r] * amps.im[c];
      rho.data[k + 1] = amps.im[r] * amps.re[c] - amps.re[r] * amps.im[c];
    }
  }
  return rho;
}

/** Column-stack a row-major matrix into an interleaved vec, index r + c N. */
export function rhoToVec(rho: ComplexMatrix): Float64Array {
  const n = rho.n;
  const v = new Float64Array(2 * n * n);
  for (let c = 0; c < n; c++) {
    for (let r = 0; r < n; r++) {
      const src = 2 * (r * n + c);
      const dst = 2 * (r + c * n);
      v[dst] = rho.data[src];
      v[dst + 1] = rho.data[src + 1];
    }
  }
  return v;
}

export function vecToRho(v: Float64Array, n: number): ComplexMatrix {
  const rho = zeros(n);
  for (let c = 0; c < n; c++) {
    for (let r = 0; r < n; r++) {
      const src = 2 * (r + c * n);
      const dst = 2 * (r * n + c);
      rho.data[dst] = v[src];
      rho.data[dst + 1] = v[src + 1];
    }
  }
  return rho;
}

/** (ρ + ρ†) / 2 on a column-stacked vector. */
export function hermitizeVec(v: Float64Array, n: number): void {
  for (let c = 0; c < n; c++) {
    for (let r = c; r < n; r++) {
      const ij = 2 * (r + c * n);
      const ji = 2 * (c + r * n);
      const re = 0.5 * (v[ij] + v[ji]);
      const im = 0.5 * (v[ij + 1] - v[ji + 1]);
      v[ij] = re;
      v[ij + 1] = im;
      v[ji] = re;
      v[ji + 1] = -im;
    }
  }
}

export interface Expectations {
  trace: number;
  n: number;
  parity: number;
  reA: number;
  imA: number;
  pops: Float64Array;
  hermAbs: number;
}

export function expectations(v: Float64Array, n: number): Expectations {
  let trace = 0;
  let nbar = 0;
  let parity = 0;
  let reA = 0;
  let imA = 0;
  let herm = 0;
  const pops = new Float64Array(n);
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const ij = 2 * (r + c * n);
      const ji = 2 * (c + r * n);
      const dr = v[ij] - v[ji];
      const di = v[ij + 1] + v[ji + 1];
      herm += dr * dr + di * di;
    }
  }
  for (let k = 0; k < n; k++) {
    const p = v[2 * (k + k * n)];
    pops[k] = p;
    trace += p;
    nbar += k * p;
    parity += k % 2 === 0 ? p : -p;
    if (k + 1 < n) {
      const s = Math.sqrt(k + 1);
      const idx = 2 * (k + 1 + k * n);
      reA += s * v[idx];
      imA += s * v[idx + 1];
    }
  }
  return { trace, n: nbar, parity, reA, imA, pops, hermAbs: Math.sqrt(herm) };
}

/** Largest |i−j| with a nonzero entry. */
export function couplingRange(m: ComplexMatrix): number {
  const n = m.n;
  let p = 0;
  const d = m.data;
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const k = 2 * (r * n + c);
      if (d[k] !== 0 || d[k + 1] !== 0) {
        const gap = r > c ? r - c : c - r;
        if (gap > p) p = gap;
      }
    }
  }
  return p;
}

export function displacementHamiltonian(n: number, epsZ: number, epsX: number): ComplexMatrix {
  const a = destroy(n);
  const ad = adjoint(a);
  let h = zeros(n);
  if (epsZ !== 0) {
    const xz = scale(addReal(a, ad), epsZ, 0);
    h = xz;
  }
  if (epsX !== 0) {
    const diff = sub(ad, a);
    const hx = scale(diff, 0, epsX);
    h = epsZ !== 0 ? addReal(h, hx) : hx;
  }
  return h;
}

function addReal(a: ComplexMatrix, b: ComplexMatrix): ComplexMatrix {
  const out = zeros(a.n);
  for (let k = 0; k < out.data.length; k++) out.data[k] = a.data[k] + b.data[k];
  return out;
}

export function twoPhotonJump(n: number, kappa2: number, alpha: number): ComplexMatrix {
  const a = destroy(n);
  const a2 = mul(a, a);
  const shifted = sub(a2, scale(eye(n), alpha * alpha, 0));
  return scale(shifted, Math.sqrt(kappa2), 0);
}

export function lossJump(n: number, rate: number, raise: boolean): ComplexMatrix {
  const a = destroy(n);
  const op = raise ? adjoint(a) : a;
  return scale(op, Math.sqrt(rate), 0);
}

export type { Complex };
