import { describe, expect, it } from "vitest";
import { ADMIN, anchorBody, makeApp, postJson } from "./harness.js";

describe("anchor list", () => {
  it("returns both anchors newest first with explorer urls and ISO timestamps", async () => {
    const harness = makeApp();
    harness.setNow(Date.UTC(2026, 9, 25, 4, 0, 0));
    const first = await postJson(harness.app, "/api/chain/anchor", anchorBody({ label: "older" }), {
      "x-admin-token": ADMIN,
    });
    expect(first.status).toBe(200);
    harness.setNow(Date.UTC(2026, 9, 25, 5, 0, 0));
    const second = await postJson(
      harness.app,
      "/api/chain/anchor",
      anchorBody({ label: "newer", sha256: "cd".repeat(32) }),
      { "x-admin-token": ADMIN },
    );
    expect(second.status).toBe(200);
    const listed = await harness.app.request("/api/chain/anchors");
    const body = await listed.json();
    expect(body.anchors.map((row: { label: string }) => row.label)).toEqual(["newer", "older"]);
    expect(body.anchors[0].ts).toBe("2026-10-25T05:00:00.000Z");
    expect(body.anchors[1].ts).toBe("2026-10-25T04:00:00.000Z");
    expect(body.anchors[0].explorer_url).toBe("https://explorer.solana.com/tx/memo2?cluster=devnet");
    expect(body.anchors[1].explorer_url).toBe("https://explorer.solana.com/tx/memo1?cluster=devnet");
    expect(body.anchors[0].sha256).toBe("cd".repeat(32));
  });
});
