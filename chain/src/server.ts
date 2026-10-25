import { serve } from "@hono/node-server";
import { Connection, Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import path from "node:path";
import { createApp, type AppDeps } from "./app.js";
import { loadConfig } from "./config.js";
import { createDemoAdapter } from "./demo.js";
import { assertDevnet, ClusterRefusedError, fetchGenesisHash } from "./guard.js";
import { broadcastMemo } from "./memo.js";
import {
  buildCreateInput,
  createLiveUmi,
  newAsset,
  requireSigner,
  sendCreateAndConfirm,
} from "./mint.js";
import { FileStore } from "./store.js";

function overridePresent(): boolean {
  return Boolean(process.env["ALLOW_MAINNET"]);
}

async function main(): Promise<void> {
  const config = loadConfig(process.env);
  const mainnetOverride = overridePresent();
  let reachable = config.mode === "demo";
  try {
    await assertDevnet(config.rpcUrl, fetchGenesisHash(config.rpcUrl), {
      skipGenesis: config.mode === "demo",
      mainnetOverride,
    });
    reachable = true;
  } catch (err) {
    if (err instanceof ClusterRefusedError) {
      console.error(err.message);
      process.exit(1);
    }
    console.error("RPC unreachable. Serving degraded; credential and anchor return 503.");
    reachable = false;
  }

  const dataDir = process.env.CHAIN_DATA_DIR?.trim() || path.resolve("data");
  const store = new FileStore(dataDir);
  const deps = wire(config, store, mainnetOverride, reachable);
  const app = createApp(deps);
  serve({ fetch: app.fetch, hostname: "0.0.0.0", port: config.port }, (info) => {
    console.log(`chain listening on ${info.port} mode=${config.mode} payer=${config.payer ?? "none"}`);
  });
}

function wire(
  config: ReturnType<typeof loadConfig>,
  store: FileStore,
  mainnetOverride: boolean,
  reachable: boolean,
): AppDeps {
  const now = () => Date.now();
  if (config.mode === "demo") {
    const demo = createDemoAdapter();
    config.attachDemoPayer(demo.payer);
    console.log(`DEMO adapter. ${demo.notice} payer=${demo.payer}`);
    return {
      config,
      store,
      now,
      mainnetOverride,
      getGenesisHash: async () => {
        throw new Error("demo does not contact RPC");
      },
      getBalance: async () => 0,
      newAsset: () => demo.newAsset(),
      mint: (input) => demo.mint(input),
      sendMemo: (memo) => demo.sendMemo(memo),
    };
  }

  const secret = config.secretKey();
  if (config.mode === "live" && secret && config.payer) {
    const umi = createLiveUmi(config.rpcUrl, secret);
    const payer = Keypair.fromSecretKey(bs58.decode(secret));
    const connection = new Connection(config.rpcUrl, "confirmed");
    console.log(`payer ${config.payer}`);
    if (!reachable) {
      console.error("Live signer is configured, but the RPC was unreachable at boot.");
    }
    return {
      config,
      store,
      now,
      mainnetOverride,
      getGenesisHash: fetchGenesisHash(config.rpcUrl),
      getBalance: async () => {
        const lamports = await connection.getBalance(payer.publicKey, "confirmed");
        return lamports / 1_000_000_000;
      },
      newAsset: () => newAsset(umi),
      mint: async (input) => {
        const txSig = await sendCreateAndConfirm(
          umi,
          buildCreateInput({
            asset: requireSigner(input.signer),
            owner: input.owner,
            uri: input.uri,
          }),
        );
        return { txSig, demo: false, broadcast: true };
      },
      sendMemo: async (memo) => {
        const txSig = await broadcastMemo(connection, payer, memo);
        return { txSig, demo: false, broadcast: true };
      },
    };
  }

  console.log("No signer configured. Credential and anchor return 503.");
  return {
    config,
    store,
    now,
    mainnetOverride,
    getGenesisHash: fetchGenesisHash(config.rpcUrl),
    getBalance: async () => {
      throw new Error("chain unavailable");
    },
    newAsset: () => {
      throw new Error("chain unavailable");
    },
    mint: async () => {
      throw new Error("chain unavailable");
    },
    sendMemo: async () => {
      throw new Error("chain unavailable");
    },
  };
}

const entry = process.argv[1] ?? "";
if (entry.endsWith("server.ts") || entry.endsWith("server.js")) {
  main().catch((err: unknown) => {
    console.error(err instanceof Error ? err.message : "chain failed to start");
    process.exit(1);
  });
}
