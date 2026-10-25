import type { PredictOption } from '../types';

let groupSeq = 0;

/** Radiogroup whose ArrowDown / ArrowUp moves the checked option, including under jsdom. */
export function mountRadios(
  host: HTMLElement,
  question: string,
  options: PredictOption[],
  onChoose: (id: string) => void,
): HTMLElement {
  const group = document.createElement('div');
  group.className = 'choices';
  group.setAttribute('role', 'radiogroup');
  group.setAttribute('aria-label', question);
  const name = `choice-${groupSeq++}`;
  const radios: HTMLInputElement[] = [];
  const legend = document.createElement('p');
  legend.className = 'question';
  legend.textContent = question;
  group.append(legend);
  for (const option of options) {
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = name;
    input.value = option.id;
    input.setAttribute('role', 'radio');
    input.setAttribute('aria-checked', 'false');
    input.setAttribute('aria-label', option.text);
    label.append(input, document.createTextNode(` ${option.text}`));
    group.append(label);
    radios.push(input);
    input.addEventListener('change', () => {
      if (!input.checked) return;
      radios.forEach((radio) => radio.setAttribute('aria-checked', radio === input ? 'true' : 'false'));
      onChoose(option.id);
    });
  }
  group.addEventListener('keydown', (ev) => {
    if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
    ev.preventDefault();
    const focusAt = radios.findIndex((radio) => radio === document.activeElement || radio.checked);
    const step = ev.key === 'ArrowDown' ? 1 : -1;
    const next = radios[(focusAt + step + radios.length) % radios.length]!;
    for (const radio of radios) {
      radio.checked = radio === next;
      radio.setAttribute('aria-checked', radio === next ? 'true' : 'false');
    }
    next.focus();
    onChoose(next.value);
  });
  host.append(group);
  return group;
}
