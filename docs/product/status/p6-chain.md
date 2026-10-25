# Status: lane `p6-chain`

| Field | Value |
|---|---|
| State | `DONE_WITH_CONCERNS` |
| Branch | `prod/p6-chain` |
| Agent / model | Cursor Grok 4.7 |
| Started (EDT) | 2026-10-25 00:34 |
| Last update (EDT) | 2026-10-25 00:56 |
| Last commit | see `git log -1` on `prod/p6-chain` after this commit |

## Milestones
- [x] Read brief, CONTRACT, SPONSORS, LEVELS L8, HUMAN §1 row 6
- [x] Tests written (31, including the brief's §5 cases plus the offline signer)
- [x] Implementation complete
- [x] Fast tests and `tsc` pass
- [x] Live devnet mint/anchor not run: no signer was provided
- [x] Acceptance gates checked below
- [x] Explain-back questions drafted

## What is real vs demo

Real, and covered by tests:
- Soulbound mint input and the Metaplex Core **create V2** instruction (`mpl-core` 1.10.0). One plugin: `PermanentFreezeDelegate`, `frozen: true`, authority `None`. Program id `CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d`. The test decodes the instruction with `getCreateV2InstructionDataSerializer`. Nothing is sent.
- Memo instruction for `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`, text `duq-academy:<label>:<sha256>`. `Transaction.sign` and `verifySignatures()` succeed. The live sender is `sendAndConfirmTransaction` on that same instruction. It was not called.
- Devnet guard. A mainnet URL exits 1. A non-empty mainnet override exits 1 and is not honored. At boot with no signer, the default `https://api.devnet.solana.com` was accepted (the process did not log "RPC unreachable"), and no transaction was sent.
- HTTP behavior with fakes: admin token, idempotency, pubkey, rate limit, metadata, anchors, CORS, secret hygiene.

Demo, labeled, same builders, no broadcast:
- `CHAIN_MODE=demo` generates an ephemeral keypair in memory. It signs the same create and memo builders with a fixed offline blockhash. RPC send/confirm are stubbed to throw. Responses set `demo: true`, `broadcast: false`, `network: "offline-demo"`, `explorer_url: null`. They are not devnet or mainnet transactions.
- Default with no signer is **degraded**, not demo. Credential returns 503 `chain_unavailable`. The claim button is wired to that API. It does not pretend a mint succeeded.

Not done, and not faked:
- No funded devnet key, so no credential and no memo were broadcast.
- The production `label=index` anchor was not sent. That stays with the integrator after the physics freeze.
- Docker is not installed on this machine. The Dockerfile is ready for P7.

## Acceptance gates
| Gate | Result | Evidence |
|---|---|---|
| Build and tests | pass | `npx vitest run` → 12 files, 31 tests passed. `npm run build` (`tsc -p .`) exit 0. Local Node is v24.18.0; `engines` is `>=22`; the image is `node:22-slim`. |
| Degraded start | pass | No signer. Health `ready: false`. Credential 503 `chain_unavailable`. Anchor with no admin token is 503 `feature_disabled` (endpoint rule). Anchor with a token and no signer is 503 `chain_unavailable`. Transcript below. |
| Docker | not built | `docker` is absent. P7 builds `docker build -t duq-chain chain` on the VM. |
| Live devnet | pending | `npx tsx src/smoke.ts` prints `LIVE CHECK PENDING (needs funded devnet keypair)`. |
| No secrets | pass | `git grep` for a `SOLANA_SECRET_KEY_B58=` assignment under `chain` and `site` prints nothing. No keypair JSON. `git status --porcelain -- deploy server src results` prints nothing. |

### Degraded curl (port 8100, no signer, default devnet RPC)

```text
No signer configured. Credential and anchor return 503.
chain listening on 8100 mode=degraded payer=none

GET /api/chain/health
HTTP/1.1 200 OK
{"ok":true,"cluster":"devnet","payer":null,"balance_sol":null,"ready":false,"mode":"degraded","broadcast":false}

POST /api/chain/credential
HTTP/1.1 503 Service Unavailable
{"error":{"code":"chain_unavailable","message":"chain unavailable"}}

POST /api/chain/anchor   (no admin token)
HTTP/1.1 503 Service Unavailable
{"error":{"code":"feature_disabled","message":"feature disabled"}}

POST /api/chain/anchor   (admin token set, still no signer, port 8102)
HTTP/1.1 503 Service Unavailable
{"error":{"code":"chain_unavailable","message":"chain unavailable"}}
```

Mainnet URL, before listen: `RPC host "api.mainnet-beta.solana.com" is not devnet. Refusing to start.` exit 1.
Mainnet override set, before listen: `Refusing to start because a mainnet override is present. This service is devnet-only.` exit 1.

### Demo curl (CHAIN_MODE=demo, port 8101)

This signature was produced locally. It was not broadcast. Do not treat it as a devnet or mainnet transaction.

```text
DEMO adapter. offline-demo: signed locally and not broadcast payer=<ephemeral>
chain listening on 8101 mode=demo

POST /api/chain/credential → 200
{"asset_address":"Fx16r9yyob87zR6yBAqHtsyJee9jLMDkq1MWise549ke","tx_sig":"2X9aeYf3ixAzacAbQ4T6EZxVKuWx7X8oTUxC5H3BrELs5A2VM2ixgb185FBnMzeBbrcnnxCz2vFgu1i9J3YfYNij","explorer_url":null,"custodial":true,"tx_url":null,"demo":true,"broadcast":false,"network":"offline-demo","notice":"offline-demo: signed locally and not broadcast"}
```

`npx tsx src/smoke.ts --demo` also signs one credential and one `label=smoke` memo, checks both signatures, and prints `broadcast: false`. It does not print explorer links.

## Resolved versions
`hono` 4.13.13, `@hono/node-server` 2.1.5, `@metaplex-foundation/umi` 1.6.0, `@metaplex-foundation/umi-bundle-defaults` 1.6.0, `@metaplex-foundation/mpl-core` 1.10.0, `@solana/web3.js` 1.99.0, `bs58` 6.0.0. Dev: `typescript` 5.9.3, `tsx` 4.23.15, `vitest` 5.0.5, `@types/node` 26.6.5.

## For P7
- Compose for `chain`: volume `chaindata:/app/data`, `expose: ["8100"]`, `restart: always`. CONTRACT §2: the chain container reads `/opt/academy/chain.env` (`SOLANA_SECRET_KEY_B58`, `SOLANA_RPC_URL`, `ADMIN_TOKEN`, `API_HOST`). The api container's env file must not contain `SOLANA_SECRET_KEY_B58`. If they still share one file, blank that variable on `api`.
- `GET /api/chain/health` is the `features.chain` probe. `ready: true` means a signer is loaded, the RPC is devnet, and the balance is at least 0.02 SOL. Demo mode reports `ready: false` and `cluster: "offline-demo"`.
- L8 completion calls `mountClaimCredential(el, { apiBase, learnerId, alias, levelsPassed, score?, l8PayloadHash? })` from `site/src/chain/index.ts`.
- Real Research calls `mountAnchorsPanel(el, { apiBase })`.
- No new site npm dependencies.
- Live check, once a devnet key is in `server/.env` and not committed: from `chain/`, `npx tsx --env-file=../server/.env src/smoke.ts`. That mints one custodial credential (alias `smoke`) and one memo with `label=smoke`. It does not send `label=index`.

## Additive fields
- Request `l8_payload_hash` (64 lowercase hex). If omitted, `content_hash` is sha256 of canonical JSON `{"alias","levels_passed","score"}` with those keys in that order. The credential request still has no L8 payload body.
- Response `tx_url` on a broadcast credential. Demo sets `tx_url` and `explorer_url` to null.
- `demo`, `broadcast`, `network`, `notice` on credential and anchor responses.
- `GET /api/chain/meta/<asset>.json`, `GET /api/chain/meta/badge.svg`, `GET /api/chain/health`.
- `CHAIN_MODE=demo` selects the offline adapter. `CHAIN_DATA_DIR` overrides the data directory (default `data/`, Docker `/app/data`).

## Commands run (most recent first)
```text
env -u SOLANA_SECRET_KEY_B58 ADMIN_TOKEN=local-dev-token PORT=8102 npx tsx src/server.ts
curl POST /api/chain/anchor → 503 chain_unavailable

env -u SOLANA_SECRET_KEY_B58 npx tsx src/server.ts
CHAIN_MODE=demo PORT=8101 npx tsx src/server.ts
curl health, credential, anchor, badge.svg

SOLANA_RPC_URL=https://api.mainnet-beta.solana.com npx tsx src/server.ts → exit 1
ALLOW_MAINNET=1 npx tsx src/server.ts → exit 1
npx tsx src/smoke.ts → LIVE CHECK PENDING
npx tsx src/smoke.ts --demo → broadcast: false, both signatures verified

npx vitest run → 12 files, 31 passed
npm run build → tsc exit 0
node --version → v24.18.0
docker → not installed
```

## Records produced
None. No devnet transaction was sent. No `results/` record was anchored.

## Figures / arrays produced
- `chain/assets/badge.svg`, served at `/api/chain/meta/badge.svg`.

## Jobs to queue
| Name | Command (from `chain/`) | RAM est. (GB) | Wall est. | Outputs |
|---|---|---|---|---|
| Live devnet smoke | `npx tsx --env-file=../server/.env src/smoke.ts` after a funded devnet key exists | < 1 | 1–2 min | explorer links in this status file. Not `label=index`. |
| Docker image | `docker build -t duq-chain chain` on the VM | < 1 | a few min | image `duq-chain` |

## Deviations from the brief (and why)
- No Solana key was provided. The live path is implemented (`sendCreateAndConfirm`, `broadcastMemo`, `smoke.ts`) and unrun. `CHAIN_MODE=demo` is an extra adapter so the same builders can be signed offline without claiming a landed transaction.
- `mpl-core` 1.10's `create` emits **create V2**. The soulbound test decodes with `getCreateV2InstructionDataSerializer`. The plugin is still PermanentFreezeDelegate, frozen, authority None.
- A mainnet override is recognized only to refuse startup. It is not an escape hatch.
- Local Node is v24.18.0, not v22. The image still uses `node:22-slim`.
- Extra files inside the lane: `chain/src/demo.ts`, `chain/test/harness.ts`, `chain/test/demo.test.ts`.
- Demo idempotency keys are tagged so a demo record is not later returned as a live mint. Live keys stay `sha256(learner_id + ":" + sorted levels)`.
- `learner_id` is not written to metadata, chain payloads, or logs.

## DECISION NEEDED
None. The brief's no-keypair fallback is the one in use: build, test, and mark the live check pending.

## Explain-back for Harshit (questions only)
1. What makes the credential soulbound at the program level, rather than just in our UI? With PermanentFreezeDelegate and authority None, who could ever thaw or transfer it? And what does "custodial" mean for a learner without a wallet?
2. What exactly does the Memo anchor of `sha256(results/index.json)` prove to a judge, and what doesn't it prove? How would someone check a given results file against it?
3. Name every safeguard that keeps this service off mainnet and away from real funds. Why do the credential and the anchor deliberately involve no tokens and no payments?

## Notes for Claude's later review
- Do not paste the demo `tx_sig` into a devnet explorer and call it a landed transaction. `explorer_url` is null on purpose.
- The two failures before the green run were a base58 decoder that double-counted an all-zero key, and the override scan matching its own search string. Neither tolerance was loosened.
- `npm test` does not touch the network. The degraded boot did call `getGenesisHash` on the public devnet RPC and then refused to mint.
