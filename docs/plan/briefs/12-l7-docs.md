# Brief `l7-docs`: README, TECHNICAL, defense questions, deck, video script, Devpost text

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l7-docs`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/12-l7-docs.md`, then execute this brief exactly. Keep `docs/plan/status/l7-docs.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l7-docs` | `std/l7-docs` (from `standard-track`) | `l0-tools` (`tools/check_claims.py`, the 9 wrapped intro records `t1_*`) + whatever physics lanes are merged into `standard-track` at each pass (`l2a`, `l2b`, `l3`, `l4a`, `l5`, `l4b`, `l4c`, `l8`; `l6` for the Lab link) | fast model for drafting; **strongest** model for the final consistency pass | 2.5 h total (draft ≤ 1.5 h, final ≤ 1 h) | Draft from **10:00 PM Sat** on merged lanes; final pass **8:00–10:00 AM Sun** after the 8:00 physics freeze. `docs/video_script.md` final by **9:00 AM** (Harshit records by 10:00), `docs/devpost.md` by **9:30 AM**, everything committed by **10:00 AM** |

## 1. Goal and why
Judges score "correctness of the physics and the numerics (including convergence checks), clarity of code and documentation, quality of the presentation" (prompt §0.4). AI use is allowed only if "(i) you state in your README where and how you used them, and (ii) your team can explain and defend every result you present" (prompt §0.3). This lane turns the merged records into the human layer (`README.md`), the judge/AI layer (`TECHNICAL.md`), the talk deck, the video script, the Devpost text and the defense **questions**. **Every result number is tied to a record** by a `rec:` token that `tools.check_claims` verifies (CONTRACT §11), so a judge can't find a number we can't trace. Readers never compute physics: you write prose and tables from `results/records/*.json`, `figures/*.png` and lane status files only.

The one-sentence claim (use verbatim in the README, deck slide 2, video and Devpost): **"We measured the bit-flip rate past the simulation wall, explained it as two physical channels, and designed a readout pulse that beats the square-pulse trade-off — every number checked two ways."** If at the final pass the capstone record (l4c) does not beat square at matched cost, or Γ_X lacks a second method, change the clause to what is true and log it under Deviations.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (allowlists), §6.2–6.3 (record schema, IDs), §11 (claim syntax), §13 (Lab data). `docs/plan/RESEARCH.md` §1 (parameters), §4 (symmetries), §5–§7 (Γ_X, Γ_Z, readout), §8 (circuit), §9 (numerics), §10 (Felis), §12 (what we got wrong first).
- `docs/challenge_prompt_v4.md` §0.3, §0.4, Task 1.3, Section 2 (Tasks 2.1–2.4 a–d). Current `README.md`, `TECHNICAL.md` (claims 1–18 to keep), `notebooks/01_*`–`04_*`.
- `docs/plan/HUMAN_TRACK.md` §6 (talk timing table), §7 (video), §8 (Devpost), §9 (publish checklist).
- Every `docs/plan/status/<lane>.md`: the **Records produced**, **Figures**, **Deviations** and **Explain-back** sections are your source for IDs, figure names and caveats. `reviews/*.md` (Gemini output from `tools/ai_review.py`) for "what we acted on".
- On `standard-track` after merges: `results/index.json` (all record IDs), `results/records/*.json`, `figures/*.png`.

## 3. Allowlist (touch nothing else)
- `README.md`, `TECHNICAL.md`, `docs/defense_questions.md`, `docs/video_script.md`, `docs/devpost.md`, `slides/**` (`slides/deck.md`, `slides/deck.pdf`, `slides/assets/*` e.g. a QR PNG).
- `notebooks/01_task_1_0_warmup.ipynb`, `02_task_1_1_two_mode.ipynb`, `03_task_1_2_convergence.ipynb`, `04_task_1_3a_which_state.ipynb`: **setup-cell fix and re-executed outputs only**.
- `docs/plan/status/l7-docs.md` (copy of `_TEMPLATE.md`).
- **Never** create or edit `docs/defense.md` or `docs/handwritten/` (Harshit-only authorship evidence), `docs/challenge_prompt_v4.md`, `notes/`, `prep/`, `reviews/`, `results/**`, `figures/**`, `site/**`, `src/`, `tasks/`, `tools/`, notebooks 05–09, or any other lane's file. Reference figures by relative path; do not copy them.

