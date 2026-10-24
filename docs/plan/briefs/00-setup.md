# Brief `setup`: Environment setup and intro reproduction (gate G0-env)

> **Paste into a new Cursor agent (local mode in the MAIN checkout, NOT worktree mode):** "You are lane `setup`. Read `AGENTS.md`, `docs/plan/CONTRACT.md`, `docs/plan/RESEARCH.md` and `docs/plan/briefs/00-setup.md`, then execute this brief exactly. Keep `docs/plan/status/setup.md` updated."

| Lane | Branch | Depends on (merged first) | Suggested Cursor model | Time cap | Phase / target finish (EDT) |
|---|---|---|---|---|---|
| `setup` | none: work directly on `standard-track` in the main checkout `D:\Brown University\duhack\duquantum-cat-qubit` (no worktree, no `std/setup` branch) | nothing (the planning package is already committed on `standard-track`) | fast | 45 min | Phase 0 / 6:15 PM Sat Oct 24 (gate G0-env, ahead of G0 at 6:45 PM) |

This lane may be run by Harshit by hand or by one agent. It is the **only** lane (besides the integrator) that commits on `standard-track` directly (CONTRACT §1); the AGENTS.md rule "never commit to standard-track" is waived for this lane only.

## 1. Goal and why
1. Create the **shared interpreter** `D:\duq-venv\Scripts\python.exe` that every worktree and lane uses (CONTRACT §2). Every lane is blocked until this works.
2. Prove the committed intro numbers reproduce on this second machine (they were produced elsewhere, Linux). A clean reproduction is itself a claim for the judges: same code, different OS and JAX build, same numbers to 1e-6.
3. Freeze the exact working versions into `requirements.txt`. These versions become the `provenance.dynamiqs/jax/python` fields of every v2 record (CONTRACT §6.2).
4. Record the facts the integrator needs: `gh` auth and `workflow` scope, repo permission, CPU/RAM, timings.

## 2. Read first
- `docs/plan/CONTRACT.md` §1 (your row: you own `requirements.txt`, pins only), §2 (environment and commands), §6.2 (provenance fields; never record hostname or username).
- `docs/plan/RESEARCH.md` §3 (Windows/JAX facts): native Windows x86_64 CPU JAX is **"experimental"** and may need the MSVC 2019 redistributable; jax >= 0.11 needs Python >= 3.12; the repo pins `jax==0.12.0.1` (released Oct 21) with `dynamiqs==0.3.7` (released Oct 15), a pairing upstream never tested; dynamiqs CI runs only on Ubuntu + Python 3.11; `OMP_NUM_THREADS` does **not** limit XLA.
- **Verified on this laptop (Oct 24): the 32-bit trap.** `uv --version` prints `uv 0.11.8 (... i686-pc-windows-msvc)`: the installed `uv` is the **32-bit** build (it lives in `...\Python38-32\Scripts\uv`), and `uv python find 3.12` resolves to `...\uv\python\cpython-3.12-windows-x86-none\python.exe`, a **32-bit** CPython. JAX/jaxlib publish **no 32-bit Windows wheels**, so a plain `-p 3.12` venv fails to install `jaxlib` (a resolver "no matching distribution / no wheels" error), and that failure is NOT a reason to fall back. A 64-bit CPython 3.12.13 is already installed by uv (`cpython-3.12.13-windows-x86_64-none`). Always pass the explicit 64-bit request `-p cpython-3.12-windows-x86_64-none` (Fallback 1: `-p cpython-3.11-windows-x86_64-none`) and check the venv is 64-bit before installing anything.
- `check_env.py`, `src/config.py` (its `__main__` block), `tasks/task_1_0.py`, `tasks/task_1_1.py`, `src/results.py` (`save` writes `results/<name>.json`), `src/plotting.py` (`save` writes `figures/<name>.png`).
- Committed references: `results/task_1_0.json`, `results/task_1_1.json` (commit `b88747b`).

