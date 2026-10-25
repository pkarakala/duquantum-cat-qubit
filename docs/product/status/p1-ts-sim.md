# Status: lane `p1-ts-sim`

| Field | Value |
|---|---|
| State | `DONE` |
| Branch | `prod/p1-ts-sim` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 00:27 |
| Last update (EDT) | 2026-10-25 00:58 |
| Last commit | filled after the solver commit |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH
- [x] Tests written first (list the test names)
- [x] Implementation complete
- [x] `--quick` run passes (≤ 2 min) — vitest suite, 10 s
- [x] Production run(s) done, or queued (see Jobs to queue) — the solver tests are the production check; nothing is queued
- [x] All acceptance gates in brief §8 checked, with evidence below
- [x] Explain-back questions drafted

## Acceptance gates (copy from brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| All §5 tests pass. linresp parity passes or is skipped pending P0 | pass | `npx -y vitest@2 run --config site/src/sim/vitest.config.ts` → 4 files, 27 tests passed. `linresp_parity` and `wigner_fixture_parity` skip with a message because `server/tests/fixtures/{linresp,wigner}` are not in the tree yet |
| N = 30, 2 µs, 400 steps under 300 ms, off the main thread | pass | direct `200.2 ms`, worker `235.2 ms` (`perf_n30`). Both under 300 ms |
| Wigner convention documented and matches dynamiqs | pass | `g = 2`, `x = Re α`, vacuum `W(0,0) = 2/π` to `1e-9`, coherent peak at `x = 2`. See `site/src/sim/README.md` |
| No 2π outside `config.ts`. No dependency beyond vitest | pass | `2 * Math.PI` appears only in `site/src/sim/config.ts`. Tests import no package except vitest |

## Commands run (most recent first)
```text
npx -y vitest@2 run --config site/src/sim/vitest.config.ts
 Test Files  4 passed (4)
      Tests  27 passed (27)
 Duration  10.10s

1.0c scale 0.25 final n 4.387166479658741 target 4.387166478874212 rel 1.79e-10
1.0c scale 1    final n 4.403969346893351 target 4.403969346892005 rel 3.06e-13
1.0c scale 4    final n 4.408144076216637 target 4.408144076214539 rel 4.76e-13
L4 interactive n 4.4087 parity 1.0000 wall 171.8 ms
CN steady |Δn| 3.22e-15; 400-vs-4000 transient max |Δn| 2.95e-3
perf N=30 400 steps direct 200.2 ms, worker 235.2 ms
L8 square SNR 0.954082 optimal SNR 4.029948 unit-energy gain 0.701376
SKIP linresp_parity: server/tests/fixtures/linresp/*.json not present yet (P0)
SKIP wigner_fixture_parity: server/tests/fixtures/wigner/*.json not present yet (P0)
```

## Test list
Banded LU (random non-diagonally-dominant band vs dense GEPP; diagonal system). Wigner vacuum analytic, coherent peak and analytic blob, cat min W < −0.2, mixture has no fringes, fixture parity skipped. Linresp poles −4.08 ± 19.72i, DC gain and memory shift, linearity and the ODE, level-8 optimal beats the square, fixture parity skipped. Physics: master equation vs superoperator, non-Hermitian ExprTree rejected, L1 coherent ⟨n⟩ = 4.41 and Fock, 1.0a decay, L2 half-life and rotation, 1.0b plateau / parity / pops / trace / hermiticity, L3 plateau window at three κ₂, 1.0c three finals, L4 cat at 400 steps plus exaggerated loss, drive quadratures and the Re⟨a⟩ = 0 symmetry, trace on a thermal driven run, CN steady vs transient, ExprTree drive matches `epsZ`, worker matches `simulate`, N = 30 performance.

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|
| (solver, not a physics record) | 1.0c finals 4.38716648, 4.40396935, 4.40814408 | photons | N = 30 as in Task 1.0 | vs `results/task_1_0.json`, rel 1.8e-10 / 3e-13 / 5e-13, tol 1e-3, agree |
| L8 square / optimal SNR | 0.954082 / 4.029948 | dimensionless | nominal g₂, κ_b, α, T = 1 µs, 20 bins, budget 0.25 g₂² µs | prototype 0.95 / 4.06 was the right scale; these are the values to quote |

## Figures / arrays produced
- None. The lane does not write `results/` or `figures/`.

## Jobs to queue (for the integrator; jobs > 15 min)
| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs (record ids) |
|---|---|---|---|---|
| none | | | | |

## Deviations from the brief (and why)
- `SimResult.finalPops` is always present. CONTRACT §5 includes it and the `final_pops` test needs it; the brief's export paste omitted the field.
- `response` accepts either a sample count or an explicit time array, so the P0 linresp fixtures can be checked on their own `t_us`.
- Crank–Nicolson uses partial pivoting on every factor. The two-photon matrix is not diagonally dominant (`dt · κ₂ N² ≫ 1`), which is the fallback the brief specifies. It is fast enough that the no-pivot path is unnecessary.
- Level-8 prototype SNR 0.95 / 4.06 verifies as **0.954082 / 4.029948** at the square's energy budget. Quote the verified pair.

## DECISION NEEDED
None.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why is Crank–Nicolson stable when RK4 needs tiny steps, and what does "stiff" mean here?
2. How do we know the browser solver agrees with dynamiqs?
3. What does the linear-response matrix R_b represent, and why is its top singular vector the best pulse?

## Notes for Claude's later review
- P7 devDependency: `vitest@2` (this lane ran `vitest@2.1.9` via `npx -y vitest@2`). No runtime dependency. Do not add anything else to `site/package.json` for this lane.
- Interactive accuracy to record next to the level checks: 400 CN steps over 2 µs, N = 20 cat inflation, max |Δ⟨n⟩| against 4000 steps is `2.95e-3`. The steady two-photon plateau matches to `3e-15`. N = 30 L4 at 400 steps and t = 1 µs gives ⟨n⟩ = 4.4087 and parity = 1.000, inside the level window, in 172 ms.
- Re-Hermitianize after every step. The full N² matrix is evolved; there is no ρ = ρ† shortcut.
- Wigner frames are 81×81 on [−4, 4]², row-major `W(x[ix], y[iy])`.
- `runInWorker` uses `node:worker_threads` and `worker-entry.ts` under Node (type stripping, Node 24), and `worker-browser.ts` when `window` is defined. Vite should bundle the browser worker; it should not try to bundle `node:worker_threads`.
- Fixture skips are the brief's cut, not a missing test. When P0 adds `server/tests/fixtures/linresp/{square,cosramp,clear}.json` and `server/tests/fixtures/wigner/{vacuum,coherent2,catplus2}.json`, the existing tests compare them to 1e-9 and 1e-5.
