/**
 * Schrö's panel. A failed fetch, a 30 s timeout or a 503 becomes a canned or scripted hint.
 * Spoken answers go through /api/voice/tts. The voice agent uses the same client tools.
 */

import { toTutorState } from "./bridge";
import { learnerId, offlineReply } from "./offline";
import { renderTurn } from "./panel";
import { makeClientTools } from "./tools";
import type { AcademyBridge, MountOptions, TutorReply } from "./types";
import { startVoice } from "./voice";

export { bridgeFromController, connectAcademy, stubBridge, toTutorState } from "./bridge";
export { makeClientTools } from "./tools";
export { startVoice } from "./voice";
export type { AcademyBridge, MountOptions, TutorReply } from "./types";

export async function askTutor(message: string, bridge: AcademyBridge, opts: MountOptions): Promise<TutorReply> {
  const state = toTutorState(bridge.getState());
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(`${opts.apiBase}/api/tutor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        learner_id: opts.learnerId ?? learnerId(),
        level_id: state.level_id,
        message,
        state,
      }),
    });
    if (!response.ok) throw new Error(String(response.status));
    return (await response.json()) as TutorReply;
  } catch {
    return offlineReply(message, state.level_id, state.hint_level);
  } finally {
    clearTimeout(timer);
  }
}

async function speak(apiBase: string, text: string) {
  try {
    const response = await fetch(`${apiBase}/api/voice/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.slice(0, 800) }),
    });
    if (!response.ok || typeof Audio === "undefined") return;
    const url = URL.createObjectURL(await response.blob());
    const audio = new Audio(url);
    await audio.play().catch(() => undefined);
  } catch {
    /* The written reply still stands when speech is unavailable. */
  }
}

export function mountTutor(root: HTMLElement, bridge: AcademyBridge, opts: MountOptions) {
  const options = { ...opts, askTutor: opts.askTutor !== false };
  root.innerHTML = `
    <section class="schro">
      <p class="recap" data-testid="recap"></p>
      <ol data-testid="log"></ol>
      <form>
        <label>Ask Schrö <input name="message" /></label>
        <button type="submit">Ask</button>
      </form>
      <button type="button" data-testid="voice">Talk</button>
    </section>`;
  const log = root.querySelector('[data-testid="log"]') as HTMLOListElement;
  const recap = root.querySelector('[data-testid="recap"]') as HTMLElement;
  const form = root.querySelector("form") as HTMLFormElement;
  const input = root.querySelector('input[name="message"]') as HTMLInputElement;
  const tools = makeClientTools(bridge, options);
  const id = options.learnerId ?? learnerId();

  bridge.on("prediction", (payload) => {
    if (payload.correct === true) return;
    fetch(`${options.apiBase}/api/memory/event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        learner_id: id,
        level_id: payload.levelId ?? bridge.getLevel(),
        kind: "wrong_prediction",
        misconception_id: payload.misconceptionId,
        detail: payload.optionId,
      }),
    }).catch(() => undefined);
  });

  const state = toTutorState(bridge.getState());
  fetch(`${options.apiBase}/api/memory/recap?learner_id=${encodeURIComponent(id)}&level_id=${encodeURIComponent(state.level_id)}`)
    .then((response) => (response.ok ? response.json() : null))
    .then((body) => {
      if (body?.recap) recap.textContent = `Welcome back… ${body.recap}`;
    })
    .catch(() => undefined);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    const turn = await askTutor(message, bridge, options);
    renderTurn(log, turn);
    if (turn.source === "gemini") void speak(options.apiBase, turn.reply);
    input.value = "";
  });

  root.querySelector('[data-testid="voice"]')?.addEventListener("click", () => {
    const starter =
      options.startSession ??
      ((session) => {
        const spec = "./voice-sdk.ts";
        return import(/* @vite-ignore */ spec).then((mod: { startElevenSession: (tools: Record<string, unknown>) => Promise<unknown> }) =>
          mod.startElevenSession(session.clientTools),
        );
      });
    void startVoice(starter as Parameters<typeof startVoice>[0], tools as unknown as Record<string, unknown>);
  });

  return { tools, askTutor: (message: string) => askTutor(message, bridge, options) };
}
