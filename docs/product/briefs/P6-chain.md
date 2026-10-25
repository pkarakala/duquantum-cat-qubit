# Brief `p6-chain`: Solana devnet soulbound credential, results-hash anchor, and the site claim UI

> **Paste into a new Cursor agent (worktree mode, base `standard-track`):** "You are product lane `p6-chain`. Read `AGENTS.md`, `docs/product/CONTRACT.md`, `docs/product/LEVELS.md`, `docs/product/SPONSORS.md` and `docs/product/briefs/P6-chain.md`, then execute the brief exactly. Keep `docs/product/status/p6-chain.md` updated."

| Lane | Branch | Depends on | Suggested Cursor model | Time cap | Start → target (EDT) |
|---|---|---|---|---|---|
| `p6-chain` | `prod/p6-chain` (from `standard-track`) | The P0 compose: `deploy/docker-compose.yml` has a `chain` service built from `../chain`, and Caddy proxies `/api/chain/*` to `chain:8100` with the path kept. Code and tests don't need it to start. The live check needs Harshit's funded devnet keypair (HUMAN.md §1 row 6). | standard (Sonnet-class) | 3 h | about 1:00 AM → **4:00 AM Sun** (before P-G2 at 4:30 AM: "a devnet credential is minted (or custodially); the results-hash anchor transaction exists") |

## 1. Goal and why
Solana is a **core** sponsor. The framing is **verifiable learning plus verifiable science**, which extends the project's "every number traceable" provenance theme to a public timestamp. You build three things:
1. **A credential:** a **soulbound Metaplex Core asset**, "Cat Qubit Architect", minted on **devnet** when a learner finishes L8. It goes to their Phantom wallet if they have one; otherwise it is minted custodially to the server's address.
2. **An anchor:** a **Memo-program transaction** carrying `sha256(results/index.json)`, so the Real Research wing can show "verified results, anchored on Solana at <time>".
3. **The site modules** to claim the credential and to display the anchors.

The rules:
- No tokens, no payments, **devnet only**.
- Chain failures never block learning: the UI shows "credential pending: retry" (spec §7).

## 2. Read first
- `docs/product/CONTRACT.md`:
  - §0: secrets live only in `.env`; learners are pseudonymous.
  - §1: you own `chain/**` and `site/src/chain/**`.
  - §2: Node 22, `@metaplex-foundation/umi`, `umi-bundle-defaults`, `mpl-core`, `@solana/web3.js`, `hono`; env `SOLANA_RPC_URL=https://api.devnet.solana.com`, `SOLANA_SECRET_KEY_B58` (chain service only), `ADMIN_TOKEN`, `ALLOWED_ORIGINS`.
  - §3: the three chain rows, and the error shape `{"error":{"code","message"}}`.
- Spec `docs/superpowers/specs/2026-10-24-cat-qubit-academy-design.md`: §5 (the Solana row), §6 (completion and anchor flow), §7, §9 (no mainnet, no payments).
- `docs/product/SPONSORS.md` (Solana). `docs/product/LEVELS.md` L8 ("On completion"). `docs/product/HUMAN.md` §1 row 6 and §2.
- `docs/product/briefs/P0-server.md` §6.7: the compose and the Caddyfile. Your service listens on **8100** and receives full `/api/chain/...` paths.
- External docs:
  - Metaplex Core soulbound guide: https://www.metaplex.com/docs/smart-contracts/core/guides/create-soulbound-nft-asset
  - The Memo program, `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`.
  - The Solana explorer `?cluster=devnet` URLs.

## 3. Allowlist (touch nothing else)
- **`chain/**`:**
  - Project files: `package.json`, `package-lock.json`, `tsconfig.json`, `vitest.config.ts`, `Dockerfile`, `.dockerignore`, `.gitignore` (`node_modules/`, `dist/`, `data/*`, `!data/.gitkeep`, `.env`).
  - Source: `src/{server,app,config,guard,validate,store,ratelimit,mint,memo,meta,smoke}.ts`.
  - Also `assets/badge.svg` and `test/*.test.ts`.
