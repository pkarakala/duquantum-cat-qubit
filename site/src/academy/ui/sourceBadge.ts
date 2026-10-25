export function mountBadge(host: HTMLElement): { set: (text: string, banner?: string) => void } {
  host.replaceChildren();
  const badge = document.createElement('p');
  badge.className = 'source-badge';
  badge.setAttribute('role', 'status');
  badge.setAttribute('aria-live', 'polite');
  badge.textContent = 'Waiting to run';
  const banner = document.createElement('p');
  banner.className = 'banner';
  banner.hidden = true;
  host.append(badge, banner);
  return {
    set(text, note) {
      badge.textContent = text;
      banner.hidden = !note;
      banner.textContent = note ?? '';
    },
  };
}
