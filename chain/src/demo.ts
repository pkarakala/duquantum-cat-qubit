import { Keypair } from "@solana/web3.js";
import type { Umi } from "@metaplex-foundation/umi";
import {
  buildCreateInput,
  createOfflineUmi,
  newAsset,
  requireSigner,
  signCreateTransaction,
  type ChainSigner,
  type MintRequest,
} from "./mint.js";
import { signMemoOffline, type SignedMemo } from "./memo.js";

/**
 * Shown on every demo response. The signature is real Ed25519 over the same
 * transaction the live path builds. Nothing is sent to devnet or mainnet.
 */
export const DEMO_NOTICE = "offline-demo: signed locally and not broadcast";

export type DemoAdapter = {
  readonly mode: "demo";
  readonly notice: string;
  readonly payer: string;
  readonly umi: Umi;
  newAsset: () => { publicKey: string; signer: MintRequest["signer"] };
  mint: (input: MintRequest) => Promise<ChainSigner>;
  sendMemo: (memo: string) => Promise<ChainSigner>;
  signMemo: (memo: string) => SignedMemo;
};

/**
 * One ephemeral keypair for the process. It is not loaded from the environment,
 * not written to disk, and not used to broadcast.
 */
export function createDemoAdapter(): DemoAdapter {
  const payer = Keypair.generate();
  const umi = createOfflineUmi(payer.secretKey);
  return {
    mode: "demo",
    notice: DEMO_NOTICE,
    payer: payer.publicKey.toBase58(),
    umi,
    newAsset: () => newAsset(umi),
    mint: async (input) => {
      const created = buildCreateInput({
        asset: requireSigner(input.signer),
        owner: input.owner,
        uri: input.uri,
      });
      const signed = await signCreateTransaction(umi, created);
      return { txSig: signed.txSig, demo: true, broadcast: false };
    },
    sendMemo: async (memo) => {
      const signed = signMemoOffline(payer, memo);
      return { txSig: signed.txSig, demo: true, broadcast: false };
    },
    signMemo: (memo) => signMemoOffline(payer, memo),
  };
}