- **`site/src/chain/**`:** `api.ts`, `format.ts`, `claim.ts`, `anchors.ts`, `index.ts`. Plain TS, no framework, **no new npm deps**.
- **Status:** `docs/product/status/p6-chain.md`.
- **Never edit:**
  - `deploy/**` (P0's, then P7's) and `server/**`.
  - `site/package.json`, `site/src/main.ts`, `site/index.html` and `site/vite*.config.ts` (l6's, then P7's).
  - `results/**` and CONTRACT.

  List the compose and wiring changes you need in status instead.

## 4. Interfaces you implement / rely on

### Endpoints
They follow CONTRACT §3 exactly. Hono (`hono` + `@hono/node-server`) on port 8100, using the full paths. CORS comes from `hono/cors`, with origins `ALLOWED_ORIGINS.split(",")` plus `"null"` (the `file://` build).

**`POST /api/chain/credential`**
- Body: `{learner_id, alias, wallet_pubkey?, levels_passed, score?, l8_payload_hash?}`.
  - `learner_id`: a UUID v4.
  - `alias`: `^[A-Za-z0-9 _.\-]{1,24}$`.
  - `wallet_pubkey`: base58 that decodes to exactly 32 bytes.
  - `levels_passed`: a subset of `L1`–`L8` that **must include `L8`**; dedupe and sort it.
  - `score`: finite.
  - `l8_payload_hash`: *additive*, 64 lowercase hex characters.
- Response: `{asset_address, tx_sig, explorer_url, custodial}`.
  - `explorer_url = https://explorer.solana.com/address/<asset>?cluster=devnet`.
  - *Additive* `tx_url = https://explorer.solana.com/tx/<sig>?cluster=devnet`.

**`POST /api/chain/anchor`**
- Requires header `X-Admin-Token`, compared in constant time (`crypto.timingSafeEqual` on sha256 digests).
  - A missing or wrong token returns 401 `unauthorized`.
  - If `ADMIN_TOKEN` is unset, return 503 `feature_disabled`.
- Body: `{sha256: ^[0-9a-f]{64}$, label: ^[a-z0-9._-]{1,32}$}`.
- Memo text: exactly `duq-academy:<label>:<sha256>`.
- Response: `{tx_sig, explorer_url: https://explorer.solana.com/tx/<sig>?cluster=devnet}`.

**`GET /api/chain/anchors`** → `{anchors:[{label, sha256, tx_sig, explorer_url, ts}]}`, newest first, with `ts` in ISO-8601 UTC (`Z`).

**Additive endpoints:**
- `GET /api/chain/meta/<asset>.json` serves the metadata, and is the asset's `uri`.
- `GET /api/chain/meta/badge.svg`.
- `GET /api/chain/health` returns `{ok, cluster:"devnet", payer, balance_sol, ready}`. `payer` is the public key, which is fine to show. P0 or P7 can probe it for `features.chain`.

**Errors:**

| Status | Code | When |
|---|---|---|
| 422 | `bad_request` | Validation |
| 401 | `unauthorized` | Bad or missing admin token |
| 404 | `not_found` | Unknown resource |
| 429 | `rate_limited` | Rate limit hit |
| 503 | `chain_unavailable` | RPC down, guard not yet passed, or balance < 0.02 SOL |
| 502 | `tx_failed` | Send or confirm failed after 3 tries with backoff |

### Minting (`mint.ts`)
1. Set up Umi: `createUmi(SOLANA_RPC_URL).use(mplCore()).use(keypairIdentity(umi.eddsa.createKeypairFromSecretKey(bs58.decode(SOLANA_SECRET_KEY_B58))))`.
2. Generate the asset: `asset = generateSigner(umi)`.
3. Write the metadata **before** minting, to `data/meta/<asset>.json`.
4. Mint: `create(umi, buildCreateInput({asset, owner, uri})).sendAndConfirm(umi)`, then convert the signature to base58 (`base58.deserialize(sig)[0]`).

`buildCreateInput` is **pure** and returns:

`{ asset, owner, name: "Cat Qubit Architect", uri: \`${PUBLIC_BASE}/api/chain/meta/${asset.publicKey}.json\`, plugins: [{ type: "PermanentFreezeDelegate", frozen: true, authority: { type: "None" } }] }`
- That plugin makes the asset **soulbound**: permanently frozen, with no authority that can thaw it.
- `PUBLIC_BASE` is `https://${API_HOST}` (the same `API_HOST` that Caddy uses), or `http://localhost:8100` when it is unset.
- `owner` is `wallet_pubkey` when given (`custodial: false`). Otherwise it is the server's public key (`custodial: true`).

