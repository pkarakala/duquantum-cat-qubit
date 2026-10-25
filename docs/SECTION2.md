# Section 2 (Standard track): bit flips, phase flips and a better readout

Sat Oct 24 2026. Every number below comes from a JSON in `results/s2/` written by a script in
`research/s2/`. `python -m research.s2.summarize` rebuilds `results/s2/SUMMARY.md` (all tables) and
`figures/s2/`. Cloud runs: `cloud/s2_batch1b.txt`, `cloud/s2_batch2.txt` (Vultr, logged in `docs/tools-log.md`).
Model and parameters exactly as in the prompt (two-mode H_2ph, κ_b, κ_a; ħ = 1, µs, rad/µs; double precision).

## The one idea behind all four tasks

Section 2 asks for rates that differ by eight orders of magnitude (Γ_Z ≈ 0.5 /µs, Γ_X ≈ 4e-7 /µs at α = 2.1).
A time-domain simulation must run for ~1/Γ to see a decay, which is why the prompt says Γ_X is
"only numerically tractable at small α". We sidestep that wall. A decay rate *is* an eigenvalue of the
Liouvillian 𝓛, and every term of the model is invariant under a → −a, so 𝓛 splits into a block even in memory
parity (holds the steady state and X_L: its slowest nonzero eigenvalue is Γ_Z) and an odd block (holds Z_L: its
slowest eigenvalue is Γ_X, with no zero mode to deflate). A sparse shift-invert Arnoldi solve on the odd block,
with a reverse-Cuthill–McKee ordering that halves the LU fill, gives Γ_X at α = 2.1 on the full two-mode model in
under a minute (28×8), however small Γ_X is.

**Validation.** Where the time domain is feasible the two methods agree to 1e-8 (α = 0.8, 1.0, 1.2, 1.4; Re⟨a⟩(t)
fitted over 40–400 µs). They also agree with the readout drive on (α = 1.4, ε_Z = 0.3 g₂: 2e-6). The one-mode values
reproduce the earlier independent anchors to all printed digits (2.2819e-3, 1.0744e-4, 2.0693e-6, 1.1699e-7).

Code: `src/spectral.py`, `research/s2/gx_eig.py`, `research/s2/gx_time.py`.

## Task 2.1: Γ_X

| α | 1.0 | 1.4 | 1.8 | 2.1 | 2.4 |
|---|---|---|---|---|---|
| Γ_X (1/µs), two-mode | 2.3007e-3 | 1.2021e-4 | 4.067e-6 | 3.849e-7 | 3.115e-8 |
| T_X | 0.43 ms | 8.3 ms | 0.25 s | 2.6 s | 32 s |
| two-mode / one-mode | 1.01 | 1.12 | 1.97 | 3.29 | 4.52 |

Convergence: changing Na by +4 or Nb from 8 → 10 → 12 moves Γ_X by < 1.5% up to α = 2.4
(α = 2.1: 3.883e-7 (28×8), 3.854e-7 (28×10), 3.849e-7 (28×12)). At α = 2.6 the truncations disagree by ~20%,
so we stop the curve at 2.5.

**Scaling.** A single log-linear fit over α = 1.0–2.5 gives γ ≈ 2.2, but the slope is not constant:
local γ = 3.1 (α = 1.0–1.4), 2.65 (1.4–1.8), 2.0 (1.8–2.1), 1.86 (2.1–2.4). So "γ ≲ 2" holds only at large α.

**Why the slope runs: two bit-flip channels.**
1. *Direct (Golden Rule).* One photon loss a acting on |+α⟩ lands in |−α⟩ with amplitude ⟨−α|a|+α⟩ = −α e^{−2α²}.
   The Golden Rule gives Γ⁽¹⁾ = κ_aα²(coth 2α² − 1) ≈ 2κ_aα²e^{−4α²}, i.e. **γ = 4**. This answers the prompt's
   discussion question: the naive estimate predicts γ = 4. It accounts for 95% of Γ_X at α = 1.0 but only 3% at
   α = 2.1.
2. *Out of the code space and back.* A photon loss knocks the state out of the code space, and the two-photon
   confinement returns it to the *wrong* well. This is second order in κ_a: Γ⁽²⁾ ≈ (κ_a²/κ₂)e^{−2α²}, i.e.
   **γ = 2** (Dubovitskii; Gautier et al. Eq. 4). It wins for α² ≳ ½ ln(κ₂/κ_a) ≈ 2.3. The Golden Rule on the
   direct matrix element cannot see it.

**Proof of the assignment.** The channels scale as κ_a and κ_a², so we swept κ_a × {¼, ½, 1, 2, 4} at fixed α.
Two-mode slope d lnΓ_X / d lnκ_a = **1.06 (α = 1.0), 1.28 (1.4), 1.78 (1.8), 2.00 (2.1), 2.05 (2.4)**, so the
switch from channel 1 to channel 2 is visible directly.

