import { describe, expect, it, vi } from "vitest";
import { makeClientTools } from "./tools";
import { startVoice } from "./voice";
import type { AcademyBridge } from "./types";

function bridge(level = "L1"): AcademyBridge & { setParam: ReturnType<typeof vi.fn>; run: ReturnType<typeof vi.fn>; showHint: ReturnType<typeof vi.fn>; nextLevel: ReturnType<typeof vi.fn> } {
  return {
    getLevel: () => level,
    getState: () => ({
      level_id: level,
      params: { alpha: 1 },
      misconception_ids: [],
      last_sim: { summary: "" },
      hint_level: 1,
    }),
    setParam: vi.fn(),
    run: vi.fn(async () => ({ summary: "n = 4.41", source: "live-one-mode" })),
    showHint: vi.fn(),
    nextLevel: vi.fn(),
    on: () => () => undefined,
  };
}

describe("client tools", () => {
  it("calls the bridge and clamps a slider", async () => {
    const fake = bridge("L1");
    const tools = makeClientTools(fake, { apiBase: "http://api", askTutor: true });
    expect(await tools.set_param({ name: "alpha", value: 9 })).toBe("Set alpha to 3");
    expect(fake.setParam).toHaveBeenCalledWith("alpha", 3);
    expect(await tools.run_sim()).toContain("source: live-one-mode");
    expect(fake.run).toHaveBeenCalledOnce();
    await tools.show_hint({ level: 2 });
    expect(fake.showHint).toHaveBeenCalledWith(2);
    await tools.next_level();
    expect(fake.nextLevel).toHaveBeenCalledOnce();
  });

  it("does not touch the bridge for an unknown parameter", async () => {
    const fake = bridge("L1");
    const tools = makeClientTools(fake, { apiBase: "http://api" });
    const message = await tools.set_param({ name: "not_a_knob", value: 1 });
    expect(message).toMatch(/unknown/i);
    expect(fake.setParam).not.toHaveBeenCalled();
  });

  it("hands the tools to the voice session", async () => {
    const startSession = vi.fn(async () => ({ ok: true }));
    const tools = makeClientTools(bridge(), { apiBase: "http://api" });
    await startVoice(startSession, tools, "agent-1");
    expect(startSession).toHaveBeenCalledWith({ agentId: "agent-1", clientTools: tools });
    expect(Object.keys(tools)).toEqual(["set_param", "run_sim", "show_hint", "next_level", "ask_tutor"]);
  });
});
