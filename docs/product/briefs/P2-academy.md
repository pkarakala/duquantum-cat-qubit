# Brief `p2-academy`: the Learn wing: level engine, 8 levels, predict and check gates, presets, progress

> **Paste into a new Cursor agent (Agents window, Worktree mode, base `standard-track`):** "You are product lane `p2-academy`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P2-academy.md`, then execute the brief exactly. Keep `docs/product/status/p2-academy.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p2-academy` | `prod/p2-academy` from `standard-track` | **P1** interface (CONTRACT §5; adapter + stub until P1 merges); **P3** (L6 only; adapter + static snippets until it merges); **l6-lab** site skeleton for routing (lane-local dev entry until then); **P0** presets (labelled mock presets until then) | standard (Sonnet-class) | 4 h | 12:00 AM → **4:00 AM Sun** (L1–L4 playable locally on the TS solver by gate **P-G1, 2:15 AM**) |

## 1. Goal and why
You build the learner-facing **Learn** wing in `site/src/academy/`:
- **8 levels** with their content taken **verbatim** from `docs/product/LEVELS.md`.
- **One loop for every level:**
  1. A concept card.
  2. **Predict** (Run stays disabled until the learner chooses).
  3. Play, with linked views and ≤ 3 controls in PhET style.
  4. Check (Katas style).
  5. Aha, plus "Show the code".
- **Around the loop:** a progress map, an offline hint ladder, and a fallback chain, so the demo **never blocks on the network**.

**Why it matters:**
- The grand prize scores "understanding, learning and growth". Prediction gates plus misconception IDs are the learning design, and the misconception events feed the tutor (P4) and its memory (Backboard).
- **Never cut** (PLAN §3): L1–L5 working offline, presets with fallback, and the predict/check loop.
- **Physics stays out of this folder.** The Lindblad solver lives in P1's `site/src/sim/`. Verified numbers come from the Lab data bundle (records). Two-mode results come from the server or from P0's precomputed presets.

