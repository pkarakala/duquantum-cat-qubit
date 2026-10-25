/** Physical constants for the in-browser solver.

Units are microseconds and rad/µs. The 2π that turns MHz into rad/µs is applied
only in this file, mirroring `src/config.py`.
*/
const TWO_PI = 2 * Math.PI;

export const G2 = TWO_PI * 0.763;
export const KAPPA_B = TWO_PI * 2.6;
export const KAPPA_A = TWO_PI * 9.3e-3;
export const ALPHA = 2.1;
export const EPS_D = ALPHA * ALPHA * G2;
export const KAPPA_2 = (4 * G2 * G2) / KAPPA_B;

/** Convert a frequency in MHz to a rate in rad/µs. 1 MHz = 1 cycle per µs. */
export function radPerUsFromMHz(freqMHz: number): number {
  return TWO_PI * freqMHz;
}
