/**
 * Pseudonymous learner id and local progress.
 * No names, no emails. Every storage call is guarded; memory is the fallback.
 */

export interface LevelProgress {
  passed: boolean;
  predictionCorrect: boolean;
  attempts: number;
  ts: number;
}

export type ProgressMap = Partial<Record<string, LevelProgress>>;

const ID_KEY = 'duq.learner_id';
const PROGRESS_KEY = 'duq.progress.v1';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

let memoryId: string | undefined;
let memoryProgress: ProgressMap = {};

function uuidV4(): string {
  const cryptoObj = globalThis.crypto;
  if (cryptoObj?.randomUUID) return cryptoObj.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoObj.getRandomValues(bytes);
  bytes[6] = (bytes[6]! & 0x0f) | 0x40;
  bytes[8] = (bytes[8]! & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function readStorage(key: string): string | null {
  try {
    return globalThis.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): boolean {
  try {
    globalThis.localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

export function getLearnerId(): string {
  try {
    const existing = readStorage(ID_KEY);
    if (existing && UUID.test(existing)) {
      memoryId = existing;
      return existing;
    }
    const id = memoryId && UUID.test(memoryId) ? memoryId : uuidV4();
    memoryId = id;
    writeStorage(ID_KEY, id);
    return id;
  } catch {
    if (!memoryId || !UUID.test(memoryId)) memoryId = uuidV4();
    return memoryId;
  }
}

export function getProgress(): ProgressMap {
  try {
    const raw = readStorage(PROGRESS_KEY);
    if (!raw) return { ...memoryProgress };
    const parsed = JSON.parse(raw) as ProgressMap;
    if (!parsed || typeof parsed !== 'object') return { ...memoryProgress };
    memoryProgress = parsed;
    return { ...parsed };
  } catch {
    return { ...memoryProgress };
  }
}

export function saveProgress(levelId: string, rec: LevelProgress): void {
  try {
    const next = getProgress();
    next[levelId] = rec;
    memoryProgress = next;
    writeStorage(PROGRESS_KEY, JSON.stringify(next));
  } catch {
    memoryProgress = { ...memoryProgress, [levelId]: rec };
  }
}
