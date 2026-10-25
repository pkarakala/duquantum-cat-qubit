/**
 * Fallback chain from CONTRACT §3.
 * Every network call has a timeout. No VITE_API_BASE means no fetch at all.
 */

import { getPreset as blockPreset } from '../blocks/presets';
import { EPS_D, G2, KAPPA_A, KAPPA_B } from '../sim/config';
import { detectTree, toPythonTree } from './blocksAdapter';
import { recordFile, recordOrigin } from './data/records';
import { H2PH_CORRECT_PYTHON, BUILD_KEYS } from './levels/L6';
import { scorePulse } from './l8score';
import { allPresets, getPreset, nearestPreset } from './presets';
import { runInWorker as workerAdapter, simulate as simulateAdapter } from './simAdapter';
import type { LevelSpec, LevelState, PresetEntry, RunOutcome, SimResultLike } from './types';

export const BADGE_BROWSER = 'In-browser sim · validated vs dynamiqs';
export const BADGE_LIVE = 'Live · Vultr dynamiqs';
export const BADGE_PRECOMPUTED = 'Precomputed';
export const BADGE_RECORDS = 'Verified records';
export const BADGE_MOCK = 'MOCK';

export const L6_NOT_YOURS = 'Live run unavailable: showing the reference build, not yours';

const WRONG_BUILD: Record<string, string> = {
  drive_on_memory_not_buffer: 'eps_z_drive_wrong',
  no_dissipation: 'missing_kappa_b',
  wrong_conversion: 'a_bd2_wrong',
};

export interface SourceDeps {
  apiBase?: string;
  fetchImpl?: typeof fetch;
  runInWorker?: (req: unknown) => Promise<unknown>;
  simulate?: (req: unknown) => unknown;
  detect?: (tree: unknown) => { key: string; message?: string }[];
  toPython?: (tree: unknown) => string;
  presets?: PresetEntry[];
}

export interface RunOpts {
  onProgress?: (update: { fraction: number; message: string }) => void;
  signal?: AbortSignal;
  deps?: SourceDeps;
}

function withTimeout<T>(work: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('timeout')), ms);
    work.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

function apiBaseOf(deps?: SourceDeps): string | undefined {
  if (deps && Object.prototype.hasOwnProperty.call(deps, 'apiBase')) {
    const base = deps.apiBase?.replace(/\/$/, '');
    return base || undefined;
  }
  const fromEnv = import.meta.env?.VITE_API_BASE;
  return fromEnv ? fromEnv.replace(/\/$/, '') : undefined;
}

function catalog(deps?: SourceDeps): PresetEntry[] {
  return deps?.presets ?? allPresets();
}

function badgeFor(preset?: PresetEntry, kind: 'preset' | 'records' = 'preset'): string {
  if (preset?.source === 'mock' || preset?.result?.meta?.source === 'mock') return BADGE_MOCK;
  return kind === 'records' ? BADGE_RECORDS : BADGE_PRECOMPUTED;
}

function fromPreset(entry: PresetEntry, extra?: Partial<RunOutcome>): RunOutcome {
  return {
    result: entry.result,
    source: 'preset',
    badge: badgeFor(entry),
    presetId: entry.id,
    ...extra,
  };
}

function labelledFallback(banner: string): RunOutcome {
  return {
    result: { tUs: [0], n: [0], summary: 'In-browser fallback has no solver loaded.' },
    source: 'in-browser-fallback',
    badge: BADGE_BROWSER,
    banner,
  };
}

function pythonOf(state: LevelState, deps?: SourceDeps): string | null {
  if (deps?.toPython && state.tree != null) return deps.toPython(state.tree);
  if (typeof state.python === 'string') return state.python;
  if (state.tree != null) return toPythonTree(state.tree);
  return null;
}

function isCorrectPython(value: string | null): boolean {
  if (!value) return false;
  const norm = value.replace(/^H\s*=\s*/, '').replace(/\s+/g, '');
  return norm === H2PH_CORRECT_PYTHON.replace(/\s+/g, '');
}

function detectKeys(state: LevelState, deps?: SourceDeps): string[] {
  if (state.detectKeys?.length) return state.detectKeys;
  const detect = deps?.detect ?? detectTree;
  if (state.tree == null) return [];
  return detect(state.tree).map((hit) => hit.key);
}

async function postJson(url: string, body: unknown, deps: SourceDeps | undefined, ms: number, onProgress?: RunOpts['onProgress']): Promise<unknown> {
  const doFetch = deps?.fetchImpl ?? globalThis.fetch.bind(globalThis);
  onProgress?.({ fraction: 0.08, message: 'Waiting for the live run…' });
  const pulse = setInterval(() => onProgress?.({ fraction: 0.4, message: 'Still waiting…' }), 1000);
  try {
    const response = await withTimeout(
      doFetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }),
      ms,
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearInterval(pulse);
  }
}

