# AGENTS.md: rules for every coding agent in this repo

This repo is the **DuQuantum 2026 Alice & Bob cat-qubit challenge**. The submission is the **Standard Track** (Tasks 2.1–2.4), plus Intro Tasks 1.3b/c. The Intro Tasks 1.0–1.3a are already done and converged.

The work runs in parallel **lanes**. Each lane is one Cursor agent working in its own git worktree, on branch `std/<slug>`, created from `standard-track`.

**Start here:** `docs/plan/README.md`.
**Then read, in this order:**
1. Your brief: `docs/plan/briefs/<NN>-<slug>.md`.
2. `docs/plan/CONTRACT.md`: frozen interfaces and file ownership.
3. `docs/plan/RESEARCH.md`: verified physics, numbers and sources.

## Non-negotiables
1. **Stay in your allowlist.** It is in CONTRACT §1 and your brief §3. Never edit another lane's files, `docs/challenge_prompt_v4.md`, `prep/`, `docs/defense.md`, or `docs/handwritten/`. Never add anything from `notes/`. It is git-ignored for a reason: it contains organizer phone numbers.
2. **Units:** ħ = 1, time in µs, rates in rad/µs. The 2π is applied **once**, in `src/config.py`; nowhere else (`G2`, `KAPPA_B`, `KAPPA_A`, `KAPPA_2`, `EPS_D`). **Always import `src.config` first**, because it sets double precision.
3. **Build physics only through `src/model.py`** (`one_mode`, `two_mode`, `loss_jumps`, `drive_ops`, `coherent2`, `cat2`). Never hand-roll H or jump operators in a task script.
4. **Drive quadratures (RESEARCH §4.1):**
   - `eps_z·(a+a†)` is the readout drive. It pushes along Im and **cannot** select a well.
   - `eps_x·i(a†−a)` pushes along Re. Use it to prepare |+α⟩.
5. **Every reported number becomes a record.** Use `src.results.record(...)` (CONTRACT §6), with:
   - a convergence block (Na and Nb swept **separately**, at **every** α);
   - at least one independent cross-check with a stated tolerance;
   - `provenance.dirty == false`. The order is: commit code, then run, then commit outputs.
6. **Eigenvalues come from `src.spectral`** (Z₂ odd block for Γ_X; `full_deflated` when ε ≠ 0). Accept an eigenvalue only if `rel_residual < 1e-4`, `edge_weight < 1e-6`, and it is stable across two truncations.
7. **Conventions (RESEARCH §5–§7):**
   - Γ_X = decay rate of Re⟨a⟩ = −λ₁. Dubovitskii's per-direction rate is Γ_X/2.
   - Γ_Z = decay rate of parity = 2κ_aα²coth(2α²).
   - Fit parity with `fit_exp_offset`, because the steady parity is 1/cosh(2α²), not 0.
8. **TDD:** write your lane's tests (`tests/test_<slug_underscored>.py`) **before** the implementation. Analytic predictions become assertions.
9. **No physics in readers.** Notebooks, the Lab (`site/`), slides and docs only read `results/` and `figures/`.

## Environment (Windows, shared venv)
```powershell
$env:DUQ_PY = "D:\duq-venv\Scripts\python.exe"        # created by docs/plan/briefs/00-setup.md
$env:XLA_FLAGS = "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2"
& $env:DUQ_PY -m pytest -m "not slow" -q              # fast tests, < 2 min total
& $env:DUQ_PY -m tasks.<task_script> --quick          # smoke run, <= 2 min, outputs to results/quick + figures/quick
```
- Run from the **worktree root** as modules (`-m tasks.x`). **No `pip install -e`.**
- `OMP_NUM_THREADS` does not limit JAX/XLA. Use `XLA_FLAGS`.
- **Laptop limits:** 16 GB RAM, 6 cores. At most 3 heavy jobs, and **only one sparse LU > 3 GB at a time**.
- **Production runs:**
  - Jobs ≤ 15 min may run in your lane, and their outputs may be committed.
  - Longer jobs: list them under **Jobs to queue** in your status file (command plus RAM estimate). The integrator runs them through `tools/runq.py` after the merge.
- **Unix / WSL / cloud:** `.venv/bin/python` (see `.cursor/setup-worktree-unix.sh`).

## Git
- Your branch is `std/<slug>`. Make small commits with the prefix `[<slug>]`. **Never** push, rebase shared branches, or commit to `standard-track`, `intro-track-tasks`, or `main`. The integrator merges.
- Stage explicit paths only. **Never `git add .` or `git add -A`.**
- End every commit message with `Co-Authored-By:` lines for the AI tools used. Cursor adds its own; keep any existing lines.

## Status and escalation
- Keep `docs/plan/status/<slug>.md` up to date (copy it from `docs/plan/status/_TEMPLATE.md`) at every milestone: started, tests written, gate passed or failed, blocked, done.
- When something is physics-relevant, cross-lane, or would change CONTRACT, **do not guess**. Write a `DECISION NEEDED` block (question, options, your recommendation), continue with anything that doesn't depend on it, and stop if everything does.
- Harshit, the integrator, and Claude (the later reviewer) read these files. **They are the only channel.**

## Style
Match the existing `src/` and `tasks/task_1_*.py` style:
- Short module docstrings that say what and why.
- `argparse` `main()` with `--quick`.
- Figures through `src.plotting.save`.
- No new heavy dependencies without a `DECISION NEEDED`.
- Comments explain *why*, not what.
