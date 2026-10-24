# Brief `reviewer`: Reviewer: spec-compliance + physics review before every merge

> **Paste into a new Cursor agent (worktree mode):** "You are lane `reviewer`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/91-reviewer.md`, then execute this brief exactly. Keep `docs/plan/status/reviews/<slug>.md` updated." (Replace `<slug>` with the lane under review, e.g. "You are the reviewer for lane `l2a-gamma-z`, round 1.")

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `reviewer` | read-only: inspect `std/<slug>` in **detached HEAD**; commit only the verdict, on `review/<slug>-r<N>` cut from `standard-track` | nothing merged; the lane's status file must say `DONE` or `DONE_WITH_CONCERNS` at the head of `std/<slug>` | strongest for physics lanes (l0-core, l1, l2a, l2b, l3, l4a, l5, l4b, l4c, l8); fast is OK for l0-tools, l6-lab, l7-docs | 15–30 min per review (hard stop 40 min) | continuous, Sat Oct 24 6:00 PM to Sun Oct 25 8:00 AM: l0-core by 6:40 PM (G0 6:45 PM); G1 lanes by 9:40 PM; G2 lanes by 1:25 AM; overnight lanes by 7:00 AM (G3); l7-docs final pass by 10:15 AM |

## 1. Goal and why
You are the last automated gate before the integrator merges a lane into `standard-track`. Decide **PASS / PASS_WITH_NOTES / FAIL** for exactly one lane, in two stages, in order, never skipped: **Stage 1 spec compliance** (did the lane build exactly what its brief asked, inside its allowlist?) then **Stage 2 physics and numerics** (is every number right, converged, cross-checked and reproducible?). The project's main risk is a *confident wrong number* (off by 2π, a missing √, a well "prepared" with the wrong drive quadrature, a 20×6 truncation trap). Every one of the RESEARCH §12 mistakes would have been caught by this checklist. Your review file is also the main evidence Claude reads later (`REVIEW_PROTOCOL.md`), so be factual: commands, real output, file:line. **You never edit code, tests, records or another lane's files.** You write one file: `docs/plan/status/reviews/<slug>.md`.

## 2. Read first
- `AGENTS.md` (non-negotiables 1–9), then `docs/plan/CONTRACT.md` §1 (allowlists + shared rules), §2 (env, quick vs production), §6 (record schema, field rules, ID scheme §6.3), §8 (eigen acceptance), §11 (claims), §14–§15 (status, tests).
- `docs/plan/RESEARCH.md` §1 (numbers), §4 (symmetries), §5 (Γ_X), §6 (Γ_Z), §7 (readout), §8 (circuit), §9 (numerics), §10 (Felis), §12 (what we got wrong first).
- `docs/plan/REVIEW_PROTOCOL.md` §1–§2: the expected-values table and the red-flag list with severities. Use the same severities.
- The **lane's brief** `docs/plan/briefs/<NN>-<slug>.md` in full, especially §3 allowlist, §4 interfaces, §5 tests, §7 outputs (exact record IDs), §8 gates.
- The lane's status file `docs/plan/status/<slug>.md` at `std/<slug>`, and any earlier round: `git show review/<slug>-r<N-1>:docs/plan/status/reviews/<slug>.md`.

