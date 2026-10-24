# Brief `l4c-capstone`: Task 2.4c/d capstone. Beat the readout trade-off with a provably optimal linear-response pulse

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l4c-capstone`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/10-l4c-capstone.md`, then execute this brief exactly. Keep `docs/plan/status/l4c-capstone.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l4c-capstone` | `std/l4c-capstone` | `l0-core`, `l4a-readout` (`src/linresp.py`). Optional: `l4b-tradeoff` grid (`results/arrays/t2_4b.grid.npz`) and `l1-spectral` | strongest reasoning model | 3 h of lane work (the gradient refinement is a separate 2 h cap) | Phase 2, while Harshit is awake. Target **1:30 AM (G2)** for the linear-response frontier and two-mode validation. The flip check and gradient refinement may run overnight through the queue. |

## 1. Goal and why
Task 2.4c asks: *propose and numerically demonstrate a strategy to improve readout contrast and/or speed without significantly degrading Γ_X*. Task 2.4d asks: *justify why it works, using your simulations as evidence*. This is the most "ingenuity"-judged item of the Standard Track.

Our strategy has three steps:
1. **Understand the plant.** Linearized about a well, the memory–buffer pair is a damped resonator. The poles are λ = −4.08 ± 19.72i /µs: it rings at **3.14 MHz** with **Q ≈ 2.46**, and it is underdamped because 8g₂α = 80.5 > κ_b = 16.3 rad/µs (RESEARCH §7). A square ε_Z pulse excites that ringing: it settles slowly (1% in 1.13 µs) and wastes drive.
2. **Optimize where the math is exact.** The readout signal Δ⟨b⟩(t) = ⟨b⟩₊ − ⟨b⟩₋ is *linear* in the drive ε_Z(t) (up to about g₂). Write that linear map as a matrix R_b. Its top right-singular vector is the pulse that maximizes signal energy (∝ SNR) per unit drive energy. Its top generalized eigenvector against R_a (memory displacement) maximizes signal per unit leakage proxy. Both are **provably optimal within linear response**. An ML person can explain this in one sentence: "R is the linear map from pulse to signal; its top singular vector is the input it amplifies most."
3. **Verify on the full two-mode model** at a converged truncation, and **measure the bit-flip cost directly** (time-domain flip check at α = 1.0), not only through the quasi-static eigen proxy.

Claim a win **only** if a candidate beats the best square pulse at matched cost on the two-mode model. Otherwise, present the frontier honestly.

## 2. Read first
- `AGENTS.md`; `docs/plan/CONTRACT.md` §1 (allowlist), §6 (records), §9 (`src/linresp.py`), §10 (`src/pulses.py`).
- `docs/plan/RESEARCH.md`:
  - §4.3 readout symmetry (⟨b⟩₋ = −⟨b⟩₊*; Γ_X even in ε_Z, no tilt);
  - §7 readout and linear response (S17, S18, poles, transfer function, SNR definition, signal size);
  - §9 numerics (gradient cost);
  - §2 dynamiqs API (`dq.pwc`, gradients).
- `src/linresp.py` and `tasks/task_2_3.py` (lane l4a), `src/model.py` (`two_mode`, `coherent2`, `drive_ops`), `src/analysis.py` (`leakage`, `code_projector`), `src/results.py`.
- If merged: `tasks/task_2_4b.py` and `results/arrays/t2_4b.grid.npz` (lane l4b), plus `docs/derivation_2_4a.md` (lane l5) for the notebook's 2.4a summary.

## 3. Allowlist (touch nothing else)
- `src/pulses.py`
- `tasks/task_2_4c_pulses.py` (candidates, linear-response frontier, matched-cost comparison)
- `tasks/task_2_4c_verify.py` (two-mode validation, flip check, optional gradient refinement, optional κ_b option)
- `notebooks/09_task_2_4_readout_design.ipynb`
- `tests/test_l4c_capstone.py`
- `docs/plan/status/l4c-capstone.md`
- Your own production outputs: `results/records/t2_4c.*.json`, `results/arrays/t2_4c.*.npz`, `figures/task_2_4c_*.png`.

