import { ONE_MHZ } from '../formulas';
import type { LevelRun } from '../engine';
import type { Control } from '../types';

function visible(control: Control, run: LevelRun): boolean {
  if ((control.revealAtHint ?? 0) > run.hintLevel) return false;
  if (control.visibleWhen && String(run.params[control.visibleWhen]) !== control.visibleValue) return false;
  return true;
}

export function mountRunButton(parent: HTMLElement, run: LevelRun, label = 'Run', onClick?: () => void): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'run';
  button.textContent = label;
  button.setAttribute('aria-label', label);
  const sync = () => {
    const ok = run.canRun();
    button.disabled = !ok;
    button.setAttribute('aria-disabled', ok ? 'false' : 'true');
  };
  sync();
  run.subscribe(sync);
  button.addEventListener('click', () => {
    if (!run.canRun()) return;
    if (onClick) onClick();
    else void run.run();
  });
  parent.append(button);
  return button;
}

export function mountControls(host: HTMLElement, run: LevelRun, onEdit: () => void): () => void {
  host.replaceChildren();
  const rows: { control: Control; wrap: HTMLElement }[] = [];
  for (const control of run.spec.controls) {
    if (control.name === 'pulse') continue;
    const wrap = document.createElement('div');
    wrap.className = 'control';
    const id = `${run.spec.id}-${control.name}`;
    if (control.type === 'range') {
      const label = document.createElement('label');
      label.htmlFor = id;
      label.textContent = control.label;
      const input = document.createElement('input');
      input.id = id;
      input.type = 'range';
      input.min = String(control.min ?? 0);
      input.max = String(control.max ?? 1);
      input.step = String(control.step ?? 0.01);
      input.value = String(run.params[control.name] ?? control.min ?? 0);
      const read = document.createElement('output');
      read.htmlFor = id;
      const paint = () => {
        let value = Number(input.value);
        if (control.snap?.length) {
          value = control.snap.reduce((best, item) => (Math.abs(item - value) < Math.abs(best - value) ? item : best));
          input.value = String(value);
        }
        const unit = control.unit ? ` ${control.unit}` : '';
        const mhz = control.name === 'kappa' ? ` · ${(value / ONE_MHZ).toFixed(3)} MHz` : '';
        read.textContent = `${value.toFixed(control.step && control.step >= 1 ? 0 : 3)}${unit}${mhz}`;
      };
      paint();
      input.addEventListener('input', () => {
        paint();
        let value = Number(input.value);
        if (control.snap?.length) {
          value = control.snap.reduce((best, item) => (Math.abs(item - value) < Math.abs(best - value) ? item : best));
        }
        run.setParam(control.name, value);
        onEdit();
      });
      wrap.append(label, input, read);
    } else if (control.type === 'select') {
      const label = document.createElement('label');
      label.htmlFor = id;
      label.textContent = control.label;
      const select = document.createElement('select');
      select.id = id;
      for (const option of control.options ?? []) {
        const node = document.createElement('option');
        node.value = option.value;
        node.textContent = option.label;
        select.append(node);
      }
      select.value = String(run.params[control.name] ?? '');
      select.addEventListener('change', () => {
        run.setParam(control.name, select.value);
        onEdit();
      });
      wrap.append(label, select);
    } else if (control.type === 'toggle') {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.id = id;
      input.checked = run.params[control.name] === true;
      input.setAttribute('aria-label', control.label);
      label.append(input, document.createTextNode(` ${control.label}`));
      input.addEventListener('change', () => {
        run.setParam(control.name, input.checked);
        onEdit();
      });
      wrap.append(label);
    } else if (control.type === 'choice') {
      const label = document.createElement('p');
      label.id = `${id}-label`;
      label.textContent = control.label;
      const group = document.createElement('div');
      group.setAttribute('role', 'group');
      group.setAttribute('aria-labelledby', label.id);
      for (const option of control.options ?? []) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = option.label;
        button.setAttribute('aria-pressed', String(run.params[control.name] === option.value));
        button.addEventListener('click', () => {
          run.setParam(control.name, option.value);
          for (const peer of group.querySelectorAll('button')) peer.setAttribute('aria-pressed', 'false');
          button.setAttribute('aria-pressed', 'true');
          onEdit();
        });
        group.append(button);
      }
      wrap.append(label, group);
    }
    rows.push({ control, wrap });
    host.append(wrap);
  }
  const sync = () => {
    for (const row of rows) row.wrap.hidden = !visible(row.control, run);
  };
  sync();
  return run.subscribe(sync);
}
