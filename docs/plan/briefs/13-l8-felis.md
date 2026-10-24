# Brief `l8-felis`: Felis / qiskit-alice-bob-provider cross-check

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l8-felis`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/13-l8-felis.md`, then execute this brief exactly. Keep `docs/plan/status/l8-felis.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l8-felis` | `std/l8-felis` (from `standard-track`) | none hard. Soft: the `l2b-gamma-x` and `l2a-gamma-z` records (fall back to illustrative anchors if they are missing) | fast | **1 h, hard cap** (this lane is cut line 3) | Phase 2: start after G1 (9:45 PM Sat Oct 24), finish by **1:00 AM Sun Oct 25**, merge at G2 (1:30 AM) |

## 1. Goal and why
Alice & Bob ship an emulator, "Felis" (`qiskit-alice-bob-provider`), whose physical-cat error model is a closed-form fit. We put its idle error rates at our operating point (n̄ = α² = 4.41, α = 2.1) into our rate conventions and compare them with our Liouvillian results. **Expected finding:** the emulator follows the one-mode scaling (its bit-flip prefactor matches our analytic channel 2 to about 3% at κ₁/κ₂ = 0.01) and misses the ≈ ×3 two-mode non-adiabatic correction that our two-mode eigenvalue shows. Its Γ_Z should match ours, because both are 2κ_a·n̄. This is not required by the challenge prompt. It is a credibility extra: it shows we know the vendor model and where our model goes beyond it. Deliverables: two records, a markdown table and 3 sentences of interpretation.

Physics you need (RESEARCH §1, §5, §6, §10):
- Our parameters: κ_a/2π = 9.3 kHz, so κ_a = 2π·9.3e3 = 5.84336e4 s⁻¹ = 0.0584336 /µs. κ₂/2π = 0.8957 MHz, so κ₂ = 5.62785e6 s⁻¹ = 5.6276 /µs. κ_a/κ₂ = 0.0103829.
- **Provider formulas** (file `qiskit_alice_bob_provider/processor/physical_cat.py`; confirm every one, §6 step 2):
  - Idle X and idle Y: each `0.5*1.1e-3*nbar*k1*exp(-2*nbar)*t`. The 1.1e-3 was fitted at κ₁/κ₂ = 1e-2. There is **no k2 dependence**.
  - Idle Z: `k1*nbar*t`.
  - `utils.full_flip_error` turns the rates into probabilities: pX = ¼(1 + e^{−2(rY+rZ)t} − e^{−2(rX+rZ)t} − e^{−2(rX+rY)t}), and cyclically for pY and pZ.
  - `mz` error is e^{−1.5−0.9n̄} over 850 ns. `mx` error is n̄·k1/k2 over a duration of 1/k2.
  - Limits: n̄ ≥ 4, κ₁ ≥ 10 Hz, 1e-7 ≤ κ₁/κ₂ ≤ 0.1. Ours pass.
  - Backends: `EMU:6Q:PHYSICAL_CATS` takes `average_nb_photons`, `kappa_1` and `kappa_2`, with rates in "Hz". There is **no 1Q physical-cat backend**: `EMU:1Q:LESCANNE_2020` is an interpolated model, so don't use it.
- **Converting conventions** (RESEARCH §5–6, §10). A Pauli channel with rates rX, rY, rZ makes ⟨Z⟩ decay at 2(rX+rY) and ⟨X⟩ decay at 2(rY+rZ).
  - Our Γ_X is the decay of Re⟨a⟩ ∝ ⟨Z_L⟩, so **Γ_X(provider) = 2(rX+rY)**.
  - Our Γ_Z is the decay of parity, i.e. of X_L, so **Γ_Z(provider) = 2(rY+rZ)**.
  - Divide by 1e6 to go from s⁻¹ to /µs. The per-direction rates (Dubovitskii, Felis k1·n̄) are half of ours.
- **Units ambiguity for `kappa_1`.**
  - Interpretation **A** (angular rate, s⁻¹ = 1/T₁): kappa_1 = 58433.6, kappa_2 = 5.62785e6.
  - Interpretation **B** (κ/2π in Hz): kappa_1 = 9300, kappa_2 = 895700.
  - κ₁/κ₂ = 0.0103829 under both. Every provider rate scales with k1, so B = A/2π.