## 4. Interfaces you implement / rely on
Implement in `src/pulses.py` (CONTRACT §10). All pulse functions return `(edges_us, values)`: `n_bins + 1` monotone bin edges in µs, and `n_bins` amplitudes in rad/µs. This is directly usable as `dq.pwc(edges_us, values, X)`, where X = a + a†, and by `src.linresp.response`. Check `dq.pwc`'s expected `times` length against the dynamiqs 0.3.7 docs (RESEARCH §2), and document the convention in the docstring.
```python
def square(T, amp, n_bins)
def ramp(T, amp, tau, n_bins, kind="cos")      # rises over tau ("cos": 0.5(1-cos(pi t/tau)); "lin": t/tau), then holds amp
def clear(T, kick_amp, kick_t, hold_amp, n_bins)  # kick_amp for t < kick_t, then hold_amp (CLEAR-style ring-up)
def from_bins(values, T)                         # uniform edges for arbitrary bin values (SVD / optimizer output)
def energy(edges, values) -> float               # ∫ε² dt
def snr(t, delta_b, kappa_b) -> float            # κ_b ∫|Δ⟨b⟩|² dt (ideal mode-matched heterodyne, unit efficiency)
def leakage_proxy(t, da) -> float                # ∫|δa|² dt
```
Rely on `src/linresp.py` (lane l4a; CONTRACT §9):
- `poles`, `ringing`, `dc_gain`, `response(eps_t, t, g2, kappa_b, alpha, well)`.
- `response_matrices(T, n_bins, n_samples, g2, kappa_b, alpha) -> (R_b, R_a)`, where Δb = b(+α) − b(−α) and R_a maps to δa of the +α well.
- `optimal_pulse(R_b, R_a=None, energy=1.0) -> (eps_bins, gain)`.

Rely on `src.model.two_mode` and `src.model.drive_ops`. For time-dependent drives, build `H = H0 + dq.pwc(edges, values, X)` with `X, _ = drive_ops(a)`, and pass it to `dq.mesolve`.

## 5. Tests to write FIRST (TDD), in `tests/test_l4c_capstone.py`
- `test_pulse_shapes_and_energy`:
  - `square(1.0, 2.0, 40)` has energy 4.0 to 1e-12.
  - `ramp(..., kind="cos")` starts at 0 and reaches `amp` at `tau`.
  - `clear` has the right piecewise values.
  - Edges are monotone with length `n_bins + 1`.
- `test_snr_known_signal`: Δb(t) = 0.1 constant over T = 1 µs with κ_b = 16.33628 gives SNR = 0.1633628, to 1e-6 (trapezoid on a fine grid).
- `test_svd_gain_ge_square_gain_equal_energy`: with `R_b` from `response_matrices(T=1.0, n_bins=40, n_samples=200, ...)` at nominal parameters, `||R_b ε_svd||² ≥ ||R_b ε_square||²` at equal `||ε||²`. This must hold mathematically (Rayleigh quotient). Allow a 1e-12 relative slack.
- `test_generalized_pulse_ratio_ge_square`: `||R_b ε||²/||R_a ε||²` for the generalized pulse ≥ the same ratio for the square pulse (Tikhonov δ = 1e-9·trace).
- `test_svd_pulse_spectrum_reported` (diagnostic, **not** a hard physics claim): compute the FFT peak frequency of the SVD pulse. Assert only that it is finite and positive, and write it to the test log. The 3.14 MHz expectation is checked and reported in the status file. **Verify, don't assume.**
- `@pytest.mark.slow test_linresp_vs_two_mode_small_amplitude`:
  - two-mode Na = 16, Nb = 5, α = 2.1;
  - prepare each well 3 µs, then apply a square ε = 0.1·g₂ for 1 µs;
  - Δ⟨b⟩(t) agrees with `linresp.response` within 10% (RMS relative over t ∈ [0.2, 1] µs), after subtracting the ε = 0 baseline.
- `@pytest.mark.slow test_readout_symmetry_with_pulse`: for a short CLEAR pulse at Na = 14, Nb = 5, ⟨b⟩₋(t) = −conj(⟨b⟩₊(t)) to 1e-9 (RESEARCH §4.3).

