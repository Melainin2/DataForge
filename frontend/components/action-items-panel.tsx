"use client";

import { ClipboardList } from "lucide-react";
import { motion } from "framer-motion";
import type { ActionItem } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  booking: "Booking",
  support_ticket: "Support ticket",
  order: "Order",
  task: "Task",
};

const CATEGORY_STYLES: Record<string, string> = {
  booking: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  support_ticket: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  order: "border-violet-400/30 bg-violet-400/10 text-violet-300",
  task: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
};

export function ActionItemsPanel({ items }: { items: ActionItem[] }) {
  if (items.length === 0) return null;

  return (
    <div className="glass flex w-full max-w-2xl flex-col gap-3 rounded-2xl p-5">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <ClipboardList className="h-4 w-4 text-indigo-300" aria-hidden="true" />
        Action items from this conversation
      </div>
      <ul className="flex flex-col gap-2">
        {items.map((item, index) => (
          <motion.li
            key={`${item.title}-${index}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="flex items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2"
          >
            <span className="text-sm text-slate-100">{item.title}</span>
            <span
              className={`shrink-0 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
                CATEGORY_STYLES[item.category] ?? "border-slate-400/30 bg-slate-400/10 text-slate-300"
              }`}
            >
              {CATEGORY_LABELS[item.category] ?? item.category}
            </span>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
