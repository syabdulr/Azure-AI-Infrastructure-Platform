"""
Multi-Provider AI Gateway

This module provides a production-grade AI gateway for routing requests
across multiple LLM providers with intelligent failover, cost optimization,
and performance monitoring.
"""

from .base import Provider, ProviderStatus, HealthCheckResult, ProviderError
from .registry import ProviderRegistry
from .models import (
    ProviderConfig,
    ModelConfig,
    RoutingStrategy,
    RoutingDecision,
    GatewayRequest,
    GatewayResponse,
    ModelCapability
)
from .azure_openai import AzureOpenAIProvider, create_azure_openai_provider
from .openai import OpenAIProvider, create_openai_provider

__all__ = [
    "Provider",
    "ProviderStatus",
    "HealthCheckResult",
    "ProviderError",
    "ProviderRegistry",
    "ProviderConfig",
    "ModelConfig",
    "RoutingStrategy",
    "RoutingDecision",
    "GatewayRequest",
    "GatewayResponse",
    "ModelCapability",
    "AzureOpenAIProvider",
    "create_azure_openai_provider",
    "OpenAIProvider",
    "create_openai_provider"
]