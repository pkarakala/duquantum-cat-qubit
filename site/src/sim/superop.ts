/** Column-stacked Lindbladian, stored on a band.

L = −i (I⊗H − Hᵀ⊗I) + Σ [J*⊗J − ½ I⊗J†J − ½ (J†J)ᵀ⊗I].
Vector index is r + c N, so a photon shift of p levels reaches bandwidth p(N+1).
*/

import { adjoint, mul, type ComplexMatrix } from './complex.ts';
import { couplingRange } from './ops.ts';

export interface Banded {
  n: number;
  kl: number;
  ku: number;
  mm: number;
  /** Row-major packed band. Element (r, c) lives at r*mm + (c − r + kl). */
  re: Float64Array;
  im: Float64Array;
}

export function emptyBand(n: number, kl: number, ku: number): Banded {
  const mm = kl + ku + 1;
  return { n, kl, ku, mm, re: new Float64Array(n * mm), im: new Float64Array(n * mm) };
}

export function bandAdd(b: Banded, r: number, c: number, re: number, im: number): void {
  if (re === 0 && im === 0) return;
  const p = c - r + b.kl;
  if (p < 0 || p >= b.mm) {
    throw new Error(`Lindbladian element (${r},${c}) is outside kl=${b.kl} ku=${b.ku}`);
  }
  const i = r * b.mm + p;
  b.re[i] += re;
  b.im[i] += im;
}

export function bandMatvec(b: Banded, v: Float64Array, y: Float64Array): void {
  const { n, kl, ku, mm, re, im } = b;
  for (let i = 0; i < n; i++) {
    const j0 = i - kl > 0 ? i - kl : 0;
    const j1 = i + ku < n - 1 ? i + ku : n - 1;
    let sr = 0;
    let si = 0;
    const row = i * mm;
    for (let j = j0; j <= j1; j++) {
      const p = row + (j - i + kl);
      const lr = re[p];
      const li = im[p];
      const vr = v[2 * j];
      const vi = v[2 * j + 1];
      sr += lr * vr - li * vi;
      si += lr * vi + li * vr;
    }
    y[2 * i] = sr;
    y[2 * i + 1] = si;
  }
}

function nnz(m: ComplexMatrix): Array<[number, number, number, number]> {
  const n = m.n;
  const out: Array<[number, number, number, number]> = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const k = 2 * (r * n + c);
      const re = m.data[k];
      const im = m.data[k + 1];
      if (re !== 0 || im !== 0) out.push([r, c, re, im]);
    }
  }
  return out;
}

/** s * (I ⊗ M), column stacking. */
function addITensor(b: Banded, n: number, entries: Array<[number, number, number, number]>, sr: number, si: number): void {
  for (const [row, col, re, im] of entries) {
    const vr = sr * re - si * im;
    const vi = sr * im + si * re;
    for (let m = 0; m < n; m++) bandAdd(b, row + m * n, col + m * n, vr, vi);
  }
}

/** s * (Mᵀ ⊗ I). */
function addTransposeTensorI(b: Banded, n: number, entries: Array<[number, number, number, number]>, sr: number, si: number): void {
  for (const [l, m, re, im] of entries) {
    const vr = sr * re - si * im;
    const vi = sr * im + si * re;
    for (let r = 0; r < n; r++) bandAdd(b, r + m * n, r + l * n, vr, vi);
  }
}

/** s = J* ⊗ J in column-stacking. J* is the elementwise conjugate, and
 * np.kron puts the first factor on the slow (column) index:
 * (J*⊗J)[r + c N, r' + c' N] = J*[c, c'] J[r, r'].
 */
function addJstarTensorJ(b: Banded, n: number, entries: Array<[number, number, number, number]>): void {
  for (const [rOut, rIn, jR, jI] of entries) {
    for (const [cOut, cIn, jcR, jcI] of entries) {
      const cr = jcR;
      const ci = -jcI;
      const vr = cr * jR - ci * jI;
      const vi = cr * jI + ci * jR;
      bandAdd(b, rOut + cOut * n, rIn + cIn * n, vr, vi);
    }
  }
}

export function lindbladian(h: ComplexMatrix, jumps: ComplexMatrix[]): Banded {
  const n = h.n;
  let p = couplingRange(h);
  const prepared = jumps.map((j) => {
    const jd = adjoint(j);
    const jdj = mul(jd, j);
    p = Math.max(p, couplingRange(j), couplingRange(jdj));
    return { entries: nnz(j), jdj: nnz(jdj) };
  });
  const dim = n * n;
  const kl = Math.min(dim - 1, p * (n + 1));
  const ku = kl;
  const band = emptyBand(dim, kl, ku);
  if (nnz(h).length) {
    const he = nnz(h);
    addITensor(band, n, he, 0, -1);
    addTransposeTensorI(band, n, he, 0, 1);
  }
  for (const j of prepared) {
    addJstarTensorJ(band, n, j.entries);
    addITensor(band, n, j.jdj, -0.5, 0);
    addTransposeTensorI(band, n, j.jdj, -0.5, 0);
  }
  return band;
}
