import { afterEach, describe, expect, it, vi } from 'vitest';
import { H2PH_CORRECT_PYTHON } from '../levels/L6';
import { L6_NOT_YOURS, runLevelSim } from '../sources';
import type { LevelSpec } from '../types';

const serverSpec = {
  id: 'L2',
  preset: 'L2',
  sim: { engine: 'server-two-mode', request: () => ({}) },
} as unknown as LevelSpec;

const l6Spec = {
  id: 'L6',
  preset: 'L6',
  sim: { engine: 'server-expr', request: () => ({}) },
} as unknown as LevelSpec;

const tsSpec = {
  id: 'L1',
  preset: 'L1',
  sim: { engine: 'ts', request: () => ({}) },
} as unknown as LevelSpec;

afterEach(() => {
  vi.useRealTimers();
});

describe('source fallback', () => {
  it('uses a preset when a server fetch never resolves', async () => {
    vi.useFakeTimers();
    const pending = runLevelSim(serverSpec, { params: {} }, {
      deps: {
        apiBase: 'http://example.test',
        fetchImpl: () => new Promise(() => {}),
        presets: [{ id: 'L2', levelId: 'L2', source: 'precomputed', params: {}, result: { tUs: [0], n: [1], summary: 'preset' } }],
      },
    });
    await vi.advanceTimersByTimeAsync(3000);
    const out = await pending;
    expect(out.source).toBe('preset');
    expect(out.badge).toBe('Precomputed');
    expect(out.banner).toBeTruthy();
  });

  it('waits 15s on L6, reports progress, then shows the reference build', async () => {
    vi.useFakeTimers();
    const progress: number[] = [];
    const pending = runLevelSim(l6Spec, { params: {} }, {
      onProgress: (update) => progress.push(update.fraction),
      deps: { apiBase: 'http://example.test', fetchImpl: () => new Promise(() => {}) },
    });
    await vi.advanceTimersByTimeAsync(15000);
    const out = await pending;
    expect(progress.length).toBeGreaterThan(0);
    expect(out.presetId).toBe('correct');
    expect(out.banner).toBe(L6_NOT_YOURS);
  });

  it('falls straight through to a preset when fetch rejects', async () => {
    const out = await runLevelSim(serverSpec, { params: {} }, {
      deps: {
        apiBase: 'http://example.test',
        fetchImpl: () => Promise.reject(new Error('offline')),
        presets: [{ id: 'L2', levelId: 'L2', source: 'precomputed', params: {}, result: { tUs: [0], n: [1] } }],
      },
    });
    expect(out.source).toBe('preset');
    expect(out.badge).toBe('Precomputed');
  });

  it('does not fetch when VITE_API_BASE is unset', async () => {
    const fetchImpl = vi.fn();
    await runLevelSim(serverSpec, { params: {} }, { deps: { fetchImpl } });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it.each([
    ['drive_on_memory_not_buffer', 'eps_z_drive_wrong'],
    ['no_dissipation', 'missing_kappa_b'],
    ['wrong_conversion', 'a_bd2_wrong'],
  ])('maps %s to %s after the live expr call fails', async (key, presetId) => {
    const fetchImpl = vi.fn(() => Promise.reject(new Error('offline')));
    const out = await runLevelSim(l6Spec, { params: {}, tree: { op: 'x' } }, {
      deps: { apiBase: 'http://example.test', fetchImpl: fetchImpl as unknown as typeof fetch, detect: () => [{ key }] },
    });
    expect(fetchImpl).toHaveBeenCalled();
    expect(String(fetchImpl.mock.calls[0]?.[0])).toContain('/api/sim/expr');
    expect(out.presetId).toBe(presetId);
  });

  it('does not fetch a known wrong build when the API is unset', async () => {
    const fetchImpl = vi.fn();
    const out = await runLevelSim(l6Spec, { params: {}, tree: { op: 'x' } }, {
      deps: { fetchImpl, detect: () => [{ key: 'no_dissipation' }] },
    });
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(out.presetId).toBe('missing_kappa_b');
  });

  it('uses the correct preset when the live expr call fails', async () => {
    const fetchImpl = vi.fn(() => Promise.reject(new Error('offline')));
    const out = await runLevelSim(l6Spec, { params: {}, tree: { op: 'h' } }, {
      deps: {
        apiBase: 'http://example.test',
        fetchImpl: fetchImpl as unknown as typeof fetch,
        detect: () => [],
        toPython: () => H2PH_CORRECT_PYTHON,
      },
    });
    expect(fetchImpl).toHaveBeenCalled();
    expect(out.presetId).toBe('correct');
  });

  it('keeps a live expr response and does not label it MOCK', async () => {
    const fetchImpl = vi.fn(async () => new Response(JSON.stringify({ t_us: [0, 2], na: [0, 4.41], meta: { engine: 'dynamiqs 0.3.7' } }), { status: 200 }));
    const out = await runLevelSim(l6Spec, { params: { build: 'correct' } }, {
      deps: { apiBase: 'http://example.test', fetchImpl: fetchImpl as unknown as typeof fetch },
    });
    expect(out.source).toBe('server');
    expect(out.badge).toBe('Live · Vultr dynamiqs');
    expect(out.badge).not.toBe('MOCK');
  });

  it('labels the in-browser fallback when nothing else is left', async () => {
    const out = await runLevelSim(tsSpec, { params: { alpha: 1 } }, {
      deps: { presets: [], runInWorker: () => Promise.reject(new Error('worker down')) },
    });
    expect(out.source).toBe('in-browser-fallback');
    expect(out.badge).toMatch(/In-browser/);
  });

  it('uses the in-browser solver when the worker rejects', async () => {
    const out = await runLevelSim(tsSpec, { params: { alpha: 2.1, state: 'coherent' } }, {
      deps: {
        runInWorker: () => Promise.reject(new Error('worker down')),
        simulate: () => ({ tUs: [0], n: [4.41], meta: { engine: 'ts-cn' } }),
      },
    });
    expect(out.source).toBe('ts');
    expect(out.badge).toMatch(/In-browser/);
    expect(out.badge).not.toBe('MOCK');
  });

  it('falls back to a preset when the worker and the solver both reject', async () => {
    const out = await runLevelSim(tsSpec, { params: { alpha: 2.1, state: 'coherent' } }, {
      deps: {
        runInWorker: () => Promise.reject(new Error('worker down')),
        simulate: () => { throw new Error('solver down'); },
      },
    });
    expect(out.source).toBe('preset');
    expect(out.presetId).toBeTruthy();
  });
});
