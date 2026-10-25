/** Render the small amount of emphasis used in LEVELS copy. No HTML from the string. */

export function setRichText(el: HTMLElement, text: string): void {
  el.replaceChildren();
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0;
  for (let match = re.exec(text); match; match = re.exec(text)) {
    if (match.index > last) el.append(document.createTextNode(text.slice(last, match.index)));
    const node = document.createElement(match[1] != null ? 'strong' : 'em');
    node.textContent = match[1] ?? match[2] ?? '';
    el.append(node);
    last = match.index + match[0].length;
  }
  if (last < text.length) el.append(document.createTextNode(text.slice(last)));
}
