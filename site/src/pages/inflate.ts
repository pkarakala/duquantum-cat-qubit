import type { Data } from "plotly.js-dist-min";
import { plot } from "../components/plot";
import { renderChip } from "../components/provenance";
import type { Bundle } from "../data/types";
import { h, uniqueId } from "../lib/dom";
import { WIGNER_SCALE, wignerRange } from "../lib/wigner";

const FPS = 8;
let timer: ReturnType<typeof setInterval> | undefined;

function stopTimer() {
  if (timer !== undefined) {
    clearInterval(timer);
    timer = undefined;
  }
}

export function render(root: HTMLElement, b: Bundle): void {
  stopTimer();
  const { inflation: d, byId } = b;
  const frames = d.wigner.frames;
  const [zmin, zmax] = wignerRange(frames);
  const a2 = (d.alpha ?? 2.1) * (d.alpha ?? 2.1);
  let idx = 0;

  const tId = uniqueId("inflate-t");
  const tLabel = h("label", { for: tId }, "");
  const slider = h("input", {
    id: tId,
    type: "range",
    min: "0",
    max: String(Math.max(frames.length - 1, 0)),
    step: "1",
    value: "0",
    "aria-valuemin": "0",
    "aria-valuemax": String(Math.max(frames.length - 1, 0)),
  });
  const play = h("button", { type: "button", "aria-pressed": "false", "aria-label": "Play Wigner animation" }, "Play");
  const wignerEl = h("div", { class: "plot tall", "aria-label": "Wigner function heatmap" });
  const nEl = h("div", { class: "plot", "aria-label": "Photon-number traces" });
  const topEl = h("div", { class: "plot", "aria-label": "Truncation monitors" });
  const chips = h("div", { class: "chips" }, ...d.record_ids.map((id) => renderChip(id, byId)));

  root.append(
    h("h1", {}, "Inflate"),
    h(
      "p",
      { class: "lede" },
      "Two-photon dissipation inflates vacuum into an even cat. The Wigner colour scale is fixed across every frame so the animation never rescales. Dashed ⟨n_a⟩ is the effective one-mode model; the dotted line is α².",
    ),
    h("div", { class: "row" }, tLabel, slider, play),
    h("h2", {}, "Wigner function W(x, y)"),
    wignerEl,
    h("h2", {}, "Photon numbers"),
    nEl,
    h("h2", {}, "Truncation monitors"),
    topEl,
    h("h2", {}, "Provenance"),
    chips,
  );

  const setLabel = () => {
    const t = frames[idx]?.t_us ?? 0;
    const text = `t = ${t.toFixed(3)} µs`;
    tLabel.textContent = text;
    slider.setAttribute("aria-valuetext", text);
    slider.setAttribute("aria-valuenow", String(idx));
  };

  const cursor = () =>
    [{ type: "line" as const, x0: frames[idx]?.t_us ?? 0, x1: frames[idx]?.t_us ?? 0, y0: 0, y1: 1, yref: "paper" as const, line: { color: "#111", width: 1, dash: "dot" as const } }];

  const drawWigner = () =>
    plot(
      wignerEl,
      [
        {
          type: "heatmap",
          x: d.wigner.x,
          y: d.wigner.y,
          z: frames[idx]?.w ?? [[]],
          zmin,
          zmax,
          zmid: 0,
          colorscale: WIGNER_SCALE,
          hovertemplate: "x=%{x:.2f}<br>y=%{y:.2f}<br>W=%{z:.3f}<extra></extra>",
        } as Data,
      ],
      {
        title: { text: `W(x, y) at t = ${(frames[idx]?.t_us ?? 0).toFixed(3)} µs` },
        xaxis: { range: [d.wigner.x[0], d.wigner.x[d.wigner.x.length - 1]], constrain: "domain" },
        yaxis: { range: [d.wigner.y[0], d.wigner.y[d.wigner.y.length - 1]], scaleanchor: "x", scaleratio: 1, constrain: "domain" },
        margin: { t: 40 },
      },
    );

  const drawTraces = () => {
    const t = d.t_us;
    void plot(
      nEl,
      [
        { type: "scatter", mode: "lines", name: "⟨n_a⟩", x: t, y: d.na, line: { color: "#0072B2" } },
        { type: "scatter", mode: "lines", name: "⟨n_b⟩", x: t, y: d.nb, line: { color: "#D55E00" } },
        { type: "scatter", mode: "lines", name: "effective ⟨n_a⟩", x: d.effective.t_us, y: d.effective.na, line: { color: "#0072B2", dash: "dash" } },
        { type: "scatter", mode: "lines", name: "α²", x: [t[0] ?? 0, t[t.length - 1] ?? 1], y: [a2, a2], line: { color: "#7f7f7f", dash: "dot", width: 1 } },
      ] as Data[],
      { yaxis: { title: { text: "photons" } }, xaxis: { title: { text: "t (µs)" } }, shapes: cursor(), legend: { orientation: "h" } },
    );
    void plot(
      topEl,
      [
        { type: "scatter", mode: "lines", name: "top-2 a", x: t, y: d.top2_a, line: { color: "#0072B2" } },
        { type: "scatter", mode: "lines", name: "top b", x: t, y: d.top_b, line: { color: "#D55E00" } },
        { type: "scatter", mode: "lines", name: "1e-4", x: [t[0] ?? 0, t[t.length - 1] ?? 1], y: [1e-4, 1e-4], line: { color: "#E69F00", dash: "dot", width: 1 } },
      ] as Data[],
      { yaxis: { type: "log", title: { text: "edge population" } }, xaxis: { title: { text: "t (µs)" } }, shapes: cursor(), legend: { orientation: "h" } },
    );
  };

  const show = () => {
    setLabel();
    void drawWigner();
    drawTraces();
  };

  const setPlaying = (on: boolean) => {
    play.setAttribute("aria-pressed", on ? "true" : "false");
    play.setAttribute("aria-label", on ? "Pause Wigner animation" : "Play Wigner animation");
    play.textContent = on ? "Pause" : "Play";
    if (!on) stopTimer();
  };

  slider.addEventListener("input", () => {
    idx = Number(slider.value);
    setPlaying(false);
    show();
  });

  play.addEventListener("click", () => {
    if (timer !== undefined) {
      setPlaying(false);
      return;
    }
    if (idx >= frames.length - 1) {
      idx = 0;
      slider.value = "0";
    }
    setPlaying(true);
    timer = setInterval(() => {
      if (idx >= frames.length - 1) {
        setPlaying(false);
        return;
      }
      idx += 1;
      slider.value = String(idx);
      show();
    }, 1000 / FPS);
  });

  show();
}
