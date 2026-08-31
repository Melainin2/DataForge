import type { ConnectionState } from "@/lib/types";

const CONFIG: Record<ConnectionState, { label: string; dot: string }> = {
  CONNECTING: { label: "Connecting", dot: "bg-amber-400 animate-pulse" },
  CONNECTED: { label: "Online", dot: "bg-emerald-400" },
  DISCONNECTED: { label: "Offline", dot: "bg-zinc-400" },
  RECONNECTING: { label: "Reconnecting", dot: "bg-amber-400 animate-pulse" },
  ERROR: { label: "Connection error", dot: "bg-red-400" },
};

export function ConnectionBadge({ state }: { state: ConnectionState }) {
  const cfg = CONFIG[state];
  return (
    <div className="glass flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium text-slate-200">
      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </div>
  );
}