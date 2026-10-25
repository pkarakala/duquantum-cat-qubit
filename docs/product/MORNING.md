# Morning note

Status: `DONE_WITH_CONCERNS`. There is no public URL. Do not invent one.

GitHub branch for the release is `prod/release` (`4bdc4cf`). The lesson-page pass lives on `prod/ux` until it is merged. `standard-track` was not touched.

The video was not recorded. The 60-second live demo and the 45-second video script are the same file: `docs/product/demo_script.md`.

## Run it locally

```text
npm --prefix site run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/#/learn`. Lessons are `#/learn/L1` through `#/learn/L8`. The block editor is `#/sandbox`. `#/inflate`, `#/errors`, `#/readout`, and `#/verify` are placeholders.

## Sponsors

Live: Gemini (tutor), ElevenLabs TTS, Timescale, and Backboard. Their keys stay in gitignored `server/.env` and are not in the commit.

Demo: Solana (`demo_mode: true`, `tx_sig: null`, no real funds) and Vultr (the API is not deployed on the VM). A stored lesson result is badged MOCK. A server answer is not proof that Vultr is the host.

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

The site commit mounts `#/learn` and `#/sandbox`. Research pages are placeholders and are not in this Academy bundle.

## What is live in the code

- Gemini, ElevenLabs TTS, Timescale, and Backboard are the live sponsor paths. Backboard uses the SDK when `BACKBOARD_API_KEY` is set, and the labeled `demo-adapter` when it is not. `BACKBOARD_MODE=off` disables memory.
- The tutor dispatches a simulator, grid, or record tool before the model answers.
- Solana and Vultr stay demo. No devnet transaction is invented. Nothing was copied to the VM.

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

GitHub has `prod/release` at `4bdc4cf`. That commit includes the earlier site merge `ddeff329`. The lesson-page pass is `prod/ux`, pushed separately, and is not `prod/release` until someone merges it. No force. `standard-track`, `main`, and tags were not pushed from this pass. Vultr was not contacted. There is still no public URL. The video was not recorded; use `docs/product/demo_script.md`.

## Secrets

Tracked files and the commits since `origin/main` were scanned for API keys, database URLs, and the Vultr password. None are in the tree. `postgres://` appears only in redaction checks. `server/.env` is gitignored.
