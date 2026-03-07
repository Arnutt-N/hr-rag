"""
Anthropic (Claude) Provider
"""

from typing import AsyncGenerator
import httpx

from app.core.config import get_settings
from .base import BaseLLMProvider

settings = get_settings()


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


__all__ = ["AnthropicProvider"]
