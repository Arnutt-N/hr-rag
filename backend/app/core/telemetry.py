"""
OpenTelemetry Configuration - Distributed Tracing & Metrics

Provides observability for production deployments.
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

from app.core.logging import get_logger

logger = get_logger(__name__)

# Global tracer
tracer: Optional[trace.Tracer] = None


def setup_telemetry(app, service_name: str = "hr-rag-backend"):
    """
    Setup OpenTelemetry for the application.
    
    Environment variables:
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (e.g., http://localhost:4317)
        OTEL_SERVICE_NAME: Service name (default: hr-rag-backend)
        OTEL_ENABLED: Enable telemetry (default: true)
    """
    global tracer
    
    # Check if telemetry is enabled
    otel_enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    
    if not otel_enabled:
        logger.info("OpenTelemetry disabled via OTEL_ENABLED=false")
        return
    
    # Get configuration
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", service_name)
    
    try:
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Create tracer
        tracer = trace.get_tracer(service_name)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument HTTP client
        HTTPXClientInstrumentor().instrument()
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        # Instrument PostgreSQL (asyncpg)
        AsyncPGInstrumentor().instrument()
        
        logger.info(
            "OpenTelemetry initialized",
            service_name=service_name,
            endpoint=otlp_endpoint
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        # Don't fail startup if telemetry fails
        tracer = None


def get_tracer() -> Optional[trace.Tracer]:
    """Get the global tracer instance."""
    return tracer


def shutdown_telemetry():
    """Shutdown telemetry on application shutdown."""
    global tracer
    
    if tracer:
        try:
            provider = trace.get_tracer_provider()
            if hasattr(provider, "shutdown"):
                provider.shutdown()
            logger.info("OpenTelemetry shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down OpenTelemetry: {e}")
    
    tracer = None


class TracingContext:
    """Context manager for creating spans."""
    
    def __init__(self, name: str, attributes: dict = None):
        self.name = name
        self.attributes = attributes or {}
        self.span = None
    
    def __enter__(self):
        if tracer:
            self.span = tracer.start_span(self.name)
            for key, value in self.attributes.items():
                self.span.set_attribute(key, value)
            self.span.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.record_exception(exc_val)
                self.span.set_status(trace.Status(trace.StatusCode.ERROR))
            self.span.__exit__(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)


def trace_function(name: str = None, attributes: dict = None):
    """
    Decorator to trace a function.
    
    Usage:
        @trace_function("my_operation", {"key": "value"})
        async def my_function():
            ...
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with TracingContext(span_name, attributes):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with TracingContext(span_name, attributes):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
