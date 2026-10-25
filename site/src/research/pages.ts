/** Results pages: Section 2 numbers from results/, exported by site/scripts/export_results.py. */

import R from "./results.json";

const REPO = "https://github.com/pkarakala/duquantum-cat-qubit/blob/main/";
const C = { blue: "#0072B2", orange: "#E69F00", green: "#009E73", red: "#D55E00", pink: "#CC79A7", sky: "#56B4E9" };

type Trace = Record<string, unknown>;
type Layout = Record<string, unknown>;

function css(name: string, fallback: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

async function draw(el: HTMLElement, data: Trace[], layout: Layout): Promise<void> {
  const fg = css("--fg", "#1a1a1a");
  const grid = css("--border", "#c8c4ba");
  const axis = (a: unknown) => ({ gridcolor: grid, zeroline: false, linecolor: grid, ...(a as object) });
  try {
    const Plotly = (await import("plotly.js-dist-min")).default;
    await Plotly.react(
      el,
      data,
      {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: fg, family: "system-ui, sans-serif", size: 13 },
        margin: { l: 64, r: 16, t: 28, b: 48 },
        legend: { orientation: "h", y: -0.22 },
        ...layout,
        xaxis: axis(layout.xaxis),
        yaxis: axis(layout.yaxis),
      },
      { displayModeBar: false, responsive: true },
    );
  } catch {
    el.textContent = "Plotly did not load; the numbers above are the result.";
  }
}

function h(tag: string, cls = "", text = ""): HTMLElement {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text) el.textContent = text;
  return el;
}

function html(tag: string, cls: string, inner: string): HTMLElement {
  const el = h(tag, cls);
  el.innerHTML = inner;
  return el;
}

function stats(items: [string, string][]): HTMLElement {
  const row = h("div", "stats");
  for (const [value, label] of items) {
    const tile = h("div", "stat");
    tile.append(html("div", "stat-value", value), html("div", "stat-label", label));
    row.append(tile);
  }
  return row;
}

function figure(caption: string): { fig: HTMLElement; plot: HTMLElement } {
  const fig = h("figure", "res-fig");
  const plot = h("div", "res-plot");
  fig.append(plot, html("figcaption", "", caption));
  return { fig, plot };
}

function table(head: string[], rows: (string | number)[][]): HTMLElement {
  const wrap = h("div", "res-table");
  const t = document.createElement("table");
  t.innerHTML =
    `<thead><tr>${head.map((x) => `<th>${x}</th>`).join("")}</tr></thead>` +
    `<tbody>${rows.map((r) => `<tr>${r.map((x) => `<td>${x}</td>`).join("")}</tr>`).join("")}</tbody>`;
  wrap.append(t);
  return wrap;
}

function reproduce(notebook: string, cmd: string): HTMLElement {
  return html("p", "res-src", `Reproduce: <code>${cmd}</code> · <a href="${REPO}notebooks/${notebook}" target="_blank" rel="noopener">notebook</a>`);
}

function sci(x: number, d = 2): string {
  if (x === 0) return "0";
  const e = Math.floor(Math.log10(Math.abs(x)));
  if (e >= -2 && e < 3) return x.toPrecision(d + 1);
  return `${(x / 10 ** e).toFixed(d)}×10<sup>${e}</sup>`;
}

function shell(root: HTMLElement, title: string, answer: string): HTMLElement {
  const page = h("article", "res");
  page.append(html("h1", "", title), html("p", "lede res-answer", answer));
  root.replaceChildren(page);
  return page;
}

