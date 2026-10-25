/** L3 · pair loss freezes parity and leaves a 0/1 plateau. */

import { constants } from '../simAdapter';
import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { opt } from './feedback';
import { asNumbers, tailMean } from './metrics';
import { mul, num, pow, sqrt, sym } from './trees';

const CODE = 'dq.mesolve(dq.zeros(N), [jnp.sqrt(kappa_2)*a@a], dq.coherent(N, alpha), t)';

function check(result: SimResultLike, state: LevelState) {
  void state;
  const n = asNumbers(result.n);
  const t = asNumbers(result.tUs);
  if (!n.length) return { pass: false, message: 'Not yet. Run the pair-loss sim and read ⟨n⟩ at the end.' };
  const plateau = t.length === n.length ? n[n.length - 1]! : tailMean(t.length ? t : [0], n, 0);
  if (plateau >= 0.43 - 1e-12 && plateau <= 0.47 + 1e-12) {
    return { pass: true, message: 'Pass. The plateau sits in [0.43, 0.47].' };
  }
  return { pass: false, message: `Not yet. The plateau is ${plateau.toFixed(3)}. It should land in [0.43, 0.47] (α ≈ 1.07).` };
}

export const L3: LevelSpec = {
  id: 'L3',
  title: 'Two at a time',
  minutes: 6,
  concept: {
    text: 'What if the box can only lose photons in pairs? The jump operator is √κ₂ · a², where κ₂/2π = 0.896 MHz.',
    narrationKey: 'L3',
  },
  predict: {
    question: 'Start at α = 2 with pair-loss only. Where does ⟨n⟩ end up?',
    options: [
      opt('A', '0', false, { misconception: 'M3' }),
      opt('B', 'About 0.5', true),
      opt('C', 'It stays at 4', false),
      opt('D', '2', false),
    ],
  },
  controls: [
    { name: 'alpha', label: 'Start α', type: 'range', min: 0.5, max: 2.5, step: 0.01, initial: 2 },
    {
      name: 'scale',
      label: 'Pair loss κ₂',
      type: 'select',
      initial: '1',
      options: [
        { value: '0.25', label: '×¼' },
        { value: '1', label: '×1' },
        { value: '4', label: '×4' },
      ],
    },
  ],
  sim: {
    engine: 'ts',
    request: (state) => {
      const alpha = Number(state.params.alpha ?? 2);
      const scale = Number(state.params.scale ?? 1);
      const kappa2 = (constants()?.KAPPA_2 ?? 0) * scale;
      return {
        params: {
          N: 30,
          alpha,
          kappa2,
          kappaA: 0,
          H: num(0),
          jumps: [mul(sqrt(num(kappa2)), pow(sym('a'), 2))],
        },
        init: { kind: 'coherent', alpha },
        tEndUs: 3,
        nT: 301,
        outputs: ['n', 'parity'],
      };
    },
  },
  views: [
    { kind: 'n_t', label: 'Photon number' },
    { kind: 'histogram', label: 'Final Fock' },
    { kind: 'parity', label: 'Parity' },
  ],
  check: { goal: 'Make the plateau land at 0.45.', fn: check },
  aha: "Pairs can't remove the last odd photon. Photon-number **parity is frozen**. That is the secret ingredient of a cat qubit. (Our Task 1.0b plateau: 0.49983, which matches theory to 1e-14.)",
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [0.5, 0.49983, 0.45, 1.07, 0.896],
  solution: [
    'a² maps n → n−2, so parity is conserved.',
    'The odd part of |α⟩ ends in |1⟩ and the even part in |0⟩.',
    '⟨n⟩_∞ = P_odd = (1 − e^{−2α²})/2.',
  ],
  hints: ['Predict.', 'Watch the parity meter.', 'Try starting in Fock |3⟩: where does it end?', 'Use the plateau formula.'],
  preset: 'L3',
  sources: ['t1_0.n_plateau.td.one_mode.a2.00'],
};
