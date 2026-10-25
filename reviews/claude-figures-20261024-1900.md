# Claude figure check

Replaces the Gemini multimodal check (`ai_review.py --figures`), which stopped on the Gemini
free-tier daily quota. Claude read each of the 12 figures in `figures/` as an image and
compared what is drawn against the claims in docs/TECHNICAL.md and the numbers in `results/*.json`
(figures and results identical to the committed ones at `881d7f1`). Same method as the Gemini
prompt: read values off the axes, then list what a judge would notice. Triage pending.

**Summary:** 1 claim contradicted (claim 20, steady-state part), 1 minor overstatement (B7),
everything else supported. 7 presentation issues, none affecting a number.

| Figure | Claim | Verdict | Evidence |
|---|---|---|---|
| `task_1_0a_photon_number.png` | 1 | supported | curve and 4e^(−κt) overlap everywhere; title shows max error 9.7e-12 = `a.max_abs_error_vs_analytic` |
| `task_1_0a_wigner.png` | — | presentation | 6 panels with no times, axes or colour scale; the blob rotates (H = Δa†a) and shrinks toward the origin, which is right but unexplained |
| `task_1_0b_two_photon_loss.png` | 2 | supported | ⟨n⟩ falls from 4 to the dashed P_odd = 0.4998 line by ~0.5 µs and stays there to 3 µs |
| `task_1_0b_two_photon_loss.png` | 3 | supported | bars at n = 0 and 1 both ≈ 0.50, nothing visible at n ≥ 2 |
| `task_1_0c_kappa2_sweep.png` | 4 | supported | all three curves end at the α² line; κ₂/4 (blue) sits visibly just below it (4.387) |
| `task_1_0c_kappa2_sweep.png` | 5 | supported | right panel: the three curves coincide against κ₂t; reaching 90% (≈ 3.95) at κ₂t ≈ 0.86–0.90 |
| `task_1_0c_wigner.png` | — | presentation | no times on the panels (they are t = 0, 0.4, …, 2.0 µs: `wigner_mosaic(n=6)` picks 6 of the 11 saved states); fringes visibly fade across panels 2–6, which a reader may not expect from an "effective model" figure without a caption |
| `task_1_1_inflation.png` | 6 | supported | blue peak ≈ 6.9 at ≈ 0.23 µs, against the α² line at 4.41 |
| `task_1_1_inflation.png` | 7 | supported | last excursions outside ±1% are at ≈ 0.87 µs (≈ 4.5) and ≈ 1.0 µs (≈ 4.36); flat at 4.40 after |
| `task_1_1_inflation.png` | 8 | supported | green buffer peak ≈ 2.0 at ≈ 0.13 µs |
| `task_1_1_inflation.png` | 9 | supported | solid blue peaks ≈ 1.4e-5, solid orange ≈ 1.7e-4, both far below 1e-3 |
| `task_1_1_inflation.png` | 10 | supported | dashed starter peak ≈ 6.1; dashed red buffer monitor peaks ≈ 4.6e-2 |
| `task_1_1_inflation.png` | — | presentation | after ~1.5 µs every monitor turns into spikes between 1e-12 and ~1e-7. That is solver noise at the `atol = 1e-10` level (values near zero, some negative, clipped by the log axis), but it looks like an instability; say so in the caption or floor the y-axis at 1e-9 |
| `task_1_1_wigner.png` | — | presentation | times are in the title only; panels are not labelled individually and have no axes. Content is right: vacuum → squeezed → cat with fringes, fringes weaker at 3 µs |
| `task_1_2_convergence.png` | 11 | supported | orange steady markers sit on the dotted α² line on both panels |
| `task_1_2_convergence.png` | 12 | cannot tell from figure | at this y-scale all steady markers overlap; the 0.1% statement needs the table, not the plot |
| `task_1_2_convergence.png` | 13 | supported | left: peak flat from N_a = 24 (6.88) on; right: rises steeply to N_b = 10 (6.87), flat after |
| `task_1_2_grid.png` | 20 (peak) | supported | 24×10 cell 0.41% (bold, cheapest bold cell), 32×12 cell 0.035%; rows and columns each saturate |
| `task_1_2_grid.png` | 20 (steady) | **contradicted** | the N_a = 20 column of the steady panel reads 3e-05 (N_b = 4), 1e-05 (N_b = 6, 8): above the claimed "within 1e-5 for every N_a ≥ 20 at any N_b". JSON agrees: max 2.9e-5 at 20×4, 1.2e-5 at 20×6. True for N_a ≥ 24 (max 4e-6) |
| `task_1_2_grid.png` | — | presentation | cells mix units: "0.021%" next to "2e-05" (a plain fraction, = 0.002%). A judge can read "2e-05" as a percent. Use one format, e.g. all percent |
| `task_1_3a_cat_diagnostics.png` | 14 | supported | orange Re⟨a⟩ is flat at 0 for the whole 6 µs |
| `task_1_3a_cat_diagnostics.png` | 15, 19 | supported | dashed fit lies on the parity curve from 1 µs; legend Γ = 0.513 (pred. 0.515) |
| `task_1_3a_cat_diagnostics.png` | 16 | supported | at 1 µs parity ≈ 0.63, 2·coherence ≈ 0.63, purity ≈ 0.69 |
| `task_1_3a_cat_diagnostics.png` | 17 | supported | parity at t ≈ 1 + 1.95 µs is ≈ 0.63/e ≈ 0.23 (reads ≈ 0.23 at 3 µs) |
| `task_1_3a_cat_diagnostics.png` | 18 | supported | at 6 µs parity ≈ 0.05, 2·coherence ≈ 0.05, purity on the 0.5 line |
| `task_1_3a_cat_diagnostics.png` | §4 text | supported | purity dips to ≈ 0.59 at ≈ 0.3 µs; fidelity with C₊ peaks ≈ 0.85 at ≈ 0.6 µs |
| `task_1_3a_cat_diagnostics.png` | — | presentation | right-panel legend shows raw "ρ_a" (underscore not rendered); the "(1 = cat)" label invites the question why the curve never exceeds 0.74 — add "(reduced by parity lost during inflation)" |
| `task_1_3a_wigner_fading.png` | 18 | supported | fringe contrast drops panel by panel and is nearly gone at 6 µs while the two blobs stay |
| `task_1_3a_wigner_fading.png` | — | presentation | title writes "kappa_a" in plain text; use κ_a |
| `task_1_3b_logical_prep.png` | B1, B3 | supported | panel A at 2 µs: β = 0 → 0.50, 0.5 → 0.84, 1.0 → 0.98, 1.5 → ≈ 1.0, 2.1 → 1.0 (flat), 3.0 → ≈ 1.0 |
| `task_1_3b_logical_prep.png` | B2 | supported | red (1.5) stays above the 0.99 line from ≈ 0.4 µs, brown (3.0) from ≈ 0.5 µs |
| `task_1_3b_logical_prep.png` | B4 | supported | middle panel: stabilized 1.00 / 0.995 / 0.97 at 15/30/45°, bare 0.74 / 0.31 / 0.08 |
| `task_1_3b_logical_prep.png` | B5 | cannot tell from figure | panel B plots Re⟨a⟩/α (0.57 / 0.88 / 0.99), not F; the F values are only in the JSON. Either plot F or say "F in the table" in the caption |
| `task_1_3b_logical_prep.png` | B6 | supported | dashed control stays at Re⟨a⟩/α = 0 |
| `task_1_3b_logical_prep.png` | B5 text | supported | green (ε = 20) overshoots to Re⟨a⟩/α ≈ 1.38, consistent with the stated peak ⟨n_a⟩ 8.5 |

