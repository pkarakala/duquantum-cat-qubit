# Fast, robust preparation of |+α⟩: findings

Script: `research/explore/fast_prep.py`. Results: `results/research/fast_prep.json` (merged) and
`results/research/fast_prep_{part1,part2,part3}_24x8.json`, `fast_prep_conv_*_32x12.json`.
Figure: `figures/research/fast_prep.png`. Two-mode model, α = 2.1, Tsit5 rtol 1e-8 (src/config.py).
Written with AI assistance (Claude). Numbers are from the runs listed at the bottom.

## Question

After a symmetry-breaking memory push to |β⟩, how fast does the stabilization reach
F(+α) = ⟨α|ρ_a|α⟩ ≥ 0.99 (and 0.999), and which recipe still works when the push is off by
amplitude ×0.7 / ×1.3 or phase ±20°? We varied the push size β, the buffer-drive schedule ε_d(t)
(step, linear ramp, two-step, brief overdrive), and for a finite push i·ε₁(a†−a) of length T whether
ε_d turns on together with the push or after it. Times are counted from the start of the push.
"Worst" is the worst of the four push variants (nominal, ×0.7, ×1.3, +20°). −20° gives exactly the
same F as +20° (H and the jump operators are real, so ρ(β*) = ρ(β)*; checked numerically, difference 0).

## Plain-language summary

1. **Aim the push at the well itself and switch the buffer drive on as a step.** With β = α the
   nominal state is already the target. Push errors still cost something: the worst case,
   a 20° phase error, needs 0.48 µs to reach 0.99. That is the best worst case of all 43 recipes.
   Aiming short (β = 1.75) is faster to 0.99 only in the rare case where the push is exactly right.
   An undershoot ×0.7 then lands at 1.23, which needs 0.70 µs and has a ceiling of 0.993.
   Aiming long (β = 2.4) protects against undershoot but not overshoot: ×1.3 = 3.1 needs 0.61 µs
   and has a ceiling of 0.996.
2. **Shaping ε_d, which helps inflation from vacuum, hurts here.** Linear ramps (0.2 or 0.4 µs)
   are much worse. Most of them never reach 0.99 within 1.5 µs. While ε_d is low, the g₂
   coupling still turns photon pairs into buffer photons that leak away, so it shrinks the
   pushed state back toward vacuum. The state then loses its memory of which well it was in.
   The two-step (Posicast) drive is slower when the push is nominal (0.48 vs 0.22 µs at β = 1.75).
   It is slightly more forgiving in the worst case (0.65 vs 0.70 µs) because it overshoots less.
   Ramps are for inflating from vacuum, not for pulling a displaced state into a well.
3. **Overdriving ε_d (1.25–2× for 50–100 ns) does not help.** It is slower in every case we ran
   (β = 2.1: 0.33–0.59 µs nominal instead of 0). It overshoots more (peak ⟨n_a⟩ up to 8.8) and
   needs more photon levels.
4. **Turning ε_d on after the push is better than turning it on together with the push, and the
   gap grows with T.** For a 20 ns push the difference is small: 0.26 vs 0.32 µs nominal, worst
   0.73 vs 0.74 µs. For 100 ns, "simultaneous" overshoots to ⟨n_a⟩ = 7.8 and is clearly worse
   (β = 1.75: 0.70 vs 0.53 µs nominal; at β = 1.5 the nominal push never reaches 0.99).
   A finite push also costs more than its own length T: g₂ is on during the push and drains
   the memory. Keep the push short (≤ 20 ns, i.e. ε₁ ≈ β/T ≈ 2π·14 MHz for β = 1.75) and
   switch ε_d on when the push ends.
