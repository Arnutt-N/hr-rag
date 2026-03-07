"""
Ollama Provider (Local Models)
"""

import json
from typing import AsyncGenerator, Optional
import httpx

from app.core.config import get_settings
from .base import BaseLLMProvider

settings = get_settings()


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


__all__ = ["OllamaProvider"]
