"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { upsertUserTranscript } from "@/lib/transcript";
import { canTransition } from "@/lib/states";
import type {
  ClientMessage,
  ConnectionState,
  ServerMessage,
  TranscriptMessage,
  VoiceState,
} from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/voice";

const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RETRY_MS = 600;

/**
 * Centralized lifecycle for the browser <-> backend WebSocket.
 * Owns the connection state machine, transcript merging, and voice state.
 */
export function useVoiceSession() {
  const [connection, setConnection] = useState<ConnectionState>("CONNECTING");
  const [voiceState, setVoiceState] = useState<VoiceState>("IDLE");
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);
  const [lastError, setLastError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const attemptsRef = useRef(0);
  const reconnectEnabledRef = useRef(true);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const queueRef = useRef<ClientMessage[]>([]);
  const closedByUsRef = useRef(false);

  const applyServerState = useCallback((next: VoiceState) => {
    setVoiceState((prev) => {
      if (canTransition(prev, next)) return next;
      if (next === "ERROR") return "ERROR";
      console.warn(`ignored invalid voice transition: ${prev} -> ${next}`);
      return prev;
    });
  }, []);

  const handleError = useCallback(
    (message: string) => {
      setLastError(message);
      applyServerState("ERROR");
    },
    [applyServerState],
  );

  const handleServerMessage = useCallback(
    (msg: ServerMessage) => {
      switch (msg.type) {
        case "connected":
          break;
        case "state":
          applyServerState(msg.state);
          break;
        case "partial":
          setTranscripts((prev) => upsertUserTranscript(prev, msg.text, false));
          break;
        case "final":
          setTranscripts((prev) => upsertUserTranscript(prev, msg.text, true));
          break;
        case "session_closed":
          applyServerState("IDLE");
          break;
        case "error":
          handleError(msg.message);
          break;
        case "pong":
          break;
      }
    },
    [applyServerState, handleError],
  );

  const clearSocket = useCallback(() => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(
    (manual = false) => {
      if (manual) {
        reconnectEnabledRef.current = true;
        attemptsRef.current = 0;
      }
      if (
        wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING)
      ) {
        return;
      }
      closedByUsRef.current = false;

      if (!("WebSocket" in window)) {
        setConnection("ERROR");
        setLastError("This browser does not support WebSockets.");
        return;
      }

      setConnection(attemptsRef.current > 0 ? "RECONNECTING" : "CONNECTING");
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        attemptsRef.current = 0;
        setConnection("CONNECTED");
        setLastError(null);
        for (const msg of queueRef.current) {
          ws.send(JSON.stringify(msg));
        }
        queueRef.current = [];
      };

      ws.onmessage = (event) => {
        try {
          handleServerMessage(JSON.parse(String(event.data)) as ServerMessage);
        } catch {
          handleError("Received a malformed message from the server.");
        }
      };

      ws.onerror = () => {
        // onclose carries the reconnect/error semantics
      };

      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null;
        if (closedByUsRef.current) {
          setConnection("DISCONNECTED");
          return;
        }
        if (!reconnectEnabledRef.current || attemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setConnection(attemptsRef.current > 0 ? "ERROR" : "DISCONNECTED");
          return;
        }
        attemptsRef.current += 1;
        setConnection("RECONNECTING");
        const delay = Math.min(BASE_RETRY_MS * 2 ** (attemptsRef.current - 1), 8000);
        retryTimerRef.current = setTimeout(() => connect(false), delay);
      };
    },
    [handleError, handleServerMessage],
  );

  const disconnect = useCallback(() => {
    reconnectEnabledRef.current = false;
    closedByUsRef.current = true;
    clearSocket();
    setConnection("DISCONNECTED");
  }, [clearSocket]);

  useEffect(() => {
    return () => {
      reconnectEnabledRef.current = false;
      closedByUsRef.current = true;
      clearSocket();
    };
  }, [clearSocket]);

  /** Send a message; queue it until the socket is open. */
  const send = useCallback((message: ClientMessage) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      queueRef.current.push(message);
    }
  }, []);

  return {
    connection,
    voiceState,
    transcripts,
    lastError,
    connect,
    disconnect,
    send,
  };
}