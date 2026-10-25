/** L2 · a coherent state shrinks and stays round. */

import { ONE_MHZ } from '../formulas';
import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { opt } from './feedback';
import { param } from './metrics';
import { mul, num, sqrt, sym } from './trees';

const CODE = 'dq.mesolve(Delta*a.dag()@a, [jnp.sqrt(kappa)*a], dq.coherent(N, 2.0), t)';

function check(result: SimResultLike, state: LevelState) {
  void result;
  const kappa = Number(param(state, 'kappa'));
  if (kappa >= 1.32 - 1e-12 && kappa <= 1.46 + 1e-12) {
    return { pass: true, message: 'Pass. κ is in [1.32, 1.46] rad/µs, so ⟨n⟩ halves near t = 0.5 µs.' };
  }
  return { pass: false, message: 'Not yet. Halving needs κ · 0.5 = ln 2, so κ ≈ 1.386 rad/µs.' };
}

export const L2: LevelSpec = {
  id: 'L2',
  title: 'The leaky box',
  minutes: 6,
  concept: {
    text: 'Real resonators leak single photons at rate κ. The Hamiltonian H = Δ a†a makes the blob rotate. Here Δ/2π = 1 MHz, so one turn per µs. The jump operator √κ · a removes one photon at a time.',
    narrationKey: 'L2',
  },
  predict: {
    question: 'Start at α = 2 and turn on loss. What happens to the blob?',
    options: [
      opt('A', 'It shrinks and stays round', true),
      opt('B', 'It gets lopsided', false, { misconception: 'M3' }),
      opt('C', 'It splits in two', false),
      opt('D', 'Nothing', false),
    ],
  },
  controls: [
    { name: 'kappa', label: 'Loss κ', type: 'range', min: 0, max: ONE_MHZ, step: 0.001, initial: 0.4, unit: 'rad/µs' },
    {
      name: 'rotate',
      label: 'Rotate',
      type: 'toggle',
      initial: false,
    },
  ],
  sim: {
    engine: 'ts',
    request: (state) => {
      const rotate = state.params.rotate === true;
      const delta = rotate ? ONE_MHZ : 0;
      const kappa = Number(state.params.kappa ?? 0);
      return {
        params: {
          N: 30,
          alpha: 2,
          kappa2: 0,
          kappaA: 0,
          H: mul(num(delta), sym('n_a')),
          jumps: [mul(sqrt(num(kappa)), sym('a'))],
        },
        init: { kind: 'coherent', alpha: 2 },
        tEndUs: 1,
        nT: 201,
        outputs: ['n', 'wigner'],
        wignerTimes: Array.from({ length: 11 }, (_, i) => i * 0.1),
      };
    },
  },
  views: [
    { kind: 'n_t', label: 'Photon number' },
    { kind: 'wigner', label: 'Wigner spiral' },
  ],
  check: { goal: 'Pick κ so that ⟨n⟩ halves at t = 0.5 µs.', fn: check },
  aha: "A coherent state stays coherent while it leaks: losing a photon doesn't change it, it just shrinks. This matches our Task 1.0a check to 1e-11.",
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [4, 0.5, 1.386, 0.693],
  solution: ['⟨n⟩ = 4e^{−κt}.', 'Halving needs κt = ln 2.'],
  hints: [
    'Predict first.',
    'Look at the dashed analytic curve.',
    'Compare κ = 0 and a large κ.',
    'Set e^{−κ·0.5} = ½.',
  ],
  preset: 'L2',
  sources: ['t1_0.max_abs_error.td.one_mode.a2.00'],
};