## 4. Interfaces you implement / rely on
- **Claim token** (CONTRACT §11): `` `rec:<id>=<displayed>` `` compares `record["value"]`; `` `rec:<id>#<dotted.path>=<displayed>` `` compares a nested field (`#numerics.rel_residual`, `#cross_check.0.rel_diff`, `#convergence.needed.Na`; integer segments index lists). The checker rounds the record value to the **significant figures of the displayed string**, and requires `convergence.converged == true` (or `null` + `notes`), ≥ 1 `cross_check` with `agree == true`, and `provenance.dirty == false`. A line containing `illustrative` turns fails into warns. CLI: `python -m tools.check_claims [--files TECHNICAL.md README.md] [--strict]`; exit 0 iff no fail (`--strict`: no fail and no warn). Write the number, then its token: ``0.5135 /µs `rec:t1_3a.gamma_z.td.two_mode.a2.10=0.5135` ``.
- **Numbers allowed without a token** (your own lint rule, §8): prompt parameters (RESEARCH §1 table), analytic predictions on a line labelled `prediction:` with the formula, anchors labelled `anchor`, versions, dates, times, claim/section numbers, and blocks whose caption contains `Illustrative (legacy results/task_1_x.json → key)`. Every simulated or fitted number gets a token.
- **Wrapped intro records** (l0-tools; display exactly these strings):

| Record id | Display | Paths you may also cite |
|---|---|---|
| `t1_0.max_abs_error.td.one_mode.a2.00` | `9.7e-12` | |
| `t1_0.n_plateau.td.one_mode.a2.00` | `0.49983` | `#cross_check.0.value` (0.5(1−e⁻⁸)) |
| `t1_0.final_n.td.one_mode.a2.10` | `4.404` | |
| `t1_1.peak_na.td.two_mode.a2.10` | `6.8944` | `#convergence.needed.Na=24`, `#convergence.needed.Nb=10`, `#cross_check.0.rel_diff` |
| `t1_1.steady_na.td.two_mode.a2.10` | `4.4026` | `#convergence.needed.Na=16`, `#convergence.needed.Nb=4`, `#cross_check.0.rel_diff` |
| `t1_1.settle_1pct.td.two_mode.a2.10` | `1.07` | `#cross_check.0.value=1.13` (linresp) |
| `t1_1.peak_nb.td.two_mode.a2.10` | `1.99` | |
| `t1_3a.gamma_z.td.two_mode.a2.10` | `0.5135` | `#cross_check.0.value=0.5146` |
| `t1_3a.cat_lifetime.td.two_mode.a2.10` | `1.95` | `#cross_check.0.value=1.94` |

  Intro claims → tokens: 1→`t1_0.max_abs_error` (change "1e-11" to `9.7e-12`); 2→`t1_0.n_plateau`; 4→`t1_0.final_n` (nominal κ₂ only); 6→`t1_1.peak_na`; 7→`t1_1.settle_1pct` + `t1_1.steady_na`; 8→`t1_1.peak_nb`; 11→`t1_1.steady_na#cross_check.0.rel_diff`; 12→`t1_1.steady_na#convergence.needed.*`; 13→`t1_1.peak_na#convergence.needed.*`; 15→`t1_3a.gamma_z` (+ `#cross_check.0.value`); 17→`t1_3a.cat_lifetime`. Claims 3, 5, 9, 10, 14, 16, 18 (and the extra values in 4, 6) have **no record**: label those rows `Illustrative (legacy results/task_1_x.json → key)` and raise the DECISION NEEDED in §11.
- **Standard claims 19+**: take exact IDs from `results/index.json` and each lane's status file. Expected shapes (CONTRACT §6.3) and sanity values (**never display a sanity value; display the record**):

