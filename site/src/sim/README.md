# In-browser one-mode solver

Levels 1–4 and the level-8 score run here, offline. Two-mode physics stays on the server.

```ts
import { simulate, runInWorker, wigner, linresp, C } from './index.ts';
```

`simulate(req)` is pure and deterministic. `runInWorker(req)` is the same step off the main thread (Node `worker_threads`, or a module worker in the browser). Rates are rad/µs and time is µs. The factor that turns MHz into rad/µs lives only in `config.ts`.

## What a request can evaluate

- States: vacuum, coherent, even/odd cat, Fock. At `tEndUs = 0` this is just the state (level 1 histogram and Wigner).
- Hamiltonian `ε_z(a+a†)` (imaginary push, readout) and `ε_x i(a†−a)` (real push).
- Jumps `√κ a`, thermal `√(κ n_th) a†`, `√κ₂ a²`, and the cat jump `√κ₂(a²−α²)`.
- A one-mode ExprTree (`a`, `ad`, `n_a`, `I`) for H and the jumps. `b` and `bd` are rejected.
- Outputs: `⟨n⟩`, parity, `Re⟨a⟩`, final Fock populations, and Wigner frames.
- `linresp`: poles, piecewise-constant response, SNR `κ_b∫|Δb|²dt`, leakage `∫|δa|²dt`, and the optimal readout pulse.

## Crank–Nicolson

The state is the full column-stacked density matrix. One factorization of `I − ½dt L` is reused for every step; the factors use partial pivoting because the two-photon Lindbladian is not diagonally dominant. After every step, `ρ ← (ρ+ρ†)/2`. Skipping that re-Hermitianization lets round-off grow like `e^{+κ₂ n² t}` and the trace blows up before 1 µs.

Default step count is 400 per 2 µs (and at least one step per output interval). Golden tests pass `nSteps` explicitly; 4000 steps over 2 µs reproduce the dynamiqs Task 1.0c finals to about `1e-10` relative. At the interactive 400-step setting the cat-inflation transient differs from a 4000-step reference by `3e-3` in `⟨n⟩` (N = 20, 2 µs). The steady two-photon plateau does not depend on the step size.

N = 30, 2 µs, 400 steps takes about 170 ms. The worker reports the same.

## Wigner

Clenshaw summation at QuTiP `g = 2`, which is dynamiqs' `hbar = 1/2`. `x` is `Re α` and `y` is `Im α`. Vacuum is `(2/π) exp(−2(x²+y²))`, so `W(0,0) = 2/π`, and `|α⟩` peaks at `x = Re α`. Frames from `simulate` use an 81×81 grid on `[−4, 4]²`. The flat buffer is row-major with index `ix * ny + iy` equal to `W(x[ix], y[iy])` — dynamiqs' layout, not QuTiP's `(y, x)` layout. The Fock diagonals are precomputed once per state.

## Linear response

`M` and `u` are the contract's 2×2 readout system. Each bin is an exact exponential of the affine 3×3 system. `optimalPulse` is the top right singular vector of `R_b`, where column `j` is `Δb = b(+α) − b(−α)` for a unit drive on bin `j`. The returned bins have energy `∫ε² dt = 1`, and `gain` is that pulse's SNR.

Verified at the nominal parameters, equal to the level-8 square budget `0.25 g₂² µs`: square SNR `0.954`, SVD pulse SNR `4.030`. The prototype `0.95` and `4.06` were the right scale; these are the values to quote.

## Tests

From the repo root, without editing `site/package.json`:

```bash
npx -y vitest@2 run --config site/src/sim/vitest.config.ts
```

P7 should add `vitest@2` as a devDependency. There is no other dependency. Linresp and Wigner parity against `server/tests/fixtures/` is skipped until P0 writes those files.
