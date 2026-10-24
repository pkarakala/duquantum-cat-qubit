# Interface contract

**Frozen at gate G0.** Every lane codes against these exact names. To change one, write a `DECISION NEEDED` in your status file. Do not change it in your own lane.

Sections: 1 Lanes · 2 Environment · 3 Model · 4 Config · 5 Analysis · 6 Results v2 · 7 Convergence · 8 Spectral · 9 Linear response · 10 Pulses and circuit · 11 Claims · 12 Run queue · 13 Lab data · 14 Status files · 15 Tests

---

## 1. Lanes, branches and file ownership

| Lane slug | Brief | Branch | Status file | Owns (allowlist; nobody else edits these) |
|---|---|---|---|---|
| `setup` | `briefs/00-setup.md` | (none; done on `standard-track`) | `status/setup.md` | `requirements.txt` (pins only) |
| `l0-core` | `briefs/01-l0-core.md` | `std/l0-core` | `status/l0-core.md` | `src/model.py`, `src/config.py`, `src/analysis.py`, `src/results.py`, `src/provenance.py`, `src/convergence.py`, `src/plotting.py`, `tasks/task_1_2.py` (import change only), `tests/conftest.py`, `tests/test_l0_core.py`, `pytest.ini` |
| `l0-tools` | `briefs/02-l0-tools.md` | `std/l0-tools` | `status/l0-tools.md` | `tools/build_index.py`, `tools/check_claims.py`, `tools/wrap_intro_records.py`, `tools/runq.py`, `run_all.sh`, `.github/workflows/tests.yml`, `tests/test_l0_tools.py` |
| `l1-spectral` | `briefs/03-l1-spectral.md` | `std/l1-spectral` | `status/l1-spectral.md` | `src/spectral.py`, `tasks/task_spectral_profile.py`, `tests/test_l1_spectral.py` |
| `l2a-gamma-z` | `briefs/04-l2a-gamma-z.md` | `std/l2a-gamma-z` | `status/l2a-gamma-z.md` | `tasks/task_2_2.py`, `notebooks/07_task_2_2_phase_flips.ipynb`, `tests/test_l2a_gamma_z.py` |
| `l2b-gamma-x` | `briefs/05-l2b-gamma-x.md` | `std/l2b-gamma-x` | `status/l2b-gamma-x.md` | `tasks/task_2_1_eig.py`, `tasks/task_2_1_td.py`, `tasks/task_2_1_channels.py`, `tasks/task_2_1_thermal.py`, `tasks/task_2_1_figures.py`, `notebooks/06_task_2_1_bit_flips.ipynb`, `tests/test_l2b_gamma_x.py` |
| `l3-prep` | `briefs/06-l3-prep.md` | `std/l3-prep` | `status/l3-prep.md` | `tasks/task_1_3b.py`, `tasks/task_lab_frames.py`, `docs/task_1_3c.md`, `notebooks/05_task_1_3b_prepare_zero.ipynb`, `tests/test_l3_prep.py` |
| `l4a-readout` | `briefs/07-l4a-readout.md` | `std/l4a-readout` | `status/l4a-readout.md` | `src/linresp.py`, `tasks/task_2_3.py`, `notebooks/08_task_2_3_readout.ipynb`, `tests/test_l4a_readout.py` |
| `l5-circuit` | `briefs/08-l5-circuit.md` | `std/l5-circuit` | `status/l5-circuit.md` | `src/circuit.py`, `tasks/task_2_4a.py`, `docs/derivation_2_4a.md`, `tests/test_l5_circuit.py` |
| `l4b-tradeoff` | `briefs/09-l4b-tradeoff.md` | `std/l4b-tradeoff` | `status/l4b-tradeoff.md` | `tasks/task_2_4b.py`, `tests/test_l4b_tradeoff.py` |
| `l4c-capstone` | `briefs/10-l4c-capstone.md` | `std/l4c-capstone` | `status/l4c-capstone.md` | `src/pulses.py`, `tasks/task_2_4c_pulses.py`, `tasks/task_2_4c_verify.py`, `notebooks/09_task_2_4_readout_design.ipynb`, `tests/test_l4c_capstone.py` |
| `l6-lab` | `briefs/11-l6-lab.md` | `std/l6-lab` | `status/l6-lab.md` | `site/**`, `tools/export_lab_data.py`, `.github/workflows/pages.yml` |
| `l7-docs` | `briefs/12-l7-docs.md` | `std/l7-docs` | `status/l7-docs.md` | `README.md`, `TECHNICAL.md`, `docs/defense_questions.md`, `docs/video_script.md`, `docs/devpost.md`, `slides/**`, `notebooks/01_*` to `04_*` (setup-cell fix only) |
| `l8-felis` | `briefs/13-l8-felis.md` | `std/l8-felis` | `status/l8-felis.md` | `tasks/felis_crosscheck.py`, `requirements-felis.txt` |
| `integrator` | `briefs/90-integrator.md` | works **on** `standard-track` | `status/integrator.md` | merges, plus production outputs: `results/records/**`, `results/arrays/**`, `results/index.json`, `figures/**`, `site/src/data/live/**` |
| `reviewer` | `briefs/91-reviewer.md` | read-only | `status/reviews/<lane>.md` | nothing else |

