/** ElevenAgents client tools. They drive the same bridge the buttons use. */

import type { AcademyBridge, MountOptions } from "./types";
import { toTutorState } from "./bridge";
import { learnerId } from "./offline";

/** Keys are the academy control names (site/src/academy/levels/L*.ts `controls[].name`). */
export const RANGES: Record<string, Record<string, [number, number]>> = {
  L1: { alpha: [0, 3], n: [0, 6] },
  L2: { kappa: [0, 6.283185307179586] },
  L3: { alpha: [0.5, 2.5], scale: [0.25, 4] },
  L4: { alpha: [1, 2.5] },
  L5: { alpha2: [1, 9] },
  L6: {},
  L7: { eps: [0.05, 3] },
  L8: {},
};

/** Names an agent prompt may still use; mapped to the real control names. */
const ALIASES: Record<string, string> = { kappa2_scale: "scale", eps_z_over_g2: "eps" };

function clamp(value: number, range: [number, number]): number {
  return Math.min(range[1], Math.max(range[0], value));
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** The SDK forwards the returned string to the agent; a throw would surface as onError mid-call. */
function safe<P>(name: string, fn: (params: P) => Promise<string>) {
  return async (params: P): Promise<string> => {
    try {
      return await fn((params ?? {}) as P);
    } catch (error) {
      return `${name} failed: ${errorText(error)}`;
    }
  };
}

export function makeClientTools(bridge: AcademyBridge, opts: MountOptions) {
  return {
    set_param: safe("set_param", async (params: { name?: string; value?: number | string }) => {
      const raw = String(params.name ?? "");
      const name = ALIASES[raw] ?? raw;
      const level = bridge.getLevel();
      const range = RANGES[level]?.[name];
      if (!range) {
        const known = Object.keys(RANGES[level] ?? {}).join(", ") || "none";
        return `Unknown parameter ${raw} on ${level}. Known: ${known}`;
      }
      const numeric = Number(params.value);
      if (!Number.isFinite(numeric)) return `set_param needs a numeric value for ${name}`;
      const value = clamp(numeric, range);
      bridge.setParam(name, value);
      return `Set ${name} to ${value}`;
    }),
    run_sim: safe("run_sim", async () => {
      const result = await bridge.run();
      return `${result.summary} (source: ${result.source})`;
    }),
    show_hint: safe("show_hint", async (params: { level?: number | string }) => {
      const parsed = Math.round(Number(params.level ?? 1));
      const level = Number.isFinite(parsed) ? Math.min(4, Math.max(1, parsed)) : 1;
      bridge.showHint(level);
      return `Showing hint ${level}`;
    }),
    next_level: safe("next_level", async () => {
      bridge.nextLevel();
      return "Next level";
    }),
    ask_tutor: safe("ask_tutor", async (params: { question?: string }) => {
      if (opts.askTutor === false) return "ask_tutor is off";
      const state = toTutorState(bridge.getState());
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 20_000);
      try {
        const response = await fetch(`${opts.apiBase}/api/tutor`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            learner_id: opts.learnerId ?? learnerId(),
            level_id: state.level_id,
            message: String(params.question ?? ""),
            state,
          }),
        });
        if (!response.ok) return "I could not check that. Try the hint ladder.";
        const body = await response.json();
        return String(body?.reply ?? "") || "The tutor had no answer. Try the hint ladder.";
      } catch {
        return "I could not reach the tutor. Try the hint ladder.";
      } finally {
        clearTimeout(timer);
      }
    }),
  };
}
