/** QuTiP Clenshaw Wigner at g = 2, the dynamiqs ħ = 1/2 convention.

x is Re α and y is Im α. Vacuum is W = (2/π) exp(−2(x²+y²)), so W(0,0) = 2/π
and a coherent state |β⟩ peaks at (Re β, Im β). The scaled Fock diagonals are
precomputed once per state; only the Clenshaw sweep depends on (x, y).
*/

import type { ComplexMatrix } from './complex.ts';

const G = 2;
const PREF = (G * G * 0.5) / Math.PI;

interface Diag {
  re: Float64Array;
  im: Float64Array;
}

/** Position-independent Laguerre coefficients: the doubled upper diagonals of ρ. */
export function wignerDiags(rho: ComplexMatrix): Diag[] {
  const m = rho.n;
  const diags: Diag[] = [];
  for (let L = 0; L < m; L++) {
    const len = m - L;
    const re = new Float64Array(len);
    const im = new Float64Array(len);
    const scale = L === 0 ? 1 : 2;
    for (let i = 0; i < len; i++) {
      const k = 2 * (i * m + (i + L));
      re[i] = scale * rho.data[k];
      im[i] = scale * rho.data[k + 1];
    }
    diags.push({ re, im });
  }
  return diags;
}

function wigLaguerre(L: number, x: number, cRe: Float64Array, cIm: Float64Array): { re: number; im: number } {
  const len = cRe.length;
  let y0r: number;
  let y0i: number;
  let y1r: number;
  let y1i: number;
  if (len === 1) {
    y0r = cRe[0];
    y0i = cIm[0];
    y1r = 0;
    y1i = 0;
  } else if (len === 2) {
    y0r = cRe[0];
    y0i = cIm[0];
    y1r = cRe[1];
    y1i = cIm[1];
  } else {
    let k = len;
    y0r = cRe[len - 2];
    y0i = cIm[len - 2];
    y1r = cRe[len - 1];
    y1i = cIm[len - 1];
    for (let i = 3; i <= len; i++) {
      k -= 1;
      const cR = cRe[len - i];
      const cI = cIm[len - i];
      const s1 = Math.sqrt(((k - 1) * (L + k - 1)) / ((L + k) * k));
      const s2 = (L + 2 * k - 1 - x) / Math.sqrt((L + k) * k);
      const n0r = cR - y1r * s1;
      const n0i = cI - y1i * s1;
      const n1r = y0r - y1r * s2;
      const n1i = y0i - y1i * s2;
      y0r = n0r;
      y0i = n0i;
      y1r = n1r;
      y1i = n1i;
    }
  }
  const s = (L + 1 - x) / Math.sqrt(L + 1);
  return { re: y0r - y1r * s, im: y0i - y1i * s };
}

export function wignerFromDiags(diags: Diag[], x: Float64Array, y: Float64Array): Float64Array {
  const nx = x.length;
  const ny = y.length;
  const out = new Float64Array(nx * ny);
  const m = diags[0].re.length;
  if (m === 1) {
    const p = diags[0].re[0];
    for (let ix = 0; ix < nx; ix++) {
      for (let iy = 0; iy < ny; iy++) {
        const b = G * G * (x[ix] * x[ix] + y[iy] * y[iy]);
        out[ix * ny + iy] = p * Math.exp(-0.5 * b) * PREF;
      }
    }
    return out;
  }
  for (let ix = 0; ix < nx; ix++) {
    const a2r = G * x[ix];
    for (let iy = 0; iy < ny; iy++) {
      const a2i = G * y[iy];
      const b = a2r * a2r + a2i * a2i;
      let w0r = diags[m - 1].re[0];
      let w0i = diags[m - 1].im[0];
      for (let L = m - 2; L >= 0; L--) {
        const yv = wigLaguerre(L, b, diags[L].re, diags[L].im);
        const inv = 1 / Math.sqrt(L + 1);
        const mr = w0r * a2r - w0i * a2i;
        const mi = w0r * a2i + w0i * a2r;
        w0r = yv.re + mr * inv;
        w0i = yv.im + mi * inv;
      }
      out[ix * ny + iy] = w0r * Math.exp(-0.5 * b) * PREF;
    }
  }
  return out;
}

/** W(x, y) row-major, index ix * y.length + iy = W(x[ix], y[iy]). */
export function wigner(rho: ComplexMatrix, x: Float64Array, y: Float64Array): Float64Array {
  return wignerFromDiags(wignerDiags(rho), x, y);
}
