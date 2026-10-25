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
  font: 16px/1.45 ui-sans-serif, system-ui, sans-serif;
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px;
  overflow-x: hidden;
}
.academy :focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.academy h1 { font-size: 1.6rem; line-height: 1.2; margin: 0 0 4px; }
.academy .aha p, .academy .concept p { white-space: pre-wrap; }
.academy .eyebrow { color: var(--muted); margin: 0; font-size: 0.85rem; }
.academy .progress-map { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }
.academy .progress-map button, .academy button, .academy select {
  font: inherit; color: var(--fg); background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px;
}
.academy .progress-map button[aria-current="step"] { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.academy .layout { display: grid; grid-template-columns: minmax(0, 320px) minmax(0, 1fr); gap: 16px; }
.academy .card, .academy .concept, .academy .aha, .academy .code {
  background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 12px; margin: 0 0 12px;
}
.academy .source-badge { display: inline-block; font-weight: 700; letter-spacing: 0.02em; }
.academy .banner { color: var(--warn); margin: 6px 0 0; }
.academy .choices { display: grid; gap: 6px; }
.academy .choices label { display: flex; gap: 8px; align-items: flex-start; padding: 6px; border-radius: 8px; }
.academy .question { font-weight: 650; margin: 0 0 6px; }
.academy .control { margin: 0 0 10px; }
.academy .control input[type="range"] { width: 100%; }
.academy .run { background: var(--accent); color: white; border-color: transparent; font-weight: 700; }
.academy .run:disabled { opacity: 0.45; }
.academy .views { display: grid; gap: 12px; min-width: 0; }
.academy .views svg, .academy canvas, .academy .plot { max-width: 100%; height: auto; }
.academy canvas { width: 100%; background: #111; border-radius: 8px; }
.academy .axis { color: var(--muted); font-size: 0.85rem; margin: 4px 0 0; }
.academy .bars { display: flex; align-items: flex-end; gap: 4px; height: 140px; }
.academy .bar-col { flex: 1; min-width: 0; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; }
.academy .bar { width: 70%; background: var(--accent); border-radius: 4px 4px 0 0; min-height: 2px; }
.academy .bar-col span { font-size: 0.7rem; color: var(--muted); }
.academy .parity-track { height: 14px; background: var(--line); border-radius: 999px; overflow: hidden; }
.academy .parity-fill { height: 100%; width: 50%; background: var(--ok); }
.academy .check-banner[data-pass="true"] { color: var(--ok); font-weight: 700; }
.academy .check-banner[data-pass="false"] { color: var(--warn); font-weight: 700; }
.academy .pulse-editor { display: grid; grid-template-columns: repeat(20, minmax(0, 1fr)); gap: 2px; align-items: end; height: 150px; }
.academy .pulse-editor input { writing-mode: vertical-lr; direction: rtl; height: 130px; width: 100%; padding: 0; }
.academy .well { width: 100%; height: auto; }
.academy .chips { display: flex; flex-wrap: wrap; gap: 4px; }
.academy .chips span { font-family: ui-monospace, monospace; font-size: 0.72rem; background: #efe9df; border-radius: 6px; padding: 2px 6px; }
.academy.is-busy .views { opacity: 0.55; }
.academy [data-slot="tutor"], .academy [data-slot="credential"] { min-height: 0; }
.academy a { color: var(--accent); }
@media (max-width: 720px) {
  .academy { padding: 12px; }
  .academy .layout { grid-template-columns: minmax(0, 1fr); }
}
@media (prefers-reduced-motion: reduce) {
  .academy.is-busy .views { opacity: 1; }
}
`;