## Checked against the JSON only (not visible in any figure)

| Claim | Verdict | Evidence |
|---|---|---|
| B7 "max memory top-2 population ≤ 3e-5" | minor overstatement | `A2_phase[75°].max_top2_a` = 3.11e-5. Write "≤ 3.1e-5" (or "≲ 3e-5") |
| 16, 18 source key | label mismatch | `task_1_3a.json → at_1us.coherence` is 0.313, i.e. \|⟨α\|ρ\|−α⟩\| without the factor 2; the claims quote 2× (0.63, 0.05). Say "2 × coherence" in the source column so a judge finds the number |
| §4 "purity dips to ~0.6 at 0.3 µs" | no JSON source | `min_purity` / `t_min_purity_us` give the global minimum (0.501 at 6 µs), not the early dip. Visible in the figure, but not backed by a saved number |

## Triage (same evening)

Acted on all of the above: docs/TECHNICAL.md claims 11, 16, 18, 20, B7 and §4 corrected or
sourced; Wigner panels now carry their times; the grid prints every cell in percent; the
1.1 monitor axis stops at 1e-9 and its title names the solver-noise wiggles; `ρ_a`, `κ_a`
render as math. The B5 figure still plots Re⟨a⟩/α (F stays in the table). All figures were
regenerated locally (Apple M2); every reported quantity matched the committed results to ≤ 1e-10 relative, the truncation monitors to ≤ 2e-6.
