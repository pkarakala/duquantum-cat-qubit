# Status: lane `setup`

> **macOS adaptation.** This lane ran on macOS 14.5 / Apple M3 arm64, not the Windows laptop in the brief. Environment and process overrides come from the git-ignored `.orchestrator/RUNBOOK.md`. There is no persisted user env var and no Cursor restart: every agent exports `DUQ_PY` and `XLA_FLAGS` in each shell (RUNBOOK §2). Paths below write the main checkout as `$MAIN` because the absolute path contains the username.

| Field | Value |
|---|---|
| State | `DONE` |
| G0-env | **PASSED** (venv works; both intro reproductions match, 33/33 numeric leaves within rule) |
| Branch | `standard-track` (main checkout; this lane has no `std/` branch, per brief) |
| Agent / model | Cursor agent |
| Started (EDT) | 18:29 Sat Oct 24 2026 |
| Finished (EDT) | 18:36 Sat Oct 24 2026 (about 7 minutes of the 45-minute cap) |
| Venv ready marker | `$MAIN/.venv/.duq-ready` written at **18:31:23 EDT** |
| Last commit | the commit that adds this file (`[setup] Pin working environment and record intro reproduction (G0-env)`, parent `27a3378`) |

## Milestones
- [x] Read AGENTS.md, CONTRACT, RESEARCH, brief, RUNBOOK
- [x] Tests written first: `compare_intro.py` (brief §5, verbatim), written before any install or run
- [x] Interpreter created and verified (attempt A: repo pins on CPython 3.12.13 arm64)
- [x] `.venv/.duq-ready` written immediately after the four step-4 checks passed, before the reproductions
- [x] Comparison self-test passed
- [x] Reproductions run and compared: ALL MATCH
- [x] `results/` and `figures/` restored byte-identical
- [x] Pins frozen into `requirements.txt`; dry-run and `uv pip check` clean
- [x] GitHub and hardware facts recorded
- [x] Explain-back questions drafted (end of file)

## Acceptance gates (brief §8)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| Interpreter usable from a new shell, `XLA_FLAGS` set there | **N/A (macOS: per-shell export, see `.orchestrator/RUNBOOK.md`)**; interpreter evidence passes | `env -i HOME=… PATH=/usr/bin:/bin /bin/zsh -f -c 'export DUQ_PY=$MAIN/.venv/bin/python; export XLA_FLAGS=…; "$DUQ_PY" -c "import sys, os; print(sys.executable); print(os.environ[\"XLA_FLAGS\"])"'` → `$MAIN/.venv/bin/python` and `XLA_FLAGS=--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2` |
| `check_env.py` final <n> in [3.9, 4.1] | PASS | `mesolve OK in 1.29s, final <n> = 3.996 (expect ~4)`; `JAX devices: [CpuDevice(id=0)]` |
| `-m src.config`, x64 check, §4 import line | PASS | `kappa_2/2pi = 0.896 MHz (expect 0.896)`; `x64 OK`; `imports OK` |
| `compare_intro.py` self-test | PASS | ref vs ref → `ALL MATCH`, exit 0 (33 `yes` rows); ref vs ref_bad → exit 1, `1 FAILURES`, single row `\| task_1_1.json \| peak_na \| 6.89441173256 \| 6.9 \| 8.11e-04 \| rel 0.0001 \| NO \|` |
| `compare_intro.py ref new` exits 0 for both files | PASS | `ALL MATCH`, exit 0 (table below) |
| After restore, `git status --porcelain` = before + only the two lane files | PASS | `status_before.txt` was empty; after restore: ` M requirements.txt`, `?? docs/plan/status/setup.md` |
| `uv pip install -r requirements.txt --dry-run` changes nothing; `uv pip check` passes | PASS | `Checked 12 packages in 84ms` / `Would make no changes`; `Checked 128 packages in 1ms` / `All installed packages are compatible` |
| Commit lists exactly the two paths | PASS | `git show --stat HEAD` → `requirements.txt`, `docs/plan/status/setup.md` (see final report for the sha) |
| Status file complete (versions, attempts, timings, table, script, pins, gh, hardware) | PASS | this file |

