import type { LevelSpec } from '../types';

export function mountConcept(host: HTMLElement, spec: LevelSpec): void {
  host.replaceChildren();
  const card = document.createElement('article');
  card.className = 'concept';
  const title = document.createElement('h2');
  title.textContent = 'Concept';
  const text = document.createElement('p');
  text.textContent = spec.concept.text;
  const audio = document.createElement('audio');
  audio.preload = 'none';
  const base = import.meta.env.BASE_URL || '/';
  audio.src = `${base}audio/${spec.concept.narrationKey}.mp3`;
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Play narration';
  button.addEventListener('click', () => {
    audio.play().catch(() => button.remove());
  });
  audio.addEventListener('error', () => button.remove());
  card.append(title, text, button, audio);
  host.append(card);
}
