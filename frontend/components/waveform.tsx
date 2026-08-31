"use client";

import { useEffect, useRef } from "react";
import type { VoiceState } from "@/lib/types";

interface WaveformProps {
  state: VoiceState;
  getLevel: () => number;
  getAnalyser: () => AnalyserNode | null;
}

const BAR_COUNT = 48;
const ACTIVE_COLOR = "rgba(129, 140, 248, 0.95)";
const QUIET_COLOR = "rgba(129, 140, 248, 0.35)";

/**
 * Canvas audio visualization. When the mic is live it draws the AnalyserNode
 * spectrum; otherwise a subtle idle shimmer. Cheap, GPU-friendly rAF loop.
 */
export function Waveform({ state, getLevel, getAnalyser }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = canvas.clientWidth * dpr;
    canvas.height = canvas.clientHeight * dpr;
    ctx.scale(dpr, dpr);

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const gap = 3;
    const barWidth = (width - (BAR_COUNT - 1) * gap) / BAR_COUNT;
    const spectrum = new Uint8Array(32);
    let smooth = 0;
    let previous = performance.now();
    let raf = 0;

    const draw = (now: number) => {
      const dt = Math.min((now - previous) / 1000, 0.1);
      previous = now;
      ctx.clearRect(0, 0, width, height);

      let live = 0;
      if (stateRef.current === "LISTENING") {
        const analyser = getAnalyser();
        if (analyser) {
          analyser.getByteFrequencyData(spectrum);
          let sum = 0;
          let count = 0;
          for (let i = 2; i < 26; i++) {
            sum += spectrum[i];
            count += 1;
          }
          live = Math.min(1, (sum / (count * 255)) * 2.4);
        } else {
          live = getLevel();
        }
      } else if (stateRef.current === "SPEAKING" || stateRef.current === "PROCESSING") {
        live = getLevel();
      }

      const target = Math.max(0.03, live);
      smooth += (target - smooth) * Math.min(1, dt * 9);

      for (let i = 0; i < BAR_COUNT; i++) {
        const center = i / (BAR_COUNT - 1) - 0.5;
        const envelope = Math.exp(-Math.pow(center * 2.4, 2));
        const idle = 0.12 + 0.05 * Math.abs(Math.sin(now / 900 + i * 0.7));
        const barHeightPx =
          (idle + smooth * 4.5 * (0.25 + 0.75 * envelope)) * (height / 2);

        const x = i * (barWidth + gap);
        const y = height / 2 - barHeightPx / 2;
        const color = live > 0.02 ? ACTIVE_COLOR : QUIET_COLOR;

        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeightPx, barWidth / 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.35 + 0.65 * envelope;
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [getLevel, getAnalyser]);

  return (
    <div className="flex h-20 w-full max-w-md justify-center">
      <canvas ref={canvasRef} className="h-full w-full" aria-hidden="true" />
    </div>
  );
}