## Interpreter
- **Path:** `$MAIN/.venv/bin/python` (export `DUQ_PY=$MAIN/.venv/bin/python`; the macOS equivalent of `D:\duq-venv\Scripts\python.exe`).
- **Python:** CPython 3.12.13 (Homebrew build, Clang 16.0.0), 64 bit, `platform.machine() == 'arm64'`.
- **Attempt that worked:** A (repo pins on Python 3.12). Fallback 1 (3.11 + jax 0.10.2) was not needed.
- **Versions:** jax 0.12.0.1, jaxlib 0.12.0.1, dynamiqs 0.3.7, numpy 2.5.4, scipy 1.18.1 (matplotlib 3.11.2, pandas 3.1.0).
- `platform.platform()` = `macOS-14.5-arm64-arm-64bit`; `os.cpu_count()` = 8.
- `XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"` was set for every check and run. XLA accepted it; there was no `Unknown flags in XLA_FLAGS` error.

## Attempts log
| # | Command | Outcome | Time |
|---|---|---|---|
| 1 | `uv venv .venv -p 3.12` (inside the Cursor agent sandbox) | `error: Failed to create virtual environment` / `Caused by: failed to open file .../.venv/CACHEDIR.TAG: Operation not permitted (os error 1)`. The sandbox blocks writes into `.venv/`. This is not a Python or pin problem. It left an empty `.venv/` directory. | < 1 min |
| 2 | `uv venv .venv -p 3.12 --clear` (outside the sandbox; `--clear` only removes the empty dir from attempt 1) | OK: `Using CPython 3.12.13 interpreter at: /opt/homebrew/opt/python@3.12/bin/python3.12`; bitness check → `64 bit`, `arm64` | 0.17 s |
| 3 | `uv pip install --python .venv/bin/python -r requirements.txt pytest sympy optax psutil` | OK: `Resolved 128 packages`, `Installed 128 packages` | 8.1 s |

## Checks (brief §6 step 4, with `XLA_FLAGS` set)
```text
$ "$DUQ_PY" check_env.py
JAX devices: [CpuDevice(id=0)]
dynamiqs version: 0.3.7
mesolve OK in 1.29s, final <n> = 3.996 (expect ~4)
(31.4 s wall on the first run: cold start of a fresh venv, compiling site-packages bytecode)

$ "$DUQ_PY" -m src.config
kappa_2/2pi = 0.896 MHz (expect 0.896)
g2/kappa_b = 0.29, eps_d/kappa_b = 1.29
phase-flip time 1/(2 kappa_a alpha^2) = 1.94 us

$ "$DUQ_PY" -c "import dynamiqs, jax, jaxlib, numpy, scipy, matplotlib, pandas, pytest, sympy, optax, psutil; print('imports OK')"
imports OK

$ "$DUQ_PY" -c "import src.config, jax.numpy as jnp; assert jnp.zeros(1).dtype == jnp.float64; print('x64 OK')"
x64 OK
```
The same x64 check also passes inside the Cursor agent sandbox (read-only use of the venv), which is how the lane agents call it.

## Timings (`XLA_FLAGS` set; `/usr/bin/time -l`)
| Step | Wall | Peak RSS | Expected (brief) |
|---|---|---|---|
| venv create | 0.17 s | | |
| install (128 packages) | 8.1 s | | |
| `check_env.py` (first, cold) | 31.4 s (mesolve itself 1.29 s) | | |
| `-m tasks.task_1_0` | **9.62 s** | 0.53 GB | ≈ 20 s |
| `-m tasks.task_1_1` (32×12 plus 24×6 starter) | **19.24 s** | 0.54 GB | ≈ 1 min |

## Comparison: committed (Linux x86_64) vs fresh (macOS arm64)
`"$DUQ_PY" .orchestrator/duq-setup/compare_intro.py ref new` → exit 0.