### Metadata
`{name, symbol:"DUQ", description, image: PUBLIC_BASE + "/api/chain/meta/badge.svg", attributes:[...]}`
- `description`: "Completed Cat Qubit Academy (8 levels). Devnet credential, non-transferable."
- `attributes`, each as `{trait_type, value}`:
  - `levels_passed`: `"L1,…,L8"`;
  - `score`;
  - `alias`;
  - `issued_at`: ISO-8601 UTC;
  - `content_hash`: `l8_payload_hash` when given, else the sha256 of the canonical JSON `{"alias","levels_passed","score"}` (sorted keys).

  The CONTRACT credential request carries no L8 payload. Note this in status.
- **The `learner_id` never appears in metadata, on chain or in any log.**

### Idempotency (`store.ts`)
- Key = `sha256(learner_id + ":" + levels_passed.join(","))`, with the levels sorted.
- `data/credentials.json` maps key → response. A repeat request returns the stored response (200) and **never mints twice**.
- Concurrent duplicates share one in-flight promise.
- `data/anchors.json` holds the anchor list.
- Every write is atomic: write to a tmp file, then rename.
- In Docker, `data/` is the volume `/app/data`.

### Memo (`memo.ts`, `@solana/web3.js` v1)
- Build the instruction: `new TransactionInstruction({ programId: new PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"), keys: [{ pubkey: payer.publicKey, isSigner: true, isWritable: false }], data: Buffer.from(memo, "utf8") })`.
- Send it with `sendAndConfirmTransaction(connection, new Transaction().add(ix), [payer], { commitment: "confirmed" })`.
- The payer is `Keypair.fromSecretKey(bs58.decode(...))`.

### Devnet guard (`guard.ts`)
`assertDevnet(rpcUrl, getGenesisHash)` allows the URL only if one of these holds:
- the URL host contains `devnet` **and** `getGenesisHash()` equals devnet's `EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG`;
- the host is `127.0.0.1` or `localhost` (a local test validator).

Anything else **refuses to start**: exit 1, with a message that contains no secrets. The only override is `ALLOW_MAINNET`, which **must never be set anywhere**; a test enforces this.
- If the RPC is unreachable at startup, start degraded: credential and anchor return 503 `chain_unavailable`, and the guard re-checks before each transaction.

### Secrets and limits
- **The secret key** is read once from env. It is **never** logged, returned, written to disk or put in an error message. Only the payer public key may be logged.
- **Rate limits** (`ratelimit.ts`; in memory, sliding window). The key is the first `X-Forwarded-For` entry, set by Caddy, else the socket address.
  - Credential: **5 per hour per IP**.
  - Anchor: 10 per hour.
- **App factory:** `createApp(deps)`, where `deps = {mint, sendMemo, getGenesisHash, getBalance, store, now, config}`. Tests inject fakes and never touch the network.

### Site modules (`site/src/chain/`)
P7 wires these in: the L8 completion screen and the Real Research wing.
- **`api.ts`:** `claimCredential(apiBase, body, {timeoutMs: 30000})` and `listAnchors(apiBase)`, both returning typed results or `{error}`.
- **`format.ts`** (pure functions): `explorerAddressUrl`, `explorerTxUrl`, `shortHash(h)` (the first 12 hex characters plus "…"), `isBase58Pubkey`.
- **`claim.ts`:** `mountClaimCredential(el, {apiBase, learnerId, alias, levelsPassed, score?, l8PayloadHash?})`.
  - Two buttons: "Connect Phantom (optional)" and "Claim without a wallet".
  - Connect: if `window.phantom?.solana?.isPhantom`, call `await connect()` and use `publicKey.toString()`. **No signing is needed**, because the server pays and mints.
  - Without a wallet: the custodial path.
  - States: idle → minting → done, or pending.
    - Done shows the explorer link, plus "held for you by the Academy" when custodial.
    - Pending shows "credential pending: retry". It saves the request to localStorage `duq.chain.pending` and retries on the next mount.
  - It never blocks the level flow.
