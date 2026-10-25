import canned from "./canned.json";
import { HINTS } from "./hints";
import type { TutorReply } from "./types";

export function learnerId(): string {
  const key = "duq.learner_id";
  try {
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const created = crypto.randomUUID();
    localStorage.setItem(key, created);
    return created;
  } catch {
    return "00000000-0000-4000-8000-000000000000";
  }
}

export function matchCanned(message: string) {
  const haystack = message.toLowerCase();
  return (canned as Array<{ level_id: string; keywords: string[]; reply: string; numbers: { value: number; source?: string; record_id?: string }[] }>).find(
    (entry) => entry.keywords.every((word) => haystack.includes(word.toLowerCase())),
  );
}

export function offlineReply(message: string, levelId: string, hintLevel: number): TutorReply {
  const hit = matchCanned(message);
  if (hit) {
    return {
      reply: hit.reply,
      hint_level: hintLevel,
      tool_calls: [],
      numbers_cited: hit.numbers.map((number) => ({
        text: String(number.value),
        value: number.value,
        unit: null,
        source: number.record_id ? `record:${number.record_id}` : number.source || "level_constant",
      })),
      guard: { passed: true, removed: [] },
      source: "scripted",
    };
  }
  const hints = HINTS[levelId] ?? HINTS.L1;
  const hint = Math.min(4, Math.max(1, hintLevel || 1));
  return {
    reply: hints[hint - 1],
    hint_level: hint,
    tool_calls: [],
    numbers_cited: [],
    guard: { passed: true, removed: [] },
    source: "scripted",
  };
}
