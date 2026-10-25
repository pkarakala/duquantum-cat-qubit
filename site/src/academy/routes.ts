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

function showSandbox(root: HTMLElement): void {
  closeBlocks();
  closeAcademy();
  root.classList.remove("academy");
  delete root.dataset.level;
  root.replaceChildren();

  const lede = paragraph(
    "lede",
    "Snap operators into H and the jumps. One-mode trees run here in the browser solver. A two-mode tree is the L6 machine: the solver refuses buffer symbols, and that run stays on the API or a preset.",
  );
  const controls = document.createElement("div");
  controls.className = "row";
  const presetLabel = document.createElement("label");
  presetLabel.textContent = "Preset ";
  const preset = document.createElement("select");
  preset.setAttribute("aria-label", "Preset");
  for (const name of PRESET_NAMES) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name.replaceAll("_", " ");
    preset.append(option);
  }
  preset.value = "h2ph_correct";
  presetLabel.append(preset);
  controls.append(presetLabel);

  const editor = document.createElement("div");
  editor.id = "editor";
  const python = document.createElement("pre");
  python.setAttribute("aria-label", "Compiled Python");
  const actions = document.createElement("div");
  actions.className = "row";
  const run = document.createElement("button");
  run.type = "button";
  run.textContent = "Run in the browser";
  actions.append(run);
  const status = document.createElement("p");
  status.setAttribute("role", "status");
  status.textContent = "The browser solver has not run yet.";

  root.append(page("Sandbox", lede, controls, editor, python, actions, status));

  const mount = (name: string) => {
    const mode = isPresetName(name) && getPreset(name).modes === "one" ? "one" : "two";
    closeBlocks();
    blocks = mountBlocks(editor, { modes: mode });
    blocks.loadPreset(name);
    const show = () => {
      if (!blocks) return;
      const program = blocks.getTree();
      const jumps = program.jumps.map((jump) => toPython(jump)).join(", ");
      python.textContent = `H = ${toPython(program.H)}\njumps = [${jumps}]`;
    };
    blocks.onChange(show);
    show();
  };
  mount("h2ph_correct");
  preset.addEventListener("change", () => mount(preset.value));

  run.addEventListener("click", () => {
    if (!blocks) return;
    void runBrowser(blocks, status);
  });
}

async function runBrowser(handle: BlocksHandle, status: HTMLElement): Promise<void> {
  const program = handle.getTree();
  const validation = validateProgram(program, handle.modes);
  if (!validation.ok) {
    status.textContent = validation.errors.join(" ");
    return;
  }
  status.textContent = "Running in the browser…";
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
      nT: 21,
      outputs: ["n", "parity"],
    });
    const last = result.n && result.n.length ? result.n[result.n.length - 1] : undefined;
    const nText = last == null ? "no ⟨n⟩" : `⟨n⟩(t_end) = ${last.toFixed(4)}`;
    status.textContent = `In-browser one-mode solver · ${nText} · ${result.meta.wallMs.toFixed(0)} ms`;
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : "The browser solver rejected this tree.";
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