- **`anchors.ts`:** `mountAnchorsPanel(el, {apiBase})` shows the label, the short hash, the local time and the explorer link for each anchor.
  - It caches the last list in localStorage.
  - Offline, it shows the cached list with an "offline" badge, or "anchors unavailable offline".
- **`index.ts`:** re-exports.

## 5. Tests to write FIRST (TDD; vitest; RPC, Umi sends and time are all mocked)
Commit them failing ("tests first").
1. **`guard.test.ts`.**
   - Mainnet (`https://api.mainnet-beta.solana.com`) and testnet URLs throw.
   - A devnet URL with the devnet genesis hash passes. A devnet-looking URL with the mainnet genesis hash `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d` throws.
   - Localhost passes.
   - `deploy/docker-compose.yml`, `server/.env.example` and every `chain/**` file (skip any that are missing) contain no `ALLOW_MAINNET=` assignment.
2. **`soulbound.test.ts`.**
   - `buildCreateInput` returns exactly one plugin, `{type:"PermanentFreezeDelegate", frozen:true, authority:{type:"None"}}`, plus `name === "Cat Qubit Architect"` and a `uri` under `/api/chain/meta/`.
   - Also build the real transaction with `createUmi("http://127.0.0.1:8899").use(mplCore())` and a generated identity, without sending it:
     - the first instruction's `programId` equals `MPL_CORE_PROGRAM_ID`;
     - decoding its data with the generated serializer that `create` emits (`getCreateV1InstructionDataSerializer` or the V2 one) shows the PermanentFreezeDelegate plugin with `frozen: true`.
   - If decoding turns out to be impractical, document why and keep the input test.
3. **`admin.test.ts`.**
   - An anchor request with no header gets 401; a wrong token gets 401.
   - The right token gets 200, and the fake `sendMemo` receives `duq-academy:index:<hash>`.
   - With `ADMIN_TOKEN` unset, the response is 503.
   - A bad `sha256` or `label` gets 422.
4. **`idempotency.test.ts`.**
   - The same learner and levels twice (in any order) mints once and returns identical bodies.
   - Different levels mint again.
   - Two concurrent identical requests mint once.
   - The store survives an app restart (it is file-backed, using a tmp dir).
5. **`pubkey.test.ts`.**
   - Invalid base58, a 31-byte key and `""` each get 422.
   - A valid key becomes the owner, with `custodial: false`.
   - No key makes the payer the owner, with `custodial: true`.
   - `levels_passed` without `L8` gets 422.
6. **`ratelimit.test.ts`.**
   - The 6th credential from one IP within an hour gets 429 `rate_limited`.
   - Another IP is unaffected.
   - The fake clock resets the window after 1 h.
7. **`meta.test.ts`.**
   - After a mint, the metadata has `levels_passed`, `score`, `alias`, `issued_at` (ISO `Z`) and `content_hash` (64 hex).
   - The JSON never contains the `learner_id` string.
   - An unknown asset returns 404.
8. **`anchors.test.ts`.** After 2 anchors, GET returns both, newest first, with tx explorer URLs and ISO timestamps.
9. **`secrets.test.ts`.**
   - Start the app with a fake secret, spying on `console.*` and capturing every response body.
   - The secret string never appears anywhere.
   - `/api/chain/health` shows only the payer public key.
