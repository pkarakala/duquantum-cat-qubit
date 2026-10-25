# Section 2 (Standard track): bit flips, phase flips and a better readout

Draft, Sat Oct 24 2026. Every number below comes from a JSON in `results/s2/` written by a script in
`research/s2/`. `python -m research.s2.summarize` rebuilds `results/s2/SUMMARY.md` and `figures/s2/`.
Numbers marked ⟨pending⟩ are waiting on the cloud batch.

## The one idea behind all four tasks

Section 2 asks for rates that differ by eight orders of magnitude (Γ_Z ≈ 0.5 /µs, Γ_X ≈ 4e-7 /µs at α = 2.1).
A time-domain simulation must run for ~1/Γ to see a decay, so the prompt warns that Γ_X is
"only numerically tractable at small α". We sidestep that wall. A decay rate *is* an eigenvalue of the
Liouvillian 𝓛, and every term of the cat model is invariant under a → −a. So 𝓛 splits into a block that is
even in memory parity (it holds the steady state and the X_L coherence, so its slowest nonzero eigenvalue is Γ_Z)
and an odd block (it holds Z_L, so its slowest eigenvalue is Γ_X, with no zero mode to deflate). A sparse
shift-invert Arnoldi solve (scipy/ARPACK) on the odd block gives Γ_X at α = 2.1 on the full two-mode model in
about a minute (28×8), however small Γ_X is. Where both methods are feasible we check the eigenvalue against a
time-domain fit; they agree to 4e-8 (α = 1.0).

Code: `src/spectral.py` (Liouvillian, parity blocks, analytic channels), `research/s2/gx_eig.py` (one job per
α, truncation and knob), `research/s2/gx_time.py` (time-domain cross-check).

## Task 2.1: Γ_X

- **Reproduces prior anchors exactly:** one-mode N = 40: 2.2819e-3, 1.0744e-4, 2.0693e-6, 1.1699e-7 /µs at
  α = 1.0, 1.4, 1.8, 2.1. Two-mode: 2.3007e-3 (α = 1.0), 1.2020e-4 (α = 1.4), 3.8831e-7 (α = 2.1, 28×8).
- **Truncation trap at α = 2.1:** 28×6 gives 3.988e-7, 28×8 3.883e-7, 32×10 3.853e-7 (Nb matters at the 3% level).
- **Two bit-flip channels.** (i) A direct, code-space process: one photon loss a acting on |+α⟩ has an amplitude
  ⟨−α|a|+α⟩ ∝ α e^{−2α²} to land in the other well; the Golden Rule gives κ_aα²(coth 2α² − 1) ≈ 2κ_aα²e^{−4α²},
  i.e. γ = 4. (ii) An out-of-code-space process: a photon loss leaves the code space and the two-photon
  confinement brings the state back to the *wrong* well, ∝ (κ_a²/κ₂)e^{−2α²}, i.e. γ = 2 (Dubovitskii; Gautier
  et al. Eq. 4). (ii) wins once α² ≳ ½ ln(κ₂/κ_a) ≈ 2.3.
- **We prove the channel assignment with a κ_a sweep** (the channels scale as κ_a and κ_a²): one-mode
  d lnΓ_X/d lnκ_a = 1.03 (α = 0.8), 1.19 (1.4), 1.58 (1.8), 1.91 (2.1), 2.02 (2.4), 2.00 (3.0).
  Two-mode: ⟨pending⟩.
- **FGR discussion (prompt).** The naive Golden-Rule estimate from the direct matrix element is channel (i):
  γ = 4. It matches the simulation only at small α (it is 96% of the one-mode rate at α = 1.0, 43% at 1.8, 10% at
  2.1). The simulation's slope drifts from ≈ 3 at α ≈ 1–1.4 toward 2 because the second-order channel (ii), which
  the Golden Rule on the direct matrix element cannot see, takes over. So the deck's "γ ≲ 2" is the large-α limit of
  a thermal-free model; real devices also have thermal photons (n_th adds an e^{−2α²} channel; ⟨pending⟩).
- **Fitted γ (two-mode):** ⟨pending⟩.

## Task 2.2: Γ_Z

- Even-block eigenvalue and time-domain parity fit agree: 0.12057 /µs at α = 1.0 both ways
  (prediction 2κ_aα² coth 2α² = 0.12123, −0.5%).
- The parity decays to 1/cosh 2α², not 0, so we fit A e^{−Γt} + C (a pure exponential is biased).
- Slope vs α²: ⟨pending⟩ (one-mode quick check: 0.96 × 2κ_a over α = 1.0–1.4, approaching 1 as coth → 1).

## Task 2.3: readout through the buffer

- With ε_Z(a + a†) on, ⟨b⟩ settles to ∓ε_Z/(2αg₂) for the ±α wells: α = 2.1, ε_Z = 0.1 g₂ gives
  −0.0238 vs −0.0238 (linear). At ε_Z = g₂: −0.2309 vs −0.2381 (3% nonlinearity).
