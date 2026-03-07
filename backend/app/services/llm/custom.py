"""
Custom Provider (OpenAI-compatible custom endpoints)
"""

from typing import AsyncGenerator, Optional

from app.core.config import get_settings
from .base import BaseLLMProvider

settings = get_settings()


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
            import httpx
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


__all__ = ["CustomProvider"]