## 3. Allowlist (touch nothing else)
- **Edit:** `requirements.txt` (pins and one comment line only).
- **Create:** `docs/plan/status/setup.md` (copy of `docs/plan/status/_TEMPLATE.md`).
- **Outside the repo (not committed):** `D:\duq-venv\`, scratch dir `$env:TEMP\duq-setup\` (comparison script, reference copies, freeze, logs), user environment variables `DUQ_PY` and `XLA_FLAGS`.
- The task scripts **overwrite** `results/task_1_0.json`, `results/task_1_0c_nominal.npy`, `results/task_1_1.json` and 7 PNGs in `figures/`. You must restore them byte-identical (`git checkout -- results figures`). Never commit them.
- Do not touch `src/`, `tasks/`, `tools/`, `.cursor/`, `.gitignore`, `notes/`, `docs/challenge_prompt_v4.md`, or any other lane file.

## 4. Interfaces you implement / rely on
**You implement (the environment contract, CONTRACT §2):**
```powershell
$env:DUQ_PY    = "D:\duq-venv\Scripts\python.exe"     # persisted as a USER env var
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
```
- `& $env:DUQ_PY -c "import dynamiqs, jax, jaxlib, numpy, scipy, matplotlib, pandas, pytest, sympy, optax, psutil"` must succeed.
- After `import src.config`, JAX must be in double precision (`dq.set_precision("double")` sets `jax_enable_x64`).

**You rely on (do not modify):**
- `check_env.py`: prints `JAX devices`, `dynamiqs version`, then `mesolve OK in <s>s, final <n> = <x> (expect ~4)`. The run is L = a² − 4 (α = 2, κ₂ = 1) from vacuum on N = 15, t ∈ [0, 3], so <n> → 4·tanh(4) ≈ 3.997.
- `python -m src.config` prints `kappa_2/2pi = 0.896 MHz (expect 0.896)`, `g2/kappa_b = 0.29, eps_d/kappa_b = 1.29`, `phase-flip time 1/(2 kappa_a alpha^2) = 1.94 us`. (κ₂ = 4g₂²/κ_b with g₂/2π = 0.763 MHz, κ_b/2π = 2.6 MHz.)
- `python -m tasks.task_1_0` (no args) writes `results/task_1_0.json`, `results/task_1_0c_nominal.npy` and figures `task_1_0a_photon_number`, `task_1_0a_wigner`, `task_1_0b_two_photon_loss`, `task_1_0c_kappa2_sweep`, `task_1_0c_wigner`.
- `python -m tasks.task_1_1` (defaults `--na 32 --nb 12`) reads `task_1_0c_nominal.npy` (so run 1_0 **first**), also runs the 24×6 starter, and writes `results/task_1_1.json`, figures `task_1_1_inflation`, `task_1_1_wigner`. Time grid: 301 points on [0, 3] µs (step 0.01 µs).

## 5. Tests to write FIRST (TDD)
There is no `tests/` directory yet (L0-core creates `pytest.ini` and `tests/`). Your test is a **comparison script written before any task run**, saved at `$env:TEMP\duq-setup\compare_intro.py` and pasted verbatim into the status file. It must contain exactly these functions and rules:
```python
"""Compare fresh intro outputs with the committed copies. Usage: python compare_intro.py <ref_dir> <new_dir>"""
import json, sys
from pathlib import Path

RULES = {  # file -> (default relative tol, {key prefix: (kind, tol)})
    "task_1_0.json": (1e-6, {"a.max_abs_error_vs_analytic": ("abs_lt", 1e-9),   # committed 9.72e-12
                             "b.rel_error": ("abs_lt", 1e-10),                   # committed 1.2e-14
                             "c.t90_us": ("abs", 1e-9), "c.alpha2": ("abs", 1e-12)}),
    "task_1_1.json": (1e-4, {"Na": ("abs", 0), "Nb": ("abs", 0), "settle_1pct_us": ("abs", 1e-9),
                             "t_peak_us": ("abs", 1e-9), "t_peak_nb_us": ("abs", 1e-9)}),
}

def leaves(d, prefix=""):
    """Yield (dotted_key, number) for every numeric leaf; list items get their index ('c.final_n.0')."""
    if isinstance(d, dict):
        for k, v in d.items(): yield from leaves(v, f"{prefix}{k}.")
    elif isinstance(d, list):
        for i, v in enumerate(d): yield from leaves(v, f"{prefix}{i}.")
    else:
        yield prefix[:-1], float(d)

