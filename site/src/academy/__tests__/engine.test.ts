// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest';
import { createLevelRun } from '../engine';
import { resetListeners, on } from '../events';
import { L1 } from '../levels/L1';
import { L2 } from '../levels/L2';
import { getProgress } from '../progress';
import { mountRunButton } from '../ui/controls';

beforeEach(() => {
  resetListeners();
  localStorage.clear();
  document.body.innerHTML = '';
});

describe('level engine', () => {
  it('keeps Run closed until a prediction is chosen', () => {
    const run = createLevelRun(L1, { runSim: async () => ({ result: {}, source: 'preset', badge: 'MOCK' }) });
    const host = document.createElement('div');
    document.body.append(host);
    const button = mountRunButton(host, run);
    expect(run.canRun()).toBe(false);
    expect(button.disabled).toBe(true);
    expect(button.getAttribute('aria-disabled')).toBe('true');
    run.choose('B');
    expect(run.canRun()).toBe(true);
    expect(button.disabled).toBe(false);
    expect(button.getAttribute('aria-disabled')).toBe('false');
  });

  it('records the misconception on a wrong first choice, and still records an option with no id', () => {
    const predictions: { optionId?: string; misconceptionId?: string }[] = [];
    on('prediction', (payload) => predictions.push(payload as { optionId?: string; misconceptionId?: string }));
    const l2 = createLevelRun(L2);
    l2.choose('B');
    expect(predictions[0]?.misconceptionId).toBe('M3');
    expect(l2.misconceptionIds).toEqual(['M3']);
    const l1 = createLevelRun(L1);
    l1.choose('C');
    expect(predictions[1]?.optionId).toBe('C');
    expect(predictions[1]?.misconceptionId).toBeUndefined();
  });

  it('keeps only the first choice as the prediction', () => {
    const run = createLevelRun(L1);
    let count = 0;
    on('prediction', () => { count += 1; });
    run.choose('C');
    run.choose('B');
    expect(run.prediction?.optionId).toBe('C');
    expect(count).toBe(1);
  });

  it('emits check on every attempt and pass plus progress when it passes', async () => {
    const checks: unknown[] = [];
    const passes: { predictionCorrect?: boolean }[] = [];
    on('check', (payload) => checks.push(payload));
    on('pass', (payload) => passes.push(payload as { predictionCorrect?: boolean }));
    const run = createLevelRun(L1, { runSim: async () => ({ result: { tUs: [0], n: [4.41] }, source: 'preset', badge: 'MOCK' }) });
    run.choose('B');
    run.setParam('alpha', 2.1);
    run.setParam('state', 'coherent');
    await run.run();
    const verdict = run.check();
    expect(verdict.pass).toBe(true);
    expect(checks).toHaveLength(1);
    expect(passes[0]?.predictionCorrect).toBe(true);
    expect(getProgress().L1?.passed).toBe(true);
  });

  it('walks hints from 1 to 4 and hides the solution until two failed checks', () => {
    const hints: number[] = [];
    on('hint', (payload) => hints.push((payload as { hintLevel: number }).hintLevel));
    const run = createLevelRun(L1, { runSim: async () => ({ result: {}, source: 'preset', badge: 'MOCK' }) });
    expect([run.showHint(), run.showHint(), run.showHint(), run.showHint()]).toEqual([1, 2, 3, 4]);
    expect(hints).toEqual([1, 2, 3, 4]);
    run.choose('A');
    run.setParam('alpha', 0);
    run.check();
    expect(run.solutionVisible()).toBe(false);
    run.check();
    expect(run.failedChecks).toBe(2);
    expect(run.solutionVisible()).toBe(true);
  });
});
