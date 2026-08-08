"""Integration tests for multi-provider routing."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.providers import (
    ProviderRegistry,
    create_azure_openai_provider,
    create_openai_provider,
    GatewayRequest,
    GatewayResponse,
    RoutingStrategy,
    ProviderStatus,
    ModelCapability,
    ProviderError
)


class TestProviderRegistration:
    """Tests for provider registration and management."""

    @pytest.mark.asyncio
    async def test_register_provider(self):
        """Test registering a provider."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com'
        }):
            provider = create_azure_openai_provider(name="test_azure")

        await registry.register(provider)

        assert registry.get_provider("test_azure") is not None
        assert len(registry.get_all_providers()) == 1

    @pytest.mark.asyncio
    async def test_register_duplicate_fails(self):
        """Test that registering duplicate provider fails."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_azure_openai_provider(name="test_azure")

        await registry.register(provider1)

        with pytest.raises(ValueError) as exc_info:
            await registry.register(provider2)

        assert "already registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unregister_provider(self):
        """Test unregistering a provider."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com'
        }):
            provider = create_azure_openai_provider(name="test_azure")

        await registry.register(provider)
        await registry.unregister("test_azure")

        assert registry.get_provider("test_azure") is None
        assert len(registry.get_all_providers()) == 0

    @pytest.mark.asyncio
    async def test_get_healthy_providers(self):
        """Test filtering healthy providers."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.DEGRADED

        # Mock health check before registration to prevent API calls
        async def mock_health_check_healthy():
            from src.providers.models import HealthCheckResult
            return HealthCheckResult(
                provider_name="test_azure",
                status=ProviderStatus.HEALTHY,
                timestamp=datetime.now(),
                latency_ms=100.0,
                success_rate=0.99
            )

        async def mock_health_check_degraded():
            from src.providers.models import HealthCheckResult
            return HealthCheckResult(
                provider_name="test_openai",
                status=ProviderStatus.DEGRADED,
                timestamp=datetime.now(),
                latency_ms=3000.0,
                success_rate=0.85
            )

        provider1.health_check = mock_health_check_healthy
        provider2.health_check = mock_health_check_degraded

        await registry.register(provider1)
        await registry.register(provider2)

        healthy = registry.get_healthy_providers()

        assert len(healthy) == 1
        assert healthy[0].config.name == "test_azure"


class TestRoundRobinRouting:
    """Tests for round-robin routing strategy."""

    @pytest.mark.asyncio
    async def test_round_robin_balances_load(self):
        """Test that round-robin distributes requests evenly."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        # Mock providers as healthy
        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.HEALTHY
        
        # Ensure they're marked as healthy in registry
        provider1._last_health_check = datetime.now()
        provider2._last_health_check = datetime.now()
        
        # Mock health checks to prevent API calls
        async def mock_health_check():
            from src.providers.models import HealthCheckResult
            return HealthCheckResult(
                provider_name="test_azure",
                status=ProviderStatus.HEALTHY,
                timestamp=datetime.now(),
                latency_ms=100.0,
                success_rate=0.99
            )

        provider1.health_check = mock_health_check
        provider2.health_check = mock_health_check

        await registry.register(provider1)
        await registry.register(provider2)

        # Track which provider gets each request
        providers_used = []

        async def mock_generate(request, model=None):
            providers_used.append(provider1.config.name if provider1.is_available() else provider2.config.name)
            mock_response = Mock(spec=GatewayResponse)
            mock_response.content = f"Response from {providers_used[-1]}"
            mock_response.model = "gpt-4"
            mock_response.provider = providers_used[-1]
            mock_response.routing_strategy = request.routing_strategy
            mock_response.routing_reason = "Test"
            mock_response.tokens_used = 10
            mock_response.latency_ms = 100.0
            mock_response.cost = 0.0003
            mock_response.request_id = "test_123"
            mock_response.metadata = {}
            mock_response.cached = False
            mock_response.quality_score = 0.9
            return mock_response

        provider1.generate = mock_generate
        provider2.generate = mock_generate

        # Make 4 requests
        for i in range(4):
            request = GatewayRequest(
                prompt=f"Test {i}",
                request_id=f"test_{i}",
                max_tokens=1000,
                temperature=0.7,
                allow_degraded_providers=False,
                routing_strategy=RoutingStrategy.ROUND_ROBIN
            )
            response = await registry.route_request(request)
            assert response.content == f"Response from {providers_used[i]}"

        # Should alternate between providers
        assert providers_used[0] == "test_azure"
        assert providers_used[1] == "test_openai"
        assert providers_used[2] == "test_azure"
        assert providers_used[3] == "test_openai"


