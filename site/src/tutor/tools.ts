/** ElevenAgents client tools. They drive the same bridge the buttons use. */

import type { AcademyBridge, MountOptions } from "./types";
import { toTutorState } from "./bridge";
import { learnerId } from "./offline";

export const RANGES: Record<string, Record<string, [number, number]>> = {
  L1: { alpha: [0, 3], n: [0, 6] },
  L2: { kappa: [0, 6.283185307179586] },
  L3: { alpha: [0.5, 2.5], kappa2_scale: [0.25, 4] },
  L4: { alpha: [1, 2.5] },
  L5: { alpha2: [1, 9] },
  L6: {},
  L7: { eps_z_over_g2: [0.05, 3] },
  L8: {},
};

function clamp(value: number, range: [number, number]): number {
  return Math.min(range[1], Math.max(range[0], Number(value)));
}

export function makeClientTools(bridge: AcademyBridge, opts: MountOptions) {
  return {
    async set_param(params: { name?: string; value?: number }) {
      const name = String(params?.name ?? "");
      const range = RANGES[bridge.getLevel()]?.[name];
      if (!range) return `Unknown parameter ${name}`;
      const value = clamp(Number(params.value), range);
      bridge.setParam(name, value);
      return `Set ${name} to ${value}`;
    },
    async run_sim() {
      const result = await bridge.run();
      return `${result.summary} (source: ${result.source})`;
    },
    async show_hint(params: { level?: number }) {
      const level = Number(params?.level ?? 1);
      bridge.showHint(level);
      return `Showing hint ${level}`;
    },
    async next_level() {
      bridge.nextLevel();
      return "Next level";
    },
    async ask_tutor(params: { question?: string }) {
      if (opts.askTutor === false) return "ask_tutor is off";
      const state = toTutorState(bridge.getState());
      const response = await fetch(`${opts.apiBase}/api/tutor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          learner_id: opts.learnerId ?? learnerId(),
          level_id: state.level_id,
          message: String(params?.question ?? ""),
          state,
        }),
      });
      if (!response.ok) return "I could not check that. Try the hint ladder.";
      const body = await response.json();
      return String(body.reply ?? "");
    },
  };
}
