/**
 * The only importer of the ElevenLabs browser SDK.
 * Client tools are the same functions the panel uses, so a spoken "make the cat bigger"
 * moves the slider through set_param.
 */

import type { MountOptions } from "./types";

export async function startElevenSession(
  clientTools: Record<string, (params: Record<string, unknown>) => Promise<string>>,
  agentId = import.meta.env?.VITE_ELEVENLABS_AGENT_ID as string | undefined,
) {
  const sdk = "@elevenlabs/client";
  const { Conversation } = await import(/* @vite-ignore */ sdk);
  return Conversation.startSession({ agentId, clientTools });
}

export async function attachWidget(root: HTMLElement, agentId: string, clientTools: Record<string, unknown>) {
  const widgetSdk = "@elevenlabs/convai-widget-embed";
  await import(/* @vite-ignore */ widgetSdk);
  const widget = document.createElement("elevenlabs-convai");
  widget.setAttribute("agent-id", agentId);
  widget.addEventListener("elevenlabs-convai:call", (event) => {
    const detail = (event as CustomEvent).detail ?? {};
    detail.config = detail.config ?? {};
    detail.config.clientTools = clientTools;
  });
  root.appendChild(widget);
}

export function agentFromEnv(opts: MountOptions): string | undefined {
  return import.meta.env?.VITE_ELEVENLABS_AGENT_ID;
}
