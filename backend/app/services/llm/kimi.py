"""
Kimi Provider (Moonshot AI)
"""

from typing import AsyncGenerator
import httpx

from app.core.config import get_settings
from .base import BaseLLMProvider

settings = get_settings()


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


__all__ = ["KimiProvider"]
