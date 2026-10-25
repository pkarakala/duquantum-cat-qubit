/**
 * The only closed forms in the academy folder.
 * poisson is the L1 histogram. coherentDecay is the L2 dashed overlay.
 * dftMagnitude is the L8 spectrum of the bars the learner drew (a display transform).
 * Rates and the Lindblad equation stay in P1 / the server.
 */

/** 1 MHz expressed in rad/µs. The 2π conversion is not recomputed here; this is the numeric value. */
export const ONE_MHZ = 6.283185307179586;

export function poisson(n: number, mu: number): number {
  if (n < 0 || !Number.isFinite(n)) return 0;
  if (mu < 0 || !Number.isFinite(mu)) return 0;
  if (mu === 0) return n === 0 ? 1 : 0;
  let p = Math.exp(-mu);
  for (let k = 0; k < n; k++) p *= mu / (k + 1);
  return p;
}

/** ⟨n⟩(t) = n0 e^{−κ t} for a coherent state losing one photon at a time. */
export function coherentDecay(n0: number, kappa: number, t: number): number {
  return n0 * Math.exp(-kappa * t);
}

const TAU = 6.283185307179586;

/** Magnitude of the DFT of a real pulse. Bin k has frequency k / T. */
export function dftMagnitude(bins: ArrayLike<number>): number[] {
  const n = bins.length;
  const out: number[] = [];
  for (let k = 0; k < n; k++) {
    let re = 0;
    let im = 0;
    for (let t = 0; t < n; t++) {
      const ang = (-TAU * k * t) / n;
      const v = bins[t] ?? 0;
      re += v * Math.cos(ang);
      im += v * Math.sin(ang);
    }
    out.push(Math.hypot(re, im));
  }
  return out;
}

export function energyCost(bins: ArrayLike<number>, dt: number): number {
  let sum = 0;
  for (let i = 0; i < bins.length; i++) {
    const e = bins[i] ?? 0;
    sum += e * e * dt;
  }
  return sum;
}

/**
 * Rescale a pulse so costFn(bins) matches target.
 * Leakage and energy are both quadratic in amplitude, so one square-root
 * scale is exact up to roundoff; a second pass absorbs that roundoff.
 */
export function fitToBudget(bins: number[], target: number, costFn: (b: number[]) => number): number[] {
  const c0 = costFn(bins);
  if (!(c0 > 0) || !(target >= 0)) return bins.slice();
  if (target === 0) return bins.map(() => 0);
  let scale = Math.sqrt(target / c0);
  let next = bins.map((b) => b * scale);
  const c1 = costFn(next);
  if (c1 > 0) {
    scale = Math.sqrt(target / c1);
    next = next.map((b) => b * scale);
  }
  return next;
}