def check(key, ref, new, default_rel, rules):
    """Return (ok, diff, rule). 'rel': |new-ref|/|ref| <= tol; 'abs': |new-ref| <= tol; 'abs_lt': |new| < tol."""
    kind, tol = next((r for k, r in rules.items() if key == k or key.startswith(k + ".")), ("rel", default_rel))
    if kind == "abs_lt": diff = abs(new); ok = diff < tol
    elif kind == "abs":  diff = abs(new - ref); ok = diff <= tol
    else:                diff = abs(new - ref) / max(abs(ref), 1e-300); ok = diff <= tol
    return ok, diff, f"{kind} {tol:g}"

def main(ref_dir, new_dir):
    fails = 0
    print("| file | key | committed | fresh | diff | rule | ok |\n|---|---|---|---|---|---|---|")
    for name, (rel, rules) in RULES.items():
        ref = dict(leaves(json.loads((Path(ref_dir) / name).read_text())))
        new = dict(leaves(json.loads((Path(new_dir) / name).read_text())))
        if set(ref) != set(new): print(f"KEY MISMATCH {name}: {set(ref) ^ set(new)}"); fails += 1
        for key in sorted(set(ref) & set(new)):
            ok, diff, rule = check(key, ref[key], new[key], rel, rules)
            fails += not ok
            print(f"| {name} | {key} | {ref[key]:.12g} | {new[key]:.12g} | {diff:.2e} | {rule} | {'yes' if ok else 'NO'} |")
    print("ALL MATCH" if fails == 0 else f"{fails} FAILURES"); return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
