# Levels: content source of truth for lane P2 (and the tutor's grounding)

**Every level runs the same loop:** concept card (narrated), then **predict** (a gate before anything runs), then **play**, then **check**, then **aha** and "Show the code".

**Design rules:**
- **PhET:** ≤ 3 visible controls, each with a 1–3 word label. Every change shows immediately. Play and pause are obvious. Representations are linked.
- **Katas:** every level has a `check()`.
- **Tutor grounding:**
  - The hidden `solution` steps and scripted `hints` below are what the tutor is grounded in.
  - The "allowed constants" are the only numbers the tutor may say without a tool call.
  - Units are always shown, with time in µs.

**Feedback defaults:**
- An option listed without its own feedback shows its misconception's "fix in one line" from the table below.
- If it has no misconception either, it shows the level's aha sentence.
- Every level spec must carry `allowedConstants` (the tutor's number guard) and, where listed, the follow-up prediction and the second check part (CONTRACT §7).

## Misconception library
| ID | Misconception | Fix in one line |
|---|---|---|
| M1 | "A superposition is just a 50/50 mixture" | The fringes (negative regions) exist only for the superposition. A mixture shows two blobs and no stripes. |
| M2 | "The Wigner function is a probability" | It can go negative. Negativity is the quantum fingerprint. |
| M3 | "Dissipation always destroys quantum information" | Engineered *two-photon* dissipation creates the cat and protects it. |
| M4 | "More photons protect against every error" | Bit flips drop exponentially, but phase flips grow linearly. |
| M5 | "Losing a photon causes a bit flip" | It flips parity, which is a **phase** flip. The blob stays in its well. |
| M6 | "Reading a qubit is instant and free" | The buffer rings and takes about 1 µs to settle. Measuring dephases the qubit. |
| M7 | "The relative phase (the sign) is unobservable" | C₊ and C₋ differ only by a sign, and their fringes (parity) are opposite. |

---

## L1 · A box of light (5 min) · engine `ts`
- **Concept:** a superconducting resonator holds microwave photons. A *coherent state* |α⟩ is the quantum version of a steady swing. Its average photon number is |α|², but each measurement gives a different count. The Wigner map shows it as a round blob at distance α from the centre.
- **Predict:** "For α = 2, what is the average number of photons?"
  - A) 2. Feedback: "Close, but the photon number goes as α²."
  - **B) 4** (correct).
  - C) Exactly 4, every time. This is the "number is definite" error. Feedback: "On average 4, but each count varies (Poisson)."
  - D) 0.
- **Controls:** `α` (0–3); `State` (Coherent or Fock n); `n` (0–6, Fock only).
- **Views:** a photon-number histogram and the Wigner map, linked.
- **Check:** "Make a state with an average of 4.41 photons." Pass if |α| is in [2.08, 2.12].
- **Aha:** "Amplitude and phase are sharp; the photon count is fuzzy. That round blob *is* a coherent state, and α = 2.1 is Alice & Bob's operating point."
- **Show code:** `psi = dq.coherent(30, alpha)`.
- **Solution:**
  1. ⟨n⟩ = |α|².
  2. 4.41 = 2.1².
- **Hints:**
  1. "What do you predict?"
  2. "Watch the histogram's centre as you move α."
  3. "Compare α = 1 and α = 2."
  4. "⟨n⟩ = α²: solve α² = 4.41."
- **Allowed constants:** 2.1, 4.41, 4.
- **Preset:** `L1`.
- **Sources:** challenge prompt §B.3–B.5.

## L2 · The leaky box (6 min) · engine `ts`
- **Concept:** real resonators leak single photons at rate κ.
  - The Hamiltonian H = Δa†a makes the blob rotate. Here Δ/2π = 1 MHz, so one turn per µs.
  - The jump operator √κ·a removes one photon at a time.
- **Predict:** "Start at α = 2 and turn on loss. What happens to the blob?"
  - **A) It shrinks and stays round** (correct).
  - B) It gets lopsided (M3).
  - C) It splits in two.
  - D) Nothing.
- **Controls:** `Loss κ` (0–2π·1 MHz); `Rotate` (on/off); ▶.
- **Views:** n(t) with the analytic 4e^{−κt} overlaid, and the Wigner spiral, linked.
- **Check:** "Pick κ so that ⟨n⟩ halves at t = 0.5 µs." Pass if κ is in [1.32, 1.46] rad/µs, i.e. ln 2/0.5 = 1.386 rad/µs (κ/2π ≈ 0.22 MHz).
- **Aha:** "A coherent state stays coherent while it leaks: losing a photon doesn't change it, it just shrinks. This matches our Task 1.0a check to 1e-11."
- **Show code:** `dq.mesolve(Delta*a.dag()@a, [jnp.sqrt(kappa)*a], dq.coherent(N, 2.0), t)`.
- **Solution:**
  1. ⟨n⟩ = 4e^{−κt}.
  2. Halving needs κt = ln 2.
