# Morning note

Status: `DONE_WITH_CONCERNS`. The release is local and on GitHub only if the push section below says so. The API is not running on the Vultr VM.

## What is on `prod/release`

| Branch | SHA | Role |
|---|---|---|
| `prod/p7-integrate` | `37d9787bc4a380290f67784c5c316e7da44d76d6` | Integrated app (server, browser solver, 8 levels, blocks, tutor, Timescale, chain) |
| `prod/p8-docs` | `a28fae98a14dcca174cf8a9104f21d324c5ca7ec` | Submission text. Base of this release. Already on `origin`. |
| `prod/backboard` | `0514f95c4719a3d72845c1657ac6cbff2460c19f` | Backboard SDK memory. Merged cleanly. |
| merge | `6922440991b6f7f5de7c3c4f98e7dbe771b75ab5` | `prod/backboard` into `prod/release` |
| `prod/release` note | `e0a43140a06a194dca72204bf22fd9733659bc1b` | First morning note. |
| `prod/site-shell` | `4431a3d97a379e092cbc0478d001fe67ef846a7a` | Vite app. Merged. |
| site merge | `ddeff329ba4e68474272712102c9d3bf27c785d9` | `prod/site-shell` into `prod/release`. |

The site commit mounts `#/learn` and `#/sandbox`. Research pages are placeholders: `#/inflate`, `#/errors`, `#/readout`, and `#/verify` say the viewers ship with the physics lab and are not in this Academy bundle.

Local dev:

```text
npm --prefix site run dev
http://127.0.0.1:5173/#/learn
```

## What is live in the code

- Tutor memory uses the Backboard SDK when `BACKBOARD_API_KEY` is set, and the labeled `demo-adapter` when it is not. `BACKBOARD_MODE=off` disables memory.
- The tutor dispatches a simulator, grid, or record tool before the model answers.
- Solana stays labeled demo: `demo_mode: true`, `tx_sig: null`. No devnet transaction is invented.
- Gemini, ElevenLabs, and Tiger Data stay live only when their own keys are set. Those values stay in gitignored `server/.env`. They are not in this commit and they were not copied to the VM.

## What is not on the VM

The API is not on `64.177.55.154`. `GET http://64.177.55.154:8000/api/health` timed out after 10 seconds from this Mac (public IP `152.3.43.41`). Ports 22, 80, and 443 also time out. SSH was not retried. `academy-api` was not created. Nothing was deployed.

The site builds on this branch. Vultr is not serving the UI, and the VM was not touched again. Solana is still demo.

## Firewall to open

In the Vultr firewall for `64.177.55.154`, allow inbound TCP from `152.3.43.41` in this order:

1. Port **22**, so a later SSH session can reach the instance.
2. Port **8000**, so `http://64.177.55.154:8000/api/health` can answer after someone deploys `server.app.main:app`.

Until port 22 accepts a connection, do not expect the health URL to return 200. The root password was not changed and is not written here.

## Tests

`MPLCONFIGDIR` set to a temp dir. Python: repo `.venv`.

```text
pytest server/tests -q
66 passed, 2 skipped, 5 warnings in 32.39s
skips: test_data_leaderboard (src.linresp is not on this branch)

vitest site/src/sim      4 files, 27 passed
vitest site/src/academy  8 files, 37 passed
vitest site/src/blocks   2 files, 10 passed
vitest site/src/tutor    2 files, 7 passed
```

`npm --prefix site run build` on this branch after the site merge: exit 0 (`vite v6.4.5`, built in 8.13s). `dist/` stays gitignored. `build:single` was already exit 0 on `4431a3d` and was not run again.

## Push

GitHub already has `prod/backboard` at `0514f95c4719a3d72845c1657ac6cbff2460c19f` and the earlier `prod/release` note. This commit adds the site merge `ddeff329ba4e68474272712102c9d3bf27c785d9` (`4431a3d`) and is pushed with `prod/site-shell`. No force. `standard-track`, `main`, and tags were not pushed. Vultr was not contacted.

## Secrets

Tracked files and the commits since `origin/main` were scanned for API keys, database URLs, and the Vultr password. None are in the tree. `postgres://` appears only in redaction checks. `server/.env` is gitignored.
