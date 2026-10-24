# Review protocol (for Claude, reviewing Cursor's work later)

**Goal:** decide, lane by lane, whether the merged work is *correct, converged, cross-checked and defensible*. Answer every open `DECISION NEEDED`. Then hand Harshit a short, ranked action list.

**Output:**
- `reviews/claude-<YYYYMMDD-HHMM>.md` (verdicts, findings, decisions).
- One line per decision in the decision log of `docs/plan/status/integrator.md`.

## 0. Inventory (5 min)
```powershell
git fetch --all; git log --all --oneline --graph -40
git log standard-track --oneline -30
git branch --list "std/*" -v
Get-ChildItem docs/plan/status/*.md, docs/plan/status/reviews/*.md
& $env:DUQ_PY -m tools.runq status
```
Build a table with these columns: lane, state, branch head, merged?, reviewer verdict, records count, open DECISION NEEDED.

## 1. Global checks (10 min)
1. `& $env:DUQ_PY -m pytest -m "not slow" -q`, then `-m slow`. Note failures and wall times.
2. `& $env:DUQ_PY -m tools.build_index`, then `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md --strict`.
3. `git diff --stat intro-track-tasks...standard-track`. Look for files outside every allowlist, `notes/` content, and committed `results/quick/` or `figures/quick/` outputs.
4. Grep for red flags:
   ```powershell
   rg -n "2 \* jnp.pi|2\*jnp.pi|2 \* math.pi|TWO_PI" src tasks tools --glob '!src/config.py'
   rg -n "options=" tasks src
   rg -n "tilt" README.md TECHNICAL.md docs tasks
   rg -n "platform.node|getpass|USERNAME" src tools tasks
   ```
5. Run `python -c` over `results/records/*.json`. Every record must have `converged` true, or null with notes; at least one agreeing `cross_check`; and `dirty == false`.

## 2. Per-lane review (10 to 20 min per physics lane)

For each lane: read its status file and reviewer verdict, then `git diff standard-track~N..` over the lane's merge commit. Check:
- **Allowlist:** every changed file is in CONTRACT §1 for that lane.
- **Tests encode physics** (assertions with tolerances), and they pass.
- **Spot checks:** recompute at least 2 numbers independently, using the expected values below, or a smaller independent run.
- **Red flags** (list below): any one of them is a finding.

### Expected values (sanity table)
| Quantity | Expected | Source |
|---|---|---|
| κ₂/2π | 0.896 MHz | RESEARCH §1 |
| Γ_X one-mode, N=40 | 2.2819e-3 (α=1.0), 1.0744e-4 (1.4), 2.0693e-6 (1.8), 1.1699e-7 (2.1) | anchor, §5 |
| Γ_X two-mode, 28×8 | 2.3007e-3 (1.0), 1.2021e-4 (1.4), 4.0696e-6 (1.8), 3.8831e-7 (2.1); Na=28–36 at Nb=6 gives 3.987e-7 | anchor, §5 |
| Truncation trap | 20×6 at α=2.1 gives 7.607e-6, and **must** be flagged by edge_weight | §5, §9 |
| Channel 1 share of one-mode λ₁ | 96 / 84 / 43 / 10 % at α = 1.0 / 1.4 / 1.8 / 2.1 | §5 |
| Channel 2 prefactor c | about 1 to 1.3 (×κ_a²/κ₂·e^{−2α²}) | §5 |
| κ_a-sweep exponent | ≈1 at small α, ≈2 at α ≈ 2.1 | §5 |
| Γ_Z | 2κ_aα²coth(2α²): 0.1212 (α=1.0), 0.5154 (2.1); 1.3a fit 0.5135 | §6 |
| Steady parity | 1/cosh(2α²): 0.266 (α=1.0) | §6 |
| ⟨b⟩_ss | ∓ε_Z/(2αg₂): 0.0238 at ε_Z = 0.1g₂, α = 2.1 | §7 |
| Ringing | λ = −4.08 ± 19.72i /µs; 3.14 MHz; Q 2.46; settling 0.73 µs (5%), 1.13 µs (1%) | §7 |
| Readout dephasing | 2ε_Z²/(κ₂α²) | §7 |
| g₂ from circuit | −½E_Jε_pφ_a²φ_b·e^{−Φ/2} = −0.721 MHz at ε_p = 0.035; ε_p ≈ 0.037 for 0.763 MHz | §8 |
| Resonant terms through order 7 | the a²b† family only | §8 |
| Felis | its bit-flip prefactor ≈ channel 2 (about 3%); it misses the ×3 two-mode factor at α = 2.1 | §10 |

### Red flags (each is a finding; severity in brackets)
- [critical] Using ε(a+a†) to prepare a well, or "tilt" language for 2.4b (RESEARCH §4.1, §4.3).
- [critical] A Γ_X quoted from a single truncation, or with edge_weight ≥ 1e-6, or above the precision floor.
- [critical] 2π applied outside `src/config.py`; a missing √ on rates; a sign flip in α².
- [critical] Records with `dirty: true`, no cross-check, or `converged: false` that are presented as results.
- [major] Parity fits without an offset; Y_L described as decaying at Γ_Z + Γ_X; a Γ_X convention mixed up with the per-direction rate (factor 2).
- [major] Tolerances loosened in tests or gates; anchors changed to match a run without an investigation note.
- [major] Time-domain Γ_X fits starting before 3 µs, or without an rtol cross-check.
- [major] Capstone claimed without a matched-cost comparison on the **two-mode** model.
- [minor] Missing `--quick`; quick outputs committed; figures without units; notebooks that recompute by default.
- [minor] Hostname or username in provenance; anything from `notes/` committed.

## 3. Decisions
For each `DECISION NEEDED` in `docs/plan/status/*.md`:
- Decide, giving the reason and the evidence (run a check if needed).
- Write the answer under the block in that status file.
- Log it in `integrator.md`.

If a decision needs new facts (an anchor that doesn't reproduce, an unclear API, a paper claim), research it first: the primary source, the dynamiqs source at v0.3.7, or arXiv HTML. Cite it in the review file.

## 4. Verdict per lane
- **ACCEPT:** all gates met, no critical or major findings.
- **ACCEPT_WITH_NOTES:** minor findings only; list them.
- **REWORK:** any critical or major finding. Give a concrete fix list, sized so a single Cursor agent can do it in 30 min or less, and specify which brief section to re-run.
- **CUT:** can't be fixed before the freeze. Apply the cut order (PLAN §8), and make sure nothing in README, TECHNICAL, slides or the Lab references it.

## 5. Report shape (`reviews/claude-<stamp>.md`)
1. A 3-line summary: what's solid, what's at risk, the top 3 actions for Harshit.
2. A table of lane verdicts.
3. Findings, numbered, with file:line, severity and the fix.
4. Decisions made.
5. Talk readiness: which claims are safe to present; which need an "illustrative" label; which explain-back questions Harshit should drill.