| file | key | committed | fresh | diff | rule | ok |
|---|---|---|---|---|---|---|
| task_1_0.json | a.max_abs_error_vs_analytic | 9.72004421396e-12 | 9.7200476834e-12 | 9.72e-12 | abs_lt 1e-09 | yes |
| task_1_0.json | b.final_n_pred | 0.499832268686 | 0.499832268686 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | b.final_n_sim | 0.499832268686 | 0.499832268686 | 2.22e-15 | rel 1e-06 | yes |
| task_1_0.json | b.parity_end | 0.000335462627884 | 0.000335462627886 | 5.13e-12 | rel 1e-06 | yes |
| task_1_0.json | b.parity_start | 0.000335462627902 | 0.000335462627902 | 3.38e-13 | rel 1e-06 | yes |
| task_1_0.json | b.pop_0 | 0.500167731314 | 0.500167731314 | 1.11e-15 | rel 1e-06 | yes |
| task_1_0.json | b.pop_1 | 0.499832268686 | 0.499832268686 | 2.33e-15 | rel 1e-06 | yes |
| task_1_0.json | b.rel_error | 1.1768364061e-14 | 9.54791801178e-15 | 9.55e-15 | abs_lt 1e-10 | yes |
| task_1_0.json | c.alpha2 | 4.41 | 4.41 | 0.00e+00 | abs 1e-12 | yes |
| task_1_0.json | c.final_n.0 | 4.38716647887 | 4.38716647887 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.final_n.1 | 4.40396934689 | 4.40396934689 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.final_n.2 | 4.40814407621 | 4.40814407621 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.t90_times_kappa2.0 | 0.858193915895 | 0.858193915895 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.t90_times_kappa2.1 | 0.872262668615 | 0.872262668615 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.t90_times_kappa2.2 | 0.900400174054 | 0.900400174054 | 0.00e+00 | rel 1e-06 | yes |
| task_1_0.json | c.t90_us.0 | 0.61 | 0.61 | 0.00e+00 | abs 1e-09 | yes |
| task_1_0.json | c.t90_us.1 | 0.155 | 0.155 | 0.00e+00 | abs 1e-09 | yes |
| task_1_0.json | c.t90_us.2 | 0.04 | 0.04 | 0.00e+00 | abs 1e-09 | yes |
| task_1_1.json | Na | 32 | 32 | 0.00e+00 | abs 0 | yes |
| task_1_1.json | Nb | 12 | 12 | 0.00e+00 | abs 0 | yes |
| task_1_1.json | epsd_over_kappab | 1.29416538462 | 1.29416538462 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | g2_over_kappab | 0.293461538462 | 0.293461538462 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | max_top2_a | 1.36188185078e-05 | 1.36188185078e-05 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | max_top_b | 0.000169208209761 | 0.000169208209761 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | overshoot_over_alpha2 | 1.56335866952 | 1.56335866952 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | peak_na | 6.89441173256 | 6.89441173256 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | peak_nb | 1.99152049 | 1.99152049 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | settle_1pct_us | 1.07 | 1.07 | 0.00e+00 | abs 1e-09 | yes |
| task_1_1.json | starter_max_top_b | 0.0462416289476 | 0.0462416289476 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | starter_peak_na | 6.11451721395 | 6.11451721395 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | steady_na | 4.40261555655 | 4.40261555655 | 0.00e+00 | rel 0.0001 | yes |
| task_1_1.json | t_peak_nb_us | 0.13 | 0.13 | 0.00e+00 | abs 1e-09 | yes |
| task_1_1.json | t_peak_us | 0.23 | 0.23 | 0.00e+00 | abs 1e-09 | yes |
ALL MATCH

The largest relative difference is 5.1e-12 (`b.parity_end`). `results/task_1_1.json` and `results/task_1_0c_nominal.npy` were rewritten **byte-identical** (git showed them unmodified). Only `results/task_1_0.json` and the 7 PNGs differed, the JSON in its last digits.

