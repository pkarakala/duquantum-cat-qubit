import { setRichText } from './richText';

export function mountAha(host: HTMLElement): { show: (text: string) => void } {
  const card = document.createElement('article');
  card.className = 'aha';
  card.hidden = true;
  const title = document.createElement('h2');
  title.textContent = 'Aha';
  const body = document.createElement('p');
  card.append(title, body);
  host.append(card);
  return {
    show(text) {
      setRichText(body, text);
      card.hidden = false;
    },
  };
}
