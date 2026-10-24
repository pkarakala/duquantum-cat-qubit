# Brief `l1-spectral`: Sparse Liouvillian, Z2 sectors, shift-invert eigen-solver, cost profile

> **Paste into a new Cursor agent (worktree mode):** "You are lane `l1-spectral`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/03-l1-spectral.md`, then execute this brief exactly. Keep `docs/plan/status/l1-spectral.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `l1-spectral` | `std/l1-spectral` (from `standard-track`) | `l0-core` | strongest reasoning model available (max thinking) | 2.5 h | Phase 1, done by **9:15 PM Sat Oct 24** (gate G1 is 9:45 PM) |

## 1. Goal and why
Build `src/spectral.py`: an exact sparse Lindblad superoperator, its memory-parity (Z2) blocks, and a shift-invert eigen-solver that returns Γ_X = −Re λ₁ of the **odd** block with acceptance diagnostics. The prompt says Γ_X hits a "numerical wall" in time domain above α ≈ 1.4; the spectral gap gets past it (Γ_X(2.1) ≈ 4e-7 /µs, i.e. seconds). L2b (Γ_X curves), L4b (trade-off) and the Lab all call this module, so correctness gates matter more than speed. Second deliverable: `tasks/task_spectral_profile.py`, a measured cost/RAM profile on this laptop that sets `NA_EIG_MAX, NB_EIG_MAX` (CONTRACT §4). Without the Z2 split, 32×12 costs ~30 min; with it ~4 min (RESEARCH §9).

## 2. Read first
- `docs/plan/CONTRACT.md` §2 (env, quick vs production), §6 (records, ID scheme §6.3), **§8 (your interface, frozen)**, §14 (status files).
- `docs/plan/RESEARCH.md` §4.2 (sectors, code-space rates), §5 (Γ_X convention, anchor table), §9 (vectorization, cost model, deflation, acceptance, speed levers).
- Code style: `src/config.py`, `src/model.py`, `tasks/task_1_2.py` (short docstrings, `argparse` main, `from src import config as C` first, figures via `src.plotting.save`, numbers via `src.results`).

## 3. Allowlist (touch nothing else)
- `src/spectral.py`, `tasks/task_spectral_profile.py`, `tests/test_l1_spectral.py` (CONTRACT §1).
- Your status file `docs/plan/status/l1-spectral.md` (copy of `docs/plan/status/_TEMPLATE.md`).
- Your production outputs only: `results/records/t2_1.wall_s.*.json`, `results/arrays/t2_1.wall_s.*.npz`, `figures/task_2_1_spectral_cost.png`.
- Do **not** edit `src/config.py` (the integrator applies your `NA_EIG_MAX/NB_EIG_MAX`), `src/model.py`, `requirements.txt`, CONTRACT/RESEARCH, or any other lane's file.

## 4. Interfaces you implement / rely on
**Rely on (from l0-core):** `src.model.one_mode(N, kappa_2, alpha, kappa_a=0.0, n_th=0.0, ...) -> (H, jumps, a)`, `src.model.two_mode(Na, Nb, g2, eps_d, kappa_b, kappa_a, n_th=0.0, ...) -> (H, jumps, (a, b))`, `src.results.record(...)`, `save_arrays(id, quick=False, **arrays)`, `std_params(alpha=...)`, `src.plotting.save(fig, name, quick=False)`. Constants (rad/µs): `C.G2=4.79411, C.KAPPA_B=16.33628, C.KAPPA_A=0.0584336, C.KAPPA_2=5.6276`; two-mode drive `eps_d = alpha**2 * C.G2`.