- **Expected numbers** (my arithmetic, illustrative; your tests must reproduce them):

| Quantity at α = 2.1, n̄ = 4.41 | Value |
|---|---|
| e^{−2n̄} | 1.47748e-4 |
| A: rX = rY; rZ (s⁻¹) | 0.0209405; 2.57692e5 |
| A: Γ_X(provider); Γ_Z(provider) (/µs) | **8.3762e-8**; **0.515385** |
| B: Γ_X; Γ_Z (/µs) | 1.33311e-8; 0.082026 |
| Channel 2, c·(κ_a²/κ₂)e^{−2α²}, c = 1; c = 1.3 (/µs) | 8.9645e-8; 1.16538e-7 |
| Channel 1, κ_aα²(coth 2α² − 1) (/µs) | 1.1251e-8 |
| Γ_X(A) / channel 2 (c = 1): at our κ₁/κ₂ = 0.01038; at κ₁/κ₂ = 0.01 exactly (= 2·1.1e-3·n̄/0.01) | 0.9344; 0.9702 |
| Our one-mode anchor 1.1699e-7 (N = 40): provider/ours | 0.716 |
| Our two-mode anchor 3.8831e-7 (28×8): provider/ours | 0.216 (ours is 4.64× = 3.32 two-vs-one-mode × 1.40 one-mode-vs-provider) |
| Γ_Z analytic 2κ_aα²coth(2α²); Task 1.3a fit (/µs) | 0.515384; 0.5135 |
| mz error; mx error; mx duration under A / B | 4.215e-3; 0.04579; 0.178 µs / 1.12 µs |

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (your allowlist), §2 (environment), §6.2 (record schema `duq.record/v2`), §6.3 (IDs, `tfelis`), §12 (runq), §14 (status), §15 (tests).
- `docs/plan/RESEARCH.md` §1, §5 (Γ_X convention, channels, anchors), §6 (Γ_Z), §10 (Felis).
- `AGENTS.md`, plus `docs/plan/status/_TEMPLATE.md`.
- For style only: `tasks/task_1_2.py` (short module docstring, argparse `main`). Unlike the other tasks, this script must not `import src`.
- The installed provider source. Read it, don't guess it: `<felis venv>\Lib\site-packages\qiskit_alice_bob_provider\processor\physical_cat.py`, the `utils` module that defines `full_flip_error`, and the package README in `qiskit_alice_bob_provider-3.0.0.dist-info\METADATA`.

## 3. Allowlist (touch nothing else)
- `tasks/felis_crosscheck.py` (new) and `requirements-felis.txt` (new). Both are from CONTRACT §1.
- `tests/test_l8_felis.py` (new). CONTRACT §15 requires it; the §1 row leaves it out.
- `docs/plan/status/l8-felis.md` (a copy of `_TEMPLATE.md`).
- Your production outputs only: `results/records/tfelis.*.json`. No figures, arrays or notebooks.
- The venv `D:\duq-felis-venv` (outside the repo). **Never** install qiskit into `D:\duq-venv`.

## 4. Interfaces you implement / rely on
Rely on: the files `results/records/<id>.json` (the CONTRACT §6.2 schema), which you read with `json` by path. The three IDs:
- `t2_1.gamma_x.eig.one_mode.a2.10.nth0` (from l2b)
- `t2_1.gamma_x.eig.two_mode.a2.10.nth0` (from l2b)
- `t2_2.gamma_z.td.two_mode.a2.10` (from l2a)

On the provider side, rely on `qiskit_alice_bob_provider.AliceBobLocalProvider().get_backend('EMU:6Q:PHYSICAL_CATS', average_nb_photons=4.41, kappa_1=k1, kappa_2=k2)`.