| Task (lane) | Claims to make | Expected record ID shape | Sanity value |
|---|---|---|---|
| 2.1 (l2b) | Γ_X eig two-mode at α 1.0 / 1.4 / 2.1; one-mode at 2.1; td cross-check; channel overlay; γ fit; local slope; κ_a exponent; thermal | `t2_1.gamma_x.eig.two_mode.a1.40.nth0`, `t2_1.gamma_x.eig.one_mode.a2.10.nth0`, `t2_1.gamma_x.td.two_mode.a1.40` (`#cross_check.0.rel_diff`, tol 0.02), `t2_1.gamma_fit.*`, `t2_1.gamma_local_slope.*`, `t2_1.kappa_a_exponent.*`, `...nth0.05` | anchor 2.3007e-3, 1.2021e-4, ~3.9e-7 (two-mode), 1.1699e-7 (one-mode) /µs; slope ~3.1 at α 1–1.4 → ~2.0 at 1.8–2.1; κ_a exponent 1 → 2 |
| 2.1 trap (l1/l2b) | 20×6 at α = 2.1 is ~20× too high | a `#convergence.sweeps.*.results.<i>` path on the α = 2.1 record if the sweep holds 20×6; else `Illustrative` + status-file pointer | anchor 7.6070e-6 vs 3.8831e-7 |
| 2.2 (l2a) | Γ_Z td + eig at each α; slope / 2κ_a | `t2_2.gamma_z.td.two_mode.a2.10`, `t2_2.gamma_z.eig.two_mode.a2.10`, `t2_2.slope_over_2kappa_a.td.two_mode` | prediction 2κ_aα²coth(2α²) = 0.5154 /µs at α = 2.1; slope ≈ 1 (coth grid 0.9959) |
| 2.3 (l4a) | b_ss vs S17; ringing freq; 5 % / 1 % settle; S18 dephasing | `t2_3.b_ss.*`, `t2_3.ring_freq.*`, `t2_3.settle_5pct.*`, `t2_3.settle_1pct.*`, `t2_3.dephasing.*` (tags `a2.10`, `ez{ε/g2:.3g}g2`) | b_ss = ∓ε_Z/(2αg₂); 3.14 MHz, Q 2.46, 0.73 µs, 1.13 µs; 2ε_Z²/(κ₂α²) |
| 2.4a (l5) | g₂ from circuit; resonant terms; Stark/Kerr; tdsim validation | `t2_4a.g2.sym.circuit`, `t2_4a.g2.tdsim.circuit`, `t2_4a.resonant_terms.sym.circuit`, `t2_4a.stark_b.*`, `t2_4a.kerr_b.*`, `t2_4a.chi_ab.*` | |g₂|/2π 0.721 MHz at ε_p 0.035 → ε_p ≈ 0.037; e^{−Φ/2} = 0.9543 |
| 2.4b (l4b) | SNR(T) and Γ_X(ε_Z) along ε_Z ∈ [0.05, 3] g₂; Γ_X even in ε_Z | `t2_4b.snr.*`, `t2_4b.gamma_x.eig.two_mode.a1.00.ez*` | Dubovitskii ΔΓ ≈ 2·(2ε_Z²/(κ₂α²))e^{−2α²} |
| 2.4c/d (l4c) | SVD pulse vs best square at matched ∫ε²dt, verified on two-mode; time-domain flip check at α = 1.0 | `t2_4c.snr.*.psvd`, `t2_4c.snr.*.psquare`, `t2_4c.cost.*`, `t2_4c.flip_prob.td.two_mode.a1.00.p*` | flip prob ~1e-3 per pulse measurable |
| 1.3b/c (l3) | P(right well), fidelity with \|+α⟩ per method | `t1_3b.p_right.*`, `t1_3b.fidelity.*` | symmetry test max\|Re⟨a⟩\| < 1e-12 under ε(a+a†) |
| Felis (l8) | provider Γ_X, Γ_Z vs ours | `tfelis.gamma_x.provider.*`, `tfelis.gamma_z.provider.*` | within ~3 % of channel 2; misses ×3 two-mode factor |

