/** L1 · a coherent state is a blob, and the photon count is Poisson. */

import { constants } from '../simAdapter';
import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { opt } from './feedback';
import { param } from './metrics';

const CODE = 'psi = dq.coherent(30, alpha)';

function check(result: SimResultLike, state: LevelState) {
  void result;
  const kind = String(param(state, 'state') ?? 'coherent');
  if (kind === 'fock') {
    return { pass: false, message: 'A Fock state has one definite count. The goal is an average of 4.41, which a coherent state has.' };
  }
  const alpha = Math.abs(Number(param(state, 'alpha')));
  if (alpha >= 2.08 - 1e-12 && alpha <= 2.12 + 1e-12) {
    return { pass: true, message: 'Pass. |α| is in [2.08, 2.12], so ⟨n⟩ = |α|² is about 4.41.' };
  }
  return { pass: false, message: 'Not yet. ⟨n⟩ = |α|². Move α until it sits between 2.08 and 2.12.' };
}

export const L1: LevelSpec = {
  id: 'L1',
  title: 'A box of light',
  minutes: 5,
  concept: {
    text: 'A superconducting resonator holds microwave photons. A coherent state |α⟩ is the quantum version of a steady swing. Its average photon number is |α|², but each measurement gives a different count. The Wigner map shows it as a round blob at distance α from the centre.',
    narrationKey: 'L1',
  },
  predict: {
    question: 'For α = 2, what is the average number of photons?',
    options: [
      opt('A', '2', false, { feedback: 'Close, but the photon number goes as α².' }),
      opt('B', '4', true),
      opt('C', 'Exactly 4, every time', false, { feedback: 'On average 4, but each count varies (Poisson).' }),
      opt('D', '0', false),
    ],
  },
  controls: [
    { name: 'alpha', label: 'Amplitude α', type: 'range', min: 0, max: 3, step: 0.01, initial: 2, unit: '' },
    {
      name: 'state',
      label: 'State',
      type: 'select',
      initial: 'coherent',
      options: [
        { value: 'coherent', label: 'Coherent' },
        { value: 'fock', label: 'Fock n' },
      ],
    },
    { name: 'n', label: 'Fock n', type: 'range', min: 0, max: 6, step: 1, initial: 1, visibleWhen: 'state', visibleValue: 'fock' },
  ],
  sim: {
    engine: 'ts',
    request: (state) => {
      const alpha = Number(state.params.alpha ?? 2);
      const kind = state.params.state === 'fock' ? 'fock' : 'coherent';
      const n = Number(state.params.n ?? 0);
      return {
        params: { N: 30, alpha, kappa2: 0, kappaA: 0 },
        init: kind === 'fock' ? { kind: 'fock', n } : { kind: 'coherent', alpha },
        tEndUs: 0,
        nT: 1,
        outputs: ['n', 'wigner'],
        nominal: constants(),
      };
    },
  },
  views: [
    { kind: 'histogram', label: 'Photon counts' },
    { kind: 'wigner', label: 'Wigner map' },
  ],
  check: { goal: 'Make a state with an average of 4.41 photons.', fn: check },
  aha: 'Amplitude and phase are sharp; the photon count is fuzzy. That round blob *is* a coherent state, and α = 2.1 is Alice & Bob\'s operating point.',
  showCode: (state) => `psi = dq.coherent(30, ${Number(state.params.alpha ?? 0)})`,
  codeFallback: CODE,
  allowedConstants: [2.1, 4.41, 4],
  solution: ['⟨n⟩ = |α|².', '4.41 = 2.1².'],
  hints: [
    'What do you predict?',
    "Watch the histogram's centre as you move α.",
    'Compare α = 1 and α = 2.',
    '⟨n⟩ = α²: solve α² = 4.41.',
  ],
  preset: 'L1',
  sources: ['challenge prompt §B.3–B.5'],
};