Implement in `tasks/felis_crosscheck.py`. **Top-level imports are stdlib only** (`argparse, json, math, os, platform, re, subprocess, sys, time, datetime, pathlib, importlib.metadata`). Import qiskit and the provider **inside** the functions that need them. The pure functions must be importable and testable from `D:\duq-venv` too.
```python
NBAR, ALPHA = 4.41, 2.1
KAPPA_A_HZ, KAPPA_2_HZ = 9.3e3, 0.8957e6           # kappa/2pi
OUR_IDS = {"gx_one": "t2_1.gamma_x.eig.one_mode.a2.10.nth0",
           "gx_two": "t2_1.gamma_x.eig.two_mode.a2.10.nth0",
           "gz_td":  "t2_2.gamma_z.td.two_mode.a2.10"}
ANCHORS = {"gx_one": 1.1699e-7, "gx_two": 3.8831e-7, "gz_td": 0.5135}   # RESEARCH §5/§6, ILLUSTRATIVE
ID_GX, ID_GZ = "tfelis.gamma_x.provider.emulator.a2.10", "tfelis.gamma_z.provider.emulator.a2.10"
ID_RE = r"^[a-z0-9_]+(\.[a-z0-9_\-]+)*$"

def provider_kappas(interp: str) -> tuple[float, float]   # 'A' -> (2pi*9.3e3, 2pi*0.8957e6); 'B' -> (9.3e3, 0.8957e6); else ValueError
def pauli_rates(nbar: float, k1: float) -> dict            # {'rX','rY','rZ'} in 1/s, the §1 formulas
def full_flip_error(rX, rY, rZ, t) -> tuple                # (pX, pY, pZ), a local re-implementation
def to_ours(r: dict) -> dict                               # {'gamma_x': 2(rX+rY)/1e6, 'gamma_z': 2(rY+rZ)/1e6} in 1/us
def channel1(alpha) -> float ; def channel2(alpha, c=1.0) -> float ; def gamma_z_coth(alpha) -> float   # 1/us, kappa_a=0.0584336, kappa_2=5.6276 (1/us)
def provider_over_channel2(nbar, kappa_ratio) -> float     # 2*1.1e-3*nbar / kappa_ratio (alpha^2 = nbar)
def load_ours(records_dir: Path, key: str) -> dict         # {'value', 'ref_id', 'source': 'record'|'anchor_illustrative'}
def xcheck(method, ref_id, value, check, tol) -> dict      # rel_diff = |value-check|/|check|; agree = rel_diff <= tol
def provenance(wall_s: float) -> dict                      # see §6 step 6
def make_record(rid, quantity, value, cross_check, numerics, notes, wall_s) -> dict
def validate_record(rec: dict) -> None                     # ValueError: bad id, non-finite value, missing key, schema != 'duq.record/v2'
def write_record(rec: dict, quick: bool) -> Path           # results/records/ or results/quick/records/ (repo root = Path(__file__).resolve().parents[1])
def markdown_table(rows: list[dict]) -> str
def inspect_provider() -> dict                             # lazy import: {'file','version','backends','lines': [(lineno, text), ...]}
def provider_probabilities(interp, t) -> tuple             # lazy: pX,pY,pZ for an idle of t seconds via the provider's OWN code path
def main(argv=None)                                        # --quick, --inspect, --interp {A,B} (default A unless §6 step 3 decides B), --allow-anchors, --records-dir
```

## 5. Tests to write FIRST (TDD)
File: `tests/test_l8_felis.py`.
- At the top: `import tasks.felis_crosscheck as F` and `from pytest import approx`.
- Provider tests begin with `pytest.importorskip("qiskit_alice_bob_provider")`, so in `D:\duq-venv` they skip and the pure tests still run.

The tests:
1. `test_provider_kappas`: `provider_kappas('A') == approx((58433.6, 5.62785e6), rel=1e-5)`; `provider_kappas('B') == (9300.0, 895700.0)`; the ratio k1/k2 equals 0.0103829 (rel 1e-5) for both; `provider_kappas('C')` raises `ValueError`.
2. `test_pauli_rates_formula`: with `pauli_rates(4.41, 58433.6)`, `rX == rY == approx(0.0209405, rel=1e-5)` and `rZ == approx(2.57692e5, rel=1e-5)`. Linear in k1: `pauli_rates(4.41, 2*k1)['rX'] == 2*rX` (rel 1e-12).
3. `test_to_ours_conversion`: `to_ours({'rX':1,'rY':2,'rZ':4}) == {'gamma_x': approx(6e-6), 'gamma_z': approx(1.2e-5)}` at rel 1e-12.
4. `test_full_flip_error_identities`, for rX, rY, rZ, t = 0.3, 0.2, 0.7, 0.5:
   - pX + pY == approx(0.5*(1 - exp(-2*(rX+rY)*t)), rel=1e-12). This is the Z-basis flip probability.
   - At small t (r·t = 1e-5), pX == approx(rX*t, rel=1e-4).
   - All p ≥ 0, and each is ≤ 0.25 + 1e-12 as t → 1e3.