## 6. Method, step by step
1. **Branch and status.** Run `git switch -c std/l4c-capstone`, create the status file from `_TEMPLATE.md`, and set the state to `IN_PROGRESS`.
2. **Write the tests (§5), watch them fail, then implement `src/pulses.py`.**
3. **Linear-response frontier** (`tasks/task_2_4c_pulses.py`; fast, pure linear algebra). Run at α = 2.1 (main) and α = 1.0 (flip-check point), and T ∈ {0.5, 1.0, 2.0} µs.
   - **Candidates:**
     - (a) Square, swept over amplitude.
     - (b) Cosine and linear ramps with τ ∈ {0.1, 0.2, 0.4, 0.8} µs.
     - (c) CLEAR-style: `kick_amp ∈ {1.5, 2, 3} × hold`, `kick_t ∈ {0.05, 0.10, 0.16}` µs (0.16 µs is half the ringing period).
     - (d) **SVD** pulse: `optimal_pulse(R_b)`.
     - (e) **Generalized** pulse: `optimal_pulse(R_b, R_a)`.
   - **For each candidate**, compute with `linresp.response` for both wells:
     - Δb(t), SNR(T) = κ_b∫|Δb|²dt, ∫ε²dt, ∫|δa|²dt;
     - the settling time of Δb to its final plateau (if any);
     - the pulse spectrum.
   - **Matched cost.** Scale every candidate's amplitude so that it is equal to the reference square pulse under each cost:
     - (i) drive energy ∫ε²dt;
     - (ii) leakage proxy ∫|δa|²dt;
     - (iii) quasi-static bit-flip cost C_X = ∫[Γ_X(ε(t)) − Γ_X(0)]dt. Take Γ_X(ε) from the l4b grid `results/arrays/t2_4b.grid.npz` (keys `alpha, eps_over_g2, gamma_x, ...`), with a cubic spline in ε² because Γ_X is even in ε. **If l4b isn't merged yet,** use Dubovitskii's ΔΓ_X ≈ 2·(2ε²/(κ₂α²))e^{−2α²} (our convention is 2× per-direction), mark those records' notes `illustrative: analytic cost proxy until l4b grid lands`, and list a re-run under Jobs to queue.
   - **Output:**
     - the frontier: SNR(T) against each cost, square sweep as a line, families and optimal pulses as points;
     - a table: name, SNR at T = 1 µs, gain over square at matched cost (i)/(ii)/(iii).
   - **Keep amplitudes in the linear regime:** ≲ g₂ (= 4.794 rad/µs). Flag any candidate that needs more.
4. **Plain-words explanation** (into the status file and the notebook), drafted for Harshit:
   - Why the optimum concentrates near the 3.14 MHz pole: the transfer function H(s) = −2g₂α/(s² + (κ_b/2)s + 4g₂²α²) has |H| at resonance ≈ Q × DC ≈ 2.5× the DC gain.
   - Why ramps reduce leakage: no sharp edges, so less broadband excitation of δa.
   - What the generalized pulse trades: signal against displacement out of the well.
5. **Two-mode validation** (`tasks/task_2_4c_verify.py --stage validate`; this is 2.4d).
   - For each finalist (best square, best ramp, best CLEAR, SVD, generalized) at α = 2.1 and T = 1 µs:
     - Prepare each well: evolve `coherent2(Na, Nb, ±α)` for 3 µs with ε = 0.
     - Apply the pulse via `dq.pwc` from the final state.
     - Record ⟨b⟩±(t), Δb, SNR, leakage `1 − Tr(Π_code ρ_a)` via a `save_extra` callback, and the truncation monitors.
   - **Truncation:** start from `C.trunc_for(2.1, 'steady')`; Nb ≥ 8. Check one larger Na and Nb, and record a convergence block on SNR (`rel_tol` 1e-2).
   - **Gate:** linear-response SNR matches two-mode SNR within 10% for amplitudes ≲ g₂. A larger mismatch is a finding: report it, don't hide it.
6. **Direct bit-flip cost check at α = 1.0** (`--stage flipcheck`), where Γ_X ≈ 2.3e-3 /µs is measurable (RESEARCH §5).
   - Start from `coherent2(Na, Nb, +1.0)` at Na = 16, Nb = 6 (verify with one larger).
   - Apply a train of N = 20 identical pulses, each of length T = 1 µs, separated by 1 µs gaps, using `dq.pwc` and `C.METHOD_LONG`.
   - Compare Re⟨a⟩ at the end of the 40 µs train with an undriven run of the same duration.
   - Re⟨a⟩ ∝ ⟨Z_L⟩ decays at Γ_X, so the extra Γ_X integrated over the train is ΔΓ_X·t = ln(Re⟨a⟩_undriven / Re⟨a⟩_driven).
   - Extra per-direction flip probability per pulse: p_flip ≈ ½·ln(ratio)/N.
   - Compare with the quasi-static estimate ½·∫ΔΓ_X dt per pulse.
   - Do this for the best square pulse and the winning candidate at matched cost (iii). It catches switching transients the quasi-static proxy misses.
   - Repeat once at rtol 1e-10/atol 1e-12. If the effect is below that integration noise floor, say so.
