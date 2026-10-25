# Morning ledger

Status: local Academy only. There is no public URL. Do not invent one.

Integrated code tip: `58e1499` (`report a late tutor sim and keep its cache`). It moved past `f281878`. This note is the commit on top of `58e1499`.

## Run it locally

Academy UI only:

```text
http://127.0.0.1:5180/#/learn
```

The API is `server.app.main:app`. Env files are gitignored and are not in any commit:

- `.worktrees/prod-release/server/.env`
- `.worktrees/integrated/server/.env`

The video was not recorded. Script: `docs/product/demo_script.md`.

`#/inflate`, `#/errors`, `#/readout`, and `#/verify` are placeholders.

## Pushed

Already on `origin` before this note:

| Branch | SHA |
|---|---|
| `prod/release` | `a1e8192` |
| `prod/ux` | `450cf2e` |
| `prod/linresp` | `ebacd9e` |
| `prod/backboard` | `0514f95` |
| `prod/site-shell` | `4431a3d` |
| `std/l1-spectral` | `d5d9709` |
| `std/l2a-gamma-z` | `3f28a84` |
| `std/l3-prep` | `96a9ee3` |
| `std/l4b-tradeoff` | `358d3a3` (includes `fc1b708`; tip is the lowercase SNR commit) |
| `std/l4c-capstone` | `029253d` |
| `std/l2b-gamma-x` | `20e6e86` (branch is on origin; the bit-flip curve is still pending) |
| `integrated` | `58e1499` |

Pushed this pass (no force). Untracked files were left uncommitted:

| Branch | SHA |
|---|---|
| `review/l0-core-r1` | `c69d6ea` |
| `review/l0-tools-r1` | `ed6789a` |
| `std/l0-core` | `effc210` |
| `std/l0-tools` | `539046c` |
| `std/l4a-readout` | `c6707ea` |
| `std/l5-circuit` | `34c5f99` |
| `std/l6-lab` | `2e15f03` |
| `std/l7-docs` | `47c0fd5` |
| `std/l8-felis` | `47c0fd5` |

`std/l4c-capstone` was already at `029253d` on origin. This pass only set its upstream.

Not pushed: `standard-track` (`47c0fd5`) is ahead 20 and behind 5 of `origin/standard-track` (`b808ed4`). The push was rejected as non-fast-forward. No force. `main` and `intro-track-tasks` were left alone. `server/.env` was not committed.

## Tests

On the earlier integrated tip, `pytest server/tests` was 66 passed, 2 failed. `test_cache_hit` returned 504 after 8s. The tutor test raised `IndexError`.

`58e1499` is that fix, and it is already on origin. A targeted rerun of `test_cache_hit`, `test_timeout`, and two tutor tests passed: 4 passed in 26.77s, on the code in that commit. A full `pytest server/tests` green run after `58e1499` was not seen. Full-suite confirmation is still in progress.

## Pending

- l2b bit-flip curve
- l4a readout records
- l5 circuit 10×8 validation (smoke was 7.4% low)
- l4b ε grid (ids now lowercase `t`; numbers not computed)
- l4c two-mode check
- l3 32×12 production
- l6 live lab data
- l7 physics docs
- l8 Felis

Vultr `64.177.55.154` ports 22, 80, and 443 time out. Nothing was deployed.

Eigen jobs above about 4 GB are queued, not run.

## Physics that finished

- Γ_Z matches 2κ_a α² coth(2α²) within 0.54% from α = 1 to 2.7.
- Γ_X at α = 2.1 is 3.88e-7 /µs on 28×8. 20×6 is the truncation trap (7.61e-6).
- SVD vs square SNR is 0.172 vs 0.038 (4.49×), in linear response only.

## Secrets

This note has no API keys and no database password. `server/.env` stays gitignored.
