# Status: lane `l5-circuit`

| Field | Value |
|---|---|
| State | `IN_PROGRESS` (paused: waiting for l0-core merge) |
| Branch | `std/l5-circuit` |
| Agent / model | Cursor agent, Grok 4.7 |
| Started (EDT) | Sat Oct 24 2026, 6:35 PM |
| Last update (EDT) | Sat Oct 24 2026, 7:25 PM |
| Last commit | `10bf57f` `[l5-circuit] Derive the ATS terms and the displaced-frame shifts` |

## Milestones
- [x] Read brief, CONTRACT, RESEARCH, RUNBOOK
- [x] Tests written first (previous commit `dd931d0`; not rewritten)
- [x] Implementation complete (`src/circuit.py`, `docs/derivation_2_4a.md`, `tasks/task_2_4a.py`)
- [ ] `--quick` run passes (≤ 2 min) — blocked on `record()` / `convergence_block` / `plotting.save(quick=)`
- [ ] Production run(s) done, or queued (see Jobs to queue)
- [ ] All acceptance gates in brief §8 checked, with evidence below
- [x] Explain-back questions drafted

## Acceptance gates (brief §8; tick with evidence)
| Gate | Result | Evidence (command → key output) |
|---|---|---|
| 1. §5 tests pass; fast suite < 2 min | pass | `pytest tests/test_l5_circuit.py -q` → `10 passed in 5.10s`. `pytest -m "not slow" -q` → `10 passed in 4.13s` (this branch has no other tests; `pytest.ini` is l0-core's) |
| 2. g₂.sym = −0.7214 MHz; ε_p(0.763) = 0.0370; ε_p\* reported; sign/gauge in doc | pass (not yet a record) | `g2_from_circuit` / 2π = −0.721434 MHz; undisplaced ε_p = 0.037017; ε_p\* = 0.037614. Sign and gauge are in `docs/derivation_2_4a.md` §4 |
| 3. Resonant count = 12 through order 7, list in notes and doc | pass (not yet a record) | `test_resonant_family_order7`; integer scan also 12. The 12 monomials are listed in the derivation §3 |
| 4. Displaced static linear terms < 1e-9 MHz; five ratios; stark_b(ε_p\*) ∈ [20, 32] MHz | pass | `test_displaced_frame_static`, `test_eps_p_star_and_stark_window`. At ε_p\*: stark_a = 1.0532, stark_b = 26.331, kerr_a = −9.479e-4, kerr_b = −0.5924, chi_ab = −0.09479 MHz |
| 5. V1: tdsim \|g₂\| within 3% of \|g₂,disp\|; no-½ excluded > 20σ; bare max P₀₁ < 0.05; retuned ≥ 0.95; rtol change < 1e-4; Na/Nb converged | not run (production) | Smoke only, not a record: 50 ns, Na=6, Nb=4, ε_p\*. Bare max P₀₁ = 0.0067; retuned P₀₁(50 ns) = 0.095 vs resonant sin²(Gt) = 0.111. Retune direction is right. Production is 0.3 µs, Na=10, Nb=8, after the merge |
| 6. V2: E1 max\|Δn_a\| ≤ 0.03; E2 error ≥ 5× E1; Re⟨a²⟩_tdsim < 0 | not run | Needs `two_mode(..., extra_H=)`, which is not on this branch. A 1 ns composed `mesolve` of circuit H plus the retuned buffer drive does run |
| 7. Production records: dirty false, cross_check agree, convergence per table | blocked | `git -C $MAIN log --oneline standard-track \| grep -m1 "merge l0-core"` → no match. `src.results` has no `record`. `--part sym` exits `PAUSED_FOR_L0_CORE` |
| 8. `docs/derivation_2_4a.md` complete (term table + extra_H recipe); status DONE | doc done, status not DONE | Term table §11, recipe §12. Status stays paused until gates 5–7 have records |

## Commands run (most recent first)
```text
$DUQ_PY -m pytest -m "not slow" -q
10 passed in 4.13s

$DUQ_PY -m pytest tests/test_l5_circuit.py -q
10 passed in 5.10s

$DUQ_PY -m tasks.task_2_4a --part sym --quick
sym collected in 0.0s: eps_p*=0.03761 g2_disp=-0.7630 MHz stark_b=26.331 MHz wp'=3.175774 GHz
PAUSED_FOR_L0_CORE: cannot import name 'record' from 'src.results'
exit 1

# 50 ns exchange smoke (Na=6, Nb=4, eps_p*, not a record)
bare     P01(end)=0.0027  max=0.0067   resonant_pred=0.1106
retuned  P01(end)=0.0954  max=0.0954   resonant_pred=0.1106

git -C $MAIN log --oneline standard-track | grep -m1 "merge l0-core"
NO_L0_MERGE
```

## Records produced
| Record id | Value | Units | Converged | Cross-check (method, rel_diff, tol, agree) |
|---|---|---|---|---|
| (none yet) | | | | |

Symbolic values the records will store, already computed by `collect_sym` (MHz unless noted):

| Quantity | Value |
|---|---|
| `t2_4a.g2.sym.circuit` | −0.721434 |
| ε_p for 0.763, undisplaced | 0.037017 |
| ε_p\* | 0.037614 |
| g₂,disp at ε_p\* | −0.763000 |
| g₂,disp at ε_p = 0.035 | −0.7115 |
| stark_a, stark_b | 1.05323, 26.3308 |
| kerr_a, kerr_b, chi_ab | −9.479e-4, −0.59244, −0.09479 |
| K_b/2π = −2 kerr_b | 1.185 |
| ω_p′/2π | 3.175774 GHz (3.2 GHz − 24.23 MHz) |
| buffer drive | 4.826331 GHz |
| resonant count | 12 |
| g_bs / ε_Z | 0.03089 |
| g_sp / ε_d | −0.045 |
| memory two-photon / ε_d | 6.18e-4 |
| 4 g_bs²/κ_b at ε_Z = 3 g₂ | 0.0483 /µs (κ_a = 0.0584 /µs) |
| iQuHACK g₂/2π at ε_p\* | −1.625 (2.130 × \|g₂\|) |
| g_eff(n_a=4.41)/g₂ | 0.9971 |

## Figures / arrays produced
None. `figures/task_2_4a_terms.png`, `figures/task_2_4a_validation.png`, and the two `results/arrays/t2_4a.*.npz` files are written by the task once `record` / `save_arrays` exist.

## Jobs to queue (for the integrator; jobs > 15 min)
| Name | Command (from repo root) | RAM est. (GB) | Wall est. | Outputs (record ids) |
|---|---|---|---|---|
| l5_v2_a2.1 | `python -m tools.runq submit --name l5_v2_a2.1 --ram-gb 2 -- $DUQ_PY -m tasks.task_2_4a --part tdsim --alpha2 4.41 --na 16 --nb 12` | 2 | ~30–60 min (estimate; not measured) | traces in `results/arrays/t2_4a.inflation.tdsim.circuit.npz` (does not overwrite the α²=1 g₂ fit) |

In-lane after the merge, not queued: `--part sym` (seconds) and `--part tdsim` at α²=1, Na=12, Nb=6, 0.2 µs. A 50 ns exchange at Na=6, Nb=4 took 1.5 s, so the 0.3 µs V1 at Na=10, Nb=8 is estimated at a few minutes per trace (bare, retuned, rtol, Na/Nb). If that set exceeds 15 min, move V1's extra truncations to the queue and keep the (10, 8) pair in-lane.

## Deviations from the brief (and why)
- No production records: `l0-core` is not merged, so `src.results.record`, `src.convergence.convergence_block` and `plotting.save(..., quick=)` are absent. `two_mode` has no `extra_H`. Checked `standard-track` for `merge l0-core`; not present. Did not merge, did not copy those files.
- Step 6 (van Vleck) is cut, as the brief allows. The one recalibration inside V1 is the numerical stand-in, and only if the Stark-retuned 0.3 µs trace has max P₀₁ < 0.95.
- κ is omitted from ξ (κ_b / 2Δ ~ 10⁻³), as the brief says.

## DECISION NEEDED
(none)

## Explain-back for Harshit (questions only; Harshit writes the answers in docs/defense.md)
1. Your g₂ has an extra e^{−(φ_a²+φ_b²)/2} and a ½ that a public tutorial leaves out. Where does each factor come from, and how did your simulation decide between them?
2. The pump shifts the buffer by about 26 MHz, roughly 35 times g₂. Why does that not destroy the cat, what exactly has to be retuned, and what would you see in the lab if it were not?
3. If the readout drive is applied through the ATS flux instead of capacitively, which new terms appear, why is one of them exactly resonant, and how would it change Γ_X or Γ_Z?

## Hand-off for the resume (after `merge l0-core` is on `standard-track`)
1. `git merge --no-edit standard-track` on `std/l5-circuit`.
2. Commit is already done, so provenance can be clean: run `$DUQ_PY -m tasks.task_2_4a --part sym`, then `--part tdsim` (α²=1). Heavy lock if a trace will exceed 5 min or 1.5 GB (`$MAIN/.git/duq-heavy.lock`).
3. Commit `results/records/t2_4a.*.json`, `results/arrays/t2_4a.*.npz`, `figures/task_2_4a_*.png` only. Then set this file to DONE with the gate-5 and gate-6 numbers.

## extra_H recipe for `l4b-tradeoff`
In `docs/derivation_2_4a.md` §12. Stark terms are omitted because ω_p′ and the buffer drive are retuned. Kerr and chi are invariant under the pump phase, so the recipe uses `C.G2 > 0`. Flux-tone readout adds `g_bs (a b† + a† b)` with `g_bs = 0.03089 * eps_z`.

## Notes for Claude's later review
- Tests were not modified (`dd931d0`).
- 50 ns smoke is not a record and is not inside the derivation's `rec:` tags.
- `n_t` is a legal axis of the merged `convergence_block` (it does not special-case Na/Nb), so the fallback "convergence: null" should not be needed. Confirm after the merge.
