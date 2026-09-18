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
  start: (onData: OnAudioData) => Promise<boolean>;
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
  const zeroGainRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const activeRef = useRef(false);
  const levelRef = useRef(0);
  const onDataRef = useRef<OnAudioData | null>(null);
  const resamplerRef = useRef({ ratio: 0, position: 0 });
  const prevTailRef = useRef(0);
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
    if (zeroGainRef.current) {
      zeroGainRef.current.disconnect();
      zeroGainRef.current = null;
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
    prevTailRef.current = 0;
    onDataRef.current = null;
  }, []);

  const start = useCallback(
    async (onData: OnAudioData): Promise<boolean> => {
      if (activeRef.current) {
        return false;
      }
      if (!navigator.mediaDevices?.getUserMedia || !("AudioContext" in window)) {
        setStatus("unsupported");
        setError("Microphone capture is not supported by this browser.");
        return false;
      }

      activeRef.current = true;
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

        // Keep the audio graph alive without routing mic audio to the speakers.
        const zeroGain = ctx.createGain();
        zeroGain.gain.value = 0;
        zeroGainRef.current = zeroGain;

        resamplerRef.current = { ratio: ctx.sampleRate / TARGET_RATE, position: 0 };
        prevTailRef.current = 0;
        chunkLenRef.current = 0;

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          const length = input.length;

          // Energy measurement for voice activity / waveform fallback.
          let sum = 0;
          for (let i = 0; i < length; i += 4) sum += input[i] * input[i];
          const rms = Math.sqrt(sum / Math.max(length / 4, 1));
          levelRef.current = Math.min(1, rms * 6);

          const { ratio, position } = resamplerRef.current;
          // Keep the output aligned so the carry position stays within (-1, ratio - 1].
          const outCount = length > 0 ? Math.floor((length - 1 - position) / ratio) + 1 : 0;
          if (outCount <= 0) {
            if (length > 0) prevTailRef.current = input[length - 1];
            return;
          }

          const chunk = chunkRef.current;
          let chunkLen = chunkLenRef.current;
          const chunkCap = chunk.length;

          for (let i = 0; i < outCount; i++) {
            const pos = position + i * ratio;
            const i0 = Math.floor(pos);
            const frac = pos - i0;
            // When the carry position is negative the interpolated sample sits
            // between the previous buffer's tail and this buffer's head.
            const s0 = i0 >= 0 ? input[i0] : prevTailRef.current;
            const s1 = i0 >= 0 ? input[Math.min(i0 + 1, length - 1)] : input[0];
            const interpolated = s0 * (1 - frac) + s1 * frac;
            const clamped = Math.max(-1, Math.min(1, interpolated));
            chunk[chunkLen] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
            chunkLen += 1;
            if (chunkLen === chunkCap) {
              onDataRef.current?.(chunk.slice(0));
              chunkLen = 0;
            }
          }

          if (length > 0) prevTailRef.current = input[length - 1];
          resamplerRef.current.position = position + outCount * ratio - length;
          chunkLenRef.current = chunkLen;
        };

        // Wire source -> analyser + processor; route output through a silent gain
        // so onaudioprocess keeps firing without audible feedback.
        source.connect(analyser);
        source.connect(processor);
        processor.connect(zeroGain);
        zeroGain.connect(ctx.destination);

        setStatus("active");
        return true;
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
        return false;
      }
    },
    [cleanup],
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