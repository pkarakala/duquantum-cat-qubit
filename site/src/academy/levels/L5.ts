/** L5 · bit flips and phase flips from verified records, or the offline snapshot. */

import type { LevelSpec, LevelState, RateGrid, SimResultLike } from '../types';
import { loadRateGrid } from '../data/records';
import { opt } from './feedback';
import { logLinear, param } from './metrics';

const CODE = 'gamma_x = spectral.gamma_x(H, jumps, Na, Nb)["gamma_x"]   # Liouvillian gap';

export function gridFrom(result: SimResultLike, state: LevelState): RateGrid | null {
  if (state.records?.gammaX?.length && state.records?.gammaZ?.length) return state.records;
  if (result.records?.gammaX?.length && result.records?.gammaZ?.length) return result.records;
  const model = String(param(state, 'model') ?? 'one_mode') === 'two_mode' ? 'two_mode' : 'one_mode';
  return loadRateGrid(model);
}

function check(result: SimResultLike, state: LevelState) {
  const alpha2 = Number(param(state, 'alpha2'));
  const grid = gridFrom(result, state);
  if (!grid) return { pass: false, message: 'Not yet. No verified data here.' };
  const gX = logLinear(grid.gammaX, alpha2);
  const gZ = logLinear(grid.gammaZ, alpha2);
  if (gX == null || gZ == null) {
    return { pass: false, message: 'Not yet. No verified data here — that α² is outside the record range, and the curves are not extrapolated.' };
  }
  const tX = 1 / gX;
  const tZ = 1 / gZ;
  if (tX > 1000 && tZ > 1) {
    return { pass: true, message: `Pass. T_X = ${tX.toFixed(0)} µs (> 1000) and T_Z = ${tZ.toFixed(3)} µs (> 1).` };
  }
  return {
    pass: false,
    message: `Not yet. T_X = ${tX.toFixed(1)} µs (need > 1000) and T_Z = ${tZ.toFixed(3)} µs (need > 1).`,
  };
}

export const L5: LevelSpec = {
  id: 'L5',
  title: 'Flip vs flip',
  minutes: 6,
  concept: {
    text: 'A bit flip means hopping from one valley to the other. Bigger cats sit in valleys that are farther apart, so bit flips become exponentially rarer. A phase flip happens every time a photon leaks. Bigger cats hold more photons, so phase flips grow linearly.',
    narrationKey: 'L5',
  },
  predict: {
    question: 'Double the photon number. Bit flips become…',
    options: [
      opt('A', 'About 2× rarer', false),
      opt('B', 'Vastly rarer, orders of magnitude', true),
      opt('C', 'More common', false, { misconception: 'M4' }),
    ],
  },
  predictFollowUp: {
    question: '…and phase flips?',
    options: [
      opt('less', 'less common', false),
      opt('more', 'more common', true),
    ],
  },
  controls: [
    { name: 'alpha2', label: 'Cat size α²', type: 'range', min: 1, max: 9, step: 0.01, initial: 1 },
    {
      name: 'model',
      label: 'Model',
      type: 'select',
      initial: 'one_mode',
      options: [
        { value: 'one_mode', label: 'One-mode' },
        { value: 'two_mode', label: 'Two-mode' },
      ],
    },
  ],
  sim: {
    engine: 'records',
    request: (state) => ({ model: state.params.model ?? 'one_mode', alpha2: Number(state.params.alpha2 ?? 1) }),
  },
  views: [
    { kind: 'rates_log', label: 'Lifetimes' },
    { kind: 'bias', label: 'Noise bias' },
    { kind: 'double_well', label: 'Double well' },
    { kind: 'wigner', label: 'Cat Wigner' },
  ],
  check: { goal: 'Design a qubit with T_X > 1 ms and T_Z > 1 µs.', fn: check },
  aha: "Noise bias is a design choice. That's why Alice & Bob only need a simple repetition code (Felis: 60–200× fewer qubits). Our two-mode model flips about 3× faster than the simple model at α = 2.1, which is real hardware physics (Ferrari et al. 2026).",
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [8.56, 1, 3, 60, 200],
  solution: [
    'Γ_X ≈ 2κ_a α² e^{−4α²} + (κ_a²/κ₂) e^{−2α²}.',
    'Γ_Z = 2κ_a α² coth 2α².',
    'Pick α² inside both bounds.',
  ],
  hints: ['Predict.', 'Read both curves at your α².', 'Try α² = 1 vs 5.', 'T_Z = 1/(2κ_aα²).'],
  preset: 'L5',
  sources: ['t2_1.gamma_x.eig.*', 't2_2.gamma_z.td.*'],
};