5. `test_expected_numbers`:
   - Interpretation A: `to_ours(pauli_rates(4.41, k1A))` gives gamma_x == approx(8.3762e-8, rel=1e-4) and gamma_z == approx(0.515385, rel=1e-5).
   - Interpretation B: gamma_x == approx(1.33311e-8, rel=1e-4) and gamma_z == approx(0.082026, rel=1e-4).
   - A/B == approx(2π, rel=1e-12).
6. `test_channels`:
   - `channel2(2.1) == approx(8.9645e-8, rel=2e-4)` and `channel2(2.1, c=1.3) == approx(1.16538e-7, rel=2e-4)`.
   - `channel1(2.1) == approx(1.1251e-8, rel=1e-3)` and `gamma_z_coth(2.1) == approx(0.515384, rel=1e-5)`.
   - `provider_over_channel2(4.41, 0.01) == approx(0.9702, rel=1e-4)`.
   - gamma_x(A) / channel2(2.1) == approx(0.9344, rel=2e-3).
7. `test_load_ours_fallback(tmp_path)`:
   - An empty directory gives `source == 'anchor_illustrative'` with values 1.1699e-7, 3.8831e-7, 0.5135, and `ref_id is None`.
   - After writing `tmp_path/'t2_1.gamma_x.eig.two_mode.a2.10.nth0.json'` = `{"id": ..., "value": 4.0e-7}`, you get `source == 'record'`, `value == 4.0e-7`, and `ref_id ==` that ID.
8. `test_xcheck`: `xcheck('m', None, 1.1, 1.0, 0.1)` gives rel_diff == approx(0.1) and agree True (the comparison is `<=`). `xcheck(..., 1.2, 1.0, 0.1)` gives agree False. Keys == {method, ref_id, value, rel_diff, tol, agree}.
9. `test_record_schema`. Build `make_record(ID_GX, 'Gamma_X', 8.3762e-8, [...], {...}, 'convergence null: ...', 1.0)`, then check:
   - `validate_record` passes; `schema == 'duq.record/v2'`; `task == 'felis'`; `units == '1/us'`.
   - `convergence is None` and `'convergence' in notes`.
   - The keys match CONTRACT §6.2. `provenance` has {script, git_commit, git_branch, dirty, python, platform, cpu_count, wall_s, timestamp}, has **no** key containing `host` or `user`, and the timestamp ends in `Z`.
   - `json.loads(json.dumps(rec)) == rec`.
   - `validate_record` raises `ValueError` on id `'Tfelis.X'` and on value `float('nan')`.
10. `test_no_src_import`. Parse `tasks/felis_crosscheck.py` with `ast`, then check:
    - No `Import` or `ImportFrom` node names `src` or `dynamiqs` anywhere.
    - Top-level imports come only from the stdlib list in §4.
    - A subprocess `[sys.executable, '-c', 'import tasks.felis_crosscheck, sys; assert "qiskit" not in sys.modules']`, run from the repo root, exits 0.
11. `test_provider_source_matches` (importorskip):
    - `inspect_provider()['file']` ends with `physical_cat.py`, and `version == '3.0.0'`.
    - `lines` contains entries matching `1\.1e-3` and `exp\(`.
    - `'EMU:6Q:PHYSICAL_CATS' in backends`, and no name contains both `1Q` and `PHYSICAL_CATS`.
12. `test_provider_probabilities_match_local` (importorskip). For interp A and B and t in {1e-6, 1e-3} s, `provider_probabilities(interp, t)` == local `full_flip_error(**pauli_rates(4.41, k1), t)` at rel 1e-9 for each of pX, pY, pZ. If the source exposes no callable idle-error path, use `pytest.xfail` with a reason that names the symbols you looked for, and record this in the status file.

