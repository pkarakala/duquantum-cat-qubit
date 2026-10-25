import type { MisconceptionId, PredictOption } from '../types';

/** One-line fixes from LEVELS.md. Used when an option has an id and no feedback of its own. */
export const FIX: Record<MisconceptionId, string> = {
  M1: 'The fringes (negative regions) exist only for the superposition. A mixture shows two blobs and no stripes.',
  M2: 'It can go negative. Negativity is the quantum fingerprint.',
  M3: 'Engineered *two-photon* dissipation creates the cat and protects it.',
  M4: 'Bit flips drop exponentially, but phase flips grow linearly.',
  M5: 'It flips parity, which is a **phase** flip. The blob stays in its well.',
  M6: 'The buffer rings and takes about 1 µs to settle. Measuring dephases the qubit.',
  M7: 'C₊ and C₋ differ only by a sign, and their fringes (parity) are opposite.',
};

/** Wrong option with no misconception id (brief §6). */
export const NEUTRAL = 'Not quite: run it and watch.';

export const YES = "That's the one.";

export function opt(
  id: string,
  text: string,
  correct: boolean,
  extra?: { misconception?: MisconceptionId; feedback?: string },
): PredictOption {
  const misconception = extra?.misconception;
  const feedback = extra?.feedback ?? (correct ? YES : misconception ? FIX[misconception] : NEUTRAL);
  return misconception ? { id, text, correct, misconception, feedback } : { id, text, correct, feedback };
}
