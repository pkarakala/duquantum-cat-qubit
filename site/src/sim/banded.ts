/** Banded complex LU with partial pivoting.

This is the Numerical Recipes `bandec` / `banbks` algorithm. Partial pivoting
keeps the lower bandwidth, and the upper bandwidth grows from ku to ku+kl.
No-pivoting LU is unstable for the stiff two-photon Lindbladian, so pivoting
is the default. Callers still pass the original kl and ku.
*/

export interface BandFactor {
  n: number;
  mm: number;
  kl: number;
  strideA: number;
  strideL: number;
  aRe: Float64Array;
  aIm: Float64Array;
  alRe: Float64Array;
  alIm: Float64Array;
  indx: Int32Array;
}

function at(i: number, j: number, stride: number): number {
  return i * stride + j;
}

/** Factor a packed band. `packed` is row-major, diagonal at offset `kl`. */
export function factorBand(packedRe: Float64Array, packedIm: Float64Array, n: number, kl: number, ku: number): BandFactor {
  const mm = kl + ku + 1;
  const strideA = mm + 2;
  const strideL = kl + 1;
  const aRe = new Float64Array((n + 1) * strideA);
  const aIm = new Float64Array((n + 1) * strideA);
  const alRe = new Float64Array((n + 1) * strideL);
  const alIm = new Float64Array((n + 1) * strideL);
  const indx = new Int32Array(n + 1);
  for (let i = 1; i <= n; i++) {
    const src = (i - 1) * mm;
    const dst = i * strideA;
    for (let j = 1; j <= mm; j++) {
      aRe[dst + j] = packedRe[src + j - 1];
      aIm[dst + j] = packedIm[src + j - 1];
    }
  }
  let l = kl;
  for (let i = 1; i <= kl; i++) {
    const rowRe = aRe.slice(i * strideA, i * strideA + mm + 1);
    const rowIm = aIm.slice(i * strideA, i * strideA + mm + 1);
    for (let j = kl + 2 - i; j <= mm; j++) {
      aRe[at(i, j - l, strideA)] = rowRe[j];
      aIm[at(i, j - l, strideA)] = rowIm[j];
    }
    l -= 1;
    for (let j = mm - l; j <= mm; j++) {
      aRe[at(i, j, strideA)] = 0;
      aIm[at(i, j, strideA)] = 0;
    }
  }
  l = kl;
  for (let k = 1; k <= n; k++) {
    let dumRe = aRe[at(k, 1, strideA)];
    let dumIm = aIm[at(k, 1, strideA)];
    let ip = k;
    if (l < n) l += 1;
    for (let j = k + 1; j <= l; j++) {
      const jr = aRe[at(j, 1, strideA)];
      const ji = aIm[at(j, 1, strideA)];
      if (jr * jr + ji * ji > dumRe * dumRe + dumIm * dumIm) {
        dumRe = jr;
        dumIm = ji;
        ip = j;
      }
    }
    indx[k] = ip;
    if (dumRe === 0 && dumIm === 0) {
      aRe[at(k, 1, strideA)] = 1e-30;
      dumRe = 1e-30;
    }
    if (ip !== k) {
      for (let j = 1; j <= mm; j++) {
        const ks = at(k, j, strideA);
        const is = at(ip, j, strideA);
        const tr = aRe[ks];
        const ti = aIm[ks];
        aRe[ks] = aRe[is];
        aIm[ks] = aIm[is];
        aRe[is] = tr;
        aIm[is] = ti;
      }
    }
    const pivRe = aRe[at(k, 1, strideA)];
    const pivIm = aIm[at(k, 1, strideA)];
    const den = pivRe * pivRe + pivIm * pivIm;
    for (let i = k + 1; i <= l; i++) {
      const ar = aRe[at(i, 1, strideA)];
      const ai = aIm[at(i, 1, strideA)];
      const mr = (ar * pivRe + ai * pivIm) / den;
      const mi = (ai * pivRe - ar * pivIm) / den;
      alRe[at(k, i - k, strideL)] = mr;
      alIm[at(k, i - k, strideL)] = mi;
      for (let j = 2; j <= mm; j++) {
        const kr = aRe[at(k, j, strideA)];
        const ki = aIm[at(k, j, strideA)];
        const pr = mr * kr - mi * ki;
        const pi = mr * ki + mi * kr;
        const dest = at(i, j - 1, strideA);
        const src = at(i, j, strideA);
        aRe[dest] = aRe[src] - pr;
        aIm[dest] = aIm[src] - pi;
      }
      aRe[at(i, mm, strideA)] = 0;
      aIm[at(i, mm, strideA)] = 0;
    }
  }
  return { n, mm, kl, strideA, strideL, aRe, aIm, alRe, alIm, indx };
}

/** Solve A x = b. `bRe` / `bIm` have length n and are overwritten with x. */
export function solveBand(f: BandFactor, bRe: Float64Array, bIm: Float64Array): void {
  const { n, mm, kl, strideA, strideL, aRe, aIm, alRe, alIm, indx } = f;
  const xRe = new Float64Array(n + 1);
  const xIm = new Float64Array(n + 1);
  for (let i = 1; i <= n; i++) {
    xRe[i] = bRe[i - 1];
    xIm[i] = bIm[i - 1];
  }
  let l = kl;
  for (let k = 1; k <= n; k++) {
    const ip = indx[k];
    if (ip !== k) {
      const tr = xRe[k];
      const ti = xIm[k];
      xRe[k] = xRe[ip];
      xIm[k] = xIm[ip];
      xRe[ip] = tr;
      xIm[ip] = ti;
    }
    if (l < n) l += 1;
    const xr = xRe[k];
    const xi = xIm[k];
    for (let i = k + 1; i <= l; i++) {
      const mr = alRe[at(k, i - k, strideL)];
      const mi = alIm[at(k, i - k, strideL)];
      xRe[i] -= mr * xr - mi * xi;
      xIm[i] -= mr * xi + mi * xr;
    }
  }
  l = 1;
  for (let i = n; i >= 1; i--) {
    let dumRe = xRe[i];
    let dumIm = xIm[i];
    for (let k = 2; k <= l; k++) {
      const idx = k + i - 1;
      const ar = aRe[at(i, k, strideA)];
      const ai = aIm[at(i, k, strideA)];
      const xr = xRe[idx];
      const xi = xIm[idx];
      dumRe -= ar * xr - ai * xi;
      dumIm -= ar * xi + ai * xr;
    }
    const pr = aRe[at(i, 1, strideA)];
    const pi = aIm[at(i, 1, strideA)];
    const den = pr * pr + pi * pi;
    xRe[i] = (dumRe * pr + dumIm * pi) / den;
    xIm[i] = (dumIm * pr - dumRe * pi) / den;
    if (l < mm) l += 1;
  }
  for (let i = 1; i <= n; i++) {
    bRe[i - 1] = xRe[i];
    bIm[i - 1] = xIm[i];
  }
}

/** Build I − (dt/2) L in packed band storage and factor it. */
export function factorShifted(lRe: Float64Array, lIm: Float64Array, n: number, kl: number, ku: number, mm: number, dt: number): BandFactor {
  const re = new Float64Array(n * mm);
  const im = new Float64Array(n * mm);
  const half = 0.5 * dt;
  for (let i = 0; i < re.length; i++) {
    re[i] = -half * lRe[i];
    im[i] = -half * lIm[i];
  }
  for (let i = 0; i < n; i++) re[i * mm + kl] += 1;
  return factorBand(re, im, n, kl, ku);
}