/** The API speaks snake_case (t_us, top2_a/top_b series); the site reads tUs and meta.top2_a/top_b. */
function fromApi(body: unknown): SimResultLike {
  const r = (body ?? {}) as Record<string, unknown> & { meta?: Record<string, unknown> };
  if (r.tUs == null && Array.isArray(r.t_us)) r.tUs = r.t_us;
  const meta = (r.meta ??= {});
  for (const key of ['top2_a', 'top_b']) {
    const v = r[key];
    if (meta[key] == null && Array.isArray(v) && v.length) meta[key] = Math.max(...(v as number[]).map(Number));
  }
  return r as unknown as SimResultLike;
}

function l4LikeRequest(): unknown {
  return {
    params: { N: 30, alpha: 2.1, kappa2: 0, kappaA: 0 },
    init: { kind: 'vacuum' },
    tEndUs: 2,
    nT: 201,
    outputs: ['n', 'parity'],
  };
}

async function inBrowser(deps: SourceDeps | undefined, banner: string): Promise<RunOutcome> {
  const simulate = deps?.simulate ?? simulateAdapter;
  try {
    const result = (await Promise.resolve(simulate(l4LikeRequest()))) as SimResultLike;
    return { result, source: 'in-browser-fallback', badge: BADGE_BROWSER, banner };
  } catch {
    return labelledFallback(banner);
  }
}

const BUILD_TO_BLOCKS: Record<string, string> = {
  correct: 'h2ph_correct',
  missing_kappa_b: 'wrong_no_dissipation',
  eps_z_drive_wrong: 'wrong_drive_on_memory',
  a_bd2_wrong: 'wrong_conversion',
};

function exprBody(state: LevelState): Record<string, unknown> {
  const tree = (state.tree ?? {}) as { H?: unknown; jumps?: unknown };
  const build = typeof state.params.build === 'string' ? state.params.build : '';
  let H = tree.H ?? state.H ?? null;
  let jumps = tree.jumps ?? state.jumps ?? [];
  if (H == null && BUILD_TO_BLOCKS[build]) {
    try {
      const preset = blockPreset(BUILD_TO_BLOCKS[build]);
      H = preset.H;
      jumps = preset.jumps;
    } catch {
      /* The named build still has a preset fallback below. */
    }
  }
  return {
    H,
    jumps,
    params: { g2: G2, eps_d: EPS_D, kappa_b: KAPPA_B, kappa_a: KAPPA_A },
    modes: 'two',
    Na: 16,
    Nb: 5,
    init: 'vacuum',
    t_end_us: 2,
    n_t: 201,
    outputs: ['na', 'nb', 'top2_a', 'top_b'],
    level_id: 'L6',
  };
}

async function runTs(spec: LevelSpec, state: LevelState, opts: RunOpts): Promise<RunOutcome> {
  const deps = opts.deps;
  const rows = catalog(deps);
  const worker = deps?.runInWorker ?? workerAdapter;
  const simulate = deps?.simulate ?? simulateAdapter;
  const req = spec.sim.request(state);
  try {
    const result = (await withTimeout(Promise.resolve(worker(req)), 8000)) as SimResultLike;
    return { result, source: 'ts', badge: BADGE_BROWSER };
  } catch {
    try {
      const result = (await Promise.resolve(simulate(req))) as SimResultLike;
      return { result, source: 'ts', badge: BADGE_BROWSER };
    } catch {
      const nearest = nearestPreset(spec.id, state.params, rows) ?? getPreset(spec.preset, rows);
      if (nearest) {
        return fromPreset(nearest, { banner: 'In-browser sim unavailable: showing a precomputed preset.' });
      }
      return inBrowser(deps, 'effective one-mode model');
    }
  }
}

async function runServer(spec: LevelSpec, state: LevelState, opts: RunOpts, ms: number): Promise<RunOutcome> {
  const deps = opts.deps;
  const rows = catalog(deps);
  const base = apiBaseOf(deps);
  const nearest = nearestPreset(spec.id, state.params, rows) ?? getPreset(spec.preset, rows);
  if (!base) {
    if (nearest) return fromPreset(nearest, { banner: 'Offline: showing a precomputed preset.' });
    return inBrowser(deps, 'effective one-mode model');
  }
  try {
    const result = fromApi(await postJson(`${base}/api/sim/two_mode`, spec.sim.request(state), deps, ms, opts.onProgress));
    return { result, source: 'server', badge: BADGE_LIVE };
  } catch {
    if (nearest) return fromPreset(nearest, { banner: 'Live run timed out: showing a precomputed preset.' });
    return inBrowser(deps, 'effective one-mode model');
  }
}