- **It rings.** ⟨b⟩ approaches steady state as a damped oscillation at 3.2 MHz with Q ≈ 2.05 and 1% settling
  in ≈ 1 µs (ε_Z = 0.1 g₂). Linearizing about a well gives b̈ + (κ_b/2)ḃ + 4g₂²α² b = drive: an oscillator at
  2g₂α/2π = 3.2 MHz, underdamped because κ_b < 8g₂α. It is the same oscillator that makes the inflation overshoot
  in Task 1.1. The linear model predicts Q = 2.46; the measured decay (4.9 /µs vs κ_b/4 = 4.1) is faster, so
  Q ≈ 2.05.
- The −α trace follows from an exact antiunitary symmetry: ⟨b⟩₋(t) = −⟨b⟩₊(t)*, checked numerically
  (⟨pending⟩ max deviation).

## Task 2.4: optimizing the readout

### (a) Circuit level
`research/s2/rwa_terms.py` expands the pumped ATS term 2E_Jε_p cos(ω_pt) sin φ̂ exactly in normal order
(e^{−Φ/2} prefactor, Φ = φ_a² + φ_b²) and lists every term up to order 7 with its detuning. Only the a²b† family is
resonant: g₂ = ½E_Jε_pφ_a²φ_b e^{−Φ/2} (so ε_p = 0.037, not 0.035, for g₂/2π = 0.763 MHz), plus number-dressed
copies a²b†(b†b) (0.034 MHz per buffer photon) and a†a³b† (0.9 kHz). Everything else is ≥ 800 MHz detuned
(nearest terms at ±0.8 GHz). A memory readout drive at ω_a enters capacitively as ε_Z(a + a†) plus counter-rotating
terms at 2ω_a. The strong off-resonant pump also Stark-shifts and Kerr-dresses both modes at second order; those
are static detunings that a retuned pump frequency absorbs.

### (b) The trade-off
More ε_Z means more signal, but also more bit flips. On the full Liouvillian, Γ_X grows as ε_Z²: one-mode
α = 2.1 gives 1.17e-7 (ε_Z = 0), 6.6e-6 (0.1 g₂), 2.6e-5 (0.2 g₂), 1.7e-4 (0.5 g₂) /µs. The drive pushes the well
toward the separatrix (shift ε_Z/(2κ₂α²)), which lowers the barrier. Two-mode grid: ⟨pending⟩.

The signal is also quadratic in ε_Z (SNR = κ_b∫|Δ⟨b⟩|²dt), so the meaningful figure of merit is
**SNR per bit flip** at a given readout time, which is what we optimize.

### (c, d) A better pulse
Families compared on the full two-mode model (`research/s2/pulse_eval.py`): square; raised cosine; a cosine at the
3.2 MHz ring frequency; its bang-bang (sign) version; the SVD-optimal pulse of the linear-response model (the top
singular vector of the map ε_Z(t) → Δ⟨b⟩(t), which maximizes SNR per drive energy); its sign version; and a
gradient-optimized pulse (`research/s2/pulse_opt.py`, jax.grad through dynamiqs, objective SNR − μP_flip with μ set
so that the square pulse scores zero).

Local results (small truncations, to be confirmed on the cloud):
- At equal drive energy, the SVD pulse gives 3.4× the SNR of a square pulse at α = 2.1 (T = 1 µs). It drives the
  memory–buffer oscillator on resonance.
- But bit flips track SNR. The useful comparison is flips per unit SNR: shaped pulses (resonant, SVD) cut it by
  ~35% at α = 1.4–1.8 and ~20–25% at α = 2.1 vs a square pulse. At a fixed peak amplitude the bang-bang resonant
  pulse also doubles the SNR collected in the same window (α = 2.1, T = 0.5 µs).
- Gradient optimization from the bang-bang start improves SNR/P_flip to 1.53× the square pulse after 12 Adam steps
  (α = 1.4, T = 0.5 µs, peak 0.5 g₂), still improving.

**Why it works (what we tested so far).** Our first guess was that the square pulse's sharp edges excite the
3.2 MHz ringing and cause extra flips. A direct test falsified it: at α = 1.4 (T = 1 µs, peak 0.5 g₂) smoothing the
edges (raised cosine) improves flips-per-SNR by only 7% (0.0252 vs 0.0272), while driving at the ring frequency
improves it by 36% whether or not the edges are smoothed (0.0174 for both the plain and smooth-edged resonant pulse).
So what matters is *where the drive's spectrum sits*, not its edges. The resonant drive is amplified by the
memory–buffer oscillator (Q ≈ 2) in the buffer field, which carries the information, more than in the memory
excursion that causes the flips. ⟨pending: quadrature-resolved check of this mechanism.⟩
