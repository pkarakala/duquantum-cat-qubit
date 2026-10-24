# Brief `l6-lab`: Cat Qubit Lab: static interactive site with provenance cards

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l6-lab`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/11-l6-lab.md`, then execute this brief exactly. Keep `docs/plan/status/l6-lab.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l6-lab` | `std/l6-lab` from `standard-track` | **Part A:** nothing; CONTRACT §13 only, mock data. **Part B:** whatever records/arrays are merged on `standard-track` (l0-tools `t1_*`, l2a, l2b, l3, l4a, l4b, l4c) | fast (Sonnet-class) | Part A 3 h + Part B 1 h | Part A: Phase 0–1, start 6:00 PM, done **9:45 PM Sat Oct 24** (G1). Part B: Phase 2–3, after records exist (aim before G2, 1:30 AM). Integrator does the final data refresh before **8:00 AM Sun** (physics freeze) |

## 1. Goal and why
Build the **Cat Qubit Lab**: a static, offline-capable site where a judge can watch a cat inflate, explore the error budget and design a readout, and **click any number to see where it came from**. Deliverable D4: `site/dist-single/index.html` opens from `file://` with no network (this is the live-demo copy for Wilkinson 132), and a GitHub Pages build exists for when the repo goes public.
- **No physics in the browser** (AGENTS.md rule 9). Every plotted number comes from JSON written by `tools/export_lab_data.py` from `results/` (CONTRACT §13). The browser only selects, formats and plots.
- **Provenance is the point.** Judges score ownership and rigor. Each number gets a card (id, value ± uncertainty, convergence, cross-checks, commit) with a green check **only** when it is converged, cross-checked and from a clean tree.
- **Mock first.** Records won't exist until Phase 2. `scripts/make_mock.mjs` writes clearly labelled mock JSON with the exact §13 shapes, so the whole site is built and tested before any physics lands. A visible `MOCK DATA` banner names every file that is still mock.
- **Pages (4 must-have + About):** Inflate, Error budget, Readout designer, Verification; About is short.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (allowlists; note the integrator owns `site/src/data/live/**`), §6.2 (record schema `duq.record/v2`), §6.3 (ID regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`), §11 (green-check rules mirror the claims checker), **§13 (Lab data shapes: your spec)**, §14 (status file).
- `docs/plan/RESEARCH.md` §1 (parameters), §4.1 (why ε(a+a†) can't pick a well), §5 (Γ_X channels, anchors), §6 (Γ_Z = 2κ_aα²coth 2α²), §7 (readout ringing 3.14 MHz, Q ≈ 2.46, settle 0.73/1.13 µs).
- `docs/plan/briefs/06-l3-prep.md` §4 (`lab.inflation_wigner.npz` keys), `07-l4a-readout.md` §7 (t2_3 ids and arrays), `02-l0-tools.md` §4 (`results/index.json` shape: `{"schema":"duq.index/v1","generated_at","count","records":[...]}`), and briefs 05/09/10 when they exist (t2_1, t2_4b, t2_4c outputs).
- `docs/challenge_prompt_v4.md` Section 2 (what each task asks) for page copy. `results/records/` and `results/arrays/` as they appear.

## 3. Allowlist (touch nothing else)
- `site/**` (except `site/src/data/live/**`, see below), `tools/export_lab_data.py`, `.github/workflows/pages.yml`, `docs/plan/status/l6-lab.md`, `docs/plan/status/l6-shots/**`.
- **Never commit `site/src/data/live/**`**: CONTRACT §1 gives it to the integrator. Generate it locally for the smoke test and leave it untracked. Before each commit: `git status --porcelain -- site/src/data/live` must show nothing staged.
- Never commit `site/node_modules/`, `site/dist/`, `site/dist-single/` (already git-ignored). **Do** commit `site/package-lock.json` and `site/src/data/mock/*.json`.
- No `tests/test_l6_lab.py` (not on the allowlist): all tests are vitest under `site/test/`; the exporter is tested from vitest against fixtures in `site/test/fixtures/`. Do not edit `.gitignore`, `src/`, `tasks/`, `tools/` other files, `results/`, `figures/`.

## 4. Interfaces you implement / rely on
**Stack:** Vite + TypeScript (vanilla, no framework) + `plotly.js-dist-min`; Node 24 locally, Node 22 in CI. Install with `npm --prefix site install -D vite typescript vitest jsdom vite-plugin-singlefile @types/plotly.js-dist-min` and `npm --prefix site install plotly.js-dist-min`; record the resolved versions in the status file.
```
site/package.json        scripts: dev="vite", build="tsc --noEmit && vite build", build:single="vite build --config vite.single.config.ts",
                         preview="vite preview", test="vitest run", typecheck="tsc --noEmit", mock="node scripts/make_mock.mjs"
site/vite.config.ts      base: './', build.outDir 'dist'; vitest: test.environment 'node' (jsdom per file via // @vitest-environment jsdom)
site/vite.single.config.ts  base './', plugins [viteSingleFile()], build.outDir 'dist-single' -> site/dist-single/index.html
site/index.html          <nav> with 5 links, <div id="banner">, <main id="app">, <dialog id="card">
site/src/main.ts         hash router: '#/inflate' (default; '' and unknown -> inflate), '#/errors', '#/readout', '#/verify', '#/about'
                         export function renderRoute(hash: string, root: HTMLElement, b: Bundle): void
site/src/data/types.ts   DuqRecord (CONTRACT §6.2), InflationData, ErrorsData, ReadoutData, VerifyData, Bundle, DataName, Source='live'|'mock'
site/src/data/validate.ts  validateRecords/Inflation/Errors/Readout/Verify(x: unknown): string[]   // [] = valid; messages name the path, e.g. "records[3].id"
site/src/data/index.ts   const live = import.meta.glob('./live/*.json', {eager: true, import: 'default'}); same for './mock/*.json'
                         export function loadBundle(liveMods = live, mockMods = mock): Bundle
                         // per file: live if present AND valid, else mock; b.sources[name] says which; invalid live -> mock + banner note
site/src/components/provenance.ts
  isConverged(r): boolean     // r.convergence?.converged === true, OR (r.convergence === null && non-empty r.notes)  (CONTRACT §11.4)
  recordStatus(r): {status: 'green'|'amber', reasons: string[]}  // green ONLY if isConverged && some cross_check.agree===true && provenance.dirty===false
  commitUrl(sha: string|null): string|null   // 'https://github.com/pkarakala/duquantum-cat-qubit/commit/' + sha
  formatValue(v: number, unc: number|null): string   // toPrecision(5) / unc toPrecision(2); exponent form if |v|<1e-3 or >=1e4
  renderCard(r): HTMLElement ; renderChip(id, byId): HTMLElement ; openCard(id, byId): void   // <dialog>, Esc closes, focus returns
site/src/components/plot.ts  plot(el, traces, layout): Promise<void>  // the ONLY file that imports Plotly (so tests can vi.mock it); applies theme
site/src/lib/wigner.ts   wignerRange(frames): [number, number]   // [-M, M], M = max|w| over ALL frames (fixed across the animation)
site/src/pages/{inflate,errors,readout,verify,about}.ts   each: export function render(root: HTMLElement, b: Bundle): void
site/src/style.css       CSS custom properties; light/dark via prefers-color-scheme; Okabe–Ito palette; >= 360 px; :focus-visible rings
site/scripts/make_mock.mjs   export function buildMock(): Record<DataName, unknown>; CLI writes site/src/data/mock/*.json (deterministic)
```
**Data shapes (CONTRACT §13, verbatim) plus additive optional keys** (allowed because no §13 key is changed; mark them optional in `types.ts`):
- `records.json` `[record, ...]`. `inflation.json` `{t_us[], na[], nb[], top2_a[], top_b[], effective:{t_us[], na[]}, wigner:{x[], y[], frames:[{t_us, w[][]}]}, record_ids[]}`, with `w[iy][ix]`.
- `errors.json` `{gamma_x:{one_mode:[{alpha2, value, unc, id}], two_mode:[...], td:[...], analytic:{alpha2[], ch1[], ch2[], total[]}, thermal:{"<nth>":[...]}, local_slope:{alpha2[], one_mode[], two_mode[]}}, gamma_z:{td:[...], eig:[...], pred:{alpha2[], value[]}}}`. `unc` may be `null`; `local_slope` arrays may hold `null`. Optional: `analytic.source`.
- `readout.json` `{alpha, linresp:{freq_MHz, Q, t5, t1}, signals:{t_us[], b_plus_re[], b_plus_im[], b_minus_re[], b_minus_im[]}, tradeoff:[{eps_over_g2, snr_T1us, gamma_x_rel, id}], pulses:{"<name>":{t_us[], eps[], snr, cost, id}}}`. Optional: `signals.eps_over_g2` (scalar), `signals_by_eps:[{eps_over_g2, t_us[], b_plus_re[], ...}]` (drives the slider), `tradeoff[].alpha` (drives the α selector), `pulses[name].signal:{t_us[], db_abs[]}`, `linresp.id`. Pulse `t_us` = bin edges (length n+1), `eps` = bin values (length n).
- `verify.json` `{generated_at, tests:{passed, failed, skipped}, convergence:[{id, axis, values[], results[], tol, converged}], cross_checks:[{id, method, rel_diff, tol, agree}]}`. Optional: `tests.source` (`"junit"`, `"mock"` or `null` = not run), `claims:{ok, warn, fail, files[]}`.

**Exporter** `tools/export_lab_data.py` (stdlib + numpy only; **never import `src.*`**, which pulls in dynamiqs):
```python
def load_records(results="results") -> list[dict]       # index.json["records"]; fallback: every results/records/*.json; sorted by id
def build_inflation(records, arrays_dir) -> dict | None  # None if lab.inflation_wigner.npz missing
def build_errors(records, arrays_dir) -> dict | None     # None if no t2_1/t2_2 records
def build_readout(records, arrays_dir) -> dict | None    # None if no t2_3 records
def build_verify(records, junit=None) -> dict            # always written (from records)
def downsample(frames, x, y, max_px=81) -> tuple         # stride = ceil(n/81) on both axes
def main(argv=None) -> int
# CLI: python -m tools.export_lab_data [--results results] [--out site/src/data/live] [--junit PATH] [--max-mb 8] [--dry-run]
```
- Select records by the **first four dot-tokens of the id** (task, quantity, method, model) and read numbers from `params` (`alpha`, `n_th`, `eps_z_over_g2`). Never parse numbers out of ids, and don't filter on the `quantity` field (the §6.2 example writes `"Gamma_X"` there).
- `inflation`: from `results/arrays/lab.inflation_wigner.npz` (l3 keys `t_us, na, nb, top2_a, top_b, eff_t_us, eff_na, x, y, frames[k, iy, ix], frame_t_us`); `record_ids` = the `t1_1.*` ids present (`t1_1.peak_na.td.two_mode.a2.10`, `t1_1.steady_na…`, `t1_1.peak_nb…`, `t1_1.settle_1pct…`). Wigner ≤ 81×81, `round(w, 4)`, `-0.0 → 0`.
- `errors.gamma_x`: `one_mode`/`two_mode` = `t2_1.gamma_x.eig.<model>.*` with `n_th == 0`; `td` = `t2_1.gamma_x.td.*`; `thermal["<n_th:g>"]` = eig records with `n_th > 0` (two_mode if any, else one_mode; say which in status); `alpha2 = alpha**2`, `unc = uncertainty`. `analytic`: an l2b npz with keys `alpha2, ch1, ch2, total` if one exists (glob `results/arrays/t2_1.*channel*.npz`); else the closed form of RESEARCH §5 on α² ∈ [0.5, 9] (200 points) with constants from the records' `params` (g₂ = 2π·g2_MHz, κ_b = 2π·kappa_b_MHz, κ_a = 2π·kappa_a_kHz·1e-3 rad/µs, κ₂ = 4g₂²/κ_b): `ch1 = κ_aα²(coth 2α² − 1)`, `ch2 = (κ_a²/κ₂)e^{−2α²}` (c = 1), `total = ch1 + ch2`, and set `analytic.source = "exporter_closed_form_RESEARCH_5"`. `local_slope`: `t2_1.gamma_local_slope.*` records if present, else finite differences of ln Γ between adjacent α² points (at midpoints) on a union grid, `null` where a model has no value.
- `errors.gamma_z`: `td` = `t2_2.gamma_z.td.two_mode.*` without `nth` (n_th == 0); `eig` = `t2_2.gamma_z.eig.two_mode.*`; `pred` = the `analytic_coth` cross_check `value` of each td record (no formula needed).
- `readout`: `linresp` from record `t2_3.ring_freq.linresp.two_mode.a2.10` numerics (`freq_MHz, Q, t_settle_5pct_us → t5, t_settle_1pct_us → t1`); `signals_by_eps` from `results/arrays/t2_3.ring_freq.td.two_mode.a2.10.npz` (`t_us, eps_over_g2, b_plus, b_minus`: complex, shape (n_eps, n_t); downsample t to ≤ 400 points); `signals` = the ε nearest 1.0 g₂. `tradeoff` comes from `results/arrays/t2_4b.grid.npz`, written by l4b (brief 09 §7) as **flat rows**, one per (α, ε), with ε = 0 rows included. Required keys: `alpha`, `eps_over_g2`, `gamma_x`, `gamma_z_re`, `snr_T0.5`, `snr_T1.0`, `snr_T2.0`, `leakage`. Extra keys: `gamma_x_rel`, `gamma_z_im`, `snr_rate`, `gamma_x_ok`.
  - Map `snr_T1us ← snr_T1.0`.
  - Map `gamma_x_rel ← gamma_x_rel`, or `gamma_x / gamma_x(ε=0, same α)` if that column is absent.
  - Map `alpha ← alpha`.
  - Drop rows where `gamma_x_ok` is false, or show them greyed and flagged "unconverged".
  - Put the key names in one `L4B_KEYS` dict at the top.
  - If there's no npz, build the same rows from `t2_4b.*` records.
  - Each `id` is the matching `t2_4b.gamma_x.*` record (`params.alpha` and `eps_z_over_g2` equal within rel 1e-6), else `null`.

`pulses` come from l4c (brief 10 §7) through an `L4C_KEYS` dict:
  - `results/arrays/t2_4c.pulses.npz`: bin edges and values per finalist, giving `t_us` (edges) and `eps` (values).
  - `results/arrays/t2_4c.frontier.npz`: per candidate, name, T, snr, costs, gains.
  - `snr` is the `t2_4c.snr.td.two_mode.a2.10.p{name}.T1.0us` record (else the `linresp` one, labelled).
  - `cost` is the `t2_4c.cost.linresp.two_mode.a2.10.p{name}` record.
  - Pulse name tokens: `square`, `ramp_cos_tau*`, `ramp_lin_tau*`, `clear_k*_t*`, `svd`, `gen`, `grad`. Read the final tokens from `docs/plan/status/l4c-capstone.md`.
- `verify`: one `convergence` row per record per swept axis (`tol = rel_tol`, `converged` = the record's flag); one `cross_checks` row per entry; `tests` from `--junit` (stdlib `xml.etree`: passed = tests − failures − errors − skipped; failed = failures + errors) else zeros with `source: null`; `claims` via `from tools.check_claims import check_file` in `try/except ImportError` (omit on failure).
- Rounding: arrays to 6 significant figures; record objects verbatim. `json.dumps(..., separators=(",", ":"), allow_nan=False)`.
- **Size gate:** build everything in memory; if the total encoded size is > `max_mb·1_000_000` bytes, print the per-file sizes, write nothing, and exit 1. A missing input means that file is omitted. Delete any stale `<out>/<name>.json` and print `omitted <name>.json (missing <path>)`. The site then falls back to mock for that file, and the banner names it.

## 5. Tests to write FIRST (TDD)
Write these under `site/test/`, run them, and see them fail; commit them as `l6-lab: tests first`. Stub Plotly with `vi.mock('../src/components/plot', () => ({ plot: vi.fn(async () => {}) }))` and stub `window.matchMedia` in jsdom tests. All of `npm test` must finish in < 30 s.
1. `schema.test.ts`
   - `validate*(buildMock()[name])` returns `[]` for all 5 files. `it.skipIf(!exists)` the same for each `site/src/data/live/<name>.json`.
   - Mutations must fail with a path in the message: deleting `records[0].id` gives an error containing `"records[0].id"`; `inflation.wigner.frames[0].w[0]` one element short gives an error mentioning `frames[0]`; `errors.gamma_x.one_mode[0].value = "x"` gives an error mentioning `one_mode[0].value`; `tradeoff[0].gamma_x_rel = NaN` gives an error.
   - Every record id matches `/^[a-z0-9_]+(\.[a-z0-9_\-]+)*$/`; every mock id starts with `mock.`. Every id referenced by the mock errors/readout/inflation resolves in the mock `records`.
   - Wigner frames are ≤ 81×81 with `w.length === y.length` and `w[0].length === x.length`; the summed `JSON.stringify` length of the mock is < 8,000,000.
2. `provenance.test.ts`
   - The base record has `convergence.converged: true`, one cross_check with `agree: true`, and `dirty: false`, giving `status 'green'` and `reasons []`.
   - Each of `converged: false`, `cross_check: []`, all `agree: false`, `dirty: true` and a missing `provenance` gives `'amber'` with a matching reason string (`"not converged"`, `"no agreeing cross-check"`, `"dirty working tree"`, `"no provenance"`).
   - `convergence: null` with `notes: "analytic, truncation-independent"` passes `isConverged`; with `notes: ""` it does not.
   - `commitUrl('abc1234') === 'https://github.com/pkarakala/duquantum-cat-qubit/commit/abc1234'`, `commitUrl(null) === null`.
   - `formatValue(1.2021e-4, 2e-8) === '1.2021e-4 ± 2.0e-8'`, `formatValue(0.5135, null) === '0.51350'`.
   - `renderCard(rec)` text contains the id, units, method, `Na`, the rel_tol, every cross-check method, `0.3.7`, the timestamp, and an `<a>` with the commit URL. The root carries `data-status="green"` and the visible text "verified". The amber state shows its reasons in text, not by color alone. A wrapped intro record (`dynamiqs: null`, `git_branch: null`) renders "n/a" without throwing.
3. `router.test.ts` (`// @vitest-environment jsdom`)
   - For each of `#/inflate #/errors #/readout #/verify #/about`, `renderRoute(hash, root, loadBundle())` doesn't throw. `root.querySelector('h1')` has the page title (Inflate / Error budget / Readout designer / Verification / About), and `plot` was called at least once on the 3 data pages.
   - `''` and `'#/nope'` render Inflate.
   - With mock sources, `#banner` has `role="status"` and text containing `MOCK DATA` plus the names of the mock files. With `loadBundle(fakeLiveMods, mockMods)` where all 5 files are live and valid, the banner is empty and hidden. With one invalid live file, that file falls back to mock and the banner names it.
   - Every `input, select, button` on every page has an accessible name (`aria-label`, `aria-labelledby`, or a `<label>`).
4. `lib.test.ts`
   - `wignerRange([{w:[[0.1,-0.3]]},{w:[[0.2,0.05]]}])` deep-equals `[-0.3, 0.3]`.
   - The readout slider maps index → `signals_by_eps[i]` sorted by `eps_over_g2`.
   - `buildMock()` deep-equals the committed `site/src/data/mock/*.json` (mocks are fresh and deterministic: no `Date.now()`, fixed `generated_at: "MOCK"`).
5. `export.test.ts` (`it.skipIf(!process.env.DUQ_PY)`; run from the repo root with `spawnSync(process.env.DUQ_PY, ['-m','tools.export_lab_data','--results','site/test/fixtures/results','--out',tmp])`).
   - Fixtures: 4 small records plus a 3-frame 5×5 `lab.inflation_wigner.npz`, written by `site/test/fixtures/make_fixtures.py` (numpy) and committed.
   - Exit 0, all written files pass `validate*`, and `inflation.wigner.frames.length === 3`.
   - `--max-mb 0.0001` gives exit 1 and an empty out dir.
   - With the npz deleted (use a copy of the fixtures), `inflation.json` is absent and the stale one is removed.

## 6. Method, step by step
**Part A (mock; 6:00–9:45 PM; 3 h cap)**
1. (10 min) `git switch -c std/l6-lab standard-track`. Copy `_TEMPLATE.md` to `docs/plan/status/l6-lab.md` and set State `IN_PROGRESS`. Hand-write `site/package.json`, `tsconfig.json` (`strict`, `resolveJsonModule`, `types: ["vite/client"]`) and the two vite configs, then install (§4).
2. (20 min) `types.ts`, `validate.ts` stubs, and the §5 tests 1–4. See them fail; commit.
3. (25 min) `make_mock.mjs` from analytic formulas, every file tagged mock. Use constants g₂ = 2π·0.763, κ_b = 2π·2.6, κ_a = 2π·9.3e-3 (rad/µs), κ₂ = 4g₂²/κ_b = 5.6275, α = 2.1.
   - Inflation: na(t) = α²[1 − e^{−σt}(cos ωt + (σ/ω)sin ωt)], with σ = κ_b/4 = 4.084 and ω = 19.717, on t = 0…3 µs (301 points); effective na = α²(1 − e^{−2κ₂α²t}). Wigner frames at l3's 39 times (0, 0.02, …, 0.50, then 0.6, …, 3.0) on x, y = linspace(−4, 4, 81), using the even-cat formula with β = √na(t). The 4 `mock.t1_1.*` chips.
   - Γ_X: one_mode = ch1 + 1.3·ch2 for α = 0.8…2.7 (step 0.1). At α = 1.0, ch1 + ch2 = 2.2625e-3 (vs the anchor 2.2819e-3). two_mode = one_mode × the log-interpolated factor through (1.0, 1.01), (1.4, 1.12), (1.8, 2), (2.1, 3) for α ≤ 2.4. td = two_mode at α ∈ {0.8, 1.0, 1.2, 1.4}. Thermal n_th ∈ {0.01, 0.03, 0.05} adds κ_a·n_th·e^{−2α²}.
   - Γ_Z = 2κ_aα²coth 2α²: 0.1212 at α = 1.0, 0.5154 at α = 2.1.
   - Readout: linresp {3.14, 2.46, 0.73, 1.13}. b₊ = −(ε/(2g₂α))·(the same step response) − 0.003i, and b₋ = −conj(b₊). ε grid {0.05, 0.1, 0.2, 0.5, 1, 2, 3} g₂; snr_T1us = κ_b∫₀¹|2b₊|²dt (≈ 0.03 at 0.1 g₂; RESEARCH §7 says ≈ 0.04); gamma_x_rel = 1 + 0.5(ε/g₂)². Pulses `square`, `cos_ramp`, `clear`, `svd`.
   - Mock records for every id: `notes: "MOCK: synthetic placeholder, not a result"`, `git_commit: "mock"`. Make at least one deliberately amber (e.g. `mock.t2_1.gamma_x.eig.two_mode.a2.40.nth0` with `converged: false`).
4. (20 min) `data/index.ts`, router, banner, `style.css` (tokens `--bg --fg --muted --accent --ok:#009E73 --warn:#E69F00`; series one_mode #0072B2, two_mode #D55E00, td #009E73, ch1 #CC79A7, ch2 #E69F00, total grey dashed, thermal #56B4E9 shades; `:focus-visible` 3 px outline; nav wraps; tables in `overflow-x:auto`). `provenance.ts` until tests 1–2 pass.
5. (60 min) Pages:
   - **Inflate:** time scrubber (`<input type=range>` over frame index, label "t = 0.240 µs") plus a Play/Pause button (`aria-pressed`, about 8 fps, stops at the end, no autoplay). Wigner `heatmap` with a diverging scale (#2166ac → #f7f7f7 → #b2182b), `zmid 0`, and `zmin/zmax = wignerRange(all frames)` fixed for every frame (update with `Plotly.react`). ⟨n_a⟩ and ⟨n_b⟩ vs t, with the dashed effective-model ⟨n_a⟩, a dotted α² = 4.41 line and a vertical cursor at the frame time. Log-y truncation monitors `top2_a` and `top_b` with a 1e-4 line. Provenance chips for `record_ids`.
   - **Error budget:** log-y Γ_X and Γ_Z vs α², with error bars from `unc`. Toggles (checkboxes): one-mode, two-mode, time-domain, analytic ch1, ch2, total, and each thermal n_th. The hovertemplate shows the value and the record id (`customdata`). A local-slope subplot sits below on a shared x axis, with reference lines at 4 and 2. `plotly_click` opens the card.
   - **Readout designer:** an α `<select>` only if `tradeoff[].alpha` has more than one value. An ε_Z slider whose integer index snaps to the precomputed grid (label "ε_Z = 0.5 g₂"). Re/Im of ⟨b⟩± vs t. A trade-off scatter of SNR(1 µs) vs Γ_X/Γ_X(0), with the current ε point enlarged and outlined. A pulse `<select>` showing the step-plotted pulse shape, its signal if present, SNR and cost, plus a comparison table of all pulses with chips. A linresp ringing card: 3.14 MHz, Q ≈ 2.46, settle 0.73 µs (5%) / 1.13 µs (1%), with its chip.
   - **Verification:** a test summary (or "not run"). A sortable convergence table (click a header to sort; `aria-sort`). A cross-check table with ✓/✗ marks plus text. The claims-check status. Copyable how-to-reproduce commands (§9).
   - **About:** what this is; the honest AI-use statement: "Planned with Claude Code, implemented by Cursor agents under Harshit's direction, physics reviewed by Gemini; every number comes from a script in this repo with a provenance record." Also a README link (`https://github.com/pkarakala/duquantum-cat-qubit#readme`) and a note on which data is mock.
   - Dark mode: `plot.ts` reads the CSS variables for paper/plot/font colors and re-plots on `matchMedia('(prefers-color-scheme: dark)')` change. Use `responsive: true`.
6. (15 min) `tools/export_lab_data.py` plus the fixtures and test 5. Run it on whatever `results/` holds now (at least the `t1_*` records) into `results/quick/lab_live` (git-ignored).
7. (10 min) `.github/workflows/pages.yml`: `on: push (branches [main]) + workflow_dispatch`; `permissions: contents read, pages write, id-token write`; `concurrency: pages`. The build job runs on ubuntu-latest: checkout, `actions/setup-node` with node 22 (npm cache, `cache-dependency-path: site/package-lock.json`), `npm ci` and `npm run build` in `site/`, then `actions/upload-pages-artifact` with path `site/dist`. The deploy job uses `environment: github-pages` and `actions/deploy-pages`. Use the current major versions. It only takes effect once the repo is public and Pages is enabled; that is Harshit/Pranav's call, so say so in a comment at the top.
8. (20 min) Build both targets and run the smoke test (§8 gate 6). Commit, then update the status: "Part A done (mock), waiting for records". The integrator can merge Part A at G1.

**Part B (live; 1 h, once records exist on `standard-track`)**
9. `git merge standard-track` into `std/l6-lab`. Run `& $env:DUQ_PY -m tools.export_lab_data` (writes the untracked `site/src/data/live/`). Fix the `L4B_KEYS`/`L4C_KEYS` mappings against what l4b/l4c actually wrote. Run `npm test`, which now validates live too. Do the live smoke test, add screenshots and commit the code only. Status: `DONE`.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **No records, figures or arrays.** This lane writes code, mock JSON (`site/src/data/mock/{records,inflation,errors,readout,verify}.json`, committed) and screenshots (`docs/plan/status/l6-shots/*.png`, committed).
- **Quick:** `--out results/quick/lab_live` (git-ignored). **Production data:** the integrator runs `tools.build_index`, then `tools.export_lab_data`, and commits `site/src/data/live/*.json` and rebuilds `dist-single` before 8:00 AM. The export takes seconds.
- **Build outputs:** `site/dist/` (Pages) and `site/dist-single/index.html` (offline demo). Both are git-ignored, so write the build command and file size in the status file.
- **Jobs to queue:** none.

## 8. Acceptance gates (ALL must pass before DONE)
1. `npm --prefix site run typecheck`: 0 errors. `npm --prefix site test`: every test passes in < 30 s, with test 5 run (DUQ_PY set) and not skipped.
2. `npm --prefix site run build` and `npm --prefix site run build:single` succeed. `site/dist-single/` contains only `index.html`, < 15 MB (record the size). If it is larger, see §11.
3. The exporter on real `results/` exits 0 and prints each file's size and the total (< 8 MB). `--max-mb 0.0001` exits 1 and writes nothing. Missing inputs are reported as `omitted …`.
4. **Provenance logic:** the mock site visibly shows at least one green ✓ "verified" card and one amber card with reasons. Every live chart point opens a card whose commit link has the form `…/commit/<sha>`.
5. **No physics in the browser:** `Select-String -Path site/src -Pattern 'cosh|tanh|Math\.exp' -Recurse` returns nothing (formulas live only in `scripts/make_mock.mjs` and the exporter).
6. **Smoke test** (`npm --prefix site run dev`, Cursor's browser): every page at desktop (≥ 1280 px) and at 375 px, with mock data and then with live data, with no console errors. At 375 px, `document.documentElement.scrollWidth <= 375` (no horizontal scroll). Keyboard check: Tab reaches the nav, slider, play and toggles, with a visible focus ring; Space toggles play; the arrow keys move the slider; Esc closes the card.
   - Save these screenshots to `docs/plan/status/l6-shots/`:
     - `<page>-desktop-mock.png` and `<page>-375-mock.png` for all 5 pages;
     - `<page>-desktop-live.png` for all 5 pages;
     - `inflate|errors|readout-375-live.png`;
     - `offline-<page>.png` for all 5 pages.
   - List them in the status file.
7. **Offline:** open `file:///D:/Brown%20University/duhack/duquantum-cat-qubit/site/dist-single/index.html` (your worktree path), go through all 5 hash routes, and open a card. The Network panel should show no http(s) requests, and the console should show no errors.
8. `git diff --name-only standard-track...HEAD` lists only §3 paths, with nothing under `site/src/data/live/`, `node_modules/` or `dist*`.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
git switch -c std/l6-lab standard-track
Copy-Item docs/plan/status/_TEMPLATE.md docs/plan/status/l6-lab.md
npm --prefix site install                        # after writing package.json; npm ci in CI
npm --prefix site run mock                       # regenerate site/src/data/mock/*.json
npm --prefix site test; npm --prefix site run typecheck
npm --prefix site run dev                        # http://localhost:5173/#/inflate
npm --prefix site run build; npm --prefix site run build:single
(Get-Item site/dist-single/index.html).Length / 1MB
& $env:DUQ_PY site/test/fixtures/make_fixtures.py
& $env:DUQ_PY -m tools.export_lab_data --out results/quick/lab_live     # quick check
& $env:DUQ_PY -m tools.export_lab_data --max-mb 0.0001; $LASTEXITCODE   # expect 1
& $env:DUQ_PY -m tools.export_lab_data                                  # live, untracked; do NOT commit
& $env:DUQ_PY -m pytest -m "not slow" -q --junitxml results/quick/junit.xml   # optional, for --junit
git status --porcelain -- site/src/data/live     # must be untracked/empty in every commit
git diff --name-only standard-track...HEAD
```
How-to-reproduce block for the Verification page: `& $env:DUQ_PY -m pytest -m "not slow" -q` · `bash run_all.sh --quick` · `& $env:DUQ_PY -m tools.build_index` · `& $env:DUQ_PY -m tools.check_claims` · `& $env:DUQ_PY -m tools.export_lab_data` · `npm --prefix site ci; npm --prefix site run build:single`.

## 10. Out of scope / do not
- No physics, fitting or solving in the browser; no fetching at runtime (data is bundled; `file://` must work). No live sandbox (cut first in the plan).
- No framework (React/Vue), no CSS framework, no analytics, no external fonts or CDNs.
- Don't invent or "fix" numbers. If live data looks wrong, show it as it is and write it in the status file for Claude's review.
- Don't commit `site/src/data/live/**`, `results/**`, `figures/**`, or edit another lane's files, CONTRACT, `.gitignore` or `tools/` other than the exporter. Don't enable Pages or change repo settings.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
- **Wording:** `> **Q:** l4b wrote results/arrays/t2_4b.grid.npz with keys [..] instead of the expected alpha/eps_over_g2/T_us/snr/gamma_x/gamma_x0: map <k> -> snr? > **Options:** A) map as listed B) build tradeoff from t2_4b records only > **Recommendation:** B (every point gets an id) > **Blocking?** no: the Readout page shows mock tradeoff meanwhile.` Use the same form for any §13 shape question or cross-lane mismatch.
- **Fallbacks:**
  - Plotly breaks in jsdom: keep it behind `plot.ts` and mock it.
  - `dist-single` is > 15 MB or slow on the demo laptop: switch to `plotly.js-cartesian-dist-min` (it includes scatter and heatmap) and note it.
  - The single-file plugin fails: `vite build` with `base './'` plus a `dist/` zip opened from `file://`; check that it works, since module scripts may be blocked, then DECISION NEEDED.
  - The Wigner animation is janky: reduce it to 20 frames in the browser by index stride.
- **Cut line at 8:45 PM if behind**, in this order:
  1. The pulse signal plot (keep the table).
  2. The local-slope subplot.
  3. The thermal toggles.
  4. The Readout designer interactivity (replace it with static tables from `readout.json`; this is the plan's cut item 8).
  5. The About styling.
- **Never cut:** the provenance card plus the green/amber logic, the Inflate, Error budget and Verification pages, the mock banner, the single-file offline build, and the exporter's size gate.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
**Status file at DONE:**
- State `DONE`, branch, last commit.
- npm and node versions, plus the resolved `vite`, `vitest`, `plotly.js-dist-min` and `vite-plugin-singlefile` versions.
- The test count and runtime, the gates table with evidence, and the `dist-single` size.
- The exporter output: files written or omitted, with sizes and total.
- Which data files are live vs mock at hand-off, the `L4B_KEYS`/`L4C_KEYS` mappings used, the `thermal` model choice, and whether `analytic` came from l2b or the closed form.
- The screenshot list, and the exact refresh commands for the integrator (build_index → export_lab_data → commit `site/src/data/live` → `build:single`).
- Any record that renders amber, with its reason.

**Explain-back questions (Harshit answers in `docs/defense.md`):**
1. A judge clicks the two-mode Γ_X point at α² = 4.41 and sees a green check. What exactly does that check certify (which convergence axes, which independent cross-check and its tolerance, which commit), and what would turn it amber?
2. On the Inflate page, why does the Wigner function stay mirror-symmetric (x → −x) all the way to |C₊⟩, and what does the ⟨n_a⟩ overshoot to about 6.89 above α² = 4.41, which the dashed effective model misses, say about the buffer?
3. On the Readout designer, moving the ε_Z slider raises both SNR and Γ_X/Γ_X(0). Why is Γ_X, not Γ_Z, the cost that matters, and why can the page snap to a precomputed grid instead of computing anything when you move it?
