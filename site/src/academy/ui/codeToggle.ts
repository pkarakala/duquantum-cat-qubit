import type { LevelState } from '../types';
import type { LevelSpec } from '../types';

export function mountCode(host: HTMLElement, spec: LevelSpec, state: () => LevelState): void {
  const details = document.createElement('details');
  details.className = 'code';
  const summary = document.createElement('summary');
  summary.textContent = 'Show the code';
  const pre = document.createElement('pre');
  const update = () => {
    try {
      pre.textContent = spec.showCode(state());
    } catch {
      pre.textContent = spec.codeFallback;
    }
  };
  details.addEventListener('toggle', update);
  update();
  details.append(summary, pre);
  host.append(details);
}
