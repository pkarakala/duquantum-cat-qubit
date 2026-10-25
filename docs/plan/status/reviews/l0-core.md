# Review `l0-core` round 1: PASS

| Lane | Reviewed commit | Base | Reviewer model | Start–end (EDT) | Prior rounds |
|---|---|---|---|---|---|
| l0-core | `effc210` (`effc210127dfee154f7e8574ceb70a71644998aa`) | `standard-track` `0a2040b` | Grok 4.7 (Cursor) | 18:50–19:06 | none (prior process died at launch; no review file) |

File:line citations are the tree at `effc210`. This branch is cut from current `standard-track` and does not contain the lane's code.

## Verdict
PASS. Blocking findings: none. Ready for the integrator to merge `std/l0-core` (`effc210`) with this review branch. Rule: FAIL if any critical/major; PASS_WITH_NOTES if only minor; PASS if none.

## Stage 1 findings

| Item | Result | Evidence |
|---|---|---|
| S1-1 Allowlist | OK | `git diff --name-only standard-track...effc210` is exactly the 12 allowlisted paths: `docs/plan/status/l0-core.md`, `pytest.ini`, `src/{analysis,config,convergence,model,plotting,provenance,results}.py`, `tasks/task_1_2.py`, `tests/{conftest,test_l0_core}.py`. No deletions outside that set. `git log --merges standard-track..effc210` is empty. `tasks/task_1_2.py` changes by one added import (`from src.convergence import converged_at`, line 21 at `effc210`) and deletion of `converged_at`, whose body matches `src/convergence.py:13-19`. Three-dot is the right check: `standard-track` has since gained setup `ed67136` and the integrator ledger `0a2040b`, which a two-dot diff would show in the other direction. |
| S1-2 Completeness | OK | Every CONTRACT §3–§7 name in brief §4 is present with the CONTRACT parameter list (`test_contract_signatures` passed; `cat2` default `sign=+1` prints as `sign=1`, and `std_params(alpha=C.ALPHA)` prints as `alpha=2.1`). All 20 brief §5 tests exist and assert the stated tolerances. No §7 records, figures, or arrays (none required). Jobs to queue: none. |
| S1-3 Nothing extra | OK | No new dependency, record ID, flag, or CONTRACT signature. Disclosed additions that do not change frozen names: `test_contract_signatures`; `matplotlib.use("Agg")` in `tests/conftest.py:9`; stricter `record` checks (fullmatch, complex/string rejection, dict-typed optional blocks, finite `rel_diff`/`tol`). See Notes. |
| S1-4 Status file | OK | `docs/plan/status/l0-core.md` at `effc210`: `State: DONE`, ready to merge = G0, commands with trimmed output, records "none", jobs "none", deviations stated, `DECISION NEEDED` none. Three explain-back questions, no answers written. TDD order: `8dee725` tests only, then `6ecd922` implementation, then `effc210` status. |

## Stage 2 findings

