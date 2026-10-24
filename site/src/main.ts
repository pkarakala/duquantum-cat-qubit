// Hash router (works from file://) and the MOCK DATA banner.
import type { Bundle, DataName } from "./data/types";
import { DATA_NAMES } from "./data/types";
import * as about from "./pages/about";
import * as errors from "./pages/errors";
import * as inflate from "./pages/inflate";
import * as readout from "./pages/readout";
import * as verify from "./pages/verify";

interface Route {
  title: string;
  render: (root: HTMLElement, b: Bundle) => void;
}

export const ROUTES: Record<string, Route> = {
  "#/inflate": { title: "Inflate", render: inflate.render },
  "#/errors": { title: "Error budget", render: errors.render },
  "#/readout": { title: "Readout designer", render: readout.render },
  "#/verify": { title: "Verification", render: verify.render },
  "#/about": { title: "About", render: about.render },
};
const DEFAULT_ROUTE = "#/inflate";

export function mockFiles(b: Bundle): DataName[] {
  return DATA_NAMES.filter((n) => b.sources[n] === "mock");
}

export function renderBanner(el: HTMLElement, b: Bundle): void {
  const mocks = mockFiles(b);
  el.setAttribute("role", "status");
  el.replaceChildren();
  if (!mocks.length && !b.notes.length) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  if (mocks.length) {
    const strong = document.createElement("strong");
    strong.textContent = "MOCK DATA";
    el.append(strong, `: ${mocks.map((n) => `${n}.json`).join(", ")} ${mocks.length === 1 ? "is a" : "are"} synthetic placeholder${mocks.length === 1 ? "" : "s"}, not results.`);
  }
  for (const n of b.notes) {
    const p = document.createElement("span");
    p.className = "banner-note";
    p.textContent = ` ${n}.`;
    el.append(p);
  }
}

export function renderRoute(hash: string, root: HTMLElement, b: Bundle): void {
  const dlg = document.getElementById("card") as HTMLDialogElement | null;
  if (dlg) {
    if (dlg.open && typeof dlg.close === "function") dlg.close();
    dlg.replaceChildren();
  }
  const key = hash in ROUTES ? hash : DEFAULT_ROUTE;
  const route = ROUTES[key];
  root.replaceChildren();
  route.render(root, b);
  document.title = `${route.title} · Cat Qubit Lab`;
  for (const a of document.querySelectorAll<HTMLAnchorElement>("nav a[href^='#/']")) {
    if (a.getAttribute("href") === key) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  const banner = document.getElementById("banner");
  if (banner) renderBanner(banner, b);
}

export function boot(b: Bundle): void {
  const root = document.getElementById("app");
  if (!root) return;
  const go = () => {
    renderRoute(location.hash, root, b);
    root.focus({ preventScroll: true });
  };
  window.addEventListener("hashchange", go);
  renderRoute(location.hash, root, b);
}
