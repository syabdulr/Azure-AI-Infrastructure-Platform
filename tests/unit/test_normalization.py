"""Tests for response normalization."""

import pytest
from datetime import datetime

from src.providers.normalization.models import (
    NormalizationError,
    ToolCall,
    LogProb,
    UsageStatistics,
    NormalizedResponse,
    NormalizationResult
)
from src.providers.normalization.azure_openai_adapter import AzureOpenAIAdapter
from src.providers.normalization.openai_adapter import OpenAIAdapter
from src.providers.normalization.normalizer import ResponseNormalizer, get_normalizer


class TestNormalizedResponse:
    """Tests for NormalizedResponse model."""

    def test_create_normalized_response(self):
        """Test creating a normalized response."""
        usage = UsageStatistics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            prompt_cost=0.001,
            completion_cost=0.0005,
            total_cost=0.0015
        )

        response = NormalizedResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            usage=usage,
            latency_ms=150.0,
            timestamp=datetime.now(),
            finish_reason="stop",
            tool_calls=[],
            logprobs=None
        )

        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.usage.total_tokens == 150
        assert response.latency_ms == 150.0
        assert response.finish_reason == "stop"
        assert response.cached == False

    def test_tool_call_model(self):
        """Test creating a tool call."""
        tool_call = ToolCall(
            id="call_123",
            name="weather",
            arguments='{"location": "NYC"}',
            type="function"
        )

        assert tool_call.id == "call_123"
        assert tool_call.name == "weather"
        assert tool_call.arguments == '{"location": "NYC"}'

    def test_log_prob_model(self):
        """Test creating a log probability."""
        logprob = LogProb(
            token="hello",
            logprob=-0.5,
            top_logprobs=[{"hello": -0.5}, {"hi": -1.0}]
        )

        assert logprob.token == "hello"
        assert logprob.logprob == -0.5
        assert len(logprob.top_logprobs) == 2