```
Self-test before running any task: `compare_intro.py ref ref` must print `ALL MATCH` (exit 0); then copy `ref` to `ref_bad`, change `peak_na` in `ref_bad\task_1_1.json` to `6.90` and confirm exit 1 with `peak_na ... NO`.

Key numbers this enforces (committed values): task_1_0 `a.max_abs_error_vs_analytic` 9.72e-12 (< 1e-9), `b.final_n_sim` 0.4998322686860546 (rel 1e-6), `c.final_n` [4.387166, 4.403969, 4.408144] (rel 1e-6), `c.t90_us` [0.61, 0.155, 0.04] (exact, grid values); task_1_1 at 32×12: `peak_na` 6.894411732563246, `steady_na` 4.402615556547587, `max_top_b` 1.6920820976e-4, `starter_max_top_b` 0.0462 (rel 1e-4), `settle_1pct_us` 1.07, `t_peak_us` 0.23 (exact, grid values).

## 6. Method, step by step
1. **Preflight (2 min).** In the main checkout: `git branch --show-current` must print `standard-track`. Snapshot `git status --porcelain` to `$T\status_before.txt` (`$T = "$env:TEMP\duq-setup"`). `git status --porcelain -- results figures` must be empty (else stop: DECISION NEEDED). Check `uv --version` (expect 0.11.x) and `gh --version`. Status file: create from `_TEMPLATE.md`, mark **started**.
2. **Write and self-test `compare_intro.py`** (section 5). Status: **tests written**.
3. **Attempt A, repo pins (Python 3.12).** Time it with `Measure-Command`.
   `uv venv D:\duq-venv -p 3.12` then `uv pip install --python D:\duq-venv\Scripts\python.exe -r requirements.txt pytest sympy optax psutil`.
4. **Verify the interpreter.** `& D:\duq-venv\Scripts\python.exe check_env.py` (final <n> ≈ 4, gate 3.9 to 4.1; devices list `CpuDevice`), `-m src.config` (must print `kappa_2/2pi = 0.896 MHz`), the import line from §4, and the x64 check `-c "import src.config, jax.numpy as jnp; assert jnp.zeros(1).dtype == jnp.float64; print('x64 OK')"`.
5. **If step 3 or 4 fails:**
   - `ImportError: DLL load failed` on `jaxlib`: it needs the Microsoft Visual C++ redistributable (2015-2022 x64 covers 2019). **Do not install system software yourself**; write DECISION NEEDED asking Harshit to install it, then retry step 4.
   - Otherwise **Fallback 1:** `uv venv D:\duq-venv -p 3.11 --clear`, then `uv pip install --python D:\duq-venv\Scripts\python.exe jax==0.10.2 jaxlib==0.10.2 dynamiqs==0.3.7 numpy scipy matplotlib pandas jupyter pytest sympy optax psutil`, then step 4.
   - Still failing: **Fallback 2, WSL Ubuntu.** In WSL, the same uv commands with a Linux path (`uv venv ~/duq-venv -p 3.12`, `uv pip install --python ~/duq-venv/bin/python -r requirements.txt pytest sympy optax psutil`, Fallback 1 pins if needed); `DUQ_PY` then points to the WSL venv and every lane runs its commands inside WSL. This changes every brief's commands: write DECISION NEEDED before telling anyone it is the plan.
   Log every attempt (command, error first line, minutes spent) in the status file.
6. **Persist the env vars** (new shells only; also set them in the current shell):
   `setx DUQ_PY "D:\duq-venv\Scripts\python.exe"` and, because `setx` may misread a value that starts with `--`, `[Environment]::SetEnvironmentVariable("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2", "User")`. Open a new PowerShell and confirm `$env:DUQ_PY` and `$env:XLA_FLAGS`.
7. **Copy references:** `Copy-Item results\task_1_0.json, results\task_1_1.json $T\ref\`.
8. **Run the reproductions, in order, timed** (expect task_1_0 ≈ 20 s, task_1_1 ≈ 1 min; both are below the 15-min production limit):
   `Measure-Command { & $env:DUQ_PY -m tasks.task_1_0 | Tee-Object $T\task_1_0.log }`, then the same for `tasks.task_1_1`. Copy the two fresh JSONs to `$T\new\`.
9. **Compare:** `& $env:DUQ_PY $T\compare_intro.py $T\ref $T\new | Tee-Object $T\compare.md`. Exit code must be 0. Paste the full table into the status file.
10. **Restore:** `git checkout -- results figures`; then `git status --porcelain -- results figures` must be empty and `git diff --quiet -- results figures` must exit 0.
11. **Pins:** `uv pip freeze --python $env:DUQ_PY > $T\freeze.txt`. Rewrite `requirements.txt`: keep line 1 (`# Versions used to produce every figure and number in this repo`), add one comment line naming the platform and Python, e.g. `# Verified 2026-10-24: Windows 11 x86_64 (native, CPU only), CPython 3.12.13, uv 0.11.8, shared venv D:\duq-venv`, then pin `==` every direct dependency with its installed version: `dynamiqs`, `jax` (keep `0.12.0.1` if it worked), `jaxlib`, `numpy`, `scipy`, `matplotlib`, `pandas`, `jupyter`, `pytest`, `sympy`, `optax`, `psutil`. No transitive packages (the full freeze goes in the status file). Verify: `uv pip install --python $env:DUQ_PY -r requirements.txt --dry-run` reports nothing to install or change, and `uv pip check --python $env:DUQ_PY` passes.
12. **GitHub and hardware facts:** `gh auth status` (logged in? token scopes list; is `workflow` present? It is needed to push `.github/workflows/*`. Never use `--show-token`); `gh repo view pkarakala/duquantum-cat-qubit --json viewerPermission` (expect `ADMIN` or `WRITE`); `Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors` and `[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)` (expect i7-9750H, 6/12, 15.9 GB). Record `python -c "import platform, os; print(platform.platform(), os.cpu_count())"`. Never record hostname or username.
13. **Status file to DONE** (section 12), then commit exactly two paths (step in §9). Do not push; the integrator/Harshit pushes.

