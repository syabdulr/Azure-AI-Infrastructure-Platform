"""Unit tests for provider models."""

from datetime import datetime

import pytest

from src.providers.models import (
    GatewayRequest,
    GatewayResponse,
    HealthCheckResult,
    ModelCapability,
    ModelConfig,
    ProviderConfig,
    ProviderMetrics,
    ProviderStatus,
    RoutingDecision,
    RoutingStrategy,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_model_config_creation(self):
        """Test creating a model configuration."""
        config = ModelConfig(
            name="gpt-4",
            cost_per_1k_tokens=0.03,
            max_tokens=8192,
            capabilities={ModelCapability.CHAT, ModelCapability.REASONING},
        )

        assert config.name == "gpt-4"
        assert config.cost_per_1k_tokens == 0.03
        assert config.max_tokens == 8192
        assert ModelCapability.CHAT in config.capabilities
        assert config.supports_streaming is True
        assert config.context_window == 8192


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_provider_config_creation(self):
        """Test creating a provider configuration."""
        config = ProviderConfig(
            name="azure_openai", provider_type="azure_openai", api_key="test_key"
        )

        assert config.name == "azure_openai"
        assert config.provider_type == "azure_openai"
        assert config.api_key == "test_key"
        assert config.health_check_enabled is True
        assert config.rate_limit == 100
        assert config.timeout == 30


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_health_check_result_creation(self):
        """Test creating a health check result."""
        result = HealthCheckResult(
            provider_name="azure_openai",
            status=ProviderStatus.HEALTHY,
            timestamp=datetime.now(),
            latency_ms=150.5,
        )

        assert result.provider_name == "azure_openai"
        assert result.status == ProviderStatus.HEALTHY
        assert result.latency_ms == 150.5
        assert result.error is None


class TestProviderMetrics:
    """Tests for ProviderMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = ProviderMetrics(provider_name="azure_openai")

        assert metrics.provider_name == "azure_openai"
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_tokens == 0
        assert metrics.total_cost == 0.0


class TestGatewayRequest:
    """Tests for GatewayRequest model."""

    def test_minimal_request(self):
        """Test creating a minimal request."""
        request = GatewayRequest(prompt="Hello, world!")

        assert request.prompt == "Hello, world!"
        assert request.temperature == 0.7
        assert request.routing_strategy == RoutingStrategy.COST_OPTIMIZED

    def test_request_with_capabilities(self):
        """Test creating a request with required capabilities."""
        request = GatewayRequest(
            prompt="Write code",
            model_requirements={ModelCapability.CODE, ModelCapability.REASONING},
        )

        assert ModelCapability.CODE in request.model_requirements
        assert ModelCapability.REASONING in request.model_requirements

    def test_request_with_metadata(self):
        """Test creating a request with tenant and user ID."""
        request = GatewayRequest(
            prompt="Test", tenant_id="tenant_123", user_id="user_456", request_id="req_789"
        )

        assert request.tenant_id == "tenant_123"
        assert request.user_id == "user_456"
        assert request.request_id == "req_789"


class TestGatewayResponse:
    """Tests for GatewayResponse model."""

    def test_minimal_response(self):
        """Test creating a minimal response."""
        response = GatewayResponse(
            content="Hello!",
            model="gpt-4",
            provider="azure_openai",
            routing_strategy=RoutingStrategy.COST_OPTIMIZED,
            routing_reason="Cheapest option",
            tokens_used=10,
            latency_ms=100.0,
            cost=0.0003,
            request_id="req_123",
        )

        assert response.content == "Hello!"
        assert response.model == "gpt-4"
        assert response.provider == "azure_openai"
        assert response.tokens_used == 10
        assert response.cost == 0.0003
        assert response.cached is False


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass."""

    def test_routing_decision_creation(self):
        """Test creating a routing decision."""
        decision = RoutingDecision(
            provider_name="azure_openai",
            model_name="gpt-4",
            strategy=RoutingStrategy.COST_OPTIMIZED,
            reason="Cheapest provider",
            confidence=0.8,
            alternate_providers=["openai", "anthropic"],
        )

        assert decision.provider_name == "azure_openai"
        assert decision.model_name == "gpt-4"
        assert decision.strategy == RoutingStrategy.COST_OPTIMIZED
        assert decision.reason == "Cheapest provider"
        assert decision.confidence == 0.8
        assert len(decision.alternate_providers) == 2


class TestEnums:
    """Tests for enums."""

    def test_provider_status(self):
        """Test ProviderStatus enum values."""
        assert ProviderStatus.HEALTHY.value == "healthy"
        assert ProviderStatus.DEGRADED.value == "degraded"
        assert ProviderStatus.UNHEALTHY.value == "unhealthy"

    def test_routing_strategy(self):
        """Test RoutingStrategy enum values."""
        assert RoutingStrategy.ROUND_ROBIN.value == "round_robin"
        assert RoutingStrategy.COST_OPTIMIZED.value == "cost_optimized"
        assert RoutingStrategy.PERFORMANCE_BASED.value == "performance_based"

    def test_model_capability(self):
        """Test ModelCapability enum values."""
        assert ModelCapability.CHAT.value == "chat"
        assert ModelCapability.CODE.value == "code"
        assert ModelCapability.REASONING.value == "reasoning"
