export function mountCheckBanner(host: HTMLElement): { set: (message: string, pass: boolean | null) => void } {
  const node = document.createElement('p');
  node.className = 'check-banner';
  node.dataset.part = 'check-banner';
  node.setAttribute('aria-live', 'polite');
  node.setAttribute('role', 'status');
  host.append(node);
  return {
    set(message, pass) {
      node.dataset.pass = pass == null ? '' : String(pass);
      node.textContent = message;
    },
  };
}
