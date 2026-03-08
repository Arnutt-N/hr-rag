export type CostLevel = "free" | "$" | "$$" | "$$$";
export type SpeedLevel = "fast" | "medium" | "slow";
export type ProviderRegion = "china" | "international";

export interface ProviderCapability {
  streaming: boolean;
  vision: boolean;
  functionCalling: boolean;
}

export interface LLMProvider {
  id: string;
  name: string;
  description: string;
  models: string[];
  region: ProviderRegion;
  cost: CostLevel;
  speed: SpeedLevel;
  capabilities: ProviderCapability;
  website?: string;
  logoUrl?: string;
  customConfig?: {
    baseUrl?: string;
    modelName?: string;
  };
}

export const LLM_PROVIDERS: LLMProvider[] = [
  // International Providers
  {
    id: "openai",
    name: "OpenAI",
    description: "GPT-4, GPT-4o",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    region: "international",
    cost: "$$$",
    speed: "medium",
    capabilities: { streaming: true, vision: true, functionCalling: true },
    website: "https://openai.com",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    description: "Claude 3.5 Sonnet",
    models: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    region: "international",
    cost: "$$$",
    speed: "medium",
    capabilities: { streaming: true, vision: true, functionCalling: true },
    website: "https://anthropic.com",
  },
  {
    id: "google",
    name: "Google",
    description: "Gemini 2.0 Flash",
    models: ["gemini-2.0-flash", "gemini-pro", "gemini-pro-vision"],
    region: "international",
    cost: "$$",
    speed: "fast",
    capabilities: { streaming: true, vision: true, functionCalling: true },
    website: "https://gemini.google.com",
  },
  // China Providers
  {
    id: "kimi",
    name: "Kimi",
    description: "Moonshot AI - รองรับบริบทยาว",
    models: ["kimi-coding", "kimi-k2p5", "kimi-chat"],
    region: "china",
    cost: "$",
    speed: "medium",
    capabilities: { streaming: true, vision: true, functionCalling: false },
    website: "https://kimi.moonshot.cn",
  },
  {
    id: "glm",
    name: "GLM",
    description: "Zhipu AI - ChatGLM",
    models: ["glm-4-flash", "glm-4-plus", "glm-4", "glm-4-vision"],
    region: "china",
    cost: "$",
    speed: "fast",
    capabilities: { streaming: true, vision: true, functionCalling: true },
    website: "https://zhipuai.cn",
  },
  {
    id: "minimax",
    name: "MiniMax",
    description: "MiniMax AI - Abab",
    models: ["abab6.5s-chat", "abab6.5g-chat", "abab6-chat"],
    region: "china",
    cost: "$",
    speed: "medium",
    capabilities: { streaming: true, vision: false, functionCalling: false },
    website: "https://minimax.cn",
  },
  {
    id: "qwen",
    name: "Qwen",
    description: "Alibaba - Tongyi Qianwen",
    models: ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-vl-max"],
    region: "china",
    cost: "$",
    speed: "fast",
    capabilities: { streaming: true, vision: true, functionCalling: true },
    website: "https://tongyi.aliyun.com",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    description: "DeepSeek V3, Coder",
    models: ["deepseek-chat", "deepseek-coder", "deepseek-math"],
    region: "china",
    cost: "$",
    speed: "fast",
    capabilities: { streaming: true, vision: false, functionCalling: true },
    website: "https://deepseek.com",
  },
  // Custom Provider
  {
    id: "custom",
    name: "Custom",
    description: "OpenAI-compatible API",
    models: [],
    region: "international",
    cost: "$$",
    speed: "medium",
    capabilities: { streaming: true, vision: false, functionCalling: false },
    customConfig: {
      baseUrl: "",
      modelName: "",
    },
  },
];