class TestHealthBasedRouting:
    """Tests for health-based routing strategy."""

    @pytest.mark.asyncio
    async def test_health_based_chooses_healthy_only(self):
        """Test that health-based routing only uses healthy providers."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        # Make one healthy, one degraded
        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.DEGRADED

        # Mock health check results
        from src.providers.models import HealthCheckResult
        registry._health_check_results = {
            "test_azure": HealthCheckResult(
                provider_name="test_azure",
                status=ProviderStatus.HEALTHY,
                timestamp=datetime.now(),
                latency_ms=100.0,
                success_rate=0.99
            ),
            "test_openai": HealthCheckResult(
                provider_name="test_openai",
                status=ProviderStatus.DEGRADED,
                timestamp=datetime.now(),
                latency_ms=3000.0,
                success_rate=0.85
            )
        }

        await registry.register(provider1)
        await registry.register(provider2)

        request = GatewayRequest(
            prompt="Test",
            request_id="test_123",
            max_tokens=1000,
            temperature=0.7,
            allow_degraded_providers=False,
            routing_strategy=RoutingStrategy.HEALTH_BASED
        )

        decision = await registry._make_routing_decision(request, RoutingStrategy.HEALTH_BASED)

        # Should choose the healthy provider
        assert decision.provider_name == "test_azure"
        assert "Healthiest provider" in decision.reason


class TestFailoverScenarios:
    """Tests for automatic failover."""

    @pytest.mark.asyncio
    async def test_failover_on_provider_failure(self):
        """Test that failover works when primary provider fails."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.HEALTHY

        await registry.register(provider1)
        await registry.register(provider2)

        # Mock primary provider to fail
        async def mock_generate_failure(request, model=None):
            raise ProviderError("Primary provider failed", is_retryable=False)

        provider1.generate = mock_generate_failure

        # Mock secondary provider to succeed
        async def mock_generate_success(request, model=None):
            mock_response = Mock(spec=GatewayResponse)
            mock_response.content = "Fallback response"
            mock_response.model = "gpt-4"
            mock_response.provider = "test_openai"
            mock_response.routing_strategy = request.routing_strategy
            mock_response.routing_reason = "Test"
            mock_response.tokens_used = 10
            mock_response.latency_ms = 100.0
            mock_response.cost = 0.0003
            mock_response.request_id = "test_123"
            mock_response.metadata = {}
            mock_response.cached = False
            mock_response.quality_score = 0.9
            return mock_response

        provider2.generate = mock_generate_success

        request = GatewayRequest(
            prompt="Test",
            request_id="test_123",
            max_tokens=1000,
            temperature=0.7,
            allow_degraded_providers=False,
            routing_strategy=RoutingStrategy.ROUND_ROBIN
        )

        response = await registry.route_request(request)

        # Should fallback to secondary provider
        assert response.content == "Fallback response"
        assert response.provider == "test_openai"
        assert "fallback" in response.routing_reason.lower()

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_error(self):
        """Test that error is raised when all providers fail."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.HEALTHY

        await registry.register(provider1)
        await registry.register(provider2)

        # Mock both providers to fail
        async def mock_generate_failure(request, model=None):
            raise ProviderError("Provider failed", is_retryable=False)

        provider1.generate = mock_generate_failure
        provider2.generate = mock_generate_failure

        request = GatewayRequest(
            prompt="Test",
            request_id="test_123",
            max_tokens=1000,
            temperature=0.7,
            allow_degraded_providers=False,
            routing_strategy=RoutingStrategy.ROUND_ROBIN
        )

        with pytest.raises(ProviderError) as exc_info:
            await registry.route_request(request)

        assert "All providers failed" in str(exc_info.value)


class TestEndToEndRequestFlow:
    """Tests for end-to-end request routing."""

    @pytest.mark.asyncio
    async def test_full_request_flow_with_cost_optimization(self):
        """Test complete request flow with cost-optimized routing."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'OPENAI_API_KEY': 'test_key'
        }):
            provider1 = create_azure_openai_provider(name="test_azure")
            provider2 = create_openai_provider(name="test_openai")

        provider1.status = ProviderStatus.HEALTHY
        provider2.status = ProviderStatus.HEALTHY

        await registry.register(provider1)
        await registry.register(provider2)

        # Mock successful generation
        async def mock_generate(request, model=None):
            mock_response = Mock(spec=GatewayResponse)
            mock_response.content = f"Generated response using {model}"
            mock_response.model = model
            mock_response.provider = provider1.config.name if "azure" in model else provider2.config.name
            mock_response.routing_strategy = request.routing_strategy
            mock_response.routing_reason = "Test"
            mock_response.tokens_used = 50
            mock_response.latency_ms = 150.0
            mock_response.cost = 0.0015
            mock_response.request_id = request.request_id
            mock_response.metadata = {}
            mock_response.cached = False
            mock_response.quality_score = 0.9
            return mock_response

        provider1.generate = mock_generate
        provider2.generate = mock_generate

        request = GatewayRequest(
            prompt="Write a function",
            request_id="test_123",
            max_tokens=1000,
            temperature=0.7,
            allow_degraded_providers=False,
            routing_strategy=RoutingStrategy.COST_OPTIMIZED,
            model_requirements={ModelCapability.CODE}
        )

        response = await registry.route_request(request)

        assert response.content is not None
        assert response.tokens_used > 0
        assert response.latency_ms > 0
        assert response.cost > 0
        assert response.routing_strategy == RoutingStrategy.COST_OPTIMIZED
        assert response.routing_reason is not None

    @pytest.mark.asyncio
    async def test_request_with_tenant_tracking(self):
        """Test request with tenant ID for budget tracking."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test_key'
        }):
            provider = create_openai_provider(name="test_openai")

        provider.status = ProviderStatus.HEALTHY

        await registry.register(provider)

        async def mock_generate(request, model=None):
            mock_response = Mock(spec=GatewayResponse)
            mock_response.content = "Response"
            mock_response.model = model
            mock_response.provider = "test_openai"
            mock_response.routing_strategy = request.routing_strategy
            mock_response.routing_reason = "Test"
            mock_response.tokens_used = 10
            mock_response.latency_ms = 100.0
            mock_response.cost = 0.0003
            mock_response.request_id = request.request_id
            mock_response.metadata = {"tenant_id": request.tenant_id}
            mock_response.cached = False
            mock_response.quality_score = 0.9
            return mock_response

        provider.generate = mock_generate

        request = GatewayRequest(
            prompt="Test",
            request_id="test_123",
            tenant_id="tenant_abc",
            user_id="user_xyz",
            max_tokens=1000,
            temperature=0.7,
            allow_degraded_providers=False
        )

        response = await registry.route_request(request)

        assert response.metadata.get("tenant_id") == "tenant_abc"
        assert response.request_id == "test_123"


class TestHealthMonitoring:
    """Tests for health monitoring functionality."""

    @pytest.mark.asyncio
    async def test_health_check_loop(self):
        """Test periodic health checks."""
        registry = ProviderRegistry()

        with patch.dict('os.environ', {
            'AZURE_OPENAI_KEY': 'test_key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com'
        }):
            provider = create_azure_openai_provider(name="test_azure")

        # Mock health check
        async def mock_health_check():
            from src.providers.models import HealthCheckResult
            return HealthCheckResult(
                provider_name="test_azure",
                status=ProviderStatus.HEALTHY,
                timestamp=datetime.now(),
                latency_ms=100.0,
                success_rate=0.99
            )

        provider.health_check = mock_health_check

        await registry.register(provider)
        await registry.start_health_checks()

        # Wait for one health check cycle
        await asyncio.sleep(0.1)

        # Stop health checks
        await registry.stop_health_checks()

        # Verify health check was performed
        result = registry.get_health_check_result("test_azure")
        assert result is not None
        assert result.status == ProviderStatus.HEALTHY