**Implement exactly (CONTRACT §8; extra dict keys allowed, signatures frozen):**
- Vectorization: column stacking, `vec(AρB) = (Bᵀ⊗A) vec(ρ)`. Composite index `i = n_a*Nb + n_b` (dynamiqs order, memory first); vector index `k = i + D*j` for ρ_ij; `D = Na*Nb`. One-mode: `Nb = 1`.
- `to_sparse(op) -> csr_matrix (complex128)`: QArray via `op.to_numpy()` (fallback `np.asarray(op)`), ndarray or sparse. Raise `ValueError` on a batched op (ndim > 2).
- `liouvillian(H, jumps) -> csc` (D²×D²): `L = −i(I⊗H − Hᵀ⊗I) + Σ_J [J*⊗J − ½ I⊗J†J − ½ (J†J)ᵀ⊗I]` with `scipy.sparse.kron(..., format="csc")`; `sum_duplicates()`, `eliminate_zeros()`. Never densify L (`dq.slindbladian(...).to_numpy()` is dense, ~348 GB at 32×12).
- `vec(rho) = np.asarray(rho).reshape(-1, order="F")`; `unvec(v, D) = v.reshape(D, D, order="F")`.
- `sector_indices(Na, Nb, parity)`: sorted `k` with `(n_a(i) − n_a(j)) % 2 == parity`, `n_a(i) = i // Nb`, `i = k % D`, `j = k // D`. parity 0 = even, 1 = odd. For even Na, `len(odd) == D²//2`.
- `deflated(L, D, eta=1.0) = L + eta |vec(I)⟩⟨vec(I)|` (D² nonzeros at k = i(D+1)). Moves the 0 eigenvalue to `eta*D`; traceless modes unchanged. vec(I) lies in the even sector.
- `diagnostics(L, lam, v, Na, Nb, w=None) -> {'rel_residual', 'edge_weight', 'cond_est'}`. Always in the **full** D² space with the **undeflated** L: callers embed block vectors (zeros outside the sector; L is block diagonal, so the residual is identical).
  - `rel_residual = ‖Lv − λv‖ / (|λ|·‖v‖)`.
  - `edge_weight`: `V = unvec(v, D)`; `edge(i) = n_a(i) >= Na−2 or (Nb > 1 and n_b(i) == Nb−1)`; fraction of `Σ|V_ij|²` on entries with `edge(i) or edge(j)`. (The buffer criterion is off for Nb = 1, else every index would be "edge".)
  - `cond_est = ‖w‖·‖v‖ / |⟨w|v⟩|` (≥ 1) when `w` is given, else `None`.
- `gamma_x(H, jumps, Na, Nb, k=2) -> dict`: odd block `A = L[odd][:, odd]`, shift-invert at σ = 0: `eigs(A, k, sigma=0, which="LM", tol=1e-12, OPinv=op)` where `op` wraps **one** `lu = splu(A, permc_spec="MMD_AT_PLUS_A")`. Left vectors reuse the same LU: `eigs(A.conj().T.tocsc(), k, sigma=0, OPinv=LinearOperator(matvec=lambda x: lu.solve(x, trans="H")))`, matched to `conj(λ)` by nearest distance. λ₁ = smallest |λ|. Returns `{'gamma_x': −Re λ₁, 'lams': [sorted by |λ|], 'rel_residual', 'edge_weight', 'cond_est', 'wall_s', 'build_s', 'lu_s', 'eigs_s', 'lu_nnz', 'sector': 'odd', 'dim': len(odd), 'sigma': 0.0, 'k': k, 'numerics': {rel_residual, edge_weight, cond_est, sector, sigma, k}}` (the `numerics` dict is ready for `record()`).
  - **Guard:** raise `ValueError("odd block singular: kappa_a == 0 ...")` unless some jump J with ‖J‖_F > 1e-14 satisfies `‖J − c·a_full‖_F ≤ 1e-10‖J‖_F` with `c = ⟨a_full, J⟩/⟨a_full, a_full⟩`, where `a_full = kron(destroy(Na), I_Nb)`. Zero-norm jumps count as absent (the pre-L0 `two_mode` appended `sqrt(0)·a`).
