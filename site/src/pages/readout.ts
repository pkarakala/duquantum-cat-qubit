import type { Data } from "plotly.js-dist-min";
import { plot } from "../components/plot";
import { formatValue, openCard, renderChip } from "../components/provenance";
import type { Bundle } from "../data/types";
import { h, scrollTable, uniqueId } from "../lib/dom";
import { defaultEpsIndex, epsGrid, fmtEps, sameEps, tradeoffAlphas, tradeoffFor } from "../lib/readout";

function stepTrace(t: number[], eps: number[], name: string, color: string): Data {
  const x: number[] = [];
  const y: number[] = [];
  for (let i = 0; i < eps.length; i++) {
    x.push(t[i], t[i + 1] ?? t[i]);
    y.push(eps[i], eps[i]);
  }
  return { type: "scatter", mode: "lines", name, x, y, line: { color, width: 2, shape: "linear" }, hovertemplate: "t=%{x:.3f} µs<br>ε=%{y:.4g}<extra></extra>" } as Data;
}

export function render(root: HTMLElement, b: Bundle): void {
  const r = b.readout;
  const grid = epsGrid(r);
  const alphas = tradeoffAlphas(r);
  let aIdx = alphas.findIndex((a) => sameEps(a, r.alpha));
  if (aIdx < 0) aIdx = 0;
  let eIdx = defaultEpsIndex(grid);

  const epsId = uniqueId("eps");
  const epsLabel = h("label", { for: epsId }, "");
  const epsSlider = h("input", {
    id: epsId,
    type: "range",
    min: "0",
    max: String(Math.max(grid.length - 1, 0)),
    step: "1",
    value: String(eIdx),
    "aria-label": "Readout drive ε_Z over g₂",
  });

  let alphaSelect: HTMLSelectElement | null = null;
  if (alphas.length > 1) {
    const aId = uniqueId("alpha");
    alphaSelect = h("select", { id: aId, "aria-label": "Cat size α" });
    for (const [i, a] of alphas.entries()) {
      const opt = h("option", { value: String(i) }, `α = ${a}`);
      if (i === aIdx) opt.selected = true;
      alphaSelect.append(opt);
    }
  }

  const sigEl = h("div", { class: "plot", "aria-label": "Buffer quadratures versus time" });
  const tradeEl = h("div", { class: "plot", "aria-label": "SNR versus bit-flip cost" });
  const pulseEl = h("div", { class: "plot", "aria-label": "Pulse shape" });
  const pulseSigEl = h("div", { class: "plot", "aria-label": "Pulse signal" });
  const pulseNames = Object.keys(r.pulses);
  let pulseName = pulseNames[0] ?? "";
  const pulseId = uniqueId("pulse");
  const pulseSelect = h("select", { id: pulseId, "aria-label": "Pulse shape" });
  for (const name of pulseNames) {
    const opt = h("option", { value: name }, name);
    if (name === pulseName) opt.selected = true;
    pulseSelect.append(opt);
  }
  const pulseMeta = h("p", {});
  const pulseTableHost = h("div", {});

  const lin = r.linresp;
  const linCard = h(
    "div",
    { class: "panel" },
    h("h2", {}, "Linear-response ringing"),
    h("p", {}, `${lin.freq_MHz} MHz, Q ≈ ${lin.Q}, settle ${lin.t5} µs (5%) / ${lin.t1} µs (1%).`),
    lin.id ? h("div", { class: "chips" }, renderChip(lin.id, b.byId)) : null,
  );

  const controls = h("div", { class: "row" });
  if (alphaSelect) {
    const aId = alphaSelect.id;
    controls.append(h("label", { for: aId }, "α"), alphaSelect);
  }
  controls.append(epsLabel, epsSlider);

  root.append(
    h("h1", {}, "Readout designer"),
    h(
      "p",
      { class: "lede" },
      "ε_Z snaps to a precomputed grid — the browser does not solve anything. SNR at 1 µs is the reward; Γ_X/Γ_X(0) is the cost that matters.",
    ),
    controls,
    h("h2", {}, "Buffer signals ⟨b⟩±"),
    sigEl,
    h("h2", {}, "Trade-off"),
    tradeEl,
    linCard,
    h("h2", {}, "Pulses"),
    pulseNames.length ? h("div", { class: "row" }, h("label", { for: pulseId }, "Pulse"), pulseSelect) : h("p", {}, "No pulse shapes in this bundle."),
    pulseMeta,
    pulseEl,
    pulseSigEl,
    pulseTableHost,
  );

  const setEpsLabel = () => {
    const e = grid[eIdx]?.eps_over_g2;
    const text = `ε_Z = ${fmtEps(e ?? NaN)}`;
    epsLabel.textContent = text;
    epsSlider.setAttribute("aria-valuetext", text);
  };

  const drawSignals = () => {
    const s = grid[eIdx] ?? r.signals;
    void plot(
      sigEl,
      [
        { type: "scatter", mode: "lines", name: "Re ⟨b⟩₊", x: s.t_us, y: s.b_plus_re, line: { color: "#0072B2" } },
        { type: "scatter", mode: "lines", name: "Im ⟨b⟩₊", x: s.t_us, y: s.b_plus_im, line: { color: "#56B4E9", dash: "dash" } },
        { type: "scatter", mode: "lines", name: "Re ⟨b⟩₋", x: s.t_us, y: s.b_minus_re, line: { color: "#D55E00" } },
        { type: "scatter", mode: "lines", name: "Im ⟨b⟩₋", x: s.t_us, y: s.b_minus_im, line: { color: "#E69F00", dash: "dash" } },
      ] as Data[],
      { xaxis: { title: { text: "t (µs)" } }, yaxis: { title: { text: "⟨b⟩" } }, legend: { orientation: "h" } },
    );
  };

  const drawTrade = () => {
    const alpha = alphas[aIdx] ?? r.alpha;
    const pts = tradeoffFor(r, alpha);
    const cur = grid[eIdx]?.eps_over_g2;
    const x = pts.map((p) => p.gamma_x_rel);
    const y = pts.map((p) => p.snr_T1us);
    const sizes = pts.map((p) => (cur !== undefined && sameEps(p.eps_over_g2, cur) ? 16 : 8));
    const colors = pts.map((p) => (p.ok === false ? "#999999" : "#0072B2"));
    void plot(
      tradeEl,
      [
        {
          type: "scatter",
          mode: "markers",
          name: `α = ${alpha}`,
          x,
          y,
          customdata: pts.map((p) => p.id ?? ""),
          marker: { size: sizes, color: colors, line: { width: sizes.map((s) => (s > 10 ? 2 : 0)), color: "#111" } },
          text: pts.map((p) => `${fmtEps(p.eps_over_g2)}${p.ok === false ? " (unconverged)" : ""}`),
          hovertemplate: "Γ_X/Γ_X(0)=%{x:.3g}<br>SNR(1 µs)=%{y:.3g}<br>%{text}<br>%{customdata}<extra></extra>",
        } as Data,
      ],
      { xaxis: { title: { text: "Γ_X / Γ_X(0)" }, type: "log" }, yaxis: { title: { text: "SNR (1 µs)" }, type: "log" } },
      {
        onClick: (cd) => {
          if (typeof cd === "string" && cd) openCard(cd, b.byId);
        },
      },
    );
  };

  const drawPulse = () => {
    const p = r.pulses[pulseName];
    if (!p) {
      pulseMeta.textContent = "";
      pulseTableHost.replaceChildren();
      return;
    }
    pulseMeta.replaceChildren(
      `SNR = ${formatValue(p.snr, null)}`,
      " · ",
      `cost = ${formatValue(p.cost, null)}`,
      p.snr_method ? ` (${p.snr_method})` : "",
      " ",
      p.id ? renderChip(p.id, b.byId) : "",
      p.cost_id ? renderChip(p.cost_id, b.byId) : "",
    );
    void plot(pulseEl, [stepTrace(p.t_us, p.eps, pulseName, "#0072B2")], {
      xaxis: { title: { text: "t (µs)" } },
      yaxis: { title: { text: "ε (rad/µs)" } },
      title: { text: pulseName },
    });
    if (p.signal) {
      pulseSigEl.hidden = false;
      void plot(
        pulseSigEl,
        [{ type: "scatter", mode: "lines", name: "|Δb|", x: p.signal.t_us, y: p.signal.db_abs, line: { color: "#009E73" } } as Data],
        { xaxis: { title: { text: "t (µs)" } }, yaxis: { title: { text: "|Δ⟨b⟩|" } } },
      );
    } else {
      pulseSigEl.hidden = true;
    }
    const rows = Object.entries(r.pulses).map(([name, q]) =>
      h(
        "tr",
        {},
        h("th", { scope: "row" }, name),
        h("td", {}, formatValue(q.snr, null)),
        h("td", {}, formatValue(q.cost, null)),
        h("td", {}, q.id ? renderChip(q.id, b.byId) : "n/a"),
        h("td", {}, q.cost_id ? renderChip(q.cost_id, b.byId) : "n/a"),
      ),
    );
    pulseTableHost.replaceChildren(
      scrollTable(
        h(
          "table",
          {},
          h("thead", {}, h("tr", {}, ...["pulse", "SNR", "cost", "snr record", "cost record"].map((c) => h("th", { scope: "col" }, c)))),
          h("tbody", {}, ...rows),
        ),
        "Pulse comparison",
      ),
    );
  };

  const redraw = () => {
    setEpsLabel();
    drawSignals();
    drawTrade();
    drawPulse();
  };

  epsSlider.addEventListener("input", () => {
    eIdx = Number(epsSlider.value);
    redraw();
  });
  alphaSelect?.addEventListener("change", () => {
    aIdx = Number(alphaSelect!.value);
    redraw();
  });
  pulseSelect.addEventListener("change", () => {
    pulseName = pulseSelect.value;
    drawPulse();
  });

  redraw();
}
