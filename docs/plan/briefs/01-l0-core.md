# Brief `l0-core`: Core platform: model extensions, results v2, provenance, convergence, analysis helpers

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l0-core`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/01-l0-core.md`, then execute this brief exactly. Keep `docs/plan/status/l0-core.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l0-core` | `std/l0-core` (from `standard-track`) | `setup` (venv `D:\duq-venv` exists, pins recorded) | strongest reasoning model available | 60 min | Phase 0, merged by **6:45 PM Sat** (this merge *is* gate G0) |

## 1. Goal and why
Extend the shared platform once, backward compatibly, so every physics lane codes against frozen names (CONTRACT §3–§7, §15). Every other code lane branches **after** this merges (only `l0-tools` and `l6-lab` start earlier, from CONTRACT text). After G0, `src/model.py`, `src/config.py` and `src/analysis.py` are frozen. Mistakes here propagate into every number, so correctness and exact backward compatibility beat features. No physics results are produced by this lane.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (allowlist), §2 (env), §3, §4, §5, §6, §7, §15. Never contradict it; if it is wrong, write DECISION NEEDED.
- `docs/plan/RESEARCH.md` §1 (parameters), §2 (dynamiqs 0.3.7 API: no `options=`; `save_extra(t, rho)`; Tsit5 signature), §4.1 (drive quadratures, antiunitary symmetry).
- Current code: `src/model.py`, `src/config.py`, `src/analysis.py`, `src/results.py`, `src/plotting.py`, `tasks/task_1_2.py` (`converged_at`), `tasks/task_1_0.py` (`part_b`), `results/task_1_0.json`, `results/task_1_2.json`.
- Style: short docstrings, `import src.config as C` (or `from src import config as C`) first, numpy/jax/dynamiqs only.

## 3. Allowlist (touch nothing else)
`src/model.py`, `src/config.py`, `src/analysis.py`, `src/results.py`, `src/provenance.py` (new), `src/convergence.py` (new), `src/plotting.py`, `tasks/task_1_2.py` (**import change only**), `tests/conftest.py`, `tests/test_l0_core.py`, `pytest.ini`, `docs/plan/status/l0-core.md`.
Not yours: `.gitignore`, `requirements.txt`, `results/**`, `figures/**`, notebooks, `tools/**`, other tasks.

## 4. Interfaces you implement / rely on
**`src/model.py`** (CONTRACT §3). Keep the old bodies' arithmetic so defaults reproduce the old H and jumps exactly.
```python
def loss_jumps(a, kappa_a, n_th=0.0) -> list:   # [sqrt(ka*(1+nth)) a] + ([sqrt(ka*nth) a†] if nth > 0); [] if ka == 0
def drive_ops(a) -> tuple:                      # (X, P) = (a + a.dag(), 1j*(a.dag() - a)), both Hermitian
def one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0):   # -> (H, jumps, a)
def two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None):  # -> (H, jumps, (a, b))
def vacuum2(Na, Nb); def coherent2(Na, Nb, alpha); def cat2(Na, Nb, alpha, sign=+1)   # buffer always in |0>
```
- `one_mode`: H = eps_z X + eps_x P, `dq.zeros(N)` when both are 0; jumps = `[sqrt(kappa_2)(a^2 - alpha^2)] + loss_jumps(a, kappa_a, n_th)`. Keep the existing L2 line verbatim (`jnp.sqrt(jnp.asarray(kappa_2))[..., None, None] * (a @ a - alpha**2 * dq.eye(N))`).
- `two_mode`: H = `g2 a a b† + g2 a† a† b - eps_d (b + b†)` (old expression, same operand order) `+ eps_z X + eps_x P + extra_H`; jumps = `[jnp.sqrt(kappa_b) * b] + loss_jumps(a, kappa_a, n_th)`, i.e. order `[√κ_b b, √(κ_a(1+n_th)) a, √(κ_a n_th) a†]`.
- Drive terms: add a term **only if it is non-zero or batched** (helper `_is_zero(x) = np.ndim(x) == 0 and float(x) == 0.0`), so the default H is bit-identical to the old one. Scalar: `x * op`. Array: `jnp.asarray(x)[..., None, None] * op`.
- At most ONE batched argument per call (`one_mode`: among `kappa_2, eps_z, eps_x`; `two_mode`: among `eps_z, eps_x`); otherwise `raise ValueError("at most one batched argument per call")`. `kappa_a`, `n_th` are scalars.
- `extra_H`: QArray on the composite space; `raise ValueError` if `extra_H.shape[-1] != Na*Nb`.
- `cat2`: `dq.tensor(dq.unit(dq.coherent(Na, alpha) + sign*dq.coherent(Na, -alpha)), dq.fock(Nb, 0))`; `sign not in (+1, -1)` -> ValueError. `model.py` must not import `analysis.py`.
- Physics of the drives (RESEARCH §4.1): `eps_z X` gives d<a>/dt = -i eps_z (imaginary axis, Z_L rotation, readout; can NOT pick a well from vacuum); `eps_x P` gives d<a>/dt = +eps_x (real axis; breaks a -> -a).

