/** Shared numeric helpers for the level checks. No differential equations. */

import type { RatePoint, SimResultLike } from '../types';

export function asNumbers(values: ArrayLike<number> | undefined): number[] {
  if (!values) return [];
  const out: number[] = [];
  for (let i = 0; i < values.length; i++) out.push(Number(values[i]));
  return out;
}

export function param(state: { params?: Record<string, unknown> } | null | undefined, name: string): unknown {
  if (state?.params && name in state.params) return state.params[name];
  if (state && name in (state as Record<string, unknown>)) return (state as Record<string, unknown>)[name];
  return undefined;
}

export function nearestIndex(t: ArrayLike<number>, target: number): number {
  let best = 0;
  let bestD = Infinity;
  for (let i = 0; i < t.length; i++) {
    const d = Math.abs(Number(t[i]) - target);
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  }
  return best;
}

/** Mean of samples in the last `window` time units, including the edge. */
export function tailMean(t: ArrayLike<number>, y: ArrayLike<number>, window = 0.5): number {
  if (!t.length || !y.length) return NaN;
  const tEnd = Number(t[t.length - 1]);
  const start = tEnd - window;
  let sum = 0;
  let n = 0;
  const m = Math.min(t.length, y.length);
  for (let i = 0; i < m; i++) {
    if (Number(t[i]) >= start - 1e-12) {
      sum += Number(y[i]);
      n += 1;
    }
  }
  return n ? sum / n : NaN;
}

/**
 * Log-linear interpolation of a positive rate versus α².
 * Returns null outside the outermost points: never extrapolate.
 */
export function logLinear(points: RatePoint[], x: number): number | null {
  const pts = points.filter((p) => p.gamma > 0 && Number.isFinite(p.alpha2)).sort((a, b) => a.alpha2 - b.alpha2);
  if (!pts.length) return null;
  const lo = pts[0]!.alpha2;
  const hi = pts[pts.length - 1]!.alpha2;
  if (x < lo - 1e-9 || x > hi + 1e-9) return null;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i]!;
    const b = pts[i + 1]!;
    if (x < a.alpha2 - 1e-12 || x > b.alpha2 + 1e-12) continue;
    const span = b.alpha2 - a.alpha2;
    if (span <= 1e-15) return a.gamma;
    const u = (x - a.alpha2) / span;
    return Math.exp(Math.log(a.gamma) * (1 - u) + Math.log(b.gamma) * u);
  }
  return pts[pts.length - 1]!.gamma;
}

export function series(result: SimResultLike, key: 'n' | 'na' | 'nb' | 'parity'): number[] {
  return asNumbers(result[key] as ArrayLike<number> | undefined);
}

/** Last 10% of n(t) is flat when its spread is under 1e-3. */
export function oddEvenPopulations(_t: ArrayLike<number>, n: ArrayLike<number>): { p0: number; p1: number } | null {
  if (n.length < 2) {
    const only = Number(n[n.length - 1]);
    if (!Number.isFinite(only)) return null;
    return { p0: 1 - only, p1: only };
  }
  const start = Math.floor(n.length * 0.9);
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = start; i < n.length; i++) {
    const v = Number(n[i]);
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  if (hi - lo >= 1e-3) return null;
  const nInf = Number(n[n.length - 1]);
  return { p0: 1 - nInf, p1: nInf };
}
