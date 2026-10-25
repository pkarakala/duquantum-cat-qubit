export type ChainError = { error: { code: string; message: string } };

export type CredentialBody = {
  learner_id: string;
  alias: string;
  wallet_pubkey?: string;
  levels_passed: string[];
  score?: number;
  l8_payload_hash?: string;
};

export type CredentialResult = {
  asset_address: string | null;
  tx_sig: string | null;
  explorer_url: string | null;
  custodial: boolean;
  tx_url?: string | null;
  demo?: boolean;
  demo_mode?: boolean;
  broadcast?: boolean;
  network?: string;
  notice?: string;
};

export type AnchorRow = {
  label: string;
  sha256: string;
  tx_sig: string;
  explorer_url: string | null;
  ts: string;
  demo?: boolean;
  broadcast?: boolean;
  network?: string;
  notice?: string;
};

export function isChainError(value: CredentialResult | { anchors: AnchorRow[] } | ChainError): value is ChainError {
  return "error" in value;
}

async function postJson<T>(url: string, body: unknown, timeoutMs: number): Promise<T | ChainError> {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    const parsed = (await res.json().catch(() => null)) as T | ChainError | null;
    if (!res.ok) {
      if (parsed && typeof parsed === "object" && "error" in parsed) return parsed;
      return { error: { code: "chain_unavailable", message: "request failed" } };
    }
    if (!parsed) return { error: { code: "chain_unavailable", message: "empty response" } };
    return parsed;
  } catch {
    return { error: { code: "chain_unavailable", message: "request failed" } };
  }
}

export async function claimCredential(
  apiBase: string,
  body: CredentialBody,
  opts: { timeoutMs?: number } = {},
): Promise<CredentialResult | ChainError> {
  const timeoutMs = opts.timeoutMs ?? 30000;
  return postJson<CredentialResult>(`${apiBase}/api/chain/credential`, body, timeoutMs);
}

export async function listAnchors(
  apiBase: string,
  opts: { timeoutMs?: number } = {},
): Promise<{ anchors: AnchorRow[] } | ChainError> {
  const timeoutMs = opts.timeoutMs ?? 30000;
  try {
    const res = await fetch(`${apiBase}/api/chain/anchors`, { signal: AbortSignal.timeout(timeoutMs) });
    const parsed = (await res.json().catch(() => null)) as { anchors: AnchorRow[] } | ChainError | null;
    if (!res.ok) {
      if (parsed && typeof parsed === "object" && "error" in parsed) return parsed;
      return { error: { code: "chain_unavailable", message: "request failed" } };
    }
    if (!parsed || !("anchors" in parsed)) {
      return { error: { code: "chain_unavailable", message: "empty response" } };
    }
    return parsed;
  } catch {
    return { error: { code: "chain_unavailable", message: "request failed" } };
  }
}