**Shared rules:**
- Every lane also owns its own status file, `docs/plan/status/<slug>.md`. The Lab lane additionally owns `docs/plan/status/l6-shots/**` for smoke-test screenshots. Reviewers own `docs/plan/status/reviews/<slug>.md`.
- Any lane may *add* its own production outputs, i.e. `results/records/<its ids>.json`, `results/arrays/<its ids>.npz` and `figures/task_<its task>_*.png`.
- Record IDs are unique per lane (§6.3), so two lanes never write the same file.
- **Nobody** edits `docs/challenge_prompt_v4.md`, `notes/`, `prep/`, `reviews/` (except new review files), or another lane's files.
- `docs/handwritten/` and `docs/defense.md` are **Harshit-only** (human authorship evidence).

---

## 2. Environment and commands

- **Shared interpreter (Windows):** `D:\duq-venv\Scripts\python.exe`, created by `briefs/00-setup.md`.
  - Optional override: environment variable `DUQ_PY`.
  - Every worktree uses the same interpreter. **No `pip install -e`.**
  - Always run from the worktree root, as modules: `& $env:DUQ_PY -m tasks.task_2_2 --quick`.
- **PowerShell setup:**
  ```powershell
  $env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
  $env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
  ```
  `OMP_NUM_THREADS` does **not** limit XLA.
- **Unix / WSL / cloud:** `.venv/bin/python` (created by `.cursor/setup-worktree-unix.sh`).
- **Tests:** `& $env:DUQ_PY -m pytest -m "not slow" -q` (under 2 min in total). Slow tests: `-m slow`.
- **Quick vs production:**
  - Every task script supports `--quick`, a small-grid smoke run in **≤ 2 min** whose outputs go to the git-ignored `results/quick/` and `figures/quick/`.
  - A run without `--quick` is a production run.
  - Lanes may run and commit production outputs for jobs **≤ 15 min**. Longer jobs are submitted to `tools/runq.py` by the integrator after the merge.
- **Heavy-job limits:** 16 GB laptop. At most 3 concurrent heavy processes, and **only one sparse LU larger than 3 GB at a time**.

---

## 3. `src/model.py`

These are backward compatible: with the default arguments, the existing intro-track calls produce identical H and jumps, in the same order.

