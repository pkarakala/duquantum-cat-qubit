/** Public academy API. P7 mounts this from its own routes.ts. */

import { bind, getLevelState, nextLevel, runSim, setParam, showHint } from './controller';
import { emit, on } from './events';
import { LEVELS } from './levels';
import { getLearnerId } from './progress';
import type { LevelId } from './types';
import { mountAcademy as mountShell, type AcademyHandle } from './ui/shell';

export { LEVELS, emit, getLearnerId, getLevelState, nextLevel, on, runSim, setParam, showHint };
export type { AcademyHandle, LevelId };

export function parseLevelHash(hash: string): LevelId | null {
  const match = hash.match(/L[1-8]/);
  return (match?.[0] as LevelId | undefined) ?? null;
}

export function mountAcademy(root: HTMLElement, opts?: { levelId?: LevelId; apiBase?: string }): AcademyHandle {
  const base = (opts?.apiBase || import.meta.env.VITE_API_BASE || '').replace(/\/$/, '');
  if (base) {
    const ctrl = new AbortController();
    const kill = window.setTimeout(() => ctrl.abort(), 3000);
    fetch(`${base}/api/health`, { signal: ctrl.signal })
      .catch(() => undefined)
      .finally(() => window.clearTimeout(kill));
  }
  const handle = mountShell(root, opts);
  return {
    navigate(levelId) {
      handle.navigate(levelId);
    },
    dispose() {
      handle.dispose();
      bind(null);
    },
  };
}
