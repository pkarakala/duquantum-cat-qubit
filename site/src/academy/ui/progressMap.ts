import type { LevelSpec } from '../types';
import { getProgress } from '../progress';

export function mountProgress(host: HTMLElement, current: LevelSpec, onJump: (id: LevelSpec['id']) => void): void {
  host.replaceChildren();
  const nav = document.createElement('nav');
  nav.className = 'progress-map';
  nav.setAttribute('aria-label', 'Levels');
  const progress = getProgress();
  const titles = ['A box of light', 'The leaky box', 'Two at a time', 'The cat appears', 'Flip vs flip', 'Build the machine', 'Read the cat', 'Design challenge'];
  titles.forEach((title, index) => {
    const id = `L${index + 1}` as LevelSpec['id'];
    const button = document.createElement('button');
    button.type = 'button';
    const passed = Boolean(progress[id]?.passed);
    button.textContent = passed ? `${id} ✓` : id;
    button.setAttribute('aria-label', `${id} ${title}${passed ? ', passed' : ', not passed'}`);
    if (id === current.id) button.setAttribute('aria-current', 'step');
    button.addEventListener('click', () => onJump(id));
    nav.append(button);
  });
  host.append(nav);
}
