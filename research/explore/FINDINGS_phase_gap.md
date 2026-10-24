# Why the two-mode model forgives less phase error than the one-mode model

Script `research/explore/phase_gap.py`; data `results/research/phase_gap.json`; figure `figures/research/phase_gap.png`.

Setup: the memory starts in |β⟩ with |β| = α = 2.1 and phase error θ; we stabilize and read F(+α) at 2 µs. Two-mode runs use the full model with an empty buffer, as in Task 1.3b. One-mode runs use the effective L2 = √κ2(a²−α²) plus κa, through the Heisenberg basin map at N = 30.

## Numbers

| model | F = 0.99 crossing | F at 45° |
|---|---|---|
| one-mode | 44.8° | 0.990 |
| two-mode, κb ×1 (experiment) | 35.5° | 0.972 |
| κb ×2 | 37.0° | 0.976 |
| κb ×4 | 38.3° | 0.979 |
| κb ×8 | 40.2° | 0.982 |
| κb ×16 | 41.4° | 0.985 |

κ2 is held fixed: g2 = √(κ2κb/4), ε_d = α²g2. Task 1.3b's coarse grid only showed "30° passes, 45° fails"; on a 5° grid the edge is 35.5°.

## Cause

- **(a) The buffer's finite bandwidth: confirmed.** The shortfall from the one-mode angle shrinks steadily with κb (9.3, 7.9, 6.5, 4.7, 3.4°, roughly κb^−0.36). At ×16 the exchange is still underdamped (κb/8g2α = 0.81); critical damping is near ×24. Mean-field orbits: in the one-mode model a goes straight to +α; in the two-mode model at real parameters it overshoots outward (|a|max = 1.35α at 45°, 1.53α at 60°), past the well to Re a ≈ 2.8, then rings back. At ×16 the overshoot is gone. The classical orbit never crosses Re a = 0: during the ringing the exchange distorts the memory state and its tail crosses into the −α basin. The leak is permanent, not slow settling: Re⟨a⟩/α = 0.945 at 45° matches ~2.8% in −α, and F changes by ≤ 2e-3 between 1 and 2 µs.
- **(b) Empty buffer: rejected.** Starting the buffer at its adiabatic amplitude b0 = −2i g2(β²−α²)/κb lowers F at κb ×4 (30/40/45/50°: 0.994/0.980/0.967/0.947 vs 0.997/0.988/0.979/0.964 with an empty buffer). With an underdamped exchange the adiabatic amplitude kicks the memory outward; the empty buffer acts as a soft turn-on. The ×1 pre-filled run is not converged (overshoot ~2.3α, top populations 0.14 and 0.05); read it only as "much worse".
- **(c) Different basin boundary: no.** Both models are symmetric under a → −a, so the boundary is Re a = 0 in both.

## Truncation

Na = 24, Nb = 8 (×1–2) or 6 (×4–16). At ×1, 32×12 gives 0.99510/0.97268 at 30/45° vs 0.99504/0.97220 at 24×8 (≤ 5e-4; matches Task 1.3b). At ×16, 28×8 and 24×6 differ by < 1e-5. Crossing angles good to ~0.1°. Solver Tsit5, rtol 1e-8; 857 s total on 4 shared cores.

## Meaning for 1.3c

At real parameters the F ≥ 0.99 phase window is about ±35°, not ±45°. A bare pulse needs θ ≤ 2.7°, so stabilization widens the tolerance about 13× (not 16×). Effective-model arguments near the basin edge overstate the margin by ~9° at today's κb, recovering ~1.5° per doubling of κb at fixed κ2. This ties Task 1.1 (the overshoot) and Task 1.3b (the phase window) to one cause: the slow buffer.
