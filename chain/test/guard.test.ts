import { readdirSync, readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEVNET_GENESIS, MAINNET_GENESIS } from "../src/config.js";
import { assertDevnet, ClusterRefusedError } from "../src/guard.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const chainRoot = path.resolve(here, "..");
const repoRoot = path.resolve(here, "../..");

describe("assertDevnet", () => {
  it("refuses mainnet and testnet urls", async () => {
    await expect(
      assertDevnet("https://api.mainnet-beta.solana.com", async () => MAINNET_GENESIS),
    ).rejects.toBeInstanceOf(ClusterRefusedError);
    await expect(
      assertDevnet("https://api.testnet.solana.com", async () => "testnet-hash"),
    ).rejects.toBeInstanceOf(ClusterRefusedError);
  });

  it("accepts devnet only when the genesis hash matches", async () => {
    await expect(
      assertDevnet("https://api.devnet.solana.com", async () => DEVNET_GENESIS),
    ).resolves.toBeUndefined();
    await expect(
      assertDevnet("https://api.devnet.solana.com", async () => MAINNET_GENESIS),
    ).rejects.toBeInstanceOf(ClusterRefusedError);
  });

  it("still refuses a non-devnet host when the genesis lookup is skipped", async () => {
    await expect(
      assertDevnet("https://api.mainnet-beta.solana.com", async () => DEVNET_GENESIS, {
        skipGenesis: true,
      }),
    ).rejects.toBeInstanceOf(ClusterRefusedError);
  });

  it("accepts localhost without asking for a genesis hash", async () => {
    let calls = 0;
    const genesis = async () => {
      calls += 1;
      return "not-devnet";
    };
    await assertDevnet("http://127.0.0.1:8899", genesis);
    await assertDevnet("http://localhost:8899", genesis);
    expect(calls).toBe(0);
  });

  it("refuses a mainnet override instead of honoring it", async () => {
    await expect(
      assertDevnet("http://127.0.0.1:8899", async () => DEVNET_GENESIS, { mainnetOverride: true }),
    ).rejects.toThrow(/devnet-only/);
  });

  it("does not assign a mainnet override anywhere in the service files", () => {
    const needle = ["ALLOW", "MAINNET="].join("_");
    const files = walk(chainRoot);
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      expect(text.includes(needle), file).toBe(false);
    }
    for (const rel of ["deploy/docker-compose.yml", "server/.env.example"]) {
      const file = path.join(repoRoot, rel);
      if (!existsSync(file)) continue;
      expect(readFileSync(file, "utf8").includes(needle)).toBe(false);
    }
  });
});

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}
