export interface TutorState {
  level_id: string;
  params: Record<string, unknown>;
  prediction?: string;
  misconception_ids: string[];
  last_sim: { summary: string };
  hint_level: number;
  attempts?: number;
}

export interface ToolCall {
  name: string;
  args?: Record<string, unknown>;
  result_summary?: string;
  source?: string;
}

export interface TutorReply {
  reply: string;
  hint_level: number;
  tool_calls: ToolCall[];
  numbers_cited: { text: string; value: number; unit: string | null; source: string }[];
  guard: { passed: boolean; removed: string[] };
  source?: "gemini" | "scripted" | string;
}

/** What the tutor needs from the academy. P2's controller is adapted in bridge.ts. */
export interface AcademyBridge {
  getLevel(): string;
  getState(): TutorState | Record<string, unknown>;
  setParam(name: string, value: number | string): void;
  run(): Promise<{ summary: string; source: string }>;
  showHint(level: number): void;
  nextLevel(): void;
  on(event: string, cb: (payload: Record<string, unknown>) => void): () => void;
}

export interface MountOptions {
  apiBase: string;
  askTutor?: boolean;
  startSession?: (options: { agentId?: string; clientTools: Record<string, (params: Record<string, unknown>) => Promise<string>> }) => Promise<unknown>;
  learnerId?: string;
}
