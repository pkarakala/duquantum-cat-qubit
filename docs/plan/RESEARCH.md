# Research notes: verified facts behind the plan

Every number and formula an agent needs, gathered in one place, each with its source. "(verified)" means it was checked against the primary source, such as the docs, the GitHub source at a tag, or the arXiv text. "(derived)" means it was worked out by hand, and an adversarial reviewer re-derived it independently. "(anchor)" means an earlier scipy run produced it: **reproduce it, don't trust it.**

---

## §1 Parameters and derived numbers

The units follow the prompt: ħ = 1, time in µs, rates in rad/µs, and ω = 2πf. The 2π is applied exactly once, in `src/config.py`.

| Symbol | Value | rad/µs |
|---|---|---|
| g₂/2π | 0.763 MHz | G2 = 4.79411 |
| κ_b/2π | 2.6 MHz | KAPPA_B = 16.33628 |
| κ_a/2π | 9.3 kHz | KAPPA_A = 0.0584336 |
| α | 2.1 (α² = 4.41) | |
| ε_d = α²g₂ | | EPS_D = 21.142 |
| κ₂ = 4g₂²/κ_b | κ₂/2π = 0.8957 MHz | KAPPA_2 = 5.6276 |
| 2κ_a | | 0.116867 /µs |
| κ_a/κ₂ | 0.01038 | |
| κ_b/g₂ | 3.41 (Ferrari's "barely nonadiabatic" case is 3.0) | |
| g₂/κ_b, ε_d/κ_b | 0.29, 1.29: the condition κ_b ≫ g₂, ε_d is **violated** | |
| 8g₂α vs κ_b | 80.5 vs 16.3 rad/µs, so **strongly non-adiabatic, underdamped** (§7) | |

---

## §2 dynamiqs 0.3.7 API (verified against the source at tag v0.3.7)

- **`dq.mesolve`.** The signature is `mesolve(H, jump_ops, rho0, tsave, *, exp_ops=None, method=Tsit5(), gradient=None, save_states=True, cartesian_batching=True, progress_meter=None, t0=None, save_extra=None, vectorized=False, assume_hermitian=True)`.
  - There is **no `options=` argument**; it was removed in 0.3.6. Pass these keywords directly.
  - The results object has `.states`, `.final_state`, `.expects` and `.extra`.
  - **`save_extra` takes `(t, rho)`.** A one-argument lambda breaks.
- **`dq.method.Tsit5`.** Signature: `Tsit5(rtol=1e-6, atol=1e-6, safety_factor=0.9, min_factor=0.2, max_factor=5.0, max_steps=100_000)`. Raise `max_steps` for traces of tens of µs (`C.METHOD_LONG`).
- **Precision.** `dq.set_precision('double')` sets `jax_enable_x64`, so it must run **before** any array is built. Importing `src.config` first handles this.
- **Gradients.** `jax.grad` works through `mesolve` by default.
  - The default gradient is `dq.gradient.BackwardCheckpointed`; `Direct`, `Forward` and `HigherOrder` (new in 0.3.7) also exist.
  - The old `Autograd` and `CheckpointAutograd` names were removed in 0.3.4.
  - Pattern to copy: the Kerr-oscillator GRAPE tutorial, which uses `dq.pwc` + `jax.value_and_grad` + `optax.adam`. https://www.dynamiqs.org/stable/documentation/advanced_examples/kerr-oscillator.html
- **Time-dependent operators:**
  - `dq.pwc(times, values, qarray)`. `values` may carry a leading batch axis `(N, nbins)`.
  - `dq.modulated(f, qarray, *, discontinuity_ts=None)`.
  - `dq.timecallable(f, *, discontinuity_ts=None)`. The function must return a QArray.
- **Batching.** Give the operators or states leading axes, and pass `cartesian_batching=` directly to `mesolve`.
- **Liouvillian.** `dq.slindbladian(H, jumps)` exists, but `to_numpy()` makes it **dense** (~348 GB at 32×12). Build L with `scipy.sparse.kron` instead (§9).
- **Helpers:** `dq.ptrace(x, keep, dims)`; `dq.wigner(state, xmax=6.0, ymax=6.0, npixels=201, ...)`; `dq.plot.wigner_gif`; `dq.plot.wigner_mosaic`; `dq.cat(dim, alpha)` (new in 0.3.7); `dq.parity`; `dq.coherent`; `dq.destroy(Na, Nb)`, which returns a tuple.

---

## §3 Windows and JAX environment (verified)

- JAX lists native Windows x86_64 CPU as **"experimental"**, and it may need the MSVC 2019 redistributable. https://docs.jax.dev/en/latest/installation.html
- jax ≥ 0.11 needs Python ≥ 3.12. The repo pins `jax==0.12.0.1` (released Oct 21), while dynamiqs 0.3.7 was released Oct 15, so that pairing is untested by upstream.
  - Fallback 1: Python 3.11 with `jax==0.10.2 jaxlib==0.10.2` (cp311 Windows wheels exist).
  - Fallback 2: WSL Ubuntu.
- dynamiqs CI runs only on Ubuntu with Python 3.11.
- `OMP_NUM_THREADS` does **not** limit XLA. Use `XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"`.
- The laptop is an i7-9750H (6 cores / 12 threads) with 15.9 GB RAM. Its GTX 1650 has poor fp64 throughput, so everything runs on CPU.

---

## §4 Symmetries: what they forbid and what they guarantee (derived, independently re-derived)

### §4.1 Drive quadratures and the antiunitary symmetry
- **What each drive does.** H_Z = ε(a + a†) gives ȧ = −iε, a push along the **imaginary** axis. The wells sit at ±α on the real axis, so the imaginary axis is the separatrix between them.
  - In the code space, (a + a†) ≈ 2α Z_L, so ε(a+a†) is a **Z_L rotation** (the readout drive).
  - H_X = ε·i(a† − a) gives ȧ = +ε, a push along **+Re**. This is what moves the state toward one well.
- **Antiunitary symmetry.** Let U = P·e^{iπb†b}·K, where P is memory parity and K is complex conjugation in the Fock basis. Then U H* U† = −H for the full two-mode H plus ε_Z(a+a†), and every jump operator maps to minus itself.
  - So ρ ↦ Uρ*U† is a symmetry of the Lindbladian. The vacuum is invariant under it, which forces ⟨a⟩ = −⟨a⟩*, i.e. **Re⟨a⟩ ≡ 0 for all t**.
  - **Consequence:** an ε(a+a†) drive can never prepare |+α⟩ from vacuum. Use `eps_x` (i(a†−a)), which only keeps the e^{iπb†b}K symmetry. That forces ⟨a⟩ to be real, so the state can tip into +α.
  - **Test:** start from vacuum with only `eps_z` on (Na = 12, Nb = 4, 0.5 µs), and check max|Re⟨a⟩| < 1e-12.

### §4.2 Z₂ sectors of the Liouvillian, and code-space rates
- H (a²b†, a†²b, b, b†), √κ_b b, √κ_a a (D[−L] = D[L]) and the thermal √(κ_a n_th) a† are all invariant under a → −a.
  - So the Liouvillian commutes with ρ ↦ PρP, and splits into blocks with (n_a − m_a) even and odd.
- **Sector contents:**
  - The steady state and X_L (parity, ≈ |α⟩⟨−α| + h.c.) are **even**.
  - Z_L ≈ |α⟩⟨α| − |−α⟩⟨−α| and Y_L are **odd**.
- **Code-space rates** (κ_a only; in the {C±} basis a = A·Z_L + iB·Y_L, with A ≈ α and B ≈ αe^{−2α²}):
  - λ_X = 2κ_aα²·coth(2α²) (parity decay)
  - λ_Y = κ_aα²·(coth(2α²) + 1)
  - λ_Z = κ_aα²·(coth(2α²) − 1) ≈ 2κ_aα²e^{−4α²} (bit flip, channel 1)
  - So λ_Y = λ_X − λ_Z: **Y_L decays at Γ_Z − Γ_X**, the *lower* of the near-degenerate pair.
  - At α = 1.0 these give 0.1212 (even), 0.1190 (odd) and 0.0022, consistent with the anchors in §5.
- **The odd block is nonsingular only if κ_a > 0.** At κ_a = 0 the C₊/C₋ coherence is conserved. Guard against it.
- **When the symmetry breaks:** ε_Z or ε_x ≠ 0 breaks a → −a. Then use the full, deflated L (§9).

### §4.3 Readout symmetry
- With ε_Z(a+a†) on, the antiunitary symmetry maps the well at +α − iδ onto the well at −α − iδ, where δ = ε_Z/(2κ₂α²). Three things follow:
  - ⟨b⟩₋(t) = −⟨b⟩₊(t)*, **exactly**. Use it as a test.
  - The two one-way flip rates are **equal**, and ⟨Z_L⟩_ss = 0. There is **no "tilt" of the double well**.
  - P maps ε_Z → −ε_Z, so **Γ_X(ε_Z) is even in ε_Z**.
- Real asymmetry appears only when terms that break the antiunitary symmetry are added, such as the Kerr and Stark terms from 2.4a via `extra_H`.

---

## §5 Bit flips Γ_X

- **Convention (fixed):** Γ_X = decay rate of Re⟨a⟩ = −λ₁, the smallest-|λ| eigenvalue of the odd block, which is the prompt's 1/T_X.
  - This equals Ferrari et al.'s Γ_bf = −λ₁.
  - Dubovitskii's rate is **per direction**: Γ_Dub = −Re λ/2, so Γ_X = 2Γ_Dub.
  - The Felis provider gives per-Pauli X and Y rates (§10).
- **Two physical channels** (derived; consistent with Dubovitskii, arXiv:2407.17299, and Gautier et al., arXiv:2112.05545, Eq. 4):
  - **Channel 1, code space / Golden Rule:** Γ⁽¹⁾ = κ_aα²(coth 2α² − 1) ≈ 2κ_aα²e^{−4α²}, so **γ = 4**. This equals the naive Fermi Golden Rule with the direct matrix element |⟨−α|a|α⟩|² = α²e^{−4α²}.
    - It accounts for about **96%, 84%, 43% and 10%** of the one-mode λ₁ at α = 1.0, 1.4, 1.8 and 2.1.
  - **Channel 2, out of the code space and back:** Γ⁽²⁾ ≈ c·(κ_a²/κ₂)·e^{−2α²}, so **γ = 2**.
    - Dubovitskii's per-direction (κ₁²/2κ₂)e^{−2α²}, doubled to our convention, gives c = 1. A fit to the residual gives c ≈ 1.3.
    - Mechanism: one photon loss leaves the code space, then the confinement returns the state to the *other* well.
  - **Crossover:** α² ≈ ln(κ₂/κ_a)/2 ≈ 2.3.
  - So with n_th = 0 the local slope d ln Γ_X/d(α²) falls from about 4 toward 2. The earlier data showed about 3.1 at α = 1 to 1.4, and about 2.0 at 1.8 to 2.1.
  - This is why "γ ≲ 2" (deck) fails at small α in a thermal-free model, matching the prompt's own REVIEW note.
- **Identification experiment:** in the one-mode model, channel 1 is ∝ κ_a and channel 2 is ∝ κ_a². So the log-log slope d ln Γ_X / d ln κ_a at fixed α moves from about 1 (small α) to about 2 (large α).
- **Thermal photons** (Gautier et al., Eq. 4): Γ ≈ κ₁|α|²e^{−4|α|²} + κ_l e^{−2|α|²}, with κ_l = κ₁n_th + |α|²κ_φ.
  - Jumps: √(κ_a(1+n_th)) a and √(κ_a n_th) a†.
  - n_th adds an e^{−2α²} channel early. **Do not promise** that γ reaches the experimental value.
- **Experiment** (Réglade et al.): T_X grows ×4.2 per added photon, so γ ≈ ln 4.2 ≈ 1.44.
  - Ferrari et al. attribute the saturation to **cross-Kerr plus dephasing**, not to non-adiabaticity alone.
- **Two-mode vs one-mode:** the two-mode model flips faster, by about ×1.01 at α = 1, ×1.12 at 1.4, ×2 at 1.8 and ×3 at 2.1 (anchor).
  - Ferrari et al. 2026: non-adiabaticity "always lead[s] to higher values of Γbf".
- **Anchors (reproduce, don't trust)** come from the earlier scipy run, full L, shift-invert:

| α | one-mode N=40 | two-mode 20×6 | two-mode 28×8 | next pair (all) | 2κ_aα² |
|---|---|---|---|---|---|
| 1.0 | 2.2819e-3 | 2.3007e-3 | 2.3007e-3 | 0.118, 0.121 | 0.117 |
| 1.4 | 1.0744e-4 | 1.2020e-4 | 1.2021e-4 | 0.228, 0.228 | 0.229 |
| 1.8 | 2.0693e-6 | 4.1670e-6 | 4.0696e-6 | 0.378, 0.378 | 0.379 |
| 2.1 | 1.1699e-7 | **7.6070e-6 (truncation trap)** | 3.8831e-7 | 0.515, 0.515 | 0.515 |

  - At α = 2.1, Nb = 6: Na = 28, 32 and 36 all give 3.987e-7. Na = 20 is wrong at any Nb.
  - Going from Nb = 6 to 8 moves the result by 2.6%.
- **Time domain** is feasible only for α² ≲ 2 (α ≤ 1.4). Γ_X(2.1) ≈ 4e-7 /µs, i.e. seconds.
  - After t₀ ≈ 3 µs (the ringdown at κ_b/4), Re⟨a⟩ is a single exponential, because the symmetry keeps Y_L from being excited.
  - **A 50 to 100 µs window is enough.** Repeat at rtol 1e-8 and 1e-10.
  - α = 0.6 is not a double well (overlap e^{−2α²} = 0.49), so exclude it from fits.

---

## §6 Phase flips Γ_Z

- **Convention:** Γ_Z = decay rate of ⟨P⟩ (the prompt's 2κ_aα²). The per-direction rate is κ_aα² (Felis `k1*nbar`).
- **Prediction:** Γ_Z = 2κ_aα²·coth(2α²). That is 0.1212 /µs at α = 1.0, and 0.5154 /µs at α = 2.1. Compare also 2κ_a·n̄ with the measured n̄.
- **Steady-state parity is 1/cosh(2α²)** (0.266 at α = 1.0, 0.0396 at α = 1.4). So fit **A·e^{−Γt} + C** (`fit_exp_offset`). A pure exponential fit on log|y| is biased.
- **Thermal:** Γ_Z = 2κ_a[(1+2n_th)·n̄ + n_th]. The dropped +2κ_a·n_th term is 4.5% at α = 1, n_th = 0.05.
- **Existing result:** Task 1.3a fitted 0.5135 /µs at α = 2.1 (from vacuum inflation) against 0.5146 for 2κ_a·n̄.
- **Experiment:** Réglade et al. report a slope 25% larger than κ_a predicts, from effects beyond this model.

---

## §7 Readout and linear response

- **Steady state** (verified, Réglade Eq. S17; derived for our sign convention): ȧ = −i(2g₂a†b + ε_Z) gives b_ss = −ε_Z/(2g₂a*), i.e. **⟨b⟩_ss = ∓ε_Z/(2αg₂)** (minus for the +α well).
  - Both wells shift by −iε_Z/(2κ₂α²).
- **Measurement-induced dephasing** (verified, Réglade Eq. S18): Γ_Z^{εZ} = (κ_b/2)|ε_Z/(αg₂)|² = 2κ_b|⟨b⟩|² = 2ε_Z²/(κ₂α²).
  - This is back-action: reading Z_L must dephase X_L at the rate the information leaves through the buffer.
  - So **the readout's cost that matters is Γ_X**, not Γ_Z.
  - The identity also **validates** the SNR definition: SNR(T) = κ_b∫₀ᵀ|Δ⟨b⟩|²dt (ideal mode-matched heterodyne, unit efficiency).
- **Linearization** about ±α (b ≈ 0, κ_a neglected), with x = (δa, b):
  - Equations: δȧ = −2i·s·g₂α·b − iε_Z(t), and ḃ = −2i·s·g₂α·δa − (κ_b/2)b, where s = ±1 is the well.
  - Characteristic equation: λ² + (κ_b/2)λ + 4g₂²α² = 0, so **λ = −4.08 ± 19.72i /µs**.
  - That means ringing at **3.14 MHz** (period 0.32 µs), with **Q ≈ 2.46**.
  - It settles to **5% in 0.73 µs** and to **1% in 1.13 µs**, set by κ_b/4 alone.
  - It is underdamped **exactly when 8g₂α > κ_b**, which is Marquet et al.'s adiabaticity-breaking criterion. The one-mode model would predict about 20 ns.
  - The 1.13 µs matches the 1.07 µs settle time of Task 1.1. This explains the late ringdown, **not** the 56% overshoot magnitude, which is a large-signal effect from the saddle at the origin.
- **Transfer function:** H(s) = b/ε = −2g₂α/(s² + (κ_b/2)s + 4g₂²α²).
  - DC gain: −1/(2g₂α) = −0.0497 µs.
  - At resonance |H| ≈ Q × DC.
  - Consequence for 2.4c: the pulse spectrum against the 3.14 MHz pole matters.
- **Signal size:** at ε_Z = 0.1g₂, Δb ≈ 0.048 and SNR ≈ 0.04 at 1 µs. Useful SNR needs ε_Z ~ g₂, so sweep up to 3g₂.
- **Simulation protocol:** prepare each well (3 µs, ε_Z = 0), *then* switch ε_Z on. Subtract the common offset of about 0.003i that κ_a produces.

---

## §8 Circuit Hamiltonian (Task 2.4a)

- **The ATS term with the prompt's bias** (φ_Δ = π/2, φ_Σ = −π/2 + ε_p cos ω_pt): −2E_J cos(φ_Σ)cos(φ̂+φ_Δ) = +2E_J sin(ε_p cos ω_pt)·sin φ̂ ≈ 2E_Jε_p cos(ω_pt)·sin φ̂ (derived; check the sign algebra yourself).
- **Exact normal ordering** (BCH): e^{iφ̂} = e^{−Φ/2}·e^{iφ_a a†}e^{iφ_a a}e^{iφ_b b†}e^{iφ_b b}, with Φ = φ_a² + φ_b² = 0.0936 and e^{−Φ/2} = 0.9543.
  - So sin φ̂ = Σ over odd p+q+r+s of e^{−Φ/2}·i^{p+q+r+s−1}·φ_a^{p+q}φ_b^{r+s}/(p!q!r!s!) · a†^p a^q b†^r b^s.
- **g₂:** the pump splits as cos = (e^{iω_pt}+e^{−iω_pt})/2, so g₂ = **−½E_Jε_pφ_a²φ_b·e^{−Φ/2}**.
  - Combinatorics check: 2·½·3·(1/6) = ½.
  - Magnitude: 0.5·40000·0.035·0.0036·0.3·0.9543 MHz = 0.721 MHz. So ε_p ≈ **0.037** is needed for 0.763 MHz. The prompt's ε_p ≈ 0.035 ignores e^{−Φ/2}.
  - **Sign:** g₂ < 0 with this bias. Combined with −ε_d(b+b†) it gives α² < 0, which puts the cat on the imaginary axis. A pump phase of π, or flipping ε_d, restores it: a gauge choice.
  - **Factor ½:** present in Réglade and in our derivation. The iQuHACK 2025 tutorial (`Tutorial_2_Cat_Qubit_QED.ipynb`, https://github.com/iQuHACK/2025-Alice-and-Bob) writes g₂ = E_Jε_pφ_a²φ_b. Settle it numerically.
- **Resonances.** In units of 0.8 GHz, (ω_a, ω_b, ω_p) = (5, 6, 4). A term a†^p a^q b†^r b^s rotates at (p−q)ω_a + (r−s)ω_b, and is resonant with the pump when that equals ±ω_p, i.e. 5Δa + 6Δb = ±4 at odd order.
  - Through order 7, only the **a²b† family** is resonant, including number-dressed versions.
  - 3ω_p = 2ω_b, but parity forbids b†².
  - The nearest non-resonant terms are 0.8 GHz away.
- **Displaced frame first, then the RWA.** The order-1 pump term is a strong off-resonant drive:
  - On the memory: E_Jε_pφ_a ≈ 2π·84 MHz at 0.8 GHz detuning, so ξ_a ≈ 0.1.
  - On the buffer: E_Jε_pφ_b ≈ 2π·420 MHz at 1.6 GHz, so ξ_b ≈ 0.26 to 0.3.
  - Substituting a → a + ξ_a(t) gives Stark shifts (rough: memory about 2π·1 MHz, buffer about 2π·25 MHz), K_b ≈ 0.6 MHz, χ_ab ≈ 0.1 MHz and K_a ≈ 1 kHz.
  - These are rough review estimates, to be **computed properly**. Since they exceed g₂, **ω_p must be retuned**.
- **Parasitics:**
  - Réglade et al.: the linear buffer drive g_lin(b+b†) (cancelled with an opposite tone), g_sp(b†²b + b†b²), and spurious Kerr.
  - Ferrari et al.: cross-Kerr χ, which drives bit-flip saturation, with realistic K_b/2π = 1 MHz and χ/2π = 0.5 MHz.
- **How a readout drive enters:**
  - A capacitive drive at ω_a gives ε_Z(a+a†) plus counter-rotating terms at 2ω_a.
  - A second ATS flux tone at ω_a gives the linear term plus number-dependent terms (n̂a, ab†b, …) from cubic order.
- **Validation simulation:** dt ≲ 10 ps over **150 to 200 ns** of inflation (100 ns gives only about 0.5 rad of g₂ rotation), at Na ≈ 12 and Nb ≈ 5.

---

## §9 Numerics: the eigen-solver and time-domain recipes

- **Vectorization:** column-stacking. L = −i(I⊗H − Hᵀ⊗I) + Σ_J [J*⊗J − ½ I⊗J†J − ½ (J†J)ᵀ⊗I].
  - Composite index i = n_a·Nb + n_b; vector index k = i + D·j; D = Na·Nb.
- **Cost model** (fitted to the anchors; single-threaded SuperLU, so the same on this laptop): t ≈ 113 s·(Na·Nb²/1792)³ for the full L. **Nb is the expensive axis.**
  - The odd block is about 1/8 the time and 1/4 the RAM. So the **Z₂ split is required**, not optional.

| Truncation | Full L | Odd block |
|---|---|---|
| 32×12 | ≈30 min, 4–6 GB | ≈4 min |
| 40×8 | ≈5.5 min | |
| 48×8 | ≈9.5 min | ≈70 s |
| 40×12 | ≈1 h | (avoid) |

- **SciPy memory limit:** Beugnot et al. report that SciPy shift-invert "runs out of memory beyond a few hundred basis states". Ferrari et al. used 24×10. **Profile first** (L1).
- **Deflation** for ε ≠ 0 (no Z₂; Beugnot et al.): L′ = L + η|𝟙⟩⟩⟨⟨𝟙|.
  - The 0 eigenvalue moves to η·D, and traceless modes are unchanged.
  - The rank-1 term has only D² nonzeros.
  - Shift-invert at σ = 0 is then safe. On an *undeflated* full L, use a small **positive** σ.
- **Acceptance:**
  - Relative residual ‖Lv−λv‖/(|λ|‖v‖) < 1e-4. An absolute threshold is meaningless when λ₁ ~ 1e-7.
  - **Edge weight** (eigenvector weight on the top 2 memory or top buffer Fock levels) < 1e-6. This would have caught the 20×6 trap.
  - A left/right condition estimate.
  - Stable across two truncations.
- **Precision floors:**
  - Two-mode: ε_mach·‖L‖ ~ 1e-13.
  - One-mode: ‖L‖ ≈ κ₂N², about 3.6e4 at N = 80, so the floor is about 1e-11. Cap the one-mode curve at α ≈ 2.7, using the smallest converged N.
- **Speed levers (measure each one):**
  1. Z₂ blocks.
  2. A real representation of L in the Hermitian-matrix basis (2 to 4× faster, and needed for `pypardiso`, which is real-only).
  3. `splu(permc_spec='MMD_AT_PLUS_A')` through a custom `OPinv`.
  4. `pypardiso`.
- **Time-domain Γ_X:** as §5. 0.1·T_X at α = 1.4 would be 830 µs (2×10⁵ steps). Don't do it; use 50 to 100 µs after t₀ = 3 µs.
- **Gradient pulse optimization:** a few seconds per step at 16×4 to 20×5 with T = 2 µs.

---

## §10 Felis / qiskit-alice-bob-provider (verified against the source)

- **Package:** `qiskit-alice-bob-provider==3.0.0` (Oct 16, 2026). Needs Python ≥ 3.10 and < 3.14, qiskit ≥ 2.5 and < 3, qiskit-aer 0.17.x and pyqir 0.10.x, all with win_amd64 wheels. **Use a separate venv.**
- **Backends:** `AliceBobLocalProvider().get_backend('EMU:6Q:PHYSICAL_CATS', average_nb_photons=..., kappa_1=..., kappa_2=...)`. Rates are in **Hz**.
  - **There is no 1Q physical-cat backend.** The only 1-qubit one, `EMU:1Q:LESCANNE_2020`, is an interpolated model.
- **Formulas** (`qiskit_alice_bob_provider/processor/physical_cat.py`):
  - Idle X and Y: each `0.5*1.1e-3*nbar*k1*exp(-2*nbar)*t`. The 1.1e-3 was fitted at κ₁/κ₂ = 1e-2; there is **no κ₂ dependence**.
  - Idle Z: `k1*nbar*t`.
  - `utils.full_flip_error` converts these rates to probabilities: pX = ¼(1 + e^{−2(rY+rZ)t} − e^{−2(rX+rZ)t} − e^{−2(rX+rY)t}).
  - Measurement: `mz` has error e^{−1.5−0.9n̄} over 850 ns; `mx` has error n̄κ₁/κ₂ over 1/κ₂.
- **Limits:** n̄ ≥ 4, κ₁ ≥ 10 Hz, and 1e-7 ≤ κ₁/κ₂ ≤ 0.1. Ours, n̄ = 4.41 and κ₁/κ₂ = 0.0104, pass.
- **Cross-check (arithmetic):** at κ₁/κ₂ = 0.01 and n̄ = 4.41, the provider's total bit-flip rate 1.1e-3·n̄·κ₁e^{−2n̄} is within about 3% of channel 2. **Expected finding:** the emulator uses one-mode scaling and misses the ×3 two-mode correction.

---

## §11 Sources

- **Réglade, Bocquet et al.**, "Quantum control of a cat qubit with bit-flip times exceeding ten seconds", Nature 629, 778 (2024). arXiv:2307.06617; https://arxiv.org/html/2307.06617v2. Parameters (Table S2); Eq. S17 and S18; ×4.2 per photon; g₂ = ½E_Jε_pφ_a²φ_b; parasitic terms.
- **Ferrari, Cohen, Savona, Minganti**, "Bit flips, saturation, and quantum chaos in dissipative cat qubits", arXiv:2605.24100 (May 2026), https://arxiv.org/html/2605.24100. Γ_bf = −λ₁; κ_b/g₂ = 3 case; non-adiabaticity raises Γ_bf; saturation from cross-Kerr plus dephasing; 24×10 truncation.
- **Beugnot, Gregory, Robin, Tilloy**, "Well-conditioned iterative methods for large open quantum systems", arXiv:2608.30860 (Aug 2026), https://arxiv.org/html/2608.30860. λ₁ = bit flip and λ₂,₃ = phase flip; deflation ℒ + η·Tr(ρ)·Id; SciPy memory limits; the cat example uses our g₂, κ_b, κ_a.
- **Gautier, Sarlette, Mirrahimi**, "Combined dissipative and Hamiltonian confinement of cat qubits", PRX Quantum 3, 020339. arXiv:2112.05545, Eq. 4 (thermal and dephasing bit-flip formula).
- **Gautier, Mirrahimi, Sarlette**, "Designing high-fidelity Zeno gates for dissipative cat qubits", PRX Quantum 4, 040316. arXiv:2303.00760 (drive design, Gaussian pulses).
- **Dubovitskii**, "Bit-flip errors in dissipative cat qubits: second-order perturbation theory", PRA 111, 012617. arXiv:2407.17299 (two channels; Z-drive term (2ε_Z²/(κ₂α²))e^{−2α²} per direction).
- **Marquet et al.**, arXiv:2307.06761: adiabaticity breaks when 8g₂|α| > κ_b.
- **dynamiqs:** https://www.dynamiqs.org/stable/ and the v0.3.7 source.
- **Felis provider:** https://github.com/Alice-Bob-SW/qiskit-alice-bob-provider.
- **iQuHACK 2025 Alice & Bob:** https://github.com/iQuHACK/2025-Alice-and-Bob.

---

## §12 What we got wrong first (honest, presentable)

1. **1.3b:** the first plan used ε(a+a†) to "tilt" inflation toward +α. The antiunitary symmetry (§4.1) proves Re⟨a⟩ ≡ 0 under that drive. The fix is the real-axis drive i(a†−a).
2. **2.4b:** the first story was that "the readout drive tilts the double well and lowers one barrier". The symmetry (§4.3) makes both flip directions equal; the cost comes from population pushed out of the code space.
3. **Eigenvalue pair:** the first claim was that Y_L decays at Γ_Z + Γ_X. It actually decays at Γ_Z − Γ_X (§4.2).
4. **Γ_Z fit:** the first plan used a pure exponential, which is biased because the steady parity 1/cosh(2α²) ≠ 0.
5. **Capstone surrogate:** an adiabatic-⟨b⟩ surrogate would have deleted the very ringing the pulse is meant to beat. The fix is the 2×2 linear-response model (§7).
6. **Eigen acceptance:** an absolute residual threshold of 1e-8 is meaningless when λ₁ ~ 1e-7. Use relative residual plus edge weight.
7. **Truncation trap** (carried over from the feasibility study): 20×6 reports a 20× wrong Γ_X at α = 2.1.
