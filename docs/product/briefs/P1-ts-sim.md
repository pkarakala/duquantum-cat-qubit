# Brief `p1-ts-sim`: in-browser Lindblad solver (Crank–Nicolson), Wigner, linear response

> **Paste into a new Cursor agent (worktree mode):** "You are product lane `p1-ts-sim`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P1-ts-sim.md`, then execute the brief exactly. Keep `docs/product/status/p1-ts-sim.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p1-ts-sim` | `prod/p1-ts-sim` from `standard-track` | none (pure TypeScript); the linresp parity fixtures come from P0 later | strongest | 2 h | 11:45 PM → 1:45 AM (P-G1) |

## 1. Goal and why
Levels 1–4 and 8 must react **instantly and offline**, so the one-mode physics runs in the browser.

Benchmarks on the target laptop (CONTRACT §5):
- **Explicit RK4 is too slow.** The problem is stiff: it is stable only for dt ≲ 2.8/(κ₂N²), and takes 1.5 s at N = 30.
- **Crank–Nicolson on the vectorized superoperator with a banded LU** takes 180 ms at N = 30 for 200 steps.
- The solver must reproduce our verified dynamiqs numbers. That is what lets the Academy say "learning sim, validated against dynamiqs".

## 2. Read first
- `docs/product/CONTRACT.md` §4 (ExprTree) and **§5** (the interface, the solver choice, the bug trap, golden values, linresp).
- `docs/plan/RESEARCH.md` §1 (parameters), §4.1 (drive quadratures) and §7 (linear response: poles −4.08 ± 19.72i /µs).
- Committed `results/task_1_0.json` (golden numbers) and `src/config.py` (constants to mirror).
- QuTiP's `wigner_clenshaw` algorithm, as a reference for the Wigner port.

## 3. Allowlist (touch nothing else)
`site/src/sim/**` (code, tests and a lane-local `vitest.config.ts` if needed) and `docs/product/status/p1-ts-sim.md`.

## 4. Interfaces you implement (`site/src/sim/index.ts` exports exactly these)
```ts
export interface OneModeParams { N: number; alpha: number; kappa2: number; kappaA: number; nTh?: number; epsZ?: number; epsX?: number; H?: ExprTree; jumps?: ExprTree[] }
export interface SimRequest { params: OneModeParams; init: { kind: 'vacuum'|'coherent'|'cat_plus'|'cat_minus'|'fock'; alpha?: number; n?: number }; tEndUs: number; nT: number; nSteps?: number; outputs: ('n'|'parity'|'re_a'|'wigner')[]; wignerTimes?: number[] }
export interface SimResult { tUs: Float64Array; n?: Float64Array; parity?: Float64Array; reA?: Float64Array; wigner?: { x: Float64Array; y: Float64Array; frames: { tUs: number; w: Float64Array }[] }; meta: { engine: 'ts-cn'; wallMs: number; nSteps: number } }
export function simulate(req: SimRequest): SimResult
export function runInWorker(req: SimRequest): Promise<SimResult>
export function wigner(rho: ComplexMatrix, x: Float64Array, y: Float64Array): Float64Array
export * as linresp from './linresp'
export * as C from './config'
```

**Files:**
- `config.ts`:
  - `G2 = 2π·0.763`, `KAPPA_B = 2π·2.6`, `KAPPA_A = 2π·9.3e-3`, `ALPHA = 2.1`, `KAPPA_2 = 4·G2²/KAPPA_B` (≈ 5.6276), `EPS_D = ALPHA²·G2`.
  - Units are rad/µs and µs. The 2π appears **only here**.
- `complex.ts`: interleaved re/im `Float64Array` dense matrices. matmul, adjoint, add, scale, trace, and a Hermitize helper (ρ ← (ρ + ρ†)/2).
- `ops.ts`:
  - `destroy(N)` (sparse: store the superdiagonal √k), number, parity (diag (−1)^n).
  - `coherent(N, α)`: Fock amplitudes via log-gamma, then normalized.
  - `cat(N, α, ±1)` and `fock(N, n)`.
- `superop.ts`: builds the **vectorized Lindbladian** L (column-stacking, D = N², sparse) for H and jumps.
  - L = −i(I⊗H − Hᵀ⊗I) + Σ [J*⊗J − ½ I⊗J†J − ½ (J†J)ᵀ⊗I].
  - Jumps for the standard model: √κ₂(a² − α²) and √κ_a·a (plus thermal).
  - H = ε_z(a + a†) + ε_x·i(a† − a).
  - `expr-eval.ts` turns a one-mode ExprTree (symbols a, ad, n_a, I) into H and the jumps.
- `cn.ts`: **Crank–Nicolson.** Solve (I − ½dt·L)ρ_{k+1} = (I + ½dt·L)ρ_k.
  - Order the vec index so L is **banded** (bandwidth about 2N + 2), then do a banded LU **once per (dt, L)** with no pivoting. Verify the diagonal dominance holds, and fall back to partial pivoting if it doesn't.
  - **Re-Hermitize ρ after every step** (the bug trap in CONTRACT §5).
- `wigner.ts`: the Clenshaw port, with position-independent coefficients precomputed.
  - **Document the axis convention** and make it match dynamiqs `dq.wigner`, i.e. the same (x, y) ↔ α scaling as `dq.wigner(xmax, ymax)`. Check this against a coherent state's peak position.
  - Use the dynamiqs convention (QuTiP `g = 2`): x = Re α, so vacuum gives **W(0,0) = 2/π** and |α=2⟩ peaks at x = 2. Verify against P0's `server/tests/fixtures/wigner/*.json` when it exists.
