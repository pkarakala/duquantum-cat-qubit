import { Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import { describe, expect, it } from "vitest";
import { credentialBody, makeApp, postJson } from "./harness.js";

describe("credential pubkey and levels", () => {
  it("rejects an invalid key, a short key, and an empty key", async () => {
    const harness = makeApp();
    for (const wallet of ["not base58 !!!", bs58.encode(Buffer.alloc(31, 7)), ""]) {
      const res = await postJson(
        harness.app,
        "/api/chain/credential",
        credentialBody({ wallet_pubkey: wallet }),
      );
      expect(res.status).toBe(422);
      expect((await res.json()).error.code).toBe("bad_request");
    }
    expect(harness.mints).toHaveLength(0);
  });

  it("uses a valid wallet as the owner", async () => {
    const harness = makeApp();
    const wallet = Keypair.generate().publicKey.toBase58();
    const res = await postJson(
      harness.app,
      "/api/chain/credential",
      credentialBody({ wallet_pubkey: wallet }),
    );
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.custodial).toBe(false);
    expect(harness.mints[0]?.owner).toBe(wallet);
  });

  it("uses the payer as owner when no wallet is given", async () => {
    const harness = makeApp();
    const res = await postJson(harness.app, "/api/chain/credential", credentialBody());
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.custodial).toBe(true);
    expect(harness.mints[0]?.owner).toBe(harness.config.payer);
  });

  it("requires L8", async () => {
    const { app } = makeApp();
    const res = await postJson(app, "/api/chain/credential", credentialBody({ levels_passed: ["L1", "L2"] }));
    expect(res.status).toBe(422);
    expect((await res.json()).error.code).toBe("bad_request");
  });
});