```python
def loss_jumps(a, kappa_a, n_th=0.0) -> list:
    """[sqrt(kappa_a*(1+n_th)) a] + ([sqrt(kappa_a*n_th) a†] if n_th > 0). Empty list if kappa_a == 0."""

def drive_ops(a) -> tuple:
    """(X, P) = (a + a†, i(a† - a)). Both Hermitian.
    eps_z * X : READOUT drive. Heisenberg: da/dt = -i eps_z, so it pushes along the IMAGINARY axis
                (a Z_L rotation in the code space). It can NOT select a well from vacuum (RESEARCH §4.1).
    eps_x * P : real-axis displacement drive. da/dt = +eps_x, so it pushes along +Re. Breaks alpha -> -alpha."""

def one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, eps_z=0.0, eps_x=0.0):
    """Effective model. Returns (H, jumps, a).
    H = eps_z X + eps_x P   (dq.zeros(N) when both are 0)
    jumps = [sqrt(kappa_2)(a^2 - alpha^2)] + loss_jumps(a, kappa_a, n_th)
    kappa_2, eps_z, eps_x may be arrays (batch axis via jnp.asarray(x)[..., None, None] * op).
    At most ONE argument may be batched per call."""

def two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, eps_z=0.0, eps_x=0.0, extra_H=None):
    """Full memory+buffer model (rotating frame, real g2). Returns (H, jumps, (a, b)).
    H = g2 a^2 b† + g2 a†^2 b - eps_d (b + b†) + eps_z X + eps_x P + (extra_H or 0)
    jumps = [sqrt(kappa_b) b] + loss_jumps(a, kappa_a, n_th)
    eps_z / eps_x may be arrays (one batched arg per call). extra_H: a QArray on (Na, Nb), e.g. Kerr terms."""

def vacuum2(Na, Nb)                    # |0>_a ⊗ |0>_b   (existing)
def coherent2(Na, Nb, alpha)           # |alpha>_a ⊗ |0>_b
def cat2(Na, Nb, alpha, sign=+1)       # |C±>_a ⊗ |0>_b,  |C±> = unit(|alpha> ± |-alpha>)
```

---

## 4. `src/config.py` additions

```python
METHOD_LONG = dq.method.Tsit5(rtol=1e-8, atol=1e-10, max_steps=10_000_000)  # long Γ_X traces (tens of µs)
NA_EIG_MAX, NB_EIG_MAX = None, None     # filled in by L1 (largest feasible eigen basis on this laptop)

def trunc_for(alpha, purpose="steady") -> tuple[int, int]:
    """STARTING POINT ONLY; every number still needs its own convergence block.
    'steady'    : Na = max(16, ceil(alpha**2 + 6*alpha + 10)) rounded up to even, Nb = 8
    'inflation' : Na = max(24, ceil(1.6*alpha**2 + 6*alpha + 10)) rounded up to even, Nb = 12
    'eig'       : same as 'steady'"""
```
All existing constants stay unchanged: `TWO_PI, G2, KAPPA_B, KAPPA_A, ALPHA, EPS_D, KAPPA_2, N_SINGLE, NA_START, NB_START, NA, NB, METHOD`.

---

## 5. `src/analysis.py` additions

```python
def fit_exp_offset(t, y, p0=None) -> dict:
    """Fit y = A exp(-gamma t) + C (scipy.optimize.curve_fit). Returns
    {'gamma', 'A', 'C', 'gamma_stderr', 'rel_rms_residual'}. Use for parity (steady parity = 1/cosh(2 alpha^2) != 0)."""
def code_basis(N, alpha) -> tuple            # (|C+>, |C->) kets on N levels
def z_logical(N, alpha)                      # |C+><C-| + |C-><C+|  (≈ |alpha><alpha| - |-alpha><-alpha|)
def code_projector(N, alpha)                 # |C+><C+| + |C-><C-|
def leakage(rho_a, alpha) -> float           # 1 - Tr(code_projector rho_a)
def p_right_well(rho_a, alpha) -> float      # (1 + Tr(z_logical rho_a)) / 2
```
Existing functions are unchanged: `memory_state, top_projector, cat_plus, memory_extras, fit_exp_decay, settle_time`.

---

## 6. Results v2 (`src/results.py`, `src/provenance.py`)

### 6.1 API
```python
def std_params(alpha=C.ALPHA, n_th=0.0, eps_z=0.0, eps_x=0.0, **extra) -> dict:
    """{'g2_MHz': 0.763, 'kappa_b_MHz': 2.6, 'kappa_a_kHz': 9.3, 'alpha': alpha, 'n_th': n_th,
        'eps_z_over_g2': eps_z / C.G2, 'eps_x_over_g2': eps_x / C.G2, **extra}"""

def record(id, *, task, quantity, value, units, method, params, script,
           truncation=None, uncertainty=None, convergence=None, numerics=None,
           cross_check=None, artifacts=None, wall_s=None, notes=None, quick=False) -> Path:
    """Validate + write results/records/<id>.json (or results/quick/records/<id>.json if quick).
    Fills 'schema' and 'provenance' automatically. Raises ValueError on a bad id, a non-finite value,
    or a missing required field."""

def save_arrays(id, quick=False, **arrays) -> Path      # results/arrays/<id>.npz (or results/quick/arrays/)
def load_record(id) -> dict
def save(name, data)                                    # existing flat JSON API, unchanged
```
`src/plotting.save(fig, name, dpi=200, quick=False)`: with `quick=True` it writes to `figures/quick/`.

