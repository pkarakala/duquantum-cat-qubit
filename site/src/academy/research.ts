/** Research index: links to main's write-ups, notebooks and results, rendered into public/research/. */

const BASE = `${import.meta.env.BASE_URL}research/`;

interface Task {
  id: string;
  title: string;
  doc: string;
  anchor: string;
  notebook: string;
  result: string;
}

export const TASKS: Task[] = [
  { id: "1.0", title: "Add dissipation one ingredient at a time", doc: "task_1", anchor: "10--add-dissipation-one-ingredient-at-a-time", notebook: "01_task_1_0_warmup", result: "task_1_0.json" },
  { id: "1.1", title: "Inflate the memory in the two-mode model", doc: "task_1", anchor: "11--inflate-the-memory-in-the-full-two-mode-model", notebook: "02_task_1_1_two_mode", result: "task_1_1.json" },
  { id: "1.2", title: "Semiclassical agreement and convergence", doc: "task_1", anchor: "12--check-semiclassical-agreement-and-convergence", notebook: "03_task_1_2_convergence", result: "task_1_2.json" },
  { id: "1.3a", title: "Identify the prepared state and its decay", doc: "task_1", anchor: "13a--identify-the-prepared-state-and-its-decay", notebook: "04_task_1_3a_which_state", result: "task_1_3a.json" },
  { id: "1.3b–c", title: "Prepare a definite logical state", doc: "task_1", anchor: "13b--prepare-a-definite-logical-state", notebook: "05_task_1_3b_logical_prep", result: "task_1_3b.json" },
  { id: "2.1", title: "Bit-flip relaxation Γ_X", doc: "task_2", anchor: "21--measure-bit-flip-relaxation", notebook: "06_task_2_1_bit_flips", result: "task_2_1.json" },
  { id: "2.2", title: "Phase-flip relaxation Γ_Z", doc: "task_2", anchor: "22--measure-phase-flip-relaxation", notebook: "07_task_2_2_phase_flips", result: "task_2_2.json" },
  { id: "2.3", title: "Read the memory bit through the buffer", doc: "task_2", anchor: "23--read-the-memory-bit-through-the-buffer", notebook: "08_task_2_3_readout", result: "task_2_3.json" },
  { id: "2.4", title: "Better readout, memory still protected", doc: "task_2", anchor: "24--improve-readout-without-sacrificing-memory-protection", notebook: "09_task_2_4_better_readout", result: "task_2_4_enlargement.json" },
];

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function link(href: string, text: string): HTMLAnchorElement {
  const a = el("a", "", text);
  a.href = href;
  return a;
}

export function renderResearch(root: HTMLElement): void {
  const wrap = el("div", "home");
  const hero = el("section", "home-hero");
  hero.append(
    el("p", "eyebrow", "Real research · from the repo's main branch"),
    el("h1", "", "Tasks, notebooks and results"),
    el("p", "lede", "Every challenge task with its write-up, the notebook that runs it, and the JSON its numbers come from. Copied unchanged from main."),
  );
  const docs = el("p", "home-cta");
  docs.append(
    Object.assign(link(`${BASE}task_1.html`, "Task 1 write-up"), { className: "button" }),
    Object.assign(link(`${BASE}task_2.html`, "Task 2 write-up"), { className: "button" }),
    Object.assign(link(`${BASE}methodology.html`, "Methodology and checks"), { className: "button primary" }),
  );
  hero.append(docs);

  const table = el("table", "task-table");
  const head = el("tr");
  for (const h of ["Task", "What", "Write-up", "Notebook", "Data"]) head.append(el("th", "", h));
  table.append(el("thead"), el("tbody"));
  table.tHead!.append(head);
  for (const t of TASKS) {
    const row = el("tr");
    const cells = [
      el("td", "level-id", t.id),
      el("td", "", t.title),
      el("td"),
      el("td"),
      el("td"),
    ];
    cells[2].append(link(`${BASE}${t.doc}.html#${t.anchor}`, "read"));
    cells[3].append(link(`${BASE}notebooks/${t.notebook}.html`, t.notebook.slice(0, 2)));
    cells[4].append(link(`${BASE}results/${t.result}`, "json"));
    row.append(...cells);
    table.tBodies[0].append(row);
  }
  const tasks = el("section", "home-section");
  const scroll = el("div", "table-scroll");
  scroll.append(table);
  tasks.append(el("h2", "", "Challenge tasks"), scroll);

  wrap.append(hero, tasks);
  root.replaceChildren(wrap);
}
