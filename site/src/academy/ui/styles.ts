/** Scoped under .academy. System fonts only; color is never the only signal. */

export const ACADEMY_CSS = `
.academy, .academy * { box-sizing: border-box; }
.academy {
  --bg: #f4f6fb;
  --surface: #ffffff;
  --surface-2: #eef1f8;
  --fg: #0f172a;
  --muted: #475569;
  --line: #d8deea;
  --grid: #d8deea;
  --brand: #312e81;
  --brand-2: #4338ca;
  --accent: #0f766e;
  --accent-strong: #115e59;
  --accent-soft: #e6f6f3;
  --on-accent: #ffffff;
  --ok: #00785a;
  --ok-soft: #e0f5ee;
  --warn: #b34700;
  --warn-soft: #fdeee3;
  --card: var(--surface);
  --shadow-1: 0 1px 2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.08);
  --shadow-2: 0 4px 16px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(15, 23, 42, 0.06);
  --r-md: 10px;
  --r-lg: 16px;
  color: var(--fg);
  background: var(--bg);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 16px 56px;
  overflow-x: clip;
  min-width: 0;
}
@media (prefers-color-scheme: dark) {
  .academy {
    --bg: #0b1020;
    --surface: #131a2d;
    --surface-2: #1a2339;
    --fg: #e7ecf6;
    --muted: #a6b2c8;
    --line: #2a3654;
    --grid: #2a3654;
    --brand: #c7d2fe;
    --brand-2: #a5b4fc;
    --accent: #2dd4bf;
    --accent-strong: #5eead4;
    --accent-soft: #123a3a;
    --on-accent: #042f2e;
    --ok: #3fd0a0;
    --ok-soft: #10302a;
    --warn: #ff9b5c;
    --warn-soft: #3a2316;
    --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.4);
    --shadow-2: 0 6px 20px rgba(0, 0, 0, 0.45);
  }
}
.academy :focus-visible { outline: 3px solid var(--brand-2); outline-offset: 2px; }

/* lesson header */
.academy > header {
  display: block; padding: 0 0 20px; margin: 0 0 20px; border: 0; border-bottom: 1px solid var(--line);
  background: transparent; max-width: 100%; position: static; backdrop-filter: none; -webkit-backdrop-filter: none;
}
.academy h1 { font-size: clamp(1.5rem, 3.6vw, 2.1rem); line-height: 1.15; margin: 4px 0 4px; letter-spacing: -0.02em; }
.academy h2 { font-size: 1.15rem; line-height: 1.3; margin: 0 0 8px; letter-spacing: -0.01em; }
.academy p { overflow-wrap: anywhere; }
.academy .aha p, .academy .concept p { white-space: pre-wrap; }
.academy .concept p, .academy .aha p, .academy .feedback { max-width: 68ch; }
.academy .eyebrow {
  display: inline-flex; align-items: center; gap: 6px; color: var(--accent); margin: 0;
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
}

/* progress map: tidy row of level nodes */
.academy .progress-map {
  display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 8px; margin: 18px 0 0; max-width: 100%;
  counter-reset: none;
}
.academy .progress-map button {
  position: relative; display: flex; align-items: center; justify-content: center; gap: 4px;
  min-height: 44px; padding: 8px 6px; border-radius: 12px; border: 1px solid var(--line);
  background: var(--surface); color: var(--muted); font-weight: 700; font-size: 0.92rem;
  box-shadow: var(--shadow-1); white-space: nowrap;
}
.academy .progress-map button:hover { border-color: var(--accent); color: var(--fg); }
.academy .progress-map button[aria-label$=", passed"] {
  background: var(--ok-soft); border-color: var(--ok); color: var(--ok);
}
.academy .progress-map button[aria-current="step"] {
  background: var(--brand-2); border-color: var(--brand-2); color: #ffffff;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-2) 25%, transparent), var(--shadow-1);
}
@media (prefers-color-scheme: dark) {
  .academy .progress-map button[aria-current="step"] { color: #0b1020; }
}

/* buttons */
.academy button, .academy select {
  font: inherit; font-weight: 600; color: var(--fg); background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--r-md); padding: 8px 14px; min-height: 40px; max-width: 100%;
  cursor: pointer; transition: background-color 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
}
.academy button:hover:not(:disabled) { border-color: var(--accent); }
.academy button:disabled { cursor: not-allowed; }
.academy .run, .academy .check {
  width: 100%; min-height: 50px; border-radius: 12px; font-weight: 750; font-size: 1.02rem; letter-spacing: 0.01em;
}
.academy .is-primary {
  background: var(--accent); color: var(--on-accent); border-color: transparent; box-shadow: var(--shadow-2);
}
.academy .is-primary:hover:not(:disabled) { background: var(--accent-strong); border-color: transparent; }
.academy .run:disabled {
  opacity: 1; background: var(--surface-2); color: var(--muted); border: 1px dashed var(--line); box-shadow: none;
}
.academy .check:disabled { opacity: 0.55; }

/* two-column lesson layout */
.academy .layout {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); gap: 24px; align-items: start;
}
.academy .layout > * { min-width: 0; }

/* cards */
.academy .card, .academy .concept, .academy .aha, .academy .code, .academy .schro {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
  padding: 18px 20px; margin: 0 0 16px; min-width: 0; max-width: 100%; box-shadow: var(--shadow-1);
}
.academy .concept { border-top: 4px solid var(--brand-2); }
.academy .aha { background: linear-gradient(180deg, var(--accent-soft), var(--surface) 70%); border-color: var(--accent); }
.academy .code summary { cursor: pointer; font-weight: 650; }

/* source badge as pill + gloss */
.academy .source-host { margin: 0 0 16px; max-width: 100%; }
.academy .source-badge {
  display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px;
  margin: 0; padding: 10px 14px; border-radius: 14px; border: 1px solid var(--line);
  background: var(--surface); max-width: 100%; box-shadow: var(--shadow-1);
}
.academy .badge-value {
  display: inline-flex; align-items: center; gap: 6px; font-weight: 750; font-size: 0.82rem; letter-spacing: 0.02em;
  padding: 3px 12px; border-radius: 999px; border: 1.5px solid var(--muted); color: var(--fg); background: var(--surface-2);
}
.academy .badge-value::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex: none; }
.academy .badge-gloss { flex: 1 1 14rem; font-weight: 450; font-size: 0.92rem; color: var(--muted); }
.academy .source-badge[data-kind="mock"] { border-color: var(--warn); border-style: dashed; }
.academy .source-badge[data-kind="mock"] .badge-value { border-style: dashed; border-color: var(--warn); color: var(--warn); background: var(--warn-soft); }
.academy .source-badge[data-kind="stored"] { border-style: dashed; }
.academy .source-badge[data-kind="stored"] .badge-value { border-style: dashed; }
.academy .source-badge[data-kind="real"] { border-color: var(--ok); }
.academy .source-badge[data-kind="real"] .badge-value { border-color: var(--ok); color: var(--ok); background: var(--ok-soft); }
.academy .banner {
  color: var(--warn); margin: 8px 0 0; font-weight: 600; font-size: 0.92rem;
  padding: 8px 12px; border-radius: 10px; background: var(--warn-soft); border-left: 4px solid var(--warn);
}
.academy .banner[hidden] { display: none; }

/* predict gate */
.academy .predict-gate[data-locked="true"] { border-color: var(--brand-2); box-shadow: inset 4px 0 0 var(--brand-2), var(--shadow-1); }
.academy .predict-gate[data-locked="false"] { box-shadow: inset 4px 0 0 var(--ok), var(--shadow-1); }
.academy .step {
  display: inline-block; margin: 0 0 4px; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--brand-2); background: var(--surface-2); padding: 3px 10px; border-radius: 999px;
}
.academy .gate-status { margin: 4px 0 12px; font-weight: 600; color: var(--muted); font-size: 0.95rem; }
.academy fieldset { border: 0; padding: 0; margin: 0 0 8px; min-width: 0; }
.academy .choices { display: grid; gap: 8px; }
.academy .choices label {
  display: flex; gap: 12px; align-items: flex-start; min-height: 46px; padding: 11px 14px;
  border: 1px solid var(--line); border-radius: 12px; background: var(--surface-2); cursor: pointer;
  transition: border-color 120ms ease, background-color 120ms ease;
}
.academy .choices label:hover { border-color: var(--accent); }
.academy .choices input { accent-color: var(--accent); margin-top: 4px; flex: none; }
.academy .choices label:has(input:checked) {
  border-color: var(--accent); box-shadow: inset 4px 0 0 var(--accent); background: var(--accent-soft); font-weight: 600;
}
.academy .question { font-size: 1.1rem; line-height: 1.35; font-weight: 750; margin: 0 0 10px; max-width: 48ch; padding: 0; }
.academy .feedback:empty { display: none; }
.academy .feedback {
  margin: 10px 0 0; padding: 10px 12px; border-radius: 10px; background: var(--surface-2); border-left: 4px solid var(--brand-2);
}

/* controls + sliders */
.academy .control {
  margin: 0 0 12px; min-width: 0; padding: 14px 16px; background: var(--surface);
  border: 1px solid var(--line); border-radius: 14px;
}
.academy .control label, .academy .control p { font-weight: 650; margin: 0 0 6px; }
.academy .control output, .academy .control .value { font-variant-numeric: tabular-nums; color: var(--accent); font-weight: 700; }
.academy input[type="range"] {
  width: 100%; max-width: 100%; min-width: 0; accent-color: var(--accent); height: 28px; margin: 4px 0 0; cursor: pointer;
  background: transparent; border: 0; padding: 0;
}
.academy .control select, .academy input[type="text"], .academy input:not([type]) { max-width: 100%; }
.academy input[type="text"], .academy input:not([type]) {
  font: inherit; color: var(--fg); background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; min-height: 40px;
}
.academy .control [role="group"] { display: flex; flex-wrap: wrap; gap: 6px; }
.academy .control [role="group"] button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); border-color: transparent; }
.academy .actions { margin: 4px 0 16px; }
.academy .blocks-note { font-size: 0.92rem; color: var(--muted); padding: 10px 12px; border-radius: 10px; background: var(--surface-2); }

/* visualizations */
.academy .views { display: grid; gap: 16px; min-width: 0; max-width: 100%; }
.academy .views > div:not(:empty) {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); padding: 14px; min-width: 0; box-shadow: var(--shadow-1);
}
.academy .views > .extra:not(:empty) { padding: 14px; }
.academy .views svg, .academy canvas, .academy .plot { max-width: 100%; height: auto; }
.academy .views svg text { fill: var(--muted); }
.academy .plot, .academy .js-plotly-plot, .academy .plotly-graph-div, .academy .svg-container {
  max-width: 100% !important; min-width: 0 !important;
}
.academy .plot { min-height: 0; }
.academy .plot.js-plotly-plot, .academy .js-plotly-plot .plot-container, .academy .js-plotly-plot .svg-container { height: 320px !important; max-height: 320px; }
.academy canvas { width: 100%; background: #0b1020; border-radius: 12px; display: block; }
.academy .axis, .academy .legend { color: var(--muted); font-size: 0.86rem; margin: 6px 0 0; }
.academy .hist { margin: 0; }
.academy .hist figcaption { color: var(--muted); font-size: 0.86rem; margin-top: 6px; }
.academy .bars { display: flex; align-items: flex-end; gap: 3px; height: 160px; max-width: 100%; }
.academy .bar-col { flex: 1; min-width: 0; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; }
.academy .bar { width: 72%; background: linear-gradient(180deg, var(--accent), var(--brand-2)); border-radius: 5px 5px 0 0; min-height: 2px; }
.academy .bar-col span { font-size: 0.7rem; color: var(--muted); max-width: 100%; overflow-wrap: anywhere; text-align: center; font-variant-numeric: tabular-nums; }
.academy .parity-track { height: 14px; background: var(--surface-2); border: 1px solid var(--line); border-radius: 999px; overflow: hidden; }
.academy .parity-fill { height: 100%; width: 50%; background: linear-gradient(90deg, var(--ok), var(--accent)); }

/* check banner */
.academy [data-part="check-banner"] { margin: 10px 0 0; }
.academy .check-banner[data-pass="true"] {
  color: var(--ok); font-weight: 750; padding: 10px 12px; border-radius: 10px; background: var(--ok-soft); border-left: 4px solid var(--ok);
}
.academy .check-banner[data-pass="false"] {
  color: var(--warn); font-weight: 750; padding: 10px 12px; border-radius: 10px; background: var(--warn-soft); border-left: 4px solid var(--warn);
}

/* pulse editor (L8) */
.academy .pulse-editor {
  display: grid; grid-template-columns: repeat(20, minmax(0, 1fr)); gap: 2px; align-items: end;
  height: 150px; width: 100%; max-width: 100%; min-width: 0;
  padding: 8px; background: var(--surface-2); border-radius: 12px; border: 1px solid var(--line); margin: 0 0 12px;
}
.academy .pulse-editor input {
  writing-mode: vertical-lr; direction: rtl; height: 120px; width: 100%; min-width: 0; max-width: 100%;
  margin: 0; padding: 0; accent-color: var(--accent);
}
.academy .well { width: 100%; height: auto; max-width: 100%; }
.academy .chips { display: flex; flex-wrap: wrap; gap: 6px; max-width: 100%; }
.academy .chips span {
  font-family: ui-monospace, "Cascadia Code", Menlo, Consolas, monospace; font-size: 0.74rem;
  background: var(--surface-2); color: var(--fg); border: 1px solid var(--line); border-radius: 999px;
  padding: 2px 9px; overflow-wrap: anywhere; max-width: 100%;
}
.academy pre, .academy code {
  max-width: 100%; overflow-x: auto; white-space: pre-wrap; overflow-wrap: anywhere;
  font-family: ui-monospace, "Cascadia Code", Menlo, Consolas, monospace; font-size: 0.86em;
}
.academy pre { background: var(--surface-2); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }

/* forms + tutor */
.academy form.card { display: grid; gap: 10px; }
.academy form.card input, .academy form.card button { width: 100%; max-width: 100%; }
.academy [data-slot="tutor"], .academy [data-slot="credential"] { min-height: 0; max-width: 100%; }
.academy [data-slot="credential"]:not(:empty) {
  padding: 14px 18px; margin: 0 0 16px; border-radius: var(--r-lg); border: 1px dashed var(--line); background: var(--surface);
}
.academy .schro { border-top: 4px solid var(--accent); }
.academy .schro::before {
  content: "Tutor · Schrö"; display: block; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--accent); margin: 0 0 8px;
}
.academy .schro ol { padding-left: 1.2rem; margin: 8px 0; display: grid; gap: 6px; max-height: 320px; overflow-y: auto; }
.academy .schro form { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; margin: 8px 0; }
.academy .schro form label { flex: 1 1 14rem; display: grid; gap: 4px; font-weight: 600; font-size: 0.92rem; }
.academy .schro button[type="submit"] { background: var(--accent); color: var(--on-accent); border-color: transparent; }
.academy .recap:empty { display: none; }
.academy .recap { color: var(--muted); font-size: 0.92rem; }
.academy.is-busy .views { opacity: 0.6; transition: opacity 160ms ease; }
.academy a { color: var(--accent); text-underline-offset: 0.18em; }

@media (max-width: 1024px) {
  .academy .layout { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; }
}
@media (max-width: 768px) {
  .academy { padding: 18px 16px 36px; font-size: 16px; }
  .academy .layout { grid-template-columns: minmax(0, 1fr); }
  .academy .progress-map { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .academy .card, .academy .concept, .academy .aha, .academy .code, .academy .schro { padding: 14px 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .academy.is-busy .views { opacity: 1; }
  .academy *, .academy *::before, .academy *::after { transition: none !important; animation: none !important; }
}
`;
