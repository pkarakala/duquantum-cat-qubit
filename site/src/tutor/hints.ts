/** Public hint ladder only. The hidden solution never ships to the browser. */

export const HINTS: Record<string, [string, string, string, string]> = {
  L1: [
    "What do you predict?",
    "Watch the histogram's centre as you move α.",
    "Compare α = 1 and α = 2.",
    "⟨n⟩ = α²: solve α² = 4.41.",
  ],
  L2: [
    "Predict first.",
    "Look at the dashed analytic curve.",
    "Compare κ = 0 and a large κ.",
    "Set e^{−κ·0.5} = ½.",
  ],
  L3: ["Predict.", "Watch the parity meter.", "Try starting in Fock |3⟩: where does it end?", "Use the plateau formula."],
  L4: [
    "Predict.",
    "Look between the blobs.",
    "Compare a 50/50 mixture (toggle).",
    "Parity = +1 means even photon numbers only.",
  ],
  L5: ["Predict.", "Read both curves at your α².", "Try α² = 1 vs 5.", "T_Z = 1/(2κ_aα²)."],
  L6: [
    "Predict.",
    "Which block lets energy leave?",
    "Compare with/without √κ_b·b.",
    "Two memory photons ↔ one buffer photon: a²b†.",
  ],
  L7: ["Predict.", "Watch the first 0.5 µs.", "Compare the two valleys.", "Signal size goes as ε_Z/(2αg₂)."],
  L8: ["Predict.", "Look at the spectrum.", "Try a ramp vs a square.", "Put energy near the ring frequency."],
};
