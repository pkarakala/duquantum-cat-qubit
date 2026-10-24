# Harshit's track (not delegable)

Judges score "your understanding and **your** ownership of the reasoning, not an LLM's". This file is about 3 focused hours spread across the night. Do it as you go, not at the end.

## 1. Now (~6:00 PM): comms
- **Message to Pranav** (edit as you like): "I'm submitting us to the Standard Track (judged on Section 2), and finishing 1.3b/c too. The work is on the new branch `standard-track` (cut from `intro-track-tasks`). The plan for Cursor agents is in `docs/plan/`. Could you: (1) leave README/TECHNICAL to my docs lane, (2) push to `intro-track-tasks` only (I'll merge it in), (3) make the repo public, or add the judges, by 10:30 AM Sunday, and (4) tell me if you want to present a part?"
- **Ask the Alice & Bob mentors:**
  1. Is a Standard team's 1.3b/c work judged?
  2. The prompt notes that a thermal-free model gives γ > 2, while the deck says γ ≲ 2. Do you want it explained, thermal photons added, or both?
  3. Is the v4 prompt final? Our copy still has REVIEW notes.
  4. Is a cross-check against your Felis emulator welcome?
  5. Is there a preferred readout metric (SNR, fidelity in time T)? Is "ε_Z ≪ g₂" binding, given that the SNR is tiny there?
- **Check access:** `gh auth status` (needs the `workflow` scope to push Actions files) and `gh repo view pkarakala/duquantum-cat-qubit --json viewerPermission`.
- **Discord:** watch for the Devpost join link.

## 2. Learn the core pictures (30 min, before 9 PM)
- Read `notes/duq plan.md`, section "Cat qubits in plain English" (local only).
- Then open `prep/cat-qubit-workbook.html`, tabs 3a to 4.
- Be able to draw three pictures from memory:
  1. The double well at ±α.
  2. The Wigner function of a cat (two blobs plus fringes) vs a mixture (no fringes).
  3. What a jump operator does: √κ a removes one photon, so the parity flips.

## 3. Three derivations by hand (photograph each into `docs/handwritten/`)
1. **Buffer elimination.**
   - Start from H = g₂a²b† + g₂a†²b − ε_d(b+b†) with buffer loss κ_b.
   - Buffer: ḃ = −i(g₂a² − ε_d) − (κ_b/2)b. A fast buffer means ḃ ≈ 0, so b ≈ −(2i/κ_b)(g₂a² − ε_d).
   - Memory: ȧ = −2ig₂a†b = −(4g₂²/κ_b)a†(a² − ε_d/g₂).
   - So **κ₂ = 4g₂²/κ_b** (0.896 MHz) and **α² = ε_d/g₂**.
   - Why it fails here: κ_b/g₂ = 3.4 is not ≫ 1.
2. **Readout, and why it rings.**
   - Add ε_Z(a+a†): ȧ = −i(2g₂a†b + ε_Z). In steady state, b = −ε_Z/(2g₂a*), so **⟨b⟩ = ∓ε_Z/(2αg₂)**.
   - Linearize with a = ±α + δa: δȧ = ∓2ig₂α·b − iε_Z and ḃ = ∓2ig₂α·δa − (κ_b/2)b.
   - That gives λ² + (κ_b/2)λ + 4g₂²α² = 0, so **λ = −4.08 ± 19.7i /µs**: it rings at 3.14 MHz and settles to 1% in about 1.1 µs.
   - It is underdamped exactly when 8g₂α > κ_b (here 80.5 > 16.3).
