import type { LevelRun } from '../engine';

export function mountHints(host: HTMLElement, run: LevelRun): { refresh: () => void } {
  host.replaceChildren();
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Hint';
  const list = document.createElement('ol');
  const solution = document.createElement('div');
  solution.className = 'solution';
  solution.hidden = true;
  const title = document.createElement('h3');
  title.textContent = 'Full solution';
  const steps = document.createElement('ol');
  for (const step of run.spec.solution) {
    const item = document.createElement('li');
    item.textContent = step;
    steps.append(item);
  }
  solution.append(title, steps);
  button.addEventListener('click', () => {
    run.showHint();
    refresh();
  });
  host.append(button, list, solution);

  function refresh() {
    list.replaceChildren();
    for (let i = 0; i < run.hintLevel; i++) {
      const item = document.createElement('li');
      item.textContent = run.spec.hints[i] ?? '';
      list.append(item);
    }
    solution.hidden = !run.solutionVisible();
  }
  return { refresh };
}
