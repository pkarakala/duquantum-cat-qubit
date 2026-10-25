import { describe, expect, it } from "vitest";
import { FileStore } from "../src/store.js";
import { credentialBody, makeApp, postJson } from "./harness.js";

describe("credential idempotency", () => {
  it("mints once for the same learner and levels in any order", async () => {
    const harness = makeApp();
    const first = await postJson(harness.app, "/api/chain/credential", credentialBody({
      levels_passed: ["L8", "L2", "L1"],
    }));
    const second = await postJson(harness.app, "/api/chain/credential", credentialBody({
      levels_passed: ["L1", "L2", "L8"],
    }));
    expect(first.status).toBe(200);
    expect(second.status).toBe(200);
    expect(await first.json()).toEqual(await second.json());
    expect(harness.mints).toHaveLength(1);
  });

  it("mints again when the level set changes", async () => {
    const harness = makeApp();
    await postJson(harness.app, "/api/chain/credential", credentialBody({ levels_passed: ["L8"] }));
    await postJson(harness.app, "/api/chain/credential", credentialBody({ levels_passed: ["L1", "L8"] }));
    expect(harness.mints).toHaveLength(2);
  });

  it("shares one mint across concurrent identical requests", async () => {
    let calls = 0;
    const harness = makeApp({
      mint: async () => {
        calls += 1;
        await new Promise((resolve) => setTimeout(resolve, 80));
        return { txSig: "only-once" };
      },
    });
    const body = credentialBody();
    const [a, b] = await Promise.all([
      postJson(harness.app, "/api/chain/credential", body),
      postJson(harness.app, "/api/chain/credential", body),
    ]);
    expect(a.status).toBe(200);
    expect(b.status).toBe(200);
    expect(await a.json()).toEqual(await b.json());
    expect(calls).toBe(1);
  });

  it("survives a new store on the same directory", async () => {
    const first = makeApp();
    const created = await postJson(first.app, "/api/chain/credential", credentialBody());
    const saved = await created.json();
    const second = makeApp({
      store: new FileStore(first.dir),
      config: first.config,
    });
    const again = await postJson(second.app, "/api/chain/credential", credentialBody());
    expect(await again.json()).toEqual(saved);
    expect(second.mints).toHaveLength(0);
  });
});
