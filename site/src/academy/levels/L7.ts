/** L7 · readout rings, then settles. The pass window is the ε grid at α = 2.1. */

import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { loadTradeoff } from '../data/records';
import { opt } from './feedback';
import { param } from './metrics';

const CODE = 'H = H + eps_z*(a + a.dag())';
export const READOUT_GRID = [0.05, 0.1, 0.2, 0.5, 1, 2, 3];

export function snrAt(result: SimResultLike, state: LevelState): number | null {
  if (typeof state.snr === 'number' && Number.isFinite(state.snr)) return state.snr;
  if (typeof result.snr === 'number' && Number.isFinite(result.snr)) return result.snr;
  const eps = Number(param(state, 'eps'));
  const rows = state.tradeoff ?? result.tradeoff ?? loadTradeoff();
  if (!rows) return null;
  const row = rows.find((r) => Math.abs(r.eps - eps) < 1e-9 && (r.alpha == null || Math.abs(r.alpha - 2.1) < 1e-6));
  return row ? row.snr : null;
}

function check(result: SimResultLike, state: LevelState) {
  const snr = snrAt(result, state);
  if (snr == null) return { pass: false, message: 'Not yet. Pick a readout strength on the grid and run.' };
  if (snr >= 1) return { pass: true, message: `Pass. SNR over 1 µs is ${snr.toFixed(3)} (≥ 1).` };
  return { pass: false, message: `Not yet. SNR over 1 µs is ${snr.toFixed(3)}. It needs to reach 1.` };
}

export const L7: LevelSpec = {
  id: 'L7',
  title: 'Read the cat',
  minutes: 7,
  concept: {
    text: 'To read 0 or 1 without a transmon, nudge the memory with a small drive ε_Z. The buffer field then leans opposite ways for the two valleys.',
    narrationKey: 'L7',
  },
  predict: {
    question: 'After switching the readout on, the buffer signal…',
    options: [
      opt('A', 'Settles smoothly', false, {
        misconception: 'M6',
        feedback: 'It actually rings for about 1 µs. Reading takes time.',
      }),
      opt('B', 'Rings, then settles', true),
      opt('C', 'Stays zero', false, {
        feedback: 'The two valleys push the buffer opposite ways, so there is a signal.',
      }),
    ],
  },
  controls: [
    {
      name: 'eps',
      label: 'Readout ε_Z',
      type: 'range',
      min: 0.05,
      max: 3,
      step: 0.01,
      initial: 0.2,
      unit: 'g₂',
      snap: READOUT_GRID,
    },
    {
      name: 'valley',
      label: 'Valley',
      type: 'select',
      initial: '0',
      options: [
        { value: '0', label: 'Valley 0' },
        { value: '1', label: 'Valley 1' },
      ],
    },
  ],
  sim: {
    engine: 'records',
    request: (state) => ({ eps: Number(state.params.eps ?? 0.2), alpha: 2.1, valley: state.params.valley ?? '0' }),
  },
  views: [
    { kind: 'b_iq', label: 'Buffer IQ' },
    { kind: 'n_t', label: 'Re and Im' },
    { kind: 'snr', label: 'SNR and cost' },
  ],
  check: { goal: 'Get an SNR ≥ 1 within 1 µs.', fn: check },
  aha: 'It rings at 3.14 MHz and needs about 1.1 µs to settle, because memory and buffer form a lightly damped pair (8g₂α > κ_b).\nReading costs something. Measuring dephases the qubit at 2ε_Z²/(κ₂α²), so harder driving reads faster but disturbs the cat.',
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [3.14, 1.13, 0.73, 2.46],
  solution: ['b_ss = ∓ε_Z/(2α g₂).', 'λ² + (κ_b/2)λ + 4 g₂² α² = 0, giving λ = −4.08 ± 19.7i /µs.'],
  hints: ['Predict.', 'Watch the first 0.5 µs.', 'Compare the two valleys.', 'Signal size goes as ε_Z/(2αg₂).'],
  preset: 'L7',
  sources: ['t2_3.* records'],
};