## 6. Method, step by step
1. **Setup.** Create the branch and the status file. Create the venv (§9). Write `requirements-felis.txt` with `qiskit-alice-bob-provider==3.0.0` and `pytest`. Install it. Then replace those lines with exact `==` pins taken from `uv pip freeze` for `qiskit-alice-bob-provider, qiskit, qiskit-aer, pyqir, numpy, scipy, pytest`, and reinstall to confirm. Expected: qiskit 2.x (≥ 2.5, < 3), qiskit-aer 0.17.x, pyqir 0.10.x, Python 3.12. Paste the versions into the status file.
2. **Source confirmation** (read-only, about 10 min):
   - Print `physical_cat.__file__`.
   - Find the lines (with line numbers) that compute the idle X/Y/Z errors, the call to `full_flip_error` and its definition in `utils`, the `mz`/`mx` errors and durations, and the n̄/κ limit checks.
   - Paste them verbatim into the status file under a heading `Provider source (physical_cat.py)`.
   - Fill in a 5-row table (idle X/Y, idle Z, full_flip_error, mz, mx), marking each against RESEARCH §10 as **CONFIRMED** or **DIFFERS (quote)**.
   - Also list the names from `AliceBobLocalProvider().backends()`.
   - Any DIFFERS → DECISION NEEDED (§11). Implement what the installed source does, not what RESEARCH says.
