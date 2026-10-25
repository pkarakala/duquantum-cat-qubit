import { Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import { describe, expect, it } from "vitest";
import {
  explorerAddressUrl,
  explorerTxUrl,
  isBase58Pubkey,
  isDevnetExplorerUrl,
  shortHash,
} from "../../site/src/chain/format.ts";

describe("site format", () => {
  it("builds devnet explorer urls, short hashes, and pubkey checks", () => {
    const address = Keypair.generate().publicKey.toBase58();
    expect(explorerAddressUrl(address)).toBe(`https://explorer.solana.com/address/${address}?cluster=devnet`);
    expect(explorerTxUrl("sig")).toBe("https://explorer.solana.com/tx/sig?cluster=devnet");
    expect(shortHash("0123456789abcdef")).toBe("0123456789ab…");
    expect(isBase58Pubkey(address)).toBe(true);
    for (let i = 0; i < 20; i++) {
      expect(isBase58Pubkey(Keypair.generate().publicKey.toBase58())).toBe(true);
    }
    expect(isBase58Pubkey("11111111111111111111111111111111")).toBe(true);
    expect(isBase58Pubkey("")).toBe(false);
    expect(isBase58Pubkey("0OIl")).toBe(false);
    expect(isBase58Pubkey(bs58.encode(Buffer.alloc(31, 4)))).toBe(false);
    expect(isDevnetExplorerUrl(explorerTxUrl("sig"))).toBe(true);
    expect(isDevnetExplorerUrl("https://explorer.solana.com/tx/sig")).toBe(false);
    expect(isDevnetExplorerUrl("https://explorer.solana.com/tx/sig?cluster=mainnet")).toBe(false);
  });
});
