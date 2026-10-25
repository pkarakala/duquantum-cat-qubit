/**
 * Lab bundle: live wins over mock. A missing directory yields {}.
 * Presets are the next fallback, applied by the callers.
 */

import type { RateGrid, RatePoint } from '../types';
import { getPreset } from '../presets';

interface PointRow {
  alpha2?: number;
  value?: number;
  id?: string;
  model?: string;
}

interface ErrorsFile {
  gamma_x?: Record<string, PointRow[] | unknown>;
  gamma_z?: {
    td?: PointRow[];
    pred?: { alpha2?: number[]; value?: number[] };
    eig?: PointRow[];
  };
}

interface TradeRow {
  eps: number;
  snr: number;
  alpha?: number;
  gammaXRel?: number;
  id?: string;
}

const bundled = import.meta.glob('../../data/{live,mock}/*.json', {
  eager: true,
  import: 'default',
}) as Record<string, unknown>;

function bucket(): { live: Record<string, unknown>; mock: Record<string, unknown> } {
  const live: Record<string, unknown> = {};
  const mock: Record<string, unknown> = {};
  for (const [path, data] of Object.entries(bundled)) {
    const name = path.split('/').pop()?.replace(/\.json$/, '') ?? path;
    if (path.includes('/live/')) live[name] = data;
    else mock[name] = data;
  }
  return { live, mock };
}

export function recordOrigin(): 'live' | 'mock' | 'none' {
  const { live, mock } = bucket();
  if (Object.keys(live).length) return 'live';
  if (Object.keys(mock).length) return 'mock';
  return 'none';
}

export function recordFile(name: string): unknown {
  const { live, mock } = bucket();
  return live[name] ?? mock[name];
}

function pointsFromRows(rows: PointRow[] | undefined): RatePoint[] {
  if (!Array.isArray(rows)) return [];
  return rows
    .filter((row) => typeof row.alpha2 === 'number' && typeof row.value === 'number')
    .map((row) => ({ alpha2: row.alpha2 as number, gamma: row.value as number, id: row.id }));
}

function gridFromErrors(errors: ErrorsFile, model: 'one_mode' | 'two_mode'): RateGrid | null {
  const gx = errors.gamma_x?.[model];
  const gammaX = pointsFromRows(Array.isArray(gx) ? gx : undefined);
  let gammaZ: RatePoint[] = [];
  if (model === 'two_mode' && Array.isArray(errors.gamma_z?.td)) {
    gammaZ = pointsFromRows(errors.gamma_z?.td);
  }
  if (!gammaZ.length && errors.gamma_z?.pred?.alpha2 && errors.gamma_z.pred.value) {
    gammaZ = errors.gamma_z.pred.alpha2.map((alpha2, i) => ({
      alpha2,
      gamma: errors.gamma_z!.pred!.value![i] ?? NaN,
      id: 'gamma_z.pred',
    })).filter((p) => Number.isFinite(p.gamma));
  }
  if (!gammaX.length || !gammaZ.length) return null;
  return { gammaX, gammaZ };
}

export function loadRateGrid(model: 'one_mode' | 'two_mode'): RateGrid | null {
  const errors = recordFile('errors') as ErrorsFile | undefined;
  if (errors) {
    const grid = gridFromErrors(errors, model);
    if (grid) return grid;
  }
  const preset = getPreset('L5');
  const bag = preset?.result.recordsByModel as Record<string, RateGrid> | undefined;
  return bag?.[model] ?? (preset?.result.records as RateGrid | undefined) ?? null;
}

export function loadTradeoff(): TradeRow[] | null {
  const readout = recordFile('readout') as { tradeoff?: { eps_over_g2: number; snr_T1us: number; alpha?: number; gamma_x_rel?: number; id?: string }[] } | undefined;
  if (readout?.tradeoff?.length) {
    return readout.tradeoff.map((row) => ({
      eps: row.eps_over_g2,
      snr: row.snr_T1us,
      alpha: row.alpha,
      gammaXRel: row.gamma_x_rel,
      id: row.id,
    }));
  }
  const preset = getPreset('L7');
  return (preset?.result.tradeoff as TradeRow[] | undefined) ?? null;
}

export type { TradeRow };