3. **Units of kappa_1** (decide from evidence; never from which answer matches ours):
   - Grep the package for `pi` (`np.pi`, `math.pi`, `2 * pi`) and read the `kappa_1`/`kappa_2` docstrings and the README in `METADATA`.
   - Rules:
     - If the probabilities are f(k1·t) with t in seconds (mz 850e-9) and no 2π anywhere, kappa_1 is a rate in s⁻¹ (1/T₁). That is **A**, and `kappa_1 = κ_a = 2π·9.3e3`.
     - If the docs say κ/2π explicitly, or the code multiplies by 2π, it is **B**.
     - If neither settles it, use A as primary and write DECISION NEEDED.
   - Always compute **both** and put both in `numerics` and in the table.
   - Physics consistency check (report it, don't decide by it): under A, Γ_Z(provider) = 2κ_a·n̄ = 0.5154 /µs, which equals our prediction. Under B it would be 2π× too small.
4. **Tests** (§5). Write them, run them under both interpreters, and watch them fail. Commit the tests. Update the status file.
5. **Implement the pure functions**, then `inspect_provider` and `provider_probabilities`:
   - Find where `physical_cat.py` calls `full_flip_error` for the idle/delay instruction, and call that same code path with `average_nb_photons=4.41, kappa_1=k1, kappa_2=k2` and duration t. If it is a method, instantiate its processor class with the same kwargs that `get_backend` takes.
   - Name the exact symbol you used in the status file.
   - Also construct `get_backend('EMU:6Q:PHYSICAL_CATS', ...)` once for each interpretation. This proves the limits pass.
6. **Records** (plain JSON, schema `duq.record/v2`). `params`:
   ```
   {'g2_MHz': 0.763, 'kappa_b_MHz': 2.6, 'kappa_a_kHz': 9.3, 'alpha': 2.1, 'n_th': 0.0,
    'eps_z_over_g2': 0.0, 'eps_x_over_g2': 0.0, 'nbar': 4.41, 'kappa_2_MHz': 0.8957,
    'backend': 'EMU:6Q:PHYSICAL_CATS', 'kappa_1_passed': k1, 'kappa_2_passed': k2, 'interp': 'A'|'B'}
   ```
   `provenance`, built by the local helper:
   - `git_commit`: `git rev-parse --short HEAD` via `subprocess`. `git_branch`: `git rev-parse --abbrev-ref HEAD`.
   - `dirty`: `git status --porcelain -- src tasks tools` is non-empty (CONTRACT §6.2).
   - `python`: `platform.python_version()`. `platform`: `platform.platform()`. `cpu_count`: `os.cpu_count()`.
   - `wall_s`; `timestamp`: UTC `YYYY-MM-DDTHH:MM:SSZ`.
   - `script`: `'tasks/felis_crosscheck.py'`.
   - `dynamiqs: None, jax: None`; `numpy` and `scipy` from `importlib.metadata.version`; plus `qiskit`, `qiskit_aer`, `qiskit_alice_bob_provider` and `pyqir` versions.
   - Never the hostname or username.
7. **Load ours** with `load_ours` (default `--records-dir` is `results/records`):
   - If any value came from anchors, a production run exits 2 unless `--allow-anchors` is given.
   - With `--allow-anchors`, the `notes` begin `ILLUSTRATIVE (RESEARCH §5/§6 anchors; re-run after l2a/l2b merge).`, the cross-check method names get the suffix `_anchor`, and `ref_id` is `None`.
   - First try `git merge standard-track`, in case l2a/l2b have landed.
8. **Print** the markdown table (§7) to stdout and copy it into the status file. Then write 3 sentences of interpretation: (1) Γ_Z agreement and the units verdict; (2) the provider vs channel 2 / one-mode / two-mode ratios, i.e. which physics is missing; (3) the consequence, e.g. "at κ_b/g₂ = 3.4 the emulator's T_X at n̄ = 4.41 is optimistic by ~N×, and its κ₂-free prefactor holds only near κ₁/κ₂ ≈ 1e-2."
9. **Optional** (cut first): a sampled Aer circuit. Initialize |0⟩, idle for T, measure Z, 2e4 shots. Check against ½(1 − e^{−2(rX+rY)T}) plus the mz error, at T = 1 s under A (≈ 0.044 ± 0.0015). Run it only if the backend exposes `delay`.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **`tfelis.gamma_x.provider.emulator.a2.10`**:
  - `task 'felis'`, `quantity 'Gamma_X'`, `units '1/us'`, `method 'provider_formula_physical_cat'`, value = 2(rX+rY)/1e6 for the primary interpretation (A expected: 8.3762e-8).
  - `uncertainty None`, `truncation None`, `convergence None`, `artifacts None`.
  - `numerics = {rX_per_s, rY_per_s, rZ_per_s, gamma_x_interp_A, gamma_x_interp_B, kappa1_over_kappa2, ratio_to_channel2_c1, prefactor_ratio_at_0p01: 0.9702, ratio_to_one_mode, ratio_to_two_mode, provider_symbol}`.
  - `cross_check`, with tolerances fixed here; **do not tune them after seeing the numbers**:
    - `analytic_channel2_c1`: ref null, tol **0.10**, expect agree (≈ 0.066).
    - `liouvillian_eig_one_mode`: ref `t2_1.gamma_x.eig.one_mode.a2.10.nth0`, tol **0.50**, expect agree (≈ 0.28).
    - `liouvillian_eig_two_mode`: ref `t2_1.gamma_x.eig.two_mode.a2.10.nth0`, tol **0.50**, expect **agree false** (≈ 0.78). That disagreement is the finding.
- **`tfelis.gamma_z.provider.emulator.a2.10`**:
  - `quantity 'Gamma_Z'`, value = 2(rY+rZ)/1e6 (A expected: 0.515385). The other fields are as above.
  - `numerics` = {rates, gamma_z_interp_A, gamma_z_interp_B, mz_error: 4.215e-3, mz_duration_s: 8.5e-7, mx_error: 0.04579, mx_duration_s}.
  - `cross_check`: `time_domain_fit_two_mode` (ref `t2_2.gamma_z.td.two_mode.a2.10`, tol **0.02**) and `analytic_coth` (0.515384, tol **0.02**).
- **`notes`** (both records) must say:
  - "Closed-form provider formula, no truncation dependence: convergence null."
  - The conversion, Γ_X = 2(rX+rY) and Γ_Z = 2(rY+rZ), from s⁻¹ to /µs.
  - Which kappa_1 interpretation was used, and the evidence for it.
  - "1.1e-3 fitted at κ₁/κ₂ = 1e-2, no κ₂ dependence."
- **Table on stdout** (and in the status file). Columns: `Quantity | Value (1/us) | Source (record id or formula) | provider / this`. Rows:
  - Γ_X: provider A, provider B, one-mode eig, two-mode eig, channel 2 (c = 1), channel 2 (c = 1.3), channel 1.
  - Γ_Z: provider A, provider B, ours td, analytic coth.
  - mz and mx errors.
- **Quick vs production:**
  - `--quick` writes `results/quick/records/tfelis.*.json` (git-ignored) and may use anchors.
  - Production writes `results/records/` and refuses if `dirty` is true.
  - The whole run takes seconds, so the lane runs production itself.
- **Jobs to queue:** if anchors were used, add one row: `felis_rerun | D:\duq-felis-venv\Scripts\python.exe -m tasks.felis_crosscheck | 0.5 GB | < 1 min | tfelis.gamma_x.provider.emulator.a2.10, tfelis.gamma_z.provider.emulator.a2.10`. Note that it runs after the l2b α = 2.1 eig records exist. It goes through `python -m tools.runq submit --name felis_rerun --ram-gb 0.5 -- D:\duq-felis-venv\Scripts\python.exe -m tasks.felis_crosscheck`.

## 8. Acceptance gates (ALL must pass before DONE)
1. The venv exists. `requirements-felis.txt` has exact `==` pins and includes `qiskit-alice-bob-provider==3.0.0`. Importing it prints 3.0.0.
2. `tests/test_l8_felis.py`:
   - Passes in the Felis venv (`--noconftest`) with **0 skipped** provider tests. An xfail on test 12 is allowed only with a documented reason.
   - Passes in `D:\duq-venv`, where the provider tests skip and the pure tests pass, in under 10 s.
3. The status file contains the `physical_cat.py` path, the verbatim source lines with line numbers, the 5-row CONFIRMED/DIFFERS table and the backend list.
4. The units verdict (A or B) is stated with a quoted line of evidence, or a DECISION NEEDED is written. Both interpretations appear in the numerics and in the table.
5. Γ_Z(provider, primary) agrees with `analytic_coth` and with the td record within 2%. Otherwise → DECISION NEEDED (most likely units).
6. Γ_X(provider, primary)/channel2(c = 1) is within 10% of 1, and the prefactor ratio at κ₁/κ₂ = 0.01 is 0.9702 ± 1e-4.
7. Both production records validate (`validate_record`), use the exact IDs, have `convergence: null` with notes, the stated tolerances and `provenance.dirty == false`, and have no host or user fields.
8. The script has no `src` or `dynamiqs` import, and a top-level qiskit import is absent (test 10). Quick and production runs each take under 2 min.
9. The table and the 3 sentences are in the status file.

## 9. Commands
```powershell
git switch -c std/l8-felis standard-track                 # skip if the worktree already made it
Copy-Item docs/plan/status/_TEMPLATE.md docs/plan/status/l8-felis.md
uv venv D:\duq-felis-venv -p 3.12                         # fallback: py -3.12 -m venv D:\duq-felis-venv
uv pip install --python D:\duq-felis-venv\Scripts\python.exe -r requirements-felis.txt
uv pip freeze --python D:\duq-felis-venv\Scripts\python.exe   # copy exact pins into requirements-felis.txt
$env:FELIS_PY = "D:\duq-felis-venv\Scripts\python.exe"; $env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
& $env:FELIS_PY -c "import qiskit_alice_bob_provider.processor.physical_cat as m; print(m.__file__)"
Select-String -Path "<that file>" -Pattern '1\.1e-3','exp\(','full_flip_error','pi','mz','mx','kappa'
& $env:FELIS_PY -m pytest tests/test_l8_felis.py --noconftest -q   # conftest imports src.config (dynamiqs): not in this venv
& $env:DUQ_PY -m pytest tests/test_l8_felis.py -q
& $env:FELIS_PY -m tasks.felis_crosscheck --inspect          # prints the path, version, lines and backends: paste into status
& $env:FELIS_PY -m tasks.felis_crosscheck --quick --allow-anchors
git add tasks/felis_crosscheck.py tests/test_l8_felis.py requirements-felis.txt; git commit -m "feat(l8): Felis provider cross-check"
git status --porcelain -- src tasks tools                    # must be empty
& $env:FELIS_PY -m tasks.felis_crosscheck                    # add --allow-anchors only if the l2a/l2b records are absent
git add results/records/tfelis.* docs/plan/status/l8-felis.md; git commit -m "results(l8): Felis cross-check records"
```
`XLA_FLAGS` is irrelevant here (no JAX), and this is not a heavy job.

## 10. Out of scope / do not
- Do not import `src`, do not install anything into `D:\duq-venv`, and do not use `pip install -e`. Do not edit `src/**`, other lanes' files, `CONTRACT.md`, `RESEARCH.md` or the challenge prompt.
- Do not use `EMU:1Q:LESCANNE_2020` as a physical-cat result. You may mention it in one line.
- Do not run Felis gate or circuit benchmarks, logical-qubit (`EMU:40Q`/`LOGICAL`) backends, or Felis cloud/remote backends (they need an API key: **never enter one**).
- Do not loosen any tolerance or flip an `agree`. Do not hand-edit record JSON. Do not decide the units by which answer matches ours.
- Do not claim that the emulator is "wrong". It is a fit to a different regime, one-mode at κ₁/κ₂ = 1e-2. Our claim is the missing ≈ ×3 two-mode correction at κ_b/g₂ = 3.4.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Use the status-file block:
> **Q:** Is Felis `kappa_1` an angular rate (s⁻¹ = 1/T₁, pass 2π·9.3e3) or κ/2π (pass 9.3e3)? Evidence: <quotes>. A gives Γ_Z = 0.5154 /µs and Γ_X = 8.38e-8 /µs; B gives 0.0820 and 1.33e-8.
> **Options:** A) record interpretation A, with B in the numerics; B) record B. **Recommendation:** A (rates multiply t in seconds; Γ_Z then equals 2κ_a·n̄). **Blocking?** no: both computed, A written.

