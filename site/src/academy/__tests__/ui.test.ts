// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../ui/plot', () => ({ plot: vi.fn(async () => {}) }));

import { LEVELS } from '../levels';
import { mountAcademy } from '../index';

function accessibleName(el: Element): string {
  const aria = el.getAttribute('aria-label')?.trim();
  if (aria) return aria;
  const id = el.getAttribute('id');
  if (id) {
    const label = document.querySelector(`label[for="${id}"]`);
    if (label?.textContent?.trim()) return label.textContent.trim();
  }
  const wrapped = el.closest('label');
  if (wrapped?.textContent?.trim()) return wrapped.textContent.trim();
  return (el.textContent ?? '').trim();
}

beforeEach(() => {
  document.body.innerHTML = '<div id="root"></div>';
  localStorage.clear();
});

describe('learner UI', () => {
  it('mounts every level with named controls, a radiogroup, and a live check banner', () => {
    const proto = HTMLCanvasElement.prototype;
    const spy = vi.spyOn(proto, 'getContext').mockReturnValue(null);
    for (const spec of LEVELS) {
      const root = document.createElement('div');
      document.body.append(root);
      const handle = mountAcademy(root, { levelId: spec.id });
      expect(root.querySelector('[role="radiogroup"]')).toBeTruthy();
      expect(root.querySelector('[data-part="check-banner"]')?.getAttribute('aria-live')).toBe('polite');
      for (const el of root.querySelectorAll('input, select, button')) {
        expect(accessibleName(el), `${spec.id} ${el.tagName}`).not.toBe('');
      }
      const group = root.querySelector('[role="radiogroup"]')!;
      const radios = [...group.querySelectorAll<HTMLInputElement>('[role="radio"]')];
      expect(radios.length).toBeGreaterThan(1);
      radios[0]?.focus();
      radios[0]?.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
      expect(radios[1]?.getAttribute('aria-checked')).toBe('true');
      handle.dispose();
    }
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