## 3. Allowlist (touch nothing else)
- Write: `docs/plan/status/reviews/<slug>.md` (one file per lane; a later round overwrites it and keeps a "Prior rounds" line).
- Git: `git switch --detach std/<slug>` to inspect; at the end `git switch -c review/<slug>-r<N> standard-track`, `git add docs/plan/status/reviews/<slug>.md`, one commit `[reviewer] <slug> r<N>: <VERDICT>` (end with the `Co-Authored-By:` lines). No other commits, no push, no merge, no rebase.
- Scratch: temporary spot-check files only under `$env:TEMP\duq-review\` (outside the repo). Running `--quick` scripts is allowed; their outputs land in git-ignored `results/quick/` and `figures/quick/`.
- Forbidden: production runs (any task script without `--quick`), `tools/runq.py submit`, `tools/build_index.py` writes, editing any status file other than your review file, answering a lane's `DECISION NEEDED` (flag it; Harshit or Claude decides).

## 4. Interfaces you implement / rely on
- **You produce** the review file (template in §7) and the branch `review/<slug>-r<N>`. The integrator merges the lane only after a PASS or PASS_WITH_NOTES round, together with that round's review branch. A FAIL round's branch stays unmerged; the lane reads it with `git show`.
- **Allowed file set for Stage 1** = the lane's row in CONTRACT §1 ∪ `docs/plan/status/<slug>.md` ∪ its own production outputs (`results/records/<id>.json`, `results/arrays/<id>.npz` for IDs named in its brief §7, and `figures/task_<its task>_*.png`) ∪ (l6-lab only) `docs/plan/status/l6-shots/**`. `results/index.json`, `figures/quick/**`, `results/quick/**`, `notes/**`, `src/model.py|config.py|analysis.py` (after G0, except lane l0-core) are never allowed.
- **Record schema** (CONTRACT §6.2): `schema == "duq.record/v2"`, ID regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`, `convergence.converged == true` (or `null` + `notes`), ≥ 1 `cross_check` with `agree == (rel_diff <= tol)` and a stated `tol`, `numerics` with `rel_residual`, `edge_weight`, `cond_est`, `sector`, `sigma`, `k` for eigen records and `fit_window_us`, `gamma_stderr`, `rel_rms_residual` for fits, `provenance.dirty == false`, `provenance.platform` from `platform.platform()` (no hostname, no username).
- **Code you may call for spot-checks** (CONTRACT §3–§9): `src.config` constants (`G2` 4.79411, `KAPPA_B` 16.33628, `KAPPA_A` 0.0584336, `KAPPA_2` 5.6276, `EPS_D` 21.142 rad/µs), `src.model.one_mode/two_mode/vacuum2/coherent2/cat2`, `src.spectral.gamma_x/low_spectrum`, `src.analysis.fit_exp_offset/p_right_well`, `src.linresp.poles/ringing`. Prefer an **analytic formula** or a **hand-built dense Liouvillian** (snippet A) over the lane's own function: a check that calls the code under review is not independent.

## 5. Tests to write FIRST (TDD)
You write no tests (read-only lane). The TDD step for a reviewer is: **before reading the implementation**, write in your draft the *expected-evidence list*: every test name in the lane's brief §5 with its assertion and tolerance, every record ID in §7, every gate in §8, and the two spot-check values from the §6 matrix. Then verify each item exists and asserts what it should. A test that only calls `main()` or checks shapes, with no physics assertion and tolerance, is a **major** finding. A tolerance looser than the brief's (e.g. 1e-12 relaxed to 1e-8 in a symmetry test) is **major** unless the status file has an investigation note and a `DECISION NEEDED`.

## 6. Method, step by step
1. **Setup (2 min).** Cursor Agents window → New Agent → Worktree mode, base `standard-track`. Set the env (§9). `git switch --detach std/<slug>`; note `git rev-parse --short HEAD` as the reviewed commit and the start time (EDT). Check that `git log standard-track..std/<slug>` contains no merges of other lanes' branches.
2. **Stage 1: spec compliance (5–8 min).** Any FAIL item here is at least **major**; touching another lane's file or a frozen `src/` file is **critical**.
   - S1-1 Allowlist: `git diff --name-only standard-track...std/<slug>` ⊆ the allowed file set (§4). Any other file = FAIL. Deleted files = critical. For l0-core, `git diff standard-track...std/l0-core -- tasks/task_1_2.py` must be import lines only.
   - S1-2 Completeness: every function (brief §4), test (§5), record ID (§7, exact spelling per CONTRACT §6.3), figure, array and notebook the brief requires exists on the branch, **or** the producing job is listed under "Jobs to queue" with command, RAM estimate and output IDs (jobs > 15 min only).
   - S1-3 Nothing extra: no public functions, flags, files, dependencies or record IDs beyond the brief (minor; major if it changes a CONTRACT signature or adds a heavy dependency without a `DECISION NEEDED`). No committed `results/quick/` or `figures/quick/` content.
   - S1-4 Status file complete: `State: DONE` (or `DONE_WITH_CONCERNS` with the concern stated), commands with real trimmed output, records table (id, value, units, converged, cross-check), deviations, Jobs to queue (or "none"), 3 explain-back **questions only** (answers written by the agent = minor), open `DECISION NEEDED` blocks listed in your Notes.
3. **Stage 2: physics and numerics (10–15 min).** Mark every item OK / FINDING / N/A (with reason) and cite file:line.
   - S2-1 **2π only in `src/config.py`.** `git grep` for `TWO_PI`, `2 * jnp.pi`, `2*math.pi`, `2 * np.pi` outside config. Multiplying any input rate or frequency by 2π outside config = critical. Dividing an *output* by `C.TWO_PI` to display MHz (e.g. linresp `freq_MHz`) is OK only if commented.
   - S2-2 **Jump operators carry √rate**, built only via `src.model` (`loss_jumps`: √(κ_a(1+n_th))·a and √(κ_a n_th)·a†; √κ_b·b; √κ₂(a² − α²)). Hand-rolled `dq.destroy`/`jnp.sqrt` operators in `tasks/` = major; a missing √ = critical.
   - S2-3 **Sign convention α² = +ε_d/g₂** (`EPS_D = α²·G2 > 0`, cat on the real axis). For l5-circuit: g₂ < 0 from the prompt's bias must be stated as a gauge choice (pump phase π or flip ε_d), not silently dropped.
   - S2-4 **Drive quadrature (RESEARCH §4.1).** `eps_z·(a+a†)` only for readout / Z_L rotation; `eps_x·i(a†−a)` for well selection. **Any code, docstring, figure title or doc claiming ε(a+a†) prepares or selects a well = FAIL (critical).** "Tilt" language for 2.4b = critical.
   - S2-5 **Symmetry tests present and passing:** Re⟨a⟩ ≡ 0 under eps_z from vacuum (`max|Re<a>| < 1e-12`); ⟨b⟩₋(t) = −conj(⟨b⟩₊(t)) (l4a); Γ_X(ε_Z) even in ε_Z (l4b); even ∪ odd sectors = full spectrum (l1).
   - S2-6 **Convergence blocks at every α**, Na and Nb swept **separately** (`sweeps.Na` with fixed Nb, `sweeps.Nb` with fixed Na), chosen ≥ `needed`, two largest values within `rel_tol`. One record without a block = critical if it is a reported number.
   - S2-7 **Eigen acceptance:** `rel_residual < 1e-4`, `edge_weight < 1e-6`, stable across two truncations, κ_a > 0 guard (`gamma_x` raises `ValueError` at κ_a = 0), odd block for Γ_X, `full_deflated` (or a small positive σ) when ε ≠ 0. No value below the precision floor (two-mode ~1e-13·‖L‖; one-mode capped near α ≈ 2.7).
   - S2-8 **Fits:** parity fitted with `fit_exp_offset` (A·e^{−Γt} + C; steady parity 1/cosh 2α² = 0.2658 at α = 1.0); fit windows stated in code and in `numerics.fit_window_us`; time-domain Γ_X starts at t₀ ≥ 3 µs, window 50–100 µs, repeated at rtol 1e-8 and 1e-10; α = 0.6 excluded.
   - S2-9 **Rate conventions:** Γ_X = −λ₁ = decay of Re⟨a⟩; Dubovitskii per-direction = Γ_X/2; Γ_Z = parity decay = 2κ_aα²coth(2α²) (per-direction κ_aα², Felis `k1*nbar`); Y_L decays at **Γ_Z − Γ_X** (never Γ_Z + Γ_X). A factor-2 mix-up = major.
   - S2-10 **Units in records:** rates `1/us`, times `us`, frequencies `MHz` (or `kHz`), counts `photons`, ratios `dimensionless`; `params` from `std_params`.
   - S2-11 **Provenance:** run the records validator (§9); `dirty == false`; `git_commit` is an ancestor of the branch head; no hostname or username anywhere.
   - S2-12 **Tests assert physics** (analytic predictions as assertions with tolerances), and fast tests stay small (lane share of the < 2 min total).
   - S2-13 **`--quick` ≤ 2 min** (time it), writes only to `results/quick/` and `figures/quick/` (`record(..., quick=True)`, `save(..., quick=True)`). Over 2 min or writing production paths = minor / major.
   - S2-14 **No silent caps or swallowed exceptions:** no bare `except: pass`, no `except Exception` that hides a solver failure, no silent clipping of α ranges or truncations (e.g. at `NA_EIG_MAX`) without a record note, no ignored `max_steps` exhaustion.
   - S2-15 **Figures labelled with units** (µs, 1/µs, MHz, α²); open each committed PNG.
4. **Run the lane's commands (5–10 min).** Per the matrix below; paste the pytest summary line and quick wall time. At most 3 heavy jobs on the laptop and only one sparse LU > 3 GB: check `& $env:DUQ_PY -m tools.runq status` before `-m slow`.
5. **Independent spot-checks (5 min):** recompute 2 numbers per lane (matrix) by an analytic formula or a smaller independent run; state value, method, rel_diff, tol.
6. **Optional Gemini** (if `$env:GEMINI_API_KEY` is set): §9 command. Summarize its findings in Stage 2 (accept, reject with reason); do not commit its `reviews/gemini-*.md` output.
7. **Verdict and write-up (3 min):** switch to `review/<slug>-r<N>`, write the file, commit (§9).

**Lane matrix** (test file = `tests/test_<slug with - → _>.py`; run `-q`, plus `-m slow` for physics lanes):

| Lane | Run (besides pytest) | Stage-2 focus (must see) | Spot-check 1 | Spot-check 2 |
|---|---|---|---|---|
| l0-core | `-m tasks.task_1_2 --quick` | S2-2, S2-4, S2-5 (eps_z one-mode and two-mode vacuum tests at 1e-12), intro H/jumps unchanged, `trunc_for` table, provenance without hostname | `KAPPA_2 = 4·G2²/KAPPA_B = 5.6276` rad/µs (κ₂/2π = 0.8957 MHz) | `p_right_well(|α=1⟩⟨α|, N=30) = (1+√(1−e⁻⁴))/2 = 0.99540` (tol 1e-6) |
| l0-tools | `-m tools.check_claims` on the intro claims | CONTRACT §11 steps 1–7 enforced (sig-fig rounding, converged, ≥1 agreeing cross_check, dirty, `illustrative` = warning); runq one big job at a time, no auto-retry | wrapped `t1_3a.gamma_z.td.two_mode.a2.10` value == `results/task_1_3a.json` 0.5134564726057531 | temp doc under `$env:TEMP` with `` `rec:t1_3a.gamma_z.td.two_mode.a2.10=0.5135` `` exits 0; with `=0.5134` exits ≠ 0 |
| l1-spectral | `-m tasks.task_spectral_profile --quick` | S2-5 (sector union), S2-7, dense = sparse, L·vec(ρ) = mesolve RHS, κ_a = 0 raises, cost/RAM profile, `NA_EIG_MAX` proposed in status (not edited) | snippet A: one-mode N=40, α=1.0: −λ₁ = 2.2819e-3 (rel 1e-3) | `gamma_x` at two-mode 20×6, α=2.1 gives ≈7.6e-6 **with edge_weight ≥ 1e-6** (the trap is flagged) |
| l2a-gamma-z | `-m tasks.task_2_2 --quick` | start `cat2(+1)`, S2-8 offset fit, within 2% of 2κ_aα²coth2α² at every α, even-block `rates[1]` cross-check | Γ_Z(1.0) = 0.116867·coth 2 = 0.12123 /µs | Γ_Z(2.1) = 0.51538 /µs; fitted C at α=1.0 ≈ 1/cosh 2 = 0.2658 |
| l2b-gamma-x | `--quick` of `task_2_1_eig`, `_td`, `_channels`, `_thermal` | S2-6 at every α, S2-7, S2-8 td window, anchors (RESEARCH §5 table), thermal √ jumps, channel formulas, Dubovitskii ×2 | channel 1 at α=1.4: κ_aα²(coth 3.92 − 1) = 9.021e-5 = 84% of one-mode 1.0744e-4 | α=2.1 two-mode record ≈3.88e-7 (28×8; 3.99e-7 at Nb=6), never the 20×6 value 7.6e-6 |
| l3-prep | `-m tasks.task_1_3b --quick`, `-m tasks.task_lab_frames --quick` | **S2-4 critical**, eps_z test 1e-12, eps_x gives Re⟨a⟩ > 0, p_right via committor or ½(1+⟨Z_L⟩), 1.3c table, Wigner ≤ 81×81 | snippet B: `two_mode(12, 4, eps_z=0.2·G2)` from vacuum, 0.5 µs: max abs Re⟨a⟩ < 1e-12 | p_right of |2.1⟩⊗|0⟩ at t=0 = (1+√(1−e^{−17.64}))/2 = 1 − 5.5e-9; ideal-displacement record ≥ 0.999 |
| l4a-readout | `-m tasks.task_2_3 --quick` | stabilize 3 µs then switch eps_z on; ⟨b⟩₋ = −conj⟨b⟩₊ test; linear to ~g₂; S17 within 5%; κ_a offset ≈0.003i handled | λ = −κ_b/4 ± i√(4g₂²α² − κ_b²/16) = −4.0841 ± 19.717i /µs → 3.138 MHz, Q = 2.465, t₅% = ln20/(κ_b/4) = 0.7335 µs, t₁% = 1.1276 µs | ⟨b⟩_ss(+α) = −ε_Z/(2αg₂) = −0.02381 at ε_Z = 0.1g₂, α=2.1; DC gain −1/(2g₂α) = −0.04967 µs |
| l5-circuit | `-m tasks.task_2_4a --quick` | exact BCH normal ordering, displaced frame before RWA, S2-3 sign as gauge, factor ½ settled numerically, dt ≲ 10 ps over 150–200 ns | g₂ = −½·40000·0.035·0.06²·0.3·e^{−0.0468} = −0.7215 MHz; ε_p = 0.0370 for 0.763 MHz | integer solutions of 5Δa + 6Δb = ±4 with abs(Δa)+abs(Δb) ≤ 7 are only ±(2, −1): the a²b† family only |
| l4b-tradeoff | `-m tasks.task_2_4b --quick` | S2-4 (no tilt), S2-5 evenness, S2-7 `full_deflated`, Dubovitskii overlay ×2, S18 overlay, SNR = κ_b∫abs(Δb)²dt, grid in Jobs to queue | 16×4, α=1.0, ε_Z = ±0.5g₂ via `low_spectrum(..., "full_deflated")`: Γ_X equal to rel 1e-4 | S18: Γ_Z(ε_Z) − Γ_Z(0) = 2ε_Z²/(κ₂α²) = 0.04167 /µs at α=1.4, ε_Z = 0.1g₂ |
| l4c-capstone | `--quick` of `task_2_4c_pulses`, `task_2_4c_verify` | SVD pulse from R_b, matched-cost comparison on the **two-mode** model at a converged truncation, td flip check at α=1.0, claim only if it beats square | `numpy.linalg.svd(R_b)`: σ_max² ≥ ‖R_b ε_sq‖²/‖ε_sq‖² for the square pulse (exact) and = the lane's gain (rel 1e-6) | `energy` of a square pulse = A²T; `snr` of constant Δb = κ_b·Δb²·T (Δb = 0.0476, T = 1 µs → 0.0370) |
| l6-lab | in `site/`: `npm ci; npm run build; npm run build:single`; open the single file from `file://` | no physics in readers; data bundled, never fetched (`git grep -n "fetch(" -- site/src`); shapes = CONTRACT §13; smoke shots in `status/l6-shots/` | `records.json` count == records in `results/index.json`; one value identical | Wigner frames ≤ 81×81, 4 decimals; bundle < 8 MB |
| l7-docs | `& $env:DUQ_PY -m tools.check_claims --files TECHNICAL.md README.md --strict` exits 0 | S2-4/S2-9 wording, rate-convention table, Y_L at Γ_Z − Γ_X, no "tilt", AI disclosure, notebooks 01–04 setup cell only | open 2 tagged records by hand: rounding, converged, agreeing cross_check | no untagged numbers in results tables (`git grep -n -E "[0-9]\.[0-9]+e-[0-9]" -- README.md TECHNICAL.md`, each hit has `rec:`) |
| l8-felis | its script in the Felis venv (its brief §9) | Hz/1/s conversion with no new 2π (κ₁ = `C.KAPPA_A`·1e6 /s), per-Pauli vs our Γ_X, Z per direction = Γ_Z/2 | Z: k1·n̄ = 0.0584336·4.41 = 0.25769 /µs = Γ_Z/2 | X+Y: 1.1e-3·n̄·κ₁e^{−2n̄} = 4.188e-8 /µs vs channel 2 per direction (κ₁²/2κ₂)e^{−2n̄} = 4.482e-8: ratio 0.934 at our κ₁/κ₂ = 0.01038 (0.970 at 0.01, RESEARCH's "~3%"); **not a bug**. Emulator misses the ×3.3 two-mode factor at α=2.1 |

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
No records, figures, arrays or jobs. Quick outputs you trigger stay git-ignored. The only output is `docs/plan/status/reviews/<slug>.md` on `review/<slug>-r<N>`, in exactly this shape:
```markdown
# Review `<slug>` round <N>: <PASS | PASS_WITH_NOTES | FAIL>
| Lane | Reviewed commit | Base | Reviewer model | Start–end (EDT) | Prior rounds |
|---|---|---|---|---|---|
## Verdict
<one line>. Blocking findings: F2, F5 (or "none"). Rule: FAIL if any critical/major; PASS_WITH_NOTES if only minor; PASS if none.
## Stage 1 findings
| Item | Result | Evidence |   (S1-1 … S1-4)
## Stage 2 findings
| Item | Result (OK / FINDING / N/A + reason) | Evidence (file:line) |   (S2-1 … S2-15)
### Findings
F<n> [critical|major|minor] `path/file.py:LINE`: what is wrong. Evidence: <command/output>. Fix: <concrete change, ≤ 30 min>.
## Commands run + results
<exact commands; trimmed real output: pytest summary lines, quick wall times, validator table, Gemini summary>
## Independent spot-checks
| Quantity | Lane value (record id) | Independent value | Method | rel_diff | tol | OK |
## Notes for Claude's later review
- tolerances near their edge; anchors that moved; open DECISION NEEDED blocks; items not checked and why; "abbreviated" if §11 cut applied
- 3 hardest judge questions on this lane (questions only; Harshit answers in docs/defense.md)
```
Severities follow `REVIEW_PROTOCOL.md` §2: **critical** = a wrong number or wrong physics could reach the talk, or another lane's file was touched, or `dirty: true` production records; **major** = a gate unmet or unverifiable, a missing required item, tests without physics assertions, a factor-2 convention error, a loosened tolerance, an offset-free parity fit; **minor** = units missing on a figure, quick > 2 min, commit prefix, extras not in the brief, notebooks that recompute by default.

## 8. Acceptance gates (ALL must pass before DONE)
1. Stage 1 then Stage 2, both complete: every S1-x and S2-x row has OK / FINDING / N/A with a reason.
2. The pytest command(s) and every `--quick` script of the lane were actually run (or the reason why not is stated), with real output pasted.
3. The records validator ran over every record the lane added, and its table is pasted.
4. ≥ 2 independent spot-checks per lane, each with value, method, rel_diff and tol.
5. Every finding has file:line, severity and a concrete fix; the verdict follows the rule exactly.
6. `git status --porcelain` shows no tracked modifications before the switch; the only commit is the review file on `review/<slug>-r<N>`.
7. Start and end times recorded; 15–30 min (≤ 40 min hard stop).

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
$slug = "l2a-gamma-z"; $N = 1; $t = "tests/test_$($slug -replace '-','_').py"
git switch --detach "std/$slug"; git rev-parse --short HEAD
# Stage 1
git diff --name-only "standard-track...std/$slug"; git diff --stat "standard-track...std/$slug"
git log --oneline "standard-track..std/$slug"
# Stage 2: tests, quick, greps
& $env:DUQ_PY -m pytest $t -q; & $env:DUQ_PY -m tools.runq status; & $env:DUQ_PY -m pytest $t -q -m slow
Measure-Command { & $env:DUQ_PY -m tasks.task_2_2 --quick | Out-Host }
git grep -n -E "TWO_PI|2 ?\* ?(jnp|np|math)\.pi" -- src tasks tools ":!src/config.py"
git grep -n -E "options=|platform\.node|gethostname|getpass|USERNAME" -- src tasks tools
git grep -n -E "except[^:]*:\s*(pass)?\s*$" -- src tasks tools
git grep -n -E "dq\.destroy|dq\.create|eps_d|eps_z" -- tasks
git grep -n -i -E "tilt|Gamma_Z \+ Gamma_X|Γ_Z \+ Γ_X" -- tasks src docs README.md TECHNICAL.md
& $env:DUQ_PY -m tools.check_claims          # l7-docs (and l0-tools)
if ($env:GEMINI_API_KEY) { & $env:DUQ_PY tools/ai_review.py --provider gemini --diff (git merge-base standard-track HEAD) }
# (the brief-level form `--diff standard-track` diffs src/ and tasks/ against the working tree; the merge-base avoids reversed upstream changes)
# Finish
git status --porcelain
git switch -c "review/$slug-r$N" standard-track
# write docs/plan/status/reviews/$slug.md now
git add "docs/plan/status/reviews/$slug.md"; git commit -m "[reviewer] $slug r${N}: FAIL"
```
**Records validator** (prints one line per record added by the lane; exit 1 on any failure):
```powershell
@'
import json, math, os, re, subprocess as sp
ps = [p for p in sp.run(["git", "diff", "--name-only", "standard-track...HEAD", "--", "results/records"],
      capture_output=True, text=True).stdout.split() if p.endswith(".json")]
bad = 0
for p in ps:
    r = json.load(open(p, encoding="utf-8")); e = []; rid = r.get("id", "")
    pv, cv, nm = r.get("provenance", {}), r.get("convergence"), r.get("numerics") or {}
    if r.get("schema") != "duq.record/v2" or rid != os.path.basename(p)[:-5]: e.append("schema/id")
    if not re.fullmatch(r"[a-z0-9_]+(\.[a-z0-9_\-]+)*", rid): e.append("id regex")
    if not math.isfinite(r.get("value", float("nan"))) or not r.get("units"): e.append("value/units")
    if pv.get("dirty") is not False: e.append("dirty")
    if sp.run(["git", "merge-base", "--is-ancestor", pv.get("git_commit", "x"), "HEAD"], capture_output=True).returncode: e.append("commit not on branch")
    if any(v and v in json.dumps(pv) for v in (os.environ.get("COMPUTERNAME"), os.environ.get("USERNAME"))): e.append("host/user")
    need = {"Na", "Nb"} if ".two_mode" in rid else {"Na"}
    if cv is None and not r.get("notes"): e.append("null convergence, no notes")
    if cv is not None and not (cv.get("converged") is True and need <= set(cv.get("sweeps", {}))): e.append("convergence")
    xc = r.get("cross_check") or []
    if not any(c.get("agree") is True for c in xc) or any("tol" not in c or c["agree"] != (c["rel_diff"] <= c["tol"]) for c in xc): e.append("cross_check")
    if ".eig." in rid and not (nm.get("rel_residual", 1) < 1e-4 and nm.get("edge_weight", 1) < 1e-6): e.append("eigen acceptance")
    if ".td." in rid and "gamma" in rid and "fit_window_us" not in nm: e.append("fit window")
    bad += bool(e); print(("FAIL " if e else "ok   ") + rid, r.get("value"), r.get("units"), e)
raise SystemExit(1 if bad else 0)
'@ | & $env:DUQ_PY -
```
**Snippet A** (dense one-mode Liouvillian, independent of `src.spectral`; ~5 s): `import src.config as C, numpy as np; from src.model import one_mode; H, J, a = one_mode(40, C.KAPPA_2, 1.0, kappa_a=C.KAPPA_A); M = lambda x: np.asarray(x.to_numpy(), dtype=complex); H = M(H); I = np.eye(40); L = -1j*(np.kron(I, H) - np.kron(H.T, I))`, then for each jump `j = M(J_k)`, `d = j.conj().T @ j`: `L += np.kron(j.conj(), j) - 0.5*np.kron(I, d) - 0.5*np.kron(d.T, I)`; `print(np.sort(-np.linalg.eigvals(L).real)[:4])` → about `[0, 2.2819e-3, 0.1190, 0.1212]` (column stacking, RESEARCH §9).
**Snippet B** (symmetry, ~seconds): `H, J, (a, b) = two_mode(12, 4, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=0.2*C.G2)`; `r = dq.mesolve(H, J, vacuum2(12, 4), jnp.linspace(0, 0.5, 51), exp_ops=[a])`; `abs(r.expects[0].real).max() < 1e-12`. Run snippets as here-strings piped to `& $env:DUQ_PY -`, importing `src.config` first.

## 10. Out of scope / do not
- Never edit code, tests, notebooks, records, figures, CONTRACT, RESEARCH, briefs or any status file except your review file, even for a one-character fix. Describe the fix; the lane applies it.
- Never run production jobs, submit to `runq`, run `build_index`, push, merge or rebase. Never commit `reviews/gemini-*.md` or quick outputs.
- Never "pass with a promise": a gate the lane says it will meet later is FAIL now (unless it is a listed > 15 min job in Jobs to queue and the quick run plus a smaller cross-check already support the method).
- Never suggest loosening a tolerance to make a test pass; ask for the investigation instead.
- Do not answer `DECISION NEEDED` blocks or re-plan the lane; do not review the integrator's merges (Claude does, per `REVIEW_PROTOCOL.md`).
- No secrets in the review file (never echo `GEMINI_API_KEY`); nothing from `notes/`.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write it in your review file under Notes, and tell Harshit in one line:
> **DECISION NEEDED (reviewer, `<slug>` r<N>):** <one-line question>
> **Options:** A) … B) …  **Recommendation:** …  **Blocking merge?** yes/no
- **Brief and CONTRACT disagree:** CONTRACT wins; record a finding against the brief, not the lane, plus a DECISION NEEDED.
- **Environment broken** (imports fail on `standard-track` too): not the lane's fault; withhold the verdict, tell the integrator, stop.
- **Compute busy** (3 heavy jobs or a > 3 GB LU running): run fast tests, quick runs and spot-checks now; run `-m slow` when a slot frees. If it cannot run within the cap, accept the lane's pasted slow-test output, mark "slow not rerun (compute)", and cap the verdict at PASS_WITH_NOTES.
- **Anchor does not reproduce:** major finding unless the status file has an investigation note and a DECISION NEEDED; then note it for Claude.
- **Round 3 still FAIL:** stop reviewing; DECISION NEEDED to Harshit (re-brief, model bump, or cut per PLAN §8).
- **Cut line** (after 7:00 AM, or ≥ 3 lanes waiting): abbreviated review = full Stage 1 + validator + fast tests + S2-1, S2-4, S2-6, S2-7, S2-11 + one spot-check; verdict at most PASS_WITH_NOTES; mark "abbreviated". **Never** skip Stage 1, the 2π grep, the drive-quadrature check or the dirty check. After the 8:00 AM freeze, review only l7-docs and l6-lab.
- **Re-review after FAIL:** review only `git diff <reviewed_sha>..std/<slug>` plus the checklist items it touches, rerun S1-1 (one command) and the failing tests, and list the prior findings as fixed / not fixed.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE, `docs/plan/status/reviews/<slug>.md` on `review/<slug>-r<N>` holds: the header table (lane, reviewed commit, base, model, times, prior rounds); the verdict line with blocking findings; S1-1…S1-4 and S2-1…S2-15 tables; numbered findings with file:line, severity and fix; the exact commands and trimmed output (pytest summaries, quick wall times, validator table, Gemini summary if run); the spot-check table; Notes for Claude, including 3 lane-specific judge questions. Then post one line to Harshit / the integrator: `Review <slug> r<N>: <VERDICT>; blocking <F#s or none>; branch review/<slug>-r<N>`. On FAIL the lane reads it with `git show review/<slug>-r<N>:docs/plan/status/reviews/<slug>.md`.

Explain-back questions on the review process itself (Harshit answers in `docs/defense.md`):
1. Why do we accept λ₁ on a relative residual below 1e-4 plus an edge weight below 1e-6, instead of an absolute residual, and what would a 20×6 basis have reported at α = 2.1 without the edge-weight check?
2. What antiunitary symmetry forces Re⟨a⟩ ≡ 0 under an ε(a+a†) drive started from vacuum, why is the vacuum invariant under it, and why does the i(a†−a) drive escape it?
3. Our Γ_X, Ferrari's Γ_bf, Dubovitskii's rate and Felis's per-Pauli rates differ by factors of 2: how do you convert each into ours, and why does Y_L decay at Γ_Z − Γ_X rather than Γ_Z + Γ_X?