7. **Optional gradient refinement** (`--stage gradient`; cut line 2; **hard cap 2 h**).
   - Optimize 20 to 50 `dq.pwc` bins with `optax.adam`, using `jax.value_and_grad` through two-mode `mesolve` at 16×4 to 20×5, T = 1 µs.
   - Objective: maximize SNR − λ·C, with the amplitude bounded via `amp_max·tanh(θ)` and a smoothness penalty Σ(Δθ)².
   - Warm-start from the SVD pulse. The pattern is the dynamiqs Kerr-oscillator GRAPE tutorial (RESEARCH §2).
   - **Verify the result at a larger truncation**, since an optimizer can exploit truncation. Report the improvement over the SVD pulse; if it is < 5%, say "linear-response optimum already near-optimal".
8. **Optional hardware-level option** (`--stage kappa_b`; cut line 6). Critical damping κ_b = 8g₂α (κ_b/2π ≈ 12.8 MHz at α = 2.1).
   - **Note:** κ₂ = 4g₂²/κ_b changes too.
   - Compute the settling time and SNR with linresp.
   - Compute Γ_X(κ_b) via `src.spectral.gamma_x` at α ∈ {1.0, 1.4} (needs l1-spectral) for κ_b/2π ∈ {2.6, 5, 8, 12.8} MHz.
   - Present it as a discussion-level trade-off: faster readout against a changed confinement.
9. **Figures:**
   - `figures/task_2_4c_pulses.png`: shapes, plus spectra with the 3.14 MHz pole marked.
   - `figures/task_2_4c_comparison.png`: SNR against cost (i), (ii) and (iii) frontiers; square sweep line against the family points and the SVD and generalized points.
   - `figures/task_2_4c_validation.png`: linear-response vs two-mode Δb(t) for the finalists, with the flip-check bar chart inset.
10. **Notebook** `notebooks/09_task_2_4_readout_design.ipynb`:
    - Use the thin-wrapper pattern of notebooks 01 to 04, with a re-run-safe setup cell: `if not os.path.isdir('src'): os.chdir('..')`.
    - `RERUN = False` loads the records.
    - Sections:
      - 2.4a summary (load `t2_4a.*` records and link `docs/derivation_2_4a.md`);
      - 2.4b trade-off (load `t2_4b.*` records and `t2_4b.grid.npz`);
      - 2.4c candidates and frontier;
      - 2.4d validation and why it works.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
**Records** (CONTRACT §6.3). Use `params = std_params(alpha=..., eps_z=<peak amplitude>)` plus `pulse=<name>` and `T_us`.
- `t2_4c.snr.linresp.two_mode.a{α:.2f}.p{name}.T{T:.1f}us`.
  - Convergence `null` with notes "linear response, truncation-free".
  - cross_check: the matching two-mode `td` record, tol 0.10.
- `t2_4c.snr.td.two_mode.a{α:.2f}.p{name}.T{T:.1f}us`.
  - Convergence block over Na/Nb.
  - cross_check: the linresp value, tol 0.10.
- `t2_4c.cost.linresp.two_mode.a{α:.2f}.p{name}`.
  - Value is C_X per pulse.
  - notes say which cost proxy (l4b grid or analytic illustrative).
- `t2_4c.flip_prob.td.two_mode.a1.00.p{name}`.
  - Value is the extra per-direction flip probability per pulse.
  - cross_check: the quasi-static estimate, tol 0.5 (a factor-of-2 level, because transients are expected).
- **Pulse name tokens** (use exactly these): `square`, `ramp_cos_tau0.2`, `ramp_lin_tau0.2`, `clear_k2_t0.16`, `svd`, `gen`, and optionally `grad`. Adjust the numeric suffix to the winning family member, and list the final tokens in the status file.

**Arrays** (consumed by lane l6, Readout designer page):
- `results/arrays/t2_4c.frontier.npz`: for all candidates, name, T, snr, costs, gains.
- `results/arrays/t2_4c.pulses.npz`: edges and values per finalist.

**Figures:** the three PNGs listed in §6 step 9.

**Quick vs production:**
- `--quick`: α = 2.1 only, T = 1 µs, linear response only, plus one tiny two-mode check at 12×4. It writes to `results/quick/` and `figures/quick/` in ≤ 2 min.
- Production linear response runs in seconds. Two-mode validation of 5 finalists runs in minutes.

**Jobs to queue** (put them in the status file with commands):

| Job | Wall estimate | RAM |
|---|---|---|
| Flip-check trains (2 runs plus 1 tolerance repeat, about 40 µs simulated each) | 10 to 30 min each | < 1 GB |
| Gradient refinement | 2 h cap | |
| κ_b eigen sweep (needs l1) | | |