**`src/config.py`** (CONTRACT §4). Keep every existing constant and the `__main__` block unchanged (`TWO_PI, G2, KAPPA_B, KAPPA_A, ALPHA, EPS_D, KAPPA_2, N_SINGLE, NA_START, NB_START, NA, NB, METHOD`). Add:
```python
METHOD_LONG = dq.method.Tsit5(rtol=1e-8, atol=1e-10, max_steps=10_000_000)
NA_EIG_MAX, NB_EIG_MAX = None, None          # L1 fills these later (mini-lane)
def trunc_for(alpha, purpose="steady") -> tuple[int, int]:
    # 'steady' and 'eig': Na = max(16, even_ceil(alpha**2 + 6*alpha + 10)), Nb = 8
    # 'inflation'       : Na = max(24, even_ceil(1.6*alpha**2 + 6*alpha + 10)), Nb = 12
    # even_ceil(x) = ceil(x) rounded up to the next even integer; other purpose -> ValueError
```
Docstring must say "STARTING POINT ONLY; every number still needs its own convergence block."

**`src/analysis.py`** (CONTRACT §5). Existing `memory_state, top_projector, cat_plus, memory_extras, fit_exp_decay, settle_time` unchanged. Add:
```python
def fit_exp_offset(t, y, p0=None) -> dict   # y = A exp(-gamma t) + C via scipy.optimize.curve_fit(maxfev=20000)
    # default p0: C0 = y[-1], A0 = y[0] - y[-1], gamma0 = 3 / (t[-1] - t[0])
    # returns {'gamma','A','C','gamma_stderr' = sqrt(pcov[0,0]), 'rel_rms_residual' = rms(y - fit) / rms(y)} (floats)
def code_basis(N, alpha) -> tuple    # (|C+>, |C->), |C±> = unit(|alpha> ± |-alpha>); |C+> == cat_plus(N, alpha)
def z_logical(N, alpha)              # |C+><C-| + |C-><C+|  (= (|a><a| - |-a><-a|)/sqrt(1 - e^{-4 alpha^2}))
def code_projector(N, alpha)         # |C+><C+| + |C-><C-|
def leakage(rho_a, alpha) -> float   # 1 - Re Tr(code_projector rho_a); N = rho_a.shape[-1]; unbatched only
def p_right_well(rho_a, alpha) -> float   # (1 + Re Tr(z_logical rho_a)) / 2
```
Use `fit_exp_offset` for parity: steady parity is 1/cosh(2 alpha^2) != 0, so a pure exponential is biased.

