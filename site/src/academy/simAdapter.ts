/**
 * P1, loaded if it has merged. Absent → the academy plays presets.
 * The glob is the contract: this file never edits site/src/sim.
 */

export interface SimConstants {
  G2: number;
  KAPPA_B: number;
  KAPPA_A: number;
  KAPPA_2: number;
  ALPHA: number;
  EPS_D?: number;
}

export interface LinrespApi {
  poles?: (...args: unknown[]) => unknown;
  response?: (...args: unknown[]) => { tUs: ArrayLike<number>; da: unknown; b: unknown };
  snr?: (tUs: ArrayLike<number>, deltaB: unknown, kappaB: number) => number;
  leakageProxy?: (tUs: ArrayLike<number>, da: unknown) => number;
  optimalPulse?: (nBins: number, T: number, g2?: number, kappaB?: number, alpha?: number) => { epsBins: number[]; gain?: number };
}

interface SimModule {
  simulate?: (req: unknown) => unknown;
  runInWorker?: (req: unknown) => Promise<unknown>;
  wigner?: (...args: unknown[]) => unknown;
  linresp?: LinrespApi;
  C?: SimConstants;
}

const modules = import.meta.glob('../sim/index.ts', { eager: true }) as Record<string, SimModule>;
const sim = Object.values(modules)[0];

export function simPresent(): boolean {
  return Boolean(sim?.simulate || sim?.runInWorker);
}

export function constants(): SimConstants | null {
  const C = sim?.C;
  if (!C || typeof C.G2 !== 'number' || typeof C.KAPPA_2 !== 'number') return null;
  return C;
}

export function linrespApi(): LinrespApi | null {
  return sim?.linresp ?? null;
}

export async function runInWorker(req: unknown): Promise<unknown> {
  if (!sim?.runInWorker) throw new Error('P1 runInWorker is not available');
  return sim.runInWorker(req);
}

export function simulate(req: unknown): unknown {
  if (!sim?.simulate) throw new Error('P1 simulate is not available');
  return sim.simulate(req);
}

export function wignerFn(): SimModule['wigner'] | null {
  return sim?.wigner ?? null;
}
