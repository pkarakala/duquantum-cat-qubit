import { describe, expect, it } from 'vitest';
import { energyCost, fitToBudget } from '../formulas';
import { constants, linrespApi } from '../simAdapter';

const ready = Boolean(constants() && linrespApi()?.optimalPulse && linrespApi()?.snr && linrespApi()?.leakageProxy && linrespApi()?.response);

describe('L8 pulse scoring', () => {
  it.skipIf(!ready)('optimalPulse at the square energy beats the square', () => {
    const C = constants()!;
    const lr = linrespApi()!;
    const opt = lr.optimalPulse!(20, 1, C.G2, C.KAPPA_B, C.ALPHA);
    const square = Array.from({ length: 20 }, () => 0.5 * C.G2);
    const energy = (bins: number[]) => {
      const dt = 1 / bins.length;
      let sum = 0;
      for (const value of bins) sum += value * value * dt;
      return sum;
    };
    const score = (bins: number[]) => {
      const n = bins.length;
      const edges = Array.from({ length: n + 1 }, (_, i) => i / n);
      const plus = lr.response!(bins, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 10);
      const minus = lr.response!(bins, edges, C.G2, C.KAPPA_B, C.ALPHA, -1, 10);
      const re = Float64Array.from(plus.tUs, (_, i) => plus.b.re[i] - minus.b.re[i]);
      const im = Float64Array.from(plus.tUs, (_, i) => plus.b.im[i] - minus.b.im[i]);
      return lr.snr!(plus.tUs, { re, im }, C.KAPPA_B);
    };
    const scale = Math.sqrt(energy(square) / energy(opt.epsBins));
    const shaped = opt.epsBins.map((value) => value * scale);
    expect(score(shaped)).toBeGreaterThan(score(square));
  });

  it.skipIf(!ready)('an over-budget pulse fails the level check', async () => {
    const { L8 } = await import('../levels/L8');
    const C = constants()!;
    const loud = Array.from({ length: 20 }, () => 3 * C.G2);
    const square = Array.from({ length: 20 }, () => 0.5 * C.G2);
    const cost = (bins: number[]) => energyCost(bins, 1 / bins.length);
    expect(L8.check.fn({}, {
      params: {},
      snr: 10,
      cost: cost(loud),
      snrSquare: 1,
      costSquare: cost(square),
    }).pass).toBe(false);
  });

  it('Fit to budget rescales a quadratic cost onto the square within 1e-9', () => {
    const square = Array.from({ length: 20 }, () => 1);
    const loud = square.map((value, i) => value * (1.4 + 0.1 * Math.sin(i)));
    const cost = (bins: number[]) => energyCost(bins, 0.05);
    const fitted = fitToBudget(loud, cost(square), cost);
    expect(Math.abs(cost(fitted) - cost(square))).toBeLessThan(1e-9);
  });
});
