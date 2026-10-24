// Minimal element builder (no framework).
type Attr = string | number | boolean | null | undefined | EventListener;
type Child = Node | string | number | null | undefined | false;

export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Record<string, Attr> = {},
  ...children: (Child | Child[])[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = String(v);
    else el.setAttribute(k, v === true ? "" : String(v));
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : String(c));
  }
  return el;
}

let uid = 0;
export function uniqueId(prefix: string): string {
  uid += 1;
  return `${prefix}-${uid}`;
}

// Table inside a horizontal scroller, so narrow screens never scroll the page sideways.
export function scrollTable(table: HTMLTableElement, label: string): HTMLElement {
  return h("div", { class: "table-scroll", role: "region", "aria-label": label, tabindex: 0 }, table);
}
