import { Keypair, PublicKey } from "@solana/web3.js";
import { describe, expect, it } from "vitest";
import { loadConfig } from "../src/config.js";
import { createDemoAdapter, DEMO_NOTICE } from "../src/demo.js";
import { MEMO_PROGRAM_ID, signMemoOffline } from "../src/memo.js";
import { buildCreateInput, signCreateTransaction } from "../src/mint.js";
import { memoText } from "../src/validate.js";
import { ADMIN, anchorBody, credentialBody, makeApp, postJson } from "./harness.js";

describe("offline demo adapter", () => {
  it("signs the memo transaction and does not broadcast it", () => {
    const payer = Keypair.generate();
    const hash = "ab".repeat(32);
    const memo = memoText("index", hash);
    const signed = signMemoOffline(payer, memo);
    expect(signed.verified).toBe(true);
    expect(signed.transaction.verifySignatures()).toBe(true);
    const ix = signed.transaction.instructions[0];
    expect(ix?.programId.equals(new PublicKey(MEMO_PROGRAM_ID))).toBe(true);
    expect(ix?.data.toString("utf8")).toBe(`duq-academy:index:${hash}`);
    expect(ix?.keys[0]?.pubkey.equals(payer.publicKey)).toBe(true);
    expect(signed.txSig).not.toContain("mainnet");
  });

  it("signs the soulbound create on the same builder and labels the HTTP result", async () => {
    const config = loadConfig({
      CHAIN_MODE: "demo",
      SOLANA_RPC_URL: "http://127.0.0.1:8899",
      ADMIN_TOKEN: ADMIN,
      ALLOWED_ORIGINS: "https://academy.example",
      SOLANA_SECRET_KEY_B58: "this-must-not-be-used-or-broadcast",
    });
    const adapter = createDemoAdapter();
    config.attachDemoPayer(adapter.payer);
    const asset = adapter.newAsset();
    const signed = await signCreateTransaction(
      adapter.umi,
      buildCreateInput({
        asset: asset.signer,
        owner: adapter.payer,
        uri: `http://localhost:8100/api/chain/meta/${asset.publicKey}.json`,
      }),
    );
    expect(signed.verified).toBe(true);

    const harness = makeApp({
      config,
      newAsset: () => adapter.newAsset(),
      mint: (input) => adapter.mint(input),
      sendMemo: (memo) => adapter.sendMemo(memo),
    });
    const credential = await postJson(harness.app, "/api/chain/credential", credentialBody());
    expect(credential.status).toBe(200);
    const body = await credential.json();
    expect(body.demo).toBe(true);
    expect(body.broadcast).toBe(false);
    expect(body.network).toBe("offline-demo");
    expect(body.explorer_url).toBeNull();
    expect(body.tx_url).toBeNull();
    expect(body.notice).toBe(DEMO_NOTICE);
    expect(JSON.stringify(body)).not.toContain("explorer.solana.com");
    expect(body.custodial).toBe(true);
    expect(body.tx_sig.length).toBeGreaterThan(40);

    const anchor = await postJson(harness.app, "/api/chain/anchor", anchorBody(), {
      "x-admin-token": ADMIN,
    });
    expect(anchor.status).toBe(200);
    const anchored = await anchor.json();
    expect(anchored.demo).toBe(true);
    expect(anchored.broadcast).toBe(false);
    expect(anchored.explorer_url).toBeNull();
    const memo = adapter.signMemo(`duq-academy:index:${anchorBody().sha256}`);
    expect(memo.verified).toBe(true);
  });

  it("stays unavailable when no signer is configured and demo mode is off", async () => {
    const harness = makeApp({ env: { SOLANA_SECRET_KEY_B58: undefined } });
    const health = await harness.app.request("/api/chain/health");
    const healthBody = await health.json();
    expect(healthBody.ready).toBe(false);
    expect(healthBody.payer).toBeNull();
    const credential = await postJson(harness.app, "/api/chain/credential", credentialBody());
    expect(credential.status).toBe(503);
    expect(await credential.json()).toEqual({
      error: { code: "chain_unavailable", message: "chain unavailable" },
    });
    expect(harness.mints).toHaveLength(0);
  });

  it("refuses to mint when the balance is under 0.02 SOL", async () => {
    const harness = makeApp({ balance: 0.019 });
    const res = await postJson(harness.app, "/api/chain/credential", credentialBody());
    expect(res.status).toBe(503);
    expect((await res.json()).error.code).toBe("chain_unavailable");
    expect(harness.mints).toHaveLength(0);
  });
});
