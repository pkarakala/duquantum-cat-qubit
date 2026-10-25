/** POST a finished level run to P5. A missing Tiger database must not block the lesson. */

export async function logRun(apiBase: string, body: Record<string, unknown>): Promise<void> {
  if (!apiBase) return;
  const ctrl = new AbortController();
  const kill = setTimeout(() => ctrl.abort(), 3000);
  try {
    await fetch(`${apiBase.replace(/\/$/, '')}/api/runs`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
  } catch {
    /* Logging is best-effort. The level result is already on screen. */
  } finally {
    clearTimeout(kill);
  }
}

export function runRow(levelId: string, learnerId: string, source: string, params: Record<string, unknown>, summary: unknown): Record<string, unknown> {
  const alpha = typeof params.alpha === 'number' ? params.alpha : undefined;
  const browser = source === 'ts' || source === 'in-browser-fallback';
  return {
    engine: browser ? 'ts-cn' : 'dynamiqs 0.3.7',
    model: browser ? 'ts_one_mode' : source === 'server' ? 'two_mode' : 'ts_one_mode',
    params: { ...params, summary: typeof summary === 'string' ? summary : '' },
    params_hash: hashParams({ levelId, params }),
    ...(alpha != null && alpha >= 0 && alpha <= 3 ? { alpha } : {}),
    learner_id: learnerId,
    level_id: levelId,
  };
}

function hashParams(value: unknown): string {
  const text = JSON.stringify(value);
  let hash = 2166136261;
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}