- `low_spectrum(H, jumps, Na, Nb, k=4, sector="even") -> dict`: `'odd'` = odd block, σ = 0, same guard; `'even'` = even block of `deflated(L, D, eta)` (0 removed, so σ = 0 is safe); `'full_deflated'` = whole deflated L, σ = 0 (REQUIRED by callers when eps_z or eps_x ≠ 0). Drop any eigenvalue within 1e-6·ηD of ηD. Return `{'rates': sorted ascending −Re λ, 'lams', 'rel_residual': [...], 'edge_weight': [...], 'cond_est': [...], 'sector', 'sigma': 0.0, 'k', 'dim', 'wall_s', 'deflated_eta': eta or None}`.
- `left_eigvec_operator(H, jumps, Na, Nb, sector="odd") -> np.ndarray (D×D)`: left eigenvector of the slowest odd mode, `W = unvec(w)` with zeros outside the sector, so that `⟨⟨w|ρ⟩⟩ = Tr(W†ρ)` decays as e^{λ₁t}. Normalize ‖W‖_F = 1; if |Im λ₁| < 1e-10|λ₁| rotate phase by θ = ½·arg Tr(W W) so W is Hermitian; fix sign so `Re Tr(W (a+a†)) > 0` (positive at the +α well). Other sectors: `NotImplementedError` (deflation changes left vectors).

## 5. Tests to write FIRST (TDD)
File `tests/test_l1_spectral.py`. Helpers: `two(Na, Nb, alpha, kappa_a=C.KAPPA_A)` → `two_mode(Na, Nb, C.G2, alpha**2*C.G2, C.KAPPA_B, kappa_a)`; `one(N, alpha, kappa_a=C.KAPPA_A)` → `one_mode(N, C.KAPPA_2, alpha, kappa_a=kappa_a)`. Spectrum matching: `scipy.optimize.linear_sum_assignment` on `|λ_i − μ_j|`. Fast tests (unmarked) must total ≤ 40 s.
1. `test_vec_kron_identity`: random complex 5×5 A, B, ρ (seed 0): `‖vec(A@ρ@B) − kron(B.T, A)@vec(ρ)‖ < 1e-12`; `unvec(vec(ρ), 5) == ρ` exactly.
2. `test_sector_indices_partition`: Na=4, Nb=2 and Na=5, Nb=1: even ∪ odd = arange(D²), disjoint, sorted; for Na=4 `len(odd) == D²//2 == 32`. Tensor order: nonzeros (i, i′) of `to_sparse(a)` from `two(4, 2, 1.0)` satisfy `i′//Nb == i//Nb + 1` and `i′%Nb == i%Nb`.
3. `test_liouvillian_matches_mesolve`: two-mode `two(6, 3, 1.0)`, ρ0 = `dq.todm(dq.tensor(dq.coherent(6, 0.8), dq.fock(3, 0)))` (populates both sectors), and one-mode `one(8, 1.0)`, ρ0 = `dq.todm(dq.coherent(8, 0.8))`. `unvec(scipy.linalg.expm(0.3*L.toarray()) @ vec(ρ0), D)` vs `dq.mesolve(H, jumps, ρ0, [0, 0.3], method=dq.method.Tsit5(rtol=1e-10, atol=1e-12)).final_state`: max abs diff `< 1e-8`; trace = 1 to 1e-12.
4. `test_trace_preservation`: for `one(8, 1.0)`, `two(6, 3, 1.0)` and `two(6, 3, 1.0)` with `n_th=0.05`: `max|L^H vec(I)| ≤ 1e-12·max(1, max|L|)`.
5. `test_sector_union_equals_full_spectrum`: `two(6, 3, 1.0)` (D² = 324). `L[even][:, odd].nnz == 0 == L[odd][:, even].nnz`; dense eigenvalues of the full L vs the union of even-block and odd-block eigenvalues: same count, max matched |Δλ| ≤ 1e-9·max(1, max|λ|).
6. `test_deflation_moves_zero`: `one(8, 1.0)`, D = 8: dense eigvals of `deflated(L, 8)` contain 8.0 (±1e-9); none has |μ| < 1e-6; after removing (0 ↔ 8.0) the rest match L's to 1e-9 relative.
7. `test_diagnostics_edge_weight_unit`: Na=4, Nb=3, single-entry V at (i, j) = (3·3+0, 0) → edge_weight == 1.0; at (0, 1·3+0) → 0.0; at n_b = 2 → 1.0. Nb=1, N=6: entry (0, 1) → 0.0, entry (4, 0) → 1.0. `cond_est(v, w=v) == 1` to 1e-12.
8. `test_odd_block_requires_kappa_a`: `pytest.raises(ValueError, match="kappa_a")` for `gamma_x` on `one(8, 1.0, kappa_a=0.0)` and `two(6, 3, 1.0, kappa_a=0.0)`, for `low_spectrum(..., sector="odd")`, and for a jump list containing `0*a`.
9. `test_code_space_rates_alpha1`: `one(40, 1.0)`. `gamma_x`: `|γ/2.2819e-3 − 1| < 0.01`, `rel_residual < 1e-4`, `edge_weight < 1e-6`, `1 ≤ cond_est < 1e6`, `dim == 800`. `low_spectrum(sector="odd", k=2)`: `rates[0]` = γ to 1e-6 rel; `rates[1]` ≈ **0.1190** within 2% (Y_L). `low_spectrum(sector="even", k=2)`: `rates[0]` ≈ **0.1212** within 2% (X_L). Analytic (RESEARCH §4.2): with `x = 2α²`, λ_X = 2κ_aα²·coth x = 0.12123, λ_Y = κ_aα²(coth x + 1) = 0.11905; assert `odd.rates[1] + odd.rates[0]` = `even.rates[0]` within 2% (**Y_L decays at Γ_Z − Γ_X**, not +).
10. `test_full_deflated_contains_both_sectors`: `one(40, 1.0)`, `low_spectrum(sector="full_deflated", k=4)`: `rates[:3]` equal [odd γ, odd rates[1], even rates[0]] to 1e-6 rel.
11. `test_left_eigvec_operator`: `one(40, 1.0)`: shape (40, 40); entries in the even sector exactly 0; `‖W − W†‖_F < 1e-8`; `‖L^H vec(W) − conj(λ₁)vec(W)‖/|λ₁| < 1e-6`; with ρ± = |±1.0⟩⟨±1.0|: `Tr(Wρ+) > 0` and `Tr(Wρ−) = −Tr(Wρ+)` to 1e-8 rel.

