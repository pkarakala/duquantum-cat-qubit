// Browser entry. The academy, the block editor, and the one-mode solver mount from here.
import "./style.css";
import { renderRoute } from "./academy/routes";

export function boot(win: Window = window): void {
  const root = win.document.getElementById("app");
  if (!root) return;
  let painting = false;
  const go = () => {
    if (painting) return;
    painting = true;
    try {
      if (!win.location.hash) win.location.hash = "#/learn";
      renderRoute(win.location.hash || "#/learn", root);
      root.focus({ preventScroll: true });
    } finally {
      painting = false;
    }
  };
  win.addEventListener("hashchange", go);
  go();
}

boot();
