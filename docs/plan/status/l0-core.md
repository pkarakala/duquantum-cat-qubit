# Status: lane `l0-core`

> This file is the only channel to Harshit, the integrator and Claude's later review. Keep it factual: commands and real output, not intentions.

| Field | Value |
|---|---|
| State | `DONE` (ready to merge = **G0**) |
| Branch | `std/l0-core` |
| Agent / model | Cursor agent, Claude Opus |
| Started (EDT) | Sat Oct 24 2026, 18:30 |
| Last update (EDT) | 18:42 |
| Last code commit | `6ecd922` `[l0-core] implement CONTRACT §3-§7: ...` (this status file is committed right after it; see `git log -1 std/l0-core`) |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK (18:30)
- [x] Tests written first (18:38, commit `8dee725`): all 20 brief tests in `tests/test_l0_core.py` plus `test_contract_signatures` (pins every CONTRACT §3–§7 parameter list). Before implementation: `17 failed, 4 passed`; every failure was ImportError / TypeError / AttributeError / ModuleNotFoundError (missing API). The 4 passes (two backward-compat tests, dark states, slow `task_1_0.part_b`) exercise only old code, as expected.
- [x] Implementation complete (18:40, commit `6ecd922`)
- [x] `--quick` run: n/a (code-only lane; brief §7 forbids running `tasks.task_1_2`)
- [x] Production runs: n/a (no outputs)
- [x] All acceptance gates in brief §8 checked, with evidence below
- [x] Explain-back questions copied (brief §12)

## Test summary
- `tests/test_l0_core.py -m "not slow"`: **20 passed in 12.1 s** (slowest: symmetry 2.5 s, drive_ops 2.0 s, quadratures 1.8 s).
- `tests/test_l0_core.py -m slow`: **1 passed in 2.7 s** (`test_intro_task_1_0_unchanged`: `final_n_sim` reproduces 0.4998322686860546 to < 1e-9).
- Full repo `-m "not slow"`: **20 passed, 1 deselected in 14.2 s** (17.8 s wall incl. interpreter start).

## Public API added (CONTRACT §3–§7)
- `src/model.py`: `loss_jumps(a, kappa_a, n_th=0.0)`, `drive_ops(a)`, `one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0)`, `two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None)`, `vacuum2(Na, Nb)` (unchanged), `coherent2(Na, Nb, alpha)`, `cat2(Na, Nb, alpha, sign=+1)`.
- `src/config.py`: `METHOD_LONG` (Tsit5 rtol 1e-8, atol 1e-10, max_steps 10_000_000), `NA_EIG_MAX = NB_EIG_MAX = None`, `trunc_for(alpha, purpose="steady")`. All existing constants and the `__main__` block unchanged.
- `src/analysis.py`: `fit_exp_offset(t, y, p0=None)`, `code_basis(N, alpha)`, `z_logical(N, alpha)`, `code_projector(N, alpha)`, `leakage(rho_a, alpha)`, `p_right_well(rho_a, alpha)`. Existing functions unchanged.
- `src/results.py`: `ID_RE`, `SCHEMA`, `std_params(...)`, `record(id, *, ...)`, `save_arrays(id, quick=False, **arrays)`, `load_record(id)`; `save(name, data)` and `RES_DIR` unchanged.
- `src/provenance.py` (new): `git_info()`, `provenance(script, wall_s=None)`.
- `src/convergence.py` (new): `sweep(fn, axis, values, fixed)`, `converged_at(rows, key, var, tol)` (moved verbatim), `convergence_block(sweeps, key, rel_tol, chosen)`.
- `src/plotting.py`: `save(fig, name, dpi=200, quick=False)`.
- `pytest.ini` (marker `slow`, `testpaths = tests`, `-ra`), `tests/conftest.py`.

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| `pytest tests/test_l0_core.py -m "not slow"` green, < 60 s | PASS | `20 passed, 1 deselected in 12.14s` |
| `-m slow` green | PASS | `1 passed, 20 deselected in 2.72s` |
| Full `-m "not slow"` suite green | PASS | `pytest -m "not slow" -q` → `20 passed, 1 deselected in 14.24s` |
| Backward compat: tests 1, 2, 18 exact | PASS | `np.array_equal` on H and every jump (tests 1, 2); `converged_at` gives 24 / 10 / 16 / 4 = stored `summary` and `tasks.task_1_2.converged_at is src.convergence.converged_at` (test 18) |
| Intro imports succeed | PASS | `python -c "import tasks.task_1_0, tasks.task_1_1, tasks.task_1_2, tasks.task_1_3a; print('ok')"` → `ok` |
| `task_1_2.py` diff = removed def + one import | PASS | `git diff standard-track -- tasks/task_1_2.py` → `+from src.convergence import converged_at` and the removed 7-line `def converged_at` plus its 2 trailing blank lines, nothing else |
| `git status --porcelain -- results figures` empty after all test runs | PASS | empty output |
| Diff lists only allowlisted files | PASS | `git diff --name-only standard-track...HEAD` → `docs/plan/status/l0-core.md pytest.ini src/analysis.py src/config.py src/convergence.py src/model.py src/plotting.py src/provenance.py src/results.py tasks/task_1_2.py tests/conftest.py tests/test_l0_core.py` (see note 1) |
| Every CONTRACT §3–§7 name importable with exact signature | PASS | `test_contract_signatures` compares `inspect.signature` (annotations stripped) of all 29 public names to the CONTRACT text |
| No hostname/username lookups in `src/` | PASS | `rg -n "gethostname\|platform.node\|getuser" src/` → no matches |
| `python -m src.config` | PASS | `kappa_2/2pi = 0.896 MHz (expect 0.896)` |