5. **0.999 is not robust.** The nominal push reaches 0.999 for β ≥ 1.68 (β = α: immediately;
   β = 2.4: 0.53 µs; β = 1.75: 0.64 µs). No recipe reaches 0.999 for all four push errors.
   The limit is not speed. A miscalibrated push leaves a fixed fraction, about 1e-3, in the
   wrong well (−α), and the stabilization can never bring it back. At 2.5 µs, β = α with
   a 20° error saturates at 0.9989, and ×0.7 saturates at 0.9985 (32×12).
   Reaching 0.999 robustly needs a better-calibrated push (smaller errors than ±20°/×0.7),
   not a cleverer schedule.

## Recipes ranked by worst-case time to F ≥ 0.99 (24×8 scan, instantaneous push unless stated)

t99 / t999: first time after which F stays above the threshold (inf = not within 1.5 µs).
F₁: F at 1 µs. Worst-case columns are over {nominal, ×0.7, ×1.3, +20°}.

| # | Recipe | t99 (µs) | t999 (µs) | F₁ | worst t99 (µs) | worst F₁ | worst case |
|---|---|---|---|---|---|---|---|
| 1 | β = α = 2.1, step ε_d | 0 | 0 | 0.99999 | **0.483** | 0.9983 | +20° |
| 2 | β = 2.1, overdrive 1.25× for 0.1 µs | 0.326 | 0.669 | 0.99976 | 0.612 | 0.9974 | ×0.7 |
| 3 | β = 2.4, step | 0.200 | 0.526 | 0.99987 | 0.613 | 0.9959 | ×1.3 |
| 4 | β = 1.75, two-step 0.7 → 1 at 0.26 µs | 0.479 | 0.889 | 0.99950 | 0.647 | 0.9940 | ×0.7 |
| 5 | β = 1.75, step | 0.221 | 0.636 | 0.99974 | 0.705 | 0.9928 | ×0.7 |
| 6 | β = 1.68 (0.8α), two-step | 0.480 | 0.887 | 0.99948 | 0.724 | 0.9920 | ×0.7 |
| 7 | β = 2.1, overdrive 2× for 0.05 µs | 0.591 | inf | 0.99775 | 0.725 | 0.9943 | +20° |
| 8 | 20 ns push to 1.75, ε_d after | 0.258 | 0.684 | 0.99970 | 0.730 | 0.9927 | ×0.7 |
| 9 | 20 ns push to 1.75, ε_d simultaneous | 0.322 | 0.663 | 0.99966 | 0.735 | 0.9922 | ×0.7 |
| 10 | β = 2.1, overdrive 1.5× for 0.1 µs | 0.578 | 1.227 | 0.99871 | 0.756 | 0.9944 | ×0.7 |
| 11 | 50 ns push to 1.75, ε_d after | 0.425 | 0.771 | 0.99954 | 0.770 | 0.9925 | ×0.7 |
| 12 | β = 1.75, overdrive 1.25× for 0.1 µs | 0.480 | 0.929 | 0.99921 | 0.835 | 0.9914 | ×0.7 |
| 13 | β = 1.68, step | 0.347 | 0.698 | 0.99957 | 0.869 | 0.9906 | ×0.7 |
| 14 | 100 ns push to 1.75, ε_d after | 0.526 | 1.322 | 0.99867 | 1.049 | 0.9898 | +20° |
| 15 | β = 1.5, step | 0.408 | inf | 0.99857 | inf | 0.9822 | ×0.7 |
| – | β ≤ 1.5 with any recipe; every linear ramp; 100 ns push with ε_d simultaneous; β = 1.0 | | | | inf | ≤ 0.989 | |

The full list of 43 recipes is in `fast_prep.json` → `ranked`. Fastest nominal t99 values:
β = α (0), β = 1.5 ×1.3 → 1.95 (0.05 µs), β = 2.4 (0.20 µs), β = 1.75 (0.22 µs).