| Item | Result | Evidence |
|---|---|---|
| S2-1 2π only in config | OK | `git grep` for `TWO_PI` / `2 * π` outside `src/config.py`: the only lane hits are `C.G2 / C.TWO_PI` (and κ_b, κ_a) in `std_params` (`src/results.py:32-36`), the inverse conversion back to the lab MHz/kHz inputs. `src/config.py:13` is the single `2 * math.pi`. Pre-existing `tasks/task_1_0.py:25` is not in the diff. |
| S2-2 √rate jumps | OK | `loss_jumps` (`src/model.py:33-42`): `√(κ_a(1+n_th)) a`, plus `√(κ_a n_th) a†` if `n_th > 0`, `[]` if `κ_a == 0`. L2 line (`src/model.py:69-70`) matches the intro body. `two_mode` jumps (`src/model.py:95`): `√κ_b b` then `loss_jumps`. Scalar one-mode H and both jumps are `np.array_equal` to the old expressions. Thermal matrix elements: `⟨0\|L\|1⟩ = √(κ_a·1.05)` and `⟨1\|L†\|0⟩ = √(κ_a·0.05)`, rel_diff 0. |
| S2-3 α² sign | OK | `EPS_D = ALPHA**2 * G2` (`src/config.py:19`). `EPS_D/G2 = 4.41 = ALPHA**2`, `EPS_D > 0`. Cat states use `±α` on the real axis (`cat2`, `src/model.py:108-113`). |
| S2-4 Drive quadrature | OK | `drive_ops` (`src/model.py:45-52`): `X = a+a†`, `P = i(a†−a)`. Docstrings say `eps_z` is readout / Z_L and cannot select a well. `array_equal`: one-mode and two-mode `eps_z` adds `X` and not `P`; `eps_x` adds `P` and not `X`. No "tilt" wording in the lane diff. Hand-built one-mode mesolve: `eps_z=1` gives `Im⟨a⟩(0.05 µs) = −0.05` (rel 4e-16) and `max\|Re⟨a⟩\| = 0`; `eps_x=1` gives `Re⟨a⟩(0.05) = +0.05` and `max\|Im⟨a⟩\| = 0`. |
| S2-5 Symmetry tests | OK | `test_drive_quadratures` and `test_symmetry_eps_z_from_vacuum` keep the 1e-12 bound (`tests/test_l0_core.py:96,115`); `test_eps_x_breaks_symmetry` requires `Re⟨a⟩(0.5 µs) > 0.05` (line 126). Independent hand-built two-mode H (`eps_z = 0.2 g₂`, Na=12, Nb=4, 0.5 µs from vacuum): H and both jumps `array_equal` to `two_mode`; `max\|Re⟨a⟩\| = 0.0`, `max\|Im⟨a⟩\| = 0.235` on both the hand-built H and `two_mode`. |
| S2-6 Convergence blocks | N/A | No records (code-only lane). `convergence_block` (`src/convergence.py:22-42`) sorts each axis, sets `needed` with the moved `converged_at`, and sets `converged` only when every axis has ≥2 rows, `chosen ≥ needed`, and the two largest values agree within `rel_tol`. Tests 17–18 pass, including the task 1.2 anchors 24 / 10 / 16 / 4. |
| S2-7 Eigen acceptance | N/A | This lane does not build a Liouvillian eigensolver or eigen records. `src/spectral.py` belongs to l1. |
| S2-8 Fits | OK | No production parity fit. `fit_exp_offset` (`src/analysis.py:63-91`) is `A exp(−γ t)+C` via `curve_fit(..., maxfev=20000)`. Parameter order is `(gamma, A, C)`, so `gamma_stderr = sqrt(pcov[0,0])`. The fit runs on `t−t[0]`; reported `A` is `A(t0)·exp(γ t0)`, i.e. the amplitude at t = 0. Noise-free `0.7 e^{−0.5 t}+0.27` on `[0,10]` and on a window with `t0 = 2.513` both return γ=0.5, A=0.7, C=0.27, matching an independent unshifted `curve_fit` (rel 0 for A and C; rel ~2e-16 for γ). Explicit `p0=(0.5, 0.7, 0.27)` on the late window does the same. |
| S2-9 Rate conventions | N/A | No Γ_X or Γ_Z is computed. The fit docstring (`src/analysis.py:66-67`) states the steady parity is `1/cosh(2α²) ≠ 0`. The lane diff has no Γ_Z+Γ_X wording. |
| S2-10 Units | N/A | No committed records. `std_params()` returns `g2_MHz=0.763`, `kappa_b_MHz=2.6`, `kappa_a_kHz=9.3` (test 15 passed). |
| S2-11 Provenance | OK | `git diff --name-only standard-track...effc210 -- results/records` is empty. Validator: 0 files, exit 0. `provenance` (`src/provenance.py:25-57`) uses `rev-parse --short HEAD`, `rev-parse --abbrev-ref HEAD`, and `status --porcelain -- src tasks tools` (dirty iff that output is non-empty; git failure → `"unknown"` and `dirty=True`). Platform is `platform.platform()` plus `os.cpu_count()`. No `platform.node`, `gethostname`, or `getpass`. On this detached checkout: `dirty=False`, `git_commit=effc210`, `git_branch=HEAD` (abbrev-ref of a detached HEAD; on `std/l0-core` the same call returns the branch name), `platform=macOS-14.5-arm64-arm-64bit`, node name and username absent from the JSON. |
| S2-12 Tests assert physics | OK | Tests 1–2 and 18 use exact equality. Quadrature and symmetry tests use 1e-12 and rel 1e-6 as specified, not a loosened bound. Fit, leakage, `p_right`, thermal jumps, and `trunc_for` assert numbers. Fast file: 20 passed in 16.30 s (gate < 60 s). This branch's whole `-m "not slow"` suite is that same file: 20 passed in 16.53 s. |
| S2-13 `--quick` | N/A | Brief §7 forbids `python -m tasks.task_1_2` even with `--quick`. That script still writes `results/task_1_2_quick.json` and `figures/task_1_2_convergence_quick.png` (`tasks/task_1_2.py:69,84`), and the lane was only allowed to change the import. `record(..., quick=True)` and `plotting.save(..., quick=True)` write under `quick/` and are covered by tests 15 and 19 (tmp_path). Not run, so the tree stayed clean. |
| S2-14 No swallowed failures | OK | No bare `except: pass`. `src/provenance.py:40` catches `Exception` only to return `"unknown"` for a missing package version, which the brief requires. `src/results.py:133-135` re-raises `ValueError`. `src/model.py:16` catches `TypeError` so a JAX tracer is not treated as a concrete 0 (default scalar 0 still adds no drive term). |
| S2-15 Figures | N/A | No new figures. `git status --porcelain -- results figures` was empty after the fast suite, the slow test, and the spot-checks. |

