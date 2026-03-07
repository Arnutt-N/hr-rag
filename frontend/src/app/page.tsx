"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ProviderSelector } from "@/components/chat/ProviderSelector";
import { FileUpload } from "@/components/chat/FileUpload";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import {
  Sparkles,
  MessageSquare,
  ArrowRight,
  Shield,
  Zap,
  Globe,
} from "lucide-react";
import Link from "next/link";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("openai");

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          provider: selectedProvider,
          history: messages,
        }),
      });

      if (!res.ok) throw new Error("Failed to get response");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              assistantContent += parsed.content || "";
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessage.id
                    ? { ...msg, content: assistantContent }
                    : msg
                )
              );
            } catch (e) {
              // Ignore
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50 dark:from-gray-900 dark:to-gray-800">
      {/* Hero Section */}
      <div className="container mx-auto px-4 pt-12 pb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-3xl mx-auto"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-6 shadow-lg">
            <Sparkles className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
            HR-RAG Assistant
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
            ผู้ช่วยอัจฉริยะสำหรับงาน HR ด้วย AI พร้อมระบบ RAG
            <br />
            อัปโหลดเอกสาร สรุปข้อมูล และสนทนาได้ทันที
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/chat">
              <Button size="lg" className="gap-2">
                <MessageSquare className="w-5 h-5" />
                เริ่มแชททันที
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="gap-2">
                เข้าสู่ระบบ
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </div>

      {/* Demo Chat Section */}
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="max-w-3xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden"
        >
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center">
              <MessageSquare className="w-5 h-5 text-primary-600 mr-2" />
              <span className="font-semibold">ทดลองใช้งาน (ไม่ต้องลงชื่อเข้าใช้)</span>
            </div>
            <ProviderSelector
              value={selectedProvider}
              onChange={setSelectedProvider}
            />
          </div>

          <div className="h-80 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <FileUpload
                  onUpload={(files) => console.log("Uploaded:", files)}
                  className="w-full max-w-sm"
                />
                <p className="mt-4 text-gray-500">
                  หรือพิมพ์คำถามด้านล่างเพื่อเริ่มสนทนา
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <ChatPanel key={message.id} message={message} />
              ))
            )}
          </div>

          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="พิมพ์คำถามของคุณ..."
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700"
              />
              <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
                {isLoading ? <LoadingSpinner size="sm" /> : "ส่ง"}
              </Button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center mb-12">ฟีเจอร์หลัก</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: <Globe className="w-8 h-8 text-primary-600" />,
              title: "รองรับภาษาไทย",
              description:
                "ระบบ Embedding และ LLM ที่ถูกปรับแต่งสำหรับภาษาไทยโดยเฉพาะ",
            },
            {
              icon: <Zap className="w-8 h-8 text-yellow-500" />,
              title: "หลายผู้ให้บริการ",
              description:
                "เลือกใช้ OpenAI, Claude, Gemini หรือ Groq ตามต้องการ",
            },
            {
              icon: <Shield className="w-8 h-8 text-green-500" />,
              title: "ความปลอดภัย",
              description:
                "ข้อมูลแยกตามโปรเจกต์ ไม่แชร์ข้ามผู้ใช้ พร้อมเข้ารหัส API Keys",
            },
          ].map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg text-center"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-2xl mb-4">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-600 dark:text-gray-400">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
