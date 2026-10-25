import { withSubs } from "./home";
/** Lab routes (#/inflate, #/errors, #/readout, #/verify): main's real figures and numbers, linked to the write-ups. */

const BASE = `${import.meta.env.BASE_URL}research/`;

interface Fig {
  src: string;
  caption: string;
}

interface LabPage {
  title: string;
  lede: string;
  stats: [string, string][];
  figures: Fig[];
  doc: string;
  notebook: string;
}

export const LAB_PAGES: Record<string, LabPage> = {
  "#/inflate": {
    title: "Inflate",
    lede: "Task 1.1: start from vacuum, pump pairs in through the buffer and watch the memory inflate into a cat.",
    stats: [["≈ 6", "memory photons at the overshoot peak"], ["α² = 4.41", "steady state"], ["≈ 2", "photons briefly held in the buffer"]],
    figures: [
      { src: "figures/task_1_1_wigner.gif", caption: "Wigner function of the memory as the cat inflates." },
      { src: "figures/task_1_1_inflation.png", caption: "Memory photon number in the two-mode model vs the one-mode shortcut." },
    ],
    doc: "task_1.html#11--inflate-the-memory-in-the-full-two-mode-model",
    notebook: "02_task_1_1_two_mode",
  },
  "#/errors": {
    title: "Error budget",
    lede: "Tasks 2.1 and 2.2: bit flips vanish exponentially with cat size, phase flips grow linearly.",
    stats: [["Γ_X = 3.85×10⁻⁷ /µs", "bit flips at α = 2.1 (T_X = 2.6 s)"], ["Γ_Z = 0.515 /µs", "phase flips at α = 2.1 (T_Z = 1.94 µs)"], ["1.3×10⁶", "Γ_Z / Γ_X"]],
    figures: [
      { src: "figures/s2/task_2_1_large_cats.png", caption: "Γ_X from the slowest odd-parity Liouvillian eigenvalue, out to large cats." },
      { src: "figures/task_2_1_bit_flips.png", caption: "Γ_X from direct time-domain fits at small α." },
      { src: "figures/task_2_2_phase_flips.png", caption: "Γ_Z vs α²: slope within 0.16% of 2κ_a." },
    ],
    doc: "task_2.html#21--measure-bit-flip-relaxation",
    notebook: "06_task_2_1_bit_flips",
  },
  "#/readout": {
    title: "Readout designer",
    lede: "Tasks 2.3 and 2.4: read the bit through the buffer, then shape the pulse so it reads faster without extra flips.",
    stats: [["0.083%", "buffer field vs weak-drive theory"], ["0.968 µs", "1% settling time"], ["1.12% → 0.65%", "readout error, square vs resonant cosine"]],
    figures: [
      { src: "figures/task_2_3_readout.png", caption: "Buffer fields for the two codewords and their settling." },
      { src: "figures/s2/task_2_4_better_readout.png", caption: "Information vs amplitude loss; an optimized resonant pulse." },
      { src: "figures/s2/task_2_4_enlargement.png", caption: "Temporary cat enlargement: same signal, 2.33× faster cycle." },
    ],
    doc: "task_2.html#23--read-the-memory-bit-through-the-buffer",
    notebook: "09_task_2_4_better_readout",
  },
  "#/verify": {
    title: "Verification",
    lede: "How we know the numbers are right: truncation sweeps, a second method for every rate, and validation against theory.",
    stats: [["0.035%", "32×12 vs 48×18 truncation"], ["10⁻⁸", "eigenvalue vs time-domain Γ_X"], ["0.1%", "Γ_Z across three methods"]],
    figures: [
      { src: "figures/task_1_2_convergence.png", caption: "Final value and overshoot vs memory and buffer truncation." },
      { src: "figures/task_1_2_error_grid.png", caption: "Error over the full truncation grid (run on Vultr)." },
      { src: "figures/task_2_3_validation.png", caption: "Readout simulation vs the linear-response prediction." },
    ],
    doc: "methodology.html",
    notebook: "03_task_1_2_convergence",
  },
};

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function link(href: string, text: string, className = ""): HTMLAnchorElement {
  const a = el("a", className, text);
  a.href = href;
  return a;
}

export function renderLab(root: HTMLElement, hash: string): boolean {
  const pageInfo = LAB_PAGES[hash];
  if (!pageInfo) return false;
  const wrap = el("div", "home");
  const hero = el("section", "home-hero");
  hero.append(el("p", "eyebrow", "Real research · results from main"), el("h1", "", pageInfo.title), el("p", "lede", pageInfo.lede));
  const stats = el("div", "slide-stats");
  for (const [v, l] of pageInfo.stats) {
    const d = el("div", "stat");
    d.append(withSubs(el("strong"), v), withSubs(el("span"), l));
    stats.append(d);
  }
  const figs = el("div", "lab-figs");
  for (const f of pageInfo.figures) {
    const fig = el("figure", "slide-fig");
    const img = el("img");
    img.src = `${BASE}${f.src}`;
    img.alt = f.caption;
    img.loading = "lazy";
    fig.append(img, el("figcaption", "muted", f.caption));
    figs.append(fig);
  }
  const cta = el("p", "home-cta");
  cta.append(
    link(`${BASE}${pageInfo.doc}`, "Read the write-up", "button primary"),
    link(`${BASE}notebooks/${pageInfo.notebook}.html`, "Open the notebook", "button"),
    link("#/research", "All tasks", "button"),
  );
  wrap.append(hero, stats, figs, cta);
  root.replaceChildren(wrap);
  return true;
}
