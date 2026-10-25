import { describe, expect, it } from 'vitest';
import { factorBand, solveBand } from './banded.ts';

function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Full GEPP, the oracle for the banded solver. */
function denseSolve(ar: Float64Array, ai: Float64Array, n: number, br: Float64Array, bi: Float64Array): { re: Float64Array; im: Float64Array } {
  const aRe = Float64Array.from(ar);
  const aIm = Float64Array.from(ai);
  const xRe = Float64Array.from(br);
  const xIm = Float64Array.from(bi);
  const at = (i: number, j: number) => i * n + j;
  for (let k = 0; k < n; k++) {
    let p = k;
    let best = aRe[at(k, k)] ** 2 + aIm[at(k, k)] ** 2;
    for (let i = k + 1; i < n; i++) {
      const mag = aRe[at(i, k)] ** 2 + aIm[at(i, k)] ** 2;
      if (mag > best) {
        best = mag;
        p = i;
      }
    }
    if (p !== k) {
      for (let j = 0; j < n; j++) {
        const s = at(k, j);
        const d = at(p, j);
        const tr = aRe[s];
        const ti = aIm[s];
        aRe[s] = aRe[d];
        aIm[s] = aIm[d];
        aRe[d] = tr;
        aIm[d] = ti;
      }
      const tr = xRe[k];
      const ti = xIm[k];
      xRe[k] = xRe[p];
      xIm[k] = xIm[p];
      xRe[p] = tr;
      xIm[p] = ti;
    }
    const pr = aRe[at(k, k)];
    const pi = aIm[at(k, k)];
    const den = pr * pr + pi * pi;
    for (let i = k + 1; i < n; i++) {
      const mr = (aRe[at(i, k)] * pr + aIm[at(i, k)] * pi) / den;
      const mi = (aIm[at(i, k)] * pr - aRe[at(i, k)] * pi) / den;
      aRe[at(i, k)] = mr;
      aIm[at(i, k)] = mi;
      for (let j = k + 1; j < n; j++) {
        aRe[at(i, j)] -= mr * aRe[at(k, j)] - mi * aIm[at(k, j)];
        aIm[at(i, j)] -= mr * aIm[at(k, j)] + mi * aRe[at(k, j)];
      }
    }
  }
  for (let k = 0; k < n; k++) {
    for (let i = k + 1; i < n; i++) {
      xRe[i] -= aRe[at(i, k)] * xRe[k] - aIm[at(i, k)] * xIm[k];
      xIm[i] -= aRe[at(i, k)] * xIm[k] + aIm[at(i, k)] * xRe[k];
    }
  }
  for (let k = n - 1; k >= 0; k--) {
    for (let j = k + 1; j < n; j++) {
      xRe[k] -= aRe[at(k, j)] * xRe[j] - aIm[at(k, j)] * xIm[j];
      xIm[k] -= aRe[at(k, j)] * xIm[j] + aIm[at(k, j)] * xRe[j];
    }
    const pr = aRe[at(k, k)];
    const pi = aIm[at(k, k)];
    const den = pr * pr + pi * pi;
    const nr = (xRe[k] * pr + xIm[k] * pi) / den;
    const ni = (xIm[k] * pr - xRe[k] * pi) / den;
    xRe[k] = nr;
    xIm[k] = ni;
  }
  return { re: xRe, im: xIm };
}

describe('banded LU', () => {
  it('matches dense GEPP on a non-diagonally-dominant band', () => {
    const rand = mulberry32(7);
    const n = 24;
    const kl = 4;
    const ku = 3;
    const mm = kl + ku + 1;
    const packedRe = new Float64Array(n * mm);
    const packedIm = new Float64Array(n * mm);
    const fullRe = new Float64Array(n * n);
    const fullIm = new Float64Array(n * n);
    for (let i = 0; i < n; i++) {
      for (let j = Math.max(0, i - kl); j <= Math.min(n - 1, i + ku); j++) {
        const re = rand() * 2 - 1;
        const im = rand() * 2 - 1;
        packedRe[i * mm + (j - i + kl)] = re;
        packedIm[i * mm + (j - i + kl)] = im;
        fullRe[i * n + j] = re;
        fullIm[i * n + j] = im;
      }
    }
    const bRe = Float64Array.from({ length: n }, () => rand() * 2 - 1);
    const bIm = Float64Array.from({ length: n }, () => rand() * 2 - 1);
    const oracle = denseSolve(fullRe, fullIm, n, bRe, bIm);
    const factor = factorBand(packedRe, packedIm, n, kl, ku);
    const gotRe = Float64Array.from(bRe);
    const gotIm = Float64Array.from(bIm);
    solveBand(factor, gotRe, gotIm);
    let err = 0;
    for (let i = 0; i < n; i++) err = Math.max(err, Math.hypot(gotRe[i] - oracle.re[i], gotIm[i] - oracle.im[i]));
    expect(err).toBeLessThan(1e-9);
  });

  it('solves a pure diagonal system', () => {
    const n = 5;
    const packedRe = new Float64Array(n);
    const packedIm = new Float64Array(n);
    for (let i = 0; i < n; i++) packedRe[i] = i + 2;
    const bRe = Float64Array.from([2, 3, 4, 5, 6]);
    const bIm = new Float64Array(n);
    const factor = factorBand(packedRe, packedIm, n, 0, 0);
    solveBand(factor, bRe, bIm);
    for (let i = 0; i < n; i++) expect(bRe[i]).toBeCloseTo((i + 2) / (i + 2), 12);
    expect(bRe[0]).toBeCloseTo(1, 12);
    expect(bRe[3]).toBeCloseTo(5 / 5, 12);
  });
});
