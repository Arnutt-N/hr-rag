"""LLM router

Expose available providers/models and allow per-user preference changes in future.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_active_member
from app.models.schemas import LLMProvider
from app.services.llm_providers import get_llm_service, _cost_tracker

router = APIRouter(prefix="/llm", tags=["llm"])


class CustomProviderConfig(BaseModel):
    """Configuration for custom provider"""
    api_key: str
    base_url: str
    model: str = "gpt-4o-mini"


class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    requests_per_minute: int = 60


@router.get("/providers")
async def list_providers(current_user=Depends(get_current_active_member)):
    """List all available LLM providers"""
    return {
        "providers": [p.value for p in LLMProvider],
        "default": "openai"
    }


@router.get("/models/{provider}")
async def list_models(provider: LLMProvider, current_user=Depends(get_current_active_member)):
    """List available models for a provider"""
    llm = get_llm_service()
    return {
        "provider": provider.value,
        "models": llm.get_available_models(provider),
        "default_model": llm.get_default_model(provider)
    }


@router.get("/fallback/{provider}")
async def get_fallback_providers(
    provider: LLMProvider,
    current_user=Depends(get_current_active_member)
):
    """Get fallback chain for a provider"""
    llm = get_llm_service()
    fallback = llm.get_fallback_providers(provider)
    return {
        "provider": provider.value,
        "fallback_providers": [p.value for p in fallback]
    }


@router.get("/cost-usage")
async def get_cost_usage(
    provider: Optional[LLMProvider] = None,
    current_user=Depends(get_current_active_member)
):
    """Get cost usage statistics"""
    llm = get_llm_service()
    usage = llm.get_cost_usage(provider)
    return {
        "usage": usage
    }


@router.post("/custom/config")
async def configure_custom_provider(
    config: CustomProviderConfig,
    current_user=Depends(get_current_active_member)
):
    """Configure custom OpenAI-compatible provider"""
    from app.services.llm_providers import CustomProvider
    
    # Create new custom provider with user config
    custom_provider = CustomProvider(
        api_key=config.api_key,
        base_url=config.base_url,
        default_model=config.model
    )
    
    # Update the global service
    llm = get_llm_service()
    llm._providers[LLMProvider.CUSTOM] = custom_provider
    
    return {
        "status": "success",
        "message": "Custom provider configured",
        "model": config.model,
        "base_url": config.base_url
    }


@router.post("/rate-limit")
async def configure_rate_limit(
    config: RateLimitConfig,
    current_user=Depends(get_current_active_member)
):
    """Configure rate limiting"""
    from app.services.llm_providers import _rate_limiter
    
    _rate_limiter.requests_per_minute = config.requests_per_minute
    
    return {
        "status": "success",
        "requests_per_minute": config.requests_per_minute
    }


@router.get("/health/{provider}")
async def health_check_provider(
    provider: LLMProvider,
    current_user=Depends(get_current_active_member)
):
    """Check if a provider is configured and working"""
    llm = get_llm_service()
    p = llm.get_provider(provider)
    
    # Check if API key is configured
    has_api_key = bool(p.api_key)
    
    return {
        "provider": provider.value,
        "configured": has_api_key,
        "available_models": llm.get_available_models(provider),
        "default_model": llm.get_default_model(provider)
    }