### Findings
None.

## Commands run + results

Worktree `.worktrees/review-l0-core`, detached at `effc210` for every check below. Interpreter `$MAIN/.venv/bin/python`, `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2`. `GEMINI_API_KEY` unset; Gemini not run. No `runq` jobs and no heavy lock.

```
git diff --name-only standard-track...HEAD
# 12 allowlisted paths only (listed in S1-1)
git log --oneline standard-track..HEAD
# effc210 status DONE
# 6ecd922 implement CONTRACT §3-§7
# 8dee725 tests first
git log --merges --oneline standard-track..HEAD
# (empty)

pytest tests/test_l0_core.py -m "not slow" -q --durations=10
# 20 passed, 1 deselected in 16.30s
# slowest: backward_compat_two_mode 3.01s, symmetry_eps_z 2.80s,
#          drive_ops_hermitian 2.46s, drive_quadratures 2.01s
# /usr/bin/time real 23.65s (includes interpreter start). Exit 0.

pytest tests/test_l0_core.py -m slow -q
# 1 passed, 20 deselected in 3.62s. Exit 0.
# test_intro_task_1_0_unchanged: |final_n_sim − 0.4998322686860546| < 1e-9

pytest -m "not slow" -q
# 20 passed, 1 deselected in 16.53s. Exit 0.

python -c "import tasks.task_1_0, tasks.task_1_1, tasks.task_1_2, tasks.task_1_3a"
# imports ok
python -m src.config
# kappa_2/2pi = 0.896 MHz (expect 0.896)

python -c "import tests.conftest, matplotlib; print(matplotlib.get_backend())"
# Agg

git status --porcelain -- results figures
# (empty)
```

Records validator over `git diff --name-only standard-track...HEAD -- results/records`: `record_files []`, `validator_bad 0`, exit 0.

`tasks.task_1_2 --quick` was not run (S2-13).

## Independent spot-checks

