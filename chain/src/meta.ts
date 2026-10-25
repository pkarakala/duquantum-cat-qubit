import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const CREDENTIAL_NAME = "Cat Qubit Architect";
export const CREDENTIAL_SYMBOL = "DUQ";
export const CREDENTIAL_DESCRIPTION =
  "Completed Cat Qubit Academy (8 levels). Devnet credential, non-transferable.";

export type Attribute = { trait_type: string; value: string };
export type CredentialMetadata = {
  name: string;
  symbol: string;
  description: string;
  image: string;
  attributes: Attribute[];
};

export function explorerAddressUrl(address: string): string {
  return `https://explorer.solana.com/address/${address}?cluster=devnet`;
}

export function explorerTxUrl(signature: string): string {
  return `https://explorer.solana.com/tx/${signature}?cluster=devnet`;
}

export function buildMetadata(input: {
  alias: string;
  levelsPassed: string[];
  score: number | null;
  issuedAt: string;
  contentHash: string;
  publicBase: string;
}): CredentialMetadata {
  return {
    name: CREDENTIAL_NAME,
    symbol: CREDENTIAL_SYMBOL,
    description: CREDENTIAL_DESCRIPTION,
    image: `${input.publicBase}/api/chain/meta/badge.svg`,
    attributes: [
      { trait_type: "levels_passed", value: input.levelsPassed.join(",") },
      { trait_type: "score", value: input.score === null ? "" : String(input.score) },
      { trait_type: "alias", value: input.alias },
      { trait_type: "issued_at", value: input.issuedAt },
      { trait_type: "content_hash", value: input.contentHash },
    ],
  };
}

let badgeCache: string | null = null;

export function badgeSvg(): string {
  if (badgeCache !== null) return badgeCache;
  const here = path.dirname(fileURLToPath(import.meta.url));
  const file = path.resolve(here, "../assets/badge.svg");
  if (!existsSync(file)) {
    throw new Error("badge.svg is missing");
  }
  badgeCache = readFileSync(file, "utf8");
  return badgeCache;
}
