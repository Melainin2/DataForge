import { Mic } from "lucide-react";
import type { VoiceState } from "@/lib/types";

const STATE_STYLE: Record<VoiceState, { glow: string; pulse: boolean }> = {
  IDLE: { glow: "rgba(129,140,248,0.4)", pulse: false },
  LISTENING: { glow: "rgba(52,211,153,0.55)", pulse: true },
  PROCESSING: { glow: "rgba(129,140,248,0.5)", pulse: true },
  THINKING: { glow: "rgba(192,132,252,0.5)", pulse: true },
  SPEAKING: { glow: "rgba(52,211,153,0.5)", pulse: true },
  ERROR: { glow: "rgba(248,113,113,0.6)", pulse: false },
};

interface MicButtonProps {
  state: VoiceState;
  disabled?: boolean;
  onClick: () => void;
}

export function MicButton({ state, disabled = false, onClick }: MicButtonProps) {
  const style = STATE_STYLE[state];
  const listening = state === "LISTENING";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={listening ? "Stop listening" : "Start listening"}
      aria-pressed={listening}
      className="group relative flex h-44 w-44 items-center justify-center rounded-full outline-none transition-transform duration-200 hover:scale-[1.03] active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
    >
      {style.pulse && (
        <span
          className="absolute inset-0 animate-ping rounded-full"
          style={{ background: style.glow, opacity: 0.25 }}
        />
      )}
      <span
        className="flex h-28 w-28 items-center justify-center rounded-full border bg-white/[0.06] backdrop-blur-xl transition-colors"
        style={{ boxShadow: `0 0 80px 0 ${style.glow}`, borderColor: "rgba(255,255,255,0.12)" }}
      >
        <Mic
          className={`h-12 w-12 transition-colors ${
            listening
              ? "text-emerald-300"
              : "text-slate-200 group-hover:text-white group-disabled:text-slate-400"
          }`}
        />
      </span>
    </button>
  );
}