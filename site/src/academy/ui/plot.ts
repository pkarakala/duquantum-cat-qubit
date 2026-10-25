/** The only Plotly import in the academy. SVG polylines take over if the library is missing. */

export interface PlotSeries {
  x: ArrayLike<number>;
  y: ArrayLike<number>;
  name: string;
  dash?: 'solid' | 'dash';
  color?: string;
}

export interface PlotOptions {
  xlabel?: string;
  ylabel?: string;
  ylog?: boolean;
  guides?: { x: number; name: string }[];
}

export const OKABE = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9'];

function cssVar(el: HTMLElement, name: string, fallback: string): string {
  const value = getComputedStyle(el).getPropertyValue(name).trim();
  return value || fallback;
}

function svgFallback(el: HTMLElement, series: PlotSeries[], opts: PlotOptions): void {
  const width = 520;
  const height = 260;
  const pad = 36;
  const xs = series.flatMap((s) => Array.from(s.x, Number)).filter(Number.isFinite);
  const ys = series.flatMap((s) => Array.from(s.y, Number).filter((v) => (opts.ylog ? v > 0 : Number.isFinite(v))));
  const x0 = Math.min(...xs);
  const x1 = Math.max(...xs);
  const y0 = opts.ylog ? Math.log10(Math.min(...ys)) : Math.min(...ys);
  const y1 = opts.ylog ? Math.log10(Math.max(...ys)) : Math.max(...ys);
  const sx = (x: number) => pad + ((x - x0) / (x1 - x0 || 1)) * (width - pad * 2);
  const sy = (y: number) => {
    const v = opts.ylog ? Math.log10(y) : y;
    return height - pad - ((v - y0) / (y1 - y0 || 1)) * (height - pad * 2);
  };
  const lines = series
    .map((s, i) => {
      const pts: string[] = [];
      for (let k = 0; k < s.x.length; k++) {
        const y = Number(s.y[k]);
        if (opts.ylog && !(y > 0)) continue;
        pts.push(`${sx(Number(s.x[k])).toFixed(1)},${sy(y).toFixed(1)}`);
      }
      const color = s.color ?? OKABE[i % OKABE.length];
      const dash = s.dash === 'dash' ? 'stroke-dasharray="5 4"' : '';
      return `<polyline fill="none" stroke="${color}" stroke-width="2" ${dash} points="${pts.join(' ')}" />`;
    })
    .join('');
  const guides = (opts.guides ?? [])
    .map((g) => `<line x1="${sx(g.x)}" x2="${sx(g.x)}" y1="${pad}" y2="${height - pad}" stroke="#D55E00" stroke-dasharray="2 3" />`)
    .join('');
  const legend = series
    .map((s, i) => `<span style="color:${s.color ?? OKABE[i % OKABE.length]}">${s.dash === 'dash' ? 'dashed ' : ''}${s.name}</span>`)
    .join(' · ');
  el.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${opts.ylabel ?? 'plot'}">${lines}${guides}</svg><p class="legend">${legend}. ${opts.xlabel ?? ''} / ${opts.ylabel ?? ''}</p>`;
}

export async function plot(el: HTMLElement, series: PlotSeries[], opts: PlotOptions = {}): Promise<void> {
  const fg = cssVar(el, '--fg', '#1c1917');
  const muted = cssVar(el, '--muted', '#57534e');
  try {
    const Plotly = (await import('plotly.js-dist-min')).default;
    const data = series.map((s, i) => ({
      type: 'scatter',
      mode: 'lines',
      name: s.name,
      x: Array.from(s.x, Number),
      y: Array.from(s.y, Number),
      line: { color: s.color ?? OKABE[i % OKABE.length], dash: s.dash === 'dash' ? 'dash' : 'solid', width: 2 },
    }));
    const shapes = (opts.guides ?? []).map((g) => ({
      type: 'line',
      x0: g.x,
      x1: g.x,
      y0: 0,
      y1: 1,
      yref: 'paper',
      line: { color: '#D55E00', dash: 'dot', width: 1 },
    }));
    await Plotly.react(
      el,
      data,
      {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: fg, family: 'ui-sans-serif, system-ui, sans-serif' },
        margin: { l: 48, r: 16, t: 12, b: 40 },
        xaxis: { title: { text: opts.xlabel ?? '' }, gridcolor: muted, zeroline: false },
        yaxis: { title: { text: opts.ylabel ?? '' }, type: opts.ylog ? 'log' : 'linear', gridcolor: muted, zeroline: false },
        legend: { orientation: 'h' },
        shapes,
      },
      { displayModeBar: false, responsive: true },
    );
  } catch {
    svgFallback(el, series, opts);
  }
}
