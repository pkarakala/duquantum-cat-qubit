import { createHash } from "node:crypto";
import bs58 from "bs58";

export class BadRequest extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BadRequest";
  }
}

const LEVELS = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8"] as const;
const ALIAS = /^[A-Za-z0-9 _.\-]{1,24}$/;
const SHA256_HEX = /^[0-9a-f]{64}$/;
const LABEL = /^[a-z0-9._-]{1,32}$/;
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ASSET = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

export type CredentialInput = {
  learnerId: string;
  alias: string;
  walletPubkey: string | null;
  levelsPassed: string[];
  score: number | null;
  l8PayloadHash: string | null;
};

export type AnchorInput = {
  sha256: string;
  label: string;
};

export function isAssetAddress(value: string): boolean {
  return ASSET.test(value);
}

export function decodePubkey(value: string): Uint8Array | null {
  try {
    const bytes = bs58.decode(value);
    return bytes.length === 32 ? bytes : null;
  } catch {
    return null;
  }
}

export function normalizeLevels(input: unknown): string[] {
  if (!Array.isArray(input) || input.length === 0) {
    throw new BadRequest("levels_passed must be a non-empty list");
  }
  const seen = new Set<string>();
  for (const item of input) {
    if (typeof item !== "string" || !LEVELS.includes(item as (typeof LEVELS)[number])) {
      throw new BadRequest("levels_passed contains an unknown level");
    }
    seen.add(item);
  }
  if (!seen.has("L8")) {
    throw new BadRequest("levels_passed must include L8");
  }
  return LEVELS.filter((level) => seen.has(level));
}

export function validateCredential(body: unknown): CredentialInput {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new BadRequest("body must be an object");
  }
  const record = body as Record<string, unknown>;
  const learnerId = record.learner_id;
  if (typeof learnerId !== "string" || !UUID_V4.test(learnerId)) {
    throw new BadRequest("learner_id must be a UUID v4");
  }
  const alias = record.alias;
  if (typeof alias !== "string" || !ALIAS.test(alias)) {
    throw new BadRequest("alias must match ^[A-Za-z0-9 _.\\-]{1,24}$");
  }
  let walletPubkey: string | null = null;
  if (record.wallet_pubkey !== undefined && record.wallet_pubkey !== null) {
    if (typeof record.wallet_pubkey !== "string" || !decodePubkey(record.wallet_pubkey)) {
      throw new BadRequest("wallet_pubkey must be a base58 32-byte public key");
    }
    walletPubkey = record.wallet_pubkey;
  }
  const levelsPassed = normalizeLevels(record.levels_passed);
  let score: number | null = null;
  if (record.score !== undefined && record.score !== null) {
    if (typeof record.score !== "number" || !Number.isFinite(record.score)) {
      throw new BadRequest("score must be a finite number");
    }
    score = record.score;
  }
  let l8PayloadHash: string | null = null;
  if (record.l8_payload_hash !== undefined && record.l8_payload_hash !== null) {
    if (typeof record.l8_payload_hash !== "string" || !SHA256_HEX.test(record.l8_payload_hash)) {
      throw new BadRequest("l8_payload_hash must be 64 lowercase hex characters");
    }
    l8PayloadHash = record.l8_payload_hash;
  }
  return { learnerId, alias, walletPubkey, levelsPassed, score, l8PayloadHash };
}

export function validateAnchor(body: unknown): AnchorInput {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new BadRequest("body must be an object");
  }
  const record = body as Record<string, unknown>;
  if (typeof record.sha256 !== "string" || !SHA256_HEX.test(record.sha256)) {
    throw new BadRequest("sha256 must be 64 lowercase hex characters");
  }
  if (typeof record.label !== "string" || !LABEL.test(record.label)) {
    throw new BadRequest("label must match ^[a-z0-9._-]{1,32}$");
  }
  return { sha256: record.sha256, label: record.label };
}

/** Live idempotency key. Levels are already sorted. Demo uses a separate tag. */
export function credentialKey(learnerId: string, levelsPassed: string[], demo: boolean): string {
  const material = `${learnerId}:${levelsPassed.join(",")}`;
  const tagged = demo ? `demo\0${material}` : material;
  return createHash("sha256").update(tagged, "utf8").digest("hex");
}

/**
 * sha256 of canonical JSON with sorted keys alias, levels_passed, score.
 * Used when the claim does not carry an L8 payload hash.
 */
export function canonicalContentHash(
  alias: string,
  levelsPassed: string[],
  score: number | null,
): string {
  const canonical = JSON.stringify({ alias, levels_passed: levelsPassed, score });
  return createHash("sha256").update(canonical, "utf8").digest("hex");
}

export function memoText(label: string, sha256: string): string {
  return `duq-academy:${label}:${sha256}`;
}
