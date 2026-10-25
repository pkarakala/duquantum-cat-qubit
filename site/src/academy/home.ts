/** Home page = the talk: one section per slide of the walkthrough, then the Academy, sponsors and why. Static content only. */

export const VULTR_URL = "https://66-42-119-3.sslip.io";

interface Sponsor {
  name: string;
  role: string;
  detail: string;
  status: "live" | "demo" | "used";
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
    name: "SpaceX · xAI Grok + Cursor",
    role: "Built the product",
    detail: "The Academy front end and API were built in Cursor with the Grok bot.",
    status: "used",
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

const TALK = `${import.meta.env.BASE_URL}talk/`;

interface Slide {
  id: string;
  tag: string;
  title: string;
  claim: string;
  figure: string;
  alt: string;
  stats: [string, string][];
  notes: string;
  extra?: { src: string; alt: string };
}

/** Same order, figures and numbers as the submitted walkthrough (slides/cat-qubit-walkthrough.pdf). */
export const SLIDES: Slide[] = [
  {
    id: "task1",
    tag: "Task 1",
    title: "First we built the cat",
    claim: "Two photons pumped in from a buffer, pairs pulled back out: the memory settles into two blobs.",
    figure: "cover_wigner.jpg",
    alt: "Wigner function snapshots of the memory inflating from vacuum into a two-lobed cat state between t = 0 and 3 µs",
    stats: [["0.035%", "cheaper truncation vs the big one"], ["two blobs + fringes", "a real superposition, not a mixture"]],
    notes: "The fringes between the blobs show it is a real superposition. We checked the result does not depend on how many photon levels we keep.",
  },
  {
    id: "s21",
    tag: "2.1 · Bit flips",
    title: "Too rare to simulate, so we take an eigenvalue",
    claim: "One bit flip every 2.6 s would need 300 million time steps. The bit flip is the Liouvillian's slowest eigenvalue.",
    figure: "s21_bitflips.jpg",
    alt: "Bit-flip rate Γ_X versus α² from the eigenvalue method and direct simulation, and the two escape channels as κ_a grows",
    stats: [["T_X = 2.6 s", "at α = 2.1"], ["10⁻⁸", "agreement with direct simulation"], ["½", "the search, by parity symmetry"]],
    notes: "Every way the state relaxes is an eigenvalue of the Liouvillian; the bit flip is the one closest to zero. On the right, two escape routes take over in turn as photon loss grows.",
  },
  {
    id: "s22",
    tag: "2.2 · Phase flips",
    title: "Every lost photon flips even and odd",
    claim: "So the phase-flip rate grows with photon number: Γ_Z ≈ 2κ_aα².",
    figure: "s22_phaseflips.jpg",
    alt: "Phase-flip rate Γ_Z versus α², linear with slope 2κ_a",
    stats: [["T_Z ≈ 2 µs", "at α = 2.1"], ["0.1%", "three methods agree"], ["1.3 × 10⁶", "phase flips per bit flip"]],
    notes: "Phase flips are the opposite story to bit flips: the bigger the cat, the more often it happens.",
  },
  {
    id: "s23",
    tag: "2.3 · Readout",
    title: "Nudge the memory, listen to the buffer",
    claim: "The two valleys give opposite signs, matching theory within 1%. But the signal rings at 3.2 MHz for about 1 µs.",
    figure: "s23_readout.jpg",
    alt: "Buffer field for the ±α codewords: opposite signs, with a damped 3.2 MHz ringing before settling",
    stats: [["±", "opposite signs for ±α"], ["1%", "agreement with theory"], ["3.2 MHz", "ringing, ~1 µs"]],
    notes: "The ringing is like a damped spring. It is exactly what Task 2.4 uses.",
  },
  {
    id: "s24a",
    tag: "2.4a · The real circuit",
    title: "No rotating-wave approximation",
    claim: "Full Josephson circuit: at the textbook pump frequency pairing switches off. Retune by −23 MHz and it works.",
    figure: "s24a_circuit.jpg",
    alt: "Pair conversion in the full circuit: flat at Δ_p = 0, following the g₂ model at Δ_p/2π = −23 MHz; pump frequency scan with a dip at −23 MHz",
    stats: [["a²b†", "the only term that survives at the pump frequency"], ["−23 MHz", "pump retune"]],
    notes: "We expand the sine term, and only the a²b† piece survives at the pump frequency: that is the pairing. The pump shifts the mode frequencies, so we retune it, and the blue line follows the model.",
    extra: { src: "s24a_equations.png", alt: "Circuit Hamiltonian H = ω_a a†a + ω_b b†b − 2E_J cos φ_Σ cos(φ̂ + φ_Δ), ATS bias φ_Δ = π/2, φ_Σ = −π/2 + ε_p cos ω_p t, and the sine expansion" },
  },
  {
    id: "s24b",
    tag: "2.4b · Pushing harder",
    title: "A harder drive doesn't buy a better trade",
    claim: "Signal and extra bit flips both grow as (drive strength)². Only the pulse shape changes the trade.",
    figure: "s24b_drive.jpg",
    alt: "Readout signal and added bit-flip rate versus drive strength, both quadratic",
    stats: [["(drive)²", "signal and flips scale alike"], ["2.6 s → 1 ms", "time between flips at 0.5 g₂"]],
    notes: "At 0.5 g₂ the cat goes from one flip every 2.6 seconds to one every millisecond while the drive is on.",
  },
  {
    id: "s24c",
    tag: "2.4c · Push in rhythm",
    title: "Push in rhythm with the ring",
    claim: "Drive at the 3.1 MHz ring, like pushing a swing at the right moment.",
    figure: "s24c_rhythm.jpg",
    alt: "Square versus resonant cosine readout pulses in a 2 µs window: lower readout error with fewer bit flips",
    stats: [["1.12% → 0.65%", "readout error in 2 µs"], ["fewer", "bit flips, same window"]],
    notes: "Same time window, 2 microseconds.",
  },
  {
    id: "s24d",
    tag: "2.4d · Why it works",
    title: "The system tells you how to read it",
    claim: "Ask for the best possible pulse with no hints: it oscillates at the ring frequency.",
    figure: "s24d_svd.jpg",
    alt: "Optimal pulse overlaid on a cosine at the ring frequency, and its spectrum peaking at 3.03 MHz next to the 3.14 MHz ring",
    stats: [["3.03 MHz", "spectral peak of the best pulse"], ["3.14 MHz", "the ring"]],
    notes: "A gradient optimizer with full freedom keeps that resonance too. Push at the system's own frequency.",
  },
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

/** "Γ_X" → Γ<sub>X</sub>; "κ_a" → κ<sub>a</sub>. */
export function withSubs(parent: HTMLElement, text: string): HTMLElement {
  for (const part of text.split(/(_[A-Za-z]+)/)) {
    if (part.startsWith("_")) parent.append(el("sub", "", part.slice(1)));
    else if (part) parent.append(part);
  }
  return parent;
}

function img(src: string, alt: string, className = ""): HTMLImageElement {
  const i = el("img", className);
  i.src = `${TALK}${src}`;
  i.alt = alt;
  i.loading = "lazy";
  i.decoding = "async";
  return i;
}

function slide(id: string, ...nodes: Node[]): HTMLElement {
  const s = el("section", "talk-slide");
  s.id = `talk-${id}`;
  s.append(...nodes);
  return s;
}

function cover(): HTMLElement {
  const text = el("div", "cover-text");
  text.append(
    el("p", "eyebrow", "DuQuantum 2026 · Alice & Bob · Standard track"),
    el("h1", "", "Cat qubits: bit flips, phase flips and a better readout"),
    el(
      "p",
      "lede",
      "A cat qubit stores a bit as light sitting in one of two valleys. We measured how often it fails, designed a better way to read it, and built a site that teaches all of it.",
    ),
    el("p", "team", "Pranav Reddy · Harshit Aggarwal · Halo Kwok · Xuanyu Zhu"),
  );
  const cta = el("p", "home-cta");
  cta.append(link("#talk-task1", "Start the walkthrough ↓", "button primary"), link("#/learn", "Jump to the Academy", "button"));
  text.append(cta);
  const art = el("figure", "cover-art");
  art.append(img("cover_wigner.jpg", "The memory inflating from vacuum into a two-lobed cat state"));
  const s = slide("cover", text, art);
  s.classList.add("talk-cover");
  return s;
}

function talkSlide(sl: Slide, n: number): HTMLElement {
  const head = el("header", "slide-head");
  head.append(el("p", "eyebrow", `${String(n).padStart(2, "0")} · ${sl.tag}`), el("h2", "", sl.title), withSubs(el("p", "slide-claim"), sl.claim));
  const fig = el("figure", sl.extra ? "slide-fig with-extra" : "slide-fig");
  fig.append(img(sl.figure, sl.alt));
  if (sl.extra) fig.append(img(sl.extra.src, sl.extra.alt, "slide-eq"));
  const stats = el("div", "slide-stats");
  for (const [v, l] of sl.stats) {
    const d = el("div", "stat");
    d.append(withSubs(el("strong"), v), withSubs(el("span"), l));
    stats.append(d);
  }
  return slide(sl.id, head, fig, stats, el("p", "slide-notes", sl.notes));
}

function academy(): HTMLElement {
  const head = el("header", "slide-head");
  head.append(
    el("p", "eyebrow", `${String(SLIDES.length + 1).padStart(2, "0")} · The product`),
    el("h2", "", "Cat Qubit Academy"),
    el("p", "slide-claim", "Eight short levels, from a photon in a box to designing this exact readout. Predict, play, check."),
  );
  const ol = el("ol", "level-list");
  for (const [id, name] of LEVELS) {
    const li = el("li");
    const a = link(`#/learn/${id}`, "");
    a.append(el("span", "level-id", id), el("span", "", name));
    li.append(a);
    ol.append(li);
  }
  const cta = el("p", "home-cta");
  cta.append(
    link("#/learn/L4", "L4 · the cat forms", "button primary"),
    link("#/learn/L8", "L8 · design the readout pulse", "button primary"),
    link("#/sandbox", "Sandbox", "button"),
    link("#/research", "Tasks, notebooks, results", "button"),
  );
  const fig = el("figure", "slide-fig");
  fig.append(img("academy.jpg", "Cat Qubit Academy level screen: predict, run the simulation, check"));
  return slide("academy", head, fig, ol, cta);
}

function sponsors(): HTMLElement {
  const grid = el("div", "sponsor-grid");
  for (const s of SPONSORS) {
    const card = el("article", "sponsor-card");
    const top = el("header");
    top.append(el("h3", "", s.name), el("span", `badge ${s.status}`, { live: "live", used: "dev tool", demo: "demo only" }[s.status]));
    card.append(top, el("p", "sponsor-role", s.role), el("p", "", s.detail));
    grid.append(card);
  }
  const host = el("p", "muted");
  host.append("Hosted at ", link(VULTR_URL, VULTR_URL.replace("https://", "")), ".");
  const head = el("header", "slide-head");
  head.append(el("p", "eyebrow", "Built with"), el("h2", "", "How we use each sponsor"));
  return slide("sponsors", head, grid, host);
}

function why(): HTMLElement {
  const head = el("header", "slide-head");
  head.append(el("p", "eyebrow", "Why"), el("h2", "", "Why we built it"));
  return slide(
    "why",
    head,
    el(
      "p",
      "slide-claim",
      "Cat qubits are hard to feel from equations alone. The fastest way we found to learn them was to predict an answer, simulate it, and be wrong in a specific way. The Academy is that loop, packaged so the next student does not need a JAX install or a physics PhD to feel why cat qubits work.",
    ),
  );
}

function dots(ids: string[]): HTMLElement {
  const nav = el("nav", "talk-dots");
  nav.setAttribute("aria-label", "Walkthrough sections");
  ids.forEach((id, i) => {
    const a = link(`#talk-${id}`, "");
    a.setAttribute("aria-label", `Section ${i + 1}`);
    nav.append(a);
  });
  return nav;
}

let keysBound = false;

/** ←/→ (and PageUp/PageDown) step through the sections like slides, only while the talk is on screen. */
function bindKeys(): void {
  if (keysBound) return;
  keysBound = true;
  document.addEventListener("keydown", (e) => {
    const sections = [...document.querySelectorAll<HTMLElement>(".talk-slide")];
    if (!sections.length || e.altKey || e.metaKey || e.ctrlKey) return;
    const target = e.target as HTMLElement | null;
    if (target?.closest("input, textarea, select, [contenteditable]")) return;
    const step = e.key === "ArrowRight" || e.key === "PageDown" ? 1 : e.key === "ArrowLeft" || e.key === "PageUp" ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const y = window.scrollY + 80;
    let i = sections.findIndex((s) => s.offsetTop > y) - 1;
    if (i < -1) i = sections.length - 1;
    const next = sections[Math.min(sections.length - 1, Math.max(0, i + step))];
    next.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

export function renderHome(root: HTMLElement): void {
  const wrap = el("div", "home talk");
  const all = [cover(), ...SLIDES.map((s, i) => talkSlide(s, i + 1)), academy(), sponsors(), why()];
  wrap.append(dots(all.map((s) => s.id.replace(/^talk-/, ""))), ...all);
  // In-page jumps must not touch location.hash: the router owns it.
  wrap.addEventListener("click", (e) => {
    const a = (e.target as HTMLElement).closest<HTMLAnchorElement>('a[href^="#talk-"]');
    if (!a) return;
    e.preventDefault();
    document.getElementById(a.getAttribute("href")!.slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  root.replaceChildren(wrap);
  bindKeys();
}
