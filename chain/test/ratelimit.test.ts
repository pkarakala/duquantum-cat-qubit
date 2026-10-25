import { describe, expect, it } from "vitest";
import { credentialBody, makeApp, postJson } from "./harness.js";

describe("credential rate limit", () => {
  it("limits one address to 5 claims an hour and leaves another address alone", async () => {
    const harness = makeApp();
    const start = 1_700_000_000_000;
    harness.setNow(start);
    for (let i = 0; i < 5; i++) {
      const res = await postJson(
        harness.app,
        "/api/chain/credential",
        credentialBody({ learner_id: `aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeee${i}` }),
        { "x-forwarded-for": "198.51.100.10" },
      );
      expect(res.status).toBe(200);
    }
    const blocked = await postJson(
      harness.app,
      "/api/chain/credential",
      credentialBody({ learner_id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeef" }),
      { "x-forwarded-for": "198.51.100.10" },
    );
    expect(blocked.status).toBe(429);
    expect((await blocked.json()).error.code).toBe("rate_limited");

    const other = await postJson(
      harness.app,
      "/api/chain/credential",
      credentialBody({ learner_id: "bbbbbbbb-bbbb-4ccc-8ddd-eeeeeeeeeeee" }),
      { "x-forwarded-for": "198.51.100.20" },
    );
    expect(other.status).toBe(200);

    harness.setNow(start + 60 * 60 * 1000);
    const later = await postJson(
      harness.app,
      "/api/chain/credential",
      credentialBody({ learner_id: "cccccccc-bbbb-4ccc-8ddd-eeeeeeeeeeee" }),
      { "x-forwarded-for": "198.51.100.10" },
    );
    expect(later.status).toBe(200);
  });
});