**`src/results.py` + `src/provenance.py`** (CONTRACT §6). Keep `save(name, data)` and `RES_DIR` exactly. Add:
```python
ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$")
def std_params(alpha=C.ALPHA, n_th=0.0, eps_z=0.0, eps_x=0.0, **extra) -> dict
    # {'g2_MHz': round(C.G2/C.TWO_PI, 9) == 0.763, 'kappa_b_MHz': 2.6, 'kappa_a_kHz': round(C.KAPPA_A/C.TWO_PI*1e3, 9) == 9.3,
    #  'alpha', 'n_th', 'eps_z_over_g2': eps_z/C.G2, 'eps_x_over_g2': eps_x/C.G2, **extra}
def record(id, *, task, quantity, value, units, method, params, script, truncation=None, uncertainty=None,
           convergence=None, numerics=None, cross_check=None, artifacts=None, wall_s=None, notes=None, quick=False) -> Path
def save_arrays(id, quick=False, **arrays) -> Path   # np.savez_compressed to RES_DIR/arrays/<id>.npz or RES_DIR/quick/arrays/
def load_record(id) -> dict                          # reads RES_DIR/records/<id>.json
```
- `record` validation (all `ValueError`): `id` fails `ID_RE`; `task, quantity, units, method, script` not non-empty `str`; `params` not a dict; `value` not a real finite scalar (reject bool, NaN, inf, arrays); `uncertainty` given but non-finite; `script` absolute (absolute paths leak user names); each `cross_check` entry lacks `method`, `rel_diff`, `tol` or `agree`, or has `agree != (rel_diff <= tol)`; `convergence` given but lacks `key, rel_tol, sweeps, needed, converged`.
- Output: every §6.2 key in §6.2 order, absent optionals written as `null`; `schema = "duq.record/v2"`; `value = float(value)`; numpy/jax scalars and arrays converted (`.item()` / `.tolist()`); `json.dumps(..., indent=2, allow_nan=False)`; `script` stored with forward slashes; prints `saved <path>`.
- Paths are computed from the module global `RES_DIR` **at call time** (tests monkeypatch it): `RES_DIR/"records"` or `RES_DIR/"quick"/"records"`; `mkdir(parents=True, exist_ok=True)`.
- `src/provenance.py` (API not named by CONTRACT; use these names): `git_info() -> dict` and `provenance(script, wall_s=None) -> dict` returning exactly `script, git_commit, git_branch, dirty, dynamiqs, jax, numpy, scipy, python, platform, cpu_count, wall_s, timestamp`. Git via `subprocess.run(["git", ...], cwd=<repo root>, capture_output=True, text=True, timeout=10)`: `rev-parse --short HEAD`, `rev-parse --abbrev-ref HEAD`, `status --porcelain -- src tasks tools` (dirty = output non-empty). Git failure -> `"unknown"` and `dirty = True`. Versions via `importlib.metadata.version` (`"unknown"` on error), `platform.python_version()`, `platform.platform()`, `os.cpu_count()`, timestamp `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`. **Never** `platform.node()`, `socket.gethostname()`, `getpass.getuser()`, `os.environ["USERNAME"]`.

**`src/convergence.py`** (CONTRACT §7):
```python
def sweep(fn, axis, values, fixed) -> list[dict]   # [{axis: v, **fixed, **fn(**fixed, **{axis: v})} for v in values]
def converged_at(rows, key, var, tol)               # moved VERBATIM (body and docstring) from tasks/task_1_2.py
def convergence_block(sweeps: dict, key: str, rel_tol: float, chosen: dict) -> dict
```
`convergence_block`: `sweeps = {"Na": (fixed_dict, rows), "Nb": (fixed_dict, rows)}` (any axis names). For each axis sort rows by the axis value, then emit `{"key", "rel_tol", "sweeps": {axis: {"fixed", "values", "results": [float(r[key])]}}, "needed": {axis: converged_at(rows, key, axis, rel_tol)}, "converged": bool}`. `converged` is true iff for every axis: `len(rows) >= 2`, `chosen[axis] >= needed[axis]`, and the two largest values agree, `|r[-1] - r[-2]| <= rel_tol * |r[-1]|`. Missing `chosen[axis]` -> ValueError.
`tasks/task_1_2.py`: delete its `converged_at` def and add `from src.convergence import converged_at`. Nothing else changes.