**Beyond γ = 2.** The two-mode model flips 3.3× faster than the adiabatically eliminated one at α = 2.1 (4.5× at
2.4), and its local γ drops *below* 2 (1.86). The finite buffer (κ_b < 8g₂α, Section 2.3) is a third ingredient
the one-mode model lacks.

**Thermal photons** (jump √(κ_a n_th) a†): n_th = 0.01 multiplies Γ_X by 3.8 at α = 2.1, and n_th = 0.05 by 15.
They add another e^{−2α²} channel, which is why experiments see γ < 2.

## Task 2.2: Γ_Z

Even-block eigenvalue and the time-domain parity fit (from |C₊⟩, fitted as A e^{−Γt} + C because the parity decays
to 1/cosh 2α², not to 0) agree to 5 digits: 0.12057 /µs (α = 1.0) and 0.51455 vs 0.51456 /µs (α = 2.1).
Over α = 0.8–2.6 the eigenvalues track 2κ_aα² coth 2α² to within 0.1–0.5%, and the slope of Γ_Z vs α² is
**0.991 × 2κ_a**. The small residual is the same in both methods, so it is a two-mode effect, not numerics.

## Task 2.3: readout through the buffer

Code: `research/s2/readout.py` (step ε_Z(a + a†) at t = 0, from the dark state |±α⟩|0⟩).

- **Contrast.** ⟨b⟩_ss = ∓ε_Z/(2αg₂) holds to 1% up to ε_Z = 0.5 g₂ at α = 2.1 (−0.1184 vs −0.1190), with 4% at
  ε_Z = g₂ and 36% at 2 g₂. Beyond that the drive makes the wells flip within the window (Section 2.4b), and the
  "steady-state" contrast collapses toward zero. The two wells' traces obey ⟨b⟩₋(t) = −⟨b⟩₊(t)* to 1e-15
  (an exact antiunitary symmetry; checked by simulating both).
- **It rings.** ⟨b⟩ approaches steady state as a damped oscillation at **3.21 MHz with Q ≈ 2.05** (α = 2.1), and
  settles to 1% in ≈ 0.97 µs. Linearizing about a well gives b̈ + (κ_b/2)ḃ + 4g₂²α² b = drive: an oscillator at
  2g₂α/2π = 3.2 MHz, underdamped because κ_b < 8g₂α. It is the same oscillator behind the inflation overshoot in
  Task 1.1. Frequency and Q grow with α (2.76 MHz / Q 1.64 at α = 1.8; 3.67 MHz / Q 2.45 at α = 2.4). The linear
  model's Q = 4g₂α/κ_b is about 17% too high; the measured damping is faster than κ_b/4.
- **For a protocol** this means integrating for ≈ 1 µs after switch-on, or shaping the drive (Task 2.4).
- Converged: 36×10 matches 32×8 to 4 digits.

## Task 2.4: optimizing the readout

### (a) Circuit level
`research/s2/rwa_terms.py` expands the pumped ATS term 2E_Jε_p cos(ω_pt) sin φ̂ exactly in normal order
(prefactor e^{−Φ/2}, Φ = φ_a² + φ_b²) and lists every term up to order 7 with its detuning.
- Only the a²b† family is resonant: g₂ = ½E_Jε_pφ_a²φ_b e^{−Φ/2}, so ε_p = **0.037** (not 0.035) for
  g₂/2π = 0.763 MHz. Number-dressed copies a²b†(b†b) (0.034 MHz per buffer photon) and a†a³b† (0.9 kHz) are also
  resonant. Everything else is ≥ 0.8 GHz away.
