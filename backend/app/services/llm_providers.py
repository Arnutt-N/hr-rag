"""
HR-RAG Backend - LLM Providers Service
Multiple LLM provider support: OpenAI, Claude, Gemini, Ollama, Kimi, GLM, MiniMax, Qwen, DeepSeek, Custom
"""

import json
import asyncio
import time
from typing import AsyncGenerator, Optional, Dict, Any, List
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.core.config import get_settings
from app.models.schemas import LLMProvider

settings = get_settings()


# ==================== RATE LIMITING & COST TRACKING ====================

@dataclass
class RateLimiter:
    """Simple rate limiter for API requests"""
    requests_per_minute: int = 60
    _requests: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    async def acquire(self, provider: str):
        """Acquire permission to make a request"""
        now = time.time()
        # Clean old requests (older than 1 minute)
        self._requests[provider] = [t for t in self._requests[provider] if now - t < 60]
        
        if len(self._requests[provider]) >= self.requests_per_minute:
            # Wait until oldest request expires
            wait_time = 60 - (now - self._requests[provider][0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                return await self.acquire(provider)
        
        self._requests[provider].append(now)


@dataclass
class CostTracker:
    """Track usage costs per provider"""
    _usage: Dict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(lambda: {
        "total_requests": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "last_updated": None
    }))
    
    # Cost per 1M tokens (approximate, in USD)
    COST_PER_MILLION = {
        "gpt-4o-mini": 0.15,
        "gpt-4o": 2.50,
        "gpt-4-turbo": 10.00,
        "claude-3-5-sonnet": 3.00,
        "claude-3-opus": 15.00,
        "gemini-2.0-flash": 0.0,
        "kimi-coding": 0.12,
        "kimi-chat": 0.12,
        "glm-5": 0.10,
        "minimax": 0.20,
        "qwen3.5-plus": 0.20,
        "qwen-max": 0.60,
        "deepseek-chat": 0.14,
        "deepseek-coder": 0.14,
        "ring2.5-t": 0.14,
    }
    
    def record_usage(self, provider: str, model: str, tokens: int):
        """Record usage for cost tracking"""
        cost_per_token = self.COST_PER_MILLION.get(model, 0.0) / 1_000_000
        cost = tokens * cost_per_token
        
        self._usage[provider]["total_requests"] += 1
        self._usage[provider]["total_tokens"] += tokens
        self._usage[provider]["total_cost"] += cost
        self._usage[provider]["last_updated"] = datetime.now()
    
    def get_usage(self, provider: str) -> Dict[str, Any]:
        """Get usage statistics for a provider"""
        return dict(self._usage.get(provider, {}))
    
    def get_all_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get all usage statistics"""
        return {k: dict(v) for k, v in self._usage.items()}


# Global instances
_rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_provider)
_cost_tracker = CostTracker()


# ==================== BASE PROVIDER ====================

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = _rate_limiter
        self.cost_tracker = _cost_tracker
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from LLM"""
        pass
    
    async def _with_rate_limit(self, provider_name: str):
        """Apply rate limiting before making request"""
        await self.rate_limiter.acquire(provider_name)
    
    def _record_cost(self, provider_name: str, model: str, tokens: int):
        """Record cost for the request"""
        self.cost_tracker.record_usage(provider_name, model, tokens)


# ==================== OPENAI PROVIDER ====================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.openai_api_key,
            base_url="https://api.openai.com/v1"
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton OpenAI client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url="https://api.openai.com/v1",
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                ) if hasattr(settings, 'llm_max_connections') else None
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        await self._with_rate_limit("openai")
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== ANTHROPIC PROVIDER ====================

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(api_key=settings.anthropic_api_key)
    
    @classmethod
    def get_client(cls):
        """Get singleton Anthropic client with connection pooling"""
        if cls._client is None:
            from anthropic import AsyncAnthropic
            cls._client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                timeout=httpx.Timeout(settings.llm_timeout),
                max_retries=settings.llm_max_retries
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        await self._with_rate_limit("anthropic")
        
        client = self.get_client()
        
        if stream:
            async with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        else:
            message = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            yield message.content[0].text


