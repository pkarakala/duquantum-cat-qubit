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
import { agentId } from "./voice-sdk";

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

  let failed = 0;
  bridge.on("check", (payload) => {
    if (payload.passed === false) failed += 1;
  });
  const voiceButton = root.querySelector('[data-testid="voice"]') as HTMLButtonElement | null;
  type Call = { endSession?: () => Promise<void> };
  let call: Call | null = null;
  if (voiceButton && !options.startSession && !agentId()) voiceButton.hidden = true;
  const learnerVars = () => {
    const s = toTutorState(bridge.getState(), failed);
    return {
      level: s.level_id,
      level_title: document.querySelector("#app h1, #app h2")?.textContent?.trim().slice(0, 80) || s.level_id,
      hint_level: String(s.hint_level ?? 1),
      failed_attempts: String(failed),
      recap: recap.textContent?.replace(/^Welcome back…\s*/, "") || "new learner, no history yet",
      last_sim: s.last_sim?.summary || "none yet",
      params: JSON.stringify(s.params ?? {}).slice(0, 200),
    };
  };
  voiceButton?.addEventListener("click", async () => {
    if (call) {
      await call.endSession?.().catch(() => undefined);
      call = null;
      voiceButton.textContent = "Talk";
      return;
    }
    voiceButton.textContent = "Connecting…";
    const status = (st: string) => {
      if (!call && st !== "connecting") return;
      voiceButton.textContent = st.startsWith("error") || st === "disconnected" ? "Talk" : `End call · ${st}`;
      if (st === "disconnected") call = null;
    };
    try {
      if (options.startSession) {
        call = (await startVoice(options.startSession as Parameters<typeof startVoice>[0], tools as unknown as Record<string, unknown>)) as unknown as Call;
      } else {
        const mod = await import("./voice-sdk");
        call = (await mod.startElevenSession(tools as never, mod.agentId(), { dynamicVariables: learnerVars(), onStatus: status })) as unknown as Call;
      }
      voiceButton.textContent = "End call · listening";
    } catch {
      call = null;
      voiceButton.textContent = "Talk (mic or agent unavailable)";
    }
  });

  return { tools, askTutor: (message: string) => askTutor(message, bridge, options) };
}
