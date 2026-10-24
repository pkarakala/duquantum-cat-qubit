// The ONLY module that imports Plotly (tests vi.mock it). Applies the light/dark theme from the CSS
// custom properties and re-plots every live chart when prefers-color-scheme changes.
import Plotly from "plotly.js-dist-min";
import type { Config, Data, Layout, PlotMouseEvent } from "plotly.js-dist-min";

export interface PlotOptions {
  onClick?: (customdata: unknown, ev: PlotMouseEvent) => void;
  config?: Partial<Config>;
}

interface Entry {
  traces: Data[];
  layout: Partial<Layout>;
  opts: PlotOptions;
}

const registry = new Map<HTMLElement, Entry>();
let themeListener = false;

function cssVar(name: string, fallback: string): string {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

type AxisLike = Record<string, unknown>;

function themed(layout: Partial<Layout>): Partial<Layout> {
  const fg = cssVar("--fg", "#1a1a1a");
  const grid = cssVar("--grid", "#dddddd");
  const out: Record<string, unknown> = {
    ...layout,
    paper_bgcolor: cssVar("--bg", "#ffffff"),
    plot_bgcolor: cssVar("--plot-bg", cssVar("--bg", "#ffffff")),
    font: { family: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", size: 13, color: fg, ...(layout.font ?? {}) },
    hoverlabel: { bgcolor: cssVar("--bg", "#ffffff"), font: { color: fg }, ...(layout.hoverlabel ?? {}) },
    legend: { bgcolor: "rgba(0,0,0,0)", ...(layout.legend ?? {}) },
    margin: { l: 64, r: 16, t: 36, b: 48, ...(layout.margin ?? {}) },
  };
  for (const [k, v] of Object.entries(layout)) {
    if (/^[xy]axis\d*$/.test(k)) {
      const ax = v as AxisLike;
      out[k] = { gridcolor: grid, zerolinecolor: grid, linecolor: grid, ...ax };
    }
  }
  if (!("xaxis" in layout)) out.xaxis = { gridcolor: grid, zerolinecolor: grid };
  if (!("yaxis" in layout)) out.yaxis = { gridcolor: grid, zerolinecolor: grid };
  return out as Partial<Layout>;
}

function ensureThemeListener() {
  if (themeListener || typeof window === "undefined" || typeof window.matchMedia !== "function") return;
  themeListener = true;
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    for (const [el, e] of registry) {
      if (!el.isConnected) {
        registry.delete(el);
        continue;
      }
      void Plotly.react(el, e.traces, themed(e.layout), config(e.opts));
    }
  });
}

function config(opts: PlotOptions): Partial<Config> {
  return { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["select2d", "lasso2d"], ...(opts.config ?? {}) };
}

export async function plot(el: HTMLElement, traces: Data[], layout: Partial<Layout>, opts: PlotOptions = {}): Promise<void> {
  ensureThemeListener();
  for (const k of registry.keys()) if (!k.isConnected) registry.delete(k);
  const first = !registry.has(el);
  registry.set(el, { traces, layout, opts });
  await Plotly.react(el, traces, themed(layout), config(opts));
  if (first && opts.onClick) {
    const gd = el as unknown as { on: (ev: string, cb: (e: PlotMouseEvent) => void) => void };
    gd.on("plotly_click", (ev: PlotMouseEvent) => {
      const cd = ev.points?.[0]?.customdata;
      const handler = registry.get(el)?.opts.onClick;
      if (cd !== undefined && cd !== null && handler) handler(cd, ev);
    });
  }
}
