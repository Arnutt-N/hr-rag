"""
LLM Providers - Base Classes
RateLimiter, CostTracker, and BaseLLMProvider abstract class
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from app.core.config import get_settings

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
    ):
        """Generate response from LLM"""
        pass
    
    async def _with_rate_limit(self, provider_name: str):
        """Apply rate limiting before making request"""
        await self.rate_limiter.acquire(provider_name)
    
    def _record_cost(self, provider_name: str, model: str, tokens: int):
        """Record cost for the request"""
        self.cost_tracker.record_usage(provider_name, model, tokens)


__all__ = [
    "RateLimiter",
    "CostTracker",
    "BaseLLMProvider",
    "_rate_limiter",
    "_cost_tracker",
]
