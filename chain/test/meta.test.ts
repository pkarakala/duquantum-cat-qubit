import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { credentialBody, makeApp, postJson } from "./harness.js";

const LEARNER = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";

describe("credential metadata", () => {
  it("serves attributes and never the learner id", async () => {
    const harness = makeApp();
    harness.setNow(Date.UTC(2026, 9, 25, 4, 0, 0));
    const levels = ["L8", "L1"];
    const score = 1.25;
    const res = await postJson(
      harness.app,
      "/api/chain/credential",
      credentialBody({ learner_id: LEARNER, alias: "Ada", levels_passed: levels, score }),
    );
    expect(res.status).toBe(200);
    const created = await res.json();
    expect(JSON.stringify(created)).not.toContain(LEARNER);
    const metaRes = await harness.app.request(`/api/chain/meta/${created.asset_address}.json`);
    expect(metaRes.status).toBe(200);
    const meta = await metaRes.json();
    const text = JSON.stringify(meta);
    expect(text).not.toContain(LEARNER);
    const attributes = Object.fromEntries(meta.attributes.map((attr: { trait_type: string; value: string }) => [attr.trait_type, attr.value]));
    expect(attributes.levels_passed).toBe("L1,L8");
    expect(attributes.score).toBe("1.25");
    expect(attributes.alias).toBe("Ada");
    expect(attributes.issued_at).toBe("2026-10-25T04:00:00.000Z");
    expect(attributes.content_hash).toMatch(/^[0-9a-f]{64}$/);
    const expected = createHash("sha256")
      .update(JSON.stringify({ alias: "Ada", levels_passed: ["L1", "L8"], score: 1.25 }))
      .digest("hex");
    expect(attributes.content_hash).toBe(expected);
    expect(meta.image).toContain("/api/chain/meta/badge.svg");
  });

  it("returns 404 for an unknown asset", async () => {
    const { app } = makeApp();
    const res = await app.request("/api/chain/meta/11111111111111111111111111111111.json");
    expect(res.status).toBe(404);
    expect((await res.json()).error.code).toBe("not_found");
  });
});
