/** L4 · vacuum plus pair exchange grows the even cat. */

import { constants } from '../simAdapter';
import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { FIX, opt } from './feedback';
import { asNumbers, nearestIndex } from './metrics';

const CODE = 'jumps = [jnp.sqrt(kappa_2)*(a@a - alpha**2*dq.eye(N)), jnp.sqrt(kappa_a)*a]';

function part1(result: SimResultLike, state: LevelState) {
  const loss = state.params?.loss === 'on' || state.params?.loss === true;
  if (loss) {
    return { pass: false, message: 'Not yet. Part 1 asks for loss off. The exaggerated loss is for the follow-up.' };
  }
  const t = asNumbers(result.tUs);
  const n = asNumbers(result.n);
  const parity = asNumbers(result.parity);
  if (!t.length || !n.length || !parity.length) {
    return { pass: false, message: 'Not yet. Run with loss off, then read ⟨n⟩ and parity at 1 µs.' };
  }
  const i = nearestIndex(t, 1);
  const n1 = n[Math.min(i, n.length - 1)]!;
  const p1 = parity[Math.min(i, parity.length - 1)]!;
  if (n1 >= 4.3 - 1e-12 && n1 <= 4.5 + 1e-12 && p1 > 0.9) {
    return { pass: true, message: 'Pass. At 1 µs, ⟨n⟩ is in [4.3, 4.5] and parity is above 0.9.' };
  }
  return {
    pass: false,
    message: `Not yet. At the save nearest 1 µs, ⟨n⟩ = ${n1.toFixed(3)} (want 4.3–4.5) and parity = ${p1.toFixed(3)} (must be > 0.9).`,
  };
}

function part2(answer: string) {
  const ok = /fringes/i.test(answer) && /parity/i.test(answer);
  return ok
    ? { pass: true, message: 'Pass. The fringes and the parity fade first: losing one photon is a phase flip.' }
    : { pass: false, message: 'Not yet. Watch the stripes and the parity meter. The blobs stay put.' };
}

export const L4: LevelSpec = {
  id: 'L4',
  title: 'The cat appears',
  minutes: 7,
  concept: {
    text: 'Remove pairs and add pairs. The jump operator becomes √κ₂ (a² − α²). It is balanced at ±α: two valleys, which are our |0⟩ and |1⟩. Start from the empty box.',
    narrationKey: 'L4',
  },
  predict: {
    question: 'Starting empty, what will the Wigner map look like?',
    options: [
      opt('A', 'One blob', false),
      opt('B', 'Two blobs, no stripes', false, { misconception: 'M1' }),
      opt('C', 'Two blobs plus stripes between them', true),
      opt('D', 'A ring', false),
    ],
  },
  controls: [
    { name: 'alpha', label: 'Cat size α', type: 'range', min: 1, max: 2.5, step: 0.01, initial: 1.5 },
    {
      name: 'loss',
      label: 'Photon loss',
      type: 'select',
      initial: 'off',
      options: [
        { value: 'off', label: 'Off' },
        { value: 'on', label: 'On ×20' },
      ],
    },
    { name: 'mixture', label: '50/50 mixture', type: 'toggle', initial: false, revealAtHint: 3 },
  ],
  sim: {
    engine: 'ts',
    request: (state) => {
      const alpha = Number(state.params.alpha ?? 2.1);
      const lossOn = state.params.loss === 'on';
      const C = constants();
      const kappa2 = C?.KAPPA_2 ?? 0;
      const kappaA = lossOn ? 20 * (C?.KAPPA_A ?? 0) : 0;
      const times: number[] = [];
      for (let t = 0; t <= 2.0001; t += 0.1) times.push(Math.round(t * 10) / 10);
      return {
        params: { N: 30, alpha, kappa2, kappaA, epsZ: 0, epsX: 0 },
        init: { kind: 'vacuum' },
        tEndUs: 2,
        nT: 201,
        outputs: ['n', 'parity', 'wigner'],
        wignerTimes: times,
      };
    },
  },
  views: [
    { kind: 'wigner', label: 'Wigner movie' },
    { kind: 'n_t', label: 'Photon number' },
    { kind: 'parity', label: 'Parity' },
  ],
  check: {
    goal: 'Grow a cat with ⟨n⟩ ≈ 4.41 and parity > 0.9 at t = 1 µs, with loss off.',
    fn: part1,
  },
  checkFollowUp: {
    question: 'Turn loss on. What fades first?',
    options: [
      opt('fringes', 'the fringes and the parity', true, {
        feedback: 'The stripes and the parity go first. The blobs stay: a phase flip, not a bit flip.',
      }),
      opt('blobs', 'the two blobs', false, { feedback: FIX.M5 }),
    ],
    fn: part2,
  },
  checkParts: [{ goal: 'Turn loss on. What fades first?', fn: (_r, state) => part2(String(state.params?.followUp ?? '')) }],
  aha: 'The stripes go negative, so this is a true superposition: an even cat (M1, M2).\nThe empty box is even, so you always get the *even* cat (M7).\nLosing one photon flips parity: that\'s a **phase flip**, not a bit flip (M5).',
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [4.41, 0.9, 1],
  solution: [
    'Pair processes conserve parity, and vacuum has P = +1, so the state goes to C₊.',
    'With κ_a on, parity decays at about 2κ_a α².',
  ],
  hints: ['Predict.', 'Look between the blobs.', 'Compare a 50/50 mixture (toggle).', 'Parity = +1 means even photon numbers only.'],
  preset: 'L4',
  sources: ['t1_3a.gamma_z.td.two_mode.a2.10', 't1_0.final_n.td.one_mode.a2.10'],
};