- **Hints:**
  1. "Predict first."
  2. "Look at the dashed analytic curve."
  3. "Compare κ = 0 and a large κ."
  4. "Set e^{−κ·0.5} = ½."
- **Allowed constants:** 4, 0.5, 1.386, 0.693.
- **Preset:** `L2`.
- **Sources:** `t1_0.max_abs_error.td.one_mode.a2.00`.

## L3 · Two at a time (6 min) · engine `ts`
- **Concept:** what if the box can only lose photons **in pairs**? The jump operator is √κ₂·a², where κ₂/2π = 0.896 MHz.
- **Predict:** "Start at α = 2 with pair-loss only. Where does ⟨n⟩ end up?"
  - A) 0 (M3).
  - **B) About 0.5** (correct).
  - C) It stays at 4.
  - D) 2.
- **Controls:** `Start α` (0.5–2.5); `Pair loss κ₂` (×¼, ×1, ×4); ▶.
- **Views:** n(t), the final Fock histogram (only |0⟩ and |1⟩ survive), and a **parity meter that never moves**.
- **Check:** "Make the plateau land at 0.45." Pass if the plateau is in [0.43, 0.47].
  - Plateau = (1 − e^{−2α²})/2, so this needs α ≈ 1.07.
- **Aha:** "Pairs can't remove the last odd photon. Photon-number **parity is frozen**. That is the secret ingredient of a cat qubit. (Our Task 1.0b plateau: 0.49983, which matches theory to 1e-14.)"
- **Show code:** `dq.mesolve(dq.zeros(N), [jnp.sqrt(kappa_2)*a@a], dq.coherent(N, alpha), t)`.
- **Solution:**
  1. a² maps n → n−2, so parity is conserved.
  2. The odd part of |α⟩ ends in |1⟩ and the even part in |0⟩.
  3. ⟨n⟩_∞ = P_odd = (1 − e^{−2α²})/2.
- **Hints:**
  1. "Predict."
  2. "Watch the parity meter."
  3. "Try starting in Fock |3⟩: where does it end?"
  4. "Use the plateau formula."
- **Allowed constants:** 0.5, 0.49983, 0.45, 1.07, 0.896.
- **Preset:** `L3`.
- **Sources:** `t1_0.n_plateau.td.one_mode.a2.00`.

## L4 · The cat appears (7 min) · engine `ts`
- **Concept:** remove pairs **and** add pairs. The jump operator becomes √κ₂(a² − α²). It is balanced at ±α: two valleys, which are our |0⟩ and |1⟩. Start from the empty box.
- **Predict:** "Starting empty, what will the Wigner map look like?"
  - A) One blob.
  - B) Two blobs, no stripes (M1).
  - **C) Two blobs plus stripes between them** (correct).
  - D) A ring.
- **Controls:** `α` (1–2.5); `Photon loss` (off, or on ×20 "exaggerated"); ▶.
- **Views:** a Wigner animation, n(t) and parity(t), linked.
- **Check, part 1:** "Grow a cat with ⟨n⟩ ≈ 4.41 and parity > 0.9 at t = 1 µs, with loss off." Pass if ⟨n⟩ is in [4.3, 4.5] and parity > 0.9.
- **Check, part 2:** "Turn loss on. What fades first?" The answer is the fringes and the parity.
- **Aha:**
  - "The stripes go negative, so this is a true superposition: an even cat (M1, M2)."
  - "The empty box is even, so you always get the *even* cat (M7)."
  - "Losing one photon flips parity: that's a **phase flip**, not a bit flip (M5)."
- **Show code:** `jumps = [jnp.sqrt(kappa_2)*(a@a - alpha**2*dq.eye(N)), jnp.sqrt(kappa_a)*a]`.
- **Solution:**
  1. Pair processes conserve parity, and vacuum has P = +1, so the state goes to C₊.
  2. With κ_a on, parity decays at about 2κ_aα².
- **Hints:**
  1. "Predict."
  2. "Look between the blobs."
  3. "Compare a 50/50 mixture (toggle)."
  4. "Parity = +1 means even photon numbers only."
- **Allowed constants:** 4.41, 0.9, 1.0.
- **Preset:** `L4`.
- **Sources:** `t1_3a.gamma_z.td.two_mode.a2.10`, `t1_0.final_n.td.one_mode.a2.10`.

