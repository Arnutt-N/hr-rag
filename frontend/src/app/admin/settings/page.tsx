"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Save,
  AlertTriangle,
  ToggleLeft,
  ToggleRight,
  Server,
  Cpu,
  Globe,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

interface SystemSettings {
  default_llm_provider: string;
  default_embedding_model: string;
  system_rate_limit: number;
  maintenance_mode: boolean;
  feature_flags: {
    guest_access: boolean;
    public_projects: boolean;
    api_key_management: boolean;
    evaluation: boolean;
  };
}

export default function AdminSettings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/admin/settings", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;
    
    setIsSaving(true);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch("http://localhost:8000/admin/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setMessage("Settings saved successfully!");
        setTimeout(() => setMessage(""), 3000);
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">System Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure system-wide settings
        </p>
      </div>

      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-green-100 text-green-800 rounded-lg"
        >
          {message}
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LLM Settings */}
        <Card className="p-6">
          <div className="flex items-center mb-6">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-xl mr-4">
              <Cpu className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">LLM Configuration</h2>
              <p className="text-sm text-gray-500">Default provider and model settings</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Default LLM Provider
              </label>
              <select
                value={settings?.default_llm_provider}
                onChange={(e) =>
                  setSettings({ ...settings!, default_llm_provider: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
                <option value="groq">Groq</option>
                <option value="kimi">Kimi</option>
                <option value="glm">GLM</option>
                <option value="minimax">MiniMax</option>
                <option value="qwen">Qwen</option>
                <option value="deepseek">DeepSeek</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Default Embedding Model
              </label>
              <Input
                value={settings?.default_embedding_model}
                onChange={(e) =>
                  setSettings({ ...settings!, default_embedding_model: e.target.value })
                }
              />
            </div>
          </div>
        </Card>

        {/* Rate Limiting */}
        <Card className="p-6">
          <div className="flex items-center mb-6">
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-xl mr-4">
              <Server className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Rate Limiting</h2>
              <p className="text-sm text-gray-500">Control request limits</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              System Rate Limit (requests/minute)
            </label>
            <Input
              type="number"
              value={settings?.system_rate_limit}
              onChange={(e) =>
                setSettings({
                  ...settings!,
                  system_rate_limit: parseInt(e.target.value),
                })
              }
            />
          </div>
        </Card>

        {/* Feature Flags */}
        <Card className="p-6">
          <div className="flex items-center mb-6">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-xl mr-4">
              <Globe className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Feature Flags</h2>
              <p className="text-sm text-gray-500">Enable or disable features</p>
            </div>
          </div>

          <div className="space-y-4">
            {[
              { key: "guest_access", label: "Guest Access", desc: "Allow users to chat without login" },
              { key: "public_projects", label: "Public Projects", desc: "Allow projects to be public" },
              { key: "api_key_management", label: "API Key Management", desc: "Users can manage their API keys" },
              { key: "evaluation", label: "Evaluation Module", desc: "Enable RAG evaluation features" },
            ].map((feature) => (
              <div
                key={feature.key}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div>
                  <p className="font-medium">{feature.label}</p>
                  <p className="text-sm text-gray-500">{feature.desc}</p>
                </div>
                <button
                  onClick={() =>
                    setSettings({
                      ...settings!,
                      feature_flags: {
                        ...settings!.feature_flags,
                        [feature.key]: !settings!.feature_flags[feature.key as keyof typeof settings.feature_flags],
                      },
                    })
                  }
                  className="p-2"
                >
                  {settings?.feature_flags[feature.key as keyof typeof settings.feature_flags] ? (
                    <ToggleRight className="w-8 h-8 text-green-600" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </Card>

        {/* Maintenance Mode */}
        <Card className="p-6 border-red-200 dark:border-red-800">
          <div className="flex items-center mb-6">
            <div className="p-3 bg-red-100 dark:bg-red-900 rounded-xl mr-4">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-red-600">Maintenance Mode</h2>
              <p className="text-sm text-gray-500">Temporarily disable the system</p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Maintenance Mode</p>
              <p className="text-sm text-red-500">
                Only admins will be able to access the system
              </p>
            </div>
            <button
              onClick={() =>
                setSettings({ ...settings!, maintenance_mode: !settings!.maintenance_mode })
              }
              className="p-2"
            >
              {settings?.maintenance_mode ? (
                <ToggleRight className="w-8 h-8 text-red-600" />
              ) : (
                <ToggleLeft className="w-8 h-8 text-gray-400" />
              )}
            </button>
          </div>
        </Card>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <Button onClick={saveSettings} disabled={isSaving}>
          {isSaving ? (
            <>
              <LoadingSpinner size="sm" className="mr-2" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