### 6.2 Record schema (`duq.record/v2`)
```json
{
  "schema": "duq.record/v2",
  "id": "t2_1.gamma_x.eig.two_mode.a1.40.nth0",
  "task": "2.1",
  "quantity": "Gamma_X",
  "value": 1.2021e-4,
  "uncertainty": 2e-8,
  "units": "1/us",
  "method": "liouvillian_eig_odd_sector",
  "params": {"g2_MHz": 0.763, "kappa_b_MHz": 2.6, "kappa_a_kHz": 9.3, "alpha": 1.4, "n_th": 0.0,
             "eps_z_over_g2": 0.0, "eps_x_over_g2": 0.0},
  "truncation": {"Na": 28, "Nb": 8},
  "convergence": {
    "key": "Gamma_X", "rel_tol": 1e-3,
    "sweeps": {"Na": {"fixed": {"Nb": 8},  "values": [20, 24, 28, 32], "results": [1.21e-4, 1.2022e-4, 1.2021e-4, 1.2021e-4]},
               "Nb": {"fixed": {"Na": 28}, "values": [6, 8, 10],       "results": [1.2020e-4, 1.2021e-4, 1.2021e-4]}},
    "needed": {"Na": 24, "Nb": 6}, "converged": true
  },
  "numerics": {"rel_residual": 3e-7, "edge_weight": 1e-9, "cond_est": 1.2e2, "sector": "odd", "sigma": 0.0, "k": 2},
  "cross_check": [
    {"method": "time_domain_fit", "ref_id": "t2_1.gamma_x.td.two_mode.a1.40", "value": 1.19e-4, "rel_diff": 0.009, "tol": 0.02, "agree": true},
    {"method": "analytic_channels", "ref_id": null, "value": 1.17e-4, "rel_diff": 0.027, "tol": 0.3, "agree": true}
  ],
  "artifacts": {"figure": "figures/task_2_1_gamma_x.png", "arrays": "results/arrays/t2_1.gamma_x.eig.two_mode.a1.40.nth0.npz"},
  "notes": "free text, optional",
  "provenance": {
    "script": "tasks/task_2_1_eig.py", "git_commit": "abc1234", "git_branch": "standard-track", "dirty": false,
    "dynamiqs": "0.3.7", "jax": "0.12.0.1", "numpy": "x", "scipy": "x", "python": "3.12.13",
    "platform": "Windows-11-...", "cpu_count": 12, "wall_s": 12.3, "timestamp": "2026-10-24T23:10:00Z"
  }
}
```
(All numbers above are synthetic examples.)

**Field rules:**
- **`convergence`:**
  - `needed` is produced by `converged_at` for each axis.
  - `converged` is true when, for each swept axis, the chosen truncation is ≥ `needed` **and** the two largest values agree within `rel_tol`.
  - Use `null` only for quantities that don't depend on truncation (for example analytic or Felis values). Those records must say so in `notes`.
- **`numerics`:** required for eigenvalue records (`rel_residual`, `edge_weight`, `cond_est`, `sector`, `sigma`, `k`). Optional otherwise. For fits, include `fit_window_us`, `gamma_stderr` and `rel_rms_residual`.
- **`cross_check`:** a list of independent checks. Each entry has `agree = rel_diff <= tol`, and **the tolerance must be stated**.
- **`provenance.dirty`:** true if `git status --porcelain -- src tasks tools` is non-empty. **Production records must have `dirty: false`.** Commit code first, run second, commit outputs third.
- **`provenance.platform`:** use `platform.platform()` and `os.cpu_count()`. **Never** use the hostname or username.