## L5 · Flip vs flip (6 min) · engine `records` (verified grid, no live sim)
- **Concept:**
  - A bit flip means hopping from one valley to the other. Bigger cats sit in valleys that are farther apart, so bit flips become exponentially rarer.
  - A phase flip happens every time a photon leaks. Bigger cats hold more photons, so phase flips grow linearly.
- **Predict:** "Double the photon number. Bit flips become…"
  - A) About 2× rarer.
  - **B) Vastly rarer, orders of magnitude** (correct).
  - C) More common (M4).
  - Follow-up question: "…and phase flips?" The answer is "more common".
- **Controls:** `Cat size α²` (1–9); `Model` (one-mode or real two-mode).
- **Views:** log T_X and T_Z against α² from **verified records**, each with a provenance chip; a bias meter; a double-well sketch; the Wigner at the chosen α.
- **Check:** "Design a qubit with T_X > 1 ms **and** T_Z > 1 µs." The pass window is computed from records at runtime. T_Z = 1/(2κ_aα²) > 1 µs means α² < 8.56; the T_X bound comes from the Γ_X records.
- **Aha:** "Noise bias is a design choice. That's why Alice & Bob only need a simple repetition code (Felis: 60–200× fewer qubits). Our two-mode model flips about 3× faster than the simple model at α = 2.1, which is real hardware physics (Ferrari et al. 2026)."
- **Show code:** `gamma_x = spectral.gamma_x(H, jumps, Na, Nb)["gamma_x"]   # Liouvillian gap`.
- **Solution:**
  1. Γ_X ≈ 2κ_aα²e^{−4α²} + (κ_a²/κ₂)e^{−2α²}.
  2. Γ_Z = 2κ_aα² coth 2α².
  3. Pick α² inside both bounds.
- **Hints:**
  1. "Predict."
  2. "Read both curves at your α²."
  3. "Try α² = 1 vs 5."
  4. "T_Z = 1/(2κ_aα²)."
- **Allowed constants:** 8.56, 1 ms, 1 µs, 3, 60, 200.
- **Preset:** `L5` (records snapshot).
- **Sources:** `t2_1.gamma_x.eig.*`, `t2_2.gamma_z.td.*`.

## L6 · Build the machine (8 min) · engine `server-expr` (Vultr), with fallback preset `L6`
- **Concept:** in hardware, a second leaky resonator (the **buffer**, b) makes the pairs.
  - The coupling g₂ swaps 2 memory photons for 1 buffer photon.
  - A buffer drive ε_d pumps pairs in.
  - Buffer loss κ_b dumps them.
  - Build it from blocks.
- **Predict:** "Will the memory fill smoothly like L4?"
  - A) Yes, smoothly.
  - **B) It overshoots, then settles** (correct).
  - C) It never fills.
- **Controls:** a **block canvas** with palette `a, a†, b, b†, ×, +, g₂, ε_d, √κ_b, √κ_a, Kerr K`, plus ▶ Run on Vultr.
- **Views:** n_a(t) and n_b(t) with the L4 curve overlaid; Wigner frames; a **truncation meter** that teaches convergence.
- **Check:** "Your blocks stabilize a cat." Pass if the steady ⟨n_a⟩ is within 2% of 4.41.
  - **This works at the live size Na = 16, Nb = 5.** The steady state already converges at Na = 16, Nb = 4 to 0.1% (Task 1.2: steady 4.4026). The transient peak does **not** converge at 16×5 (about 6.4 vs 6.89 converged), and the truncation meter shows exactly that, which is a convergence lesson.
  - Never widen the window.
  - Common wrong builds get tutor explanations:
    - ε(a+a†) instead of the buffer drive. It pushes along the separatrix and can't make a cat (RESEARCH §4.1).
    - Missing √κ_b·b, so nothing dissipates.
    - Swapping a²b† for a b†².
- **Aha:**
  - "Real hardware overshoots by about 56%, because the buffer isn't fast enough (κ_b ≫ g₂ is violated: g₂/κ_b = 0.29)."
  - "And the textbook simulation size (6 buffer levels) underestimates the peak by 11%. Convergence matters (our Task 1.2)."
- **Show code:** `H = g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())`, generated from the blocks by `toPython`.
- **Solution:**
  1. H = g₂(a²b† + a†²b) − ε_d(b+b†), with jumps √κ_b·b and √κ_a·a.
  2. α² = ε_d/g₂.
  3. A slow buffer causes the overshoot.
