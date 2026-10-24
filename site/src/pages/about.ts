import type { Bundle } from "../data/types";
import { DATA_NAMES } from "../data/types";
import { h } from "../lib/dom";

export function render(root: HTMLElement, b: Bundle): void {
  const mocks = DATA_NAMES.filter((n) => b.sources[n] === "mock");
  const live = DATA_NAMES.filter((n) => b.sources[n] === "live");
  root.append(
    h("h1", {}, "About"),
    h(
      "p",
      { class: "lede" },
      "The Cat Qubit Lab is a static, offline viewer for the DuQuantum 2026 Alice & Bob cat-qubit challenge. ",
      "A judge can watch a cat inflate, inspect the bit- and phase-flip budget, and design a readout — and click any number to see the record it came from.",
    ),
    h("h2", {}, "No physics in the browser"),
    h(
      "p",
      {},
      "Every plotted number is bundled JSON written by ",
      h("code", {}, "tools/export_lab_data.py"),
      " from ",
      h("code", {}, "results/"),
      ". This page only selects, formats and plots. Opening ",
      h("code", {}, "site/dist-single/index.html"),
      " from ",
      h("code", {}, "file://"),
      " needs no network.",
    ),
    h("h2", {}, "AI use"),
    h(
      "p",
      {},
      "Planned with Claude Code, implemented by Cursor agents under Harshit's direction, physics reviewed by Gemini; every number comes from a script in this repo with a provenance record.",
    ),
    h("h2", {}, "Source"),
    h(
      "p",
      {},
      h(
        "a",
        { href: "https://github.com/pkarakala/duquantum-cat-qubit#readme", rel: "noopener", target: "_blank" },
        "Repository README",
      ),
      ".",
    ),
    h("h2", {}, "Which data is mock?"),
    mocks.length
      ? h("p", {}, "Still synthetic placeholders: ", mocks.map((n) => `${n}.json`).join(", "), ".")
      : h("p", {}, "Every Lab file is live."),
  );
  if (live.length) root.append(h("p", {}, "Live files: ", live.map((n) => `${n}.json`).join(", "), "."));
  if (b.notes.length) root.append(h("ul", {}, ...b.notes.map((n) => h("li", {}, n))));
}
