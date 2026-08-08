"""OpenAI provider implementation."""

import os
import time
from typing import Optional
import openai

from .base import Provider, ProviderError
from .models import (
    ProviderConfig,
    ModelConfig,
    ProviderStatus,
    HealthCheckResult,
    GatewayRequest,
    GatewayResponse,
    ModelCapability
)


class OpenAIProvider(Provider):
    """
    OpenAI provider implementation.

    Supports OpenAI API with GPT models including GPT-4, GPT-4o, and GPT-3.5.
    """

    @property
    def provider_type(self) -> str:
        """Return provider type."""
        return "openai"

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            api_key=config.api_key,
            timeout=config.timeout
        )

    async def generate(
        self,
        request: GatewayRequest,
        model: Optional[str] = None
    ) -> GatewayResponse:
        """
        Generate a response using OpenAI.

        Args:
            request: The gateway request
            model: The model to use (defaults to config default)

        Returns:
            GatewayResponse with generated content and metadata

        Raises:
            ProviderError: If the request fails
        """
        model_name = model or list(self.config.models.keys())[0]
        model_config = self.get_model(model_name)

        if not model_config:
            raise ProviderError(
                f"Model {model_name} not found in provider {self.config.name}"
            )

        start_time = time.time()
        request_id = request.request_id or f"{self.config.name}_{int(time.time())}"

        try:
            # Make the API call
            completion = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=request.max_tokens or model_config.max_tokens,
                temperature=request.temperature,
                timeout=self.config.timeout
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract response
            content = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens
            cost = (tokens_used / 1000) * model_config.cost_per_1k_tokens

            return GatewayResponse(
                content=content,
                model=model_name,
                provider=self.config.name,
                routing_strategy=request.routing_strategy,
                routing_reason="Direct call to OpenAI",
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                cost=cost,
                request_id=request_id,
                metadata={
                    "finish_reason": completion.choices[0].finish_reason,
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens
                }
            )

        except openai.APIError as e:
            # Handle different API error types
            if hasattr(e, 'status_code'):
                status_code = getattr(e, 'status_code')
                is_retryable = status_code not in [400, 401, 403, 404]
                is_rate_limit = status_code == 429
            else:
                is_retryable = True
                is_rate_limit = False

            raise ProviderError(
                f"OpenAI API error: {e}",
                provider_name=self.config.name,
                is_retryable=is_retryable,
                is_rate_limit=is_rate_limit
            )

        except openai.APITimeoutError as e:
            raise ProviderError(
                f"OpenAI timeout: {e}",
                provider_name=self.config.name,
                is_retryable=True
            )

        except openai.RateLimitError as e:
            raise ProviderError(
                f"OpenAI rate limit: {e}",
                provider_name=self.config.name,
                is_retryable=True,
                is_rate_limit=True
            )

        except openai.APIConnectionError as e:
            raise ProviderError(
                f"OpenAI connection error: {e}",
                provider_name=self.config.name,
                is_retryable=True
            )

        except Exception as e:
            raise ProviderError(
                f"Unexpected error from OpenAI: {e}",
                provider_name=self.config.name,
                is_retryable=False
            )

    async def health_check(self) -> HealthCheckResult:
        """
        Check OpenAI health with a simple request.

        Returns:
            HealthCheckResult with status and latency
        """
        from datetime import datetime

        start_time = time.time()

        try:
            # Simple completion request for health check
            completion = self.client.chat.completions.create(
                model=list(self.config.models.keys())[0],
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                timeout=5
            )

            latency_ms = (time.time() - start_time) * 1000

            # Update status based on latency
            if latency_ms < 1000:
                status = ProviderStatus.HEALTHY
            elif latency_ms < 3000:
                status = ProviderStatus.DEGRADED
            else:
                status = ProviderStatus.UNHEALTHY

            return HealthCheckResult(
                provider_name=self.config.name,
                status=status,
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                success_rate=self.get_success_rate()
            )

        except openai.RateLimitError:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                provider_name=self.config.name,
                status=ProviderStatus.DEGRADED,
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                error="Rate limited",
                success_rate=self.get_success_rate()
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                provider_name=self.config.name,
                status=ProviderStatus.UNHEALTHY,
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                error=str(e),
                success_rate=self.get_success_rate()
            )

    def get_model(self, name: str) -> Optional[ModelConfig]:
        """
        Get model configuration by name.

        Args:
            name: Model name

        Returns:
            ModelConfig if found, None otherwise
        """
        return self.config.models.get(name)


def create_openai_provider(
    name: str,
    api_key: Optional[str] = None,
    models: Optional[dict] = None
) -> OpenAIProvider:
    """
    Factory function to create OpenAI provider with default models.

    Args:
        name: Provider name
        api_key: OpenAI API key (defaults to env var OPENAI_API_KEY)
        models: Custom model configurations (defaults to standard models)

    Returns:
        OpenAIProvider instance
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OpenAI API key is required")

    # Default models if not provided
    if not models:
        models = {
            "gpt-4": ModelConfig(
                name="gpt-4",
                cost_per_1k_tokens=0.03,
                max_tokens=8192,
                capabilities={
                    ModelCapability.CHAT,
                    ModelCapability.REASONING,
                    ModelCapability.CODE,
                    ModelCapability.ANALYSIS
                },
                context_window=8192,
                supports_function_calling=True
            ),
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                cost_per_1k_tokens=0.01,
                max_tokens=128000,
                capabilities={
                    ModelCapability.CHAT,
                    ModelCapability.REASONING,
                    ModelCapability.CODE,
                    ModelCapability.ANALYSIS,
                    ModelCapability.MULTIMODAL
                },
                context_window=128000,
                supports_function_calling=True
            ),
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                cost_per_1k_tokens=0.005,
                max_tokens=128000,
                capabilities={
                    ModelCapability.CHAT,
                    ModelCapability.REASONING,
                    ModelCapability.CODE,
                    ModelCapability.ANALYSIS,
                    ModelCapability.MULTIMODAL
                },
                context_window=128000,
                supports_function_calling=True
            ),
            "gpt-35-turbo": ModelConfig(
                name="gpt-35-turbo",
                cost_per_1k_tokens=0.002,
                max_tokens=4096,
                capabilities={
                    ModelCapability.CHAT,
                    ModelCapability.SIMPLE_REASONING
                },
                context_window=4096,
                supports_function_calling=True
            )
        }

    config = ProviderConfig(
        name=name,
        provider_type="openai",
        api_key=api_key,
        models=models
    )

    return OpenAIProvider(config)