## 2. Read first
- **`docs/product/LEVELS.md`, all of it** (your content source of truth: text, options, misconception IDs, controls, views, checks, aha, show-code, solution, hints, allowed constants, preset, sources).
- **`docs/product/CONTRACT.md`:**
  - §0–§1 (ownership: **P7 owns `site/src/academy/routes.ts`**, so don't create it);
  - **§3**, including "Two-mode is not interactive": the fixed live shape, timeouts and the client fallback order;
  - §4 (ExprTree), **§5** (the sim interface you call), **§7** (LevelSpec), §8 (client tools).
- **The other lanes' interfaces (§4 of each brief):**
  - `docs/product/briefs/P1-ts-sim.md`: `simulate`, `runInWorker`, `wigner`, `linresp`, `C`.
  - `P3-blocks.md`: `mountBlocks`, `expr.toPython`, `wrong-builds.detect`.
  - `P0-server.md` §6 step 5: the preset file names.
- **Spec:** `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md` §3, §4 rules, §6 and §7.
- **`docs/plan/briefs/11-l6-lab.md` §4:** the stack, the data bundle `site/src/data/{live,mock}/*.json`, CSS tokens, the Okabe–Ito palette and the `w[iy][ix]` convention. Also physics `docs/plan/CONTRACT.md` §13 (the `errors.json` and `readout.json` shapes).
- **`docs/plan/RESEARCH.md`:** §1, §4.1, §5–§7. Use these so your copy and overlays never contradict the physics.

## 3. Allowlist (touch nothing else)
- **Yours:**
  - `site/src/academy/**` **except `routes.ts`**: engine, levels, ui, presets, data adapters, the dev entry (`dev.html`, `dev.ts`), the lane-local `vite.config.mts`, `vitest.config.mts` and `tsconfig.json`, and `__tests__/`.
  - `docs/product/status/p2-academy.md`.
- **Import only, never edit:** `site/src/sim/**` (P1), `site/src/blocks/**` (P3), `site/src/data/**` (l6).
- **Never create or edit:** `site/package.json`, lockfiles, `site/index.html`, `site/src/main.ts`, `site/vite*.config.ts` (l6, then P7), `site/src/tutor/**` (P4), `site/src/chain/**` (P6), audio files (P4 ships `/audio/*.mp3`), or `server/**`.
- **Untracked only:** `site/node_modules/`. List the routes and npm deps you need in your status file for P7.

## 4. Interfaces you implement / rely on
```
types.ts        LevelSpec / Control / View / MisconceptionId exactly as CONTRACT §7, plus optional extras (note them for the CONTRACT):
                allowedConstants: number[]; predictFollowUp? (L5 "…and phase flips?"); checkFollowUp? (L4 part 2); codeFallback: string
events.ts       on(type, fn) → off; emit(type, payload). Payloads:
                prediction {levelId, optionId, correct, misconceptionId?, firstTry}   check {levelId, pass, attempt, message}
                pass {levelId, attempts, predictionCorrect}   hint {levelId, hintLevel}   sim {levelId, source, params, summary}
engine.ts       createLevelRun(spec, deps): phases 'concept' → 'predict' → 'play' → 'check' → 'aha'; canRun() is false until choose(optionId);
                records only the FIRST choice as the prediction; setParam, run, check, showHint, attempts, failedChecks
controller.ts   the single API used by the UI, P4's get_level_state tool and the ElevenAgents client tools (CONTRACT §8):
                getLevelState() → {levelId, params, prediction?, misconceptionIds, lastSim:{summary}, hintLevel};
                setParam(name, value), runSim(), showHint(), nextLevel()
sources.ts      runLevelSim(spec, state, {onProgress, signal}) → {result, source, banner?}; source ∈ 'ts' | 'server' | 'preset' | 'records' | 'in-browser-fallback'
simAdapter.ts   P1 through import.meta.glob('../sim/index.ts', {eager: true}), typed by a local copy of the CONTRACT §5 interfaces; when absent, a stub plays presets
blocksAdapter.ts  P3 (workspace/expr/wrong-builds) through the same glob pattern; when absent, L6 shows static example builds and codeFallback strings
progress.ts     getLearnerId(): UUID v4 (crypto.randomUUID, else getRandomValues), localStorage 'duq.learner_id'; progress 'duq.progress.v1' =
                {L1: {passed, predictionCorrect, attempts, ts}}; every storage access in try/catch, with an in-memory fallback. No names or emails, ever.
formulas.ts     the ONLY closed forms in this folder (LEVELS overlays): poisson(n, α²) for the L1 histogram, plus re-exports of P1 helpers when present
levels/L1.ts … L8.ts, levels/index.ts (LEVELS: LevelSpec[])
presets/*.json, presets/index.ts   nearestPreset(levelId, params): the entry minimising Σ((pᵢ − qᵢ)/rangeᵢ)²
data/records.ts the Lab bundle via import.meta.glob('../../data/{live,mock}/*.json', {eager: true, import: 'default'}): live > mock > preset; a missing dir gives {}
ui/             conceptCard (audio slot), predictPanel, controls, plot.ts (the ONLY Plotly import; vi.mock it), wignerCanvas.ts, histogram,
                parityMeter, checkBanner, ahaCard, codeToggle, hintLadder, progressMap, sourceBadge
index.ts        mountAcademy(root, {levelId?, apiBase?}) → {navigate(levelId), dispose()}; LEVELS; events; controller; getLearnerId
```

**What you call:**

| From | Calls |
|---|---|
| P1 | `runInWorker(req)` and `simulate(req)` (SimRequest/SimResult per P1 §4, which adds `nSteps?` and `meta.engine:'ts-cn'`); `wigner(rho, x, y)`; `linresp.{response, snr, leakageProxy, optimalPulse}`; `C.{G2, KAPPA_B, KAPPA_A, KAPPA_2, ALPHA, EPS_D}` |
| P3 | `mountBlocks(el, {modes:'two'}) → {getTree(), onChange(cb), loadPreset(name)}`; `expr.validate(tree, 'two')`, `expr.toPython(tree)`; `wrongBuilds.detect(tree) → {key, misconception?, message}[]`, with keys `drive_on_memory_not_buffer`, `no_dissipation`, `wrong_conversion`, `missing_hc` |
| HTTP | `/api/health` (once at mount, 3 s); `/api/sim/expr` (L6); `POST /api/leaderboard` (L8). Base = `import.meta.env.VITE_API_BASE`. Unset means offline mode: never fetch. |

**Fallback chain** (CONTRACT §3). A `sourceBadge` (`role="status"`, `aria-live="polite"`) always names the active source: "In-browser sim · validated vs dynamiqs" / "Live · Vultr dynamiqs" / "Precomputed" / "Verified records" / "MOCK".
- **`ts` levels (L1–L4):**
  1. `runInWorker`. If it rejects, or nothing arrives within 5 s, go to step 2.
  2. The nearest preset, with a banner.
- **`server-expr` (L6):**
  1. Validate with P3. Never send an invalid or non-Hermitian tree; show its feedback instead.
  2. **Match a precomputed build first**, for an instant result:
     - `detect()` key `drive_on_memory_not_buffer` → `eps_z_drive_wrong`;
     - `no_dissipation` → `missing_kappa_b`;
     - `wrong_conversion` → `a_bd2_wrong`;
     - no keys, and `toPython(H)` equals the `h2ph_correct` build's → `correct`.
  3. Otherwise, when online, POST the **fixed live shape** `{H, jumps, params:{g2, eps_d, kappa_b, kappa_a, K?}, modes:'two', Na:16, Nb:5, init:'vacuum', t_end_us:2, n_t:201, outputs:['na','nb','top2_a','top_b']}`. Show a progress state and wait up to 15 s.
  4. Then the `correct` preset, with the banner "Live run unavailable: showing the reference build, not yours".
  5. Then P1's in-browser one-mode L4 curve, labelled "effective one-mode model".
- **Any other server sim:** a 3 s timeout, then the nearest preset, then in-browser.
- **`records` (L5, L7):** the Lab bundle (live, then mock), else the `L5`/`L7` preset.

**Presets:**
- Copy them from `server/precomputed/presets/` (P0), in the endpoint response shape, into `site/src/academy/presets/`.
- Keep one id map in `presets/index.ts` from P0's names (`correct`, `missing_kappa_b`, `eps_z_drive_wrong`, `a_bd2_wrong`, the one-mode `L1`–`L4` defaults plus 3 slider positions each, and the L7 ε grid) to level ids.
- Until P0 lands, hand-make minimal presets with `"source":"mock"`, shown with a MOCK badge.
  - The L6 `correct` mock may reuse the Lab's `inflation.json` (t1_1 two-mode data), labelled with its source.
- Keep the total under 2 MB, with Wigner frames ≤ 61×61 at 4 decimals: it is bundled into the single-file build.

## 5. Tests to write FIRST (TDD)
- **Location:** `site/src/academy/__tests__/`, using vitest. Add `// @vitest-environment jsdom` per UI file, and `vi.mock('../ui/plot', () => ({ plot: vi.fn(async () => {}) }))`.
- **Fixtures:** read `docs/product/LEVELS.md` with `import md from '../../../../docs/product/LEVELS.md?raw'`. Use small hand-made SimResult-shaped fixtures, so no test depends on P1 being merged. Write them all, see them fail, then commit `[p2-academy] tests first`.
1. **`checks.test.ts`.** Each level's `check.fn` at its **exact LEVELS windows**: inclusive edges pass; ±0.001 outside fails.
   - **L1:**
     - Pass: coherent, |α| ∈ [2.08, 2.12] (2.08, 2.1 and 2.12 pass; 2.079 and 2.121 fail).
     - Fock state: fails, with a message.
   - **L2:**
     - Pass: κ ∈ [1.32, 1.46] rad/µs (1.386 passes; 1.319 and 1.461 fail).
   - **L3:**
     - Pass: the plateau = n(t_end) ∈ [0.43, 0.47].
   - **L4:**
     - Pass: loss off, n at the save nearest t = 1 µs ∈ [4.3, 4.5], **and** parity(1 µs) > 0.9 (strict: 0.9 fails).
     - Loss on: fails.
     - Part 2: the follow-up answer "the fringes and the parity" is accepted.
   - **L5:**
     - Pass: T_X = 1/Γ_X > 1000 µs and T_Z = 1/Γ_Z > 1 µs at the chosen α².
     - Interpolate Γ log-linearly between record points, and never extrapolate; outside the record range, fail with "no verified data here".
     - Fixture records: α² = 8.5 passes T_Z, and α² = 8.6 fails it (the 8.56 bound).
   - **L6:**
     - Pass: steady ⟨n_a⟩ = the mean over the last 0.5 µs, with |n_ss/4.41 − 1| ≤ 0.02 (4.3218 and 4.4982 pass; 4.32 and 4.50 fail), **and** `detect()` returns no keys.
   - **L7:**
     - Pass: `tradeoff` `snr_T1us` at the chosen ε (α = 2.1) ≥ 1 (1.0 passes; 0.99 fails).
   - **L8:**
     - Pass: `snr(yours) > snr(square)` (strict) and `cost(yours) ≤ cost(square)`, where cost = `linresp.leakageProxy`.
     - The square itself fails.
2. **`engine.test.ts`:**
   - **The predict gate:** `canRun()` is false and the Run button is `disabled` + `aria-disabled="true"` until a choice is made.
   - **Misconception recording:** a wrong option records its misconception ID and emits `prediction`. L2 B gives `misconceptionId: 'M3'`; L1 C has no M-id, but its `optionId` is still recorded.
   - **First choice only:** only the first choice counts as the prediction.
   - **Checks:** `check` is emitted on every attempt; `pass` is emitted and progress saved on a pass.
   - **Hints:** they go 1→4 and emit `hint`. The **full solution stays hidden until 2 failed checks**.
3. **`sources.test.ts`** (fake timers, mocked `fetch`):
   - **Hung server:** a fetch that never resolves gives the preset after 3000 ms, with badge "Precomputed" and a banner.
   - **L6 slow path:** L6 waits up to 15 000 ms and calls `onProgress`, then falls back to the `correct` preset with the "not yours" banner.
   - **Offline:** a rejected fetch goes straight to the preset. No `VITE_API_BASE` means no fetch at all.
   - **Known wrong builds:** each detector key maps to its precomputed build **without** a fetch.
   - **Last resort:** with no preset, the in-browser fallback is labelled.
   - **Worker failure:** the `ts` engine falls back to the preset.
4. **`progress.test.ts`:**
   - `getLearnerId()` matches `/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/` and is stable across re-import.
   - Progress persists.
   - A localStorage that throws gives an in-memory fallback, with no throw.
5. **`content.test.ts`.** For every level:
   - **Verbatim match with the parsed LEVELS.md:** the title; the predict question; each option's text; the misconception IDs; the check goal; the 4 hints; the aha; the allowed constants (equal sets); the preset id; the sources.
   - **Structure:** ≤ 3 visible controls; exactly one correct option; IDs ⊂ M1–M7.
   - **Presets:** a preset file exists, and all presets together are < 2 MB.
6. **`ui.test.ts`** (jsdom; mount every level):
   - No throw.
   - Every `input/select/button` has an accessible name.
   - The options form a `radiogroup` that ArrowDown moves through.
   - The check banner is `aria-live`.
   - The canvas code tolerates `getContext()` returning null (jsdom).
7. **`colormap.test.ts`:** the diverging map is a pure function. −M is the blue end (#2166ac), 0 is #f7f7f7, +M is the red end (#b2182b), and values outside are clamped. M = 2/π (|W| ≤ 2/π in dynamiqs' g = 2 convention).
8. **`l8.test.ts`** (`it.skipIf` when the P1 adapter is absent):
   - `linresp.optimalPulse(20, 1)`, scaled to the square's cost, beats the square.
   - An over-budget pulse fails.
   - "Fit to budget" rescales to cost(square) within 1e-9.

## 6. Method, step by step
1. **(10 min) Setup.** Branch and status (State `IN_PROGRESS`, Branch `prod/p2-academy`), tooling and the lane-local configs (§9).
2. **(35 min) Core and tests.** Write the §5 tests, then `types`, `events`, `progress`, `engine` and `controller`. Commit.
3. **(30 min) `levels/L1…L8.ts`, from LEVELS.md verbatim.**
   - **Missing feedback:** where LEVELS gives no feedback for an option, use that misconception's one-line fix from the library table. With no M-id, use a neutral line ("Not quite: run it and watch."). List every authored string in the status file.
   - **L7 interpretation:** LEVELS tags M6 on the *correct* option. Attach `M6` to option A ("Settles smoothly", the instant-readout belief), and note this in status.
   - **Sim requests**, per level (all on N = 30 unless P1 says N = 24 for L4):

| Level | Request | Notes |
|---|---|---|
| L1 | `tEndUs:0, nT:1, outputs ['n','wigner']`; `coherent(α)` or `fock(n)` | Histogram from `formulas.poisson` (Fock: a single bar) |
| L2 | H = ExprTree `mul[num Δ, sym n_a]` with Δ = 2π·1 rad/µs if Rotate is on, else 0; jumps `[mul[sqrt(num κ), sym a]]`; coherent 2; `tEndUs:1, nT:201`; Wigner every 0.1 µs | κ slider range 0–2π·1 MHz, labelled in rad/µs **and** MHz; the dashed 4e^{−κt} overlay via P1's `C`/formulas |
| L3 | H `num 0`; jumps `[mul[sqrt(num κ₂·s), pow(sym a, 2)]]`, s ∈ {¼, 1, 4}; coherent(Start α); `tEndUs:3, nT:301` | Parity meter. Final Fock histogram: P1 exports no populations, so show P(0) = 1 − n_∞ and P(1) = n_∞ (only \|0⟩ and \|1⟩ survive, by parity) when the last 10% of n(t) varies < 1e-3; otherwise show "still settling". Request P1 add `finalPops` in status. |
| L4 | Built-in model: α slider, κ₂ = `C.KAPPA_2`, κ_a = loss ? 20·`C.KAPPA_A` : 0, vacuum; `tEndUs:2, nT:201`; Wigner at 0, 0.1, …, 2 µs | The 50/50-mixture toggle appears only after hint 3: ½(W of \|α⟩ + W of \|−α⟩) through `wigner` |

4. **(60 min) UI, then L1–L4 on the TS solver. These must be playable by 2:15 AM.**
   - **Concept card:** the text, plus an audio button for `narrationKey` → `${import.meta.env.BASE_URL}audio/<key>.mp3`. Hide the button on load error, which covers offline and `file://`.
   - **Controls:** 1–3 word labels, units shown (µs, rad/µs), obvious ▶/⏸.
   - **Debouncing:** sliders debounce at ~100 ms. Keep **one sim in flight**: coalesce to the latest request and drop stale results by sequence id. Show a busy shimmer while computing.
   - **Plots:** line plots go through `ui/plot.ts` (Plotly, for Lab consistency) with the Okabe–Ito palette and CSS variables (`--bg --fg --muted --accent --ok --warn`, with fallbacks).
   - **Wigner:** draw it on a raw `<canvas>` with **ImageData** (~60 fps), not Plotly heatmaps (10–20 fps).
     - Keep a fixed diverging scale ±2/π for every frame.
     - Paint 61×61 to an offscreen canvas, then `drawImage` it scaled.
     - Label the axes "Re α" and "Im α", with row = Im α (`w[iy*nx+ix]`).
     - Give the canvas `role="img"` and an `aria-label` with its min W and peak positions.
     - Respect `prefers-reduced-motion`: no autoplay.
   - **Progress map:** 8 nodes, all reachable (never locked, so judges can jump around), with ✓ on the ones passed.
   - **Styles:** scope all CSS under `.academy`.
5. **(45 min) Sources, presets and L5–L7.**
   - **L5:**
     - Read `errors.json` (`gamma_x.one_mode|two_mode`, `gamma_z.td|pred`). Plot log T_X and T_Z against α², with record-id chips; the Model toggle switches between one-mode and two-mode.
     - Add the bias meter, a static double-well SVG, and the Wigner of `cat_plus` at the chosen α (P1 `simulate` with `tEndUs:0`).
   - **L6:**
     - `mountBlocks`; ▶ "Run on Vultr"; n_a(t) and n_b(t) with the L4 curve overlaid.
     - A **truncation meter**: `top2_a`/`top_b` against 1e-4, comparing the 16×5 live shape with P0's 32×12 reference (6.89 vs 6.11 peak).
     - `detect()` messages go in the feedback card.
   - **L7:**
     - Read `readout.json` `signals_by_eps`/`signals` + `tradeoff` (else the `L7` preset). The ε_Z control snaps to the grid {0.05, 0.1, 0.2, 0.5, 1, 2, 3} g₂.
     - Show the IQ trajectories of ⟨b⟩ for both valleys, and Re/Im against t with the analytic ringing overlaid from `linresp.response`.
     - Add an SNR meter and a cost meter.
6. **(25 min) L8:**
   - A **pulse editor** of 20 draggable bars over 1 µs (pointer **and** keyboard: arrows move a bar's value, Tab moves between bars). Add a spectrum (DFT of the bars, with 3.14 MHz marked), the signal |Δb|(t), and SNR against budget.
   - **Scoring:** use `linresp.response` (both wells; Δb = 2b₊) with `samplesPerBin` ≥ 10, `snr` and `leakageProxy`.
   - **Square reference:** `readout.json` `pulses.square` if present (re-binned to 20 by mean); otherwise a flat ε = 0.5·`C.G2`. Record which in status. "Fit to budget" rescales the bars to cost(square).
   - **Aha:** compare against `optimalPulse(20, 1)` at equal cost, and against `pulses.svd` if present.
   - **Leaderboard:** online, `POST /api/leaderboard {challenge:'readout_pulse', learner_id, alias, score, payload:{eps_bins, T_us:1, n_bins:20}}` (3 s; the server recomputes). Otherwise label it "local score (unverified)".
   - **On pass:** emit `pass`, show a `<div data-slot="credential">` for P6, and add an "Unlock Real Research" link to `#/inflate`.
7. **(15 min) Accessibility and offline pass:**
   - Keyboard through a whole level, visible focus rings, color never the only carrier.
   - At 375 px, `document.documentElement.scrollWidth ≤ 375`.
   - L1–L5 work with DevTools set to Offline and no `VITE_API_BASE`.
8. **(10 min) Status and commit.** Fill in the status file (§12) and commit `[p2-academy] …`, staging explicit paths only. When P1/P3 land on `standard-track`, run `git merge standard-track` and re-run everything against the real modules.

## 7. Outputs
- **Code and data, no physics records:** code under `site/src/academy/`; presets `site/src/academy/presets/*.json` (mock-labelled until P0's are copied in); and the dev entry.
- **Status file contents:**
  - **For P7:**
    - The routes needed: `#/learn` (the map) and `#/learn/L1` … `#/learn/L8`, all through `mountAcademy`.
    - The deps: `plotly.js-dist-min` (already l6's), plus `jsdom` and `vitest` as devDependencies.
    - Where the tutor (P4) and credential (P6) slots are.
  - **For the CONTRACT:** the additive LevelSpec extras and the authored feedback strings.
  - **Records:** which data files are live vs mock.

## 8. Acceptance gates (ALL must pass before DONE)
1. Every §5 test passes (`l8` runs once P1 has merged). `npx tsc -p src/academy/tsconfig.json` reports 0 errors.
2. **L1–L5 are playable offline in the dev entry** (DevTools Offline, no `VITE_API_BASE`): predict → play → check → aha → "Show the code", for each level.
3. **L6–L8 are playable with presets**, showing the correct badge and banner.
4. **The predict gate holds:** Run is disabled before a choice. A wrong choice emits `prediction` with its M-id (seen in a test and by hand).
5. **The fallback chain and badge work** (`sources.test.ts`), and a known wrong build shows its precomputed run instantly.
6. **The Wigner canvas holds ≥ 30 fps** during the L4 animation (measure frame times with `performance.now()` and log them in the status file).
7. **Accessibility:** at 375 px there is no horizontal scroll, the keyboard path works, and every control has an accessible name.
8. **No physics model in this folder:** no Lindblad/ODE code under `site/src/academy`. The only closed forms are in `formulas.ts`.
9. **Diff:** `git diff --name-only standard-track...HEAD` lists only `site/src/academy/**` (no `routes.ts`) and the status file.

## 9. Commands
```powershell
git switch -c prod/p2-academy standard-track
Test-Path docs/product/CONTRACT.md      # must be True; otherwise ask the integrator to merge product-academy first
New-Item -ItemType Directory -Force docs/product/status | Out-Null
Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p2-academy.md   # set Branch = prod/p2-academy
# Tooling. site/package.json belongs to l6 (then P7): never create or edit it.
if (Test-Path site/package.json) { npm --prefix site install }              # l6 merged: use its toolchain
# Otherwise (or if anything is missing): ONE no-save install into the git-ignored site/node_modules.
# npm prunes extraneous packages on every install, so list everything at once. Add blockly@13.4.0 too once you mount P3's blocks.
npm --prefix site install --no-save --no-package-lock vitest@3 vite@7 jsdom@26 typescript@5 plotly.js-dist-min
git status --porcelain -- site     # only site/src/academy/** may appear; Remove-Item any untracked site/package.json or lockfile npm created
Push-Location site
npx vitest run --config src/academy/vitest.config.mts               # all academy tests
npx tsc -p src/academy/tsconfig.json
$env:VITE_API_BASE = "http://localhost:8000"                         # optional: P0 running locally; omit it to test offline mode
npx vite src/academy --port 5174                                     # then open http://localhost:5174/dev.html#L1
Pop-Location
Copy-Item server/precomputed/presets/*.json site/src/academy/presets/   # after P0 merges (git merge standard-track first)
git diff --name-only standard-track...HEAD
```
**Lane-local files.** They are in your folder, and all caches land in the ignored `site/node_modules`.
- `site/src/academy/vite.config.mts`. Its `root` is this folder; serve `dev.html`:
  ```ts
  export default { cacheDir: '../../node_modules/.vite-academy', server: { fs: { allow: ['../..'] } } };
  ```
- `site/src/academy/vitest.config.mts`:
  ```ts
  export default { test: { include: ['src/academy/**/*.test.ts'], environment: 'node' } };
  ```
  Run it from `site/`. UI files opt into jsdom per file.
- `site/src/academy/tsconfig.json`: strict; `lib ["ES2022","DOM"]`; `types ["vite/client"]`; `moduleResolution "Bundler"`; `resolveJsonModule`; `noEmit`.
- `npx vite src/academy`, run from `site/`, is the same as `npx vite site/src/academy` from the repo root. Running it from `site/` uses the vite in `site/node_modules` instead of downloading a second copy.
- After l6 merges, `cd site; npm test` picks up `src/academy/__tests__` too. P7 does the final route wiring in `routes.ts`.

## 10. Out of scope / do not
- **Not yours:** `routes.ts`, `main.ts`, `index.html` or `package.json` (all P7); the tutor UI or Gemini/Backboard/ElevenLabs calls (P4 subscribes to your events and the controller); progress or run POSTs (P5 subscribes); chain or wallet UI (P6).
- **No physics:** no ODE/Lindblad code, no two-mode sim in the browser, and no invented numbers in copy. Use only the LEVELS text and allowed constants, because the tutor's number guard relies on them.
- **No accounts, PII, analytics or external fonts/CDNs.** No React/Vue framework (vanilla TS like the Lab).
- **Never block on the network:** every fetch has a timeout, and every network feature has a labelled fallback.

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
**Wording**, in the status file (then continue with whatever is unblocked):
```
DECISION NEEDED (p2-academy, HH:MM): <one line>. Seen: <facts>. Options: (a) … (b) …
My default if no answer by HH:MM+30: (a).
```
**Fallbacks:**
- **P1 not merged:** code against the CONTRACT §5 types, with the stub that plays presets, and keep going. Merge `standard-track` when P1 lands.
- **P3 not merged:** L6 shows the 4 precomputed builds as buttons (correct + 3 wrong), plus `codeFallback`.
- **l6 not merged:** keep the dev entry.
- **P0's presets are absent:** use mock presets, visibly labelled.
- **P0's preset shape or names differ:** adapt `presets/index.ts`, and don't ask P0 to change.
- **The 16×5 `correct` build misses L6's 2% window:** DECISION NEEDED (options: check against P0's 32×12 reference, or widen nothing and say so). Never edit the LEVELS windows.
- **The L8 cost definition (leakage proxy vs energy):** default to `leakageProxy`; record it.

**Cut line**, in PLAN §3 order, if behind at 3:15 AM:
1. The L4 mixture toggle.
2. The audio slot (narration).
3. The L8 leaderboard POST (keep the local score "unverified").
4. The L7 IQ plot (keep Re/Im).
5. The L5 Wigner at α.
6. All of L8 (PLAN cut 8: Real Research shows our optimal pulse).

**Never cut:** the predict gate, the checks, L1–L5 offline, the presets plus badge fallback, the events, progress, or the controller API.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer — questions only)
**Status file at DONE:**
- State `DONE`, branch, last commit, and the tool versions.
- The gate table with evidence: the test count and runtime, and the fps measurement.
- Which levels run on which source (live, preset, mock, records), the preset id map, and the authored feedback strings.
- The L7 M6 mapping and the L8 square and cost choices.
- The routes, deps and slots for P7.
- The event payloads and controller API for P4/P5.
- Open DECISION NEEDED items.

**Explain-back questions** (Harshit answers them himself; don't write answers):
1. In L4 the learner always grows the *even* cat from the empty box. What conservation law guarantees that, and which two things on screen prove it (the parity meter and W at the origin)? Why does photon loss kill the fringes first, as a phase flip and not a bit flip?
2. Why does L6 run on precomputed builds and a fixed 16×5 live shape instead of live two-mode simulation? Walk through the fallback chain: what does each badge state certify about where the number came from?
3. In L8, why can a shaped pulse beat a square pulse at equal leakage cost? Why is it legitimate to score with the 2×2 linear-response model in the browser, when the leaderboard recomputes the score on the server?