### 6.3 Record ID scheme
The pattern is `t<task>.<quantity>.<method>.<model>[.<tags>]`. It is lowercase, matches the regex `^[a-z0-9_]+(\.[a-z0-9_\-]+)*$`, and allows dots inside numeric tags (`a1.40`).

The lists below are the **common** values. Any other lowercase snake_case quantity, method or model token is allowed (for example `leakage`, `wall_s`, `peak_na`, `emulator`), provided the lane's brief names it and the ID stays unique to that lane.

| Part | Values |
|---|---|
| task | `t1_3b`, `t2_1`, `t2_2`, `t2_3`, `t2_4a`, `t2_4b`, `t2_4c`, `tfelis`, `t1_0`, `t1_1`, `t1_2`, `t1_3a` (intro, wrapped) |
| quantity | `gamma_x`, `gamma_z`, `gamma_local_slope`, `gamma_fit`, `kappa_a_exponent`, `slope_over_2kappa_a`, `b_ss`, `ring_freq`, `settle_5pct`, `settle_1pct`, `dephasing`, `snr`, `cost`, `flip_prob`, `fidelity`, `p_right`, `g2`, `stark_a`, `stark_b`, `kerr_a`, `kerr_b`, `chi_ab`, `resonant_terms` |
| method | `eig`, `td` (time-domain fit), `analytic`, `linresp`, `sym` (symbolic), `tdsim` (time-dependent circuit simulation), `provider` (Felis), plus lane-specific names listed in each brief |
| model | `one_mode`, `two_mode`, `circuit` |
| tags | `a{alpha:.2f}`, `nth{n_th:g}`, `ez{eps_z/g2:.3g}g2`, `T{T:.1f}us`, `well{p|m}`, `p{pulse_name}` |

---

## 7. `src/convergence.py`

```python
def sweep(fn, axis, values, fixed) -> list[dict]:
    """rows = [{axis: v, **fixed, **fn(**fixed, **{axis: v})} for v in values]; fn returns a dict of floats."""
def converged_at(rows, key, var, tol):
    """Moved VERBATIM from tasks/task_1_2.py (which now imports it from here)."""
def convergence_block(sweeps: dict, key: str, rel_tol: float, chosen: dict) -> dict:
    """sweeps = {'Na': (fixed_dict, rows), 'Nb': (fixed_dict, rows)}; returns the §6.2 'convergence' dict."""
```

---

## 8. `src/spectral.py`

**Vectorization:** column-stacking, vec(AρB) = (Bᵀ ⊗ A) vec(ρ). The composite index is i = n_a·Nb + n_b (dynamiqs tensor order, memory first). The vector index is k = i + D·j for ρ_ij, with D = Na·Nb.

```python
def to_sparse(op) -> scipy.sparse.csr_matrix                 # QArray/ndarray -> CSR (complex128)
def liouvillian(H, jumps) -> scipy.sparse.csc_matrix          # D^2 x D^2
def vec(rho) -> np.ndarray ; def unvec(v, D) -> np.ndarray
def sector_indices(Na, Nb, parity) -> np.ndarray              # k with (n_a(i) - n_a(j)) % 2 == parity
def deflated(L, D, eta=1.0) -> csc                            # L + eta |1>><<1|  (moves 0 -> eta*D)
def diagnostics(L, lam, v, Na, Nb, w=None) -> dict            # rel_residual, edge_weight, cond_est
def gamma_x(H, jumps, Na, Nb, k=2) -> dict:
    """Smallest-|lambda| eigenvalue of the ODD block via shift-invert at sigma=0 (requires kappa_a > 0).
    Returns {'gamma_x': -Re(lam1), 'lams': [...], 'rel_residual', 'edge_weight', 'cond_est', 'wall_s',
             'sector': 'odd', 'dim': ...}. Raises ValueError if kappa_a == 0 (odd block singular)."""
def low_spectrum(H, jumps, Na, Nb, k=4, sector="even") -> dict:
    """sector in {'even', 'odd', 'full_deflated'}; 'full_deflated' is REQUIRED when eps_z or eps_x != 0 (no Z2).
    Returns sorted {'rates': [-Re lam ...], 'lams': [...], diagnostics...}."""
def left_eigvec_operator(H, jumps, Na, Nb, sector="odd") -> np.ndarray   # D x D matrix of the left eigvec (committor)
```
For the one-mode model, use `Nb = 1` and the same functions.

