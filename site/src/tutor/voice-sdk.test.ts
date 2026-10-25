import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const startSession = vi.fn(async (_options: Record<string, unknown>) => ({ endSession: vi.fn(async () => undefined) }));
vi.mock("@elevenlabs/client", () => ({ Conversation: { startSession } }));

import { mountTutor } from "./index";
import { makeClientTools } from "./tools";
import type { AcademyBridge } from "./types";
import { startElevenSession } from "./voice-sdk";

const TOOL_NAMES = ["set_param", "run_sim", "show_hint", "next_level", "ask_tutor"];

function bridge(overrides: Partial<AcademyBridge> = {}): AcademyBridge {
  return {
    getLevel: () => "L3",
    getState: () => ({ level_id: "L3", params: { alpha: 2 }, misconception_ids: [], last_sim: { summary: "" }, hint_level: 1 }),
    setParam: vi.fn(),
    run: vi.fn(async () => ({ summary: "plateau 1.41", source: "ts" })),
    showHint: vi.fn(),
    nextLevel: vi.fn(),
    on: () => () => undefined,
    ...overrides,
  };
}

function stubMic(impl: () => Promise<unknown>) {
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia: vi.fn(impl) } });
}

const stream = () => ({ getTracks: () => [{ stop: vi.fn() }] });

beforeEach(() => {
  startSession.mockClear();
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, json: async () => ({}) })));
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("ElevenLabs session start", () => {
  it("passes clientTools and dynamicVariables to Conversation.startSession", async () => {
    stubMic(async () => stream());
    const tools = makeClientTools(bridge(), { apiBase: "http://api" });
    const vars = { level: "L3", failed_attempts: "0" };
    await startElevenSession(tools as never, "agent-x", { dynamicVariables: vars });
    expect(startSession).toHaveBeenCalledOnce();
    const options = startSession.mock.calls[0][0];
    expect(options.agentId).toBe("agent-x");
    expect(Object.keys(options.clientTools as object)).toEqual(TOOL_NAMES);
    expect(options.dynamicVariables).toEqual(vars);
    expect(typeof options.onStatusChange).toBe("function");
    expect(typeof options.onError).toBe("function");
  });

  it("the Talk button starts a session with the learner's dynamic variables", async () => {
    stubMic(async () => stream());
    const root = document.createElement("div");
    mountTutor(root, bridge(), { apiBase: "http://api" });
    const button = root.querySelector('[data-testid="voice"]') as HTMLButtonElement;
    button.click();
    await vi.waitFor(() => expect(startSession).toHaveBeenCalledOnce());
    const options = startSession.mock.calls[0][0];
    expect(Object.keys(options.clientTools as object)).toEqual(TOOL_NAMES);
    expect(options.dynamicVariables).toMatchObject({ level: "L3", failed_attempts: "0", hint_level: "1" });
    await vi.waitFor(() => expect(button.textContent).toBe("End call · listening"));
  });

  it("a denied mic never starts a session and the button recovers", async () => {
    stubMic(async () => {
      throw new Error("NotAllowedError");
    });
    const root = document.createElement("div");
    mountTutor(root, bridge(), { apiBase: "http://api" });
    const button = root.querySelector('[data-testid="voice"]') as HTMLButtonElement;
    button.click();
    await vi.waitFor(() => expect(button.textContent).toBe("Talk (mic or agent unavailable)"));
    expect(startSession).not.toHaveBeenCalled();
  });

  it("an unanswered mic prompt times out after 15 s", async () => {
    vi.useFakeTimers();
    stubMic(() => new Promise(() => undefined));
    const pending = startElevenSession({}, "agent-x").catch((error: Error) => error.message);
    await vi.advanceTimersByTimeAsync(15_000);
    expect(await pending).toBe("mic timeout");
    expect(startSession).not.toHaveBeenCalled();
  });
});

describe("client tools never throw", () => {
  it("run_sim returns the error as a string", async () => {
    const tools = makeClientTools(
      bridge({ run: vi.fn(async () => Promise.reject(new Error("Choose a prediction before running."))) }),
      { apiBase: "http://api" },
    );
    expect(await tools.run_sim()).toBe("run_sim failed: Choose a prediction before running.");
  });

  it("ask_tutor returns a string when the network fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));
    const tools = makeClientTools(bridge(), { apiBase: "http://api" });
    expect(await tools.ask_tutor({ question: "why?" })).toMatch(/could not reach/i);
  });

  it("set_param maps the real control names and rejects a non-number", async () => {
    const fake = bridge();
    const tools = makeClientTools(fake, { apiBase: "http://api" });
    expect(await tools.set_param({ name: "scale", value: 9 })).toBe("Set scale to 4");
    expect(await tools.set_param({ name: "kappa2_scale", value: "0.25" })).toBe("Set scale to 0.25");
    expect(await tools.set_param({ name: "alpha", value: "big" })).toMatch(/numeric/);
    expect(fake.setParam).toHaveBeenCalledTimes(2);
  });

  it("L7 readout uses the eps control", async () => {
    const fake = bridge({ getLevel: () => "L7" });
    const tools = makeClientTools(fake, { apiBase: "http://api" });
    expect(await tools.set_param({ name: "eps", value: 1 })).toBe("Set eps to 1");
    expect(fake.setParam).toHaveBeenCalledWith("eps", 1);
  });
});
