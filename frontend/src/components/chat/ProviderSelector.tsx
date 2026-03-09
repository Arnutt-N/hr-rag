"use client";

import { useState } from "react";
import { LLM_PROVIDERS, type LLMProvider } from "@/types";
import { 
  ChevronDown, 
  Bot, 
  Zap, 
  Eye, 
  Workflow, 
  Globe, 
  Building2,
  Settings,
  ChevronRight
} from "lucide-react";

interface ProviderSelectorProps {
  value: string;
  onChange: (value: string) => void;
  customConfig?: {
    baseUrl?: string;
    modelName?: string;
  };
  onCustomConfigChange?: (config: { baseUrl: string; modelName: string }) => void;
}

const providerIcons: Record<string, React.ReactNode> = {
  openai: <span className="text-lg">🔵</span>,
  anthropic: <span className="text-lg">🟤</span>,
  google: <span className="text-lg">🟢</span>,
  groq: <span className="text-lg">🟣</span>,
  kimi: <span className="text-lg">🌙</span>,
  glm: <span className="text-lg">🔷</span>,
  minimax: <span className="text-lg">🟡</span>,
  qwen: <span className="text-lg">🟠</span>,
  deepseek: <span className="text-lg">🔵</span>,
  "ring2.5-t": <span className="text-lg">💠</span>,
  custom: <Settings className="w-4 h-4" />,
};

const costLabels: Record<string, string> = {
  free: "ฟรี",
  $: "ถูก",
  $$: "ปานกลาง",
  $$$: "แพง",
};

const speedLabels: Record<string, string> = {
  fast: "เร็ว",
  medium: "ปานกลาง",
  slow: "ช้า",
};

export function ProviderSelector({ 
  value, 
  onChange, 
  customConfig,
  onCustomConfigChange 
}: ProviderSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedProvider = LLM_PROVIDERS.find((p) => p.id === value);

  const internationalProviders = LLM_PROVIDERS.filter(p => p.region === "international" && p.id !== "custom");
  const chinaProviders = LLM_PROVIDERS.filter(p => p.region === "china");
  const customProvider = LLM_PROVIDERS.find(p => p.id === "custom");

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 pr-8 text-sm hover:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
      >
        {selectedProvider && (
          <>
            <span className="text-lg">{providerIcons[selectedProvider.id] || <Bot className="w-4 h-4" />}</span>
            <span className="font-medium">{selectedProvider.name}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
              {selectedProvider.cost === "free" ? "🆓" : selectedProvider.cost === "$" ? "💲" : selectedProvider.cost === "$$" ? "💰" : "💎"}
            </span>
          </>
        )}
        <ChevronDown className={`w-4 h-4 text-gray-500 absolute right-2 pointer-events-none transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute z-20 mt-1 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
            
            {/* International Providers */}
            <div className="p-2">
              <div className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <Globe className="w-3 h-3" />
                International
              </div>
              {internationalProviders.map((provider) => (
                <ProviderOption
                  key={provider.id}
                  provider={provider}
                  isSelected={value === provider.id}
                  onClick={() => {
                    onChange(provider.id);
                    setIsOpen(false);
                  }}
                  icon={providerIcons[provider.id]}
                />
              ))}
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700" />

            {/* China Providers */}
            <div className="p-2">
              <div className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <Building2 className="w-3 h-3" />
                🇨🇳 China
              </div>
              {chinaProviders.map((provider) => (
                <ProviderOption
                  key={provider.id}
                  provider={provider}
                  isSelected={value === provider.id}
                  onClick={() => {
                    onChange(provider.id);
                    setIsOpen(false);
                  }}
                  icon={providerIcons[provider.id]}
                />
              ))}
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700" />

            {/* Custom Provider */}
            {customProvider && (
              <div className="p-2">
                <div className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <Settings className="w-3 h-3" />
                  Custom
                </div>
                <ProviderOption
                  key={customProvider.id}
                  provider={customProvider}
                  isSelected={value === customProvider.id}
                  onClick={() => {
                    onChange(customProvider.id);
                    setIsOpen(false);
                  }}
                  icon={providerIcons[customProvider.id]}
                />
              </div>
            )}
          </div>
        </>
      )}

      {/* Custom Provider Config */}
      {value === "custom" && onCustomConfigChange && (
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg space-y-2">
          <input
            type="text"
            placeholder="Base URL (e.g., https://api.example.com/v1)"
            value={customConfig?.baseUrl || ""}
            onChange={(e) => onCustomConfigChange({ 
              ...customConfig, 
              baseUrl: e.target.value,
              modelName: customConfig?.modelName || ""
            })}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary-500"
          />
          <input
            type="text"
            placeholder="Model name"
            value={customConfig?.modelName || ""}
            onChange={(e) => onCustomConfigChange({ 
              ...customConfig, 
              baseUrl: customConfig?.baseUrl || "",
              modelName: e.target.value
            })}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}
    </div>
  );
}

interface ProviderOptionProps {
  provider: LLMProvider;
  isSelected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
}

function ProviderOption({ provider, isSelected, onClick, icon }: ProviderOptionProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors ${
        isSelected 
          ? "bg-primary-100 dark:bg-primary-900/30 border border-primary-300 dark:border-primary-700" 
          : "hover:bg-gray-100 dark:hover:bg-gray-700"
      }`}
    >
      <div className="flex items-center gap-2">
        {icon}
        <div>
          <div className="font-medium text-sm">{provider.name}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{provider.description}</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {/* Cost indicator */}
        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700" title={`Cost: ${costLabels[provider.cost]}`}>
          {provider.cost === "free" ? "🆓" : provider.cost === "$" ? "💲" : provider.cost === "$$" ? "💰" : "💎"}
        </span>
        {/* Speed indicator */}
        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700" title={`Speed: ${speedLabels[provider.speed]}`}>
          {provider.speed === "fast" ? "⚡" : provider.speed === "medium" ? "⏱️" : "🐢"}
        </span>
        {/* Capabilities */}
        <div className="flex gap-1" title="Capabilities">
          {provider.capabilities.streaming && <span title="Streaming"><Zap className="w-3 h-3 text-green-500" /></span>}
          {provider.capabilities.vision && <span title="Vision"><Eye className="w-3 h-3 text-blue-500" /></span>}
          {provider.capabilities.functionCalling && <span title="Function Calling"><Workflow className="w-3 h-3 text-purple-500" /></span>}
        </div>
      </div>
    </button>
  );
}
