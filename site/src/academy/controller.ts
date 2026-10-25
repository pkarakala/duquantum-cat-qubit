/**
 * The single API shared by the UI, P4's get_level_state tool, and the ElevenAgents client tools.
 */

import type { LevelRun } from './engine';
import { nextLevelId } from './levels';
import type { LevelId } from './types';

let active: LevelRun | null = null;
let onNavigate: ((id: LevelId) => void) | null = null;

export function bind(run: LevelRun | null, navigate?: (id: LevelId) => void): void {
  active = run;
  if (!run) {
    onNavigate = null;
    return;
  }
  if (navigate) onNavigate = navigate;
}

export function getLevelState() {
  const run = active;
  if (!run) {
    return { levelId: 'L1', params: {}, misconceptionIds: [], lastSim: { summary: '' }, hintLevel: 0 };
  }
  return {
    levelId: run.spec.id,
    params: run.params,
    ...(run.prediction ? { prediction: run.prediction } : {}),
    misconceptionIds: run.misconceptionIds,
    lastSim: { summary: run.lastResult?.result.summary ?? '' },
    hintLevel: run.hintLevel,
  };
}

export function setParam(name: string, value: number | string | boolean): void {
  active?.setParam(name, value);
}

export function runSim(): Promise<unknown> {
  if (!active) return Promise.resolve(null);
  return active.run();
}

export function showHint(level?: number): number {
  if (!active) return 0;
  if (typeof level === 'number') {
    while (active.hintLevel < Math.min(4, level)) active.showHint();
    return active.hintLevel;
  }
  return active.showHint();
}

export function nextLevel(): void {
  if (!active || !onNavigate) return;
  onNavigate(nextLevelId(active.spec.id));
}
