import { Hono } from "hono";
import { cors } from "hono/cors";
import type { Context } from "hono";
import { ChainConfig, MIN_BALANCE_SOL } from "./config.js";
import { DEMO_NOTICE } from "./demo.js";
import { assertDevnet } from "./guard.js";
import { tokenMatches } from "./guard.js";
import { badgeSvg, buildMetadata, explorerAddressUrl, explorerTxUrl } from "./meta.js";
import type { ChainSigner, MintRequest } from "./mint.js";
import { anchorLimiter, clientIp, credentialLimiter } from "./ratelimit.js";
import { FileStore, type StoredAnchor, type StoredCredential } from "./store.js";
import {
  BadRequest,
  canonicalContentHash,
  credentialKey,
  isAssetAddress,
  memoText,
  validateAnchor,
  validateCredential,
} from "./validate.js";

export type AppDeps = {
  config: ChainConfig;
  store: FileStore;
  now: () => number;
  getGenesisHash: () => Promise<string>;
  getBalance: () => Promise<number>;
  /** When true, assertDevnet refuses even a localhost URL. */
  mainnetOverride?: boolean;
  newAsset: () => { publicKey: string; signer: unknown };
  mint: (input: MintRequest) => Promise<ChainSigner>;
  sendMemo: (memo: string) => Promise<ChainSigner>;
};

export function createApp(deps: AppDeps): Hono {
  const app = new Hono();
  const origins = new Set([...deps.config.allowedOrigins, "null"]);
  const credentials = credentialLimiter(deps.now);
  const anchors = anchorLimiter(deps.now);

  app.use(
    "*",
    cors({
      origin: (origin) => (origins.has(origin) ? origin : null),
      allowMethods: ["GET", "POST", "OPTIONS"],
      allowHeaders: ["Content-Type", "X-Admin-Token"],
    }),
  );

  app.get("/api/chain/health", async (c) => {
    if (deps.config.mode === "demo") {
      return c.json({
        ok: true,
        cluster: "offline-demo",
        payer: deps.config.payer,
        balance_sol: null,
        ready: false,
        mode: "demo",
        broadcast: false,
        notice: DEMO_NOTICE,
      });
    }
    const ready = await chainReady(deps);
    let balance: number | null = null;
    if (deps.config.payer) {
      try {
        balance = await deps.getBalance();
      } catch {
        balance = null;
      }
    }
    return c.json({
      ok: true,
      cluster: "devnet",
      payer: deps.config.payer,
      balance_sol: balance,
      ready: ready.ok,
      mode: deps.config.mode,
      broadcast: deps.config.mode === "live",
    });
  });

  app.post("/api/chain/credential", async (c) => {
    let body: ReturnType<typeof validateCredential>;
    try {
      body = validateCredential(await readJson(c));
    } catch (err) {
      return badRequest(c, err);
    }
    if (!credentials.allow(`credential:${clientIp(c)}`)) {
      return error(c, 429, "rate_limited", "rate limited");
    }
    const unavailable = await ensureChain(c, deps);
    if (unavailable) return unavailable;

    const demo = deps.config.mode === "demo";
    const owner = body.walletPubkey ?? deps.config.payer;
    if (!owner) return error(c, 503, "chain_unavailable", "chain unavailable");
    const custodial = body.walletPubkey === null;
    const key = credentialKey(body.learnerId, body.levelsPassed, demo);

    try {
      const stored = await deps.store.once(key, async () => {
        const asset = deps.newAsset();
        if (!isAssetAddress(asset.publicKey)) throw new Error("asset address rejected");
        const uri = `${deps.config.publicBase}/api/chain/meta/${asset.publicKey}.json`;
        const issuedAt = new Date(deps.now()).toISOString();
        const contentHash = body.l8PayloadHash ?? canonicalContentHash(body.alias, body.levelsPassed, body.score);
        const metadata = buildMetadata({
          alias: body.alias,
          levelsPassed: body.levelsPassed,
          score: body.score,
          issuedAt,
          contentHash,
          publicBase: deps.config.publicBase,
        });
        await deps.store.writeMeta(asset.publicKey, metadata);
        const minted = await deps.mint({
          owner,
          uri,
          signer: asset.signer,
          alias: body.alias,
          levelsPassed: body.levelsPassed,
          score: body.score,
          contentHash,
          custodial,
        });
        return credentialResponse(asset.publicKey, minted.txSig, custodial, demo || minted.demo === true);
      });
      return c.json(stored);
    } catch {
      return error(c, 502, "tx_failed", "transaction failed");
    }
  });

  app.post("/api/chain/anchor", async (c) => {
    if (!deps.config.hasAdminToken) {
      return error(c, 503, "feature_disabled", "feature disabled");
    }
    const expected = deps.config.adminToken() ?? "";
    const provided = c.req.header("x-admin-token") ?? "";
    if (!tokenMatches(provided, expected)) {
      return error(c, 401, "unauthorized", "unauthorized");
    }
    let body: ReturnType<typeof validateAnchor>;
    try {
      body = validateAnchor(await readJson(c));
    } catch (err) {
      return badRequest(c, err);
    }
    if (!anchors.allow(`anchor:${clientIp(c)}`)) {
      return error(c, 429, "rate_limited", "rate limited");
    }
    const unavailable = await ensureChain(c, deps);
    if (unavailable) return unavailable;
    const demo = deps.config.mode === "demo";
    const memo = memoText(body.label, body.sha256);
    try {
      const sent = await deps.sendMemo(memo);
      const record: StoredAnchor = {
        label: body.label,
        sha256: body.sha256,
        tx_sig: sent.txSig,
        explorer_url: demo || sent.broadcast === false ? null : explorerTxUrl(sent.txSig),
        ts: new Date(deps.now()).toISOString(),
        demo: demo || sent.demo === true,
        broadcast: !(demo || sent.broadcast === false),
        network: demo || sent.demo === true ? "offline-demo" : "devnet",
        ...(demo || sent.demo === true ? { notice: DEMO_NOTICE } : {}),
      };
      await deps.store.addAnchor(record);
      return c.json({
        tx_sig: record.tx_sig,
        explorer_url: record.explorer_url,
        demo: record.demo,
        broadcast: record.broadcast,
        network: record.network,
        ...(record.notice ? { notice: record.notice } : {}),
      });
    } catch {
      return error(c, 502, "tx_failed", "transaction failed");
    }
  });

  app.get("/api/chain/anchors", async (c) => {
    const list = await deps.store.listAnchors();
    return c.json({ anchors: list });
  });

  app.get("/api/chain/meta/badge.svg", (c) => {
    return c.body(badgeSvg(), 200, { "content-type": "image/svg+xml; charset=utf-8" });
  });

  app.get("/api/chain/meta/:file", async (c) => {
    const file = c.req.param("file");
    if (!file.endsWith(".json")) return error(c, 404, "not_found", "not found");
    const asset = file.slice(0, -".json".length);
    if (!isAssetAddress(asset)) return error(c, 404, "not_found", "not found");
    const meta = await deps.store.readMeta(asset);
    if (!meta) return error(c, 404, "not_found", "not found");
    return c.json(meta);
  });

  return app;
}