Other triggers:
- A formula DIFFERS from RESEARCH §10. Implement the installed source and quote the diff.
- Install fails: no wheel for py3.12, or a pyqir/aer conflict. Try `-p 3.11`. If that fails too, use the fallback below.
- `provider_probabilities` is unreachable. Use the test-12 xfail and the source-line evidence.

Fallback if the provider can't be installed in 20 min: implement the formulas from RESEARCH §10 only, set `method 'provider_formula_research_s10'`, and mark both records' notes `NOT VERIFIED AGAINST INSTALLED SOURCE`. Set State `DONE_WITH_CONCERNS`.

**Cut line (in order):**
1. The step 9 Aer sampling.
2. Test 12, the provider-path probabilities (keep the source lines).
3. The whole lane (global cut 3). At the 1 h cap, stop, commit tests and code, and set State `BLOCKED` with what exists.

Never cut the units verdict, the conversion formulas in the notes, or the fixed tolerances.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
At DONE the status file has:
- State `DONE` (or `DONE_WITH_CONCERNS`) and the last commit sha.
- The pinned versions.
- The `physical_cat.py` path and verbatim lines, the CONFIRMED/DIFFERS table, the backend list and the units verdict with evidence.
- Every §8 gate ticked, with its command and key output.
- The records table: both IDs, values, and each cross-check with method, rel_diff, tol and agree.
- The markdown table and the 3 interpretation sentences.
- Whether anchors were used, and the `felis_rerun` row in Jobs to queue if they were.
- Deviations, plus notes for review: anything surprising, and anything you were tempted to loosen.

Explain-back questions (write them into the status file; Harshit answers in `docs/defense.md`):
1. The emulator's phase-flip rate is k1·n̄, but we report Γ_Z = 2κ_a·n̄. Where does the factor 2 come from in Pauli-channel terms? And why does the Γ_Z comparison also test whether `kappa_1` means κ or κ/2π?
2. The emulator's bit-flip prefactor has no κ₂ dependence, while our channel 2 scales as κ_a²/κ₂. At what κ₁/κ₂ do they coincide? And what would the emulator get wrong if κ₂ were doubled at fixed κ₁?
3. Our two-mode Γ_X at α = 2.1 is about 4.6× the emulator's. How much of that is channel 1 plus the fitted c, and how much is the two-mode non-adiabatic correction? And why should an adiabatically eliminated model underestimate bit flips at κ_b/g₂ = 3.4?