## 5. Tests to write FIRST (TDD)
CONTRACT §1 gives this lane no `tests/` file, so do **not** create `tests/test_l7_docs.py` (DECISION NEEDED if you think it should exist). Instead, before writing prose, put these checks in the status file as a checklist and run them as one-off commands (§9) at every milestone:
1. `check_claims_gate`: `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md` exits **0** at the final pass. During drafting, fails are allowed **only** for records not yet merged; list them in the status file. `--strict` may warn only on `Illustrative` rows; report `N ok, M warn, K fail`.
2. `setup_cell_idempotent`: for each of notebooks 01–04, `exec` the setup cell (cell index 1) **twice** from inside `notebooks/` and assert `os.path.isdir('src')` afterwards (the cwd is the repo root, not its parent). Assert the cell contains `if 'src' not in os.listdir('.')` and no unguarded `os.chdir(os.path.abspath('..'))`.
3. `no_stale_paths`: `Select-String -Path notebooks\0[1-4]_*.ipynb -Pattern '/home/claude'` prints nothing; every code cell has outputs from the new run with no error output.
4. `task_coverage`: `TECHNICAL.md` has a `##` heading for each of 2.1, 2.2, 2.3, 2.4a, 2.4b, 2.4c/d, 1.3b/c and Felis; the README results table has a row for 2.1, 2.2, 2.3, 2.4a, 2.4b, 2.4c/d, 1.3b, 1.3c. A task that was cut says so in one line (what, why), with no number.
5. `numbers_have_tokens`: one-off Python scan of README/TECHNICAL lines matching `\d\.\d|\de-\d|\d %` outside `rec:` tokens; every hit must fall under a §4 exemption. Paste the residual list into the status file.
6. `links_resolve`: every relative link and image path in README, TECHNICAL and `slides/deck.md` exists on disk (`Test-Path`).
7. `deck`: `slides/deck.md` has 11–13 slides before the `<!-- backup -->` marker (count `---` separators after the front matter), each with a `<!-- ... -->` speaker-notes comment; the Marp build (§9) writes `slides/deck.pdf` with exit 0.
8. `video_length`: the segments in `docs/video_script.md` sum to ≤ **240 s** (target 225 s) and the narration is ≤ **560 words** (≈ 140 wpm).
9. `defense_questions`: 14–17 numbered questions, each ending in `→ figure/record` pointing at an existing `figures/*.png` path or record id; no answer text anywhere (no `A:` / `Answer` lines).
10. `allowlist_and_human_files`: `git diff --name-only standard-track...HEAD` lists only §3 paths, and `git diff --name-only standard-track...HEAD -- docs/defense.md docs/handwritten` is empty.

## 6. Method, step by step
1. **Setup (5 min).** `git switch -c std/l7-docs standard-track`; copy `_TEMPLATE.md` to `docs/plan/status/l7-docs.md` (State `IN_PROGRESS`); paste the §5 checklist. Before each later pass run `git merge standard-track` so the newest records and figures are present.
2. **Notebook setup-cell fix.** In notebooks 01–04 replace only the first code cell's path lines with:
   ```python
   import os, sys, json
   if 'src' not in os.listdir('.'):
       os.chdir('..')                       # run from the repo root so figures/ and results/ resolve
   sys.path.insert(0, os.getcwd())
   ```
   Keep the `show`/`load` lambdas unchanged. Edit with a throwaway `nbformat` snippet (`& $env:DUQ_PY -c ...`), not by hand-editing JSON. Leave `03` on its load-saved-results default. Run test 2.