async function runExpr(spec: LevelSpec, state: LevelState, opts: RunOpts): Promise<RunOutcome> {
  const deps = opts.deps;
  const rows = catalog(deps);
  const base = apiBaseOf(deps);
  if (base) {
    try {
      const result = fromApi(await postJson(`${base}/api/sim/expr`, exprBody(state), deps, 15000, opts.onProgress));
      return { result, source: 'server', badge: BADGE_LIVE };
    } catch {
      /* Named builds and the reference preset are the fallback. */
    }
  } else if (opts.onProgress) {
    opts.onProgress({ fraction: 1, message: 'Offline: skipping the live run.' });
  }
  const build = typeof state.params.build === 'string' ? state.params.build : '';
  if (build && getPreset(build, rows)) {
    const entry = getPreset(build, rows)!;
    return fromPreset(entry, { banner: entry.source === 'mock' ? 'Demo build: precomputed, not a live Vultr run.' : undefined });
  }
  const keys = detectKeys(state, deps);
  for (const key of keys) {
    const id = WRONG_BUILD[key];
    const entry = id ? getPreset(id, rows) : undefined;
    if (entry) return fromPreset(entry);
  }
  if (isCorrectPython(pythonOf(state, deps))) {
    const entry = getPreset('correct', rows) ?? getPreset(spec.preset, rows);
    if (entry) return fromPreset(entry);
  }
  const correct = getPreset('correct', rows) ?? getPreset(spec.preset, rows);
  if (correct) return fromPreset(correct, { banner: L6_NOT_YOURS });
  return inBrowser(deps, 'effective one-mode model');
}

function runRecords(spec: LevelSpec, state: LevelState, deps?: SourceDeps): RunOutcome {
  const rows = catalog(deps);
  const origin = recordOrigin();
  if (spec.id === 'L7') {
    const readout = recordFile('readout');
    if (readout) {
      const nearest = nearestPreset(spec.id, state.params, rows);
      return {
        result: { ...(nearest?.result ?? {}), summary: 'Readout grid' },
        source: 'records',
        badge: origin === 'live' ? BADGE_RECORDS : BADGE_MOCK,
        presetId: nearest?.id,
      };
    }
  }
  if (spec.id === 'L5' && recordFile('errors')) {
    const nearest = nearestPreset(spec.id, state.params, rows);
    return {
      result: nearest?.result ?? { summary: 'Rate records' },
      source: 'records',
      badge: origin === 'live' ? BADGE_RECORDS : BADGE_MOCK,
      presetId: nearest?.id,
    };
  }
  const nearest = nearestPreset(spec.id, state.params, rows) ?? getPreset(spec.preset, rows);
  if (nearest) return fromPreset(nearest);
  return labelledFallback('No records and no preset.');
}

function squareOf(rows: PresetEntry[]): { bins: number[]; snr: number } {
  const entry = getPreset('L8', rows) ?? getPreset('L8_square', rows);
  const bins = (entry?.result.squareBins as number[] | undefined) ?? Array.from({ length: 20 }, () => 1);
  const snr = typeof entry?.result.squareSnr === 'number' ? entry.result.squareSnr : 0.95;
  return { bins, snr };
}

function runL8(state: LevelState, deps?: SourceDeps): RunOutcome {
  const rows = catalog(deps);
  const square = squareOf(rows);
  const bins = (state.bins?.length ? state.bins : square.bins).slice(0, 20);
  while (bins.length < 20) bins.push(square.bins[bins.length] ?? 0);
  const score = scorePulse(bins, square.bins, square.snr);
  const preset = getPreset('L8', rows);
  return {
    result: {
      ...(preset?.result ?? {}),
      summary: score.mode === 'linresp' ? 'Scored with linresp.' : 'Demo score: linresp is not loaded. A flat pulse uses the square prototype; a shaped pulse is marked higher and still labelled MOCK.',
      snr: score.snr,
      cost: score.cost,
      snrSquare: score.snrSquare,
      costSquare: score.costSquare,
      bins,
      squareBins: square.bins,
      meta: { ...(preset?.result.meta ?? {}), scoreMode: score.mode, source: score.mode === 'demo' ? 'mock' : 'linresp' },
    },
    source: score.mode === 'linresp' ? 'ts' : 'preset',
    badge: score.mode === 'linresp' ? BADGE_BROWSER : BADGE_MOCK,
    banner: score.mode === 'demo' ? 'Local score (unverified): linresp is not loaded, so this is a demo comparison against the square prototype.' : undefined,
    presetId: 'L8',
  };
}

export async function runLevelSim(spec: Pick<LevelSpec, 'id' | 'preset' | 'sim'>, state: LevelState, opts: RunOpts = {}): Promise<RunOutcome> {
  if (spec.id === 'L8') return runL8(state, opts.deps);
  if (spec.sim.engine === 'ts') return runTs(spec as LevelSpec, state, opts);
  if (spec.sim.engine === 'server-expr') return runExpr(spec as LevelSpec, state, opts);
  if (spec.sim.engine === 'records') return runRecords(spec as LevelSpec, state, opts.deps);
  return runServer(spec as LevelSpec, state, opts, 3000);
}

export function buildDetectKeys(build: string): string[] {
  return BUILD_KEYS[build] ?? [];
}