class TestAzureOpenAIAdapter:
    """Tests for Azure OpenAI adapter."""

    def test_normalize_successful_response(self):
        """Test normalizing a successful Azure OpenAI response."""
        adapter = AzureOpenAIAdapter()

        raw_response = {
            "choices": [{
                "message": {"content": "Hello, world!"},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-4",
            prompt_tokens=10,
            completion_tokens=5,
            cost_per_1k=0.03
        )

        assert result.success is True
        assert result.response is not None
        assert result.response.content == "Hello, world!"
        assert result.response.provider == "azure_openai"
        assert result.response.usage.total_tokens == 15
        assert result.response.finish_reason == "stop"

    def test_normalize_response_with_tool_calls(self):
        """Test normalizing a response with tool calls."""
        adapter = AzureOpenAIAdapter()

        raw_response = {
            "choices": [{
                "message": {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "weather",
                            "arguments": '{"location": "NYC"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-4",
            prompt_tokens=20,
            completion_tokens=10,
            cost_per_1k=0.03
        )

        assert result.success is True
        assert len(result.response.tool_calls) == 1
        assert result.response.tool_calls[0].name == "weather"

    def test_normalize_error_response(self):
        """Test normalizing an error response."""
        adapter = AzureOpenAIAdapter()

        raw_response = {
            "error": {
                "message": "Rate limit exceeded"
            }
        }

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-4",
            prompt_tokens=0,
            completion_tokens=0,
            cost_per_1k=0.03
        )

        assert result.success is False
        assert result.response.error == "Rate limit exceeded"
        assert len(result.errors) > 0


class TestOpenAIAdapter:
    """Tests for OpenAI adapter."""

    def test_normalize_successful_response(self):
        """Test normalizing a successful OpenAI response."""
        adapter = OpenAIAdapter()

        raw_response = {
            "choices": [{
                "message": {"content": "AI response"},
                "finish_reason": "stop"
            }]
        }

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-3.5-turbo",
            prompt_tokens=15,
            completion_tokens=10,
            cost_per_1k=0.002
        )

        assert result.success is True
        assert result.response.content == "AI response"
        assert result.response.provider == "openai"
        assert result.response.usage.total_tokens == 25


class TestResponseNormalizer:
    """Tests for response normalizer."""

    def test_get_normalizer(self):
        """Test getting global normalizer instance."""
        normalizer = get_normalizer()
        assert isinstance(normalizer, ResponseNormalizer)

    def test_list_supported_providers(self):
        """Test listing supported providers."""
        normalizer = get_normalizer()
        providers = normalizer.list_supported_providers()

        assert "azure_openai" in providers
        assert "openai" in providers

    def test_normalize_azure_openai(self):
        """Test normalizing Azure OpenAI response."""
        normalizer = get_normalizer()

        raw_response = {
            "choices": [{
                "message": {"content": "Test content"},
                "finish_reason": "stop"
            }]
        }

        result = normalizer.normalize(
            raw_response=raw_response,
            provider_name="azure_openai",
            model_name="gpt-4",
            prompt_tokens=5,
            completion_tokens=3,
            cost_per_1k=0.03
        )

        assert result.success is True
        assert result.response.content == "Test content"
        assert result.response.provider == "azure_openai"

    def test_normalize_openai(self):
        """Test normalizing OpenAI response."""
        normalizer = get_normalizer()

        raw_response = {
            "choices": [{
                "message": {"content": "OpenAI content"},
                "finish_reason": "stop"
            }]
        }

        result = normalizer.normalize(
            raw_response=raw_response,
            provider_name="openai",
            model_name="gpt-3.5-turbo",
            prompt_tokens=8,
            completion_tokens=4,
            cost_per_1k=0.002
        )

        assert result.success is True
        assert result.response.content == "OpenAI content"
        assert result.response.provider == "openai"

    def test_normalize_unsupported_provider(self):
        """Test normalizing from unsupported provider."""
        normalizer = get_normalizer()

        raw_response = {"choices": [{"message": {"content": "Test"}}]}

        result = normalizer.normalize(
            raw_response=raw_response,
            provider_name="anthropic",
            model_name="claude-3",
            prompt_tokens=5,
            completion_tokens=3,
            cost_per_1k=0.015
        )

        assert result.success is False
        assert "No adapter registered" in result.errors[0]

    def test_normalization_metrics(self):
        """Test normalization timing metrics."""
        import time

        normalizer = get_normalizer()

        raw_response = {
            "choices": [{
                "message": {"content": "Timed response"},
                "finish_reason": "stop"
            }]
        }

        result = normalizer.normalize(
            raw_response=raw_response,
            provider_name="openai",
            model_name="gpt-3.5-turbo",
            prompt_tokens=5,
            completion_tokens=3,
            cost_per_1k=0.002
        )

        assert result.normalization_duration_ms >= 0
        assert result.normalization_duration_ms < 100  # Should be fast


class TestNormalizationErrorHandling:
    """Tests for error handling in normalization."""

    def test_missing_content_warning(self):
        """Test warning when content is missing."""
        adapter = AzureOpenAIAdapter()

        raw_response = {"choices": [{"message": {}}]}

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-4",
            prompt_tokens=5,
            completion_tokens=0,
            cost_per_1k=0.03
        )

        assert len(result.warnings) > 0
        assert "empty_response" in result.warnings[0].lower()

    def test_malformed_response(self):
        """Test handling malformed response."""
        adapter = OpenAIAdapter()

        raw_response = {"invalid": "structure"}

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-3.5-turbo",
            prompt_tokens=5,
            completion_tokens=0,
            cost_per_1k=0.002
        )

        assert len(result.warnings) > 0 or len(result.errors) > 0

    def test_tool_call_parsing_with_missing_name(self):
        """Test parsing tool calls with missing function name."""
        adapter = AzureOpenAIAdapter()

        raw_response = {
            "choices": [{
                "message": {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_123",
                        "function": {}  # Missing name
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        }

        result = adapter.normalize(
            raw_response=raw_response,
            model_name="gpt-4",
            prompt_tokens=10,
            completion_tokens=5,
            cost_per_1k=0.03
        )

        assert len(result.warnings) > 0
        # Check that one of the warnings is about missing function name
        has_missing_name_warning = any("missing function name" in warning.lower() for warning in result.warnings)
        assert has_missing_name_warning