**`src/plotting.py`**: `save(fig, name, dpi=200, quick=False)`; quick writes `FIG_DIR/"quick"/<name>.png` (`mkdir(parents=True, exist_ok=True)`, `FIG_DIR` read at call time).
**`pytest.ini`**: `[pytest]`, `testpaths = tests`, `addopts = -ra`, `markers = slow: long physics reproductions (run with -m slow)`.
**`tests/conftest.py`**: insert the repo root at `sys.path[0]`, then `import src.config  # noqa: F401` (double precision before any array).

## 5. Tests to write FIRST (TDD)
All in `tests/test_l0_core.py`. Commit them (failing) before implementing. Use `C.METHOD`, `exp_ops=[a]`, `save_states=False`; `Re/Im<a>` from `res.expects[0]`.
1. `test_backward_compat_two_mode`: Na=8, Nb=3, nominal `C` params. Build the OLD H and jumps inline in the test (copy of the old body). `two_mode` defaults: `np.array_equal` on `H.to_jax()`; `len(jumps) == 2`; jumps[0] equals `sqrt(kb) b`, jumps[1] equals `sqrt(ka) a` (`np.array_equal`).
2. `test_backward_compat_one_mode`: `one_mode(30, jnp.array([C.KAPPA_2/4, C.KAPPA_2, 4*C.KAPPA_2]), C.ALPHA, C.KAPPA_A)` equals the old construction exactly; `jumps[0].shape == (3, 30, 30)`; H all zeros; `one_mode(30, C.KAPPA_2, C.ALPHA)` has exactly one jump.
3. `test_drive_ops_hermitian`: N=10 single mode and the memory `a` of `two_mode(6, 3, ...)`: `X == X†`, `P == P†` to 1e-15; top-left (N-1)x(N-1) block of `[X, P]` equals `2i·I` to 1e-12.
4. `test_drive_quadratures`: `one_mode(20, 0.0, 0.0, eps_z=1.0)`, start `dq.fock(20, 0)`, `tsave = jnp.linspace(0, 0.05, 11)`: `max|Re<a>| < 1e-12`, `Im<a>(0.05)` equals `-0.05` to rel 1e-6. Then `eps_x=1.0` only: `Re<a>(0.05)` equals `+0.05` to rel 1e-6, `max|Im<a>| < 1e-12`.
5. `test_symmetry_eps_z_from_vacuum` (RESEARCH §4.1): `two_mode(12, 4, C.G2, C.EPS_D, C.KAPPA_B, C.KAPPA_A, eps_z=0.2*C.G2)`, from `vacuum2(12, 4)`, `tsave = jnp.linspace(0, 0.5, 51)`: `max|Re<a>| < 1e-12` and `max|Im<a>| > 1e-3` (the drive did act).
6. `test_eps_x_breaks_symmetry`: same with `eps_x=0.2*C.G2` only: `Re<a>(0.5 µs) > 0.05`.
7. `test_one_mode_dark_states`: `H, jumps, a = one_mode(40, C.KAPPA_2, 2.1)`; `||jumps[0] @ dq.coherent(40, ±2.1)|| < 1e-8` for both signs (N=40, not 30: the N=30 truncation residual is ~1e-6); control `||jumps[0] @ fock(40, 0)|| > 1`.
8. `test_loss_jumps_thermal`: `a = dq.destroy(10)`, `ka = C.KAPPA_A`: `loss_jumps(a, ka, 0.05)` has 2 entries equal to `sqrt(ka*1.05) a` and `sqrt(ka*0.05) a†` (1e-15); `n_th=0` gives 1 entry; `ka=0` gives `[]`. `two_mode(..., n_th=0.05)` has 3 jumps in the order of §4.
9. `test_drive_terms_batched_and_guard`: `two_mode(6, 3, ..., eps_z=jnp.array([0., .1, .2])*C.G2)` gives `H.shape == (3, 18, 18)` and slice 0 equals the default H; passing `eps_z` and `eps_x` both as arrays raises `ValueError`; `extra_H` of the wrong shape raises `ValueError`.
10. `test_states2`: `coherent2(20, 3, 2.1)`: `<a>` equals 2.1 to 1e-6; `cat2(20, 3, 2.1, ±1)`: norm 1 to 1e-12, memory parity `dq.expect(dq.tensor(dq.parity(20), dq.eye(3)), ψ)` equals ±1 to 1e-10; `sign=0` raises.
11. `test_config_constants_and_trunc_for`: existing constants unchanged (`C.G2 == C.TWO_PI*0.763`, `C.ALPHA == 2.1`, `(C.NA, C.NB) == (32, 12)`, `(C.NA_START, C.NB_START) == (24, 6)`, `C.N_SINGLE == 30`); `METHOD_LONG.max_steps == 10_000_000`, `rtol == 1e-8`, `atol == 1e-10`; `NA_EIG_MAX is None`; `trunc_for(2.1) == (28, 8)`, `trunc_for(2.1, "inflation") == (30, 12)`, `trunc_for(1.0) == (18, 8)`, `trunc_for(0.5) == (16, 8)`, `trunc_for(2.1, "eig") == (28, 8)`; `"bogus"` raises.
12. `test_z_logical_matches_projector_difference`: alpha=2.1, N=30: `max|z_logical - (|α><α| - |-α><-α|)| < 1e-6`; `code_projector` is idempotent to 1e-10; `code_basis(30, 2.1)[0]` equals `cat_plus(30, 2.1)`.
13. `test_leakage_and_p_right`: N=30, alpha=2.1: `leakage(|α><α|) < 1e-10`; `leakage(|1><1|) > 0.8`; `p_right_well(|α><α|) > 1 - 1e-6`; `p_right_well(|-α><-α|) < 1e-6`.
14. `test_fit_exp_offset_synthetic`: `t = np.linspace(0, 10, 200)`, `y = 0.7*exp(-0.5 t) + 0.27` (noise-free): gamma, A, C each to rel 1e-6; `rel_rms_residual < 1e-8`; `gamma_stderr` finite and >= 0.
15. `test_record_validation(tmp_path, monkeypatch)`: `monkeypatch.setattr(src.results, "RES_DIR", tmp_path)`. A valid record (`id="t9_9.test_q.td.one_mode.a2.10"`, `params=std_params()`, `script="tests/test_l0_core.py"`) writes `tmp_path/records/<id>.json`, has `schema == "duq.record/v2"`, every §6.2 key, the 13 provenance keys, a timestamp matching `^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$`, and `load_record(id)` round-trips. `quick=True` writes `tmp_path/quick/records/<id>.json` and nothing under `tmp_path/records`. `ValueError` for ids `"T2_1.x"`, `"t2_1..x"`, `"t2_1.x y"`, `"t2-1.x"`, `""`; for `value` = NaN, inf, `True`; for `units=""`; for an absolute `script`; for a `cross_check` entry without `tol` or with `agree` inconsistent. `std_params()["g2_MHz"] == 0.763`, `["kappa_a_kHz"] == 9.3`. `save_arrays(id, quick=True, x=np.arange(3))` round-trips.
16. `test_provenance_no_hostname`: `s = json.dumps(provenance("tasks/x.py", 1.0))`; `platform.node()` and `getpass.getuser()` (each if `len >= 4`) not in `s`; `isinstance(dirty, bool)`; `cpu_count == os.cpu_count()`.
17. `test_convergence_helpers`: `sweep(lambda Na, Nb: {"x": Na*Nb}, "Na", [2, 3], {"Nb": 5}) == [{"Na": 2, "Nb": 5, "x": 10}, {"Na": 3, "Nb": 5, "x": 15}]`. `convergence_block` with Na values [8, 12, 16, 20] -> [1.0, 1.1, 1.1001, 1.1001], rel_tol 1e-3: `needed["Na"] == 12`, converged for `chosen Na=16`, not for `Na=8`; results [1.0, 1.2, 1.4] -> not converged; rows given out of order are sorted first.
18. `test_converged_at_reproduces_task_1_2`: load `results/task_1_2.json`; `converged_at(sweep_Na, "peak_na", "Na", 5e-3) == 24`, `(sweep_Nb, "peak_na", "Nb", 5e-3) == 10`, `(sweep_Na, "steady_na", "Na", 1e-3) == 16`, `(sweep_Nb, "steady_na", "Nb", 1e-3) == 4`, each equal to the stored `summary`; `tasks.task_1_2.converged_at is src.convergence.converged_at`.
19. `test_plotting_quick(tmp_path, monkeypatch)`: patch `src.plotting.FIG_DIR`; `save(fig, "x", quick=True)` creates `tmp_path/quick/x.png`.
20. `@pytest.mark.slow test_intro_task_1_0_unchanged(monkeypatch)`: `monkeypatch.setattr(tasks.task_1_0, "save_fig", lambda *a, **k: None)` (so committed figures are untouched); `out = tasks.task_1_0.part_b()`; `abs(out["final_n_sim"] - 0.4998322686860546) < 1e-9`.