/** log-linear interpolation of y(x) on sorted points */
function logInterp(xs: number[], ys: number[], x: number): number {
  if (x <= xs[0]) return ys[0];
  for (let i = 1; i < xs.length; i++) {
    if (x <= xs[i]) {
      const f = (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
      return Math.exp(Math.log(ys[i - 1]) * (1 - f) + Math.log(ys[i]) * f);
    }
  }
  return ys[ys.length - 1];
}

function duration(us: number): string {
  if (us < 1e3) return `${us.toPrecision(3)} µs`;
  if (us < 1e6) return `${(us / 1e3).toPrecision(3)} ms`;
  if (us < 6e7) return `${(us / 1e6).toPrecision(3)} s`;
  return `${(us / 6e7).toPrecision(3)} min`;
}

export function showBitFlips(root: HTMLElement): void {
  const gx = R.gx;
  const at = gx.eig.find((e) => e.alpha === 2.1)!;
  const page = shell(
    root,
    "Task 2.1 · Bit flips Γ<sub>X</sub>",
    `At α = 2.1, Γ<sub>X</sub> = ${sci(at.gx)} µs⁻¹: one bit flip every ${duration(1 / at.gx)}. Time-domain fits reach α = 1.4; the slowest odd Liouvillian eigenvalue −λ<sub>odd</sub> covers larger cats. Where both run they agree to 10⁻⁸.`,
  );
  const maxRel = Math.max(...gx.td.map((c) => Math.abs(c.rel)));
  page.append(
    stats([
      [`${sci(at.gx)} µs⁻¹`, "Γ<sub>X</sub> at α = 2.1"],
      [duration(1 / at.gx), "T<sub>X</sub> = 1/Γ<sub>X</sub>"],
      [`${gx.gamma_fit}`, "γ in Γ<sub>X</sub> ∝ e<sup>−γα²</sup>, 0.7 ≤ α ≤ 1.4"],
      [sci(maxRel, 1), "max |fit − eigen| / eigen"],
    ]),
  );

  const a = figure(
    "Squares: time-domain fits of Re⟨a⟩(t). Line: −λ<sub>odd</sub> at the largest converged (N<sub>a</sub>, N<sub>b</sub>). Dotted and dash-dot: one-mode one-loss and two-loss routes (slopes, not sizes).",
  );
  page.append(a.fig);
  void draw(
    a.plot,
    [
      { x: gx.one_loss.map((p) => p[0]), y: gx.one_loss.map((p) => p[1]), name: "lose one photon", mode: "lines", line: { color: C.green, dash: "dot" } },
      { x: gx.two_loss.map((p) => p[0]), y: gx.two_loss.map((p) => p[1]), name: "lose two photons", mode: "lines", line: { color: C.pink, dash: "dashdot" } },
      {
        x: gx.eig.map((e) => e.alpha ** 2),
        y: gx.eig.map((e) => e.gx),
        name: "−λ<sub>odd</sub> (eigenvalue)",
        mode: "lines+markers",
        line: { color: C.blue },
        customdata: gx.eig.map((e) => [e.alpha, `${e.na}×${e.nb}`]),
        hovertemplate: "α = %{customdata[0]}<br>Γ<sub>X</sub> = %{y:.3e} µs⁻¹<br>N<sub>a</sub>×N<sub>b</sub> = %{customdata[1]}<extra></extra>",
      },
      { x: gx.td.map((c) => c.alpha ** 2), y: gx.td.map((c) => c.fit), name: "time-domain fit", mode: "markers", marker: { symbol: "square-open", size: 10, color: css("--fg", "#1a1a1a") } },
    ],
    {
      xaxis: { title: { text: "α²" }, range: [0.4, 6.4] },
      yaxis: { title: { text: "Γ<sub>X</sub> (µs⁻¹)" }, type: "log", exponentformat: "power", range: [-9, -1.5] },
    },
  );

  const b = figure("Γ<sub>X</sub> ∝ κ<sub>a</sub><sup>s</sup> from a κ<sub>a</sub> × {¼, ½, 1, 2, 4} sweep. s = 1: one loss per flip. s = 2: two losses. The handover is complete by α = 2.1.");
  page.append(b.fig);
  void draw(
    b.plot,
    [
      { x: gx.kappa_slope.map((p) => p[0]), y: gx.kappa_slope.map((p) => p[1]), name: "fit", mode: "lines+markers", line: { color: C.blue } },
      { x: [0.4, 6.4], y: [1, 1], name: "s = 1", mode: "lines", line: { color: C.green, dash: "dot" } },
      { x: [0.4, 6.4], y: [2, 2], name: "s = 2", mode: "lines", line: { color: C.pink, dash: "dashdot" } },
    ],
    { xaxis: { title: { text: "α²" }, range: [0.4, 6.4] }, yaxis: { title: { text: "d ln Γ<sub>X</sub> / d ln κ<sub>a</sub>" }, range: [0.8, 2.3] } },
  );

  // Bias explorer: Γ<sub>X</sub> from the eigenvalue table, Γ<sub>Z</sub> from the ideal-cat law 2κ<sub>a</sub>α² coth 2α².
  const box = h("section", "res-card");
  box.append(h("h2", "", "Bias at your α"));
  const label = h("label", "res-slider");
  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = "1.0";
  slider.max = "2.5";
  slider.step = "0.05";
  slider.value = "2.1";
  const out = h("div", "stats");
  label.append(html("span", "", "α"), slider);
  box.append(label, out);
  const xs = gx.eig.map((e) => e.alpha);
  const ys = gx.eig.map((e) => e.gx);
  const ka = R.params.kappa_a;
  const update = () => {
    const al = Number(slider.value);
    const g = logInterp(xs, ys, al);
    const n = al * al;
    const gz = (2 * ka * n) / Math.tanh(2 * n);
    out.replaceChildren(
      ...stats([
        [`${al.toFixed(2)}`, "α"],
        [`${sci(g)} µs⁻¹`, "Γ<sub>X</sub> (eigenvalue, interpolated)"],
        [`${gz.toFixed(3)} µs⁻¹`, "Γ<sub>Z</sub> ≈ 2κ<sub>a</sub>α² coth 2α²"],
        [sci(gz / g, 1), "bias Γ<sub>Z</sub> / Γ<sub>X</sub>"],
      ]).children,
    );
  };
  slider.addEventListener("input", update);
  update();
  page.append(box);

  page.append(
    table(
      ["α", "Γ<sub>X</sub> fit (µs⁻¹)", "−λ<sub>odd</sub> (µs⁻¹)", "rel. diff"],
      gx.td.map((c) => [c.alpha, c.fit.toExponential(4), c.eig.toExponential(4), c.rel.toExponential(1)]),
    ),
    reproduce("06_task_2_1_bit_flips.ipynb", "python -m tasks.task_2_1"),
  );
}

export function showPhaseFlips(root: HTMLElement): void {
  const gz = R.gz;
  const last = gz.cases[gz.cases.length - 1];
  const g21 = gz.cases.find((c) => c.alpha === 2.1)!.eig;
  const gx21 = R.gx.eig.find((e) => e.alpha === 2.1)!.gx;
  const page = shell(
    root,
    "Task 2.2 · Phase flips Γ<sub>Z</sub>",
    `Γ<sub>Z</sub> grows linearly with cat size: fitted slope ${gz.slope.toFixed(4)} µs⁻¹ per photon against ${gz.slope_pred.toFixed(4)} predicted by 2κ<sub>a</sub>α². At α = 2.1, Γ<sub>Z</sub> = ${g21.toFixed(4)} µs⁻¹, one phase flip every ${(1 / g21).toFixed(2)} µs, so the bias Γ<sub>Z</sub>/Γ<sub>X</sub> ≈ ${sci(g21 / gx21, 1)}.`,
  );
  const maxRel = Math.max(...gz.cases.map((c) => Math.abs(c.rel)));
  page.append(
    stats([
      [`${g21.toFixed(3)} µs⁻¹`, "Γ<sub>Z</sub> at α = 2.1"],
      [`${(1 / g21).toFixed(2)} µs`, "T<sub>Z</sub> = 1/Γ<sub>Z</sub>"],
      [sci(g21 / gx21, 1), "bias Γ<sub>Z</sub> / Γ<sub>X</sub>"],
      [sci(maxRel, 1), "max |fit − eigen| / eigen"],
    ]),
  );
  const a = figure(
    "Squares: ⟨Π⟩(t) = Π<sub>∞</sub> + A e<sup>−Γ<sub>Z</sub> t</sup> fits from the even cat. Line: slowest nonzero even eigenvalue. Dashed: ideal-cat 2κ<sub>a</sub>α² coth 2α².",
  );
  page.append(a.fig);
  const n2 = Array.from({ length: 50 }, (_, i) => 1.2 + (i * (6 - 1.2)) / 49);
  const ka = R.params.kappa_a;
  void draw(
    a.plot,
    [
      { x: n2, y: n2.map((n) => (2 * ka * n) / Math.tanh(2 * n)), name: "2κ<sub>a</sub>α² coth 2α²", mode: "lines", line: { color: C.orange, dash: "dash" } },
      { x: gz.cases.map((c) => c.alpha ** 2), y: gz.cases.map((c) => c.eig), name: "eigenvalue", mode: "lines", line: { color: C.blue } },
      { x: gz.cases.map((c) => c.alpha ** 2), y: gz.cases.map((c) => c.fit), name: "time-domain fit", mode: "markers", marker: { symbol: "square-open", size: 10, color: C.blue } },
    ],
    { xaxis: { title: { text: "α²" } }, yaxis: { title: { text: "Γ<sub>Z</sub> (µs⁻¹)" } } },
  );
  page.append(
    table(
      ["α", "Γ<sub>Z</sub> fit (µs⁻¹)", "eigenvalue (µs⁻¹)", "Π∞", "rel. diff", "ideal cat"],
      gz.cases.map((c) => [c.alpha, c.fit.toFixed(6), c.eig.toFixed(6), c.offset.toExponential(2), c.rel.toExponential(1), c.ideal.toFixed(6)]),
    ),
    html("p", "res-note", `Largest case α = ${last.alpha}: Γ<sub>Z</sub> is ${(100 * (1 - last.fit / last.ideal)).toFixed(2)}% below the ideal law, because the memory holds n̄ ≈ α² − 0.007 photons.`),
    reproduce("07_task_2_2_phase_flips.ipynb", "python -m tasks.task_2_2"),
  );
}

export function showReadout(root: HTMLElement): void {
  const r = R.readout;
  const page = shell(
    root,
    "Task 2.3 · Buffer readout",
    `A weak memory drive H<sub>Z</sub> = ε<sub>Z</sub>(a + a†) makes the two codewords leak opposite buffer fields, Re⟨b⟩<sub>±</sub> → ∓b<sub>0</sub> with b<sub>0</sub> = ε<sub>Z</sub>/(2αg<sub>2</sub>). At α = 2.1, ε<sub>Z</sub> = 0.05g<sub>2</sub> the plateau matches b<sub>0</sub> to ${Math.abs(100 * r.contrast_err).toFixed(2)}%.`,
  );
  page.append(
    stats([
      [r.b0.toFixed(4), "b<sub>0</sub> = ε<sub>Z</sub>/(2αg<sub>2</sub>)"],
      [`${r.ring_us} µs`, `ring period (linear model ${r.lin_period_us} µs)`],
      [`${r.settle_us} µs`, "settles within 1%"],
      [`${Math.abs(100 * r.contrast_err).toFixed(2)}%`, "plateau vs b<sub>0</sub>"],
    ]),
  );
  const a = figure(
    "Full two-mode model, (N<sub>a</sub>, N<sub>b</sub>) = (32, 12). The memory–buffer pair is an underdamped oscillator, b̈ + (κ<sub>b</sub>/2)ḃ + (2g<sub>2</sub>α)²b = drive, so the signal rings before it settles.",
  );
  page.append(a.fig);
  void draw(
    a.plot,
    [
      { x: r.t, y: r.re_plus, name: "|+α⟩", mode: "lines", line: { color: C.blue } },
      { x: r.t, y: r.re_minus, name: "|−α⟩", mode: "lines", line: { color: C.red } },
      { x: [0, 4], y: [-1, -1], name: "∓1", mode: "lines", line: { color: "#777", dash: "dot", width: 1 }, showlegend: false },
      { x: [0, 4], y: [1, 1], mode: "lines", line: { color: "#777", dash: "dot", width: 1 }, showlegend: false },
    ],
    {
      xaxis: { title: { text: "t (µs)" } },
      yaxis: { title: { text: "Re⟨b⟩ / b₀" } },
      shapes: [{ type: "line", x0: r.settle_us, x1: r.settle_us, y0: 0, y1: 1, yref: "paper", line: { color: C.orange, dash: "dot" } }],
    },
  );
  page.append(reproduce("08_task_2_3_readout.ipynb", "python -m tasks.task_2_3"));
}

const FAMILY: Record<string, { name: string; plain: string; color: string; symbol: string }> = {
  square: { name: "square", plain: "square", color: "#777777", symbol: "square" },
  res: { name: "cos ω<sub>r</sub> t", plain: "cos ωᵣt (resonant)", color: C.blue, symbol: "circle" },
  bang: { name: "sgn(cos ω<sub>r</sub> t)", plain: "sgn(cos ωᵣt) (bang-bang)", color: C.orange, symbol: "triangle-up" },
};

export function showBetterReadout(root: HTMLElement): void {
  const b = R.better;
  const pct = (x: number) => `${(100 * x).toFixed(2)}%`;
  const page = shell(
    root,
    "Task 2.4 · A better readout",
    `Drive the memory at the buffer's ringing frequency ω<sub>r</sub>/2π = ${b.omega_r_MHz} MHz. At α = 2.1 over T = ${b.T} µs the readout error ε<sub>ro</sub> falls from ${pct(b.best.square.err1)} (square) to ${pct(b.best.res.err1)} (cos ω<sub>r</sub>t), and from ${pct(b.best05.square)} to ${pct(b.best05.res)} with a 50% efficient detector. In the full pumped circuit, pairing needs the pump retuned by Δ<sub>p</sub>/2π = −23 MHz.`,
  );
  page.append(
    stats([
      [`${pct(b.best.square.err1)} → ${pct(b.best.res.err1)}`, "ε<sub>ro</sub>, η = 1"],
      [`${pct(b.best05.square)} → ${pct(b.best05.res)}`, "ε<sub>ro</sub>, η = 0.5"],
      [`${b.omega_r_MHz} MHz`, "ω<sub>r</sub>/2π = √((2g<sub>2</sub>α)² − κ<sub>b</sub>²/16)/2π"],
      ["−23 MHz", "pump retune Δ<sub>p</sub>/2π"],
    ]),
    html(
      "p",
      "res-note",
      "ε<sub>ro</sub> = ½ erfc √(η SNR/2) + P<sub>flip</sub>, SNR = κ<sub>b</sub>∫|⟨b⟩<sub>+</sub> − ⟨b⟩<sub>−</sub>|² dt over the pulse and 2.5 µs of free decay.",
    ),
  );

  // Pulse explorer
  const card = h("section", "res-card");
  card.append(h("h2", "", "Pick a pulse"));
  const controls = h("div", "row");
  const fam = document.createElement("select");
  fam.setAttribute("aria-label", "Pulse shape");
  for (const [k, v] of Object.entries(FAMILY)) fam.append(new Option(v.plain, k));
  fam.value = "res";
  const lvl = document.createElement("select");
  lvl.setAttribute("aria-label", "Peak drive");
  for (const l of [0.5, 0.75, 1]) lvl.append(new Option(`peak ${l} g₂`, String(l)));
  lvl.value = "0.75";
  controls.append(fam, lvl);
  const out = h("div", "stats");
  const pulsePlot = h("div", "res-plot res-plot-short");
  const bPlot = h("div", "res-plot res-plot-short");
  card.append(controls, out, pulsePlot, bPlot);
  page.append(card);
  const update = () => {
    const row = b.rows.find((r) => r.family === fam.value && r.level === Number(lvl.value))!;
    out.replaceChildren(
      ...stats([
        [row.snr.toFixed(2), "SNR"],
        [sci(row.p_flip, 2), "P<sub>flip</sub>"],
        [pct(row.err1), "ε<sub>ro</sub> (η = 1)"],
        [pct(row.err05), "ε<sub>ro</sub> (η = 0.5)"],
      ]).children,
    );
    const color = FAMILY[row.family].color;
    void draw(pulsePlot, [{ x: b.t, y: row.pulse, mode: "lines", line: { color, shape: "hv" }, name: "ε<sub>Z</sub>/g₂" }], {
      xaxis: { title: { text: "t (µs)" } },
      yaxis: { title: { text: "ε<sub>Z</sub>(t) / g₂" } },
      showlegend: false,
      height: 220,
    });
    void draw(
      bPlot,
      [
        { x: b.t, y: row.b_re, mode: "lines", line: { color }, name: "Re⟨b⟩₊" },
        { x: b.t, y: row.b_im, mode: "lines", line: { color, dash: "dot" }, name: "Im⟨b⟩₊" },
      ],
      { xaxis: { title: { text: "t (µs)" } }, yaxis: { title: { text: "⟨b⟩₊" } }, height: 240 },
    );
  };
  fam.addEventListener("change", update);
  lvl.addEventListener("change", update);
  update();

  const a = figure("SNR against P<sub>flip</sub> for each shape at ε<sub>max</sub> = 0.5, 0.75, 1 g<sub>2</sub>. Resonant shapes reach more signal for the same flips because the buffer amplifies a drive in step with its 3.14 MHz ringing.");
  page.append(a.fig);
  void draw(
    a.plot,
    Object.entries(FAMILY).map(([k, v]) => {
      const rows = b.rows.filter((r) => r.family === k).sort((x, y) => x.level - y.level);
      return {
        x: rows.map((r) => r.p_flip),
        y: rows.map((r) => r.snr),
        name: v.name,
        mode: "lines+markers",
        marker: { symbol: v.symbol, size: 9, color: v.color },
        line: { color: v.color },
        customdata: rows.map((r) => [r.level, (100 * r.err1).toFixed(2)]),
        hovertemplate: "ε<sub>max</sub> = %{customdata[0]} g₂<br>SNR %{y:.2f}<br>P<sub>flip</sub> %{x:.2e}<br>ε<sub>ro</sub> %{customdata[1]}%<extra></extra>",
      };
    }),
    { xaxis: { title: { text: "P<sub>flip</sub>" }, type: "log", exponentformat: "power" }, yaxis: { title: { text: "SNR" } } },
  );

  const c = figure("Full pumped ATS circuit without the RWA, 150 ns, no loss: largest ⟨a†a⟩ mismatch against the g<sub>2</sub>(a²b† + h.c.) model versus pump detuning. Pair conversion works only near −23 MHz.");
  page.append(c.fig);
  void draw(
    c.plot,
    [{ x: b.circuit.map((p) => p[0]), y: b.circuit.map((p) => p[1]), mode: "lines+markers", line: { color: C.blue }, name: "mismatch" }],
    {
      xaxis: { title: { text: "Δ<sub>p</sub> / 2π (MHz)" } },
      yaxis: { title: { text: "max<sub>t</sub> |Δ⟨a†a⟩|" } },
      showlegend: false,
      shapes: [{ type: "line", x0: -23, x1: -23, y0: 0, y1: 1, yref: "paper", line: { color: C.orange, dash: "dot" } }],
    },
  );

  const d = figure("Gradient optimization through the simulator (jax.grad through dynamiqs), T = 0.5 µs, from the bang-bang start. It keeps the sign changes at the ringing period and adds at most 16% signal per flip over its start.");
  page.append(d.fig);
  void draw(
    d.plot,
    [
      { x: b.opt.t, y: b.opt.t.map(() => b.opt.peak), name: "square", mode: "lines", line: { color: "#777777", shape: "hvh" } },
      { x: b.opt.t, y: b.opt.start, name: "start: sgn(cos ω<sub>r</sub> t)", mode: "lines", line: { color: C.orange, dash: "dash", shape: "hvh" } },
      { x: b.opt.t, y: b.opt.best, name: "optimized", mode: "lines", line: { color: C.blue, shape: "hvh" } },
    ],
    { xaxis: { title: { text: "t (µs)" } }, yaxis: { title: { text: "ε<sub>Z</sub>(t) / g₂" } } },
  );
  page.append(reproduce("09_task_2_4_better_readout.ipynb", "python -m research.s2.pulse_eval"));
}
