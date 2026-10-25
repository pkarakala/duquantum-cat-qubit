import { describe, expect, it } from 'vitest';
import { energyCost, fitToBudget } from '../formulas';
import { constants, linrespApi } from '../simAdapter';

const ready = Boolean(constants() && linrespApi()?.optimalPulse && linrespApi()?.snr && linrespApi()?.leakageProxy && linrespApi()?.response);

describe('L8 pulse scoring', () => {
  it.skipIf(!ready)('optimalPulse scaled to the square cost beats the square', () => {
    const C = constants()!;
    const lr = linrespApi()!;
    const opt = lr.optimalPulse!(20, 1, C.G2, C.KAPPA_B, C.ALPHA);
    const square = Array.from({ length: 20 }, () => 0.5 * C.G2);
    const score = (bins: number[]) => {
      const n = bins.length;
      const edges = Array.from({ length: n + 1 }, (_, i) => i / n);
      const plus = lr.response!(bins, edges, C.G2, C.KAPPA_B, C.ALPHA, 1, 10);
      return { snr: lr.snr!(plus.tUs, plus.b, C.KAPPA_B), cost: lr.leakageProxy!(plus.tUs, plus.da) };
    };
    const fitted = fitToBudget(opt.epsBins, score(square).cost, (bins) => score(bins).cost);
    const yours = score(fitted);
    const ref = score(square);
    expect(yours.snr).toBeGreaterThan(ref.snr);
    expect(yours.cost).toBeLessThanOrEqual(ref.cost + 1e-9);
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
