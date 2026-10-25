# Brief `p3-blocks`: operator blocks → ExprTree, validation, pretty printers

> **Paste into a new Cursor agent (worktree mode):** "You are product lane `p3-blocks`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P3-blocks.md`, then execute the brief exactly. Keep `docs/product/status/p3-blocks.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p3-blocks` | `prod/p3-blocks` from `standard-track` | none. The expr fixtures come from P0; until they land, use the format below and reconcile. | standard | 2 h | 11:45 PM → 1:45 AM (P-G1) |

## 1. Goal and why
This is the "code.org" heart of level 6 ("Build the machine") and of the Sandbox. Learners **snap operator blocks together** to build the Hamiltonian and the jump operators of Alice & Bob's memory–buffer system. The blocks compile to one shared **ExprTree** (CONTRACT §4), which drives the TS solver (one-mode), the server (two-mode) and "Show the code".

Common wrong builds become teachable moments for the tutor. The biggest one is ε(a + a†) instead of the buffer drive, which can't make a cat (RESEARCH §4.1).

## 2. Read first
- `docs/product/CONTRACT.md` §4 (ExprTree: allowlist, limits, sqrt rule, pretty printers, fixtures).
- `docs/product/LEVELS.md` L6 (palette, check, the wrong builds).
- `docs/plan/RESEARCH.md` §4.1 (why ε(a + a†) can't select a well).
- Blockly docs: **v13.4.0**, now maintained under RaspberryPiFoundation/blockly. Custom blocks, a JSON block definition and a code generator.

## 3. Allowlist (touch nothing else)
`site/src/blocks/**` (code, tests, lane-local `vitest.config.ts`) and `docs/product/status/p3-blocks.md`.

## 4. Interfaces you implement
- `blocks.ts`: Blockly block definitions, colour-coded and colour-blind safe (memory ops one hue, buffer ops another, params a third).
  - `op_a`, `op_ad` (a†), `op_b`, `op_bd` (b†), `op_n_a`, `op_I`
  - `num` (a number field), `param` (dropdown: g₂, ε_d, κ_b, κ_a, κ₂, α, ε_z, ε_x, K, χ)
  - `mul` (variadic; non-commutative, left to right), `add` (variadic), `pow` (2–4), `dag`
  - `sqrt_param` (for jump coefficients only)
  - Two top-level holders: **`hamiltonian` ("H =")** and **`jumps` ("Jumps:", a list)**.
- `workspace.ts`: `mountBlocks(el, {modes: 'one'|'two', initialXml?}) → {getTree(): {H, jumps}, onChange(cb), loadPreset(name)}`. Presets: `empty`, `h2ph_correct`, `one_mode_cat` (√κ₂(a² − α²)), and the wrong builds for the tutor demo.
- `compile.ts`: workspace → `{H: ExprTree, jumps: ExprTree[]}`.
- `expr.ts`:
  - `validate(tree, modes) → {ok, errors[]}`: allowlist symbols (b, bd only when modes = 'two'), depth ≤ 8, ≤ 64 nodes, integer pow 0–4, `sqrt` only on param or num, jump coefficients wrapped in `sqrt`.
  - `toLatex(tree)`.
  - **`toPython(tree)`**: must equal the Python `server/app/expr.py::to_python` string **exactly** on the shared fixtures `server/tests/fixtures/expr/*.json`.
  - `isHermitianSymbolic(H)`: normalize, then check H == dag(H) as trees. Use P1's numeric check at N = 8 when available.
- `wrong-builds.ts`: `detect(tree) → {key, misconception?, message}[]`. The keys:
  - `drive_on_memory_not_buffer`: H contains ε(a + a†) and no buffer drive. Message: "this pushes along the ridge between the wells, so it can't make a cat" (RESEARCH §4.1).
  - `no_dissipation`: no jump containing `b` (two-mode) or a²-type jump (one-mode). Linked to M3.
  - `wrong_conversion`: a·b†² instead of a²·b†.
  - `missing_hc`: the h.c. term is missing, so H isn't Hermitian.
- **Optional stretch** (cut item 2): `parse.ts` is a typed equation line. A Pratt parser for `g2*(a^2*bd + ad^2*b) - eps_d*(b+bd)`, also accepting `dag(x)` and `D[L]` for a dissipator term (which becomes a jump). It produces the same ExprTree, with round-trip tests.

**Fixture format** (shared with P0): `{"name": "...", "modes": "two", "tree": {...}, "python": "g2*(a@a@b.dag()) + ..."}`.

Until P0 commits the real files, write your expected Python strings into the status file. On mismatch, raise a `DECISION NEEDED` that proposes **one canonical style**: operators `a`, `a.dag()`, `@` for products, `**` never, powers expanded (`a@a`), params as bare names, sums with ` + ` and ` - `. Keep it consistent with P0.

## 5. Tests to write FIRST (vitest; jsdom for workspace tests)
- `compile_h2ph`: the preset `h2ph_correct` compiles to the tree of `h_2ph.json`.
- `validate_rejects`: unknown symbol; `b` in one-mode; depth 9; 65 nodes; `pow` 5; `sqrt(a)`; a jump without `sqrt` on its coefficient. Each case gives a specific error message.
- `to_python_matches_fixtures`: for every fixture file present, `toPython(tree) === python`. Skip with a message if absent.
- `to_latex_smoke`: `a^{2} b^{\dagger}` appears for the h2ph tree.
- `hermitian`: h2ph is true; `g2*a@a@b.dag()` alone is false (the `missing_hc` wrong build).
- `wrong_builds`: each of the 4 detectors fires on its crafted tree and stays silent on `h2ph_correct`.
- (Stretch) `parse_roundtrip`: parse, then `toPython`, gives the expected string for 5 inputs.

## 6. Method
1. Run `git switch -c prod/p3-blocks`, create the status file and write the tests.
2. Use `blockly` from npm. Because `site/package.json` belongs to l6 until P7 wires dependencies, **list `blockly@13.4.0` and `vitest` in your status file**, and run tests with a lane-local config: `npx -y vitest@2 run --config site/src/blocks/vitest.config.ts`. Mock Blockly in the unit tests for compile, validate and printers, and keep the Blockly-dependent code in `blocks.ts`/`workspace.ts`.
3. Implement `expr.ts` and `wrong-builds.ts` first (pure TS), then the blocks and the workspace.
4. Build a tiny lane-local demo page, `site/src/blocks/demo.html` + `demo.ts`, served with `npx vite site/src/blocks`. It shows the workspace, the live LaTeX, `toPython` and the detector messages. Take a screenshot into the status file.

## 7. Outputs
`site/src/blocks/` with green tests, the demo page, and the presets, including the wrong builds for the tutor demo.

## 8. Acceptance gates
- [ ] All tests pass. `toPython` matches the fixtures, or a single `DECISION NEEDED` about the format is raised and resolved with P0.
- [ ] The demo builds H_2ph by drag and drop, shows the correct LaTeX and Python, and the detector flags the 4 wrong builds.
- [ ] Keyboard-accessible block selection (Blockly keyboard navigation plugin if feasible; note if not). Colour-blind-safe palette.

## 9. Commands
```powershell
git switch -c prod/p3-blocks
npx -y vitest@2 run --config site/src/blocks/vitest.config.ts
npx -y vite site/src/blocks
```

## 10. Out of scope / do not
- No simulation (P1 and P0 do that) and no level UI (P2). Do not edit `site/package.json`.
- Never `eval` anything. Compile trees only.

## 11. If blocked
- **Blockly integration is slow:** ship the pure ExprTree, validation, printers and detectors first (P2 can show static presets), then the blocks.
- **The fixture format conflicts with P0:** `DECISION NEEDED`. Propose P0's style, since the server is the source of truth for the generated Python.
- **Cut line:** the typed equation line (stretch) goes first.

## 12. Hand-off
At DONE, the status file has: tests, the demo screenshot, deps for P7, the fixture reconciliation, and the preset list.

**Questions Harshit should be able to answer:**
1. Why is the product a²b† and not a b†², and what physical process does each term describe?
2. Why can't the block build ε(a + a†) prepare a cat, while the buffer drive can?
3. How do we make sure learner-built Hamiltonians can't run arbitrary code on our server?
