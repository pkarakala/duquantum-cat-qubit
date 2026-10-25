/** L8 · shape a readout pulse. Scoring uses linresp when P1 is present, else a labelled demo. */

import type { LevelSpec, LevelState, SimResultLike } from '../types';
import { opt } from './feedback';

const CODE = 'eps_bins, gain = linresp.optimal_pulse(R_b)';

function check(result: SimResultLike, state: LevelState) {
  const snr = state.snr ?? result.snr;
  const cost = state.cost ?? result.cost;
  const snrS = state.snrSquare ?? result.snrSquare;
  const costS = state.costSquare ?? result.costSquare;
  if (typeof snr !== 'number' || typeof cost !== 'number' || typeof snrS !== 'number' || typeof costS !== 'number') {
    return { pass: false, message: 'Not yet. Score your pulse against the square reference.' };
  }
  if (snr > snrS && cost <= costS + 1e-12) {
    return { pass: true, message: 'Pass. Your SNR beats the square, and the cost stays inside the square budget.' };
  }
  if (!(snr > snrS)) {
    return { pass: false, message: 'Not yet. The square itself does not win: SNR must be strictly higher at the same budget.' };
  }
  return { pass: false, message: 'Not yet. The pulse is over the square’s leakage budget. Fit it to the budget and score again.' };
}

export const L8: LevelSpec = {
  id: 'L8',
  title: 'Design challenge',
  minutes: 8,
  concept: {
    text: 'Design the readout pulse. You get 20 bars of drive strength over 1 µs. Maximize signal (SNR) without spending more than the bit-flip budget.',
    narrationKey: 'L8',
  },
  predict: {
    question: 'Which beats a flat (square) pulse at the same budget?',
    options: [
      opt('A', 'Nothing: square is best', false),
      opt('B', 'A shaped pulse', true),
      opt('C', 'A bigger square pulse', false),
    ],
  },
  controls: [{ name: 'pulse', label: 'Pulse bars', type: 'choice', initial: 'square' }],
  sim: {
    engine: 'ts',
    request: (state) => ({
      bins: state.bins ?? [],
      T: 1,
      nBins: 20,
    }),
  },
  views: [
    { kind: 'pulse', label: 'Pulse and spectrum' },
    { kind: 'snr', label: 'SNR against budget' },
    { kind: 'leaderboard', label: 'Leaderboard' },
  ],
  check: { goal: 'Beat the square pulse at equal budget.', fn: check },
  aha: "Our provably optimal pulse is the top singular vector of the system's response. It puts its energy near the 3.14 MHz ring. You just did optimal control.",
  showCode: () => CODE,
  codeFallback: CODE,
  allowedConstants: [3.14, 20, 1],
  solution: ['SNR = κ_b ∫|Δb|² dt.', 'Response is linear in ε.', 'Optimum = top singular vector at fixed energy.'],
  hints: ['Predict.', 'Look at the spectrum.', 'Try a ramp vs a square.', 'Put energy near the ring frequency.'],
  preset: 'L8',
  sources: ['t2_4c.* records'],
};
