import type { VoiceState } from "./types";

export const VALID_TRANSITIONS: Record<VoiceState, VoiceState[]> = {
  IDLE: ["LISTENING", "ERROR"],
  LISTENING: ["PROCESSING", "THINKING", "IDLE", "ERROR"],
  PROCESSING: ["THINKING", "LISTENING", "IDLE", "ERROR"],
  THINKING: ["SPEAKING", "LISTENING", "IDLE", "ERROR"],
  SPEAKING: ["LISTENING", "IDLE", "ERROR"],
  ERROR: ["IDLE", "LISTENING"],
};

export function canTransition(from: VoiceState, to: VoiceState): boolean {
  if (to === "ERROR") return true;
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

export const VOICE_STATE_LABELS: Record<VoiceState, string> = {
  IDLE: "Idle",
  LISTENING: "Listening…",
  PROCESSING: "Processing…",
  THINKING: "Thinking…",
  SPEAKING: "Speaking…",
  ERROR: "Error",
};