3. **Why "γ ≲ 2" fails at small α (two channels).**
   - Naive Golden Rule: Γ ∝ κ_a|⟨−α|a|α⟩|² = κ_aα²e^{−4α²}, so **γ = 4** (channel 1, exact form κ_aα²(coth2α² − 1)).
   - Channel 2: one photon loss takes the state out of the code space, then the confinement returns it to the *other* well. That gives Γ ∝ (κ_a²/κ₂)e^{−2α²}, so **γ = 2**.
   - They cross at α² ≈ ln(κ₂/κ_a)/2 ≈ 2.3. So the measured γ goes from about 3 to 2.
   - Proof: in the κ_a sweep, the exponent of κ_a moves from 1 to 2.

## 4. Explain-back (after each merge of a talk lane: 2.1, 2.2, 2.3, 2.4a, 2.4c, 1.3b)
- Each lane's status file ends with 3 hardest questions, and `docs/defense_questions.md` collects about 15.
- **Answer them in your own words** in `docs/defense.md`, in 5 lines or less each, pointing at a figure.
- If you can't answer one after 10 minutes with the figure open, flag it and ask Claude to review that lane (`REVIEW_PROTOCOL.md`). Do not present it blind.

## 5. Sleep: about 2:00 to 6:00 AM
Before sleeping, check these with the integrator:
- The queue is running (`tools.runq status`).
- The morning-brief time is set.
- Nothing is waiting on you.

## 6. Talk: 8 minutes, solo
| Time | Segment | On screen |
|---|---|---|
| 0:00–0:40 | Hook: a cat inflating from empty; what a cat qubit buys you | Lab, Inflate page |
| 0:40–1:20 | The trade-off (bit flips down exponentially, phase flips up linearly) and our one-sentence claim | double-well sketch |
| 1:20–2:20 | How we verified: provenance cards, convergence, the 20×6 truncation trap, symmetry tests | Lab, Verification page |
| 2:20–4:10 | Γ_X two ways (eigen vs time domain), two channels (γ 4 → 2) with the κ_a sweep, two-mode vs one-mode (non-adiabatic ×3) | Lab, Error budget page |
| 4:10–5:00 | Γ_Z matches 2κ_aα²coth2α²; the buffer **rings** (3.14 MHz, analytic vs simulation) | readout signals |
| 5:00–6:40 | Capstone: the trade-off curve, then the SVD-optimal pulse vs the square pulse at matched cost, verified on the full model | Lab, Readout designer |
| 6:40–7:30 | What we got wrong first (the ε(a+a†) prep, the "tilt" story, the Y_L rate) and how we used AI | one slide |
| 7:30–8:00 | Close: the result in one line, plus the Lab link | QR code |

## 7. Video (≤4:00, recorded by 10:00 AM)
- Follow `docs/video_script.md`. Record a screen capture of the Lab with Win+Alt+R, or OBS.
- Narrate live. ElevenLabs is optional, and is also MLH prize bait.
- Upload to Devpost by 10:30.

## 8. Devpost (submit by 10:45 AM)
Use the text in `docs/devpost.md`, the public repo link, the video, and the Lab link (Pages URL, or say "open site/dist-single/index.html").

## 9. Publish and scrub checklist (before the repo goes public)
- [ ] `git ls-files notes` is empty (`notes/` is ignored; never commit it).
- [ ] No API keys in the repo: `rg -n "AIza|xai-|sk-" .`
- [ ] Decide whether to keep `docs/plan/`, `AGENTS.md` and `.cursor/`. Keeping them is honest AI-use transparency; removing them is cleaner. Our recommendation is **keep**, and point to them from the README's "How we used AI" section.
- [ ] `prep/HANDOFF.md` mentions an organizer's Discord handle. That's low risk, so keep or trim it.
- [ ] The notebooks have been re-executed locally, so there are no `/home/claude/...` paths.
- [ ] The README "How we used AI" section is accurate: Claude Code planned, Cursor agents implemented, Gemini reviewed, and Harshit derived, verified and presents.
- [ ] Pranav has made the repo public, or added the judges.

## 10. Rehearse (10:45 to 11:45 AM)
Do two timed run-throughs. Then answer 3 hostile questions per lane aloud, without notes.
