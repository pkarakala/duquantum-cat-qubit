import { describe, expect, it } from "vitest";
import { ADMIN, anchorBody, makeApp, postJson } from "./harness.js";

describe("admin anchor", () => {
  it("rejects a missing or wrong token", async () => {
    const { app } = makeApp();
    const missing = await postJson(app, "/api/chain/anchor", anchorBody());
    expect(missing.status).toBe(401);
    expect(await missing.json()).toEqual({ error: { code: "unauthorized", message: "unauthorized" } });

    const wrong = await postJson(app, "/api/chain/anchor", anchorBody(), { "x-admin-token": "nope" });
    expect(wrong.status).toBe(401);
    expect((await wrong.json()).error.code).toBe("unauthorized");
  });

  it("sends the memo text when the token matches", async () => {
    const harness = makeApp();
    const body = anchorBody();
    const res = await postJson(harness.app, "/api/chain/anchor", body, { "x-admin-token": ADMIN });
    expect(res.status).toBe(200);
    expect(harness.memos).toEqual([`duq-academy:index:${body.sha256}`]);
    const json = await res.json();
    expect(json.explorer_url).toBe(`https://explorer.solana.com/tx/memo1?cluster=devnet`);
  });

  it("is disabled when the admin token is unset", async () => {
    const { app } = makeApp({ env: { ADMIN_TOKEN: undefined } });
    const res = await postJson(app, "/api/chain/anchor", anchorBody(), { "x-admin-token": ADMIN });
    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ error: { code: "feature_disabled", message: "feature disabled" } });
  });

  it("rejects a bad hash or label", async () => {
    const { app } = makeApp();
    const badHash = await postJson(
      app,
      "/api/chain/anchor",
      anchorBody({ sha256: "ABC" }),
      { "x-admin-token": ADMIN },
    );
    expect(badHash.status).toBe(422);
    expect((await badHash.json()).error.code).toBe("bad_request");

    const badLabel = await postJson(
      app,
      "/api/chain/anchor",
      anchorBody({ label: "Not A Label" }),
      { "x-admin-token": ADMIN },
    );
    expect(badLabel.status).toBe(422);
  });
});