Extra evidence:
- RESEARCH §4.1 symmetry (Na=12, Nb=4, eps_z = 0.2 g2, 0.5 µs from vacuum, `C.METHOD`): `max|Re<a>| = 0.0` exactly, `max|Im<a>| = 0.235`. With eps_x = 0.2 g2 instead: `Re<a>(0.5 µs) = 0.364`.
- Provenance on the clean tree: `{"script": "tasks/x.py", "git_commit": "6ecd922", "git_branch": "std/l0-core", "dirty": false, "dynamiqs": "0.3.7", "jax": "0.12.0.1", "numpy": "2.5.4", "scipy": "1.18.1", "python": "3.12.13", "platform": "macOS-14.5-arm64-arm-64bit", "cpu_count": 8, ...}`
- `jax.grad` through `two_mode(..., eps_z=e)` works (14.4 = 2e·Tr X², analytic 14.4).

Note 1: two-dot `git diff --name-only standard-track` also lists `requirements.txt` and `docs/plan/status/setup.md`. Those come from the `setup` lane's commits on `standard-track` after this branch was cut; this branch does not touch them. The three-dot form (the lane-discipline check) is the right one.

## Decisions taken (within the brief; no CONTRACT change)
- Absent optional record fields are serialized as `null`; keys are written in the §6.2 order.
- `fit_exp_offset`: `p0` order is `(gamma, A, C)`, forced by the brief's `gamma_stderr = sqrt(pcov[0,0])`. `rel_rms_residual = rms(y - fit) / rms(y)`. The fit runs internally in `t - t[0]` and reports A at t = 0, so a window starting late stays well conditioned (tested: a window from t = 2.5 recovers A and gamma to 1e-6).
- Provenance API names: `git_info()` and `provenance(script, wall_s=None)`. Git failure gives `"unknown"` and `dirty = True`.
- Dark-state test at N = 40 (per the brief).
- `std_params` rounds the lab-unit constants to 9 decimals and casts `alpha`, `n_th`, `eps_*_over_g2` to `float`.
- No dynamiqs fallback was needed: `jnp_array[..., None, None] * QArray` and broadcasting `QArray + batched QArray` work natively and keep `dims`.
- `tests/conftest.py` also pins `matplotlib.use("Agg")`: the macOS GUI backend aborted the interpreter (`Fatal Python error: Aborted` in `plt.subplots`) inside pytest. This protects every lane's tests.
- Test 3 on the two-mode space: the truncation edge of `[X, P]` is the top memory level, i.e. the first `(Na-1)*Nb` composite indices, not `D-1`.
- `_is_zero` treats a JAX tracer as non-zero, so gradients through a drive amplitude work. A concrete scalar 0 still adds no term (bit-identical default H).
- A batched `extra_H` counts toward the "at most one batched argument" guard (two batched arguments would broadcast element-wise, not as a grid). `loss_jumps` raises on `n_th < 0`.
- `record` validation beyond the brief's list (all `ValueError`): ids checked with `fullmatch` (a trailing newline is rejected); complex and string values are rejected; `truncation`, `numerics` and `artifacts` must be dicts; `notes` must be a string; cross-check `rel_diff` and `tol` must be finite reals; any non-strict-JSON content raises.
- `leakage` and `p_right_well` raise `ValueError` on batched input (the brief specifies unbatched only).

## Records produced
None. Outputs: none (code only).

## Jobs to queue
None.

## Deviations from the brief (and why)
- An extra 21st test, `test_contract_signatures`, gives machine-checkable evidence for the §8 signature gate.
- The agent's sandbox could not write `~/.matplotlib`, so matplotlib used a temporary cache directory. This is harmless and does not affect the repo.

## DECISION NEEDED
None.

## Open items
None.

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Why can a drive ε(a + a†) never prepare the +α well starting from vacuum, which exact symmetry does your 1e-12 test check, and why does ε·i(a† − a) escape it?
2. Your records say `"converged": true`. What exactly does that guarantee, and how could a number still be wrong (think of the 20×6 truncation trap) even when two truncations agree?
3. Why fit memory parity with A e^{−γt} + C instead of a pure exponential: what is the steady-state parity at α = 2.1, and which way would a pure-exponential fit bias γ?

## Notes for Claude's later review
- The symmetry residual is exactly 0.0, not just < 1e-12: H is real, every term flips the total parity n_a + n_b, and the jumps are real, so the "imaginary pattern" entries of ρ never get a real part, even in floating point.
- No tolerance was loosened. Every brief tolerance passed on the first run once the implementation was in place.
