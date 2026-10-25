import {
  create,
  mplCore,
  type CreateArgs,
} from "@metaplex-foundation/mpl-core";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import {
  generateSigner,
  keypairIdentity,
  publicKey,
  type Blockhash,
  type Signer,
  type Umi,
} from "@metaplex-foundation/umi";
import { base58 } from "@metaplex-foundation/umi/serializers";
import bs58 from "bs58";
import { OFFLINE_BLOCKHASH } from "./memo.js";

export type MintRequest = {
  owner: string;
  uri: string;
  signer: unknown;
  alias: string;
  levelsPassed: string[];
  score: number | null;
  contentHash: string;
  custodial: boolean;
};

export type ChainSigner = {
  txSig: string;
  demo?: boolean;
  broadcast?: boolean;
};

/**
 * Pure description of the soulbound mint. The single plugin freezes the asset
 * forever and sets its freeze authority to None, so nobody can thaw or transfer it.
 */
export function buildCreateInput(args: { asset: Signer; owner: string; uri: string }): CreateArgs {
  return {
    asset: args.asset,
    owner: publicKey(args.owner),
    name: "Cat Qubit Architect",
    uri: args.uri,
    plugins: [
      {
        type: "PermanentFreezeDelegate",
        frozen: true,
        authority: { type: "None" },
      },
    ],
  };
}

export function requireSigner(value: unknown): Signer {
  if (
    value &&
    typeof value === "object" &&
    "publicKey" in value &&
    "signMessage" in value &&
    "signTransaction" in value
  ) {
    return value as Signer;
  }
  throw new Error("asset signer is missing");
}

/** Umi context whose RPC methods refuse to dial out. Used by the demo adapter. */
export function createOfflineUmi(secretKey?: Uint8Array): Umi {
  const umi = createUmi("http://127.0.0.1:8899").use(mplCore());
  const keypair = secretKey
    ? umi.eddsa.createKeypairFromSecretKey(secretKey)
    : umi.eddsa.generateKeypair();
  umi.use(keypairIdentity(keypair));
  const refuse = async () => {
    throw new Error("offline demo adapter does not contact RPC");
  };
  umi.rpc.getLatestBlockhash = refuse;
  umi.rpc.sendTransaction = refuse;
  umi.rpc.confirmTransaction = refuse as Umi["rpc"]["confirmTransaction"];
  return umi;
}

export function createLiveUmi(rpcUrl: string, secretB58: string): Umi {
  const umi = createUmi(rpcUrl).use(mplCore());
  const keypair = umi.eddsa.createKeypairFromSecretKey(bs58.decode(secretB58));
  umi.use(keypairIdentity(keypair));
  return umi;
}

export type SignedCreate = {
  txSig: string;
  verified: boolean;
};

/**
 * Build and sign the Core create transaction locally.
 * Does not call sendAndConfirm. A preset blockhash keeps this off the network.
 */
export async function signCreateTransaction(umi: Umi, input: CreateArgs): Promise<SignedCreate> {
  const builder = create(umi, input)
    .useLegacyVersion()
    .setBlockhash({
      blockhash: OFFLINE_BLOCKHASH as Blockhash,
      lastValidBlockHeight: 1,
    });
  const signed = await builder.buildAndSign(umi);
  const signature = signed.signatures[0];
  if (!signature) throw new Error("create signature missing");
  const verified = umi.eddsa.verify(signed.serializedMessage, signature, umi.identity.publicKey);
  if (!verified) throw new Error("create signature did not verify");
  const [txSig] = base58.deserialize(signature);
  if (!txSig) throw new Error("create signature missing");
  return { txSig, verified };
}

/** Live devnet send. Three attempts with backoff. Not used by the demo adapter. */
export async function sendCreateAndConfirm(umi: Umi, input: CreateArgs): Promise<string> {
  let last: unknown;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const sent = await create(umi, input).sendAndConfirm(umi);
      const [txSig] = base58.deserialize(sent.signature);
      if (!txSig) throw new Error("create signature missing");
      return txSig;
    } catch (err) {
      last = err;
      if (attempt < 3) await delay(200 * attempt);
    }
  }
  throw last instanceof Error ? last : new Error("transaction failed");
}

export function newAsset(umi: Umi): { publicKey: string; signer: Signer } {
  const signer = generateSigner(umi);
  return { publicKey: String(signer.publicKey), signer };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