### `compare_intro.py` (source, verbatim from brief §5; stored at `.orchestrator/duq-setup/compare_intro.py`)
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
        # utf-8-sig: tolerates a BOM if a JSON was ever rewritten by Windows PowerShell 5.1
        ref = dict(leaves(json.loads((Path(ref_dir) / name).read_text(encoding="utf-8-sig"))))
        new = dict(leaves(json.loads((Path(new_dir) / name).read_text(encoding="utf-8-sig"))))
        if set(ref) != set(new): print(f"KEY MISMATCH {name}: {set(ref) ^ set(new)}"); fails += 1
        for key in sorted(set(ref) & set(new)):
            ok, diff, rule = check(key, ref[key], new[key], rel, rules)
            fails += not ok
            print(f"| {name} | {key} | {ref[key]:.12g} | {new[key]:.12g} | {diff:.2e} | {rule} | {'yes' if ok else 'NO'} |")
    print("ALL MATCH" if fails == 0 else f"{fails} FAILURES"); return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
```
Self-test: `ref_bad/task_1_1.json` was written as plain ASCII by Python (first bytes `7b0a20`, no BOM), with `peak_na` changed from `6.894411732563246` to `6.90`.

## Pins (`requirements.txt`, final content)
```text
# Versions used to produce every figure and number in this repo
# Verified 2026-10-24: macOS 14.5 arm64 (Apple M3, CPU only), CPython 3.12.13, uv 0.11.24, shared venv <repo>/.venv
dynamiqs==0.3.7
jax==0.12.0.1
jaxlib==0.12.0.1
numpy==2.5.4
scipy==1.18.1
matplotlib==3.11.2
pandas==3.1.0
jupyter==1.1.1
pytest==9.1.1
sympy==1.14.0
optax==0.2.8
psutil==7.2.2
```
These versions are the values for `provenance.dynamiqs/jax/python` in v2 records (CONTRACT §6.2): dynamiqs 0.3.7, jax 0.12.0.1, python 3.12.13.

<details><summary>Full <code>uv pip freeze</code> (128 packages)</summary>

```text
absl-py==2.5.1
anyio==4.15.1
appnope==1.0.0
argon2-cffi==25.1.0
argon2-cffi-bindings==26.1.0
arrow==1.4.0
asttokens==3.0.2
async-lru==2.4.0
attrs==26.1.0
babel==2.18.0
beautifulsoup4==4.15.0
bleach==6.4.0
certifi==2026.10.23
cffi==2.1.1
charset-normalizer==3.5.2
cmap==0.8.0
comm==0.2.3
contourpy==1.4.0
cycler==0.12.1
debugpy==1.8.22
defusedxml==0.7.1
diffrax==0.7.2
dynamiqs==0.3.7
equinox==0.13.8
executing==2.3.0
fastjsonschema==2.22.2
fonttools==4.67.0
fqdn==1.6.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.20
iniconfig==2.3.1
ipykernel==7.4.0
ipython==9.17.1
ipython-pygments-lexers==1.1.1
ipywidgets==8.1.9
isoduration==20.11.0
jax==0.12.0.1
jaxlib==0.12.0.1
jaxtyping==0.3.11
jedi==0.20.1
jinja2==3.1.6
json5==0.17.3
jsonpointer==3.5
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
jupyter==1.1.1
jupyter-builder==1.2.3
jupyter-client==8.10.0
jupyter-console==6.6.3
jupyter-core==5.9.1
jupyter-events==0.12.1
jupyter-lsp==2.3.1
jupyter-server==2.21.1
jupyter-server-terminals==0.5.4
jupyterlab==4.6.4
jupyterlab-pygments==0.3.0
jupyterlab-server==2.28.1
jupyterlab-widgets==3.0.17
kiwisolver==1.5.1
lark==1.3.1
lineax==0.1.1
markupsafe==3.0.4
matplotlib==3.11.2
matplotlib-inline==0.2.2
mistune==3.4.0
ml-dtypes==0.6.0
mpmath==1.3.0
nbclient==0.11.0
nbconvert==7.17.2
nbformat==5.11.1
nest-asyncio2==1.7.4
notebook==7.6.3
notebook-shim==0.2.4
numpy==2.5.4
opt-einsum==3.4.0
optax==0.2.8
optimistix==0.1.0
packaging==26.3
pandas==3.1.0
pandocfilters==1.5.1
parso==0.8.7
pexpect==4.9.0
pillow==13.0.0
platformdirs==4.13.5
pluggy==1.7.0
prometheus-client==0.26.0
prompt-toolkit==3.0.53
psutil==7.2.2
ptyprocess==0.7.0
pure-eval==0.2.4
pycparser==3.12
pygments==2.21.0
pyparsing==3.3.3
pytest==9.1.1
python-dateutil==3.0.0
python-json-logger==4.2.0
pyyaml==6.0.3
pyzmq==27.2.0
qutip==5.3.1
referencing==0.37.0
requests==2.34.2
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rfc3987-syntax==1.1.0
rpds-py==2026.9.1
scipy==1.18.1
send2trash==2.1.0
six==1.17.0
soupsieve==3.0.4
stack-data==0.6.3
sympy==1.14.0
terminado==0.18.1
tinycss2==1.5.1
tornado==6.6
tqdm==4.70.1
traitlets==5.16.1
typing-extensions==4.16.0
tzdata==2026.5
uri-template==1.3.0
urllib3==2.8.0
wadler-lindig==0.1.7
wcwidth==0.9.4
webcolors==25.10.0
webencodings==0.6.1
websocket-client==1.9.2
widgetsnbextension==4.0.16
```
</details>

## GitHub
- `gh`: **not installed** on this machine (`command -v gh` finds nothing). Not installed, per instructions. So "logged in", "`workflow` scope present" and `viewerPermission` are **unknown**. Before pushing `.github/workflows/*`, the integrator or Harshit must push from a machine with an authenticated `gh` (or git credentials) that has the `workflow` scope (`gh auth refresh -s workflow`).
- `git remote -v` → `origin https://github.com/pkarakala/duquantum-cat-qubit.git` (fetch and push).

## Hardware
- `system_profiler SPHardwareDataType` (filtered): MacBook Air (Mac15,12), Chip: Apple M3, Total Number of Cores: 8 (4 performance and 4 efficiency), Memory: 8 GB.
- `sysctl`: `hw.ncpu: 8`, `hw.physicalcpu: 8`, `hw.logicalcpu: 8` (no SMT), `hw.perflevel0.physicalcpu: 4`, `hw.perflevel1.physicalcpu: 4`, `hw.memsize: 8589934592` (8.0 GiB).
- `python -c "import platform, os; print(platform.platform(), os.cpu_count())"` → `macOS-14.5-arm64-arm-64bit 8`.
- CPU only (no GPU backend; `JAX devices: [CpuDevice(id=0)]`).

## Restore proof
```text
$ git checkout -- results figures
$ git status --porcelain -- results figures
(empty)
$ git diff --quiet -- results figures; echo $?
0
$ git status --porcelain
 M requirements.txt
?? docs/plan/status/setup.md
```
`status_before.txt` (preflight snapshot) was empty.

## Commands run (zsh translation of brief §9; scratch dir `T=$MAIN/.orchestrator/duq-setup`)
```text
git branch --show-current                         -> standard-track
git status --porcelain > $T/status_before.txt     -> (empty)
~/.local/bin/uv --version                         -> uv 0.11.24 (5e04460c0 2026-06-23 aarch64-apple-darwin)
time uv venv .venv -p 3.12 --clear
.venv/bin/python -c "import struct, sys, platform; ..."   -> 3.12.13, 64 bit, arm64
time uv pip install --python .venv/bin/python -r requirements.txt pytest sympy optax psutil
export DUQ_PY=$MAIN/.venv/bin/python XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
"$DUQ_PY" check_env.py; "$DUQ_PY" -m src.config; import line; x64 check
touch .venv/.duq-ready                            -> 18:31:23 EDT
cp results/task_1_0.json results/task_1_1.json $T/ref/; self-test (ref vs ref, ref vs ref_bad)
/usr/bin/time -l "$DUQ_PY" -m tasks.task_1_0 | tee $T/task_1_0.log
/usr/bin/time -l "$DUQ_PY" -m tasks.task_1_1 | tee $T/task_1_1.log
cp results/task_1_0.json results/task_1_1.json $T/new/
"$DUQ_PY" $T/compare_intro.py $T/ref $T/new | tee $T/compare.md   -> ALL MATCH, exit 0
git checkout -- results figures
uv pip freeze --python .venv/bin/python > $T/freeze.txt
uv pip install --python .venv/bin/python -r requirements.txt --dry-run; uv pip check --python .venv/bin/python
system_profiler SPHardwareDataType | grep ...; sysctl ...; command -v gh; git remote -v
```

## Records produced
None (brief §7: no v2 records; lane `l0-tools` wraps the intro JSONs and cites the comparison table above).

## Figures / arrays produced
- None committed. The 7 intro PNGs, `task_1_0.json` and `task_1_0c_nominal.npy` were regenerated, compared, and restored with `git checkout -- results figures`.

## Jobs to queue (for the integrator; jobs > 15 min)
None.

## Deviations from the brief (and why)
- **Platform:** macOS 14.5 arm64 / Apple M3 / 8 GB instead of Windows 11 x86_64 / i7-9750H / 16 GB (RUNBOOK §1). The interpreter is `$MAIN/.venv/bin/python` instead of `D:\duq-venv\Scripts\python.exe`. CONTRACT §2 already names `.venv/bin/python` for Unix. Brief §10's "no second venv inside the repo (`.venv/` is for WSL/cloud only)" is overridden by RUNBOOK §2 on this machine; `.venv/` is git-ignored.
- **Env-var persistence (`setx`, new PowerShell, Cursor restart):** not applicable on macOS; agents export `DUQ_PY` and `XLA_FLAGS` in each shell (RUNBOOK §2).
- **Scratch dir:** `$MAIN/.orchestrator/duq-setup/` (git-ignored) instead of `$env:TEMP\duq-setup`, because the agent sandbox only allows writes inside the workspace.
- **venv creation needed to run outside the Cursor sandbox:** the sandbox refuses writes into `.venv/` (attempt 1 above). Install and verification also ran unsandboxed so bytecode for site-packages could be written into the venv once. Sandboxed read-only use works: the x64 check passes inside the sandbox.
- **`gh` facts unavailable:** `gh` is not installed (see GitHub).

## DECISION NEEDED
None.

## Notes for Claude's later review
- Cross-platform reproduction is essentially bit-level. Every task_1_1 leaf is bit-identical (the JSON file was byte-identical). task_1_0's largest relative difference is 5.1e-12, and `t90_us` / `settle_1pct_us` / `t_peak_us` grid crossings did not move. No tolerance was touched.
- The run times are about 2× faster than the brief's Windows estimates (9.6 s vs ≈ 20 s, and 19.2 s vs ≈ 1 min) with `intra_op_parallelism_threads=2`. Peak RSS is about 0.54 GB for both. The other lanes were idle or starting while these ran.
- **Cross-lane environment note (performance only, not correctness):** inside the Cursor agent sandbox `~/.matplotlib` is not writable. Matplotlib then logs `/Users/<user>/.matplotlib is not a writable directory`, makes a temporary cache dir under `$TMPDIR`, and rebuilds its font cache in every new process (a few seconds each). A coordinator could set `MPLCONFIGDIR` to a writable, git-ignored directory in each lane shell to avoid this. I did not change the RUNBOOK (not this lane's file).
- The venv must not be recreated from now on (other lanes are using it; `.duq-ready` exists).

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. κ₂/2π comes out as 0.896 MHz. Derive it from g₂ and κ_b, say where the 2π is applied in the code, and explain why applying it twice would silently pass `check_env.py` but break every rate.
2. The committed numbers came from a Linux x86_64 machine, and you reproduced them on macOS arm64 (Apple M3) with a different jaxlib build, to about 1e-12 and bit-identical for Task 1.1. What does that agreement actually prove? What does it not prove (for example about truncation)? What size of disagreement would make you distrust the solver rather than the platform?
3. In Task 1.1 the buffer's top-level population is 1.69e-4 at 32×12 but 4.6e-2 at the 24×6 starter truncation. What is this monitor measuring? Why does it decide whether `peak_na` = 6.89 can be trusted? Why is the overshoot above α² = 4.41 physical rather than a truncation artifact?
