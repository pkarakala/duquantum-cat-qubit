import { describe, expect, it } from 'vitest';
import { L1 } from '../levels/L1';
import { L2 } from '../levels/L2';
import { L3 } from '../levels/L3';
import { L4 } from '../levels/L4';
import { L5 } from '../levels/L5';
import { L6 } from '../levels/L6';
import { L7 } from '../levels/L7';
import { L8 } from '../levels/L8';
import type { LevelState, SimResultLike } from '../types';

function state(params: LevelState['params'], extra: Partial<LevelState> = {}): LevelState {
  return { params, ...extra };
}

describe('level checks at the LEVELS windows', () => {
  it('L1 accepts the inclusive α window and rejects a Fock state', () => {
    for (const alpha of [2.08, 2.1, 2.12]) {
      expect(L1.check.fn({}, state({ alpha, state: 'coherent' })).pass).toBe(true);
    }
    for (const alpha of [2.079, 2.121]) {
      expect(L1.check.fn({}, state({ alpha, state: 'coherent' })).pass).toBe(false);
    }
    const fock = L1.check.fn({}, state({ alpha: 2.1, state: 'fock' }));
    expect(fock.pass).toBe(false);
    expect(fock.message.length).toBeGreaterThan(0);
  });

  it('L2 accepts the inclusive κ window', () => {
    for (const kappa of [1.32, 1.386, 1.46]) expect(L2.check.fn({}, state({ kappa })).pass).toBe(true);
    for (const kappa of [1.319, 1.461]) expect(L2.check.fn({}, state({ kappa })).pass).toBe(false);
  });

  it('L3 reads the plateau from n(t_end)', () => {
    const trace = (plateau: number): SimResultLike => ({ tUs: [0, 3], n: [2, plateau] });
    for (const plateau of [0.43, 0.45, 0.47]) expect(L3.check.fn(trace(plateau), state({ alpha: 1.07 })).pass).toBe(true);
    for (const plateau of [0.429, 0.471]) expect(L3.check.fn(trace(plateau), state({ alpha: 1 })).pass).toBe(false);
  });

  it('L4 uses the save nearest 1 µs, rejects loss and parity 0.9, and accepts the follow-up', () => {
    const trace = (n: number, parity: number): SimResultLike => ({ tUs: [0, 1, 2], n: [0, n, n], parity: [1, parity, parity] });
    expect(L4.check.fn(trace(4.3, 0.91), state({ loss: 'off' })).pass).toBe(true);
    expect(L4.check.fn(trace(4.5, 0.91), state({ loss: 'off' })).pass).toBe(true);
    expect(L4.check.fn(trace(4.4, 0.9), state({ loss: 'off' })).pass).toBe(false);
    expect(L4.check.fn(trace(4.299, 0.95), state({ loss: 'off' })).pass).toBe(false);
    expect(L4.check.fn(trace(4.501, 0.95), state({ loss: 'off' })).pass).toBe(false);
    expect(L4.check.fn(trace(4.41, 0.97), state({ loss: 'on' })).pass).toBe(false);
    expect(L4.checkFollowUp?.fn?.('the fringes and the parity').pass).toBe(true);
  });

  it('L5 interpolates log-linearly and refuses to extrapolate', () => {
    const records = {
      gammaX: [
        { alpha2: 1, gamma: 1e-4 },
        { alpha2: 9, gamma: 1e-6 },
      ],
      gammaZ: [
        { alpha2: 8, gamma: 0.9 },
        { alpha2: 8.56, gamma: 1 },
        { alpha2: 9, gamma: 1.2 },
      ],
    };
    expect(L5.check.fn({}, state({ alpha2: 8.5 }, { records })).pass).toBe(true);
    expect(L5.check.fn({}, state({ alpha2: 8.6 }, { records })).pass).toBe(false);
    expect(L5.check.fn({}, state({ alpha2: 0.5 }, { records })).message).toMatch(/no verified data here/i);
    expect(L5.check.fn({}, state({ alpha2: 9.01 }, { records })).message).toMatch(/no verified data here/i);
  });

  it('L6 averages the last 0.5 µs and requires a quiet detector', () => {
    const trace = (nss: number): SimResultLike => ({ tUs: [0, 1.5, 2], na: [1, nss, nss] });
    for (const nss of [4.3218, 4.41, 4.4982]) {
      expect(L6.check.fn(trace(nss), state({}, { detectKeys: [] })).pass).toBe(true);
    }
    for (const nss of [4.32, 4.5]) expect(L6.check.fn(trace(nss), state({}, { detectKeys: [] })).pass).toBe(false);
    expect(L6.check.fn(trace(4.41), state({}, { detectKeys: ['no_dissipation'] })).pass).toBe(false);
  });

  it('L7 passes SNR ≥ 1', () => {
    expect(L7.check.fn({}, state({ eps: 1 }, { snr: 1 })).pass).toBe(true);
    expect(L7.check.fn({}, state({ eps: 0.5 }, { snr: 0.99 })).pass).toBe(false);
  });

  it('L8 requires a strict SNR win inside the square budget', () => {
    const square = state({}, { snr: 1, cost: 1, snrSquare: 1, costSquare: 1 });
    const shaped = state({}, { snr: 1.2, cost: 1, snrSquare: 1, costSquare: 1 });
    const loud = state({}, { snr: 2, cost: 1.001, snrSquare: 1, costSquare: 1 });
    expect(L8.check.fn({}, square).pass).toBe(false);
    expect(L8.check.fn({}, shaped).pass).toBe(true);
    expect(L8.check.fn({}, loud).pass).toBe(false);
  });
});
