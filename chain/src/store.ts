import { mkdirSync } from "node:fs";
import { readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

export type StoredCredential = {
  asset_address: string;
  tx_sig: string;
  explorer_url: string | null;
  custodial: boolean;
  tx_url: string | null;
  demo: boolean;
  broadcast: boolean;
  network: "devnet" | "offline-demo";
  notice?: string;
};

export type StoredAnchor = {
  label: string;
  sha256: string;
  tx_sig: string;
  explorer_url: string | null;
  ts: string;
  demo?: boolean;
  broadcast?: boolean;
  network?: "devnet" | "offline-demo";
  notice?: string;
};

type CredentialFile = { credentials: Record<string, StoredCredential> };
type AnchorFile = { anchors: StoredAnchor[] };

/**
 * File-backed credential and anchor store. Writes are temp-file then rename.
 * Identical in-flight claims share one promise so a double-click mints once.
 */
export class FileStore {
  readonly dir: string;
  private chain: Promise<void> = Promise.resolve();
  private readonly inflight = new Map<string, Promise<StoredCredential>>();

  constructor(dir: string) {
    this.dir = dir;
    mkdirSync(dir, { recursive: true });
    mkdirSync(path.join(dir, "meta"), { recursive: true });
  }

  async getCredential(key: string): Promise<StoredCredential | null> {
    return this.enqueue(async () => {
      const all = await this.readCredentials();
      return all.credentials[key] ?? null;
    });
  }

  async putCredential(key: string, value: StoredCredential): Promise<void> {
    await this.enqueue(async () => {
      const all = await this.readCredentials();
      all.credentials[key] = value;
      await atomicWrite(this.credentialFile(), JSON.stringify(all));
    });
  }

  /**
   * Run `fn` at most once per key. A stored result is returned as-is.
   * Concurrent callers share the same promise.
   */
  once(key: string, fn: () => Promise<StoredCredential>): Promise<StoredCredential> {
    const pending = this.inflight.get(key);
    if (pending) return pending;
    const run = (async () => {
      const existing = await this.getCredential(key);
      if (existing) return existing;
      const created = await fn();
      await this.putCredential(key, created);
      return created;
    })();
    this.inflight.set(key, run);
    void run.finally(() => {
      if (this.inflight.get(key) === run) this.inflight.delete(key);
    });
    return run;
  }

  async addAnchor(anchor: StoredAnchor): Promise<void> {
    await this.enqueue(async () => {
      const all = await this.readAnchors();
      all.anchors.push(anchor);
      await atomicWrite(this.anchorFile(), JSON.stringify(all));
    });
  }

  async listAnchors(): Promise<StoredAnchor[]> {
    return this.enqueue(async () => {
      const all = await this.readAnchors();
      return all.anchors
        .map((anchor, index) => ({ anchor, index }))
        .sort((a, b) => {
          if (a.anchor.ts === b.anchor.ts) return b.index - a.index;
          return a.anchor.ts < b.anchor.ts ? 1 : -1;
        })
        .map((item) => item.anchor);
    });
  }

  async writeMeta(asset: string, meta: unknown): Promise<void> {
    await atomicWrite(this.metaFile(asset), JSON.stringify(meta));
  }

  async readMeta(asset: string): Promise<unknown | null> {
    return readJson(this.metaFile(asset));
  }

  private credentialFile(): string {
    return path.join(this.dir, "credentials.json");
  }

  private anchorFile(): string {
    return path.join(this.dir, "anchors.json");
  }

  private metaFile(asset: string): string {
    return path.join(this.dir, "meta", `${asset}.json`);
  }

  private async readCredentials(): Promise<CredentialFile> {
    const parsed = await readJson(this.credentialFile());
    if (!parsed || typeof parsed !== "object") return { credentials: {} };
    const credentials = (parsed as CredentialFile).credentials;
    return { credentials: credentials && typeof credentials === "object" ? credentials : {} };
  }

  private async readAnchors(): Promise<AnchorFile> {
    const parsed = await readJson(this.anchorFile());
    if (!parsed || typeof parsed !== "object") return { anchors: [] };
    const anchors = (parsed as AnchorFile).anchors;
    return { anchors: Array.isArray(anchors) ? anchors : [] };
  }

  private enqueue<T>(fn: () => Promise<T>): Promise<T> {
    const run = this.chain.then(fn, fn);
    this.chain = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }
}

async function readJson(file: string): Promise<unknown | null> {
  try {
    const text = await readFile(file, "utf8");
    return JSON.parse(text) as unknown;
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw err;
  }
}

async function atomicWrite(file: string, data: string): Promise<void> {
  const tmp = `${file}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(tmp, data, "utf8");
  await rename(tmp, file);
}