**Acceptance for a reported eigenvalue:**
- `rel_residual = ||Lv − λv|| / (|λ|·||v||) < 1e-4`.
- `edge_weight` (the fraction of ||v||² on the top 2 memory levels or the top buffer level) `< 1e-6`.
- Stable across two truncations, recorded in `convergence`.

---

## 9. `src/linresp.py`

Linearize about the well ±α, with b ≈ 0 and κ_a neglected. For the state x = (δa, b) ∈ ℂ², and well = +1 or −1:

```
dx/dt = M x + u ε(t),   M = [[0, -2i·s·g2·α], [-2i·s·g2·α, -κ_b/2]],   u = [-i, 0],   s = well
characteristic: λ² + (κ_b/2) λ + 4 g2² α² = 0
```
```python
def system(g2, kappa_b, alpha, well=+1) -> (M, u)
def poles(g2, kappa_b, alpha) -> np.ndarray                       # nominal: -4.08 ± 19.7i per us
def ringing(g2, kappa_b, alpha) -> dict    # {'freq_MHz': 3.14, 'decay_per_us': 4.08, 'Q': 2.46, 't_settle_5pct_us': 0.73, 't_settle_1pct_us': 1.13}
def dc_gain(g2, alpha) -> float           # b_ss / eps = -1/(2 g2 alpha) for well=+1
def response(eps_t, t, g2, kappa_b, alpha, well=+1) -> (da_t, b_t)  # exact matrix-exponential stepping, piecewise-constant eps
def response_matrices(T, n_bins, n_samples, g2, kappa_b, alpha) -> (R_b, R_a)
    # Δb(t_k) = (R_b ε)_k with Δb = b(+α) − b(−α); R_a maps to δa of the +α well
def optimal_pulse(R_b, R_a=None, energy=1.0) -> (eps_bins, gain)
    # R_a None: top right singular vector of R_b (max ||R_b ε||² at fixed ||ε||²)
    # R_a given: top generalized eigenvector of (R_bᴴR_b, R_aᴴR_a + δI) (max signal per unit leakage proxy)
```

---

## 10. `src/pulses.py` and `src/circuit.py`

```python
# src/pulses.py (L4c). All return (bin_edges_us, values_rad_per_us) for dq.pwc and src.linresp.
def square(T, amp, n_bins) ; def ramp(T, amp, tau, n_bins, kind="cos"|"lin") ; def clear(T, kick_amp, kick_t, hold_amp, n_bins)
def from_bins(values, T) ; def energy(edges, values) -> float           # ∫ε² dt
def snr(t, delta_b, kappa_b) -> float                                   # κ_b ∫|Δ⟨b⟩|² dt  (ideal mode-matched heterodyne)
def leakage_proxy(t, da) -> float                                       # ∫|δa|² dt

# src/circuit.py (L5)
def sin_phi_terms(phi_a, phi_b, max_order) -> list[dict]
    # EXACT normal-ordered coefficients: e^{iφ̂} = e^{-(φa²+φb²)/2} e^{iφa a†} e^{iφa a} e^{iφb b†} e^{iφb b};
    # sin φ̂ = Σ_{odd p+q+r+s} c_pqrs a†^p a^q b†^r b^s with c = e^{-Φ/2} i^{p+q+r+s-1} φa^{p+q} φb^{r+s} / (p! q! r! s!)
def term_frequency(term, w_a, w_b) -> float                              # frame rotation frequency of a†^p a^q b†^r b^s
def resonant_terms(terms, w_a, w_b, w_p, tol) -> list[dict]
def g2_from_circuit(EJ, eps_p, phi_a, phi_b) -> float                    # -(1/2) EJ eps_p phi_a^2 phi_b e^{-Φ/2}
```

---

## 11. Claim syntax and `tools/check_claims.py`

