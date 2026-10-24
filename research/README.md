# Research prototypes (stretch goals)

Quick, self-contained scripts that tested each stretch idea before it goes into the
notebooks. Parameters are the challenge values (`common.py`), double precision,
dynamiqs 0.3.7. Times are on 4 CPU cores. These were written with AI assistance
(Claude) and must be re-run and checked before any number goes in the main README.

| Script | Idea | Run | Key output |
|---|---|---|---|
| `base.py` | Damped-pendulum theory of the 1.1 overshoot | `python base.py` (13 s) | ringing period 0.315 µs simulated vs 0.319 µs predicted by `2π/sqrt((2 g2 α)² − κb²/16)` |
| `shapes.py` | Shaped buffer drive ε_d(t): two-step (Posicast), linear and sin² ramps | `python shapes.py 28 7` (~3 min) | at 28×7 a linear 0.6 µs ramp stays within 1% after 0.63 µs vs 1.06 µs for a step |
| `verify_shapes.py` | Re-check the three best schedules at a larger truncation | `python verify_shapes.py 40 12` | 40×12: step 1.06 µs (peak 6.89), linear ramp 0.88 µs (peak 4.45, right on the 1% line), two-step 0.71 µs (peak 4.74) |
| `heis.py` | Heisenberg-picture "basin map": one backward evolution gives F(+α) for every start | `python heis.py` (seconds) | F(β=1)=0.981; best {0,1}-photon seed 0.912 |
| `robust.py` | How much stabilization forgives a miscalibrated displacement pulse | `python robust.py` (seconds) | F ≥ 0.99 for phase errors up to 44.5° (2.5° without stabilization) |
| `beta2mode.py` | Displace-then-inflate in the full two-mode model | `python beta2mode.py 32 8` (47 s) | β=1.5 → F=0.9988 at 2 µs |
| `grape.py` | Joint gradient optimization of memory drive ε1(t) and buffer drive ε_d(t) for fast \|+α⟩ prep | `python grape.py 28 7 0.4 16 60 5 [disp]` (~8 s/step) | optimized pulse JSON; `iters=0` prints the displacement baselines |
| `moon.py` | "Moon cat" pair operator a² + λ a†a (Rousseau et al. 2025) | `python moon.py 28 7` | λ = 0.2, 0.4 give no gain for inflation or \|+α⟩ prep (F 0.974, 0.963 vs 0.978), so it was set aside |

Gotcha found while building `grape.py`: `dq.mesolve` starts at `tsave[0]`, so a
`tsave` that does not begin at 0 silently skips the start of the pulse.

Solver note: these prototypes use the default `mesolve` tolerances. The main task
code (PR #2) uses Tsit5 with rtol 1e-8 because the default leaves ~1e-4 noise in the
truncation monitors; re-run anything that goes in the README with those settings.
