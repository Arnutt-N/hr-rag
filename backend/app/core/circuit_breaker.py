"""
Circuit Breaker - Resilience Pattern for External Services

Prevents cascade failures when external services are unavailable.
"""

import time
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject all calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Service failing, reject all calls immediately
    - HALF_OPEN: Testing recovery, allow limited calls
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        @breaker.protect
        async def call_external_service():
            ...
    """
    
    name: str = "default"
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 3
    
    # State
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    half_open_calls: int = 0
    
    def protect(self, func: Callable) -> Callable:
        """Decorator to protect a function with circuit breaker."""
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await self.call(func, *args, **kwargs)
        
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self.recovery_timeout - (time.time() - self.last_failure_time):.1f}s"
                )
        
        # Limit calls in HALF_OPEN state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN with max calls reached"
                )
            self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self._transition_to(CircuitState.CLOSED)
        
        logger.debug(
            "circuit_breaker_success",
            name=self.name,
            state=self.state.value
        )
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
        
        logger.warning(
            "circuit_breaker_failure",
            name=self.name,
            state=self.state.value,
            failure_count=self.failure_count
        )
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        
        # Reset counters on transition
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self.half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0
            self.half_open_calls = 0
        
        logger.info(
            "circuit_breaker_transition",
            name=self.name,
            old_state=old_state.value,
            new_state=new_state.value
        )
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Pre-configured circuit breakers for common services
llm_breaker = CircuitBreaker(name="llm", failure_threshold=3, recovery_timeout=30.0)
vector_db_breaker = CircuitBreaker(name="vector_db", failure_threshold=5, recovery_timeout=60.0)
neo4j_breaker = CircuitBreaker(name="neo4j", failure_threshold=5, recovery_timeout=60.0)


def get_all_circuit_stats() -> list:
    """Get stats for all circuit breakers."""
    return [
        llm_breaker.get_stats(),
        vector_db_breaker.get_stats(),
        neo4j_breaker.get_stats()
    ]
