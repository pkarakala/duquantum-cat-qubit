import {
  Connection,
  Keypair,
  PublicKey,
  Transaction,
  TransactionInstruction,
  sendAndConfirmTransaction,
} from "@solana/web3.js";
import bs58 from "bs58";

/** Official Solana Memo program. The anchor is a memo, not a token transfer. */
export const MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr";

/**
 * Blockhash used only by the offline demo adapter. It is a valid 32-byte
 * base58 value so the transaction can be signed and verified. It is not a
 * recent blockhash and must never be broadcast.
 */
export const OFFLINE_BLOCKHASH = "11111111111111111111111111111111";

export function buildMemoInstruction(payer: PublicKey, memo: string): TransactionInstruction {
  return new TransactionInstruction({
    programId: new PublicKey(MEMO_PROGRAM_ID),
    keys: [{ pubkey: payer, isSigner: true, isWritable: false }],
    data: Buffer.from(memo, "utf8"),
  });
}

/** Shared signing path. Demo stops here. Live broadcast fetches a real blockhash first. */
export function signMemoTransaction(payer: Keypair, memo: string, recentBlockhash: string): Transaction {
  const tx = new Transaction({ recentBlockhash, feePayer: payer.publicKey });
  tx.add(buildMemoInstruction(payer.publicKey, memo));
  tx.sign(payer);
  if (!tx.verifySignatures() || !tx.signature) {
    throw new Error("memo signature did not verify");
  }
  return tx;
}

export function memoSignature(tx: Transaction): string {
  if (!tx.signature) throw new Error("memo signature missing");
  return bs58.encode(tx.signature);
}

export type SignedMemo = {
  txSig: string;
  verified: boolean;
  memo: string;
  transaction: Transaction;
};

export function signMemoOffline(payer: Keypair, memo: string): SignedMemo {
  const transaction = signMemoTransaction(payer, memo, OFFLINE_BLOCKHASH);
  return {
    txSig: memoSignature(transaction),
    verified: true,
    memo,
    transaction,
  };
}

/**
 * Broadcast a memo on the configured cluster. Retries three times.
 * This is the live path. The demo adapter does not call it.
 */
export async function broadcastMemo(
  connection: Connection,
  payer: Keypair,
  memo: string,
): Promise<string> {
  let last: unknown;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const ix = buildMemoInstruction(payer.publicKey, memo);
      return await sendAndConfirmTransaction(connection, new Transaction().add(ix), [payer], {
        commitment: "confirmed",
      });
    } catch (err) {
      last = err;
      if (attempt < 3) await delay(200 * attempt);
    }
  }
  throw last instanceof Error ? last : new Error("transaction failed");
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