## 7. Outputs (records, figures, arrays; quick vs production; jobs to queue)
- **Committed (2 files only):** `requirements.txt` (exact pins + platform comment), `docs/plan/status/setup.md`.
- **No v2 records, arrays or figures.** The intro JSONs are later wrapped into `t1_0.*` / `t1_1.*` records by lane `l0-tools` (`tools/wrap_intro_records.py`); this lane's comparison table is the evidence they cite.
- **Quick vs production:** not applicable. The two intro scripts are run in their committed (production) form, their outputs are compared, then discarded via `git checkout -- results figures`.
- **Jobs to queue:** none.
- **Not committed:** everything under `$env:TEMP\duq-setup\` (`compare_intro.py`, `ref\`, `new\`, `ref_bad\`, `freeze.txt`, `*.log`, `compare.md`, `status_before.txt`).

## 8. Acceptance gates (ALL must pass before DONE)
- [ ] `& $env:DUQ_PY -c "import sys; print(sys.executable)"` prints `D:\duq-venv\Scripts\python.exe` in a **new** PowerShell (env var persisted); `$env:XLA_FLAGS` is set there too.
- [ ] `check_env.py` runs; final <n> between 3.9 and 4.1.
- [ ] `-m src.config` prints `kappa_2/2pi = 0.896 MHz`; x64 check prints `x64 OK`; the §4 import line succeeds.
- [ ] `compare_intro.py` self-test passed (ref vs ref exit 0; ref vs ref_bad exit 1).
- [ ] `compare_intro.py $T\ref $T\new` exits 0 for **both** files (every numeric leaf within its rule).
- [ ] After restore, `git status --porcelain` equals `status_before.txt` plus only ` M requirements.txt` and `?? docs/plan/status/setup.md`.
- [ ] `uv pip install ... -r requirements.txt --dry-run` changes nothing; `uv pip check` passes.
- [ ] Commit on `standard-track` with `git show --stat HEAD` listing exactly `requirements.txt` and `docs/plan/status/setup.md`.
- [ ] Status file contains: versions, attempts log, timings, comparison table, the compare script, pins, `gh` facts, hardware.

**Gate G0-env = venv works + both reproductions match.** Report it as `G0-env: PASSED` or `G0-env: FAILED (<which item>)` at the top of the status file.

## 9. Commands
```powershell
cd "D:\Brown University\duhack\duquantum-cat-qubit"
$T = "$env:TEMP\duq-setup"; New-Item -ItemType Directory -Force $T, "$T\ref", "$T\new" | Out-Null
git branch --show-current; git status --porcelain | Set-Content -Encoding utf8 $T\status_before.txt
uv --version; gh --version
Measure-Command { uv venv D:\duq-venv -p 3.12 }
Measure-Command { uv pip install --python D:\duq-venv\Scripts\python.exe -r requirements.txt pytest sympy optax psutil }
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY check_env.py
& $env:DUQ_PY -m src.config
& $env:DUQ_PY -c "import src.config, jax.numpy as jnp; assert jnp.zeros(1).dtype == jnp.float64; print('x64 OK')"
setx DUQ_PY "D:\duq-venv\Scripts\python.exe"
[Environment]::SetEnvironmentVariable("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2", "User")
Copy-Item results\task_1_0.json, results\task_1_1.json "$T\ref\"
Measure-Command { & $env:DUQ_PY -m tasks.task_1_0 | Tee-Object "$T\task_1_0.log" }
Measure-Command { & $env:DUQ_PY -m tasks.task_1_1 | Tee-Object "$T\task_1_1.log" }
Copy-Item results\task_1_0.json, results\task_1_1.json "$T\new\"
& $env:DUQ_PY "$T\compare_intro.py" "$T\ref" "$T\new" | Tee-Object "$T\compare.md"; "exit=$LASTEXITCODE"
git checkout -- results figures; git status --porcelain -- results figures
uv pip freeze --python $env:DUQ_PY | Set-Content -Encoding utf8 "$T\freeze.txt"
uv pip install --python $env:DUQ_PY -r requirements.txt --dry-run; uv pip check --python $env:DUQ_PY
gh auth status; gh repo view pkarakala/duquantum-cat-qubit --json viewerPermission
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 1)
git add requirements.txt docs/plan/status/setup.md
git commit -m "[setup] Pin working environment and record intro reproduction (G0-env)" -m "Co-Authored-By: <the AI tool(s) used>"
git show --stat HEAD
```

## 10. Out of scope / do not
- Do not edit `src/`, `tasks/`, `check_env.py`, `.gitignore`, `.cursor/*` (the worktree setup scripts are not this lane's), or any committed result/figure.
- Do not "fix" a mismatch by editing code or re-committing intro JSONs; report it.
- No `pip install -e`, no conda, no second venv inside the repo (`.venv/` is for WSL/cloud only).
- Do not install system software (MSVC redistributable, WSL) without Harshit's explicit yes in chat.
- Do not create `std/setup`, do not push, do not use `git add .` / `git add -A`.
- Do not set up Felis/qiskit (lane `l8-felis` uses a separate venv and `requirements-felis.txt`).
- Do not record hostname, username, tokens or full `gh auth status` output with account emails.

## 11. If blocked (DECISION NEEDED wording + fallbacks + cut line)
Use this block in the status file:
```
### DECISION NEEDED (setup-<n>)
Question: <one line, e.g. "task_1_1 peak_na differs by 3e-4 rel on jax 0.12.0.1 / Windows; accept?">
Evidence: <command, error first line or comparison rows>
Options: A) <...>  B) <...>  C) <...>
Recommendation: <letter + one-line reason>
Blocking: <what waits on this>  | Not blocking: <what you continue with>
```
- **Fallback order:** A) repo pins on 3.12 → B) Python 3.11 + `jax==0.10.2 jaxlib==0.10.2 dynamiqs==0.3.7` → C) WSL Ubuntu with the same uv commands → D) cloud VM (Harshit decides; DECISION NEEDED only).
- **Mismatch above tolerance but rel < 1e-3:** do not retry blindly; note the versions, try the same comparison under the other fallback only if time remains, then DECISION NEEDED (Options: accept with the measured tolerance stated / switch pins / investigate). Larger mismatch or missing keys: G0-env FAILED, DECISION NEEDED.
- **Grid quantities** (`settle_1pct_us`, `t_peak_us`, `c.t90_us`) off by exactly one step (0.01 µs for 1_1): report it as such in the DECISION block; it means a threshold crossing moved, not a physics change.
- **Cut line (45 min):** if the venv works but a reproduction is still failing, commit the pins and the status file with `G0-env: FAILED (reproduction)` plus the DECISION block, because L0-core can still start on a working interpreter. If no interpreter works by 45 min, stop, commit only the status file with the attempts log, and escalate: every lane is blocked.

## 12. Hand-off (status-file contents at DONE + 3 hardest judge questions for Harshit's explain-back: QUESTIONS ONLY, Harshit answers himself)
`docs/plan/status/setup.md` at DONE must contain, in this order:
1. `State: DONE`, `G0-env: PASSED` (or FAILED + reason), finish time (EDT), minutes used.
2. **Interpreter:** path, Python version, which attempt worked (A/B/C), `jax`, `jaxlib`, `dynamiqs`, `numpy`, `scipy` versions, `platform.platform()`, `os.cpu_count()`.
3. **Attempts log:** command, outcome, minutes.
4. **Checks:** `check_env.py` output line (final <n>, mesolve time), `src.config` output (3 lines), `x64 OK`.
5. **Timings:** venv create, install, task_1_0 (≈ 20 s expected), task_1_1 (≈ 1 min expected), with XLA_FLAGS set.
6. **Comparison table** (the full `compare.md`) and the `compare_intro.py` source.
7. **Pins:** the final `requirements.txt` content, plus the full `uv pip freeze` in a collapsed block.
8. **GitHub:** logged in (yes/no), `workflow` scope present (yes/no; if no, the integrator must run `gh auth refresh -s workflow` before pushing `.github/workflows/`), `viewerPermission`.
9. **Hardware:** CPU name, cores/threads, RAM GB.
10. **Restore proof:** `git status --porcelain -- results figures` empty; commit hash.
11. Any DECISION NEEDED blocks (resolved or open).

Explain-back questions for Harshit (answer them yourself, out loud, without notes):
1. κ₂/2π comes out as 0.896 MHz: derive it from g₂ and κ_b, say where the 2π is applied in the code and why applying it twice would silently pass `check_env.py` but break every rate.
2. The committed numbers came from a Linux machine and you reproduced them on native Windows with a different JAX build: what does agreement to 1e-6 actually prove, what would it not prove (for example about truncation), and what size of disagreement would make you distrust the solver rather than the platform?
3. In Task 1.1 the buffer top-level population is 1.69e-4 at 32×12 but 4.6e-2 at the 24×6 starter truncation: what is this monitor measuring, why does it decide whether `peak_na` = 6.89 can be trusted, and why is the overshoot above α² = 4.41 physical rather than a truncation artifact?
