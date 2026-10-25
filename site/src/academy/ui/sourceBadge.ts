/**
 * The value is the source string from the run (`MOCK`, in-browser, records, server).
 * The gloss says what that string does and does not mean.
 */

type Kind = 'mock' | 'real' | 'stored' | 'idle';

function kindOf(text: string): Kind {
  if (/MOCK/i.test(text)) return 'mock';
  if (/In-browser|Verified records|Live ·/.test(text)) return 'real';
  if (/Precomputed/.test(text)) return 'stored';
  return 'idle';
}

function glossFor(text: string): string {
  if (/MOCK/i.test(text)) return 'Stored demo. Not a measurement from this run.';
  if (text.includes('Vultr')) {
    return 'The API returned a dynamiqs result. Vultr is not deployed for this demo, so the label is not proof of that host.';
  }
  if (text.includes('In-browser')) return 'Computed in this browser. Not a live two-mode lab run.';
  if (text.includes('Verified records')) return 'Taken from the committed record bundle.';
  if (text.includes('Precomputed')) return 'Stored trace. Not computed just now.';
  if (text === 'Not run yet') return 'Nothing has been computed yet.';
  return '';
}

export function mountBadge(host: HTMLElement): { set: (text: string, banner?: string) => void } {
  host.classList.add('source-host');
  host.replaceChildren();
  const badge = document.createElement('p');
  badge.className = 'source-badge';
  badge.dataset.kind = 'idle';
  badge.setAttribute('role', 'status');
  badge.setAttribute('aria-live', 'polite');
  const value = document.createElement('span');
  value.className = 'badge-value';
  const gloss = document.createElement('span');
  gloss.className = 'badge-gloss';
  badge.append(value, gloss);
  const banner = document.createElement('p');
  banner.className = 'banner';
  banner.hidden = true;
  host.append(badge, banner);

  const apply = (text: string) => {
    badge.dataset.kind = kindOf(text);
    value.textContent = text;
    gloss.textContent = glossFor(text);
  };
  apply('Not run yet');

  return {
    set(text, note) {
      apply(text);
      banner.hidden = !note;
      banner.textContent = note ?? '';
    },
  };
}