- A memory readout drive at ω_a enters capacitively as ε_Z(a + a†), plus counter-rotating terms at 2ω_a.
- **The direct circuit simulation shows what the RWA misses.** `research/s2/circuit_sim.py` integrates the full
  time-dependent sin φ̂ in the rotating frame (no RWA; displacement operators built on an enlarged space) for
  150 ns with a 20 ns pump ramp, and compares it with g₂(a²b† + h.c.). With the pump at the nominal
  ω_p = 2ω_a − ω_b, the two-photon conversion **does not happen**: n_a stays near 0.8 while the RWA model converts
  it down to 0.58. The strong off-resonant pump Stark-shifts the modes (memory −0.9 MHz, measured from the phase of
  ⟨a⟩; the buffer's shift, inferred from the retuning below, is much larger), which detunes a²b† by far more than g₂. Scanning the pump frequency restores the
  resonance at **δω_p/2π ≈ −23 MHz**: the averaged n_a deviation drops from 0.43 to 0.06. The remaining n_b offset
  of 0.069 is the buffer's pump micromotion |ξ_b|², which we predict analytically as
  (E_Jε_pφ_b/(ω_b − ω_p))² ≈ 0.26² = 0.068. Converged at 12×5 and 14×6; a too-small 8×3 truncation hides the
  effect entirely.

### (b) The trade-off
More ε_Z gives more signal and more bit flips. On the full two-mode Liouvillian (validated in the time domain
at α = 1.0 and 1.4):

| α | Γ_X(0) | Γ_X(0.1 g₂) | Γ_X(0.3 g₂) | Γ_X(g₂) |
|---|---|---|---|---|
| 1.4 | 1.20e-4 | 3.85e-3 | 3.69e-2 | 0.51 |
| 2.1 | 3.85e-7 | 2.38e-5 | 2.47e-4 | 8.6e-3 |

The drive-induced part is quadratic, Γ_X − Γ_X(0) = c(α)ε_Z², up to ε_Z ≈ 0.3 g₂, and grows faster beyond that.
The coefficient falls as **c ∝ e^{−2.03α²}**, the e^{−2α²} law of a drive-activated out-of-code-space channel. The
signal is also quadratic, since SNR = κ_b∫|⟨b⟩₊ − ⟨b⟩₋|²dt ∝ ε_Z². So in the linear regime **turning up ε_Z does not
change the flips you pay per unit of information**. The only levers are the drive's *shape* in time and frequency,
and the cat size (c drops ~e^{−2α²} while the signal per ε_Z drops only as 1/α²).

### (c, d) A better pulse
We compared pulse families at the same **peak** amplitude and window on the full two-mode model
(`research/s2/pulse_eval.py`): square; raised cosine; a cosine at the ring frequency ("res"); res with smooth edges;
its sign ("bang-bang"); the SVD-optimal pulse of the linear-response model (the top singular vector of the map
ε_Z(t) → Δ⟨b⟩(t), which maximizes SNR per unit drive energy; `research/s2/linresp.py`); and a gradient-optimized
pulse (`research/s2/pulse_opt.py`: jax.grad through dynamiqs, objective SNR − μP_flip with μ chosen so the square
pulse scores 0, peak bounded by tanh). P_flip is read from the loss of Re⟨a⟩ after the pulse plus 2 µs of relaxation.

At α = 2.1, T = 0.5 µs, peak 0.5 g₂ (converged: 32×8 and 36×10 agree, rtol 1e-9 and 1e-11 agree), relative to the
square pulse:

| pulse | SNR | flips per unit SNR |
|---|---|---|
| square | 1 | 1 |
| raised cosine | 0.42 | 0.86 |
| resonant cosine | **1.29** | **0.79** (the same flip count as square, 29% more signal) |
| resonant, smooth edges | 0.55 | 0.73 |
| bang-bang resonant | 2.04 | 0.88 |
| SVD-optimal | 0.93 | 0.76 |
| gradient-optimized (30×8, 15 Adam steps) | **1.51** | 0.79 (the same ratio as resonant, at 20% more flips) |

The same ordering holds at α = 1.4 and 1.8 (resonant: 0.64–0.74 flips per SNR) and for T = 0.25–1 µs. At peak 0.5 g₂ the optimizer does not beat the resonant pulse on flips per unit SNR; it spends the extra
flips on more signal. At peak 1.0 g₂ it reached 1.40× the square pulse's SNR with 0.90× its
flips (30×8; 26×6 gave 1.42× and 0.89×), and at α = 1.4, T = 1 µs, peak 0.5 g₂ it gave 1.13× the SNR with 0.71× the
flips (22×8). A square pulse is never the best choice.

**Why it works.** We first guessed that the square pulse's sharp edges cause extra flips by
kicking the ringing. Smoothing the edges alone (raised cosine) helps only 8–14%, so that is not the main effect.
What matters is *where the drive's spectrum sits* (resonant with or without smooth edges: 0.73–0.79). Our interpretation: the memory and buffer form a damped oscillator at 2g₂α
(Section 2.3). A drive at that frequency is amplified by its Q in the buffer field, which carries the
information, and it moves the memory along with the oscillator instead of pushing it statically toward the
separatrix. A DC (square) drive does the opposite: it parks the memory displaced toward the separatrix for the
whole pulse. The gradient optimizer, started from the bang-bang pulse, keeps the resonant structure and reshapes
the envelope.

## Numerics and convergence checklist
- Precision: float64 throughout; Tsit5 rtol 1e-8–1e-11 (pulse results checked at two tolerances).
- Every headline number is checked at ≥ 2 truncations; the population in the top Fock level is ≤ 1e-6 in all
  readout and pulse runs (columns `max_top_a`).
- Eigen vs time domain: Γ_X at 4 values of α (≤ 4e-8), Γ_X with the drive on at 4 points, and Γ_Z at 6 values of α.
- Known limits: Γ_X at α ≥ 2.6 is not converged in our truncations; the circuit simulation is a 150 ns window
  without loss (enough to see the conversion rate and the Stark-shift detuning, not the steady state).
