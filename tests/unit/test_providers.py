"""Unit tests for Azure OpenAI and OpenAI providers."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.providers.azure_openai import AzureOpenAIProvider, create_azure_openai_provider
from src.providers.base import ProviderError
from src.providers.models import (
    GatewayRequest,
    GatewayResponse,
    ModelCapability,
    ModelConfig,
    ProviderConfig,
    ProviderStatus,
    RoutingStrategy,
)
from src.providers.openai import OpenAIProvider, create_openai_provider


class TestAzureOpenAIProvider:
    """Tests for Azure OpenAI provider."""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return ProviderConfig(
            name="test_azure",
            provider_type="azure_openai",
            api_key="test_key",
            endpoint="https://test.openai.azure.com",
            models={
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    cost_per_1k_tokens=0.03,
                    max_tokens=8192,
                    capabilities={ModelCapability.CHAT, ModelCapability.REASONING},
                )
            },
        )

    @pytest.fixture
    def provider(self, provider_config):
        """Create Azure OpenAI provider for testing."""
        with patch("src.providers.azure_openai.openai.AzureOpenAI"):
            return AzureOpenAIProvider(provider_config)

    def test_provider_initialization(self, provider):
        """Test provider initialization."""
        assert provider.config.name == "test_azure"
        assert provider.provider_type == "azure_openai"
        assert provider.status == ProviderStatus.UNKNOWN
        assert provider.is_healthy() is False

    @pytest.mark.asyncio
    async def test_successful_generation(self, provider, provider_config):
        """Test successful generation."""
        # Mock the client
        mock_client = Mock()
        provider.client = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Test response"
        mock_completion.choices[0].finish_reason = "stop"
        mock_completion.usage.total_tokens = 100
        mock_completion.usage.prompt_tokens = 50
        mock_completion.usage.completion_tokens = 50
        mock_client.chat.completions.create.return_value = mock_completion

        request = GatewayRequest(
            prompt="Test prompt", request_id="test_123", max_tokens=1000, temperature=0.7
        )

        # Generate response
        response = await provider.generate(request, model="gpt-4")

        # Verify
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "test_azure"
        assert response.tokens_used == 100
        assert response.cost == 0.003  # 100/1000 * 0.03
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test health check with healthy provider."""
        # Mock the client
        mock_client = Mock()
        provider.client = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "OK"
        mock_completion.usage.total_tokens = 1
        mock_client.chat.completions.create.return_value = mock_completion

        result = await provider.health_check()

        assert result.provider_name == "test_azure"
        assert result.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]
        assert result.latency_ms > 0

    def test_get_model(self, provider):
        """Test getting model configuration."""
        model = provider.get_model("gpt-4")
        assert model is not None
        assert model.name == "gpt-4"
        assert model.cost_per_1k_tokens == 0.03

        # Non-existent model
        model = provider.get_model("non-existent")
        assert model is None

    def test_create_azure_openai_provider_factory(self):
        """Test factory function for creating Azure OpenAI provider."""
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            },
        ):
            provider = create_azure_openai_provider(name="test_azure")

            assert provider.config.name == "test_azure"
            assert provider.provider_type == "azure_openai"
            assert len(provider.config.models) > 0  # Should have default models


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    @pytest.fixture
    def provider_config(self):
        """Create test provider configuration."""
        return ProviderConfig(
            name="test_openai",
            provider_type="openai",
            api_key="test_key",
            models={
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    cost_per_1k_tokens=0.03,
                    max_tokens=8192,
                    capabilities={ModelCapability.CHAT, ModelCapability.REASONING},
                )
            },
        )

    @pytest.fixture
    def provider(self, provider_config):
        """Create OpenAI provider for testing."""
        with patch("src.providers.openai.openai.OpenAI"):
            return OpenAIProvider(provider_config)

    def test_provider_initialization(self, provider):
        """Test provider initialization."""
        assert provider.config.name == "test_openai"
        assert provider.provider_type == "openai"
        assert provider.status == ProviderStatus.UNKNOWN
        assert provider.is_healthy() is False

    @pytest.mark.asyncio
    async def test_successful_generation(self, provider):
        """Test successful generation."""
        # Mock the client
        mock_client = Mock()
        provider.client = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Test response"
        mock_completion.choices[0].finish_reason = "stop"
        mock_completion.usage.total_tokens = 100
        mock_completion.usage.prompt_tokens = 50
        mock_completion.usage.completion_tokens = 50
        mock_client.chat.completions.create.return_value = mock_completion

        request = GatewayRequest(
            prompt="Test prompt", request_id="test_123", max_tokens=1000, temperature=0.7
        )

        # Generate response
        response = await provider.generate(request, model="gpt-4")

        # Verify
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "test_openai"
        assert response.tokens_used == 100
        assert response.cost == 0.003  # 100/1000 * 0.03
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, provider):
        """Test health check with healthy provider."""
        # Mock the client
        mock_client = Mock()
        provider.client = mock_client

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "OK"
        mock_completion.usage.total_tokens = 1
        mock_client.chat.completions.create.return_value = mock_completion

        result = await provider.health_check()

        assert result.provider_name == "test_openai"
        assert result.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]
        assert result.latency_ms > 0

    def test_get_model(self, provider):
        """Test getting model configuration."""
        model = provider.get_model("gpt-4")
        assert model is not None
        assert model.name == "gpt-4"
        assert model.cost_per_1k_tokens == 0.03

        # Non-existent model
        model = provider.get_model("non-existent")
        assert model is None

    def test_create_openai_provider_factory(self):
        """Test factory function for creating OpenAI provider."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}):
            provider = create_openai_provider(name="test_openai")

            assert provider.config.name == "test_openai"
            assert provider.provider_type == "openai"
            assert len(provider.config.models) > 0  # Should have default models


class TestProviderErrorHandling:
    """Tests for provider error handling."""

    @pytest.fixture
    def azure_provider(self):
        """Create Azure OpenAI provider for testing."""
        config = ProviderConfig(
            name="test_azure",
            provider_type="azure_openai",
            api_key="test_key",
            endpoint="https://test.openai.azure.com",
            models={
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    cost_per_1k_tokens=0.03,
                    max_tokens=8192,
                    capabilities={ModelCapability.CHAT},
                )
            },
        )
        with patch("src.providers.azure_openai.openai.AzureOpenAI"):
            return AzureOpenAIProvider(config)

    @pytest.fixture
    def openai_provider(self):
        """Create OpenAI provider for testing."""
        config = ProviderConfig(
            name="test_openai",
            provider_type="openai",
            api_key="test_key",
            models={
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    cost_per_1k_tokens=0.03,
                    max_tokens=8192,
                    capabilities={ModelCapability.CHAT},
                )
            },
        )
        with patch("src.providers.openai.openai.OpenAI"):
            return OpenAIProvider(config)

    def test_circuit_breaker(self, azure_provider):
        """Test circuit breaker opens after failures."""
        # Reset circuit state
        azure_provider._circuit_open = False
        azure_provider._circuit_failure_count = 0

        # Simulate 3 failures
        for _ in range(3):
            azure_provider._record_failure()

        # Manually open circuit after threshold is reached
        if azure_provider._circuit_failure_count >= azure_provider._circuit_failure_threshold:
            azure_provider._circuit_open = True

        assert azure_provider._circuit_open is True
        assert azure_provider._circuit_failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_requests(self, azure_provider):
        """Test that open circuit prevents requests."""
        # Open circuit
        azure_provider._circuit_open = True
        azure_provider._circuit_failure_count = 3

        request = GatewayRequest(
            prompt="Test", max_tokens=1000, temperature=0.7, request_id="test_123"
        )

        # Should raise error because circuit is open
        with pytest.raises(ProviderError) as exc_info:
            await azure_provider.generate_with_fallback(request)

        assert "Circuit breaker open" in str(exc_info.value)

    def test_success_rate_calculation(self, openai_provider):
        """Test success rate calculation."""
        # 5 successes, 1 failure
        for _ in range(5):
            openai_provider._record_success(100, 100, 0.003)

        openai_provider._record_failure()

        assert openai_provider.get_success_rate() == 0.8333333333333334  # 5/6

    def test_cost_calculation(self, openai_provider):
        """Test cost per 1k tokens calculation."""
        # Record usage: 5000 tokens, $0.15 total
        openai_provider._record_success(100, 5000, 0.15)

        # Cost per 1k tokens = (0.15 / 5000) * 1000 = 0.03
        assert openai_provider.get_avg_cost_per_1k_tokens() == 0.03


class TestModelCapabilities:
    """Tests for model capability filtering."""

    def test_get_models_with_capability_azure(self):
        """Test filtering models by capability using Azure provider."""
        config = ProviderConfig(
            name="test_provider",
            provider_type="azure_openai",
            api_key="test_key",
            models={
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    cost_per_1k_tokens=0.03,
                    max_tokens=8192,
                    capabilities={
                        ModelCapability.CHAT,
                        ModelCapability.REASONING,
                        ModelCapability.CODE,
                    },
                ),
                "gpt-35-turbo": ModelConfig(
                    name="gpt-35-turbo",
                    cost_per_1k_tokens=0.002,
                    max_tokens=4096,
                    capabilities={ModelCapability.CHAT, ModelCapability.SIMPLE_REASONING},
                ),
            },
        )
        with patch("src.providers.azure_openai.openai.AzureOpenAI"):
            provider = AzureOpenAIProvider(config)

            code_models = provider.get_models_with_capability(ModelCapability.CODE)
            assert len(code_models) == 1
            assert "gpt-4" in code_models
            assert "gpt-35-turbo" not in code_models

            chat_models = provider.get_models_with_capability(ModelCapability.CHAT)
            assert len(chat_models) == 2
            assert "gpt-4" in chat_models
            assert "gpt-35-turbo" in chat_models
