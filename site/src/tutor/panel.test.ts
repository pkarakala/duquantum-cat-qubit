/** @vitest-environment jsdom */

import { afterEach, describe, expect, it, vi } from "vitest";
import { mountTutor } from "./index";
import type { AcademyBridge } from "./types";

function bridge() {
  const listeners: Record<string, Array<(payload: Record<string, unknown>) => void>> = {};
  const fake: AcademyBridge & { fire: (event: string, payload: Record<string, unknown>) => void } = {
    getLevel: () => "L7",
    getState: () => ({
      level_id: "L7",
      params: { eps_z_over_g2: 0.2 },
      misconception_ids: [],
      last_sim: { summary: "" },
      hint_level: 1,
    }),
    setParam: () => undefined,
    run: async () => ({ summary: "rings", source: "grid" }),
    showHint: () => undefined,
    nextLevel: () => undefined,
    on: (event, cb) => {
      (listeners[event] ??= []).push(cb);
      return () => undefined;
    },
    fire: (event, payload) => (listeners[event] ?? []).forEach((fn) => fn(payload)),
  };
  return fake;
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("panel", () => {
  it("shows the badge, chips and hint only when numbers were verified", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (String(url).includes("/api/memory/recap")) return json({ recap: "", misconceptions: [] });
      if (String(url).includes("/api/tutor")) {
        return json({
          reply: "It rings at 3.14 MHz.",
          hint_level: 2,
          tool_calls: [{ name: "lookup_grid", args: {}, result_summary: "3.14", source: "grid" }],
          numbers_cited: [{ text: "3.14 MHz", value: 3.14, unit: "MHz", source: "level_constant" }],
          guard: { passed: true, removed: [] },
          source: "gemini",
        });
      }
      return json({}, 503);
    });
    vi.stubGlobal("fetch", fetchMock);
    const root = document.createElement("div");
    mountTutor(root, bridge(), { apiBase: "http://api" });
    const input = root.querySelector("input") as HTMLInputElement;
    input.value = "why does the readout ring?";
    root.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(root.querySelector(".reply")).toBeTruthy());
    expect(root.querySelector('[data-testid="numbers-verified"]')?.textContent).toContain("numbers verified");
    expect(root.querySelector(".chip")?.textContent).toBe("lookup_grid · grid");
    expect(root.querySelector(".hint")?.textContent).toBe("Hint 2 of 4");
    expect(root.querySelector(".offline")).toBeNull();
  });

  it("hides the badge when the guard removed a number", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (String(url).includes("/api/tutor")) {
          return json({
            reply: "maybe 9",
            hint_level: 1,
            tool_calls: [],
            numbers_cited: [],
            guard: { passed: false, removed: ["9"] },
            source: "gemini",
          });
        }
        return json({});
      }),
    );
    const root = document.createElement("div");
    mountTutor(root, bridge(), { apiBase: "http://api" });
    (root.querySelector("input") as HTMLInputElement).value = "hello";
    root.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(root.querySelector(".reply")).toBeTruthy());
    expect(root.querySelector('[data-testid="numbers-verified"]')).toBeNull();
  });

  it("uses the canned readout answer when the tutor is offline, else a scripted hint", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new Error("offline"))));
    const root = document.createElement("div");
    mountTutor(root, bridge(), { apiBase: "http://api" });
    const input = root.querySelector("input") as HTMLInputElement;
    input.value = "why does the readout ring?";
    root.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(root.textContent).toContain("3.14 MHz"));
    expect(root.querySelector(".offline")?.textContent).toBe("offline");

    input.value = "hello there";
    root.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(root.textContent).toContain("Predict."));
  });

  it("posts a memory event when the prediction is wrong", async () => {
    const urls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        urls.push(String(url));
        if (String(url).includes("/api/memory/event")) {
          expect(init?.method).toBe("POST");
          const body = JSON.parse(String(init?.body));
          expect(body.kind).toBe("wrong_prediction");
          expect(body.misconception_id).toBe("M3");
          return json({ ok: true });
        }
        return json({ recap: "still on M3", misconceptions: ["M3"] });
      }),
    );
    const root = document.createElement("div");
    const fake = bridge();
    mountTutor(root, fake, { apiBase: "http://api", learnerId: "learner-1" });
    fake.fire("prediction", { levelId: "L2", optionId: "B", correct: false, misconceptionId: "M3" });
    await vi.waitFor(() => expect(urls.some((url) => url.includes("/api/memory/event"))).toBe(true));
    await vi.waitFor(() => expect(root.querySelector('[data-testid="recap"]')?.textContent).toContain("Welcome back"));
  });
});
