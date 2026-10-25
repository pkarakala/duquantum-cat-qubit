/** Preset catalog. Mock-labelled until P0's precomputed files are copied in. */

import type { LevelState, PresetEntry } from '../types';

const modules = import.meta.glob('./*.json', { eager: true, import: 'default' }) as Record<
  string,
  PresetEntry | PresetEntry[]
>;

function flatten(source: Record<string, PresetEntry | PresetEntry[]> = modules): PresetEntry[] {
  const out: PresetEntry[] = [];
  for (const mod of Object.values(source)) {
    if (Array.isArray(mod)) out.push(...mod);
    else if (mod && typeof mod === 'object' && 'id' in mod) out.push(mod);
  }
  return out;
}

let cache: PresetEntry[] | null = null;

export function allPresets(): PresetEntry[] {
  if (!cache) cache = flatten();
  return cache;
}

/** P0 preset name → level id. Built from the catalog so a renamed file still resolves. */
export function presetLevelMap(): Record<string, string> {
  const map: Record<string, string> = {};
  for (const entry of allPresets()) map[entry.id] = entry.levelId;
  return map;
}

export function getPreset(id: string, catalog: PresetEntry[] = allPresets()): PresetEntry | undefined {
  return catalog.find((entry) => entry.id === id);
}

function numeric(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'boolean') return value ? 1 : 0;
  if (typeof value === 'string' && value !== '' && Number.isFinite(Number(value))) return Number(value);
  return null;
}

/**
 * Entry that minimises Σ ((p − q) / range)².
 * Non-numeric params (state, loss, model) must match when both sides set them.
 */
export function nearestPreset(levelId: string, params: LevelState['params'] | Record<string, unknown>, catalog = allPresets()): PresetEntry | null {
  let rows = catalog.filter((entry) => entry.levelId === levelId);
  if (!rows.length) return null;
  for (const key of ['state', 'loss', 'model', 'build']) {
    const wanted = params[key];
    if (wanted == null) continue;
    const matched = rows.filter((entry) => entry.params[key] == null || entry.params[key] === wanted);
    if (matched.length) rows = matched;
  }
  let best = rows[0]!;
  let bestScore = Infinity;
  for (const row of rows) {
    let score = 0;
    let used = 0;
    const ranges = row.ranges ?? {};
    for (const [key, range] of Object.entries(ranges)) {
      const p = numeric(params[key]);
      const q = numeric(row.params[key]);
      if (p == null || q == null) continue;
      const span = range[1] - range[0] || 1;
      const d = (p - q) / span;
      score += d * d;
      used += 1;
    }
    if (!used) {
      for (const [key, raw] of Object.entries(row.params)) {
        const q = numeric(raw);
        const p = numeric(params[key]);
        if (q == null || p == null) continue;
        const d = p - q;
        score += d * d;
      }
    }
    if (score < bestScore) {
      bestScore = score;
      best = row;
    }
  }
  return best;
}
