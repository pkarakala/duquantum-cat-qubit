/** Tiny pub/sub. P4 and P5 subscribe; the UI does not own their network calls. */

type Handler = (payload: unknown) => void;

const listeners = new Map<string, Set<Handler>>();

export function on(type: string, fn: Handler): () => void {
  let set = listeners.get(type);
  if (!set) {
    set = new Set();
    listeners.set(type, set);
  }
  set.add(fn);
  return () => set!.delete(fn);
}

export function emit(type: string, payload: unknown): void {
  const set = listeners.get(type);
  if (!set) return;
  for (const fn of [...set]) fn(payload);
}

/** Test isolation. Not part of the learner API. */
export function resetListeners(): void {
  listeners.clear();
}
