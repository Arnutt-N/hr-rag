"""
LangChain LLM Service - Unified interface for multiple LLM providers
"""

import os
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


class LangChainLLMService:
    """
    Unified LLM service using LangChain.
    Supports multiple providers: OpenAI, Anthropic, Kimi, Google, etc.
    """
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        """
        Initialize LLM service with specified provider.
        
        Args:
            provider: LLM provider name (openai, anthropic, kimi, google)
            model: Specific model name (optional, uses default for provider)
        """
        self.provider = provider
        self.llm = self._get_llm(provider, model)
    
    def _get_llm(self, provider: str, model: Optional[str] = None) -> BaseChatModel:
        """
        Get LangChain LLM instance for provider.
        
        Args:
            provider: Provider name
            model: Model name (optional)
        
        Returns:
            LangChain chat model instance
        """
        providers = {
            "openai": self._get_openai,
            "anthropic": self._get_anthropic,
            "kimi": self._get_kimi,
            "google": self._get_google,
        }
        
        factory = providers.get(provider)
        if not factory:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return factory(model)
    
    def _get_openai(self, model: Optional[str] = None) -> ChatOpenAI:
        """Get OpenAI chat model."""
        return ChatOpenAI(
            model=model or "gpt-4o",
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
    
    def _get_anthropic(self, model: Optional[str] = None) -> ChatAnthropic:
        """Get Anthropic chat model."""
        return ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=0.7,
            api_key=settings.anthropic_api_key,
        )
    
    def _get_kimi(self, model: Optional[str] = None) -> ChatOpenAI:
        """Get Kimi (Moonshot) chat model via OpenAI-compatible API."""
        return ChatOpenAI(
            model=model or "kimi-k2.5",
            temperature=0.7,
            api_key=getattr(settings, "kimi_api_key", None) or os.environ.get("KIMI_API_KEY"),
            base_url="https://api.moonshot.cn/v1",
        )
    
    def _get_google(self, model: Optional[str] = None) -> ChatOpenAI:
        """Get Google Gemini via OpenAI-compatible API."""
        return ChatOpenAI(
            model=model or "gemini-2.0-flash",
            temperature=0.7,
            api_key=getattr(settings, "google_api_key", None) or os.environ.get("GOOGLE_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    
    def convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """
        Convert message dicts to LangChain message objects.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            List of LangChain message objects
        """
        lc_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
        
        return lc_messages
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send chat messages and get response.
        
        Args:
            messages: List of message dicts
            temperature: Override temperature
            max_tokens: Max tokens in response
            **kwargs: Additional provider-specific options
        
        Returns:
            Assistant response text
        """
        # Convert to LangChain messages
        lc_messages = self.convert_messages(messages)
        
        # Build invoke kwargs
        invoke_kwargs = {}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature
        if max_tokens is not None:
            invoke_kwargs["max_tokens"] = max_tokens
        
        # Invoke LLM
        response = await self.llm.ainvoke(lc_messages, **invoke_kwargs)
        
        return response.content
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat with tool calling support.
        
        Args:
            messages: List of message dicts
            tools: List of tool definitions
            **kwargs: Additional options
        
        Returns:
            Response with potential tool calls
        """
        from langchain_core.utils.function_calling import convert_to_openai_tool
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        # Convert messages
        lc_messages = self.convert_messages(messages)
        
        # Invoke
        response = await llm_with_tools.ainvoke(lc_messages, **kwargs)
        
        return {
            "content": response.content,
            "tool_calls": response.tool_calls if hasattr(response, "tool_calls") else [],
            "response": response
        }


# Singleton instance
_llm_service: Optional[LangChainLLMService] = None


def get_llm_service(provider: str = "openai") -> LangChainLLMService:
    """
    Get or create LLM service singleton.
    
    Args:
        provider: LLM provider name
    
    Returns:
        LangChainLLMService instance
    """
    global _llm_service
    
    if _llm_service is None or _llm_service.provider != provider:
        _llm_service = LangChainLLMService(provider=provider)
    
    return _llm_service
