# Status: lane `l6-lab`

> This file is the only channel to Harshit, the integrator and Claude's later review. Keep it factual: commands and real output, not intentions.

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (Part A done; Part B waits for real records) |
| Branch | `std/l6-lab` |
| Agent / model | Cursor agent (Grok 4.6) |
| Started (EDT) | Sat Oct 24 2026, 18:30 |
| Last update (EDT) | Sat Oct 24 2026, 19:10 |
| Last commit | (Part A commit on `std/l6-lab`; sha filled after commit) |

## Environment
- Node v24.18.0, npm 11.16.0
- Resolved: vite@8.3.5, vitest@5.0.5, plotly.js-dist-min@4.1.2, vite-plugin-singlefile@2.3.4, typescript@7.0.2, jsdom@30.1.3

## Milestones
- [x] Read brief, CONTRACT §13, RESEARCH, RUNBOOK
- [x] Tests written first: `site/test/{schema,provenance,router,lib,export}.test.ts` (commit `aaf52be`)
- [x] Part A implementation complete (mock Lab, 4 pages + About, exporter, Pages workflow)
- [x] Builds: `site/dist/` and `site/dist-single/index.html`
- [x] Exporter written and tested on fixtures (`DUQ_PY` set; not skipped)
- [x] Smoke test (mock) done; screenshots under `docs/plan/status/l6-shots/`
- [ ] Part B (live data): waits for records on `standard-track`
- [x] Explain-back questions drafted (from brief §12)

## Acceptance gates (brief §8, Part A)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. typecheck + test | PASS | `npm --prefix site run typecheck`: 0 errors. `DUQ_PY=... npm --prefix site test`: **58 passed, 5 skipped** (the 5 skips are `live *.json` validators; no live files). Export suite 6/6 passed when run as `vitest run test/export.test.ts`. Duration ~0.9–1.5 s. |
| 2. builds | PASS | `npm --prefix site run build` and `build:single` succeed. `site/dist-single/` contains only `index.html`, **6,120,493 bytes (5.8 MB) < 15 MB**. |
| 3. exporter | PASS | Fixtures: exit 0, writes records/inflation/errors/verify, omits readout. `--max-mb 0.0001` exits 1, writes nothing. Real `results/` (intro JSONs only): omitted inflation/errors/readout; wrote empty `records.json` + `verify.json`; total 134 bytes. |
| 4. provenance logic | PASS | Green chip `mock.t1_1.peak_na.td.two_mode.a2.10` opens a card with "verified: converged, cross-checked, clean tree". Amber chip `mock.t2_1.gamma_x.eig.two_mode.a2.40.nth0` is labelled "needs review (not converged)". Mock commit is `mock` so `commitUrl` is null (no fake GitHub link). |
| 5. no physics in browser | PASS | `rg -n 'cosh|tanh|Math\.exp' site/src` → no matches. Formulas live in `site/scripts/make_mock.mjs` and `tools/export_lab_data.py`. |
| 6. smoke (mock) | PASS | Dev server `http://127.0.0.1:5173`. All 5 pages at desktop and 375. Banner `MOCK DATA: records.json, inflation.json, errors.json, readout.json, verify.json are synthetic placeholders, not results.` At 375, `document.documentElement.scrollWidth === 375` on inflate/errors/readout/verify. Green card `mock.t1_1.peak_na.td.two_mode.a2.10`; amber `mock.t2_1.gamma_x.eig.two_mode.a2.40.nth0`. Live smoke waits for real records (Part B). |
| 7. offline | PASS | Chrome headless opened `file://…/site/dist-single/index.html#/{inflate,errors,readout,verify,about}`. Title becomes `Inflate · Cat Qubit Lab`; dump-dom shows inlined JSON (no runtime fetch). Cursor browser blocks `file://`, so Network-panel check is: `import.meta.glob` eager + no `fetch(` in `site/src`. |
| 8. allowlist | PASS | `git diff --name-only standard-track...HEAD` is only `site/**`, `tools/export_lab_data.py`, `.github/workflows/pages.yml`, `docs/plan/status/l6-lab.md`, `docs/plan/status/l6-shots/**`. Nothing under `site/src/data/live/`. |

## Screenshots (`docs/plan/status/l6-shots/`)
Mock desktop: `inflate-desktop-mock.png` (green provenance card open), `errors-desktop-mock.png`, `readout-desktop-mock.png`, `verify-desktop-mock.png`, `about-desktop-mock.png`.
Mock 375: `inflate-375-mock.png`, `errors-375-mock.png`, `readout-375-mock.png`, `verify-375-mock.png`, `about-375-mock.png`.
Offline (`file://` dist-single via Chrome headless): `offline-inflate.png`, `offline-errors.png`, `offline-readout.png`, `offline-verify.png`, `offline-about.png`.
Live (`*-desktop-live.png`, `inflate|errors|readout-375-live.png`): **deferred to Part B** (no v2 records/arrays on this worktree yet).

## Exporter on current `results/`
```
records.json  0.000 MB
verify.json  0.000 MB
total 0.000 MB
omitted inflation.json (missing results/arrays/lab.inflation_wigner.npz)
omitted errors.json (missing t2_1/t2_2 records)
omitted readout.json (missing t2_3 records)
```
`--max-mb 0.0001` → exit 1, `total 134 bytes exceeds --max-mb 0.0001 (100 bytes); writing nothing`.

