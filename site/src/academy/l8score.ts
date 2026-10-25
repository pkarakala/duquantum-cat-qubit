/** L8 scoring. linresp when P1 is here; otherwise a labelled demo against the square preset. */

import { energyCost, fitToBudget } from './formulas';
import { constants, linrespApi } from './simAdapter';

export interface PulseScore {
  snr: number;
  cost: number;
  snrSquare: number;
  costSquare: number;
  mode: 'linresp' | 'demo';
  bins: number[];
}

export function isFlat(bins: ArrayLike<number>): boolean {
  if (!bins.length) return true;
  let mean = 0;
  for (let i = 0; i < bins.length; i++) mean += bins[i] ?? 0;
  mean /= bins.length;
  let ac = 0;
  for (let i = 0; i < bins.length; i++) {
    const d = (bins[i] ?? 0) - mean;
    ac += d * d;
  }
  return ac <= 1e-8 * (mean * mean + 1);
}

function scaleComplex(value: unknown, factor: number): unknown {
  if (value instanceof Float64Array) {
    const out = new Float64Array(value.length);
    for (let i = 0; i < value.length; i++) out[i] = value[i]! * factor;
    return out;
  }
  if (Array.isArray(value)) {
    return value.map((item) => {
      if (typeof item === 'number') return item * factor;
      if (item && typeof item === 'object') {
        const z = item as { re?: number; im?: number };
        return { re: (z.re ?? 0) * factor, im: (z.im ?? 0) * factor };
      }
      return item;
    });
  }
  return value;
}

function scoreLinresp(bins: number[], squareBins: number[]): Omit<PulseScore, 'bins'> | null {
  const C = constants();
  const lr = linrespApi();
  if (!C || !lr?.response || !lr.snr || !lr.leakageProxy) return null;
  const once = (pulse: number[]) => {
    const n = pulse.length;
    const dt = 1 / n;
    const edges = Array.from({ length: n + 1 }, (_, i) => i * dt);
    const plus = lr.response!(pulse, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 10);
    const deltaB = scaleComplex(plus.b, 2);
    return {
      snr: Number(lr.snr!(plus.tUs, deltaB, C.KAPPA_B)),
      cost: Number(lr.leakageProxy!(plus.tUs, plus.da)),
    };
  };
  const yours = once(bins);
  const square = once(squareBins);
  if (![yours.snr, yours.cost, square.snr, square.cost].every((n) => Number.isFinite(n))) return null;
  return { snr: yours.snr, cost: yours.cost, snrSquare: square.snr, costSquare: square.cost, mode: 'linresp' };
}

export function scorePulse(bins: number[], squareBins: number[], squareSnr: number): PulseScore {
  try {
    const live = scoreLinresp(bins, squareBins);
    if (live) return { ...live, bins };
  } catch {
    /* demo below */
  }
  const dt = 1 / Math.max(1, bins.length);
  const cost = energyCost(bins, dt);
  const costSquare = energyCost(squareBins, dt);
  const snr = isFlat(bins) ? squareSnr : squareSnr * 1.25;
  return { snr, cost, snrSquare: squareSnr, costSquare, mode: 'demo', bins };
}

export function costOf(bins: number[], squareBins: number[], squareSnr: number): number {
  return scorePulse(bins, squareBins, squareSnr).cost;
}

export function fitPulse(bins: number[], squareBins: number[], squareSnr: number): number[] {
  const target = scorePulse(squareBins, squareBins, squareSnr).costSquare;
  return fitToBudget(bins, target, (candidate) => scorePulse(candidate, squareBins, squareSnr).cost);
}

export { fitToBudget };
