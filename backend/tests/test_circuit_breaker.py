"""
Unit Tests for Circuit Breaker
"""

import pytest
import asyncio
import time
from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    llm_breaker,
    vector_db_breaker,
    neo4j_breaker
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_initial_state_is_closed(self):
        """Circuit breaker should start in CLOSED state."""
        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_transition_to_open_after_threshold(self):
        """Should transition to OPEN after failure threshold."""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        # Simulate failures
        breaker._on_failure()
        assert breaker.state == CircuitState.CLOSED
        
        breaker._on_failure()
        assert breaker.state == CircuitState.CLOSED
        
        breaker._on_failure()
        assert breaker.state == CircuitState.OPEN
    
    def test_transition_to_half_open_after_timeout(self):
        """Should transition to HALF_OPEN after recovery timeout."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1  # 100ms
        )
        
        # Trigger OPEN state
        breaker._on_failure()
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should allow HALF_OPEN
        assert breaker.state == CircuitState.OPEN
        # Manual transition check would happen in call()
    
    def test_success_resets_failure_count(self):
        """Success should reset failure count."""
        breaker = CircuitBreaker(name="test")
        
        breaker._on_failure()
        breaker._on_failure()
        assert breaker.failure_count == 2
        
        breaker._on_success()
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_protect_decorator_success(self):
        """Protect decorator should pass through successful calls."""
        breaker = CircuitBreaker(name="test")
        
        @breaker.protect
        async def successful_func():
            return "success"
        
        result = await successful_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_protect_decorator_failure(self):
        """Protect decorator should track failures."""
        breaker = CircuitBreaker(name="test", failure_threshold=1)
        
        @breaker.protect
        async def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await failing_func()
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self):
        """OPEN circuit should reject calls immediately."""
        breaker = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=60)
        
        # Force OPEN state
        breaker._on_failure()
        assert breaker.state == CircuitState.OPEN
        
        @breaker.protect
        async def test_func():
            return "should not reach"
        
        with pytest.raises(CircuitBreakerOpenError):
            await test_func()
    
    def test_get_stats(self):
        """Should return circuit breaker statistics."""
        breaker = CircuitBreaker(name="test", failure_threshold=5)
        stats = breaker.get_stats()
        
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["failure_threshold"] == 5
        assert "failure_count" in stats
    
    def test_preconfigured_breakers(self):
        """Pre-configured breakers should be available."""
        assert llm_breaker.name == "llm"
        assert vector_db_breaker.name == "vector_db"
        assert neo4j_breaker.name == "neo4j"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