## 6. Method, step by step
1. Create the branch (§9), copy `docs/plan/status/_TEMPLATE.md` to `docs/plan/status/l0-core.md`, mark STARTED.
2. Write `pytest.ini`, `tests/conftest.py`, then all 20 tests. Run them; confirm they fail for the right reason (ImportError / AttributeError), commit "l0-core: tests first". Status: TESTS WRITTEN.
3. `src/config.py` additions, then `src/model.py`. Re-run tests 1–11 until green. Do not "fix" a failing symmetry test by loosening 1e-12: check the sign of `P` and that no `eps_z` term leaks a real part.
4. `src/analysis.py` additions (tests 12–14), `src/provenance.py` + `src/results.py` (15–16), `src/convergence.py` + the `tasks/task_1_2.py` import swap (17–18), `src/plotting.py` (19).
5. Run the full fast suite with `--durations=10` (this file < 60 s), then `-m slow`, then the import smoke and the "nothing written" checks (§9). Commit.
6. Update the status file to DONE (§12) and tell the integrator it is ready to merge (G0).

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- Code and tests only. **No records, arrays or figures**, quick or production. Tests write only under `tmp_path`.
- Do not run `python -m tasks.task_1_2` (even `--quick`): it writes `results/task_1_2_quick.json` and `figures/task_1_2_convergence_quick.png` outside the quick dirs.
- Jobs to queue: none. (The intro records are wrapped into v2 by `l0-tools`.)

