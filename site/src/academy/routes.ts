/** Hash routes for the Academy shell. Level checks stay in the academy modules. */

import {
  getPreset,
  isPresetName,
  mountBlocks,
  PRESET_NAMES,
  toPython,
  validateProgram,
  type BlocksHandle,
} from "../blocks/index";
import { ALPHA, KAPPA_2, KAPPA_A } from "../sim/config";
import type { ExprTree as SimTree } from "../sim/expr";
import { runInWorker } from "../sim/index";
import { renderHome } from "./home";
import { plot } from "./ui/plot";
import { renderResearch } from "./research";
import { mountAcademy, type AcademyHandle, type LevelId } from "./index";

export const ROUTE_HASHES = {
  home: "#/",
  learn: "#/learn",
  sandbox: "#/sandbox",
  challenge: "#/challenge",
  inflate: "#/inflate",
  errors: "#/errors",
  readout: "#/readout",
  verify: "#/verify",
  research: "#/research",
  about: "#/about",
} as const;

const LEVELS: LevelId[] = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"];

export type RouteName = keyof typeof ROUTE_HASHES;

export interface ResolvedRoute {
  name: RouteName;
  title: string;
  levelId: LevelId | null;
  /** Nav href that should carry aria-current. */
  navHash: string;
}

const RESEARCH: Record<string, { title: string; blurb: string }> = {
  [ROUTE_HASHES.inflate]: {
    title: "Inflate",
    blurb: "The inflation viewer reads the committed research records. It ships with the physics lab, and it is not in this Academy bundle.",
  },
  [ROUTE_HASHES.errors]: {
    title: "Error budget",
    blurb: "The error-budget viewer reads the committed research records. It ships with the physics lab, and it is not in this Academy bundle.",
  },
  [ROUTE_HASHES.readout]: {
    title: "Readout designer",
    blurb: "The readout designer reads the committed research records. It ships with the physics lab, and it is not in this Academy bundle.",
  },
  [ROUTE_HASHES.verify]: {
    title: "Verification",
    blurb: "The verification viewer reads the committed research records. It ships with the physics lab, and it is not in this Academy bundle.",
  },
};