- `simulate.ts` + `worker.ts`: `runInWorker` posts to a dedicated worker. Transfer the typed arrays.
- `linresp.ts`, per CONTRACT §5:
  - `poles`.
  - `response(epsBins, edgesUs, g2, kappaB, alpha, well)`: exact 2×2 complex exponential per bin. M = [[0, −2i·s·g2·α], [−2i·s·g2·α, −κ_b/2]], u = [−i, 0].
  - `snr = κ_b∫|Δb|²dt`.
  - `leakageProxy = ∫|δa|²dt`.
  - `optimalPulse(nBins, T)`: power iteration on R_bᴴR_b, where R_b is built by unit-bin responses.

## 5. Tests to write FIRST (vitest)
| Test | Setup | Assertion |
|---|---|---|
| `plateau_1_0b` | H = 0, jump √κ₂·a², N = 30, coherent α₀ = 2, t = 3 µs | final ⟨n⟩ = **0.4998322686860546** (rel 1e-4) |
| `decay_1_0a` | Δ/2π = κ/2π = 1 MHz, coherent α = 2, t ∈ [0, 1] µs | ⟨n⟩ = 4e^{−κt} (abs 1e-4; use fine steps) |
| `final_n_1_0c` | κ₂/4, κ₂, 4κ₂ with κ_a on, from vacuum, 2 µs | **4.387, 4.404, 4.408** (rel 1e-3) |
| `trace_and_hermiticity` | any run | Tr ρ = 1 ± 1e-9; ‖ρ − ρ†‖ < 1e-12 |
| `parity_conserved` | pure two-photon loss | parity constant to 1e-9 |
| `wigner_vacuum` | vacuum | W(0,0) = 2/π (1e-9; dynamiqs convention) |
| `final_pops` | 1.0b run | `finalPops` has weight only on \|0⟩ and \|1⟩ (others < 1e-6) |
| `wigner_coherent_peak` | coherent α = 2 | the peak is at the documented location |
| `wigner_cat_negative` | C₊, α = 2 | min W < −0.1 |
| `drive_quadratures` | no dissipation, from vacuum, short t | eps_z only: Re⟨a⟩ ≈ 0, Im⟨a⟩ ≈ −εt. eps_x only: Re⟨a⟩ ≈ +εt (RESEARCH §4.1) |
| `cn_matches_reference` | N = 20, 200 steps vs 4000 steps | steady ⟨n⟩ matches to 1e-5; transient error at 400 steps reported |
| `linresp_poles` | nominal parameters | −4.08 ± 19.72i (rel 2e-3) |
| `linresp_parity` | `server/tests/fixtures/linresp/*.json` from P0 | matches to 1e-9. **Skip with a clear message** if the fixtures are absent |
| `perf_n30` | N = 30, 2 µs, 400 steps | log the wall time; assert < 600 ms on CI and report the actual |

## 6. Method
1. Run `git switch -c prod/p1-ts-sim`, create the status file and write the tests.
2. **Running tests when `site/package.json` belongs to the l6 lane:** use a lane-local `site/src/sim/vitest.config.ts` and run `npx -y vitest@2 run --config site/src/sim/vitest.config.ts`. List `vitest` as a needed devDependency in your status file for P7.
3. Implement in this order: complex, ops, superop, cn, simulate, wigner, worker, linresp.
4. **Profile at N = 30.** If CN takes over 300 ms for 400 steps:
   - exploit the band structure further, or reuse the LU across slider moves that don't change dt or L;
   - as a last resort, use N = 24 for L4, after checking that N = 24 vs 30 gives |Δ⟨n⟩| < 1e-3.
5. Document the interactive accuracy (400 steps) in the status file: the max transient ⟨n⟩ error against 4000 steps.

## 7. Outputs
- `site/src/sim/` with green tests.
- A short `site/src/sim/README.md` covering the API, accuracy, performance numbers and the Wigner convention.

## 8. Acceptance gates
- [ ] All tests in §5 pass. linresp parity passes or is skipped pending P0.
- [ ] N = 30, 2 µs runs in under 300 ms (or under 600 ms with a documented reason), off the main thread via the worker.
- [ ] The Wigner convention is documented and matches dynamiqs.
- [ ] No 2π outside `config.ts`. No dependency beyond vitest.

## 9. Commands
```powershell
git switch -c prod/p1-ts-sim
npx -y vitest@2 run --config site/src/sim/vitest.config.ts
```

## 10. Out of scope / do not
- No two-mode solver in the browser. It is too slow (20×6 takes about 2.6 s); the server and presets cover it.
- No UI, which belongs to P2. Do not edit `site/package.json`.

## 11. If blocked
- **The banded LU is unstable without pivoting:** use a sparse LU with partial pivoting (hand-written, or a small vendored routine). Add a `DECISION NEEDED` if it is over 600 ms.
- **The Wigner convention is unclear:** match dynamiqs numerically, using a value from the dynamiqs docs example or one provided by P0 from the server, and record it.
- **Cut line:** `optimalPulse` may fall back to a precomputed pulse from the physics records if power iteration misbehaves.

## 12. Hand-off
At DONE, the status file has: the test list and results, perf numbers, the accuracy at the interactive setting, the Wigner convention, and devDependencies for P7.

**Questions Harshit should be able to answer:**
1. Why is Crank–Nicolson stable when RK4 needs tiny steps, and what does "stiff" mean here?
2. How do we know the browser solver agrees with dynamiqs?
3. What does the linear-response matrix R_b represent, and why is its top singular vector the best pulse?
