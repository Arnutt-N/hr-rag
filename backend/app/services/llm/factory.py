"""
LLM Provider Factory
Provider registry and factory for creating provider instances
"""

from typing import Dict, Optional, List, Type
from enum import Enum

from app.models.schemas import LLMProvider
from .base import BaseLLMProvider, _cost_tracker
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .ollama import OllamaProvider
from .kimi import KimiProvider
from .glm import GLMProvider
from .minimax import MiniMaxProvider
from .qwen import QwenProvider
from .deepseek import DeepSeekProvider
from .custom import CustomProvider


class ProviderFactory:
    """Factory for creating and managing LLM provider instances"""
    
    # Provider class registry
    PROVIDER_CLASSES: Dict[LLMProvider, Type[BaseLLMProvider]] = {
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.ANTHROPIC: AnthropicProvider,
        LLMProvider.GOOGLE: GoogleProvider,
        LLMProvider.OLLAMA: OllamaProvider,
        LLMProvider.KIMI: KimiProvider,
        LLMProvider.GLM: GLMProvider,
        LLMProvider.MINIMAX: MiniMaxProvider,
        LLMProvider.QWEN: QwenProvider,
        LLMProvider.DEEPSEEK: DeepSeekProvider,
        LLMProvider.CUSTOM: CustomProvider,
    }
    
    # Provider model mappings
    PROVIDER_MODELS = {
        LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        LLMProvider.GOOGLE: ["gemini-2.0-flash", "gemini-pro", "gemini-pro-vision"],
        LLMProvider.OLLAMA: ["llama3.2", "llama3.1", "mistral", "phi3", "qwen2.5"],
        LLMProvider.KIMI: ["kimi-coding", "kimi-k2p5", "kimi-chat"],
        LLMProvider.GLM: ["glm-5", "glm-4-flash", "glm-4-plus"],
        LLMProvider.MINIMAX: ["MiniMax-M2.5", "MiniMax-Text-01"],
        LLMProvider.QWEN: ["qwen-plus", "qwen-max", "qwen3.5-plus", "qwen-turbo"],
        LLMProvider.DEEPSEEK: ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        LLMProvider.CUSTOM: ["custom"],
    }
    
    DEFAULT_MODELS = {
        LLMProvider.OPENAI: "gpt-4o-mini",
        LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
        LLMProvider.GOOGLE: "gemini-2.0-flash",
        LLMProvider.OLLAMA: "llama3.2",
        LLMProvider.KIMI: "kimi-coding",
        LLMProvider.GLM: "glm-5",
        LLMProvider.MINIMAX: "MiniMax-M2.5",
        LLMProvider.QWEN: "qwen-plus",
        LLMProvider.DEEPSEEK: "deepseek-chat",
        LLMProvider.CUSTOM: "gpt-4o-mini",
    }
    
    # Fallback chain: if one provider fails, try next
    FALLBACK_CHAIN = {
        LLMProvider.OPENAI: [LLMProvider.ANTHROPIC, LLMProvider.GOOGLE, LLMProvider.OLLAMA],
        LLMProvider.KIMI: [LLMProvider.OPENAI, LLMProvider.GLM, LLMProvider.DEEPSEEK],
        LLMProvider.GLM: [LLMProvider.KIMI, LLMProvider.OPENAI, LLMProvider.MINIMAX],
        LLMProvider.MINIMAX: [LLMProvider.GLM, LLMProvider.QWEN, LLMProvider.OPENAI],
        LLMProvider.QWEN: [LLMProvider.DEEPSEEK, LLMProvider.MINIMAX, LLMProvider.OPENAI],
        LLMProvider.DEEPSEEK: [LLMProvider.OPENAI, LLMProvider.KIMI, LLMProvider.GLM],
        LLMProvider.CUSTOM: [LLMProvider.OPENAI, LLMProvider.GOOGLE, LLMProvider.OLLAMA],
    }
    
    _instances: Dict[LLMProvider, BaseLLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider: LLMProvider) -> BaseLLMProvider:
        """Get or create provider instance (singleton per provider type)"""
        if provider not in cls._instances:
            provider_class = cls.PROVIDER_CLASSES.get(provider)
            if not provider_class:
                raise ValueError(f"Unknown provider: {provider}")
            cls._instances[provider] = provider_class()
        return cls._instances[provider]
    
    @classmethod
    def get_default_model(cls, provider: LLMProvider) -> str:
        """Get default model for provider"""
        return cls.DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    
    @classmethod
    def get_available_models(cls, provider: LLMProvider) -> List[str]:
        """Get available models for a provider"""
        return cls.PROVIDER_MODELS.get(provider, [])
    
    @classmethod
    def get_fallback_providers(cls, provider: LLMProvider) -> List[LLMProvider]:
        """Get fallback providers if primary fails"""
        return cls.FALLBACK_CHAIN.get(provider, [])
    
    @classmethod
    def reset_instances(cls):
        """Reset all provider instances (useful for testing)"""
        cls._instances.clear()


__all__ = ["ProviderFactory"]
