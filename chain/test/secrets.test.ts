import { afterEach, describe, expect, it, vi } from "vitest";
import { ADMIN, anchorBody, credentialBody, makeApp, postJson } from "./harness.js";

describe("secret hygiene", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("never prints the signer secret", async () => {
    const seen: string[] = [];
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      vi.spyOn(console, method).mockImplementation((...args: unknown[]) => {
        seen.push(args.map((part) => String(part)).join(" "));
      });
    }
    const harness = makeApp();
    const responses = [
      await harness.app.request("/api/chain/health"),
      await postJson(harness.app, "/api/chain/credential", credentialBody()),
      await postJson(harness.app, "/api/chain/anchor", anchorBody(), { "x-admin-token": ADMIN }),
      await postJson(harness.app, "/api/chain/credential", credentialBody({ wallet_pubkey: "" })),
    ];
    const bodies: string[] = [];
    for (const res of responses) bodies.push(await res.text());
    const blob = [String(harness.config), JSON.stringify(harness.config), JSON.stringify(harness.mints), ...seen, ...bodies].join("\n");
    expect(blob).not.toContain(harness.secret);
    const health = JSON.parse(bodies[0] ?? "{}");
    expect(health.payer).toBe(harness.config.payer);
    expect(health.payer).not.toBe(harness.secret);
  });
});
