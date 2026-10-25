# Status: lane `p7-integrate`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p7-integrate` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 01:00 |
| Last update (EDT) | 2026-10-25 01:16 |

## Merged

| Lane | SHA | Result |
|---|---|---|
| `prod/p0-server` | `4b5ce58` | merged |
| `prod/p1-ts-sim` | `33e8791` | merged |
| `prod/p2-academy` | `8dfe627` | merged |
| `prod/p3-blocks` | `46c95a4` | merged |
| `prod/p4-tutor` | `8ae1e90` | merged |
| `prod/p5-data` | `9ae88f2` | merged. Kept p5's `server/app/data/__init__.py`. |
| `prod/p6-chain` | `2a728a5` | merged |

`prod/p4-tutor` was dirty and even with the base when the first pass started, so it was skipped then. It later committed `8ae1e90` with a clean worktree and was merged. Placeholder `__init__.py` files from p0 were replaced by the tutor, memory, and voice packages.

No push. `standard-track` was not written. `src/model.py` was not edited. The `eps_x` compat shim in `server/app/sim.py` is still in place.

## Wired

- L1–L4 and L8 call the in-browser Crank–Nicolson solver. A worker failure falls through to `simulate` before any mock preset. A real solver result is badged in-browser, not MOCK.
- L6 posts `POST /api/sim/expr` when `VITE_API_BASE` is set, then falls back to the named preset. A live response is badged `Live · Vultr dynamiqs`.
- The block editor's Run button posts the ExprTree to `POST /api/sim/expr`. `toPython` matches `server/tests/fixtures/expr/*.json`.
- Finished level runs post `POST /api/runs`. With no Tiger URL the row still reaches the in-process sink and returns `{ok: true}`. An empty body stays `503 feature_disabled`.
- The L8 credential slot calls `mountClaimCredential` (`POST /api/chain/credential`). With no Solana key the API answer is `demo_mode: true`, `tx_sig: null`.
- `POST /api/tutor` uses `server.app.sim` (`label: p0`), not `mock-sim`. The number guard and ElevenLabs voice routes stay. With no Backboard key, memory is the labeled `demo-adapter`.
- Docker was not built. It is not installed here.

## Verification

```text
pytest server/tests -q
65 passed, 2 skipped, 1 warning in 30.64s
skips: test_data_leaderboard (src.linresp is not on this branch)

vitest site/src/sim     4 files, 27 passed
vitest site/src/academy 8 files, 37 passed
vitest site/src/blocks  2 files, 10 passed
vitest site/src/tutor   2 files, 7 passed
```

Live L1, in process, no keys invented:

```text
tutor_client p0
L1 one_mode source live-one-mode n0 4.407 (N=12) engine dynamiqs 0.3.7
POST /api/sim/one_mode 200 engine dynamiqs 0.3.7
POST /api/chain/credential 200 demo_mode true, tx_sig null, asset_address null
POST /api/memory/event 200 source demo-adapter, demo_mode true
POST /api/runs 200 {ok: true}
browser simulate L1 n 4.410 engine ts-cn
```

## Concerns

- No Vultr host, Solana key, or Backboard key. Those three stay labeled demo. Gemini and ElevenLabs are not called from this lane.
- `src.linresp` is absent, so the two leaderboard recompute tests skip.
- `l0-core` is not on this branch, so `_two_mode_compat` still supplies `eps_x`.
- Docker is not installed, so the image was not built.
- Public URL, offline `file://` dry run, Grok Bot, and think-aloud are not done. This pass is the local wiring, not the P-G3 freeze.

## DECISION NEEDED

None blocking.
