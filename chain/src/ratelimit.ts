import type { Context } from "hono";
import { getConnInfo } from "@hono/node-server/conninfo";

const HOUR_MS = 60 * 60 * 1000;

/** In-memory sliding window. One process, which matches a single chain container. */
export class SlidingWindowLimiter {
  private readonly hits = new Map<string, number[]>();

  constructor(
    private readonly limit: number,
    private readonly windowMs: number,
    private readonly now: () => number,
  ) {}

  /** Return true when the call is allowed and recorded. */
  allow(key: string): boolean {
    const t = this.now();
    const start = t - this.windowMs;
    const recent = (this.hits.get(key) ?? []).filter((ts) => ts > start);
    if (recent.length >= this.limit) {
      this.hits.set(key, recent);
      return false;
    }
    recent.push(t);
    this.hits.set(key, recent);
    return true;
  }
}

export function credentialLimiter(now: () => number): SlidingWindowLimiter {
  return new SlidingWindowLimiter(5, HOUR_MS, now);
}

export function anchorLimiter(now: () => number): SlidingWindowLimiter {
  return new SlidingWindowLimiter(10, HOUR_MS, now);
}

/** First X-Forwarded-For hop, which Caddy sets, otherwise the socket address. */
export function clientIp(c: Context): string {
  const forwarded = c.req.header("x-forwarded-for");
  if (forwarded) {
    const first = forwarded.split(",")[0]?.trim();
    if (first) return first;
  }
  try {
    const address = getConnInfo(c).remote.address;
    if (address) return address;
  } catch {
    // app.request has no socket. Fall through.
  }
  return "unknown";
}