# ==================== GOOGLE PROVIDER ====================

class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider"""
    
    # Singleton client - class-level (genai client is stateless, but configure once)
    _configured = False
    
    def __init__(self):
        super().__init__(api_key=settings.google_api_key)
    
    @classmethod
    def configure(cls):
        """Configure Google genai client once"""
        if not cls._configured:
            import google.generativeai as genai
            genai.configure(
                api_key=settings.google_api_key,
                timeout=settings.llm_timeout
            )
            cls._configured = True
    
    async def generate(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        await self._with_rate_limit("google")
        
        # Configure once
        self.configure()
        
        import google.generativeai as genai
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )
        
        if stream:
            response = await model_instance.generate_content_async(
                prompt,
                stream=True
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            response = await model_instance.generate_content_async(prompt)
            yield response.text


# ==================== OLLAMA PROVIDER ====================

class OllamaProvider(BaseLLMProvider):
    """Ollama local model provider"""
    
    # Singleton httpx client with connection pooling
    _client = None
    
    def __init__(self):
        super().__init__(
            base_url=settings.ollama_base_url
        )
        self.default_model = settings.ollama_model
    
    @classmethod
    def get_client(cls):
        """Get singleton httpx client with connection pooling"""
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=httpx.Timeout(settings.llm_timeout),
                limits=httpx.Limits(
                    max_keepalive_connections=settings.llm_keepalive_connections,
                    max_connections=settings.llm_max_connections
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        
        await self._with_rate_limit("ollama")
        
        client = self.get_client()
        
        if stream:
            async with client.stream(
                "POST",
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
        else:
            response = await client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            data = response.json()
            yield data.get("response", "")


# ==================== KIMI PROVIDER (Moonshot AI) ====================

class KimiProvider(BaseLLMProvider):
    """Kimi (Moonshot AI) provider - OpenAI compatible"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.kimi_api_key,
            base_url=settings.kimi_base_url
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton Kimi client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.kimi_api_key,
                base_url=settings.kimi_base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "kimi-coding",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Kimi API key not configured")
        
        await self._with_rate_limit("kimi")
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== GLM PROVIDER (Zhipu AI) ====================

class GLMProvider(BaseLLMProvider):
    """GLM (Zhipu AI) provider - OpenAI compatible"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.glm_api_key,
            base_url=settings.glm_base_url
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton GLM client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.glm_api_key,
                base_url=settings.glm_base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "glm-5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("GLM API key not configured")
        
        await self._with_rate_limit("glm")
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== MINIMAX PROVIDER ====================

class MiniMaxProvider(BaseLLMProvider):
    """MiniMax provider - OpenAI compatible"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_base_url
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton MiniMax client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.minimax_api_key,
                base_url=settings.minimax_base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "MiniMax-M2.5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("MiniMax API key not configured")
        
        await self._with_rate_limit("minimax")
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== QWEN PROVIDER (Alibaba) ====================