3. **TECHNICAL.md (judge/AI layer).** Sections in this order:
   1. One-paragraph summary + the claim + "how to read a `rec:` token" (record → convergence → cross-check → provenance commit).
   2. **Model and units**: ħ = 1, µs, rad/µs, 2π applied once in `src/config.py`; two-mode H = g₂a²b† + g₂a†²b − ε_d(b+b†), jumps √κ_b b, √κ_a a (thermal √(κ_a(1+n_th)) a, √(κ_a n_th) a†); one-mode L₂ = √κ₂(a²−α²), κ₂ = 4g₂²/κ_b; drives ε_Z(a+a†) (readout, Im axis) and ε_x·i(a†−a) (Re axis); parameter table from RESEARCH §1.
   3. **Rate conventions** table: Γ_X = decay rate of Re⟨a⟩ = −λ₁ (smallest-|λ| eigenvalue of the odd block) = the prompt's 1/T_X = Ferrari's Γ_bf; Dubovitskii per-direction = Γ_X/2; Γ_Z = decay of ⟨P⟩ = 2κ_aα²coth(2α²) (prompt: 2κ_aα²); per-direction phase flip κ_aα²; Felis per-Pauli X and Y rates, each 0.5·1.1e-3·n̄κ₁e^{−2n̄}, Z = κ₁n̄, in **Hz** (RESEARCH §10).
   4. **Symmetry facts** (RESEARCH §4): Z₂ sectors (steady state, X_L even; Z_L, Y_L odd); code-space rates λ_X = 2κ_aα²coth(2α²), λ_Y = κ_aα²(coth+1), λ_Z = κ_aα²(coth−1), so Y_L decays at Γ_Z − Γ_X; odd block singular at κ_a = 0; antiunitary U = P·e^{iπb†b}·K forces Re⟨a⟩ ≡ 0 under ε(a+a†) from vacuum; ⟨b⟩₋ = −⟨b⟩₊* exactly; no tilt; Γ_X(ε_Z) even.
   5. **Eigen method and acceptance** (RESEARCH §9, CONTRACT §8): sparse column-stacked L, shift-invert at σ = 0 on the odd block; deflation L′ = L + η\|𝟙⟩⟩⟨⟨𝟙\| when ε ≠ 0 (no Z₂); acceptance rel_residual < 1e-4, edge_weight < 1e-6, stable across two truncations; cost model t ≈ 113 s·(Na·Nb²/1792)³ (Nb is the expensive axis); cite the l1 profile records.
   6. **Convergence policy**: Na and Nb swept separately at every α (`src/convergence.py`), `needed` from `converged_at`, the stated rel_tol per quantity; the 20×6 trap as the cautionary example.
   7. **Claims table**: rows 1–18 (intro, tokenized per §4) then 19+ (Standard); columns `# | Claim | Value (token) | Check (method, tol) | Record | Script | Figure`.
   8. One section each: **2.1**, **2.2**, **2.3**, **2.4a**, **2.4b**, **2.4c/d**, **1.3b/c**, **Felis**: question (prompt wording), method, result with tokens, the independent check, the figure, caveats from that lane's Deviations. Keep the intro "Convergence study (Task 1.2)" tables (caption them `Illustrative (legacy results/task_1_2.json)`) and the "Task 1.3a reasoning" text.
   9. **Limitations**: precision floors (two-mode ε‖L‖ ~ 1e-13; one-mode ~1e-11, curve capped at α ≈ 2.7); thermal model is n_th only (no κ_φ, no cross-Kerr), so γ is not expected to reach the experimental ≈ 1.44; circuit: RWA to order 7, displaced frame, 150–200 ns validation window; linear response assumes b ≈ 0, κ_a neglected, ε_Z ≲ g₂, and misses the 56 % large-signal overshoot; SNR is ideal mode-matched heterodyne at unit efficiency.
   10. **AI use** (same facts as README, more detail), **File map** (src/, tasks/, tools/, site/, notebooks 01–09, docs/plan/), **Reproduce** (§6.5 commands, run times from records' `wall_s`).
4. **README.md (human layer).** Title with the Standard Track headline, then `DuQuantum 2026 · Alice & Bob challenge · Standard Track (+ Intro Task 1.3b/c)`, team **Harshit Aggarwal + Pranav Reddy** (confirm first, §11). Sections: the claim; the story in plain words (cat qubit, double well, bit flips exponentially rare, phase flips linear, readout through the buffer; no jargon without a one-line gloss); **results table** (`Task | Question | Our answer (token) | Checked by | Figure`); 3–4 key figures with one-line captions (inflation, Γ_X vs α² with channels, readout ringing, SVD vs square); **Lab** link (Pages URL from the l6 status file if the repo is public, else "open `site/dist-single/index.html` in a browser"); **Run it yourself** (§6.5); **How we used AI** (§6.6); **What we got wrong first** (§6.7); repo map; link to `TECHNICAL.md`.
5. **Run it yourself** text: Windows `uv venv -p 3.12` (or `python -m venv .venv`) + `pip install -r requirements.txt`; `python -m src.config` (prints κ₂/2π = 0.896 MHz); `bash run_all.sh --quick` (≤ a few min, writes `results/quick/`, `figures/quick/`); full `bash run_all.sh`; then notebooks 01–09 in order.
6. **How we used AI** (honest and specific; state only what you can point to): plan drafted with **Claude Code** (literature and API research, verified facts in `docs/plan/RESEARCH.md`, an adversarial review that caught the errors in §6.7), committed under `docs/plan/`; implementation by **Cursor agents** in parallel lanes, one branch `std/<lane>` and one brief each (`docs/plan/briefs/`), under **Harshit's direction** (he resolved every `DECISION NEEDED`, merged, and reviewed); commits carry `Co-Authored-By` trailers; the intro-track code was written earlier with Claude; **Gemini** as an independent physics reviewer via `tools/ai_review.py` (outputs in `reviews/`; list what we acted on, read from `reviews/*.md` and status files); what **Harshit derived by hand** (`docs/handwritten/`: κ₂ = 4g₂²/κ_b by buffer elimination; b_ss = ∓ε_Z/(2αg₂) and the 2×2 characteristic equation for the ringing; the code-space Golden Rule giving γ = 4 and why channel 2 takes over); list **only** files actually present (`Get-ChildItem docs/handwritten`). Close with prompt §0.3 (i) and (ii): where AI was used (this section) and how we can defend every result (records + cross-checks + `check_claims`, and Harshit's answers to `docs/defense_questions.md`).
7. **What we got wrong first** (RESEARCH §12, plain words): ε(a+a†) cannot tilt inflation toward +α (symmetry forces Re⟨a⟩ ≡ 0; fix: i(a†−a)); the "readout tilts the double well" story (both flip directions are equal; the cost is population pushed out of the code space); Y_L decays at Γ_Z − Γ_X, not Γ_Z + Γ_X; a pure-exponential Γ_Z fit is biased (steady parity 1/cosh(2α²)); an adiabatic ⟨b⟩ surrogate would delete the ringing the capstone exploits; an absolute residual threshold is meaningless at λ₁ ~ 1e-7; 20×6 gives a 20× wrong Γ_X at α = 2.1.
8. **docs/defense_questions.md**: header "Questions only. Harshit answers in his own words in `docs/defense.md`." Grouped by lane, each with `→ figure/record` (fill pointers from the merged figures/IDs):
   - **2.1**: Why is the bit-flip rate the slowest eigenvalue of the odd block, and why is Re⟨a⟩'s decay the sum of both flip directions? · Why does the naive Golden Rule estimate fail above α² ≈ 2.3? · Why does the buffer truncation matter more during inflation than in steady state? · Which diagnostic would have caught the 20×6 truncation trap, and why does Nb dominate the cost? · Why does the two-mode model flip faster than the one-mode model, increasingly with α? · Why is your thermal-free γ above the deck's ≲ 2, and what would bring it down?
   - **2.2**: Why fit A·e^{−Γt} + C rather than a pure exponential, and what sets C? · Why coth(2α²), and where does it differ from 2κ_aα²?
   - **2.3**: Why does the readout ring instead of settling monotonically? · Why is ⟨b⟩₋(t) = −⟨b⟩₊(t)* exact, and what does that rule out? · Why does reading Z_L dephase X_L at 2κ_b\|⟨b⟩\|², and why is Γ_X then the cost that matters?
   - **2.4a**: Where does g₂ = ½E_Jε_pφ_a²φ_b come from, and why is ε_p ≈ 0.037 rather than 0.035? · Which other terms survive the RWA, and why must ω_p be retuned?
   - **2.4c**: Why is the top singular vector of the response operator the optimal linear-response pulse, and what is its spectrum? · How do you know the optimized pulse didn't exploit the truncation? · Why ∫ε²dt as the matched cost, and how did the time-domain flip check confirm it?
   - **1.3b**: Why can't ε(a+a†) prepare \|+α⟩? · How do you know the state is in the right well (committor vs ½(1+⟨Z_L⟩)), and what does the method cost (1.3c)?