## 8. Acceptance gates (ALL must pass before DONE)
- `pytest tests/test_l0_core.py -m "not slow"`: all green, wall < 60 s. `-m slow`: green. Full `-m "not slow"` suite green.
- Backward compatibility: tests 1, 2 and 18 pass with exact equality; `import tasks.task_1_0, tasks.task_1_1, tasks.task_1_2, tasks.task_1_3a` succeeds.
- `git diff standard-track -- tasks/task_1_2.py` shows only the removed `converged_at` def and one added import line.
- `git status --porcelain -- results figures` is empty after all test runs (no committed output changed, nothing new written).
- `git diff --name-only standard-track` lists only allowlisted files.
- Every name in CONTRACT §3, §4, §5, §6.1, §7 is importable with the exact signature (check with `inspect.signature` in the REPL).
- `Select-String -Path src\*.py -Pattern "gethostname|platform.node|getuser"` returns nothing.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
git switch -c std/l0-core standard-track          # skip if the worktree already sits on std/l0-core
& $env:DUQ_PY -m pytest tests/test_l0_core.py -m "not slow" -q --durations=10
& $env:DUQ_PY -m pytest tests/test_l0_core.py -m slow -q
& $env:DUQ_PY -m pytest -m "not slow" -q
& $env:DUQ_PY -c "import tasks.task_1_0, tasks.task_1_1, tasks.task_1_2, tasks.task_1_3a; print('ok')"
& $env:DUQ_PY -m src.config                        # prints kappa_2/2pi = 0.896 MHz
git status --porcelain -- results figures          # must print nothing
git diff --name-only standard-track
git add <allowlisted files>; git commit -m "l0-core: ..."   # commit on std/l0-core only; never push to standard-track
```

## 10. Out of scope / do not
- No `src/spectral.py`, `src/linresp.py`, task scripts, tools, notebooks, `requirements.txt`, `.gitignore`, `results/**`, `figures/**`.
- Do not change existing function behavior or constants, rename anything, or reorder jumps. Do not "improve" `converged_at`.
- Do not add a hostname, username or absolute path to any record. No `pip install` into the shared venv. No `pip install -e`.
- Do not weaken a tolerance to make a test pass; write DECISION NEEDED with the measured value.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write in `docs/plan/status/l0-core.md`:
```
### DECISION NEEDED (l0-core, <HH:MM> EDT)
Question: <one sentence>   Evidence: <test name, measured value vs tolerance, command>
Options: A) <...>  B) <...>    Default if no answer by <HH:MM + 15 min>: <A or B>    Blocking G0: yes/no
```
- dynamiqs refuses `jnp_array * QArray` broadcasting for batched H: build `dq.asqarray(jnp.asarray(x)[..., None, None] * X.to_jax())`; record it under "decisions".
- Symmetry test gives 1e-13 < max|Re<a>| < 1e-10: report the value and the solver; do not loosen it yourself.
- Git missing in the worktree: provenance returns `"unknown"` / `dirty=True` and the record still writes; note it.
- A CONTRACT name looks wrong: implement it as written, then DECISION NEEDED. Never rename.
- **Cut line at 60 min** (ship in this order, everything else to "Open items"): model.py + config.py with tests 1–11 -> results.py/provenance.py (15–16) -> convergence.py + task_1_2 swap (17–18) -> analysis additions (12–14) -> plotting quick (19) -> slow test (20). Tests 1, 2, 5, 15 are never cut.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
`docs/plan/status/l0-core.md` at DONE must contain:
- `State: DONE`, branch `std/l0-core`, final commit hash, "ready to merge = G0".
- Test summary: fast count and wall time of this file, slow test result, full-suite count.
- The public API list (every new name in §4) and the gate checklist from §8 with each item ticked.
- Decisions taken: absent optionals serialized as `null`; `rel_rms_residual = rms(resid)/rms(y)`; provenance API names; dark-state test at N=40; `std_params` rounding to 9 decimals; any fallback used.
- Open items / DECISION NEEDED blocks (or "none") and "Outputs: none (code only)".

Judge questions for Harshit (do not answer them here):
1. Why can a drive ε(a + a†) never prepare the +α well starting from vacuum, which exact symmetry does your 1e-12 test check, and why does ε·i(a† − a) escape it?
2. Your records say `"converged": true`. What exactly does that guarantee, and how could a number still be wrong (think of the 20×6 truncation trap) even when two truncations agree?
3. Why fit memory parity with A e^{−γt} + C instead of a pure exponential: what is the steady-state parity at α = 2.1, and which way would a pure-exponential fit bias γ?