## 8. Acceptance gates (ALL must pass before DONE)
- [ ] All fast tests pass. `-m slow` tests pass, or are documented as findings.
- [ ] The SVD and generalized pulses beat square at matched cost (i) and (ii) respectively in linear response (mathematical sanity).
- [ ] Two-mode validation: linear-response vs two-mode SNR within 10% for every finalist with amplitude ≲ g₂, with a convergence block (rel_tol 1e-2).
- [ ] A matched-cost (iii) comparison exists. The grid source (l4b grid, or analytic illustrative) is stated in the record notes.
- [ ] The flip check at α = 1.0 ran for square and the winner, or was queued, with commands in the status file.
- [ ] A verdict sentence in the status file: "Candidate X beats square by Y× in SNR at equal C_X on the two-mode model", **or** "No candidate beats square at matched cost; frontier shown." No unverified win claims.
- [ ] Every production record has `provenance.dirty == false`; the three figures and the notebook exist; `--quick` takes ≤ 2 min.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git switch -c std/l4c-capstone
& $env:DUQ_PY -m pytest tests/test_l4c_capstone.py -q -m "not slow"
& $env:DUQ_PY -m pytest tests/test_l4c_capstone.py -q -m slow
& $env:DUQ_PY -m tasks.task_2_4c_pulses --quick
& $env:DUQ_PY -m tasks.task_2_4c_pulses                      # production frontier (seconds to minutes)
& $env:DUQ_PY -m tasks.task_2_4c_verify --stage validate     # two-mode validation of finalists
& $env:DUQ_PY -m tasks.task_2_4c_verify --stage flipcheck    # long; prefer the queue (see status file)
& $env:DUQ_PY -m tasks.task_2_4c_verify --stage gradient     # optional, 2 h cap
& $env:DUQ_PY -m tasks.task_2_4c_verify --stage kappa_b      # optional, needs l1-spectral
git add src/pulses.py tasks/task_2_4c_pulses.py tasks/task_2_4c_verify.py tests/test_l4c_capstone.py docs/plan/status/l4c-capstone.md
git commit -m "[l4c-capstone] pulses, frontier, validation"
```
Run production only after committing the code (provenance.dirty must be false). Then commit the outputs by explicit path.

## 10. Out of scope / do not
- Do not edit `src/linresp.py`, `src/model.py` or any other lane's files. Request a change via `DECISION NEEDED`.
- Do not claim a win from linear response alone, or from a single truncation.
- Do not use `eps_x` for readout. The readout drive is `eps_z·(a + a†)` (RESEARCH §4.1).
- Do not describe the cost as a "tilted double well". Γ_X is even in ε_Z and the one-way rates are equal; the cost is out-of-code population (RESEARCH §4.3).
- Do not run GRAPE on large truncations or at large α. Do not exceed the 2 h gradient cap.
- No physics in the notebook beyond loading records (RERUN path excepted).

## 11. If blocked
- **`src/linresp.py` not merged or broken:** write `DECISION NEEDED: linresp unavailable — implement a private _linresp in tasks/task_2_4c_pulses.py mirroring CONTRACT §9 until l4a lands? (recommend yes; delete after merge)`. Continue with `src/pulses.py` and its tests meanwhile.
- **l4b grid missing:** use the analytic cost proxy, labelled illustrative (see §6 step 3), and queue a re-run.
- **Two-mode disagrees with linear response by more than 10%:** report it with plots. Check (a) the baseline subtraction of the κ_a offset, (b) whether the well preparation finished, (c) the amplitude regime. Do **not** tune tolerances. `DECISION NEEDED` if unresolved after 30 min.
- **Flip check below the noise floor:** report the floor, keep the quasi-static estimate, and label it.
- **Cut lines:** gradient refinement (cut line 2) and the κ_b option (cut line 6) are first to go. **Never cut** the SVD-vs-square comparison on the two-mode model.

## 12. Hand-off
At DONE the status file contains:
- State DONE, commits, commands with output excerpts.
- The finalist table (SNR, costs, gains; linresp vs two-mode).
- Record IDs, figures and arrays.
- Jobs to queue with RAM and wall estimates.
- Deviations, any DECISION NEEDED, and the verdict sentence.

**Explain-back questions for Harshit** (questions only; Harshit answers in `docs/defense.md`):
1. Why is the top singular vector of the response matrix the best pulse at fixed drive energy, and what does "matched cost" mean in your comparison?
2. Why does the optimal pulse put its energy near 3.14 MHz, and why does a square pulse waste drive?
3. How do you know the winning pulse doesn't hurt bit flips more than the proxy says? What did the direct flip check at α = 1.0 show?
