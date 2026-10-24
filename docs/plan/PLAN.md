# Master plan: DuQuantum 2026 · Alice & Bob cat qubits · Standard Track

**Owner:** Harshit Aggarwal (solo human); Pranav Reddy may contribute separately.
**Drafted:** Sat Oct 24, 2026, about 6 PM EDT, with Claude Code: survey of the repo and `notes/`, deep research, and an adversarial plan review.
**Executed by:** Cursor agents in parallel lanes. **Reviewed later by:** Claude (`REVIEW_PROTOCOL.md`).

## 1. Context: why this plan exists

`intro-track-tasks` has Intro Tasks 1.0 to 1.3a done well. The results are converged and checked against hand predictions, with a claims table in `TECHNICAL.md` and a Gemini physics review. **We submit the Standard Track**, which is judged on Section 2 only. We also finish Intro 1.3b/c, because preparing |+α⟩ is the same physics Task 2.1 starts from.

**The story we want to tell:**
- **Γ_X past the "numerical wall":** we take it from the Liouvillian spectral gap, check it against time-domain fits where both methods work, and explain it as **two physical channels** with analytic formulas.
- **The γ ≲ 2 trap:** the prompt's own caveat becomes a finding.
- **Readout:** Γ_Z and the readout are understood analytically. The buffer *rings* at 3.14 MHz.
- **Capstone:** a provably optimal linear-response readout pulse beats the square pulse at matched cost, and is verified on the full model.

**The intended outcome:** every headline number has a convergence record, an independent cross-check and a clickable provenance card. The demo can't hang. Harshit can defend every number.

**Decisions locked with Harshit:**
1. Standard Track, plus 1.3b/c.
2. The full Cat Qubit Lab, with 4 must-have pages.
3. Multi-agent development, now run with Cursor agents in worktrees.
4. Harshit solo with agents.

## 2. Done signal (10:45 AM)

| # | Done when | Checked by |
|---|---|---|
| D1 | Every Standard Track number in `TECHNICAL.md` resolves to a converged, cross-checked, clean record | `python -m tools.check_claims` exits 0 |
| D2 | A fresh clone plus the venv reproduces every figure | `bash run_all.sh --quick` |
| D3 | Physics and symmetry tests pass | `pytest -m "not slow"`; `-m slow` at freeze |
| D4 | The Lab works offline, and online if the repo is public | `site/dist-single/index.html` from `file://`; Pages URL |
| D5 | Devpost submitted | repo link, video ≤4:00, text |
| D6 | Harshit owns it | `docs/defense.md` answered aloud, with no notes |

## 3. Scope

**Must:**
- Tasks 2.1, 2.2, 2.3, 2.4a–d, 1.3b, 1.3c.
- Results contract v2 with provenance; convergence harness; physics and symmetry tests.
- Lab pages: Inflate, Error budget, Readout designer, Verification.
- README and TECHNICAL rewrite; notebooks 05 to 09; defense questions; deck; video; Devpost.

**Core techniques (required, not optional):**
- **Z₂-sector Liouvillian.** A 32×12 solve takes about 30 min on the full L and about 4 min on the odd block.
- **2×2 linear-response model** of memory displacement and buffer field. It gives the readout ringing analytically and is the backbone of the capstone.

**Above and beyond (each cuttable):**
- Analytic overlays on every headline curve.
- The κ_a sweep that identifies the two bit-flip channels.
- The committor Wigner plot (left eigenvector).
- An exact normal-ordered RWA term finder with a displaced frame, validated by a short-window circuit simulation.
- The Felis cross-check.
- The claims linter.
- CI.
- Provenance cards.
- A hardware-level κ_b option.

**Out:**
- Full-GHz circuit simulation over µs.
- GRAPE on the full model at large α.
- Unrelated sponsor tech.
- Any live heavy simulation in the demo.
- The live browser sandbox.

## 4. Architecture (details in `CONTRACT.md`)

```
src/config.py ─► src/model.py ─► tasks/task_*.py ─► results/records/<id>.json (+ results/arrays/<id>.npz), figures/
                     └► src/spectral.py, src/linresp.py, src/circuit.py, src/pulses.py
          src/convergence.py · src/results.py (v2) · src/provenance.py · src/analysis.py
   integration branch only:  tools/build_index.py → results/index.json → tools/export_lab_data.py → site/src/data/live/
                             tools/check_claims.py ⇄ TECHNICAL.md / README.md
   readers only: notebooks · site/ (Lab) · slides · README / TECHNICAL
```
**Rules:**
- Arrows point one way; readers never compute physics.
- Every figure comes from a script.
- **One record per file,** so lanes never collide.
- Production records must have `provenance.dirty == false`.