function credentialResponse(
  asset: string,
  txSig: string,
  custodial: boolean,
  demo: boolean,
): StoredCredential {
  if (demo) {
    return {
      asset_address: asset,
      tx_sig: txSig,
      explorer_url: null,
      custodial,
      tx_url: null,
      demo: true,
      broadcast: false,
      network: "offline-demo",
      notice: DEMO_NOTICE,
    };
  }
  return {
    asset_address: asset,
    tx_sig: txSig,
    explorer_url: explorerAddressUrl(asset),
    custodial,
    tx_url: explorerTxUrl(txSig),
    demo: false,
    broadcast: true,
    network: "devnet",
  };
}

async function chainReady(deps: AppDeps): Promise<{ ok: boolean }> {
  if (deps.config.mode !== "live" || !deps.config.hasSecret) return { ok: false };
  try {
    await assertDevnet(deps.config.rpcUrl, deps.getGenesisHash, {
      mainnetOverride: deps.mainnetOverride === true,
    });
    const balance = await deps.getBalance();
    return { ok: balance >= MIN_BALANCE_SOL };
  } catch {
    return { ok: false };
  }
}

async function ensureChain(c: Context, deps: AppDeps): Promise<Response | null> {
  if (deps.config.mode === "demo") return null;
  const ready = await chainReady(deps);
  if (!ready.ok) return error(c, 503, "chain_unavailable", "chain unavailable");
  return null;
}

async function readJson(c: Context): Promise<unknown> {
  try {
    return await c.req.json();
  } catch {
    throw new BadRequest("invalid json");
  }
}

function badRequest(c: Context, err: unknown): Response {
  if (err instanceof BadRequest) return error(c, 422, "bad_request", err.message);
  return error(c, 422, "bad_request", "invalid json");
}

function error(
  c: Context,
  status: 401 | 404 | 422 | 429 | 502 | 503,
  code: string,
  message: string,
): Response {
  return c.json({ error: { code, message } }, status);
}
