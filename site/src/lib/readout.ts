// Readout designer helpers: the epsilon slider snaps to the precomputed grid; nothing is computed.
import type { ReadoutData, SignalsAtEps, TradeoffPoint } from "../data/types";

// Slider index i -> signals_by_eps[i], ascending in eps_over_g2 (falls back to the single `signals`).
export function epsGrid(r: ReadoutData): SignalsAtEps[] {
  if (r.signals_by_eps && r.signals_by_eps.length) {
    return [...r.signals_by_eps].sort((a, b) => a.eps_over_g2 - b.eps_over_g2);
  }
  return [{ ...r.signals, eps_over_g2: r.signals.eps_over_g2 ?? NaN }];
}

// Start the slider at the grid point nearest 1 g2 (the point shown in `signals`).
export function defaultEpsIndex(grid: SignalsAtEps[], target = 1): number {
  let best = 0;
  grid.forEach((s, i) => {
    if (Math.abs(s.eps_over_g2 - target) < Math.abs(grid[best].eps_over_g2 - target)) best = i;
  });
  return best;
}

export function tradeoffAlphas(r: ReadoutData): number[] {
  const set = new Set<number>();
  for (const t of r.tradeoff) set.add(t.alpha ?? r.alpha);
  return [...set].sort((a, b) => a - b);
}

export function sameEps(a: number, b: number): boolean {
  return Math.abs(a - b) <= 1e-6 * Math.max(Math.abs(a), Math.abs(b), 1e-12);
}

export function tradeoffFor(r: ReadoutData, alpha: number): TradeoffPoint[] {
  return r.tradeoff
    .filter((t) => sameEps(t.alpha ?? r.alpha, alpha))
    .sort((a, b) => a.eps_over_g2 - b.eps_over_g2);
}

export function fmtEps(x: number): string {
  return Number.isFinite(x) ? `${Number(x.toPrecision(3))} g₂` : "n/a";
}
