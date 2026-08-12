"""
Multi-Provider AI Gateway

This module provides a production-grade AI gateway for routing requests
across multiple LLM providers with intelligent failover, cost optimization,
and performance monitoring.
"""

from .azure_openai import AzureOpenAIProvider, create_azure_openai_provider
from .base import HealthCheckResult, Provider, ProviderError, ProviderStatus
from .models import (
    GatewayRequest,
    GatewayResponse,
    ModelCapability,
    ModelConfig,
    ProviderConfig,
    RoutingDecision,
    RoutingStrategy,
)
from .openai import OpenAIProvider, create_openai_provider
from .registry import ProviderRegistry

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
    "create_openai_provider",
]
