# Status: lane `p3-blocks`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p3-blocks` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 00:27 |
| Last update (EDT) | 2026-10-25 01:00 |
| Last commit | implementation `12a673b` `[p3-blocks] Add the operator-block editor and ExprTree compiler.` |

## Milestones
- [x] Read brief, CONTRACT §4, LEVELS L6, RESEARCH §4.1
- [x] Tests written first (then implementation)
- [x] Implementation complete
- [x] Vitest green (10 tests)
- [x] Demo checked in the browser
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## Acceptance gates
| Gate | Result | Evidence |
|---|---|---|
| Tests pass; `toPython` matches fixtures or one canonical style is recorded | PASS, fixtures absent | `./node_modules/.bin/vitest run` in `site/src/blocks`: 2 files, 10 tests passed. `server/tests/fixtures/expr/` is not in this tree, so the fixture loop does not compare files. The canonical strings are locked in `to_python_canonical`. |
| Demo builds H_2ph, shows LaTeX and Python, flags the 4 wrong builds | PASS | Browser at `site/src/blocks/demo.html`. Python: `H = g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())`, jumps `jnp.sqrt(kappa_b)*b`, `jnp.sqrt(kappa_a)*a`. LaTeX contains `a^{2} b^{\dagger}`. Clicking "wrong drive on memory" showed `drive_on_memory_not_buffer: this pushes along the ridge between the wells, so it can't make a cat`. Screenshot: `site/src/blocks/demo-screenshot.png`. |
| Keyboard-accessible block selection; colour-blind-safe palette | PASS with a note | `@blockly/keyboard-navigation@4.0.0-beta.0` does not run on Blockly 13.4.0 (peer is `blockly@^12.3.0`; the bundle calls removed `LineCursor`, and `registerNavigationDeferringToolbox` recurses). Selection is a real `<button>` toolbar: Tab, then Enter, drops the block in the first empty socket. Memory `#0072B2`, buffer `#D55E00`, rates `#009E73`, structure `#56B4E9`, jumps `#CC79A7`, each also labelled in words. |

## What the editor can express
Blocks: `a`, `a†`, `n`, `I`, `b`, `b†`, param (`g2`, `eps_d`, `kappa_b`, `kappa_a`, `kappa2`, `alpha`, `eps_z`, `eps_x`, `K`, `chi`), complex number (so `i(a†−a)` can be built), `√` of `κ_b` / `κ_a` / `κ₂` or of a number, variadic `×` and `+` (each summand has `+`/`−`), power 0–4, dagger, holders `H =` and `Jumps`.

Presets: `empty`, `h2ph_correct`, `one_mode_cat`, `wrong_drive_on_memory`, `wrong_no_dissipation`, `wrong_conversion`, `wrong_missing_hc`, `readout_z`, `state_prep_x`, `kerr`.

Serialization: ExprTree JSON (`serializeProgram` / `deserializeProgram`), Blockly XML (`saveXml` / `loadXml` / `initialXml`), Blockly state (`saveState` / `loadState`). `toPython` and `toLatex`. The equation line (`parseEquation`) accepts `g2*(a^2*bd + ad^2*b) - eps_d*(b+bd)`, `dag(x)`, `D[L]`, and the Python dialect (`@`, `.dag()`, `jnp.sqrt`, `dq.eye(N)`). Nothing is `eval`'d.

## Canonical `toPython` (for P0)
Until `server/tests/fixtures/expr/*.json` exists, this is the style:

- operators `a`, `a.dag()`, `b`, `b.dag()`, identity `dq.eye(N)`, `n_a` as `(a.dag()@a)`
- products of operators with `@`, scalars with `*`, powers expanded (`a@a`, never `**`)
- sums joined with ` + ` and ` - `
- `sqrt` prints `jnp.sqrt(...)`
- pure imaginary `1j*eps_x*(a.dag() - a)`; a general complex is `(1+2j)`
- integers print without `.0`

Locked strings:

- `g2*(a@a@b.dag() + a.dag()@a.dag()@b) - eps_d*(b + b.dag())`
- `jnp.sqrt(kappa_b)*b`
- `jnp.sqrt(kappa_a)*a`
- `jnp.sqrt(kappa2)*(a@a - alpha*alpha*dq.eye(N))`
- `1j*eps_x*(a.dag() - a)`

## Commands run
```text
cd site/src/blocks && ./node_modules/.bin/vitest run
 Test Files  2 passed (2)
      Tests  10 passed (10)
```

`npx -y vitest@2` from the repo root does not see the lane-local `jsdom` (Blockly 13 peers `jsdom>=27.4`). Use the local Vitest 2.1.9 above.

Demo: `cd site/src/blocks && ./node_modules/.bin/vite --host 127.0.0.1 --port 5183`, open `/demo.html`.

## Deps for P7
Add to `site/package.json` (this lane did not edit it):

- `blockly@13.4.0` (runtime)
- dev, for this folder's tests and demo: `vitest@2.1.9`, `jsdom@^27.4.0`, `vite@^6`, `typescript@^5.6`

Do not add `@blockly/keyboard-navigation@4.0.0-beta.0` until it supports Blockly 13.

## Records produced
None. This lane does not emit physics records.

## Deviations from the brief
- Keyboard navigation is a DOM toolbar, not the Blockly plugin. See the gate note.
- Default mount leaves the `H =` socket empty so the first keyboard insert has a hole. `loadPreset('empty')` still compiles to the number 0.
- Presets also include `readout_z`, `state_prep_x`, and `kerr`, which the level text needs and the brief's minimum list did not name.

## DECISION NEEDED
> **Q:** P0 has not committed `server/tests/fixtures/expr/*.json`. Is the canonical `toPython` style above the one `server/app/expr.py::to_python` will emit?
> **Options:** A) P0 matches these strings. B) P0 publishes fixtures and this lane updates `toPython` to them.
> **Recommendation:** A. The strings match CONTRACT §4 and the L6 show-code line.
> **Blocking?** no. Tests lock the strings. If P0's files disagree, reconcile before P-G1.

## Explain-back for Harshit
1. Why is the product a²b† and not a b†², and what physical process does each term describe?
2. Why can't the block build ε(a + a†) prepare a cat, while the buffer drive can?
3. How do we make sure learner-built Hamiltonians can't run arbitrary code on our server?

## Notes for Claude's later review
- Hermitian check is symbolic (commute a-mode past b-mode, then compare with the dagger) and numeric at Na=8 or Na=4, Nb=3, tolerance 1e-9, with every param set to 1.
- `validate(tree, modes, role)` takes an optional third argument `'jump'`. Jumps must carry a top-level `sqrt` coefficient. α² inside `√κ₂(a² − α² I)` is not required to sit under `sqrt`.
- jsdom warns that `canvas` is not installed. Blockly still injects; the browser demo is the visual check.