In `TECHNICAL.md` and `README.md`, every reported number is tagged inline with a backticked token:
```
`rec:<id>=<displayed value>`            compares record["value"]
`rec:<id>#<dotted.path>=<displayed>`    compares a nested field, e.g. #numerics.rel_residual or #cross_check.0.rel_diff
```
Example table cell: `` 0.5135 /µs `rec:t2_2.gamma_z.td.two_mode.a2.10=0.5135` ``.

The checker:
1. Finds every token in the file. A row containing the word `illustrative` only produces warnings.
2. Loads `results/records/<id>.json`. A missing record fails.
3. Rounds the record value to the number of **significant figures** in the displayed string. A mismatch fails.
4. Requires `convergence.converged == true` (or a `null` convergence with a `notes` justification).
5. Requires at least one `cross_check` entry with `agree == true`.
6. Requires `provenance.dirty == false`.
7. Prints a table, and exits 0 only if nothing failed.

`python -m tools.check_claims [--files TECHNICAL.md README.md] [--strict]`

---

## 12. `tools/runq.py`

A stdlib-only, file-based job queue. The default directory is `results/logs/runq/` (git-ignored), overridable with the `DUQ_RUNQ_DIR` environment variable.
```
python -m tools.runq submit --name <job> --ram-gb <float> [--cwd <path>] -- <command ...>
python -m tools.runq worker [--max-jobs 3] [--max-ram-gb 11]      # big job = ram-gb > 3: one at a time
python -m tools.runq status                                         # table: pending/running/done/failed, wall time, log path
```
- Each job is stored as `<dir>/jobs/<timestamp>_<name>.json`, with its log at `<dir>/logs/<name>.log`.
- The worker sets `XLA_FLAGS` (two threads) for every job, and records the exit code and wall time.
- A failed job is never retried automatically.

---

## 13. Lab data contract

`tools/export_lab_data.py` (owned by L6) reads `results/index.json`, `results/records/` and `results/arrays/`. It writes `site/src/data/live/*.json`, which is **bundled at build time**, never fetched. That is why the single-file build works from `file://`. The mock files in `site/src/data/mock/` use the same shapes.

| File | Shape |
|---|---|
| `records.json` | `[record, ...]`: every v2 record (from `results/index.json`) |
| `inflation.json` | `{t_us[], na[], nb[], top2_a[], top_b[], effective:{t_us[], na[]}, wigner:{x[], y[], frames:[{t_us, w[][]}]}, record_ids[]}` |
| `errors.json` | `{gamma_x:{one_mode:[{alpha2, value, unc, id}], two_mode:[...], td:[...], analytic:{alpha2[], ch1[], ch2[], total[]}, thermal:{"<nth>":[...]}, local_slope:{alpha2[], one_mode[], two_mode[]}}, gamma_z:{td:[...], eig:[...], pred:{alpha2[], value[]}}}` |
| `readout.json` | `{alpha, linresp:{freq_MHz, Q, t5, t1}, signals:{t_us[], b_plus_re[], b_plus_im[], b_minus_re[], b_minus_im[]}, tradeoff:[{eps_over_g2, snr_T1us, gamma_x_rel, id}], pulses:{"<name>":{t_us[], eps[], snr, cost, id}}}` |
| `verify.json` | `{generated_at, tests:{passed, failed, skipped}, convergence:[{id, axis, values[], results[], tol, converged}], cross_checks:[{id, method, rel_diff, tol, agree}]}` |

Wigner frames come from `results/arrays/lab.inflation_wigner.npz` (written by `tasks/task_lab_frames.py`, lane L3). They are downsampled to at most 81×81 and rounded to 4 decimals. The total bundle must stay under 8 MB.

---

## 14. Status files

Each lane keeps `docs/plan/status/<slug>.md`, copied from `status/_TEMPLATE.md`, and updates it at **every** milestone (started, tests written, gate passed or failed, blocked, done). It is the only channel to Harshit, Claude and the integrator. Write a `DECISION NEEDED` block instead of guessing on anything physics-relevant or cross-lane.

---

## 15. Tests

- `pytest.ini` (L0-core) defines the marker `slow`, sets `testpaths = tests`, and enables `-ra`.
- Each lane writes `tests/test_<lane_slug_underscored>.py` **before** its implementation (TDD). Analytic predictions become tests.
- Fast tests (`not slow`) use small truncations, so that the **total** stays under 2 min.
- `tests/conftest.py` (L0-core) imports `src.config` first, so that double precision is set.
