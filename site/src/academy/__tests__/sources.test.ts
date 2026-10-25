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
  ])('maps %s to %s without a fetch', async (key, presetId) => {
    const fetchImpl = vi.fn(() => new Promise(() => {}));
    const out = await runLevelSim(l6Spec, { params: {}, tree: { op: 'x' } }, {
      deps: { apiBase: 'http://example.test', fetchImpl: fetchImpl as unknown as typeof fetch, detect: () => [{ key }] },
    });
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(out.presetId).toBe(presetId);
  });

  it('matches the correct python build without a fetch', async () => {
    const fetchImpl = vi.fn();
    const out = await runLevelSim(l6Spec, { params: {}, tree: { op: 'h' } }, {
      deps: {
        apiBase: 'http://example.test',
        fetchImpl,
        detect: () => [],
        toPython: () => H2PH_CORRECT_PYTHON,
      },
    });
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(out.presetId).toBe('correct');
  });

  it('labels the in-browser fallback when nothing else is left', async () => {
    const out = await runLevelSim(tsSpec, { params: { alpha: 1 } }, {
      deps: { presets: [], runInWorker: () => Promise.reject(new Error('worker down')) },
    });
    expect(out.source).toBe('in-browser-fallback');
    expect(out.badge).toMatch(/In-browser/);
  });

  it('falls back to a preset when the worker rejects', async () => {
    const out = await runLevelSim(tsSpec, { params: { alpha: 2.1, state: 'coherent' } }, {
      deps: { runInWorker: () => Promise.reject(new Error('worker down')) },
    });
    expect(out.source).toBe('preset');
    expect(out.presetId).toBeTruthy();
  });
});