## 5. Physics in one page (full detail: `RESEARCH.md` and the lane briefs)

| Task | What | How | Independent checks |
|---|---|---|---|
| 1.3b/c | Prepare \|+α⟩; what it costs | (i) ideal displacement, (ii) a finite `eps_x·i(a†−a)` pulse, then stabilization, (iii) a weak `eps_x` during inflation, (iv) postselect (discussion). **ε(a+a†) cannot work:** the antiunitary symmetry forces Re⟨a⟩ ≡ 0. | Symmetry test; fidelity; committor P(right) |
| 2.1 | Γ_X(α) | λ₁ of the odd Z₂ block (one-mode up to α = 2.7; two-mode 0.8 to 3.0 within budget). Time-domain Re⟨a⟩ fits at α ≤ 1.4 over 50 to 100 µs. κ_a sweep; thermal n_th. | Eigen vs time domain within 2%; channel 1 κ_aα²(coth2α²−1) [γ=4] plus channel 2 ≈(κ_a²/κ₂)e^{−2α²} [γ=2]; anchors |
| 2.2 | Γ_Z(α) | Parity decay from \|C₊⟩, fitted as A·e^{−Γt}+C | 2κ_aα²coth(2α²) within 2%; even-block eigenvalue; 1.3a value |
| 2.3 | Readout ⟨b⟩± | Stabilize, then switch ε_Z on, from 0.05 to 3 g₂ | ⟨b⟩ = ∓ε_Z/(2αg₂); ringing at 3.14 MHz, Q 2.46, 1% settling in 1.13 µs; ⟨b⟩₋ = −⟨b⟩₊*; dephasing 2ε_Z²/(κ₂α²) |
| 2.4a | Circuit terms | Exact normal-ordered sin φ̂, displaced frame, then RWA; validation simulation over 150 to 200 ns | g₂ = −½E_Jε_pφ_a²φ_b·e^{−Φ/2} (ε_p ≈ 0.037); only the a²b† family is resonant through order 7 |
| 2.4b | Trade-off | SNR(T) vs Γ_X(ε_Z) (full deflated L) at α = 1.0 to 1.4 | Γ_X even in ε_Z; Dubovitskii ε² overlay; S18 dephasing |
| 2.4c/d | Beat it | Square vs ramps vs CLEAR vs the **SVD-optimal** pulse (top singular vector of the response operator); optional gradient refinement | Two-mode validation; time-domain flip check at α = 1.0; matched-cost comparison |
| Felis | Emulator vs first principles | `EMU:6Q:PHYSICAL_CATS` formulas against our Γ_X and Γ_Z | Expect the emulator to miss the ×3 two-mode correction |

**Rate conventions:**
- Γ_X = decay rate of Re⟨a⟩ = −λ₁. Dubovitskii's per-direction rate is Γ_X/2.
- Γ_Z = decay rate of parity.

## 6. Lanes (parallel execution matrix; ownership is in `CONTRACT.md` §1)

| Lane | Brief | Depends on | Model | Cap | Target |
|---|---|---|---|---|---|
| setup | `00-setup.md` | none | fast | 45 min | 6:15 PM |
| l0-core | `01-l0-core.md` | setup | strongest | 60 min | 6:45 PM (G0) |
| l0-tools | `02-l0-tools.md` | contract text | fast | 75 min | 7:30 PM |
| l1-spectral | `03-l1-spectral.md` | l0-core | strongest | 2.5 h | 9:15 PM |
| l2a-gamma-z | `04-l2a-gamma-z.md` | l0-core (l1 for eig) | fast | 1.5 h | 8:45 PM |
| l2b-gamma-x | `05-l2b-gamma-x.md` | l0-core, l1 | strongest | 3 h | 1:30 AM |
| l3-prep | `06-l3-prep.md` | l0-core | fast/standard | 2 h | 9:30 PM |
| l4a-readout | `07-l4a-readout.md` | l0-core | strongest | 2.5 h | 9:45 PM |
| l5-circuit | `08-l5-circuit.md` | l0-core | strongest | 3 h | 11:30 PM |
| l4b-tradeoff | `09-l4b-tradeoff.md` | l1, l4a | strongest | 2.5 h | code 12:30 AM; grid overnight |
| l4c-capstone | `10-l4c-capstone.md` | l4a (l4b grid optional) | strongest | 3 h | 1:30 AM |
| l6-lab | `11-l6-lab.md` | contract (mock first) | fast | 3 h + 1 h | 9:45 PM; live data later |
| l7-docs | `12-l7-docs.md` | merged lanes, l0-tools | fast, then strongest | 2.5 h | draft 10 PM; final 10 AM |
| l8-felis | `13-l8-felis.md` | l2a, l2b records | fast | 1 h | 1:00 AM |
| integrator | `90-integrator.md` | n/a | strongest | continuous | n/a |
| reviewer | `91-reviewer.md` | each lane | strongest (physics) | 15–30 min/lane | n/a |

