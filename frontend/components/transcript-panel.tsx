"use client";

import { useEffect, useRef } from "react";
import { Bot, User } from "lucide-react";
import { motion } from "framer-motion";
import type { TranscriptMessage } from "@/lib/types";

export function TranscriptPanel({ messages }: { messages: TranscriptMessage[] }) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages]);

  return (
    <div className="glass flex max-h-72 min-h-40 w-full max-w-2xl flex-col gap-4 overflow-y-auto rounded-2xl p-5">
      {messages.length === 0 ? (
        <p className="m-auto text-center text-sm text-slate-400">
          Speak to start a conversation.
        </p>
      ) : (
        messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="flex items-start gap-3"
          >
            <span
              className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border ${
                message.speaker === "user"
                  ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                  : message.needsConfirmation
                    ? "border-amber-400/30 bg-amber-400/10 text-amber-300"
                    : "border-indigo-400/30 bg-indigo-400/10 text-indigo-300"
              }`}
            >
              {message.speaker === "user" ? (
                <User className="h-3.5 w-3.5" />
              ) : (
                <Bot className="h-3.5 w-3.5" />
              )}
            </span>
            <div className="flex flex-col gap-1">
              <p
                className={`text-sm leading-relaxed ${
                  message.final ? "text-slate-100" : "text-slate-300"
                } ${message.needsConfirmation ? "italic text-amber-200" : ""}`}
              >
                {message.text}
                {!message.final && <span className="text-slate-500">…</span>}
              </p>
              {message.speaker === "user" &&
                message.final &&
                typeof message.confidence === "number" &&
                message.confidence < 0.55 && (
                  <span className="w-fit rounded-full border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-[11px] font-medium text-amber-300">
                    Low confidence — {Math.round(message.confidence * 100)}%
                  </span>
                )}
            </div>
          </motion.div>
        ))
      )}
      <div ref={endRef} />
    </div>
  );
}