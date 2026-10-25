const ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/** Decode base58 without a dependency. Returns null when the string is not base58. */
export function decodeBase58(input: string): Uint8Array | null {
  if (input.length === 0) return new Uint8Array();
  // Little-endian accumulation. Start empty so an all-zero key is not double counted.
  const bytes: number[] = [];
  for (let i = 0; i < input.length; i++) {
    const value = ALPHABET.indexOf(input[i] ?? "");
    if (value < 0) return null;
    let carry = value;
    for (let j = 0; j < bytes.length; j++) {
      carry += (bytes[j] ?? 0) * 58;
      bytes[j] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) {
      bytes.push(carry & 0xff);
      carry >>= 8;
    }
  }
  for (let i = 0; input[i] === "1"; i++) bytes.push(0);
  return Uint8Array.from(bytes.reverse());
}

/** True when `value` is a base58 encoding of exactly 32 bytes. */
export function isBase58Pubkey(value: string): boolean {
  if (!value) return false;
  const bytes = decodeBase58(value);
  return bytes !== null && bytes.length === 32;
}

export function explorerAddressUrl(address: string): string {
  return `https://explorer.solana.com/address/${address}?cluster=devnet`;
}

export function explorerTxUrl(signature: string): string {
  return `https://explorer.solana.com/tx/${signature}?cluster=devnet`;
}

/** First 12 hex characters plus an ellipsis. For display, not for verification. */
export function shortHash(hash: string): string {
  return `${hash.slice(0, 12)}…`;
}

/** Accept only explorer links that are explicitly devnet. */
export function isDevnetExplorerUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.hostname === "explorer.solana.com" && parsed.searchParams.get("cluster") === "devnet";
  } catch {
    return false;
  }
}