Slow (`@pytest.mark.slow`), anchors from an earlier scipy run, **reproduce, don't trust** (RESEARCH §5):
12. `test_anchor_two_mode` (parametrized): `(20, 6, 1.0, 2.3007e-3, 0.005)`, `(20, 6, 1.4, 1.2020e-4, 0.005)`, `(28, 8, 1.4, 1.2021e-4, 0.02)`, `(28, 8, 2.1, 3.8831e-7, 0.02)`; also `rel_residual < 1e-4` and `edge_weight < 1e-6`.
13. `test_anchor_one_mode_a2_1`: `one(40, 2.1)` → 1.1699e-7 within 2% (cheap, but floor-sensitive).
14. `test_truncation_trap_flagged`: `two(20, 6, 2.1)` → γ within 5% of **7.6070e-6** AND `edge_weight > 1e-6`; `two(28, 8, 2.1)` → `edge_weight < 1e-6` and γ₂₈/γ₂₀ < 0.1.

On any anchor mismatch: record both values, then check vectorization (test 3), sector indexing (tests 2, 5) and units (rad/µs, `eps_d = α²g₂`, κ_a jump `sqrt(κ_a)·a`) **before** touching a test; then DECISION NEEDED (§11).

## 6. Method, step by step
1. Wait until `l0-core` is merged into `standard-track`; branch `std/l1-spectral`; copy the status template; status "started".
2. Write all tests in §5; run them; confirm they fail on import; commit (`l1: tests first`); status "tests written".
3. Implement in order: `to_sparse`, `vec/unvec`, `liouvillian`, `sector_indices`, `deflated`, `diagnostics`, private `_block(L, idx)` (`L.tocsr()[idx][:, idx].tocsc()`), private `_shift_invert(A, k, sigma, left, permc)` (one `splu`, both `trans="N"` and `trans="H"`; `lu.solve(np.ascontiguousarray(x, complex).ravel())`; on `ArpackNoConvergence` retry with `ncv=max(2k+1, 40)`, `maxiter=10_000`), private `_require_memory_loss(jumps, Na, Nb)`, then `gamma_x`, `low_spectrum`, `left_eigvec_operator`. Time `build_s`, `lu_s`, `eigs_s` with `time.perf_counter`; `lu_nnz = lu.L.nnz + lu.U.nnz`.
4. Fast tests green, then `-m slow`. Put the anchor table (anchor, measured, rel diff, rel_residual, edge_weight) in the status file. Status "gate: anchors".
5. Measure LU fill of `deflated` vs the plain even block at `two(20, 6, 1.0)`; if `lu_nnz` grows > 2×, write a DECISION NEEDED (sparse alternative: `L + η|vec(|0⟩⟨0|)⟩⟨vec(I)|`, D nonzeros, moves 0 → η) since L2b/L4b use `full_deflated`.
6. Write `tasks/task_spectral_profile.py` (CLI in §9). The parent runs each case in a **fresh child process** (`subprocess.Popen([sys.executable, "-m", "tasks.task_spectral_profile", "--single", "28x8", "--sector", "odd", ...])`) with `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=2` and `XLA_FLAGS` set; polls child RSS with `psutil` every 0.5 s; kills it at **> 600 s or > 6 GB** (status `timeout`/`ram`, no record; skip larger sizes along that axis). The child prints one line `RESULT {json}` with wall/LU/eigs times, `lu_nnz`, `dim`, `nnz(A)`, γ, diagnostics and `peak_rss_gb` (`psutil.Process().memory_info().peak_wset` on Windows, `resource.getrusage(...).ru_maxrss*1024` on Linux); the parent keeps max(child peak, polled peak).
7. Cases at **α = 2.1** (`eps_d = C.EPS_D`), odd block via `gamma_x`: 24×10, 28×8, 32×10, 40×8, 48×8 (`--extra` adds 32×12). Plus the **full unsplit L at 28×8**: `eigs(L, k=3, sigma=+1e-3, OPinv=splu(L − σI))`, take the smallest-|λ| mode whose eigenvector has > 99% of ‖v‖² on odd indices; it must agree with the odd-block γ within 1e-3 rel. Plus `--permc-compare`: 28×8 odd with `COLAMD` vs `MMD_AT_PLUS_A`; keep the faster as the default in `gamma_x` (one-line note in the status file).
8. Cost model check (RESEARCH §9): full L `t ≈ 113 s·(Na·Nb²/1792)³`, odd ≈ 1/8 time, 1/4 RAM. Expected: 24×10 (x = 2400): full 271 s / odd ≈ 34 s; 28×8 (1792): 113 / 14 s; 32×10 (3200): 643 / 80 s; 40×8 (2560): 330 / 41 s; 48×8 (3072): 569 / 71 s; 32×12 (4608): ~32 min / ~4 min. Report the fitted exponent p in `t ∝ (Na·Nb²)^p` (odd cases), the measured full/odd time and RAM ratios at 28×8, and the odd-block dims (28×8: 25088; 24×10: 28800; 32×10 and 40×8: 51200; 48×8: 73728).
9. Quick run, commit code (clean tree), production run (est. 6 to 8 min total, so the lane runs it), commit outputs. If after 28×8 and 24×10 the extrapolated total exceeds 15 min, stop and move the rest to "Jobs to queue".
10. Recommend in the status file: `NA_EIG_MAX` = largest Na that finished at Nb = 8; `NB_EIG_MAX` = largest Nb that finished at Na ≥ 28 (both within 10 min and 6 GB), plus a "comfortable" pair (≤ 5 min, ≤ 3 GB, so it is not a "big LU" and can run beside 2 other heavy jobs).
11. Optional, only if ≥ 30 min remain before 9:15 PM: (a) real representation in the Hermitian basis (for i < j: (E_ij+E_ji)/√2, i(E_ij−E_ji)/√2, plus E_ii; sparse unitary U, assert `max|Im(U L U†)| < 1e-13·max|L|`; keeps sectors since (i,j),(j,i) share parity), as private `_gamma_x_real`; adopt only if ≥ 1.5× faster at 28×8 and γ equal to 1e-8 rel; (b) `pypardiso` (real-only) **only if already importable**; never `pip install`. Report the measured speedups.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **Records** (one per finished case; exact IDs, CONTRACT §6.3):
  - odd block: `t2_1.wall_s.eig.two_mode.a2.10.na24nb10`, `...na28nb8`, `...na32nb10`, `...na40nb8`, `...na48nb8` (optional `...na32nb12`), method `"liouvillian_eig_odd_sector"`.
  - full L: `t2_1.wall_s.eig_full.two_mode.a2.10.na28nb8` (lane-specific method token `eig_full`), method `"liouvillian_eig_full_small_sigma"`.
  - Fields: `task="2.1"`, `quantity="wall_s"`, `value` = total wall seconds, `units="s"`, `params=std_params(alpha=2.1)`, `script="tasks/task_spectral_profile.py"`, `truncation={"Na","Nb"}`, `convergence=None`, `numerics={rel_residual, edge_weight, cond_est, sector, sigma, k, dim, nnz, lu_nnz, build_s, lu_s, eigs_s, peak_rss_gb, gamma_x, blas_threads: 2}`, `cross_check=[{"method": "cost_model", "ref_id": None, "value": t_model, "rel_diff": |t−t_model|/t_model, "tol": 1.0, "agree": rel_diff <= 1.0}]` with `t_model` = full model (/8 for odd), `notes="cost profile; wall time is a property of this truncation, not a converged physics quantity, so convergence is null"`.
  - Do **not** write `gamma_x` records: L2b owns `t2_1.gamma_x.*`.
