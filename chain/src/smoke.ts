import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { Connection, Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import type { Signer } from "@metaplex-foundation/umi";
import { fetchAsset, transfer } from "@metaplex-foundation/mpl-core";
import { generateSigner } from "@metaplex-foundation/umi";
import { loadConfig, MIN_BALANCE_SOL, payerFromSecret } from "./config.js";
import { createDemoAdapter, DEMO_NOTICE } from "./demo.js";
import { assertDevnet, fetchGenesisHash } from "./guard.js";
import { broadcastMemo } from "./memo.js";
import {
  buildCreateInput,
  createLiveUmi,
  newAsset,
  sendCreateAndConfirm,
  signCreateTransaction,
} from "./mint.js";
import { buildMetadata, explorerAddressUrl, explorerTxUrl } from "./meta.js";
import { FileStore } from "./store.js";
import { canonicalContentHash, memoText } from "./validate.js";

/**
 * Live devnet check. Without a signer this prints LIVE CHECK PENDING and exits.
 * Pass --demo to run the offline adapter. That path signs and does not broadcast.
 * The production results anchor (label=index) is not sent here.
 */
async function main(): Promise<void> {
  const demo = process.argv.includes("--demo");
  const secret = process.env.SOLANA_SECRET_KEY_B58?.trim() ?? "";
  if (demo || !secret) {
    if (!demo) {
      console.log("LIVE CHECK PENDING (needs funded devnet keypair)");
      return;
    }
    await runDemo();
    return;
  }
  await runLive(secret);
}

async function runDemo(): Promise<void> {
  const adapter = createDemoAdapter();
  const asset = adapter.newAsset();
  const uri = `http://localhost:8100/api/chain/meta/${asset.publicKey}.json`;
  const signed = await signCreateTransaction(
    adapter.umi,
    buildCreateInput({ asset: asset.signer as Signer, owner: adapter.payer, uri }),
  );
  const hash = createHash("sha256").update("duq-academy smoke", "utf8").digest("hex");
  const memo = adapter.signMemo(memoText("smoke", hash));
  console.log(DEMO_NOTICE);
  console.log("broadcast: false");
  console.log("network: offline-demo");
  console.log(`payer: ${adapter.payer}`);
  console.log(`credential_signature: ${signed.txSig}`);
  console.log(`credential_verified: ${signed.verified}`);
  console.log(`anchor_signature: ${memo.txSig}`);
  console.log(`anchor_verified: ${memo.verified}`);
  console.log("not broadcast");
}

async function runLive(secret: string): Promise<void> {
  const config = loadConfig({
    SOLANA_RPC_URL: process.env.SOLANA_RPC_URL,
    SOLANA_SECRET_KEY_B58: secret,
    API_HOST: process.env.API_HOST,
    CHAIN_MODE: "live",
  });
  const signerSecret = config.secretKey();
  if (!signerSecret || !config.payer) {
    throw new Error("signer secret is not a 64-byte keypair");
  }
  await assertDevnet(config.rpcUrl, fetchGenesisHash(config.rpcUrl));
  const payer = Keypair.fromSecretKey(bs58.decode(signerSecret));
  if (payerFromSecret(secret) !== config.payer) {
    throw new Error("payer mismatch");
  }
  const connection = new Connection(config.rpcUrl, "confirmed");
  const balance = (await connection.getBalance(payer.publicKey, "confirmed")) / 1_000_000_000;
  if (balance < MIN_BALANCE_SOL) {
    throw new Error(`balance ${balance} SOL is below ${MIN_BALANCE_SOL}`);
  }
  const umi = createLiveUmi(config.rpcUrl, signerSecret);
  const asset = newAsset(umi);
  const uri = `${config.publicBase}/api/chain/meta/${asset.publicKey}.json`;
  const store = new FileStore(path.resolve("data"));
  const issuedAt = new Date().toISOString();
  const levels = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"];
  const contentHash = canonicalContentHash("smoke", levels, null);
  await store.writeMeta(
    asset.publicKey,
    buildMetadata({
      alias: "smoke",
      levelsPassed: levels,
      score: null,
      issuedAt,
      contentHash,
      publicBase: config.publicBase,
    }),
  );
  const txSig = await sendCreateAndConfirm(
    umi,
    buildCreateInput({ asset: asset.signer, owner: config.payer, uri }),
  );
  const hash = resultsHash();
  const anchorSig = await broadcastMemo(connection, payer, memoText("smoke", hash));
  const fetched = await fetchAsset(umi, asset.publicKey);
  const freeze = fetched.permanentFreezeDelegate;
  if (!freeze?.frozen || freeze.authority.type !== "None") {
    throw new Error("asset did not read back as permanently frozen with authority None");
  }
  const recipient = generateSigner(umi).publicKey;
  try {
    await transfer(umi, { asset: fetched, newOwner: recipient }).sendAndConfirm(umi);
    throw new Error("transfer succeeded; credential is not soulbound");
  } catch (err) {
    if (err instanceof Error && err.message.includes("not soulbound")) throw err;
    console.log(`transfer failed as expected: ${err instanceof Error ? err.message : "transfer rejected"}`);
  }
  console.log(`credential: ${explorerAddressUrl(asset.publicKey)}`);
  console.log(`mint_tx: ${explorerTxUrl(txSig)}`);
  console.log(`anchor_tx: ${explorerTxUrl(anchorSig)}`);
}

function resultsHash(): string {
  const candidates = [
    path.resolve(process.cwd(), "results/index.json"),
    path.resolve(process.cwd(), "../results/index.json"),
  ];
  for (const file of candidates) {
    if (existsSync(file)) {
      return createHash("sha256").update(readFileSync(file)).digest("hex");
    }
  }
  return createHash("sha256").update("duq-academy smoke", "utf8").digest("hex");
}

const entry = process.argv[1] ?? "";
if (entry.endsWith("smoke.ts") || entry.endsWith("smoke.js")) {
  main().catch((err: unknown) => {
    console.error(err instanceof Error ? err.message : "smoke failed");
    process.exit(1);
  });
}
