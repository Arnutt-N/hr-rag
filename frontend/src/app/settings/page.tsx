"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { 
  ChevronLeft, 
  Key, 
  Save, 
  Check, 
  Eye, 
  EyeOff,
  Globe,
  Building2,
  Settings,
  Plus,
  X,
  ExternalLink
} from "lucide-react";
import Link from "next/link";

interface ApiKeys {
  openai?: string;
  anthropic?: string;
  google?: string;
  groq?: string;
  kimi?: string;
  glm?: string;
  minimax?: string;
  qwen?: string;
  deepseek?: string;
  ring2_5_t?: string;
  custom?: string;
}

interface CustomProviderConfig {
  name: string;
  baseUrl: string;
  modelName: string;
}

const providerGroups = [
  {
    id: "international",
    name: "International",
    icon: Globe,
    providers: [
      {
        key: "openai",
        name: "OpenAI",
        description: "GPT-4, GPT-4o, GPT-3.5-turbo",
        placeholder: "sk-...",
        website: "https://platform.openai.com/api-keys",
      },
      {
        key: "anthropic",
        name: "Anthropic (Claude)",
        description: "Claude 3.5 Sonnet, Claude 3 Opus",
        placeholder: "sk-ant-...",
        website: "https://console.anthropic.com/settings/keys",
      },
      {
        key: "google",
        name: "Google (Gemini)",
        description: "Gemini Pro, Gemini Ultra",
        placeholder: "AIza...",
        website: "https://aistudio.google.com/app/apikey",
      },
      {
        key: "groq",
        name: "Groq",
        description: "Llama 3, Mixtral - เร็วและฟรี",
        placeholder: "gsk_...",
        website: "https://console.groq.com/keys",
      },
    ],
  },
  {
    id: "china",
    name: "� China",
    icon: Building2,
    providers: [
      {
        key: "kimi",
        name: "Kimi (Moonshot AI)",
        description: "บริการ AI จาก Moonshot รองรับบริบทยาว",
        placeholder: "sk-...",
        website: "https://platform.moonshot.cn/",
      },
      {
        key: "glm",
        name: "GLM (Zhipu AI)",
        description: "ChatGLM, GLM-4 Vision",
        placeholder: "...",
        website: "https://open.bigmodel.cn/",
      },
      {
        key: "minimax",
        name: "MiniMax",
        description: "Abab6.5 - AI จาก MiniMax",
        placeholder: "...",
        website: "https://platform.minimax.io/",
      },
      {
        key: "qwen",
        name: "Qwen (Alibaba)",
        description: "Tongyi Qianwen - ราคาถูก เร็ว",
        placeholder: "...",
        website: "https://dashscope.console.aliyun.com/",
      },
      {
        key: "deepseek",
        name: "DeepSeek",
        description: "DeepSeek V3, Coder - ราคาถูก",
        placeholder: "sk-...",
        website: "https://platform.deepseek.com/",
      },
      {
        key: "ring2_5_t",
        name: "Ring2.5-T (DeepSeek)",
        description: "DeepSeek Reasoner - โมเดลตอบคำถามเชิงเหตุผล",
        placeholder: "sk-...",
        website: "https://platform.deepseek.com/",
      },
    ],
  },
  {
    id: "custom",
    name: "Custom",
    icon: Settings,
    providers: [
      {
        key: "custom",
        name: "Custom Provider",
        description: "OpenAI-compatible API endpoint",
        placeholder: "sk-...",
        website: "",
      },
    ],
  },
];

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKeys>({});
  const [customConfig, setCustomConfig] = useState<CustomProviderConfig>({
    name: "",
    baseUrl: "",
    modelName: "",
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState("");
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [expandedGroups, setExpandedGroups] = useState<string[]>(["international", "china", "custom"]);
  const [showCustomForm, setShowCustomForm] = useState(false);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/api/keys", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data.keys || {});
        if (data.customConfig) {
          setCustomConfig(data.customConfig);
        }
      }
    } catch (error) {
      console.error("Failed to fetch API keys:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveApiKeys = async () => {
    setIsSaving(true);
    const token = localStorage.getItem("token");

    try {
      const res = await fetch("http://localhost:8000/api/keys", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          keys: apiKeys,
          customConfig: customConfig,
        }),
      });

      if (res.ok) {
        setSavedMessage("บันทึกสำเร็จ!");
        setTimeout(() => setSavedMessage(""), 3000);
      }
    } catch (error) {
      console.error("Failed to save API keys:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const toggleShowKey = (key: string) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) =>
      prev.includes(groupId)
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId]
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center mb-8">
          <Link
            href="/chat"
            className="mr-4 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-2xl font-bold">ตั้งค่า</h1>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="p-6 mb-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-xl mr-4">
                <Key className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">API Keys</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  ตั้งค่ากุญแจ API สำหรับผู้ให้บริการ LLM ต่างๆ
                </p>
              </div>
            </div>

            {/* Provider Groups */}
            <div className="space-y-4">
              {providerGroups.map((group) => {
                const Icon = group.icon;
                const isExpanded = expandedGroups.includes(group.id);

                return (
                  <div 
                    key={group.id} 
                    className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                  >
                    {/* Group Header */}
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="w-5 h-5 text-gray-500" />
                        <span className="font-medium">{group.name}</span>
                        <span className="text-sm text-gray-500">
                          ({group.providers.length} providers)
                        </span>
                      </div>
                      <ChevronRight 
                        className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                      />
                    </button>

                    {/* Group Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="p-4 space-y-4">
                            {group.providers.map((provider) => (
                              <div key={provider.key}>
                                <div className="flex items-center justify-between mb-2">
                                  <label className="block text-sm font-medium">
                                    {provider.name}
                                    <span className="text-gray-500 font-normal ml-2">
                                      — {provider.description}
                                    </span>
                                  </label>
                                  {provider.website && (
                                    <a
                                      href={provider.website}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                                    >
                                      Get API Key
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                                <div className="relative">
                                  <Input
                                    type={showKeys[provider.key] ? "text" : "password"}
                                    value={apiKeys[provider.key as keyof ApiKeys] || ""}
                                    onChange={(e) =>
                                      setApiKeys({
                                        ...apiKeys,
                                        [provider.key]: e.target.value,
                                      })
                                    }
                                    placeholder={provider.placeholder}
                                    className="pr-10"
                                  />
                                  <button
                                    type="button"
                                    onClick={() => toggleShowKey(provider.key)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                  >
                                    {showKeys[provider.key] ? (
                                      <EyeOff className="w-4 h-4" />
                                    ) : (
                                      <Eye className="w-4 h-4" />
                                    )}
                                  </button>
                                </div>
                              </div>
                            ))}

                            {/* Custom Provider Additional Fields */}
                            {group.id === "custom" && (
                              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <h4 className="text-sm font-medium mb-3">Custom Provider Configuration</h4>
                                <div className="grid gap-3">
                                  <div>
                                    <label className="block text-xs text-gray-500 mb-1">
                                      Provider Name
                                    </label>
                                    <Input
                                      value={customConfig.name}
                                      onChange={(e) =>
                                        setCustomConfig({ ...customConfig, name: e.target.value })
                                      }
                                      placeholder="My Custom Provider"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-xs text-gray-500 mb-1">
                                      Base URL
                                    </label>
                                    <Input
                                      value={customConfig.baseUrl}
                                      onChange={(e) =>
                                        setCustomConfig({ ...customConfig, baseUrl: e.target.value })
                                      }
                                      placeholder="https://api.example.com/v1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block text-xs text-gray-500 mb-1">
                                      Model Name
                                    </label>
                                    <Input
                                      value={customConfig.modelName}
                                      onChange={(e) =>
                                        setCustomConfig({ ...customConfig, modelName: e.target.value })
                                      }
                                      placeholder="model-name"
                                    />
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>

            {/* Save Button */}
            <div className="mt-6 flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
              <div>
                {savedMessage && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-green-600 flex items-center"
                  >
                    <Check className="w-4 h-4 mr-1" />
                    {savedMessage}
                  </motion.p>
                )}
              </div>
              <Button onClick={saveApiKeys} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    กำลังบันทึก...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    บันทึกการตั้งค่า
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Quick Guide Card */}
          <Card className="p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">💡 คู่มือการเลือก Provider</h3>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="font-medium text-green-700 dark:text-green-400 mb-1">🆓 ฟรี / ราคาถูก</div>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• <strong>Groq</strong> - เร็วมาก ฟรี</li>
                  <li>• <strong>Qwen</strong> - เร็ว ราคาถูก</li>
                  <li>• <strong>DeepSeek</strong> - ราคาถูก</li>
                </ul>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="font-medium text-blue-700 dark:text-blue-400 mb-1">⚡ เร็ว</div>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• <strong>Groq</strong> - เร็วที่สุด</li>
                  <li>• <strong>GLM</strong> - เร็ว ฟรี tier</li>
                  <li>• <strong>Google</strong> - เร็ว</li>
                </ul>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <div className="font-medium text-purple-700 dark:text-purple-400 mb-1">👁️ Vision Support</div>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <li>• <strong>OpenAI</strong> - GPT-4o</li>
                  <li>• <strong>Anthropic</strong> - Claude</li>
                  <li>• <strong>Google</strong> - Gemini</li>
                </ul>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">🔒 คำแนะนำด้านความปลอดภัย</h3>
            <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li>• API Keys จะถูกเข้ารหัสก่อนบันทึกในฐานข้อมูล</li>
              <li>• อย่าแชร์ API Keys ของคุณกับผู้อื่น</li>
              <li>• หากสงสัยว่ากุญแจรั่วไหล ให้สร้างใหม่ที่เว็บไซต์ผู้ให้บริการ</li>
              <li>• ใช้งานฟรี Groq สำหรับเริ่มต้นทดสอบระบบ</li>
              <li>• <strong>China Providers</strong> ต้องใช้ VPN ในการเข้าถึง</li>
            </ul>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