- **Arrays:** `results/arrays/t2_1.wall_s.eig.two_mode.a2.10.profile.npz` with `na, nb, sector (0 odd, 1 full), dim, nnz, lu_nnz, wall_s, lu_s, eigs_s, peak_rss_gb, gamma_x, rel_residual, edge_weight, status (0 ok, 1 timeout, 2 ram)`, including aborted cases.
- **Figure:** `figures/task_2_1_spectral_cost.png`: left, log-log wall_s vs Na·Nb² (odd markers, full marker, lines for 113 s·(x/1792)³ and /8); right, peak RSS vs Na·Nb².
- **Quick** (`--quick`, ≤ 2 min): α = 1.0, odd 12×4, 16×4, 20×6 and full 12×4; writes `results/quick/` and `figures/quick/` only.
- **Jobs to queue** (only if the production run exceeds 15 min, or for `--extra`): `python -m tools.runq submit --name l1_profile_extra --ram-gb 6 -- <DUQ_PY> -m tasks.task_spectral_profile --sizes 32x12 --no-full`.

## 8. Acceptance gates (ALL must pass before DONE)
1. All 11 fast tests pass in ≤ 40 s; full `-m "not slow"` suite still passes.
2. All 3 slow tests pass, or each failure has a DECISION NEEDED with both values and the checks from §5 done.
3. Every production odd-block γ: `rel_residual < 1e-4`, `edge_weight < 1e-6`, finite `cond_est`; the 20×6 α=2.1 trap is flagged by edge_weight.
4. Full-L 28×8 γ agrees with the odd block within 1e-3 rel; measured full/odd time ratio reported (expected ~8; explain if outside 4 to 16).
5. Records validate through `record()`, IDs exactly as §7, `provenance.dirty == false`, arrays and figure exist.
6. Status file has the anchor table, profile table, fitted exponent, permc choice, `NA_EIG_MAX/NB_EIG_MAX` recommendation.
7. `git diff --name-only standard-track...HEAD` lists only §3 paths.