export function academyRoute(hash: string): ResolvedRoute | null {
  const path = (hash || ROUTE_HASHES.home).replace(/^#/, "");
  if (path === "/" || path === "") return { name: "home", title: "Home", levelId: null, navHash: ROUTE_HASHES.home };
  if (path === "/learn") {
    return { name: "learn", title: "Learn", levelId: "L1", navHash: ROUTE_HASHES.learn };
  }
  const level = path.match(/^\/learn\/(L[1-8])$/)?.[1] as LevelId | undefined;
  if (level && LEVELS.includes(level)) {
    return { name: "learn", title: level, levelId: level, navHash: ROUTE_HASHES.learn };
  }
  if (path === "/sandbox") return { name: "sandbox", title: "Sandbox", levelId: null, navHash: ROUTE_HASHES.sandbox };
  if (path === "/challenge") return { name: "challenge", title: "Challenge", levelId: null, navHash: ROUTE_HASHES.challenge };
  if (path === "/inflate") return { name: "inflate", title: "Inflate", levelId: null, navHash: ROUTE_HASHES.inflate };
  if (path === "/errors") return { name: "errors", title: "Error budget", levelId: null, navHash: ROUTE_HASHES.errors };
  if (path === "/readout") return { name: "readout", title: "Readout designer", levelId: null, navHash: ROUTE_HASHES.readout };
  if (path === "/verify") return { name: "verify", title: "Verification", levelId: null, navHash: ROUTE_HASHES.verify };
  if (path === "/research") return { name: "research", title: "Research", levelId: null, navHash: ROUTE_HASHES.research };
  if (path === "/about") return { name: "about", title: "About", levelId: null, navHash: ROUTE_HASHES.about };
  return null;
}

function apiBase(): string {
  return (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");
}

function markNav(navHash: string | null): void {
  for (const link of document.querySelectorAll<HTMLAnchorElement>("nav a[href^='#/']")) {
    if (navHash && link.getAttribute("href") === navHash) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

function page(title: string, ...nodes: Node[]): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const h1 = document.createElement("h1");
  h1.textContent = title;
  fragment.append(h1, ...nodes);
  return fragment;
}

function paragraph(className: string, text: string): HTMLParagraphElement {
  const p = document.createElement("p");
  p.className = className;
  p.textContent = text;
  return p;
}

let academy: AcademyHandle | null = null;
let blocks: BlocksHandle | null = null;

function closeAcademy(): void {
  academy?.dispose();
  academy = null;
}

function closeBlocks(): void {
  blocks?.dispose();
  blocks = null;
}

function showLearn(root: HTMLElement, levelId: LevelId): void {
  closeBlocks();
  if (!academy) {
    root.classList.remove("academy");
    delete root.dataset.level;
    academy = mountAcademy(root, { levelId, apiBase: apiBase() || undefined });
    return;
  }
  academy.navigate(levelId);
}

const SANDBOX_PRESETS: Record<string, string> = {
  one_mode_cat: "Cat qubit, one mode: √κ₂(a² − α²)",
  state_prep_x: "Prepare |+α⟩: drive + two-photon loss",
  kerr: "Kerr term + two-photon loss",
  empty: "Empty: build your own",
  h2ph_correct: "Two-mode cat (memory + buffer)",
  readout_z: "Buffer readout (two-mode)",
  wrong_drive_on_memory: "Bug: drive on memory (two-mode)",
  wrong_no_dissipation: "Bug: no buffer loss (two-mode)",
  wrong_conversion: "Bug: wrong conversion (two-mode)",
  wrong_missing_hc: "Bug: missing h.c. (two-mode)",
};

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className?: string, text?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function showSandbox(root: HTMLElement): void {
  closeBlocks();
  closeAcademy();
  root.classList.remove("academy");
  delete root.dataset.level;
  root.replaceChildren();

  const wrap = el("div", "sandbox");
  const lede = paragraph(
    "lede",
    "Build a Lindblad model from operator blocks: a Hamiltonian H and a list of jump operators L. The site compiles your blocks to dynamiqs Python and, for one-mode models, solves dρ/dt = −i[H, ρ] + Σ D[L]ρ right in your browser.",
  );

  const how = el("ol", "sandbox-how");
  for (const step of [
    "Pick a preset, or start from Empty.",
    "Click a block in the bar to insert it. Drag blocks into the H = and Jumps sockets. Select a block to edit its number, parameter or power.",
    "Read the compiled Python under the editor. It updates as you edit.",
    "Press Run. One-mode models simulate ⟨n⟩ and parity from vacuum for 1 µs. Two-mode models (with b) run in Level 6.",
  ]) how.append(el("li", undefined, step));
  const howCard = el("section", "card sandbox-intro");
  howCard.append(el("h2", undefined, "How to use"), how);

  const bar = el("div", "sandbox-bar");
  const presetLabel = el("label", "sandbox-preset", "Preset");
  const preset = document.createElement("select");
  preset.setAttribute("aria-label", "Preset");
  for (const name of PRESET_NAMES) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = SANDBOX_PRESETS[name] ?? name.replaceAll("_", " ");
    preset.append(option);
  }
  preset.value = "one_mode_cat";
  presetLabel.append(preset);
  const mode = el("span", "sandbox-mode");
  const run = el("button", undefined, "Run ▶");
  run.type = "button";
  bar.append(presetLabel, mode, run);

  const editor = document.createElement("div");
  editor.id = "editor";
  const out = el("div", "sandbox-out");
  const codeCard = el("section", "card");
  const python = document.createElement("pre");
  python.setAttribute("aria-label", "Compiled Python");
  codeCard.append(el("h2", undefined, "Compiled Python"), python);
  const resultCard = el("section", "card");
  const status = document.createElement("p");
  status.setAttribute("role", "status");
  status.textContent = "Press Run to simulate.";
  const chart = el("div", "sandbox-chart");
  resultCard.append(el("h2", undefined, "Result"), status, chart);
  out.append(codeCard, resultCard);

  wrap.append(lede, howCard, bar, editor, out);
  root.append(page("Sandbox", wrap));

  const load = (name: string) => {
    const one = isPresetName(name) && getPreset(name).modes === "one";
    closeBlocks();
    blocks = mountBlocks(editor, { modes: one ? "one" : "two" });
    blocks.loadPreset(name);
    mode.textContent = one ? "One mode · runs in your browser" : "Two modes · run it in Level 6";
    mode.dataset.mode = one ? "one" : "two";
    run.disabled = !one;
    chart.replaceChildren();
    status.textContent = one ? "Press Run to simulate." : "This model has a buffer mode b. Open Level 6 to run it on the server.";
    const show = () => {
      if (!blocks) return;
      const program = blocks.getTree();
      const jumps = program.jumps.map((jump) => toPython(jump)).join(",\n         ");
      python.textContent = `H = ${toPython(program.H)}\njumps = [${jumps}]`;
    };
    blocks.onChange(show);
    show();
  };
  load(preset.value);
  preset.addEventListener("change", () => load(preset.value));

  run.addEventListener("click", () => {
    if (!blocks) return;
    void runBrowser(blocks, status, chart, run);
  });
}

async function runBrowser(handle: BlocksHandle, status: HTMLElement, chart: HTMLElement, button: HTMLButtonElement): Promise<void> {
  const program = handle.getTree();
  const validation = validateProgram(program, handle.modes);
  if (!validation.ok) {
    status.textContent = validation.errors.join(" ");
    return;
  }
  status.textContent = "Running in your browser…";
  button.disabled = true;
  try {
    const result = await runInWorker({
      params: {
        N: 20,
        alpha: ALPHA,
        kappa2: KAPPA_2,
        kappaA: KAPPA_A,
        H: program.H as unknown as SimTree,
        jumps: program.jumps as unknown as SimTree[],
      },
      init: { kind: "vacuum" },
      tEndUs: 1,
      nT: 101,
      outputs: ["n", "parity"],
    });
    const last = result.n && result.n.length ? result.n[result.n.length - 1] : undefined;
    const nText = last == null ? "no ⟨n⟩" : `⟨n⟩(1 µs) = ${last.toFixed(3)} (α² = ${(ALPHA * ALPHA).toFixed(2)})`;
    status.textContent = `${nText} · N = 20 · ${result.meta.wallMs.toFixed(0)} ms in your browser`;
    if (result.tUs && result.n) {
      const series = [{ x: result.tUs, y: result.n, name: "⟨n⟩" }];
      if (result.parity) series.push({ x: result.tUs, y: result.parity, name: "parity" });
      await plot(chart, series, { xlabel: "t (µs)", ylabel: "value" });
    }
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : "The browser solver rejected this tree.";
  } finally {
    button.disabled = false;
  }
}

function showChallenge(root: HTMLElement): void {
  closeAcademy();
  closeBlocks();
  root.classList.remove("academy");
  delete root.dataset.level;
  const lede = paragraph("lede", "Level 8 scores the readout pulse. Submit it from #/learn/L8. This page reads the leaderboard when the API is configured.");
  const status = document.createElement("p");
  status.setAttribute("role", "status");
  const list = document.createElement("ol");
  root.replaceChildren(page("Challenge", lede, status, list));
  const base = apiBase();
  if (!base) {
    status.textContent = "No VITE_API_BASE, so the leaderboard stays on the server.";
    return;
  }
  status.textContent = "Loading the leaderboard…";
  const ctrl = new AbortController();
  const kill = window.setTimeout(() => ctrl.abort(), 3000);
  fetch(`${base}/api/leaderboard?challenge=readout_pulse`, { signal: ctrl.signal })
    .then(async (response) => {
      window.clearTimeout(kill);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const body = (await response.json()) as { rows?: { alias?: string; score?: number; verified?: boolean }[] };
      list.replaceChildren();
      const rows = body.rows ?? [];
      if (!rows.length) {
        status.textContent = "The leaderboard is empty.";
        return;
      }
      status.textContent = `${rows.length} scores.`;
      for (const row of rows) {
        const item = document.createElement("li");
        const score = typeof row.score === "number" ? row.score.toFixed(4) : "?";
        item.textContent = `${row.alias || "anon"} · ${score}${row.verified ? " · verified" : ""}`;
        list.append(item);
      }
    })
    .catch(() => {
      window.clearTimeout(kill);
      status.textContent = "The leaderboard did not answer. The L8 score on this page is still local.";
    });
}

function showResearch(root: HTMLElement, hash: string): void {
  closeAcademy();
  closeBlocks();
  root.classList.remove("academy");
  delete root.dataset.level;
  const info = RESEARCH[hash] ?? { title: "Real Research", blurb: "This viewer is not in the Academy bundle." };
  const lede = paragraph("lede", info.blurb);
  const back = document.createElement("p");
  const link = document.createElement("a");
  link.href = ROUTE_HASHES.learn;
  link.textContent = "Back to Learn";
  back.append(link);
  root.replaceChildren(page(info.title, lede, back));
}

function showAbout(root: HTMLElement): void {
  closeAcademy();
  closeBlocks();
  root.classList.remove("academy");
  delete root.dataset.level;
  const lede = paragraph(
    "lede",
    "Eight lessons, the operator-block editor, and the in-browser one-mode solver. Two-mode dynamics are not an interactive browser loop: L6 uses the API or a precomputed preset. ħ = 1, time is in µs, and rates are in rad/µs.",
  );
  root.replaceChildren(page("About", lede));
}

function showMissing(root: HTMLElement): void {
  closeAcademy();
  closeBlocks();
  root.classList.remove("academy");
  delete root.dataset.level;
  const lede = paragraph("lede", "That page is not in the Academy. The lessons start at #/learn.");
  const back = document.createElement("p");
  const link = document.createElement("a");
  link.href = ROUTE_HASHES.learn;
  link.textContent = "Learn";
  back.append(link);
  root.replaceChildren(page("Not found", lede, back));
}

export function renderRoute(hash: string, root: HTMLElement): void {
  const route = academyRoute(hash);
  if (!route) {
    markNav(null);
    document.title = "Not found · Cat Qubit Academy";
    showMissing(root);
    return;
  }
  markNav(route.navHash);
  document.title = `${route.title} · Cat Qubit Academy`;
  if (route.name === "learn" && route.levelId) {
    showLearn(root, route.levelId);
    return;
  }
  if (route.name === "sandbox") {
    showSandbox(root);
    return;
  }
  if (route.name === "challenge") {
    showChallenge(root);
    return;
  }
  if (route.name === "home") {
    closeAcademy();
    closeBlocks();
    root.classList.remove("academy");
    delete root.dataset.level;
    renderHome(root);
    return;
  }
  if (route.name === "research") {
    closeAcademy();
    closeBlocks();
    root.classList.remove("academy");
    delete root.dataset.level;
    renderResearch(root);
    return;
  }
  if (route.name === "about") {
    showAbout(root);
    return;
  }
  showResearch(root, route.navHash);
}
