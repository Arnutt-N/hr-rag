"""
LLM Service
Main service class for LLM interactions with multiple provider support
"""

from typing import AsyncGenerator, Optional, Dict, Any, List

from app.core.config import get_settings
from app.models.schemas import LLMProvider

from .base import BaseLLMProvider, CostTracker, _cost_tracker
from .factory import ProviderFactory
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

settings = get_settings()


class LLMService:
    """LLM service with multiple provider support"""
    
    def __init__(self):
        self.default_provider = LLMProvider(settings.default_llm_provider)
        self.cost_tracker = _cost_tracker
    
    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get LLM provider instance"""
        provider = provider or self.default_provider
        return ProviderFactory.get_provider(provider)
    
    def get_default_model(self, provider: Optional[LLMProvider] = None) -> str:
        """Get default model for provider"""
        provider = provider or self.default_provider
        return ProviderFactory.get_default_model(provider)
    
    def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get available models for a provider"""
        return ProviderFactory.get_available_models(provider)
    
    def get_fallback_providers(self, provider: LLMProvider) -> List[LLMProvider]:
        """Get fallback providers if primary fails"""
        return ProviderFactory.get_fallback_providers(provider)
    
    async def generate_response(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True,
        use_fallback: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from LLM with optional fallback"""
        provider = provider or self.default_provider
        model = model or self.get_default_model(provider)
        
        # Try primary provider first
        try:
            llm_provider = self.get_provider(provider)
            async for chunk in llm_provider.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            ):
                yield chunk
        except Exception as e:
            if use_fallback:
                # Try fallback providers
                fallback_providers = self.get_fallback_providers(provider)
                for fallback_provider in fallback_providers:
                    try:
                        llm_provider = self.get_provider(fallback_provider)
                        fallback_model = self.get_default_model(fallback_provider)
                        async for chunk in llm_provider.generate(
                            prompt=prompt,
                            model=fallback_model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=stream
                        ):
                            yield chunk
                        break  # Fallback succeeded
                    except Exception:
                        continue  # Try next fallback
            else:
                raise e
    
    def get_cost_usage(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """Get cost usage statistics"""
        if provider:
            return self.cost_tracker.get_usage(provider.value)
        return self.cost_tracker.get_all_usage()
    
    def build_rag_prompt(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Build RAG prompt with context"""
        # Format context documents
        context_text = "\n\n".join([
            f"--- Document {i+1}: {doc.get('filename', 'Unknown')} ---\n{doc.get('text', '')}"
            for i, doc in enumerate(context_docs)
        ])
        
        # Default system prompt for HR assistant
        if not system_prompt:
            system_prompt = """You are a helpful HR assistant. 
Answer the user's question based ONLY on the provided context documents.
If the answer cannot be found in the context, say so honestly.
Be concise and professional."""
        
        # Build full prompt
        prompt = f"""System: {system_prompt}

Context Documents:
{context_text}

User Question: {query}

Answer:"""
        
        return prompt


# Global singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def close_llm_clients():
    """Close all LLM client connections gracefully"""
    global _llm_service
    
    # Close OpenAI-compatible clients
    providers_with_clients = [
        OpenAIProvider,
        AnthropicProvider,
        KimiProvider,
        GLMProvider,
        MiniMaxProvider,
        QwenProvider,
        DeepSeekProvider,
        CustomProvider,
    ]
    
    for provider_class in providers_with_clients:
        if provider_class._client is not None:
            try:
                await provider_class._client.close()
            except Exception:
                pass
            provider_class._client = None
    
    # Close Ollama httpx client
    if OllamaProvider._client is not None:
        try:
            await OllamaProvider._client.aclose()
        except Exception:
            pass
        OllamaProvider._client = None
    
    # Reset Google configuration
    GoogleProvider._configured = False
    
    # Clear LLM service
    _llm_service = None


__all__ = [
    "LLMService",
    "get_llm_service",
    "close_llm_clients",
]
