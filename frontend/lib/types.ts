export type VoiceState =
  | "IDLE"
  | "LISTENING"
  | "PROCESSING"
  | "THINKING"
  | "SPEAKING"
  | "ERROR";

export type ConnectionState =
  | "CONNECTING"
  | "CONNECTED"
  | "DISCONNECTED"
  | "RECONNECTING"
  | "ERROR";

export type Speaker = "user" | "agent";

export interface TranscriptMessage {
  id: string;
  speaker: Speaker;
  text: string;
  timestamp: number;
  final: boolean;
}

export type ServerMessage =
  | { type: "connected"; session_id?: string }
  | { type: "state"; state: VoiceState }
  | { type: "partial"; text: string }
  | { type: "final"; text: string }
  | { type: "session_closed" }
  | { type: "pong" }
  | { type: "error"; code: string; message: string };

export type ClientMessage =
  | { type: "start_session" }
  | { type: "audio"; data: string }
  | { type: "stop_session" }
  | { type: "ping" };

export type MicrophoneStatus =
  | "idle"
  | "starting"
  | "active"
  | "error"
  | "unsupported";