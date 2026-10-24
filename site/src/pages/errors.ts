import type { Data } from "plotly.js-dist-min";
import { openCard, renderChip } from "../components/provenance";
import { plot } from "../components/plot";
import type { Bundle, RatePoint } from "../data/types";
import { h, uniqueId } from "../lib/dom";

const COLORS = {
  one_mode: "#0072B2",
  two_mode: "#D55E00",
  td: "#009E73",
  ch1: "#CC79A7",
  ch2: "#E69F00",
  total: "#7f7f7f",
  thermal: "#56B4E9",
};

function shade(hex: string, k: number): string {
  const n = parseInt(hex.slice(1), 16);
  const mix = (c: number) => Math.round(c + (255 - c) * k);
  return `#${[mix((n >> 16) & 255), mix((n >> 8) & 255), mix(n & 255)].map((c) => c.toString(16).padStart(2, "0")).join("")}`;
}

function series(name: string, pts: RatePoint[], color: string, visible: boolean): Data {
  const hasUnc = pts.some((p) => p.unc !== null);
  return {
    type: "scatter",
    mode: "markers+lines",
    name,
    x: pts.map((p) => p.alpha2),
    y: pts.map((p) => p.value),
    customdata: pts.map((p) => p.id),
    error_y: hasUnc
      ? { type: "data", array: pts.map((p) => p.unc ?? 0), visible: true, color }
      : undefined,
    marker: { color, size: 7 },
    line: { color, width: 1.4 },
    hovertemplate: "%{y:.4g}<br>%{customdata}<extra>%{fullData.name}</extra>",
    visible,
  } as Data;
}

function line(name: string, x: number[], y: number[], color: string, dash: string, visible: boolean): Data {
  return {
    type: "scatter",
    mode: "lines",
    name,
    x,
    y,
    line: { color, dash, width: name === "analytic total" ? 2 : 1.5 },
    hovertemplate: "%{y:.4g}<extra>%{fullData.name}</extra>",
    visible,
  } as Data;
}

export function render(root: HTMLElement, b: Bundle): void {
  const gx = b.errors.gamma_x;
  const gz = b.errors.gamma_z;
  const thermKeys = Object.keys(gx.thermal).sort((a, c) => Number(a) - Number(c));
  const gxEl = h("div", { class: "plot tall", "aria-label": "Gamma_X versus alpha squared" });
  const slopeEl = h("div", { class: "plot", "aria-label": "Local slope of Gamma_X" });
  const gzEl = h("div", { class: "plot", "aria-label": "Gamma_Z versus alpha squared" });

  const flags: Record<string, boolean> = {
    one_mode: true,
    two_mode: true,
    td: true,
    ch1: true,
    ch2: true,
    total: true,
  };
  for (const k of thermKeys) flags[`th:${k}`] = true;

  const boxes = [
    ["one_mode", "one-mode"],
    ["two_mode", "two-mode"],
    ["td", "time-domain"],
    ["ch1", "analytic ch1"],
    ["ch2", "analytic ch2"],
    ["total", "analytic total"],
    ...thermKeys.map((k) => [`th:${k}`, `thermal n_th = ${k}`] as const),
  ] as const;

  const fieldset = h(
    "fieldset",
    {},
    h("legend", {}, "Series"),
    h(
      "div",
      { class: "toggles" },
      ...boxes.map(([key, label]) => {
        const id = uniqueId(`err-${key}`);
        const box = h("input", { id, type: "checkbox", checked: flags[key] !== false });
        box.addEventListener("change", () => {
          flags[key] = box.checked;
          draw();
        });
        return h("span", {}, box, " ", h("label", { for: id }, label));
      }),
    ),
  );

  const ids = new Set<string>();
  for (const list of [gx.one_mode, gx.two_mode, gx.td, gz.td, gz.eig, ...Object.values(gx.thermal)]) {
    for (const p of list) ids.add(p.id);
  }

  root.append(
    h("h1", {}, "Error budget"),
    h(
      "p",
      { class: "lede" },
      "Bit-flip rate Γ_X and phase-flip rate Γ_Z versus cat size α². Click a marker to open its provenance card. Local slope is −d ln Γ / d(α²); the guides at 4 and 2 are the two exponential channels.",
    ),
    fieldset,
    h("h2", {}, "Γ_X"),
    gxEl,
    h("h2", {}, "Local slope"),
    slopeEl,
    h("h2", {}, "Γ_Z"),
    gzEl,
    h("h2", {}, "Provenance"),
    h("div", { class: "chips" }, ...[...ids].sort().map((id) => renderChip(id, b.byId))),
  );

  const open = (cd: unknown) => {
    if (typeof cd === "string") openCard(cd, b.byId);
  };

  const draw = () => {
    const gxTraces: Data[] = [
      series("one-mode", gx.one_mode, COLORS.one_mode, flags.one_mode),
      series("two-mode", gx.two_mode, COLORS.two_mode, flags.two_mode),
      series("time-domain", gx.td, COLORS.td, flags.td),
      line("analytic ch1", gx.analytic.alpha2, gx.analytic.ch1, COLORS.ch1, "solid", flags.ch1),
      line("analytic ch2", gx.analytic.alpha2, gx.analytic.ch2, COLORS.ch2, "solid", flags.ch2),
      line("analytic total", gx.analytic.alpha2, gx.analytic.total, COLORS.total, "dash", flags.total),
      ...thermKeys.map((k, i) => series(`thermal n_th=${k}`, gx.thermal[k], shade(COLORS.thermal, i * 0.18), flags[`th:${k}`])),
    ];
    void plot(gxEl, gxTraces, { yaxis: { type: "log", title: { text: "Γ_X (1/µs)" } }, xaxis: { title: { text: "α²" } }, legend: { orientation: "h" } }, { onClick: open });

    const sl = gx.local_slope;
    void plot(
      slopeEl,
      [
        { type: "scatter", mode: "lines+markers", name: "one-mode", x: sl.alpha2, y: sl.one_mode, line: { color: COLORS.one_mode }, marker: { color: COLORS.one_mode }, visible: flags.one_mode } as Data,
        { type: "scatter", mode: "lines+markers", name: "two-mode", x: sl.alpha2, y: sl.two_mode, line: { color: COLORS.two_mode }, marker: { color: COLORS.two_mode }, visible: flags.two_mode } as Data,
        { type: "scatter", mode: "lines", name: "4", x: [sl.alpha2[0] ?? 0.5, sl.alpha2[sl.alpha2.length - 1] ?? 9], y: [4, 4], line: { color: "#7f7f7f", dash: "dot" } } as Data,
        { type: "scatter", mode: "lines", name: "2", x: [sl.alpha2[0] ?? 0.5, sl.alpha2[sl.alpha2.length - 1] ?? 9], y: [2, 2], line: { color: "#7f7f7f", dash: "dash" } } as Data,
      ],
      { yaxis: { title: { text: "−d ln Γ / d(α²)" } }, xaxis: { title: { text: "α²" } }, legend: { orientation: "h" } },
    );

    void plot(
      gzEl,
      [
        series("Γ_Z time-domain", gz.td, COLORS.td, true),
        series("Γ_Z eigen", gz.eig, COLORS.two_mode, true),
        line("analytic coth", gz.pred.alpha2, gz.pred.value, COLORS.total, "dash", true),
      ],
      { yaxis: { type: "log", title: { text: "Γ_Z (1/µs)" } }, xaxis: { title: { text: "α²" } }, legend: { orientation: "h" } },
      { onClick: open },
    );
  };

  draw();
}