Caveat on t99: F(t) rings with the inflation pendulum (period about 0.32 µs). For a start near
the threshold, F touches 0.99 early, dips, and recovers, so t99 can jump by about 0.1–0.3 µs
between neighbouring β. Examples: β = 1.68 gives 0.35 µs and β = 1.75 gives 0.22 µs; β = 2.4 ×0.7
gives 0.35 µs and β = 1.75 ×1.3 gives 0.05 µs. Read the ranking with roughly ±0.1 µs resolution.
The 5 ns time grid adds ±2.5 ns.

## Truncation and convergence check

The scan used 24×8. Three recipes were re-run at 32×12 to 2.5 µs (β = 2.1, 1.75 and 2.4, step
ε_d, all four push variants). Results, 24×8 → 32×12:

| Recipe | worst t99 | nominal t999 | worst F₁ | F at 2.5 µs (nom / ×0.7 / ×1.3 / +20°), 32×12 |
|---|---|---|---|---|
| β = 2.1 step | 0.483 → 0.483 | 0 → 0 | 0.99828 → 0.99830 | 0.99999 / 0.99851 / 0.99929 / 0.99887 |
| β = 1.75 step | 0.705 → 0.702 | 0.636 → 0.636 | 0.99281 → 0.99289 | 0.99980 / 0.99335 / 0.99996 / 0.99814 |
| β = 2.4 step | 0.613 → 0.611 | 0.526 → 0.526 | 0.99590 → 0.99596 | 0.99990 / 0.99966 / 0.99635 / 0.99854 |

Times agree within 3 ms and F within 1e-4. At 32×12 the top-two memory levels hold at most
5e-7 and the top buffer level at most 5e-6. In the 24×8 scan they stay below 5e-4 / 3e-3 for
every recipe without overdrive. The overdrive and 100 ns-simultaneous runs reach ⟨n_a⟩ ≈ 8–9
and up to 3e-3 / 8e-3 there, so treat those rows as indicative. They are slower anyway, so the
ranking does not depend on them. The finite-push rows (part 2) were not re-checked at 32×12.

## Is it worth a slide?

Yes, as one half-slide "lesson" next to Task 1.3(b), not as a headline. The message:
*aim the push at the well, step the buffer drive on right after it, and keep the push short. The
stabilization then reaches F ≥ 0.99 within 0.5 µs for ±20° / ±30% push errors. 0.999 is limited by
push calibration, because errors leave about 1e-3 in the wrong well, not by speed.* The finding
that the drive shaping which helps inflation (ramp/Posicast) hurts here is a nice
counter-intuitive point, and the physics fits in one line: a weak drive lets g₂ pull the state
back toward vacuum. Use the figure's right panel (worst-case vs nominal bars) or a cut-down version.

## Runs (4 cores, shared with another agent)

| Run | Trajectories | Wall time |
|---|---|---|
| part1, 24×8, 1.5 µs | 80 (+2 for the mirror check) | 4.9 min |
| part2, 24×8 | 48 | 3.6 min |
| part3, 24×8 | 36 + 8 | 3.0 min |
| conv β = 2.1, 32×12, 2.5 µs | 4 | 2.2 min |
| conv β = 1.75, 2.4, 32×12, 2.5 µs | 8 | 5.5 min |

```bash
python -m research.explore.fast_prep part1 --na 24 --nb 8
python -m research.explore.fast_prep part2 --na 24 --nb 8
python -m research.explore.fast_prep part3 --na 24 --nb 8
python -m research.explore.fast_prep conv --na 32 --nb 12 --betas 2.1 --t-end 2.5
python -m research.explore.fast_prep conv --na 32 --nb 12 --betas 1.75,2.4 --t-end 2.5
python -m research.explore.fast_prep summary
```

Model notes: in part 2, g₂ stays on during the push and only ε_d is delayed. A push with the pump
fully off (g₂ = ε_d = 0) is just an exact displacement, κ_a being negligible over ≤ 100 ns, so it
equals the part-1 instantaneous result shifted by T. The pushes were not optimized beyond the grid
above; GRAPE (`research/grape.py`) is the tool for that.
