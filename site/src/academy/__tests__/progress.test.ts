// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
  vi.restoreAllMocks();
});

describe('progress', () => {
  it('issues a stable v4 learner id', async () => {
    const first = await import('../progress');
    const id = first.getLearnerId();
    expect(id).toMatch(UUID);
    vi.resetModules();
    const second = await import('../progress');
    expect(second.getLearnerId()).toBe(id);
  });

  it('persists a pass', async () => {
    const mod = await import('../progress');
    mod.saveProgress('L1', { passed: true, predictionCorrect: false, attempts: 2, ts: 10 });
    vi.resetModules();
    const again = await import('../progress');
    expect(again.getProgress().L1).toMatchObject({ passed: true, attempts: 2 });
  });

  it('falls back to memory when storage throws', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const mod = await import('../progress');
    expect(() => mod.getLearnerId()).not.toThrow();
    expect(mod.getLearnerId()).toMatch(UUID);
    expect(() => mod.saveProgress('L2', { passed: true, predictionCorrect: true, attempts: 1, ts: 1 })).not.toThrow();
    expect(mod.getProgress().L2?.passed).toBe(true);
  });
});
