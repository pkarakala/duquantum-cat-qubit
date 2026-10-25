import { claimCredential, isChainError, type CredentialBody, type CredentialResult } from "./api";
import { isDevnetExplorerUrl } from "./format";

const PENDING_KEY = "duq.chain.pending";

export type ClaimOptions = {
  apiBase: string;
  learnerId: string;
  alias: string;
  levelsPassed: string[];
  score?: number;
  l8PayloadHash?: string;
};

type PhantomSolana = {
  isPhantom?: boolean;
  connect: () => Promise<{ publicKey: { toString(): string } }>;
};

/**
 * L8 claim panel. Phantom is optional and is never asked to sign:
 * the chain service pays and mints. A failure shows "credential pending: retry"
 * and does not block the rest of the level.
 */
export function mountClaimCredential(el: HTMLElement, opts: ClaimOptions): void {
  el.replaceChildren();
  const status = document.createElement("p");
  status.dataset.role = "status";
  const connectBtn = document.createElement("button");
  connectBtn.type = "button";
  connectBtn.textContent = "Connect Phantom (optional)";
  const custodialBtn = document.createElement("button");
  custodialBtn.type = "button";
  custodialBtn.textContent = "Claim without a wallet";
  el.append(status, connectBtn, custodialBtn);
  setState(el, "idle");
  status.textContent = "";

  const saved = readPending();
  if (saved) {
    void submit(saved, true);
  }

  connectBtn.addEventListener("click", () => {
    void (async () => {
      const wallet = await connectPhantom(status);
      if (!wallet) return;
      await submit(bodyOf(opts, wallet), false);
    })();
  });
  custodialBtn.addEventListener("click", () => {
    void submit(bodyOf(opts, undefined), false);
  });

  async function submit(body: CredentialBody, fromRetry: boolean): Promise<void> {
    setBusy(true);
    setState(el, "minting");
    status.textContent = "Minting…";
    const result = await claimCredential(opts.apiBase, body);
    setBusy(false);
    if (isChainError(result)) {
      writePending(body);
      setState(el, "pending");
      status.textContent = "credential pending: retry";
      return;
    }
    clearPending();
    setState(el, "done");
    renderDone(status, result, fromRetry);
  }

  function setBusy(busy: boolean): void {
    connectBtn.disabled = busy;
    custodialBtn.disabled = busy;
  }
}

function bodyOf(opts: ClaimOptions, wallet: string | undefined): CredentialBody {
  return {
    learner_id: opts.learnerId,
    alias: opts.alias,
    levels_passed: opts.levelsPassed,
    ...(opts.score !== undefined ? { score: opts.score } : {}),
    ...(opts.l8PayloadHash ? { l8_payload_hash: opts.l8PayloadHash } : {}),
    ...(wallet ? { wallet_pubkey: wallet } : {}),
  };
}

function renderDone(status: HTMLElement, result: CredentialResult, _fromRetry: boolean): void {
  status.replaceChildren();
  if (result.demo === true || result.demo_mode === true || result.broadcast === false || result.network === "offline-demo") {
    const label = result.demo_mode
      ? "Demo mode: no Solana key, so this credential was not broadcast."
      : (result.notice ?? "Demo signature only. Signed locally and not broadcast.");
    status.append(document.createTextNode(result.notice ?? label));
    return;
  }
  const url = result.explorer_url;
  if (url && isDevnetExplorerUrl(url)) {
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "View credential on Solana devnet";
    status.append(link);
  }
  if (result.custodial) {
    status.append(document.createTextNode(" held for you by the Academy"));
  }
}

async function connectPhantom(status: HTMLElement): Promise<string | null> {
  const provider = phantom();
  if (!provider) {
    status.textContent = "Phantom is not available. You can claim without a wallet.";
    return null;
  }
  try {
    const connected = await provider.connect();
    return connected.publicKey.toString();
  } catch {
    status.textContent = "Phantom connection was dismissed. You can claim without a wallet.";
    return null;
  }
}

function phantom(): PhantomSolana | undefined {
  const host = window as Window & { phantom?: { solana?: PhantomSolana } };
  const provider = host.phantom?.solana;
  if (provider?.isPhantom) return provider;
  return undefined;
}

function setState(el: HTMLElement, state: "idle" | "minting" | "done" | "pending"): void {
  el.dataset.state = state;
}

function readPending(): CredentialBody | null {
  try {
    const raw = localStorage.getItem(PENDING_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CredentialBody;
    if (!parsed || typeof parsed.learner_id !== "string") return null;
    return parsed;
  } catch {
    return null;
  }
}

function writePending(body: CredentialBody): void {
  try {
    localStorage.setItem(PENDING_KEY, JSON.stringify(body));
  } catch {
    // Private mode can reject storage. The level flow still continues.
  }
}

function clearPending(): void {
  try {
    localStorage.removeItem(PENDING_KEY);
  } catch {
    // Ignore storage failures.
  }
}
