"""
Google (Gemini) Provider
"""

from typing import AsyncGenerator

from app.core.config import get_settings
from .base import BaseLLMProvider

settings = get_settings()


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


__all__ = ["GoogleProvider"]