| Quantity | Lane value (record id) | Independent value | Method | rel_diff | tol | OK |
|---|---|---|---|---|---|---|
| κ₂ | `C.KAPPA_2 = 5.627501087839` rad/µs (no record) | `4·(2π·0.763)²/(2π·2.6) = 5.627501087839`; `/2π = 0.895644615385` MHz | formula from the lab frequencies, not from `C.KAPPA_2` | 0 | exact | OK |
| `p_right_well(\|α=1⟩⟨α\|, N=30)` | `0.995399929630` (no record) | `(1+√(1−e^{−4}))/2 = 0.995399929630` | analytic infinite-dimensional coherent state; also a numpy cat construction that does not call `p_right_well` | 0 | 1e-6 | OK |
| `max\|Re⟨a⟩\|` under `eps_z=0.2 g₂`, vacuum, 0.5 µs, 12×4 | `0.0` from `two_mode` | `0.0` from an inline H; `max\|Im⟨a⟩\| = 0.235096` on both | `mesolve` of a hand-built H; that H and both jumps are `array_equal` to `two_mode` | 0 | 1e-12 | OK |

The RESEARCH display values 5.6276 rad/µs and 0.8957 MHz are roundings of 5.627501 and 0.895645 (rel 1.8e-5 and 6.2e-5). The constant matches the defining formula, and `python -m src.config` prints 0.896 MHz at three decimals as its own check says. Do not edit `KAPPA_2` to force the rounded table entry.

Normalization of `Z_L`, which the α=2.1 test cannot see: at α=1, `max\|Z_L − (\|α⟩⟨α\|−\|−α⟩⟨−α\|)\| = 6.83e-3`, while `max\|Z_L·√(1−e^{−4}) − that difference\| = 1.1e-16`. At α=2.1 the unnormalized residual is only 4.0e-9, under the brief's 1e-6, and the normalized residual is 6e-17. The operator is the exact cat formula (`src/analysis.py:100-103`).

## Notes for Claude's later review
- No open `DECISION NEEDED`. No tolerance was loosened. Symmetry residual is exactly 0, not merely under 1e-12, on both the lane Hamiltonian and a hand-built one.
- Fast tests here were 16.30 s (pytest) / 23.65 s (process wall) against the lane's 12.1 s. Same 20 passed. The gate is < 60 s. The extra seconds are interpreter and JAX startup (`test_backward_compat_two_mode` at 3.01 s).
- Accepted, disclosed extras, not findings: Agg backend before `import src.config` (`tests/conftest.py:9-13`), confirmed `Agg` under import; `test_contract_signatures`; `record` rejects a trailing newline, complex and string values, non-string `notes`, and an `agree` that is not `rel_diff <= tol`; `loss_jumps` raises on `n_th < 0`; a batched `extra_H` counts toward the one-batch guard. Defaults still omit a zero drive, and nominal intro H/jumps stay bit-identical.
- Brief vs CONTRACT, not charged to the lane: CONTRACT §6.2 says a null `convergence` must be justified in `notes`. Brief §4's `ValueError` list does not require that, and `record` allows both to be null (`src/results.py:116-129`). No production records exist. `tools/check_claims` (l0-tools) is the enforcement point.
- `task_1_2 --quick` still writes outside `results/quick` and `figures/quick`. That is pre-G0 intro behavior; this lane was forbidden to change it. Later lanes must use `record(..., quick=True)` and `plotting.save(..., quick=True)`.
- Provenance `git_branch` is `HEAD` while detached. That is `rev-parse --abbrev-ref HEAD`, as specified, not a hardcoded branch.
- Items not re-run: production task scripts, `runq`, Gemini. Abbreviated review was not used.
- 3 hardest judge questions (questions only; Harshit answers in `docs/defense.md`):
  1. Why can a drive ε(a+a†) never prepare the +α well from vacuum, which symmetry does the 1e-12 test check, and why does ε·i(a†−a) escape it?
  2. A record says `"converged": true`. What does `convergence_block` actually guarantee, and how can two truncations still agree on a wrong number (the 20×6 trap at α=2.1)?
  3. Why fit memory parity as A e^{−γt}+C rather than a pure exponential: what is the steady parity at α=2.1, and which way would a pure-exponential fit bias γ?
