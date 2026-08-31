"use client";

import { useCallback, useRef, useState } from "react";
import type { MicrophoneStatus } from "@/lib/types";

const TARGET_RATE = 16000;
/** AssemblyAI recommends audio frames of 50-1000ms; 500ms keeps the sent volume low. */
const CHUNK_SAMPLES = Math.floor(TARGET_RATE * 0.5); // 8000 samples

type OnAudioData = (pcm16: Int16Array) => void;

interface Microphone {
  status: MicrophoneStatus;
  error: string | null;
  start: (onData: OnAudioData) => Promise<void>;
  stop: () => void;
  getLevel: () => number;
  getAnalyser: () => AnalyserNode | null;
}

/**
 * Reusable microphone abstraction.
 * Captures mic audio, resamples it to 16 kHz mono PCM16, and emits fixed-size
 * chunks. Exposes a live level + AnalyserNode for the audio visualization.
 */
export function useMicrophone(): Microphone {
  const [status, setStatus] = useState<MicrophoneStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const ctxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const activeRef = useRef(false);
  const levelRef = useRef(0);
  const onDataRef = useRef<OnAudioData | null>(null);
  const resamplerRef = useRef({ ratio: 0, position: 0 });
  const chunkRef = useRef(new Int16Array(CHUNK_SAMPLES));
  const chunkLenRef = useRef(0);

  const cleanup = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.onaudioprocess = null;
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (ctxRef.current) {
      ctxRef.current.close().catch(() => undefined);
      ctxRef.current = null;
    }
    analyserRef.current = null;
    levelRef.current = 0;
    chunkLenRef.current = 0;
    onDataRef.current = null;
  }, []);

  const start = useCallback(
    async (onData: OnAudioData) => {
      if (activeRef.current || status === "starting") {
        console.warn("microphone already starting/active");
        return;
      }
      if (!navigator.mediaDevices?.getUserMedia || !("AudioContext" in window)) {
        setStatus("unsupported");
        setError("Microphone capture is not supported by this browser.");
        return;
      }

      setStatus("starting");
      setError(null);
      onDataRef.current = onData;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        streamRef.current = stream;

        const AudioContextCtor =
          window.AudioContext ??
          (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const ctx = new AudioContextCtor();
        await ctx.resume();
        ctxRef.current = ctx;

        const source = ctx.createMediaStreamSource(stream);
        sourceRef.current = source;

        const processor = ctx.createScriptProcessor(2048, 1, 1);
        processorRef.current = processor;

        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.7;
        analyserRef.current = analyser;

        resamplerRef.current = { ratio: ctx.sampleRate / TARGET_RATE, position: 0 };
        chunkLenRef.current = 0;

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);

          // Energy measurement for voice activity / waveform fallback.
          let sum = 0;
          for (let i = 0; i < input.length; i += 4) sum += input[i] * input[i];
          const rms = Math.sqrt(sum / (input.length / 4));
          levelRef.current = Math.min(1, rms * 6);

          const { ratio, position } = resamplerRef.current;
          const outCount = Math.floor((input.length - position) / ratio);
          if (outCount <= 0) return;

          const chunk = chunkRef.current;
          let chunkLen = chunkLenRef.current;
          const chunkCap = chunk.length;

          for (let i = 0; i < outCount; i++) {
            const pos = position + i * ratio;
            const i0 = Math.floor(pos);
            const i1 = Math.min(i0 + 1, input.length - 1);
            const frac = pos - i0;
            const sample = input[i0] * (1 - frac) + input[i1] * frac;
            const clamped = Math.max(-1, Math.min(1, sample));
            chunk[chunkLen] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
            chunkLen += 1;
            if (chunkLen === chunkCap) {
              onDataRef.current?.(chunk.slice(0));
              chunkLen = 0;
            }
          }

          resamplerRef.current.position = position + outCount * ratio - input.length;
          chunkLenRef.current = chunkLen;
        };

        // Wire source -> analyser + processor; keep the graph alive via destination.
        source.connect(analyser);
        source.connect(processor);
        processor.connect(ctx.destination);

        activeRef.current = true;
        setStatus("active");
      } catch (err) {
        activeRef.current = false;
        const name = (err as { name?: string }).name;
        const message =
          name === "NotAllowedError" || name === "SecurityError"
            ? "Microphone permission was denied. Allow access and try again."
            : name === "NotFoundError"
              ? "No microphone was found on this device."
              : name === "NotReadableError"
                ? "The microphone is busy or unavailable."
                : "Could not start the microphone.";
        setError(message);
        setStatus("error");
        cleanup();
      }
    },
    [cleanup, status],
  );

  const stop = useCallback(() => {
    activeRef.current = false;
    cleanup();
    setStatus("idle");
    setError(null);
  }, [cleanup]);

  const getLevel = useCallback(() => levelRef.current, []);
  const getAnalyser = useCallback(() => analyserRef.current, []);

  return { status, error, start, stop, getLevel, getAnalyser };
}