"use client";

import { useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { ActionItemsPanel } from "@/components/action-items-panel";
import { ConnectionBadge } from "@/components/connection-badge";
import { MicButton } from "@/components/mic-button";
import { TranscriptPanel } from "@/components/transcript-panel";
import { Waveform } from "@/components/waveform";
import { int16ToBase64 } from "@/lib/audio";
import { VOICE_STATE_LABELS } from "@/lib/states";
import { useMicrophone } from "@/hooks/use-microphone";
import { useVoiceSession } from "@/hooks/use-voice-session";

export default function Home() {
  const { connection, voiceState, transcripts, actionItems, lastError, connect, disconnect, send } =
    useVoiceSession();
  const microphone = useMicrophone();

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const toggleListening = useCallback(async () => {
    if (microphone.status === "active" || voiceState === "LISTENING") {
      microphone.stop();
      send({ type: "stop_session" });
      return;
    }
    if (connection !== "CONNECTED") {
      connect(true);
      return;
    }
    const started = await microphone.start((pcm16) =>
      send({ type: "audio", data: int16ToBase64(pcm16) }),
    );
    if (started) {
      send({ type: "start_session" });
    }
  }, [connection, connect, microphone, send, voiceState]);

  const micDisabled =
    connection === "CONNECTING" ||
    connection === "DISCONNECTED" ||
    connection === "RECONNECTING" ||
    microphone.status === "starting";

  const hasError = voiceState === "ERROR" || microphone.status === "unsupported";
  const statusMessage =
    microphone.status === "unsupported"
      ? microphone.error
      : microphone.status === "error"
        ? microphone.error
        : lastError
          ? lastError
          : VOICE_STATE_LABELS[voiceState];

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col items-center px-4 py-8">
      <header className="flex w-full max-w-2xl items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-400" aria-hidden="true" />
          <span className="text-sm font-semibold tracking-wide text-slate-100">
            DataForge
          </span>
          <span className="hidden text-xs text-slate-500 sm:inline">
            — AI Voice Agent
          </span>
        </div>
        <ConnectionBadge state={connection} />
      </header>

      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-6 py-10"
      >
        <h1 className="text-balance text-center text-3xl font-semibold tracking-tight text-slate-50 sm:text-4xl">
          Your voice is the interface
        </h1>

        <div className="flex flex-col items-center gap-5">
          <MicButton state={voiceState} disabled={micDisabled} onClick={toggleListening} />
          <Waveform
            state={voiceState}
            getLevel={microphone.getLevel}
            getAnalyser={microphone.getAnalyser}
          />
          <p
            className={`text-sm font-medium ${
              hasError ? "text-red-300" : "text-slate-400"
            }`}
            role="status"
            aria-live="polite"
          >
            {statusMessage}
          </p>
        </div>
      </motion.section>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
        className="flex w-full max-w-2xl flex-col gap-4 pb-12"
      >
        <TranscriptPanel messages={transcripts} />
        <ActionItemsPanel items={actionItems} />
      </motion.div>
    </main>
  );
}