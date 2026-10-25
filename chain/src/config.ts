import { Keypair } from "@solana/web3.js";
import bs58 from "bs58";

/** Devnet is the only cluster this service will talk to. */
export const DEVNET_GENESIS = "EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG";
export const MAINNET_GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d";
export const DEFAULT_RPC_URL = "https://api.devnet.solana.com";
export const MIN_BALANCE_SOL = 0.02;
export const LOCAL_PUBLIC_BASE = "http://localhost:8100";

export type ChainMode = "live" | "demo" | "degraded";
export type Env = Record<string, string | undefined>;

/**
 * Public configuration. The signer secret and admin token are private fields
 * so JSON, string conversion, and Node's inspector cannot print them.
 */
export class ChainConfig {
  readonly rpcUrl: string;
  readonly allowedOrigins: readonly string[];
  readonly publicBase: string;
  readonly port: number;
  readonly mode: ChainMode;
  readonly hasSecret: boolean;
  readonly hasAdminToken: boolean;
  payer: string | null;
  readonly #secret?: string;
  readonly #admin?: string;

  constructor(init: {
    rpcUrl: string;
    allowedOrigins: string[];
    publicBase: string;
    port: number;
    mode: ChainMode;
    payer: string | null;
    secret?: string;
    admin?: string;
  }) {
    this.rpcUrl = init.rpcUrl;
    this.allowedOrigins = init.allowedOrigins;
    this.publicBase = init.publicBase;
    this.port = init.port;
    this.mode = init.mode;
    this.payer = init.payer;
    this.hasSecret = Boolean(init.secret);
    this.hasAdminToken = Boolean(init.admin);
    this.#secret = init.secret;
    this.#admin = init.admin;
  }

  secretKey(): string | undefined {
    return this.#secret;
  }

  adminToken(): string | undefined {
    return this.#admin;
  }

  /** Ephemeral demo payer. The real secret, if one was configured, stays unused. */
  attachDemoPayer(payer: string): void {
    if (this.mode !== "demo") {
      throw new Error("demo payer can only be attached in demo mode");
    }
    this.payer = payer;
  }

  toString(): string {
    return `ChainConfig(mode=${this.mode}, payer=${this.payer ?? "none"})`;
  }

  toJSON(): Record<string, unknown> {
    return {
      rpcUrl: this.rpcUrl,
      allowedOrigins: this.allowedOrigins,
      publicBase: this.publicBase,
      port: this.port,
      mode: this.mode,
      payer: this.payer,
      hasSecret: this.hasSecret,
      hasAdminToken: this.hasAdminToken,
    };
  }

  [Symbol.for("nodejs.util.inspect.custom")](): string {
    return this.toString();
  }
}

export function payerFromSecret(secret: string): string | null {
  try {
    const bytes = bs58.decode(secret);
    if (bytes.length !== 64) return null;
    return Keypair.fromSecretKey(bytes).publicKey.toBase58();
  } catch {
    return null;
  }
}

export function loadConfig(env: Env): ChainConfig {
  const rpcUrl = env.SOLANA_RPC_URL?.trim() || DEFAULT_RPC_URL;
  const requested = env.CHAIN_MODE?.trim() ?? "";
  if (requested && requested !== "demo" && requested !== "live") {
    throw new Error(`Unknown CHAIN_MODE "${requested}". Use demo or live.`);
  }

  const admin = env.ADMIN_TOKEN?.trim() || undefined;
  const origins = (env.ALLOWED_ORIGINS ?? "")
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
  const apiHost = env.API_HOST?.trim() ?? "";
  const publicBase = apiHost ? `https://${apiHost}` : LOCAL_PUBLIC_BASE;
  const port = parsePort(env.PORT);

  // Demo mode never loads a signer secret, so a configured key cannot be broadcast.
  if (requested === "demo") {
    return new ChainConfig({
      rpcUrl,
      allowedOrigins: origins,
      publicBase,
      port,
      mode: "demo",
      payer: null,
      admin,
    });
  }

  const secret = env.SOLANA_SECRET_KEY_B58?.trim() || undefined;
  const payer = secret ? payerFromSecret(secret) : null;
  const usable = Boolean(secret && payer);
  return new ChainConfig({
    rpcUrl,
    allowedOrigins: origins,
    publicBase,
    port,
    mode: usable ? "live" : "degraded",
    payer: usable ? payer : null,
    secret: usable ? secret : undefined,
    admin,
  });
}

function parsePort(raw: string | undefined): number {
  if (!raw || raw.trim() === "") return 8100;
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("PORT is not a valid TCP port");
  }
  return port;
}
