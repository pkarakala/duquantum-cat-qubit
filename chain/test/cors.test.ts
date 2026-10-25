import { describe, expect, it } from "vitest";
import { makeApp } from "./harness.js";

describe("cors", () => {
  it("allows the null origin and listed origins only", async () => {
    const { app } = makeApp();
    const fileOrigin = await app.request("/api/chain/health", { headers: { origin: "null" } });
    expect(fileOrigin.headers.get("access-control-allow-origin")).toBe("null");

    const listed = await app.request("/api/chain/health", {
      headers: { origin: "https://academy.example" },
    });
    expect(listed.headers.get("access-control-allow-origin")).toBe("https://academy.example");

    const other = await app.request("/api/chain/health", {
      headers: { origin: "https://evil.example" },
    });
    expect(other.headers.get("access-control-allow-origin")).toBeNull();
  });
});
