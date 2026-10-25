/** Voice session with an injected starter, so tests never load the ElevenLabs SDK. */

export function startVoice(
  startSession: (options: { agentId?: string; clientTools: Record<string, unknown> }) => Promise<unknown>,
  clientTools: Record<string, unknown>,
  agentId?: string,
) {
  return startSession({ agentId, clientTools });
}
