"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatPanelProps {
  message: Message;
}

export function ChatPanel({ message }: ChatPanelProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3 mb-4", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary-600 text-white"
            : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
        )}
      >
        <div className="prose dark:prose-invert max-w-none text-sm">
          {message.content.split("\n").map((line, i) => (
            <p key={i} className={cn("mb-1 last:mb-0", !line && "h-4")}>
              {line || "\u00A0"}
            </p>
          ))}
          {message.isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>
        <div
          className={cn(
            "text-xs mt-2",
            isUser ? "text-primary-100" : "text-gray-500"
          )}
        >
          {message.timestamp.toLocaleTimeString("th-TH", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
          <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </div>
      )}
    </motion.div>
  );
}
