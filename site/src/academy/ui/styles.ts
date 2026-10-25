/** Scoped under .academy. System fonts only; color is never the only signal. */

export const ACADEMY_CSS = `
.academy, .academy * { box-sizing: border-box; }
.academy {
  --bg: #f6f3ee;
  --fg: #1c1917;
  --muted: #57534e;
  --accent: #0072b2;
  --ok: #009e73;
  --warn: #d55e00;
  --card: #fffdf8;
  --line: #e7e0d6;
  color: var(--fg);
  background: var(--bg);
  font: 17px/1.55 ui-sans-serif, system-ui, sans-serif;
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 16px 40px;
  overflow-x: clip;
  min-width: 0;
}
.academy :focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.academy header { display: block; padding: 0; border: 0; background: transparent; max-width: 100%; }
.academy h1 { font-size: clamp(1.45rem, 4.2vw, 1.9rem); line-height: 1.2; margin: 0 0 8px; letter-spacing: -0.02em; }
.academy h2 { font-size: 1.15rem; line-height: 1.3; margin: 0 0 8px; }
.academy p { overflow-wrap: anywhere; }
.academy .aha p, .academy .concept p { white-space: pre-wrap; }
.academy .concept p, .academy .aha p, .academy .feedback { max-width: 65ch; }
.academy .eyebrow { color: var(--muted); margin: 0; font-size: 0.9rem; }
.academy .progress-map { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0 0; max-width: 100%; }
.academy .progress-map button, .academy button, .academy select {
  font: inherit; color: var(--fg); background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px;
}
.academy .progress-map button[aria-current="step"] { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.academy .layout { display: grid; grid-template-columns: minmax(0, 22rem) minmax(0, 1fr); gap: 20px; align-items: start; }
.academy .layout > * { min-width: 0; }
.academy .card, .academy .concept, .academy .aha, .academy .code {
  background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px; margin: 0 0 12px; min-width: 0; max-width: 100%;
}
.academy .source-host { margin: 0 0 12px; max-width: 100%; }
.academy .source-badge {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px;
  margin: 0; padding: 10px 12px; border-radius: 12px; border: 2px solid var(--line);
  background: var(--card); max-width: 100%;
}
.academy .source-badge[data-kind="mock"] { border-style: dashed; border-color: var(--warn); }
.academy .source-badge[data-kind="stored"] { border-style: dashed; border-color: var(--muted); }
.academy .source-badge[data-kind="real"] { border-style: solid; border-color: var(--ok); }
.academy .badge-value { font-weight: 750; }
.academy .badge-gloss { flex-basis: 100%; font-weight: 450; color: var(--fg); }
.academy .banner { color: var(--warn); margin: 8px 0 0; font-weight: 650; }
.academy .predict-gate[data-locked="true"] { border-color: var(--accent); box-shadow: inset 4px 0 0 var(--accent); }
.academy .step { margin: 0; font-size: 0.78rem; font-weight: 750; letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent); }
.academy .gate-status { margin: 2px 0 10px; font-weight: 650; }
.academy .choices { display: grid; gap: 8px; }
.academy .choices label {
  display: flex; gap: 10px; align-items: flex-start; min-height: 44px; padding: 10px 12px;
  border: 1px solid var(--line); border-radius: 10px; background: var(--bg); cursor: pointer;
}
.academy .choices label:has(input:checked) { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); background: var(--card); }
.academy .question { font-size: 1.12rem; line-height: 1.35; font-weight: 750; margin: 0 0 8px; max-width: 40ch; }
.academy .feedback:empty { display: none; }
.academy .feedback { margin: 8px 0 0; }
.academy .control { margin: 0 0 12px; min-width: 0; }
.academy .control label, .academy .control p { font-weight: 650; }
.academy .control input[type="range"] { width: 100%; max-width: 100%; min-width: 0; }
.academy .control select, .academy input[type="text"] { max-width: 100%; }
.academy .control [role="group"] { display: flex; flex-wrap: wrap; gap: 6px; }
.academy .actions { margin: 4px 0 0; }
.academy .run, .academy .check { width: 100%; min-height: 48px; border-radius: 12px; font-weight: 750; }
.academy .is-primary { background: var(--accent); color: #fff; border-color: transparent; }
.academy .run:disabled { opacity: 1; background: var(--line); color: var(--muted); border-color: transparent; cursor: not-allowed; }
.academy .check:disabled { opacity: 0.55; }
.academy .views { display: grid; gap: 12px; min-width: 0; max-width: 100%; }
.academy .views svg, .academy canvas, .academy .plot { max-width: 100%; height: auto; }
.academy .plot, .academy .js-plotly-plot, .academy .plotly-graph-div, .academy .svg-container {
  max-width: 100% !important; min-width: 0 !important;
}
.academy canvas { width: 100%; background: #111; border-radius: 8px; display: block; }
.academy .axis, .academy .legend { color: var(--muted); font-size: 0.9rem; margin: 4px 0 0; }
.academy .bars { display: flex; align-items: flex-end; gap: 3px; height: 140px; max-width: 100%; }
.academy .bar-col { flex: 1; min-width: 0; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; }
.academy .bar { width: 70%; background: var(--accent); border-radius: 4px 4px 0 0; min-height: 2px; }
.academy .bar-col span { font-size: 0.7rem; color: var(--muted); max-width: 100%; overflow-wrap: anywhere; text-align: center; }
.academy .parity-track { height: 14px; background: var(--line); border-radius: 999px; overflow: hidden; }
.academy .parity-fill { height: 100%; width: 50%; background: var(--ok); }
.academy .check-banner[data-pass="true"] { color: var(--ok); font-weight: 750; }
.academy .check-banner[data-pass="false"] { color: var(--warn); font-weight: 750; }
.academy .pulse-editor {
  display: grid; grid-template-columns: repeat(20, minmax(0, 1fr)); gap: 2px; align-items: end;
  height: 150px; width: 100%; max-width: 100%; min-width: 0;
}
.academy .pulse-editor input {
  writing-mode: vertical-lr; direction: rtl; height: 120px; width: 100%; min-width: 0; max-width: 100%;
  margin: 0; padding: 0;
}
.academy .well { width: 100%; height: auto; max-width: 100%; }
.academy .chips { display: flex; flex-wrap: wrap; gap: 4px; max-width: 100%; }
.academy .chips span {
  font-family: ui-monospace, monospace; font-size: 0.72rem; background: #efe9df; border-radius: 6px;
  padding: 2px 6px; overflow-wrap: anywhere; max-width: 100%;
}
.academy pre, .academy code {
  max-width: 100%; overflow-x: auto; white-space: pre-wrap; overflow-wrap: anywhere;
}
.academy form.card { display: grid; gap: 8px; }
.academy form.card input, .academy form.card button { width: 100%; max-width: 100%; }
.academy.is-busy .views { opacity: 0.55; }
.academy [data-slot="tutor"], .academy [data-slot="credential"] { min-height: 0; max-width: 100%; }
.academy a { color: var(--accent); }
@media (max-width: 720px) {
  .academy { padding: 12px 12px 32px; font-size: 16.5px; }
  .academy .layout { grid-template-columns: minmax(0, 1fr); }
}
@media (prefers-reduced-motion: reduce) {
  .academy.is-busy .views { opacity: 1; }
}
`;