10. **`cors.test.ts`.** `Origin: null` and the listed origins are allowed; any other origin gets no allow header.
11. **`site_format.test.ts`.** Imports `../../site/src/chain/format.ts` by relative path (the site's vitest config is l6's or P7's) and checks the explorer URLs, `shortHash` and `isBase58Pubkey`.

## 6. Method, step by step
1. **Set up.**
   - Create the branch and the status file ("started"). Run `node --version` (expect 22.x).
   - In `chain/`, run `npm init -y` and set `"type":"module"`, `"engines":{"node":">=22"}`.
   - Scripts:
     - `dev` = `tsx watch src/server.ts`
     - `build` = `tsc -p .`
     - `start` = `node dist/server.js`
     - `test` = `vitest run`
     - `smoke:devnet` = `tsx src/smoke.ts`
   - Install exact versions: `npm i --save-exact hono @hono/node-server @metaplex-foundation/umi @metaplex-foundation/umi-bundle-defaults @metaplex-foundation/mpl-core @solana/web3.js@1 bs58` and `npm i -D --save-exact typescript tsx vitest @types/node`.
   - Record the resolved versions in status, and commit the lockfile.
2. **Tests.** Write the §5 tests and commit "tests first".
3. **Core modules, with fakes:** `config.ts` (env parsing; no secret in `toString`), `guard.ts`, `validate.ts`, `store.ts`, `ratelimit.ts`, `meta.ts`, then `app.ts` routes. Tests 1 and 3–11 go green.
4. **Real chain calls:** `mint.ts` and `memo.ts`. Test 2 goes green.
5. **Server.** `server.ts` wires the real deps and runs the guard at boot. With no keys set, `npm run dev` must start degraded and return 503 `chain_unavailable`. Curl this.
6. **`chain/Dockerfile`:**
   - Base `node:22-slim`, `WORKDIR /app`.
   - `npm ci`, `npm run build`, `npm prune --omit=dev`.
   - Create `/app/data` owned by `node`, then switch to `USER node`.
   - `EXPOSE 8100`, `HEALTHCHECK` on `/api/chain/health`, `CMD ["node","dist/server.js"]`.
   - `.dockerignore`: `node_modules`, `data`, `.env`, `dist`.
   - Build it with `docker build -t duq-chain chain` if Docker exists; otherwise P7 builds it on the VM.
7. **Site modules** (`site/src/chain/`). Keep the logic in `format.ts` and `api.ts`, with thin DOM code.
8. **Live devnet check** (only once Harshit says the keypair is funded and in `server/.env`; never print, copy or commit it):
   - Run `npx tsx --env-file=../server/.env src/smoke.ts`. It:
     1. runs the guard;
     2. checks the balance;
     3. mints **1 custodial credential** (a fresh UUID, alias "smoke", L1–L8);
     4. sends **1 anchor** with `label=smoke`, over the sha256 of `results/index.json` if that file exists, else of the string `duq-academy smoke`;
     5. reads the asset back with `fetchAsset(umi, addr)` and asserts `permanentFreezeDelegate.frozen === true` with authority `None`;
     6. tries a `transfer` and expects it to **fail**;
     7. prints the explorer links.
   - Paste the links and the failed-transfer error into status.
   - **The real results anchor** (`label=index` over `sha256(results/index.json)`) is the integrator's job after the physics freeze (spec §6). Don't send it yourself.

## 7. Outputs
- **The service:** `chain/` builds, tests and runs on :8100. Data files are git-ignored.
- **The site modules:** `site/src/chain/` (`claim`, `anchors`, `api`, `format`, `index`).
- **Status, including what P7 needs:**
  - compose additions: `chaindata:/app/data` volume, `env_file: /opt/academy/.env`, `expose: ["8100"]`, `restart: always`;
  - that the api container should blank `SOLANA_SECRET_KEY_B58`, since it shares the env file;
  - that the `/api/chain/health` probe is available for `features.chain`;
  - the mount points: the L8 completion screen calls `mountClaimCredential`, and the Real Research wing calls `mountAnchorsPanel`;
  - no new site npm deps.

## 8. Acceptance gates
1. **Build and tests.** `npm test` is all green and `npm run build` is clean (`tsc` strict, no errors).
2. **Degraded start.** A local `npm run dev` with no keys starts degraded: health reports `ready:false`, and credential and anchor return 503 `chain_unavailable` with the error shape. Paste the curl transcript.
3. **Docker.** `docker build` succeeds, or status says Docker is unavailable and P7 builds on the VM.
4. **Live, on devnet:**
   - 1 credential and 1 anchor exist, and their explorer links open with `?cluster=devnet`.
   - The asset reads back as permanently frozen with authority None.
   - A transfer attempt fails.

   If there are no keys yet, write "LIVE CHECK PENDING (needs funded devnet keypair)".
5. **No secrets.**
   - `git grep -nE "SOLANA_SECRET_KEY_B58\s*=\s*\S" -- chain site` prints nothing.
   - No keypair JSON is committed.
   - `git status --porcelain -- deploy server src results` prints nothing.

## 9. Commands
```powershell
git switch -c prod/p6-chain standard-track
Copy-Item docs/plan/status/_TEMPLATE.md docs/product/status/p6-chain.md
node --version                                     # v22.x
Set-Location chain
npm install
npm test
npm run build
npm run dev                                        # second terminal: the curls below
Invoke-RestMethod http://localhost:8100/api/chain/health
Invoke-RestMethod -Method Post http://localhost:8100/api/chain/credential -ContentType "application/json" -Body '{"learner_id":"3f1c2b9e-8a4d-4c2e-9b7a-1d2e3f4a5b6c","alias":"test","levels_passed":["L1","L2","L3","L4","L5","L6","L7","L8"]}'
npx tsx --env-file=../server/.env src/smoke.ts     # live devnet check, only with Harshit's go-ahead
Set-Location ..
docker build -t duq-chain chain
git add <explicit paths>; git commit -m "[p6-chain] <what>"   # never `git add .`, never push or merge
```

## 10. Out of scope / do not
- **Never** use mainnet, real funds, fungible tokens, payments, royalties, marketplaces or token-gating. Never set `ALLOW_MAINNET`.
- **No wallet signing in the browser**, and no private keys anywhere in the site.
- **No automated airdrops or faucet scripting.** Harshit funds the devnet keypair at faucet.solana.com; agents never solve CAPTCHAs.
- **Don't edit `deploy/**`, `server/**` or the site entry files.** Request changes in status.
- **No `learner_id` or other learner data on chain** beyond the alias and score the learner chose to claim with.
- **No Solana Actions or Blinks** (an optional stretch in SPONSORS.md) unless every gate passes by 3:30 AM.
- **Don't send the production `index` anchor yourself.**

## 11. If blocked (DECISION NEEDED + fallbacks + cut line)
Wording (in status; then carry on with whatever is unblocked):
```
DECISION NEEDED (p6-chain, HH:MM): <one line>. Observed: <error text, package versions>. Options: (a) ... (b) ...
My default if no answer by HH:MM+30: (a).
```
- **No keypair yet.** Build and test everything with fakes, and mark "LIVE CHECK PENDING". Harshit or P7 runs `smoke.ts` later.
- **The `mpl-core` plugin field names differ in the installed version.** Follow the Metaplex soulbound guide for that version, and keep the test asserting frozen with authority None. If a soulbound Core asset proves impossible, write DECISION NEEDED; never ship a transferable credential silently.
- **Devnet RPC errors or rate limits.**
  - Retry 3 times with backoff.
  - Harshit may supply a provider devnet URL; one whose host contains `devnet` passes the guard, provided its genesis hash matches.
- **The metadata URI isn't reachable yet** (Caddy isn't deployed). Mint anyway: the `uri` is just a string, and it resolves once P7 deploys with `API_HOST` set.
- **Cut line**, following PLAN §3 #5:
  1. Phantom connect (keep the custodial claim);
  2. the anchors-panel offline cache;
  3. the read-back and transfer proof in `smoke.ts` (keep the mint and anchor).

  **Never cut:** the custodial soulbound credential, the anchor endpoint and list, the devnet guard, the admin token check, idempotency, and secret hygiene.

## 12. Hand-off (status contents + 3 questions Harshit should be able to answer: QUESTIONS ONLY)
At DONE, `docs/product/status/p6-chain.md` contains:
- **Basics:** state, branch, last commit; the resolved package versions; test and build output.
- **Degraded start:** the curl transcript.
- **Live check:** the devnet explorer links (credential asset, mint tx, anchor tx), the frozen read-back and the failed-transfer error, or "LIVE CHECK PENDING".
- **For P7:** the compose and env needs, and the site mount points.
- **Additive fields:** `l8_payload_hash`, `tx_url`, `/api/chain/meta/*`, `/api/chain/health`.
- **Open items:** any open DECISION NEEDED.

Explain-back questions (Harshit answers them himself; don't write answers):
1. What makes the credential soulbound at the program level, rather than just in our UI? With PermanentFreezeDelegate and authority None, who could ever thaw or transfer it? And what does "custodial" mean for a learner without a wallet?
2. What exactly does the Memo anchor of `sha256(results/index.json)` prove to a judge, and what doesn't it prove? How would someone check a given results file against it?
3. Name every safeguard that keeps this service off mainnet and away from real funds. Why do the credential and the anchor deliberately involve no tokens and no payments?