class QwenProvider(BaseLLMProvider):
    """Qwen (Alibaba) provider - OpenAI compatible"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.qwen_api_key,
            base_url=settings.qwen_base_url
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton Qwen client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.qwen_api_key,
                base_url=settings.qwen_base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Qwen API key not configured")
        
        await self._with_rate_limit("qwen")
        
        client = self.get_client()
        
        # Map model names to DashScope format
        model_map = {
            "qwen-plus": "qwen-plus",
            "qwen-max": "qwen-max",
            "qwen3.5-plus": "qwen3.5-plus",
            "qwen-turbo": "qwen-turbo"
        }
        model = model_map.get(model, model)
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== DEEPSEEK PROVIDER ====================

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek provider - OpenAI compatible"""
    
    # Singleton client - class-level
    _client = None
    
    def __init__(self):
        super().__init__(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url
        )
    
    @classmethod
    def get_client(cls):
        """Get singleton DeepSeek client with connection pooling"""
        if cls._client is None:
            from openai import AsyncOpenAI
            cls._client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
        return cls._client
    
    async def generate(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
        
        await self._with_rate_limit("deepseek")
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== CUSTOM PROVIDER ====================

class CustomProvider(BaseLLMProvider):
    """Custom OpenAI-compatible provider"""
    
    # Instance-level client (since api_key/base_url can be custom per instance)
    _client = None
    _client_key = None
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        super().__init__(
            api_key=api_key or settings.custom_api_key,
            base_url=base_url or settings.custom_base_url
        )
        self.default_model = default_model or settings.custom_model
    
    def get_client(self):
        """Get singleton client with connection pooling (instance-level)"""
        # Create a unique key for this configuration
        client_key = f"{self.api_key}:{self.base_url}"
        
        # Only create new client if config changed or no client exists
        if CustomProvider._client is None or CustomProvider._client_key != client_key:
            from openai import AsyncOpenAI
            CustomProvider._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=settings.llm_timeout,
                max_retries=settings.llm_max_retries,
                http_client=httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=settings.llm_keepalive_connections,
                        max_connections=settings.llm_max_connections
                    )
                )
            )
            CustomProvider._client_key = client_key
        
        return CustomProvider._client
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise ValueError("Custom provider API key not configured")
        
        await self._with_rate_limit("custom")
        
        model = model or self.default_model
        
        client = self.get_client()
        
        if stream:
            stream_response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            yield response.choices[0].message.content


# ==================== LLM SERVICE ====================

class LLMService:
    """LLM service with multiple provider support"""
    
    PROVIDER_MODELS = {
        LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        LLMProvider.GOOGLE: ["gemini-2.0-flash", "gemini-pro", "gemini-pro-vision"],
        LLMProvider.OLLAMA: ["llama3.2", "llama3.1", "mistral", "phi3", "qwen2.5"],
        # New providers
        LLMProvider.KIMI: ["kimi-coding", "kimi-k2p5", "kimi-chat"],
        LLMProvider.GLM: ["glm-5", "glm-4-flash", "glm-4-plus"],
        LLMProvider.MINIMAX: ["MiniMax-M2.5", "MiniMax-Text-01"],
        LLMProvider.QWEN: ["qwen-plus", "qwen-max", "qwen3.5-plus", "qwen-turbo"],
        LLMProvider.DEEPSEEK: ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        LLMProvider.CUSTOM: ["custom"],  # User-defined
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
    
    def __init__(self):
        self._providers = {
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.ANTHROPIC: AnthropicProvider(),
            LLMProvider.GOOGLE: GoogleProvider(),
            LLMProvider.OLLAMA: OllamaProvider(),
            LLMProvider.KIMI: KimiProvider(),
            LLMProvider.GLM: GLMProvider(),
            LLMProvider.MINIMAX: MiniMaxProvider(),
            LLMProvider.QWEN: QwenProvider(),
            LLMProvider.DEEPSEEK: DeepSeekProvider(),
            LLMProvider.CUSTOM: CustomProvider(),
        }
        self.default_provider = LLMProvider(settings.default_llm_provider)
        self.cost_tracker = _cost_tracker
    
    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get LLM provider instance"""
        provider = provider or self.default_provider
        return self._providers[provider]
    
    def get_default_model(self, provider: Optional[LLMProvider] = None) -> str:
        """Get default model for provider"""
        provider = provider or self.default_provider
        return self.DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    
    def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get available models for a provider"""
        return self.PROVIDER_MODELS.get(provider, [])
    
    def get_fallback_providers(self, provider: LLMProvider) -> List[LLMProvider]:
        """Get fallback providers if primary fails"""
        return self.FALLBACK_CHAIN.get(provider, [])
    
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