9. **slides/deck.md** (Marp; ~12 slides, 8 min; follow HUMAN_TRACK §6 timing). Front matter `marp: true`, `paginate: true`, `size: 16:9`. Images `![w:900](../figures/<name>.png)`. Every slide has a `<!-- speaker notes -->` comment (≤ 60 words, the spoken line + the record behind the headline number). Order: 1 hook: a cat inflating from vacuum (Task 1.1 figure); 2 the trade-off (bit flips down exponentially, phase flips up linearly) + the claim; 3 verification: provenance card, convergence, symmetry tests, the 20×6 truncation trap; 4 Γ_X two ways (eigen vs time domain) with the two channel overlays; 5 κ_a sweep: exponent 1 → 2 identifies the channels; 6 two-mode vs one-mode (non-adiabatic); 7 Γ_Z vs 2κ_aα²coth(2α²); 8 readout ringing, analytic 3.14 MHz / 0.73 µs vs simulation; 9 the trade-off curve (2.4b) and where the cost comes from; 10 capstone: SVD pulse vs square at matched cost, verified on the two-mode model; 11 what we got wrong first + how we used AI; 12 close: the claim in one line + Lab link / QR. After `<!-- backup -->`: 2.4a term table, 1.3b preparation, Felis table, limitations. Headline numbers on slides use the same displayed values as TECHNICAL (no tokens on slides; the speaker note names the record id). QR only if a Pages URL exists: `npx qrcode@1.5.4 -o slides/assets/lab_qr.png "<url>"`.
10. **docs/video_script.md** (≤ 4:00; aim 3:45): table `Time | Narration (spoken text) | Screen action in the Lab`. Segments: 0:00–0:20 hook (Inflate page, play the inflation); 0:20–0:45 trade-off + claim; 0:45–1:15 Verification page (open one provenance card, show the trap); 1:15–2:00 Error budget (Γ_X two ways, channels, κ_a sweep, two-mode vs one-mode); 2:00–2:30 Γ_Z + ringing; 2:30–3:15 Readout designer (square vs SVD); 3:15–3:35 what we got wrong + AI use; 3:35–3:45 close with the repo + Lab link. Add recording notes: Win+Alt+R (Xbox Game Bar) or OBS at 1080p, browser zoom 110 %, close notifications, optional ElevenLabs narration from the same text.
11. **docs/devpost.md**: Title; Tagline (≤ 200 characters); Inspiration; What it does; How we built it (dynamiqs, sparse Liouvillian, Z₂ sectors, linear response, parallel agent lanes, record/claims pipeline); Challenges (simulation wall, truncation trap, Windows JAX); Accomplishments; What we learned (RESEARCH §12 in one paragraph); What's next (thermal + cross-Kerr saturation, gradient refinement, hardware κ_b option); Built with: dynamiqs 0.3.7, JAX 0.12.0.1, SciPy, NumPy, Matplotlib, SymPy, Vite, Plotly, Marp (+ qiskit-alice-bob-provider 3.0.0 if l8 merged); Links: repo, Lab, video (placeholder `<VIDEO_URL>` for Harshit). Same token rule does not apply here, but every number must equal the README's displayed value.
12. **Final pass (8:00–10:00 AM, strongest model):** `git merge standard-track`; replace every pending token with the frozen record value; run all §5 checks; consistency sweep (the same number is displayed identically in README, TECHNICAL, deck, video, Devpost); re-execute notebooks 01–04 (§9), restore any regenerated `figures/`/`results/` files; build the PDF; commit; set the status to DONE.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **No records, arrays or figures.** No quick vs production split; no jobs to queue. You never run physics scripts, except the notebook re-execution, whose regenerated `figures/`/`results/` files you **restore** (`git restore figures results`) because the integrator owns them.
- Files: `README.md`, `TECHNICAL.md`, `docs/defense_questions.md`, `docs/video_script.md`, `docs/devpost.md`, `slides/deck.md`, `slides/deck.pdf` (commit the PDF at the final pass), optional `slides/assets/lab_qr.png`, re-executed notebooks 01–04, `docs/plan/status/l7-docs.md`.
- Commits: `l7: draft docs on merged lanes` (draft), `l7: notebooks 01-04 setup-cell fix + re-execute`, `l7: final docs at freeze`.

