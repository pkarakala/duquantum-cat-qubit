/**
 * The only importer of the ElevenLabs browser SDK.
 * Client tools are the same functions the panel uses, so a spoken "make the cat bigger"
 * moves the slider through set_param. Dynamic variables carry the learner's level, failed
 * checks and Backboard recap, so the agent adapts to who it is talking to.
 */

import type { MountOptions } from "./types";

/** Public by design (CONTRACT: the agent is public with auth off). The build env overrides it. */
export const DEFAULT_AGENT_ID = "agent_0201m5syr24geva8w2vnjhg36k89";

export function agentId(): string {
  return (import.meta.env?.VITE_ELEVENLABS_AGENT_ID as string | undefined) || DEFAULT_AGENT_ID;
}

export interface VoiceHooks {
  dynamicVariables?: Record<string, string | number | boolean>;
  onStatus?: (status: string) => void;
}

export const MIC_TIMEOUT_MS = 15_000;

/** Ask for the mic first so a denied or ignored prompt fails fast; the SDK opens its own stream. */
async function checkMic(timeoutMs = MIC_TIMEOUT_MS): Promise<void> {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error("microphone unavailable");
  let timer: ReturnType<typeof setTimeout> | undefined;
  const mic = navigator.mediaDevices.getUserMedia({ audio: true });
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("mic timeout")), timeoutMs);
  });
  try {
    const stream = await Promise.race([mic, timeout]);
    stream.getTracks().forEach((track) => track.stop());
  } catch (error) {
    // A prompt answered after the timeout still yields a stream; release it.
    mic.then((stream) => stream.getTracks().forEach((track) => track.stop())).catch(() => undefined);
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * @elevenlabs/client 1.30: clientTools and dynamicVariables are startSession options
 * (BaseConversation.d.ts ClientToolsConfig, BaseConnection.d.ts SessionConfig). They are
 * read once at start; nothing is attached to the conversation object afterwards.
 */
export async function startElevenSession(
  clientTools: Record<string, (params: Record<string, unknown>) => Promise<string>>,
  id = agentId(),
  hooks: VoiceHooks = {},
) {
  const { Conversation } = await import("@elevenlabs/client");
  await checkMic();
  return Conversation.startSession({
    agentId: id,
    clientTools,
    dynamicVariables: hooks.dynamicVariables,
    onStatusChange: ({ status }: { status: string }) => hooks.onStatus?.(status),
    onModeChange: ({ mode }: { mode: string }) => hooks.onStatus?.(mode === "speaking" ? "speaking" : "listening"),
    onError: (message: string) => hooks.onStatus?.(`error: ${message}`),
  });
}

export async function attachWidget(root: HTMLElement, id: string, clientTools: Record<string, unknown>) {
  const widgetSdk = "@elevenlabs/convai-widget-embed";
  await import(/* @vite-ignore */ widgetSdk);
  const widget = document.createElement("elevenlabs-convai");
  widget.setAttribute("agent-id", id);
  widget.addEventListener("elevenlabs-convai:call", (event) => {
    const detail = (event as CustomEvent).detail ?? {};
    detail.config = detail.config ?? {};
    detail.config.clientTools = clientTools;
  });
  root.appendChild(widget);
}

export function agentFromEnv(_opts: MountOptions): string | undefined {
  return agentId() || undefined;
}
