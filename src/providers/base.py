"""Base provider class for multi-provider AI gateway."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Set
import time
import random

from .models import (
    ProviderConfig,
    ModelConfig,
    ProviderStatus,
    HealthCheckResult,
    ProviderMetrics,
    GatewayRequest,
    GatewayResponse,
    ModelCapability
)


class Provider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class and implement
    the abstract methods. This class provides common functionality for
    health tracking, metrics collection, and caching.
    """

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration."""
        self.config = config
        self.status = ProviderStatus.UNKNOWN
        self.metrics = ProviderMetrics(provider_name=config.name)
        self._last_health_check: Optional[datetime] = None
        self._circuit_open = False
        self._circuit_open_since: Optional[datetime] = None
        self._circuit_failure_count = 0
        self._circuit_failure_threshold = 3  # failures before opening circuit
        self._circuit_timeout_seconds = 300  # 5 minutes before half-open

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type (e.g., 'azure_openai', 'openai', 'anthropic')."""
        pass

    @abstractmethod
    async def generate(
        self,
        request: GatewayRequest,
        model: Optional[str] = None
    ) -> GatewayResponse:
        """
        Generate a response for the given request.

        Args:
            request: The gateway request
            model: The model to use (defaults to config default)

        Returns:
            GatewayResponse with the generated content and metadata

        Raises:
            ProviderError: If the request fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """
        Check provider health with a simple request.

        Returns:
            HealthCheckResult with status and latency
        """
        pass

    @abstractmethod
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """
        Get model configuration by name.

        Args:
            name: Model name

        Returns:
            ModelConfig if found, None otherwise
        """
        pass

    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Get all available models for this provider."""
        return self.config.models

    def get_models_with_capability(
        self,
        capability: ModelCapability
    ) -> Dict[str, ModelConfig]:
        """
        Get models that have a specific capability.

        Args:
            capability: Required capability

        Returns:
            Dictionary of model name to ModelConfig
        """
        return {
            name: model
            for name, model in self.config.models.items()
            if capability in model.capabilities
        }

    async def generate_with_fallback(
        self,
        request: GatewayRequest,
        model: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> GatewayResponse:
        """
        Generate with automatic retry and circuit breaker.

        Args:
            request: The gateway request
            model: The model to use
            max_retries: Max retries (defaults to config max_retries)

        Returns:
            GatewayResponse

        Raises:
            ProviderError: If all retries fail
        """
        if self._circuit_open:
            if self._should_attempt_circuit_reset():
                self._circuit_open = False
                self._circuit_failure_count = 0
            else:
                raise ProviderError(
                    f"Circuit breaker open for provider {self.config.name}"
                )

        max_retries = max_retries or self.config.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = await self.generate(request, model)
                latency_ms = (time.time() - start_time) * 1000

                # Update metrics
                self._record_success(latency_ms, response.tokens_used, response.cost)

                # Reset circuit breaker on success
                self._circuit_failure_count = 0

                return response

            except Exception as e:
                last_error = e
                self._record_failure()

                # Check if we should open circuit
                if self._circuit_failure_count >= self._circuit_failure_threshold:
                    self._circuit_open = True
                    self._circuit_open_since = datetime.now()
                    break

                # Exponential backoff
                if attempt < max_retries - 1:
                    backoff = self.config.retry_backoff_multiplier ** attempt
                    backoff = backoff + (random.random() * 0.1)  # Add jitter
                    await self._sleep(backoff)

        raise ProviderError(
            f"Provider {self.config.name} failed after {max_retries} attempts: {last_error}"
        )

    def _should_attempt_circuit_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if not self._circuit_open_since:
            return False
        elapsed = (datetime.now() - self._circuit_open_since).total_seconds()
        return elapsed >= self._circuit_timeout_seconds

    def _record_success(
        self,
        latency_ms: float,
        tokens_used: int,
        cost: float
    ) -> None:
        """Record a successful request in metrics."""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.total_tokens += tokens_used
        self.metrics.total_cost += cost
        self.metrics.last_success_time = datetime.now()

        # Update latency metrics (simplified EWMA)
        alpha = 0.1  # smoothing factor
        self.metrics.avg_latency_ms = (
            alpha * latency_ms +
            (1 - alpha) * self.metrics.avg_latency_ms
        )

    def _record_failure(self) -> None:
        """Record a failed request in metrics."""
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = datetime.now()
        self._circuit_failure_count += 1

    async def _sleep(self, seconds: float) -> None:
        """Async sleep with timeout support."""
        await asyncio.sleep(seconds)

    def is_healthy(self) -> bool:
        """Check if provider is healthy and circuit is closed."""
        return self.status == ProviderStatus.HEALTHY and not self._circuit_open

    def is_degraded(self) -> bool:
        """Check if provider is in degraded state."""
        return self.status == ProviderStatus.DEGRADED

    def is_available(self) -> bool:
        """Check if provider is available (healthy or degraded)."""
        return self.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]

    def get_success_rate(self) -> float:
        """Calculate success rate from metrics."""
        if self.metrics.total_requests == 0:
            return 1.0
        return self.metrics.successful_requests / self.metrics.total_requests

    def get_avg_cost_per_1k_tokens(self) -> float:
        """Calculate average cost per 1k tokens."""
        if self.metrics.total_tokens == 0:
            return 0.0
        return (self.metrics.total_cost / self.metrics.total_tokens) * 1000


class ProviderError(Exception):
    """Exception raised when a provider request fails."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        is_retryable: bool = True,
        is_rate_limit: bool = False
    ):
        """Initialize provider error."""
        super().__init__(message)
        self.provider_name = provider_name
        self.is_retryable = is_retryable
        self.is_rate_limit = is_rate_limit


# Import asyncio at module level
import asyncio