# Research scripts (stretch goals)

Scripts for the ideas beyond the Introductory Track tasks. They use the same parameters,
truncations and solver as `tasks/` (`src/config.py`: `METHOD = Tsit5(rtol=1e-8, atol=1e-10)`),
the models in `src/model.py`, and save every number to `results/research/*.json` and every
figure to `figures/research/`. Run them from the repo root as modules (`python -m research.<name>`).

**Status: these numbers must be re-run before quoting.** The scripts started as quick prototypes
(branch `claude/project-thread-80xv97`, default solver tolerances), written with AI assistance
(Claude). The prototype numbers below are only a guide to what to expect. Nothing goes in the
main README until it has been re-run with these scripts and checked.

## Scripts

Runtimes are for 4 CPU cores. "Cloud" jobs are listed in `cloud/research_jobs.txt`.

| Script | What it does | Command | Runtime | Where | Output |
|---|---|---|---|---|---|
| `base.py` | Damped-pendulum theory of the Task 1.1 overshoot: ringing period and decay vs `2π/√((2g₂α)² − κ_b²/16)` and `κ_b/4` | `python -m research.base` | ~1 min | laptop | `base_32x12` |
| `alpha_sweep.py` | Same for α = 1.5, 1.8, 2.1, 2.4: peak, period, envelope decay, settle time; truncation grows with α (`na_rule`), with truncation monitors | `python -m research.alpha_sweep --alpha 2.4` | 0.5–2.5 min per α; 2.5–8 min for the Na+6, Nb=16 check | cloud | `alpha_<α>_<Na>x<Nb>` |
| `schedules.py` | Shaped buffer drive ε_d(t): step, linear, sin², two-step (Posicast). `--schedules scan` is the prototype grid; one spec per run for the cloud | `python -m research.schedules --na 28 --nb 7 --schedules scan` | ~5 min (scan, 28×7); ~3 min per schedule at 40×14 | both | `schedules_<tag>_<Na>x<Nb>` |
| `heis.py` | Heisenberg-picture basin map: one backward evolution gives F(\|+α⟩) for every start state | `python -m research.heis` | ~30 s | laptop | `heis_basin_N30` |
| `robust.py` | Phase and amplitude error windows of displace-then-stabilize (one-mode, from the basin map) | `python -m research.robust` | ~20 s | laptop | `robust_N30` |
| `grape.py` | Gradient optimization (`jax.grad` through `mesolve`) of memory drive ε₁(t) and buffer drive ε_d(t) for fast \|+α⟩ prep. `--iters 0` gives the displacement baselines | `python -m research.grape --na 36 --nb 10 --iters 60 --init disp --seed 1` | ~45 min per seed at 36×10 | cloud | `grape_T0.4_36x10_e5_<init>_s<seed>` |
| `moon.py` | **Negative result.** "Moon cat" operator a² + λa†a (Rousseau et al. 2025): no gain for inflation or \|+α⟩ prep. Kept so the check can be repeated | `python -m research.moon` | ~1 min | laptop | `moon_28x7` |
| `wigner_gif.py` | Wigner GIF of the memory during inflation (32×12, 0–6 µs): the cat forms, then the fringes fade | `python -m research.wigner_gif` | ~2–3 min | both | `figures/inflation.gif`, `wigner_gif_32x12` |
| `merge_cloud.py` | Combines the per-job cloud files into summaries and figures | `python -m research.merge_cloud` | seconds | laptop | `*_summary`, `results/task_1_3b_fine.json` |
| `common.py` | Shared helpers: truncation rule, monitors, ringing analysis, linear theory, basin map | | | | |

Output names are under `results/research/` (JSON) and `figures/research/` (PNG) unless shown otherwise.

Dropped: `beta2mode.py` (displace-then-inflate in the two-mode model). `tasks/task_1_3b.py` now
does this properly. For its finer phase/amplitude grid at 40×14, the task script takes
`--phase P` or `--beta B` and runs a single start, writing `results/task_1_3b_points/`
(the default run and its output file are unchanged).

## Cloud runs

`cloud/research_jobs.txt` has one job per line with a rough weight in minutes, for
`cloud/vultr_batch.py`:

```bash
python cloud/vultr_batch.py cloud/research_jobs.txt --branch research-runs --servers 4 --plan <id> --budget 20
python -m research.merge_cloud      # after the results are copied back
```

41 jobs, ~4.6 h of compute in total. The four GRAPE jobs (~45 min each) are the longest; every
other job is under ~8 min. Estimates are scaled from the Task 1.2 grid timings (`results/grid.log`).

## Smoke tests

Every script accepts small truncations (`--na 12 --nb 4`, or `--n 16` for the one-mode scripts)
and most accept `--t-end`, so a check takes seconds:

```bash
python -m research.alpha_sweep --alpha 2.1 --na 12 --nb 4 --t-end 0.6
python -m research.grape --na 12 --nb 4 --T 0.2 --nbins 4 --iters 3
```

## Prototype findings (default tolerances, to be re-run)

- Ringing period at α = 2.1: 0.315 µs simulated vs 0.319 µs from the linear theory.
- Shaped drive at 40×12: settle to 1% in 1.06 µs (step, peak 6.89), 0.88 µs (linear 0.6 µs ramp,
  peak 4.45) and 0.71 µs (two-step 0.7 until 0.26 µs, peak 4.74).
- Basin map (T = 1 µs): F = 0.981 from |β = 1⟩; the best start in span{|0⟩, |1⟩} reaches 0.912.
- Robustness: F ≥ 0.99 for phase errors up to 44.5° with stabilization, 2.5° without.
- Moon cat: λ = 0.2 and 0.4 give F = 0.974 and 0.963 vs 0.978 at λ = 0.

Gotcha found while building `grape.py`: `dq.mesolve` starts at `tsave[0]`, so a `tsave` that
does not begin at 0 silently skips the start of the pulse.