- **Hints:**
  1. "Predict."
  2. "Which block lets energy leave?"
  3. "Compare with/without √κ_b·b."
  4. "Two memory photons ↔ one buffer photon: a²b†."
- **Allowed constants:** 4.41, 56%, 0.29, 11%, 6.89 (peak), 1.07 µs.
- **Preset:** `L6`.
- **Sources:** `t1_1.peak_na.td.two_mode.a2.10`, `t1_1.steady_na.td.two_mode.a2.10`.

## L7 · Read the cat (7 min) · engine `records` + server grid (`t2_3` arrays), fallback preset `L7`
- **Concept:** to read 0 or 1 without a transmon, nudge the memory with a small drive ε_Z. The buffer field then leans **opposite ways** for the two valleys.
- **Predict:** "After switching the readout on, the buffer signal…"
  - A) Settles smoothly (M6). Feedback: "It actually rings for about 1 µs. Reading takes time."
  - **B) Rings, then settles** (correct).
  - C) Stays zero. Feedback: "The two valleys push the buffer opposite ways, so there is a signal."
- **Controls:** `Readout ε_Z` (grid 0.05–3 g₂); `Valley` (0 or 1); ▶.
- **Views:** IQ trajectories of ⟨b⟩ for both valleys; Re and Im against t with the analytic ringing overlaid; an SNR meter; a "cost" meter (back-action).
- **Check:** "Get an SNR ≥ 1 within 1 µs." Pass is read from the grid.
- **Aha:**
  - "It rings at 3.14 MHz and needs about 1.1 µs to settle, because memory and buffer form a lightly damped pair (8g₂α > κ_b)."
  - "Reading costs something. Measuring dephases the qubit at 2ε_Z²/(κ₂α²), so harder driving reads faster but disturbs the cat."
- **Show code:** `H = H + eps_z*(a + a.dag())`.
- **Solution:**
  1. b_ss = ∓ε_Z/(2αg₂).
  2. λ² + (κ_b/2)λ + 4g₂²α² = 0, giving λ = −4.08 ± 19.7i /µs.
- **Hints:**
  1. "Predict."
  2. "Watch the first 0.5 µs."
  3. "Compare the two valleys."
  4. "Signal size goes as ε_Z/(2αg₂)."
- **Allowed constants:** 3.14 MHz, 1.13 µs, 0.73 µs, 2.46.
- **Preset:** `L7`.
- **Sources:** `t2_3.*` records.

## L8 · Design challenge (8 min) · engine `ts` (`linresp.ts`) for scoring; server recomputes for the leaderboard
- **Concept:** design the readout pulse. You get 20 bars of drive strength over 1 µs. Maximize signal (SNR) without spending more than the bit-flip budget.
- **Predict:** "Which beats a flat (square) pulse at the same budget?"
  - A) Nothing: square is best.
  - **B) A shaped pulse** (correct).
  - C) A bigger square pulse. That breaks the budget.
- **Controls:** a **pulse editor** (drag the bars); a `Budget` meter; ▶ Score.
- **Views:** the pulse and its spectrum, with the 3.14 MHz ring marked; the signal; SNR against budget; the leaderboard.
- **Check:** "Beat the square pulse at equal budget." Pass when `snr(yours) > snr(square)` and `cost(yours) ≤ cost(square)`.
- **Aha:** "Our provably optimal pulse is the top singular vector of the system's response. It puts its energy near the 3.14 MHz ring. You just did optimal control." The page then compares with our SVD pulse from `t2_4c`.
- **On completion:**
  - Leaderboard: POST, and the server recomputes the score.
  - **Claim your "Cat Qubit Architect" credential** on Solana devnet (wallet optional).
  - Unlock Real Research.
- **Show code:** `eps_bins, gain = linresp.optimal_pulse(R_b)`.
- **Solution:**
  1. SNR = κ_b∫|Δb|²dt.
  2. Response is linear in ε.
  3. Optimum = top singular vector at fixed energy.
- **Hints:**
  1. "Predict."
  2. "Look at the spectrum."
  3. "Try a ramp vs a square."
  4. "Put energy near the ring frequency."
- **Allowed constants:** 3.14 MHz, 20, 1 µs.
- **Preset:** `L8`.
- **Sources:** `t2_4c.*` records.

---

## Allowed level constants for the number guard
These are the union of each level's "allowed constants": 2.1, 4.41, 4, 0.5, 1.386, 0.693, 0.49983, 0.45, 1.07, 0.896, 0.9, 1.0, 8.56, 3, 60, 200, 56, 0.29, 11, 6.89, 3.14, 1.13, 0.73, 2.46, 20. Anything else must come from a tool result or record.
