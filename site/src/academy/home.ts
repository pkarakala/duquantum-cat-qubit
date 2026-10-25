/** Home page: the project, the product, the sponsors, and why. Static content only. */

export const VULTR_URL = "https://66-42-119-3.sslip.io";

interface Sponsor {
  name: string;
  role: string;
  detail: string;
  status: "live" | "demo";
}

export const SPONSORS: Sponsor[] = [
  {
    name: "Google Gemini",
    role: "Ask Schrö, the tutor",
    detail: "Sees your level, your prediction and your last run, then answers in context. Falls back to a scripted tutor with no key.",
    status: "live",
  },
  {
    name: "ElevenLabs",
    role: "Voice",
    detail: "Reads lessons and tutor answers aloud through /api/voice/tts.",
    status: "live",
  },
  {
    name: "Backboard",
    role: "Memory",
    detail: "Remembers what you tried, so the tutor greets you with a recap next visit.",
    status: "live",
  },
  {
    name: "Tiger Data",
    role: "Run log",
    detail: "Every simulation run (level, parameters, result) lands in a Postgres time-series table.",
    status: "live",
  },
  {
    name: "Vultr",
    role: "Hosting + compute",
    detail: "Hosts this site and API, and ran our JAX/dynamiqs research sweeps.",
    status: "live",
  },
  {
    name: "Solana",
    role: "Completion credential",
    detail: "Demo mode only: the claim flow runs, but nothing is minted on-chain.",
    status: "demo",
  },
];

const LEVELS: [string, string][] = [
  ["L1", "A box of light"],
  ["L2", "The leaky box"],
  ["L3", "Two at a time"],
  ["L4", "The cat appears"],
  ["L5", "Flip vs flip"],
  ["L6", "Build the machine"],
  ["L7", "Read the cat"],
  ["L8", "Design challenge"],
];

function el<K extends keyof HTMLElementTagNameMap>(tag: K, className = "", text = ""): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function link(href: string, text: string, className = ""): HTMLAnchorElement {
  const a = el("a", className, text);
  a.href = href;
  if (href.startsWith("http")) a.rel = "noopener";
  return a;
}

function section(title: string, ...nodes: Node[]): HTMLElement {
  const s = el("section", "home-section");
  s.append(el("h2", "", title), ...nodes);
  return s;
}

function hero(): HTMLElement {
  const h = el("section", "home-hero");
  h.append(
    el("p", "eyebrow", "DuQuantum 2026 · Alice & Bob challenge · Standard track"),
    el("h1", "", "Learn cat qubits by building one."),
    el(
      "p",
      "lede",
      "A cat qubit stores information in two blobs of light that pair-photon pumping holds apart. Bit flips get exponentially rare; phase flips are what is left. We computed both rates, designed a better readout, and turned the physics into eight hands-on levels.",
    ),
  );
  const cta = el("p", "home-cta");
  cta.append(link("#/learn", "Start Level 1", "button primary"), link("#/sandbox", "Open the sandbox", "button"));
  h.append(cta);
  return h;
}

function stat(value: string, label: string): HTMLElement {
  const d = el("div", "stat");
  d.append(el("strong", "", value), el("span", "", label));
  return d;
}

function results(): HTMLElement {
  const grid = el("div", "stat-grid");
  grid.append(
    stat("Γ_X ≈ 4e-7 /µs", "bit-flip rate at α = 2.1 (T_X ≈ 2.6 s), from the odd-parity Liouvillian eigenvalue"),
    stat("Γ_Z ≈ 2κ_aα²", "phase-flip rate, linear in α²: the price of bigger cats"),
    stat("1.12% → 0.65%", "readout error, square pulse vs our shaped pulse through the buffer"),
  );
  const note = el(
    "p",
    "muted",
    "Every number comes from a script in the repo and is checked against a hand estimate or a convergence sweep.",
  );
  return section("What we found", grid, note);
}

function product(): HTMLElement {
  const ol = el("ol", "level-list");
  for (const [id, name] of LEVELS) {
    const li = el("li");
    const a = link(`#/learn/${id}`, "");
    a.append(el("span", "level-id", id), el("span", "", name));
    li.append(a);
    ol.append(li);
  }
  const lede = el(
    "p",
    "",
    "Each level asks you to predict first, then run the real Lindblad simulation in your browser and compare. The sandbox lets you snap operators into H and the jump list yourself.",
  );
  return section("The Academy", lede, ol);
}

function sponsors(): HTMLElement {
  const grid = el("div", "sponsor-grid");
  for (const s of SPONSORS) {
    const card = el("article", "sponsor-card");
    const head = el("header");
    head.append(el("h3", "", s.name), el("span", `badge ${s.status}`, s.status === "live" ? "live" : "demo only"));
    card.append(head, el("p", "sponsor-role", s.role), el("p", "", s.detail));
    grid.append(card);
  }
  const host = el("p", "muted");
  host.append("Hosted at ", link(VULTR_URL, VULTR_URL.replace("https://", "")), ".");
  return section("How we use each sponsor", grid, host);
}

function why(): HTMLElement {
  return section(
    "Why we built it",
    el(
      "p",
      "",
      "Cat qubits are hard to feel from equations alone. The fastest way we found to learn them was to predict an answer, simulate it, and be wrong in a specific way. The Academy is that loop, packaged so the next student does not need a JAX install or a physics PhD to feel why cat qubits work.",
    ),
  );
}

export function renderHome(root: HTMLElement): void {
  const wrap = el("div", "home");
  wrap.append(hero(), results(), product(), sponsors(), why());
  root.replaceChildren(wrap);
}