## 8. Acceptance gates (ALL must pass before DONE)
1. `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md` exits **0** at the final pass (paste `N ok, M warn, K fail`); warns only on `Illustrative` rows.
2. Every Section 2 task (2.1, 2.2, 2.3, 2.4a, 2.4b, 2.4c, 2.4d) and 1.3b/c is explicitly addressed in both README and TECHNICAL (test 4).
3. AI policy: README "How we used AI" states where and how (Claude Code plan, Cursor lanes, Gemini review, Harshit's derivations and verification) and links `docs/defense_questions.md` and `TECHNICAL.md` (prompt §0.3 (i) + (ii)); no claim that can't be pointed to a file.
4. No result number without a token (test 5 residual list fully justified); links resolve (test 6).
5. Deck builds to `slides/deck.pdf` (test 7); video ≤ 240 s (test 8); defense questions valid and answer-free (test 9).
6. Notebooks 01–04: setup cell idempotent, no `/home/claude`, executed without errors (tests 2, 3).
7. Allowlist clean; `docs/defense.md` and `docs/handwritten/` untouched (test 10).

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git switch -c std/l7-docs standard-track          # first time; afterwards: git merge standard-track
& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md
& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md --strict
& $env:DUQ_PY -c "import json,os; os.chdir('notebooks'); s=''.join(json.load(open('01_task_1_0_warmup.ipynb',encoding='utf-8'))['cells'][1]['source']); exec(s); exec(s); assert os.path.isdir('src'), os.getcwd(); print('ok')"
& $env:DUQ_PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 notebooks/01_task_1_0_warmup.ipynb notebooks/02_task_1_1_two_mode.ipynb notebooks/03_task_1_2_convergence.ipynb notebooks/04_task_1_3a_which_state.ipynb
git status --porcelain -- figures results          # non-empty -> git restore figures results
Select-String -Path notebooks\0[1-4]_*.ipynb -Pattern '/home/claude'
npx @marp-team/marp-cli@latest slides/deck.md --pdf --allow-local-files -o slides/deck.pdf
# if Marp can't find Chrome: $env:CHROME_PATH = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
git diff --name-only standard-track...HEAD
```
Run the first `exec` check for each of the four notebooks (change the filename). Notebooks 01, 02 and 04 rerun Tasks 1.0, 1.1 and 1.3a (≈ 20 s, 1 min, 2 min); 03 loads saved results.

## 10. Out of scope / do not
- Do not compute, refit, round differently or "fix" any physics number; if a record looks wrong, write it in the status file for the reviewer and leave the claim out.
- Do not write answers to the defense questions, and never touch `docs/defense.md` or `docs/handwritten/`.
- Do not edit records, figures, `site/`, `tools/check_claims.py` or other lanes' notebooks; do not loosen a check to make a claim pass (fix the display or label it `Illustrative`).
- Do not mark a Standard result `Illustrative` to dodge a failing check: a result without a passing record is removed and the gap is stated in words.
- Do not overstate: no "first", "exact", or "proves" unless the record's cross-check shows it; do not promise γ reaches the experimental 1.44.
- Do not add anything from `notes/`; do not commit secrets; do not change repo visibility (Pranav does that).

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write in `docs/plan/status/l7-docs.md`:
> **Q:** Team names: confirm full names for the README/Devpost. The brief says "Harshit Aggarwal + Pranav Reddy", but the repo owner's GitHub handle is `pkarakala`. **Options:** A) as briefed B) Harshit supplies. **Recommendation:** B. **Blocking?** no: placeholder `<!-- confirm names -->` meanwhile.

> **Q:** Intro claims 3, 5, 9, 10, 14, 16, 18 have no wrapped record. **Options:** A) l0-tools/integrator wraps more intro fields (pop_0/pop_1, κ₂·t₉₀, max_top2_a/max_top_b, starter_peak_na, max_abs_re_a, at_1us, at_6us) B) keep them as `Illustrative (legacy JSON → key)` rows. **Recommendation:** B. **Blocking?** no.

Other DECISION NEEDED triggers: a lane's record ID or figure name differs from §4 (use the real one, note it); the Lab is not public by 9:30 AM (use the `site/dist-single/index.html` wording, drop the QR); a headline record fails `check_claims` at freeze (drop the claim; ask whether the one-sentence claim still holds); `docs/handwritten/` is empty (say so instead of claiming hand derivations); Marp cannot build (fallback: `--html` export plus Harshit prints to PDF from the browser).
**Cut order** when time runs short: Devpost polish → backup slides → deck speaker notes shortened → video script reduced to timed bullets → notebook re-execution (keep the setup-cell fix). **Never cut:** README with tokens, TECHNICAL claims passing `check_claims`, the AI-use section, `docs/defense_questions.md`. **Cut line:** at 9:45 AM commit whatever passes the gates.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
Status file at DONE: State `DONE` (or `DONE_WITH_CONCERNS`); last commit sha; the gate table with evidence (the `check_claims` summary line, the slide count + PDF path, the video total seconds and word count, the question count, the `git diff --name-only` list); a table of **every** token used (`id | displayed | file:line`); the list of `Illustrative` rows with reasons; claims dropped at freeze and why; any number that appears in more than one file, with its displayed value; the Lab link used; open DECISION NEEDED items.

Explain-back for Harshit (questions only; he writes the answers in `docs/defense.md`):
1. A judge points at one number in the README: walk from its `rec:` token to the record's convergence block, its independent cross-check and the commit that produced it. What exactly would make `check_claims` fail on it?
2. Precisely what did AI write, what did you derive or verify yourself, and which AI mistake did you catch before it reached the results?
3. Which headline result is the weakest, what is its limiting assumption (truncation, thermal model, linear response or RWA), and what result would change your one-sentence claim?