**Collision rules:**
- Allowlists are disjoint.
- `src/model.py`, `src/config.py` and `src/analysis.py` are frozen after l0-core. The only exception is the integrator's single NA_EIG_MAX edit.
- Long runs (over 15 min) go through `tools/runq.py`, owned by the integrator on `standard-track`.

## 7. Timeline and gates (EDT)

- **G0, 6:45 PM:** setup plus l0-core merged; contract and claim syntax frozen; l0-tools and l6-lab running.
- **G1, 9:45 PM:** l1 (anchors plus cost profile), l2a, l3 and l4a merged; l5 running.
- **G2, 1:30 AM:**
  - Γ_X two ways at small α, with the channel overlays.
  - The capstone frontier plus two-mode validation.
  - Felis.
  - The l4b grid and large-α confirmations queued overnight.
- **Sleep, about 2:00 to 6:00 AM.** The integrator's queue keeps running. The morning brief is in `status/integrator.md` by 6:30 AM.
- **G3, 7:00 AM:** all physics merged or cut.
- **Freeze, 8:00 AM:** `check_claims`, Gemini `ai_review.py --diff intro-track-tasks`, fresh-clone smoke. No new numbers after this.
- **Package, 8:00 to 10:45 AM:** docs final, Lab deployed, video recorded by 10:00, Devpost by 10:45.
- **Rehearse, 10:45 to 11:45 AM.** Hacking ends at 11:30.

## 8. Risks and cut order

| Risk | Early sign | Response |
|---|---|---|
| A confident wrong number | Off by about 6 (2π), or it moves with Na | Record + convergence + cross-check; the linter gates the docs |
| Windows JAX install | `check_env` fails | Python 3.11 / jax 0.10.2, then WSL, then a cloud VM |
| Eigen RAM or time blow-up | LU > 6 GB, or a solve > 10 min | Odd block, real form, MMD ordering, pypardiso; quote only the converged, feasible range |
| Precision floor | rel_residual > 1e-4, or edge_weight > 1e-6 | Cap the curve there and say so |
| Flat SNR at small ε_Z | SNR² < 0.1 | Sweep up to 3g₂; argue at α ≤ 1.4 |
| The optimizer stalls | No gain by its cap | The SVD pulse and the families stand alone |
| Lab scope creep | Requests for new data | Reads `results/` only; frozen at 8 AM; the single file is the fallback |
| The repo stays private | No public link by 10:15 | Pranav adds judges, or makes it public |
| An agent result Harshit can't defend | A failed explain-back | Simplify it or cut it from the talk |

**Cut order (if a gate slips by more than 1 h):** (1) live sandbox, (2) gradient refinement, (3) Felis, (4) thermal beyond 3 values, (5) 2.4b `extra_H` asymmetry sweep, (6) κ_b critical-damping option, (7) 1.3b method (iii), (8) Readout designer page (replace with a static figure), (9) CI.

**Never cut:** convergence records; the Γ_Z check; Γ_X two ways at small α with the channel overlays; the readout trade-off; the SVD-vs-square comparison; a reproducible README; defense prep.

## 9. Roles
- **Harshit:** decides; answers each `DECISION NEEDED`; launches lanes; human track (`HUMAN_TRACK.md`); presents.
- **Cursor lane agents:** implement exactly one brief each, test-first, inside their allowlist.
- **Reviewer agent:** spec review, then physics review per lane, before each merge.
- **Integrator** (Harshit, or one agent in the main checkout): merges, production runs, gates, freeze.
- **Claude:** later asynchronous review, decisions and research (`REVIEW_PROTOCOL.md`).
- **Gemini** (`tools/ai_review.py`): independent physics review at freeze.

## 10. Verification (end to end)
1. **Tests:** `& $env:DUQ_PY -m pytest -m "not slow"` (under 2 min), including the symmetry tests. `-m slow` at G2 and at freeze.
2. **Reproduction:** fresh clone, then `bash run_all.sh --quick` with `PY=$env:DUQ_PY`. Figures regenerate and records match.
3. **Claims:** `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md` exits 0.
4. **Independent review:** Gemini `ai_review.py`, plus Claude's review per `REVIEW_PROTOCOL.md`.
5. **Lab:** `npm run build`, `npm run build:single`, and browser smoke tests at desktop and mobile widths, offline from `file://`.
6. **Notebooks:** `jupyter nbconvert --execute --inplace notebooks/0*.ipynb` with the results-loading defaults.
7. **Human:** two timed rehearsals of 8:00 or less, with every defense answer given aloud.
