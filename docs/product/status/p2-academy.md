# Status: lane `p2-academy`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p2-academy` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 00:27 |
| Last update (EDT) | 2026-10-25 00:58 |
| Last commit | see git log after this commit |

## Milestones
- [x] Read brief, CONTRACT, LEVELS, PLAN
- [x] Tests written (checks, engine, sources, progress, content, ui, colormap, l8)
- [x] Implementation complete for L1–L8
- [x] Vitest suite green
- [x] `tsc -p src/academy/tsconfig.json` clean
- [x] Dev entry played in the browser, offline (no `VITE_API_BASE`)
- [x] Explain-back questions drafted

## Acceptance gates
| Gate | Result | Evidence |
|---|---|---|
| 1. Tests + tsc | pass, with the two linresp cases skipped | `npx vitest run --config src/academy/vitest.config.mts` → 8 files, **32 passed, 2 skipped**, 1.44s. `npx tsc -p src/academy/tsconfig.json` → exit 0. TypeScript 5.9.3, Node v24.18.0, Vitest 3.2.7. |
| 2. L1–L5 offline | pass on mock presets | Dev server `npx vite src/academy --port 5174` with no `VITE_API_BASE`. Browser: predict → run → check → aha for L1–L5. Badges `MOCK`. L1–L4 banner: "In-browser sim unavailable: showing a precomputed preset." |
| 3. L6–L8 presets | pass | L6 correct build: badge `MOCK`, banner "Demo build: precomputed, not a live Vultr run.", check "Steady ⟨n_a⟩ is within 2% of 4.41". L7 ε=1: SNR 3.816, badge `MOCK`. L8 shaped pulse: badge `MOCK`, banner "Local score (unverified)…", check passes, credential slot and `#/inflate` link appear. |
| 4. Predict gate | pass | L1 Run starts `disabled` and `aria-disabled="true"` until option B. Engine test records L2 B as `M3` and L1 C with no misconception id. |
| 5. Fallback chain | pass | `sources.test.ts`: hung fetch → preset after 3s with badge `Precomputed`; L6 waits 15s then `correct` with the "not yours" banner; rejected fetch and missing `VITE_API_BASE` do not hang; the three wrong-build keys skip fetch; worker rejection uses a preset; empty catalog is labelled in-browser. |
| 6. Wigner fps | pass | `colormap.test.ts`: `fillRgba` on 61×61, 40 frames, mean **2.6866 ms (372 fps)**. L4 playback is paced at 30 fps. `prefers-reduced-motion` does not autoplay. |
| 7. Accessibility | pass | jsdom mounts all 8 levels: every input/select/button has a name, ArrowDown moves the radiogroup, check banner is `aria-live`. At 375×812, `documentElement.scrollWidth` was 375 on L1, L4 and L8. |
| 8. No Lindblad in this folder | pass | Closed forms are `poisson`, `coherentDecay`, `dftMagnitude`, `energyCost`, `fitToBudget` in `formulas.ts`. `WIGNER_M = 2/π` is the brief's colormap scale, not a rate. `mesolve` appears only inside the LEVELS show-code strings. |
| 9. Diff vs `standard-track` | concern | This branch was created from `product-academy-build`, which is not in `standard-track`. `git diff --name-only standard-track...HEAD` therefore includes `docs/product/**` and `docs/superpowers/**` from that base. Files added by this lane are only `site/src/academy/**` and `docs/product/status/p2-academy.md`. |

## Commands run
```text
npx vitest run --config src/academy/vitest.config.mts
8 files, 32 passed | 2 skipped, 1.44s
wigner fillRgba mean 2.6866 ms (372 fps)

npx tsc -p src/academy/tsconfig.json
exit 0

npx vite src/academy --port 5174
browser play of L1–L8 (see gates)
```

## What runs on which source
| Level | This branch | When P1 / P0 / the lab bundle arrive |
|---|---|---|
| L1–L4 | `ts` worker throws (P1 absent) → nearest mock preset, badge MOCK | `runInWorker`, badge "In-browser sim · validated vs dynamiqs" |
| L5 | mock `recordsByModel` in `presets/L5.json`, badge MOCK | `errors.json` live, then mock, else this preset. No extrapolation. |
| L6 | four mock builds, badge MOCK. Unmatched trees that time out use the "not yours" banner. | POST `/api/sim/expr` at Na=16, Nb=5, then `correct` |
| L7 | tradeoff and decimated traces copied from the lab mock `readout.json` (α=2.1), badge MOCK | live/mock `readout.json`, else this preset. ε snaps to {0.05, 0.1, 0.2, 0.5, 1, 2, 3} |
| L8 | demo score, badge MOCK, "local score (unverified)" | `linresp.snr` + `leakageProxy` |

Preset id → level (from the catalog): `L1`/`L1_alpha_*`/`L1_fock` → L1; `L2`/`L2_k*` → L2; `L3`/`L3_a*` → L3; `L4`/`L4_a*`/`L4_loss` → L4; `L5` → L5; `L6` and `correct`, `missing_kappa_b`, `eps_z_drive_wrong`, `a_bd2_wrong` → L6; `L7`/`L7_eps_*` → L7; `L8` → L8.

