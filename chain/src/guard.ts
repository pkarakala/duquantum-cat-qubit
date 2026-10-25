import { createHash, timingSafeEqual } from "node:crypto";
import { DEVNET_GENESIS } from "./config.js";

/** The RPC host is not devnet or localhost, or a forbidden override is set. */
export class ClusterRefusedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ClusterRefusedError";
  }
}

/** The RPC could not be reached. The process may stay up in degraded mode. */
export class RpcUnreachableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RpcUnreachableError";
  }
}

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

export type GuardOptions = {
  /** Accept a devnet-shaped host without dialing. Used by the offline demo adapter. */
  skipGenesis?: boolean;
  /**
   * True when the forbidden mainnet override is present in the environment.
   * The override is not honored: the process refuses to start.
   */
  mainnetOverride?: boolean;
};

export function rpcHostname(rpcUrl: string): string {
  let url: URL;
  try {
    url = new URL(rpcUrl);
  } catch {
    throw new ClusterRefusedError("RPC URL is not valid.");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new ClusterRefusedError("RPC URL must be http or https.");
  }
  return url.hostname;
}

/**
 * Allow the URL only for localhost or for a host that both looks like devnet
 * and returns devnet's genesis hash. Anything else refuses to run.
 */
export async function assertDevnet(
  rpcUrl: string,
  getGenesisHash: () => Promise<string>,
  options: GuardOptions = {},
): Promise<void> {
  if (options.mainnetOverride) {
    throw new ClusterRefusedError(
      "Refusing to start because a mainnet override is present. This service is devnet-only.",
    );
  }
  const host = rpcHostname(rpcUrl);
  if (LOCAL_HOSTS.has(host)) return;
  if (!host.includes("devnet")) {
    throw new ClusterRefusedError(`RPC host "${host}" is not devnet. Refusing to start.`);
  }
  if (options.skipGenesis) return;
  let hash: string;
  try {
    hash = await getGenesisHash();
  } catch {
    throw new RpcUnreachableError("RPC did not return a genesis hash.");
  }
  if (hash !== DEVNET_GENESIS) {
    throw new ClusterRefusedError("Genesis hash is not Solana devnet. Refusing to start.");
  }
}

export function fetchGenesisHash(rpcUrl: string, timeoutMs = 4000): () => Promise<string> {
  return async () => {
    const res = await fetch(rpcUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "getGenesisHash" }),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const json = (await res.json()) as { result?: unknown };
    if (typeof json.result !== "string") {
      throw new Error("missing genesis hash");
    }
    return json.result;
  };
}

/** Compare admin tokens by SHA-256 so length differences do not short-circuit. */
export function tokenMatches(provided: string, expected: string): boolean {
  const actual = createHash("sha256").update(provided, "utf8").digest();
  const wanted = createHash("sha256").update(expected, "utf8").digest();
  return timingSafeEqual(actual, wanted);
}
