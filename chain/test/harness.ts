import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import type { Hono } from "hono";
import { createApp, type AppDeps } from "../src/app.js";
import { DEVNET_GENESIS, loadConfig, type ChainConfig } from "../src/config.js";
import type { MintRequest } from "../src/mint.js";
import { FileStore } from "../src/store.js";

export const ADMIN = "test-admin-token";

export function credentialBody(over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    learner_id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
    alias: "Ada",
    levels_passed: ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"],
    score: 1,
    ...over,
  };
}

export function anchorBody(over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    sha256: "ab".repeat(32),
    label: "index",
    ...over,
  };
}

export type Harness = {
  app: Hono;
  config: ChainConfig;
  store: FileStore;
  dir: string;
  secret: string;
  payer: string;
  mints: MintRequest[];
  memos: string[];
  setNow: (n: number) => void;
};

export function makeApp(opts: {
  env?: Record<string, string | undefined>;
  balance?: number;
  store?: FileStore;
  config?: ChainConfig;
  mint?: AppDeps["mint"];
  sendMemo?: AppDeps["sendMemo"];
  newAsset?: AppDeps["newAsset"];
  getBalance?: () => Promise<number>;
  getGenesisHash?: () => Promise<string>;
} = {}): Harness {
  const kp = Keypair.generate();
  const secret = bs58.encode(kp.secretKey);
  const config =
    opts.config ??
    loadConfig({
      SOLANA_RPC_URL: "http://127.0.0.1:8899",
      SOLANA_SECRET_KEY_B58: secret,
      ADMIN_TOKEN: ADMIN,
      ALLOWED_ORIGINS: "https://academy.example",
      ...opts.env,
    });
  const dir = opts.store ? opts.store.dir : mkdtempSync(path.join(tmpdir(), "duq-chain-"));
  const store = opts.store ?? new FileStore(dir);
  let clock = 1_700_000_000_000;
  const mints: MintRequest[] = [];
  const memos: string[] = [];
  const app = createApp({
    config,
    store,
    now: () => clock,
    mainnetOverride: false,
    getGenesisHash: opts.getGenesisHash ?? (async () => DEVNET_GENESIS),
    getBalance: opts.getBalance ?? (async () => opts.balance ?? 1),
    newAsset:
      opts.newAsset ??
      (() => {
        const asset = Keypair.generate().publicKey.toBase58();
        return { publicKey: asset, signer: { publicKey: asset } };
      }),
    mint:
      opts.mint ??
      (async (input) => {
        mints.push(input);
        return { txSig: `sig${mints.length}` };
      }),
    sendMemo:
      opts.sendMemo ??
      (async (memo) => {
        memos.push(memo);
        return { txSig: `memo${memos.length}` };
      }),
  });
  return {
    app,
    config,
    store,
    dir,
    secret,
    payer: config.payer ?? kp.publicKey.toBase58(),
    mints,
    memos,
    setNow: (value: number) => {
      clock = value;
    },
  };
}

export function postJson(
  app: Hono,
  url: string,
  body: unknown,
  headers: Record<string, string> = {},
): Promise<Response> {
  return app.request(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-forwarded-for": "203.0.113.10",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}
