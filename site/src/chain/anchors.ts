import { isChainError, listAnchors, type AnchorRow } from "./api";
import { isDevnetExplorerUrl, shortHash } from "./format";

const CACHE_KEY = "duq.chain.anchors";

/** Real Research anchor list. Falls back to the last cached list when offline. */
export function mountAnchorsPanel(el: HTMLElement, opts: { apiBase: string }): void {
  el.replaceChildren();
  const list = document.createElement("div");
  el.append(list);
  void load();

  async function load(): Promise<void> {
    const result = await listAnchors(opts.apiBase);
    if (isChainError(result)) {
      const cached = readCache();
      if (cached) render(cached, true);
      else list.textContent = "anchors unavailable offline";
      return;
    }
    writeCache(result.anchors);
    render(result.anchors, false);
  }

  function render(anchors: AnchorRow[], offline: boolean): void {
    list.replaceChildren();
    if (offline) {
      const badge = document.createElement("p");
      badge.dataset.role = "offline";
      badge.textContent = "offline";
      list.append(badge);
    }
    if (anchors.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "No anchors yet.";
      list.append(empty);
      return;
    }
    for (const anchor of anchors) {
      const row = document.createElement("p");
      const when = new Date(anchor.ts).toLocaleString();
      row.append(document.createTextNode(`${anchor.label} ${shortHash(anchor.sha256)} ${when} `));
      const url = anchor.explorer_url;
      if (url && anchor.demo !== true && anchor.broadcast !== false && isDevnetExplorerUrl(url)) {
        const link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = "explorer";
        row.append(link);
      } else if (anchor.demo === true || anchor.broadcast === false) {
        row.append(document.createTextNode("(demo, not broadcast)"));
      }
      list.append(row);
    }
  }
}

function readCache(): AnchorRow[] | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AnchorRow[];
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeCache(anchors: AnchorRow[]): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(anchors));
  } catch {
    // Ignore storage failures. The live list is already on screen.
  }
}
