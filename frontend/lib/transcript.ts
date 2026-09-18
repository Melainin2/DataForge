import type { Speaker, TranscriptMessage } from "./types";

let counter = 0;

function nextId(): string {
  counter += 1;
  return `m-${Date.now()}-${counter}`;
}

/**
 * Merge a streaming user transcript into the list.
 * A running partial replaces the previous partial; a final resolves it.
 */
export function upsertUserTranscript(
  messages: TranscriptMessage[],
  text: string,
  final: boolean,
  confidence?: number,
): TranscriptMessage[] {
  const last = messages[messages.length - 1];
  if (last && last.speaker === "user" && !last.final) {
    return [...messages.slice(0, -1), { ...last, text, final, confidence }];
  }
  return [
    ...messages,
    { id: nextId(), speaker: "user" as Speaker, text, timestamp: Date.now(), final, confidence },
  ];
}

/** Append a completed agent reply as a distinct conversation message. */
export function appendAgentMessage(
  messages: TranscriptMessage[],
  text: string,
  needsConfirmation?: boolean,
): TranscriptMessage[] {
  return [
    ...messages,
    {
      id: nextId(),
      speaker: "agent" as Speaker,
      text,
      timestamp: Date.now(),
      final: true,
      needsConfirmation,
    },
  ];
}