/** L6 · build the two-mode machine. Live runs use a fixed 16×5 shape; presets cover the rest. */

import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { opt } from './feedback';
import { asNumbers, tailMean } from './metrics';

export const H2PH_CORRECT_PYTHON = 'g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())';
const CODE = `H = ${H2PH_CORRECT_PYTHON}`;

export const BUILD_KEYS: Record<string, string[]> = {
  correct: [],
  missing_kappa_b: ['no_dissipation'],
  eps_z_drive_wrong: ['drive_on_memory_not_buffer'],
  a_bd2_wrong: ['wrong_conversion'],
};

const TARGET = 4.41;

function check(result: SimResultLike, state: LevelState) {
  const keys = state.detectKeys ?? result.detectKeys ?? [];
  if (keys.length) {
    return { pass: false, message: 'Not yet. The blocks are not the stabilizing build. Read the feedback card.' };
  }
  const y = asNumbers(result.na ?? result.n);
  const t = asNumbers(result.tUs);
  if (!y.length) return { pass: false, message: 'Not yet. Run a build and read the steady memory population.' };
  const nss = t.length ? tailMean(t, y, 0.5) : y[y.length - 1]!;
  if (Math.abs(nss / TARGET - 1) <= 0.02 + 1e-9) {
    return { pass: true, message: 'Pass. Steady ⟨n_a⟩ is within 2% of 4.41, and the detector is quiet.' };
  }
  return { pass: false, message: `Not yet. Steady ⟨n_a⟩ = ${nss.toFixed(4)} (need |n/4.41 − 1| ≤ 0.02).` };
}

export const L6: LevelSpec = {
  id: 'L6',
  title: 'Build the machine',
  minutes: 8,
  concept: {
    text: 'In hardware, a second leaky resonator (the buffer, b) makes the pairs. The coupling g₂ swaps 2 memory photons for 1 buffer photon. A buffer drive ε_d pumps pairs in. Buffer loss κ_b dumps them. Build it from blocks.',
    narrationKey: 'L6',
  },
  predict: {
    question: 'Will the memory fill smoothly like L4?',
    options: [
      opt('A', 'Yes, smoothly', false),
      opt('B', 'It overshoots, then settles', true),
      opt('C', 'It never fills', false),
    ],
  },
  controls: [
    {
      name: 'build',
      label: 'Build',
      type: 'choice',
      initial: 'correct',
      options: [
        { value: 'correct', label: 'Correct H₂ph' },
        { value: 'missing_kappa_b', label: 'No √κ_b·b' },
        { value: 'eps_z_drive_wrong', label: 'ε(a+a†) drive' },
        { value: 'a_bd2_wrong', label: 'a·b†²' },
      ],
    },
  ],
  sim: {
    engine: 'server-expr',
    request: (state) => ({
      build: state.params.build ?? 'correct',
      tree: state.tree ?? null,
    }),
  },
  views: [
    { kind: 'blocks', label: 'Blocks' },
    { kind: 'n_t', label: 'Populations' },
    { kind: 'truncation', label: 'Truncation' },
    { kind: 'wigner', label: 'Wigner frames' },
  ],
  check: { goal: 'Your blocks stabilize a cat.', fn: check },
  aha: 'Real hardware overshoots by about 56%, because the buffer isn\'t fast enough (κ_b ≫ g₂ is violated: g₂/κ_b = 0.29).\nAnd the textbook simulation size (6 buffer levels) underestimates the peak by 11%. Convergence matters (our Task 1.2).',
  showCode: (state) => (typeof state.python === 'string' && state.python ? state.python : CODE),
  codeFallback: CODE,
  allowedConstants: [4.41, 56, 0.29, 11, 6.89, 1.07],
  solution: [
    'H = g₂(a²b† + a†²b) − ε_d(b+b†), with jumps √κ_b·b and √κ_a·a.',
    'α² = ε_d/g₂.',
    'A slow buffer causes the overshoot.',
  ],
  hints: [
    'Predict.',
    'Which block lets energy leave?',
    'Compare with/without √κ_b·b.',
    'Two memory photons ↔ one buffer photon: a²b†.',
  ],
  preset: 'L6',
  sources: ['t1_1.peak_na.td.two_mode.a2.10', 't1_1.steady_na.td.two_mode.a2.10'],
};