## Data at hand-off (Part A)
- All five Lab files are **mock** (`site/src/data/mock/*.json`, committed).
- `site/src/data/live/**` is untracked / empty (integrator-owned).
- `L4B_KEYS`: `snr_T1us ← snr_T1.0`; `gamma_x_rel` from column or `gamma_x / gamma_x(ε=0)`; drop/flag `gamma_x_ok == false`.
- `L4C_KEYS`: `t2_4c.pulses.npz`, `t2_4c.frontier.npz`.
- `thermal` prefers two_mode if any `n_th > 0` eig records exist, else one_mode.
- `analytic` uses l2b `t2_1.*channel*.npz` if present, else `exporter_closed_form_RESEARCH_5` (200 pts on α² ∈ [0.5, 9]).
- Amber mock record: `mock.t2_1.gamma_x.eig.two_mode.a2.40.nth0` (not converged). Also `mock.t2_4b.gamma_x.eig.two_mode.a2.10.ez3g2` has a disagreeing overlay.

## Integrator refresh (Part B / before 8:00 AM)
```
$DUQ_PY -m tools.build_index
$DUQ_PY -m tools.export_lab_data --out site/src/data/live
# commit site/src/data/live/*.json on standard-track (integrator)
npm --prefix site ci
npm --prefix site run build:single
```

## Commands run (most recent first)
```text
npm --prefix site test
# 58 passed | 5 skipped (live validators), ~0.9 s

npm --prefix site run typecheck
# 0 errors

npm --prefix site run build && npm --prefix site run build:single
# dist/ + dist-single/index.html 6120493 bytes

$DUQ_PY -m tools.export_lab_data --results site/test/fixtures/results --out <tmp>
# exit 0; inflation.wigner.frames.length == 3; omitted readout.json

$DUQ_PY -m tools.export_lab_data --max-mb 0.0001
# exit 1

$DUQ_PY -m tools.export_lab_data --out results/quick/lab_live
# omitted inflation/errors/readout (no Standard Track arrays yet)
```

## Records produced
None (this lane writes no records).

## Figures / arrays produced
None. Screenshots: `docs/plan/status/l6-shots/*.png`.

## Jobs to queue (for the integrator; jobs > 15 min)
None.

## Deviations from the brief (and why)
- macOS machine (RUNBOOK): POSIX commands; worktree was pre-created (no `git switch -c`).
- Mock pulse SNR ids use lowercase `t1.0us` so they match CONTRACT §6.3 (`^[a-z0-9_]+…`). The brief writes `T1.0us`. See DECISION NEEDED.
- Live smoke screenshots deferred: this worktree's `results/` still has only intro-track flat JSON, not v2 records/arrays. Part B refreshes live data after other lanes merge.
- A workspace checkout briefly moved this worktree to `standard-track`; recovered via existing `std/l6-lab` (commit `2314dc1` preserved in-progress files). Did not create a new worktree.

## DECISION NEEDED
> **Q:** CONTRACT §6.3 id regex is lowercase-only, but briefs 09/10/11 write the pulse/readout tag as `T1.0us`. Mock Lab ids use `t1.0us`. When l4c lands, should the exporter accept both, and should live `validate.ts` allow `T`?
> **Options:** A) keep regex frozen, ask l4c to emit `t1.0us` B) relax ID_RE / validator to allow `T` in the last tag C) exporter maps `T1.0us` → `t1.0us` on read
> **Recommendation:** A (CONTRACT is frozen at G0; l4c brief §11 already flags this). Exporter already matches both suffixes when looking up SNR records.
> **Blocking?** no: mock site and fixture exporter pass.

> **Q:** Part A live screenshots (`*-desktop-live.png`, `inflate|errors|readout-375-live.png`) have no real v2 bundle yet. Take them from fixture export, or wait for Part B?
> **Options:** A) wait for Part B (honest) B) export fixtures into untracked `site/src/data/live/` and shoot that
> **Recommendation:** A
> **Blocking?** no for Part A merge; yes for gate 6 "live" shots until records exist.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. A judge clicks the two-mode Γ_X point at α² = 4.41 and sees a green check. What exactly does that check certify (which convergence axes, which independent cross-check and its tolerance, which commit), and what would turn it amber?
2. On the Inflate page, why does the Wigner function stay mirror-symmetric (x → −x) all the way to |C₊⟩, and what does the ⟨n_a⟩ overshoot to about 6.89 above α² = 4.41, which the dashed effective model misses, say about the buffer?
3. On the Readout designer, moving the ε_Z slider raises both SNR and Γ_X/Γ_X(0). Why is Γ_X, not Γ_Z, the cost that matters, and why can the page snap to a precomputed grid instead of computing anything when you move it?

## Notes for Claude's later review
- Mock Γ_X one-mode is ch1 + 1.3·ch2 (brief §6.3); at α = 1.0 that is 2.2625e-3 vs the RESEARCH anchor 2.2819e-3. Do not "fix" the mock to the anchor.
- Wigner colour scale is fixed by `wignerRange(all frames)`; zmid 0; even-cat formula only in `make_mock.mjs`.
- `tools/export_lab_data.py` never imports `src.*`.