Bundle size of `presets/*.json`: about 35 KB.

## L7 M6 and L8 square / cost
- LEVELS puts `(M6)` on option A, "Settles smoothly", not on the correct option. The spec does the same. The explicit feedback on A is kept: "It actually rings for about 1 µs. Reading takes time."
- `readout.json` `pulses.square` is not on this branch. The square is a flat **0.5·g₂** (20 bins, amplitude 2.397 from `src/config.py`'s G2). SNR **0.95** is the CONTRACT §6 prototype and is labelled unverified. Do not quote 4.06.
- Cost is `linresp.leakageProxy` when P1 is present. Until then, cost is ∫ε² dt, and "Fit to budget" rescales with that quadratic stand-in (tested to 1e-9).

## For P7
- Routes, all through `mountAcademy`: `#/learn` (same shell, defaults to L1) and `#/learn/L1` … `#/learn/L8`. Dev entry: `site/src/academy/dev.html` via `npx vite src/academy --port 5174`. Do not add `routes.ts` here.
- Deps to add when l6's `package.json` is yours: `plotly.js-dist-min` (already l6's), devDependencies `vitest`, `jsdom`, `typescript`, `vite`. No Blockly in this lane.
- Tutor slot: `[data-slot="tutor"]` on every level. Credential slot: `[data-slot="credential"]`, shown after an L8 pass, plus an "Unlock Real Research" link to `#/inflate`.
- Narration: `${BASE_URL}audio/L1.mp3` … `L8.mp3`. The button removes itself if the file 404s.

## For the CONTRACT (additive)
`LevelSpec` already has `allowedConstants`, `predictFollowUp`, and `checkParts`. This lane also sets `codeFallback: string` and `checkFollowUp` (L4 part 2; `checkParts[0]` calls the same function). `Control` may carry `initial`, `revealAtHint`, `visibleWhen`, `visibleValue`, `snap`.

### Authored feedback (not taken verbatim from an option line)
- Correct options, when LEVELS gives no line: "That's the one."
- Wrong options with no misconception and no Feedback line: "Not quite: run it and watch."
- Misconception fixes, used when LEVELS gives an id and no Feedback line: the one-line fixes in the LEVELS library table (M1–M7).
- Explicit LEVELS feedback kept as written: L1 A and L1 C; L7 A and L7 C.
- L4 follow-up "the fringes and the parity": "The stripes and the parity go first. The blobs stay: a phase flip, not a bit flip." The other follow-up option uses the M5 fix.
- L5 follow-up "more common" uses "That's the one." The other option uses the M4 fix.

## For P4 / P5
Events: `prediction {levelId, optionId, correct, misconceptionId?, firstTry}`, `check {levelId, pass, attempt, message}`, `pass {levelId, attempts, predictionCorrect}`, `hint {levelId, hintLevel}`, `sim {levelId, source, params, summary}`.

`getLevelState()` → `{levelId, params, prediction?, misconceptionIds, lastSim:{summary}, hintLevel}`. Also `setParam`, `runSim`, `showHint`, `nextLevel`. Learner id is `duq.learner_id` (UUID v4). Progress is `duq.progress.v1` in localStorage, memory if storage throws. No names or emails.

## Records
No new physics records. L5/L7 numbers on this branch are mock. L7's SNR grid and ⟨b⟩ traces are a decimation of the lab mock `readout.json` (ids already marked `mock.t2_*`). The L6 curve is a hand-made mock (tail mean 4.440, peak 6.33) labelled MOCK; 6.89 and 6.11 are the documented references, not a new measurement.

## P1 request
L3's histogram wants `finalPops`. Until that exists, a settled trace shows P(0)=1−⟨n⟩∞ and P(1)=⟨n⟩∞, otherwise "still settling".

## Deviations
- Worktree base is `product-academy-build`, as instructed, not `standard-track`. See gate 9.
- L4's 50/50 mixture is a stored schematic frame (`mixtureW`), revealed at hint 3. It is not a second Wigner solve.
- `2/π` appears once, as the Wigner color scale required by the brief.

## DECISION NEEDED
None blocking. Default already taken: L8 cost is `leakageProxy` when P1 exists, energy only as the labelled demo stand-in. L6's 2% window was not widened; the mock correct build sits inside it.

## Explain-back for Harshit (questions only)
1. In L4 the learner always grows the even cat from the empty box. What conservation law guarantees that, and which two things on screen prove it (the parity meter and W at the origin)? Why does photon loss kill the fringes first, as a phase flip and not a bit flip?
2. Why does L6 run on precomputed builds and a fixed 16×5 live shape instead of live two-mode simulation? Walk through the fallback chain: what does each badge state certify about where the number came from?
3. In L8, why can a shaped pulse beat a square pulse at equal leakage cost? Why is it legitimate to score with the 2×2 linear-response model in the browser, when the leaderboard recomputes the score on the server?

## Notes for Claude's later review
- Do not treat the mock L5 grid or the L8 prototype SNR 0.95 as verified records.
- The 16×5 mock peak is 6.33, not the 6.89 reference. The truncation card says so.
- `l8.test.ts` skips the two `linresp` cases until `site/src/sim` exports `optimalPulse`, `response`, `snr`, and `leakageProxy`.
