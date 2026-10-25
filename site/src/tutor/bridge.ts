/**
 * The only tutor file that imports the academy (P2).
 * Until that package is in the tree, connectAcademy() returns a labeled stub.
 */

import type { AcademyBridge, TutorState } from "./types";

export function toTutorState(raw: TutorState | Record<string, unknown>, attempts = 0): TutorState {
  const state = raw as Record<string, unknown>;
  if (typeof state.level_id === "string") {
    return { ...(raw as TutorState), attempts: (raw as TutorState).attempts ?? attempts };
  }
  const last = (state.lastSim as { summary?: string } | undefined) ?? { summary: "" };
  return {
    level_id: String(state.levelId ?? "L1"),
    params: (state.params as Record<string, unknown>) ?? {},
    prediction: state.prediction as string | undefined,
    misconception_ids: (state.misconceptionIds as string[]) ?? [],
    last_sim: { summary: last.summary ?? "" },
    hint_level: Number(state.hintLevel ?? 1),
    attempts,
  };
}

export function bridgeFromController(
  controller: {
    getLevelState: () => Record<string, unknown>;
    setParam: (name: string, value: number | string) => void;
    runSim: () => Promise<{ summary?: string; source?: string }>;
    showHint: (level?: number) => void;
    nextLevel: () => void;
  },
  events: { on: (type: string, fn: (payload: Record<string, unknown>) => void) => () => void },
): AcademyBridge {
  let attempts = 0;
  events.on("check", (payload) => {
    if (payload.pass === false) attempts += 1;
  });
  return {
    getLevel: () => String(controller.getLevelState().levelId ?? "L1"),
    getState: () => toTutorState(controller.getLevelState(), attempts),
    setParam: (name, value) => controller.setParam(name, value),
    run: async () => {
      const result = await controller.runSim();
      return { summary: result.summary ?? "", source: result.source ?? "academy" };
    },
    showHint: (level) => controller.showHint(level),
    nextLevel: () => controller.nextLevel(),
    on: (event, cb) => events.on(event, cb),
  };
}

export function stubBridge(): AcademyBridge {
  const state: TutorState = {
    level_id: "L1",
    params: { alpha: 2.1 },
    misconception_ids: [],
    last_sim: { summary: "" },
    hint_level: 1,
    attempts: 0,
  };
  const listeners: Record<string, Array<(payload: Record<string, unknown>) => void>> = {};
  return {
    getLevel: () => state.level_id,
    getState: () => state,
    setParam: (name, value) => {
      state.params[name] = value;
    },
    run: async () => ({ summary: "stub sim", source: "stub" }),
    showHint: (level) => {
      state.hint_level = level;
    },
    nextLevel: () => undefined,
    on: (event, cb) => {
      (listeners[event] ??= []).push(cb);
      return () => {
        listeners[event] = (listeners[event] ?? []).filter((fn) => fn !== cb);
      };
    },
  };
}

export async function connectAcademy(): Promise<AcademyBridge> {
  try {
    const spec = "../academy/index.ts";
    const mod = (await import(/* @vite-ignore */ spec)) as {
      getLevelState: () => Record<string, unknown>;
      setParam: (name: string, value: number | string) => void;
      runSim: () => Promise<{ summary?: string; source?: string; result?: { summary?: string } } | null>;
      showHint: (level?: number) => void;
      nextLevel: () => void;
      on: (type: string, fn: (payload: Record<string, unknown>) => void) => () => void;
    };
    return bridgeFromController(
      {
        getLevelState: () => mod.getLevelState(),
        setParam: (name, value) => mod.setParam(name, value),
        runSim: async () => {
          const outcome = await mod.runSim();
          return {
            summary: outcome?.summary ?? outcome?.result?.summary ?? "",
            source: outcome?.source ?? "academy",
          };
        },
        showHint: (level) => {
          mod.showHint(level);
        },
        nextLevel: () => mod.nextLevel(),
      },
      { on: mod.on },
    );
  } catch {
    return stubBridge();
  }
}