## 9. Commands
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -c "import psutil, scipy; print(psutil.__version__, scipy.__version__)"
& $env:DUQ_PY -m pytest tests/test_l1_spectral.py -m "not slow" -q
& $env:DUQ_PY -m pytest tests/test_l1_spectral.py -m slow -q
& $env:DUQ_PY -m tasks.task_spectral_profile --quick
git add src/spectral.py tasks/task_spectral_profile.py tests/test_l1_spectral.py; git commit -m "l1: spectral solver + profile"
& $env:DUQ_PY -m tasks.task_spectral_profile                        # production, est. 6-8 min
& $env:DUQ_PY -m tasks.task_spectral_profile --permc-compare --no-full --sizes 28x8
git add results/records/t2_1.wall_s.* results/arrays/t2_1.wall_s.* figures/task_2_1_spectral_cost.png docs/plan/status/l1-spectral.md; git commit -m "l1: cost profile outputs"
```
Profile CLI: `--quick`, `--sizes 24x10,28x8,32x10,40x8,48x8` (default), `--extra`, `--alpha 2.1`, `--no-full`, `--permc-compare`, `--max-wall 600`, `--max-rss-gb 6`, internal `--single NAxNB --sector odd|full --permc SPEC`. Before production, check (status files / `python -m tools.runq status`) that no other > 3 GB LU is running.

## 10. Out of scope / do not
- No Γ_X vs α sweeps, convergence blocks, time-domain fits or channel analysis (L2b). No readout/ε_Z physics (L4a/L4b).
- No edits to `src/config.py`, `src/model.py`, CONTRACT, or public signatures; no new public kwargs without a DECISION NEEDED.
- No dense Liouvillian above D² = 2000 except in tests; no GPU; no `pip install`; no notebook.
- Do not loosen a test tolerance or "fix" an anchor to match your output.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Write in the status file:
```
### DECISION NEEDED (l1-spectral, <EDT time>)
Question: <one sentence>
Evidence: anchor <value> vs measured <value> (rel diff <x>); checks done: tests 2/3/5, units, eps_d
Options: A) ... B) ...
Recommendation: <A/B, why>
Blocking: <yes/no; what I continue meanwhile>
```
- **Anchor mismatch** after all checks: keep the test at the anchor (xfail with reason only after the DECISION is written), continue with the profile.
- **28×8 α=2.1 edge_weight ≥ 1e-6**: report the value and the 32×8 / 28×10 values; L2b needs this.
- **l0-core not merged by 7:15 PM**: write tests + `spectral.py` against the current `src/model.py` (positional args compatible; build states with `dq.tensor`), note it, rebase when L0 lands.
- **`psutil` missing**: DECISION NEEDED (setup owns `requirements.txt`); fallback Windows `ctypes` `GetProcessMemoryInfo().PeakWorkingSetSize`.
- **ARPACK no convergence**: retry as in §6.3, then `k=3`; report.
- **Cut line (8:45 PM):** must-have = `spectral.py` + fast tests + 20×6/28×8 anchors + odd 28×8 and 40×8 profile records. Drop in this order: optional levers, 48×8, 32×10, full-L comparison (queue it). Never cut the κ_a guard, residual/edge diagnostics or the trap test.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
Status file at DONE: state `DONE`, branch + final commit hash; test counts (fast/slow, wall); anchor table (anchor, measured, rel diff, rel_residual, edge_weight); profile table (Na×Nb, sector, dim, lu_nnz, wall_s, peak_rss_gb, γ, model time, status); fitted exponent p; full/odd time and RAM ratios at 28×8; full-vs-odd γ agreement; permc choice; deflation fill result; speed-lever results (or "not attempted"); `NA_EIG_MAX, NB_EIG_MAX` = `(.., ..)` plus comfortable pair, for the integrator to apply to `src/config.py`; jobs to queue (exact `runq submit` lines); open DECISIONS NEEDED; any deviation from this brief.

Judge questions for Harshit:
1. Why is Γ_X exactly the smallest-|λ| eigenvalue of the odd parity block, and what quantity becomes conserved (making that block singular) when κ_a = 0?
2. At 20×6 the solver returns 7.6e-6 at α = 2.1 with a tiny residual; how do you know it is a truncation artifact, and why is a relative residual meaningful when λ ~ 4e-7 while ‖L‖ is ~1e2 or larger?
3. Why does Y_L decay at Γ_Z − Γ_X rather than Γ_Z + Γ_X, and once ε_Z ≠ 0 breaks the Z2 symmetry, why must you deflate (or shift by a small positive σ) instead of shift-inverting the full L at σ = 0?
