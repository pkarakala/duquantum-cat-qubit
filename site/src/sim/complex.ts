/** Dense complex matrices as interleaved re/im Float64Arrays, row-major. */

export interface ComplexMatrix {
  n: number;
  /** Length 2 n². Element (r, c) is at 2 (r n + c). */
  data: Float64Array;
}

export interface Complex {
  re: number;
  im: number;
}

export function zeros(n: number): ComplexMatrix {
  return { n, data: new Float64Array(2 * n * n) };
}

export function eye(n: number, re = 1, im = 0): ComplexMatrix {
  const m = zeros(n);
  for (let i = 0; i < n; i++) {
    const k = 2 * (i * n + i);
    m.data[k] = re;
    m.data[k + 1] = im;
  }
  return m;
}

export function get(m: ComplexMatrix, r: number, c: number): Complex {
  const k = 2 * (r * m.n + c);
  return { re: m.data[k], im: m.data[k + 1] };
}

export function set(m: ComplexMatrix, r: number, c: number, re: number, im: number): void {
  const k = 2 * (r * m.n + c);
  m.data[k] = re;
  m.data[k + 1] = im;
}

export function scale(m: ComplexMatrix, re: number, im: number): ComplexMatrix {
  const out = zeros(m.n);
  const a = m.data;
  const b = out.data;
  for (let k = 0; k < a.length; k += 2) {
    const ar = a[k];
    const ai = a[k + 1];
    b[k] = ar * re - ai * im;
    b[k + 1] = ar * im + ai * re;
  }
  return out;
}

export function add(a: ComplexMatrix, b: ComplexMatrix): ComplexMatrix {
  const out = zeros(a.n);
  for (let k = 0; k < out.data.length; k++) out.data[k] = a.data[k] + b.data[k];
  return out;
}

export function sub(a: ComplexMatrix, b: ComplexMatrix): ComplexMatrix {
  const out = zeros(a.n);
  for (let k = 0; k < out.data.length; k++) out.data[k] = a.data[k] - b.data[k];
  return out;
}

export function mul(a: ComplexMatrix, b: ComplexMatrix): ComplexMatrix {
  const n = a.n;
  const out = zeros(n);
  const ad = a.data;
  const bd = b.data;
  const cd = out.data;
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < n; k++) {
      const ar = ad[2 * (i * n + k)];
      const ai = ad[2 * (i * n + k) + 1];
      if (ar === 0 && ai === 0) continue;
      for (let j = 0; j < n; j++) {
        const br = bd[2 * (k * n + j)];
        const bi = bd[2 * (k * n + j) + 1];
        const o = 2 * (i * n + j);
        cd[o] += ar * br - ai * bi;
        cd[o + 1] += ar * bi + ai * br;
      }
    }
  }
  return out;
}

export function adjoint(m: ComplexMatrix): ComplexMatrix {
  const n = m.n;
  const out = zeros(n);
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const s = 2 * (r * n + c);
      const t = 2 * (c * n + r);
      out.data[t] = m.data[s];
      out.data[t + 1] = -m.data[s + 1];
    }
  }
  return out;
}

export function trace(m: ComplexMatrix): Complex {
  let re = 0;
  let im = 0;
  const n = m.n;
  for (let i = 0; i < n; i++) {
    const k = 2 * (i * n + i);
    re += m.data[k];
    im += m.data[k + 1];
  }
  return { re, im };
}

/** ρ ← (ρ + ρ†) / 2. Kills the round-off that would otherwise blow up. */
export function hermitize(m: ComplexMatrix): void {
  const n = m.n;
  const d = m.data;
  for (let r = 0; r < n; r++) {
    for (let c = r; c < n; c++) {
      const ij = 2 * (r * n + c);
      const ji = 2 * (c * n + r);
      const re = 0.5 * (d[ij] + d[ji]);
      const im = 0.5 * (d[ij + 1] - d[ji + 1]);
      d[ij] = re;
      d[ij + 1] = im;
      d[ji] = re;
      d[ji + 1] = -im;
    }
  }
}

/** Frobenius norm of ρ − ρ†. */
export function hermDeviation(m: ComplexMatrix): number {
  const n = m.n;
  const d = m.data;
  let sum = 0;
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const ij = 2 * (r * n + c);
      const ji = 2 * (c * n + r);
      const dr = d[ij] - d[ji];
      const di = d[ij + 1] + d[ji + 1];
      sum += dr * dr + di * di;
    }
  }
  return Math.sqrt(sum);
}

export function maxAbs(m: ComplexMatrix): number {
  let mabs = 0;
  const d = m.data;
  for (let k = 0; k < d.length; k += 2) {
    const a = Math.hypot(d[k], d[k + 1]);
    if (a > mabs) mabs = a;
  }
  return mabs;
}

export function cAbs(z: Complex): number {
  return Math.hypot(z.re, z.im);
}

export function cAdd(a: Complex, b: Complex): Complex {
  return { re: a.re + b.re, im: a.im + b.im };
}

export function cSub(a: Complex, b: Complex): Complex {
  return { re: a.re - b.re, im: a.im - b.im };
}

export function cMul(a: Complex, b: Complex): Complex {
  return { re: a.re * b.re - a.im * b.im, im: a.re * b.im + a.im * b.re };
}

export function cDiv(a: Complex, b: Complex): Complex {
  const den = b.re * b.re + b.im * b.im;
  return {
    re: (a.re * b.re + a.im * b.im) / den,
    im: (a.im * b.re - a.re * b.im) / den,
  };
}

export function cScale(a: Complex, s: number): Complex {
  return { re: a.re * s, im: a.im * s };
}

export function cExp(a: Complex): Complex {
  const mag = Math.exp(a.re);
  return { re: mag * Math.cos(a.im), im: mag * Math.sin(a.im) };
}

export function cSqrt(a: Complex): Complex {
  const r = Math.hypot(a.re, a.im);
  if (r === 0) return { re: 0, im: 0 };
  const re = Math.sqrt((r + a.re) / 2);
  const im = Math.sign(a.im || 1) * Math.sqrt((r - a.re) / 2);
  return { re, im: a.im < 0 ? -Math.abs(im) : Math.abs(im) };
}
