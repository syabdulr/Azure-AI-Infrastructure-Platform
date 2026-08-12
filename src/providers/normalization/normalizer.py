"""Response normalizer for multi-provider AI gateway."""

from typing import Any, Dict, List, Optional

from .adapter import ResponseAdapter
from .azure_openai_adapter import AzureOpenAIAdapter
from .models import NormalizationResult, NormalizedResponse
from .openai_adapter import OpenAIAdapter


class ResponseNormalizer:
    """Normalizes responses from different providers into a unified format."""

    def __init__(self) -> None:
        """Initialize normalizer with all registered adapters."""
        self._adapters: Dict[str, ResponseAdapter] = {
            "azure_openai": AzureOpenAIAdapter(),
            "openai": OpenAIAdapter(),
        }

    def register_adapter(self, provider_name: str, adapter: ResponseAdapter) -> None:
        """
        Register a new adapter for a provider.

        Args:
            provider_name: Name of the provider
            adapter: Adapter instance
        """
        self._adapters[provider_name] = adapter

    def get_adapter(self, provider_name: str) -> Optional[ResponseAdapter]:
        """
        Get adapter for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Adapter or None if not found
        """
        return self._adapters.get(provider_name)

    def normalize(
        self,
        raw_response: Dict[str, Any],
        provider_name: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_per_1k: float,
    ) -> NormalizationResult:
        """
        Normalize a provider's raw response.

        Args:
            raw_response: Raw response from provider API
            provider_name: Name of the provider
            model_name: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            cost_per_1k: Cost per 1k tokens

        Returns:
            NormalizationResult

        Raises:
            ValueError: If provider is not supported
        """
        adapter = self.get_adapter(provider_name)

        if adapter is None:
            # Create error result
            return NormalizationResult(
                success=False,
                response=None,
                warnings=[],
                errors=[f"No adapter registered for provider: {provider_name}"],
                original_provider=provider_name,
                normalization_duration_ms=0.0,
            )

        # Normalize using the adapter
        return adapter.normalize(
            raw_response=raw_response,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_per_1k=cost_per_1k,
        )

    def is_provider_supported(self, provider_name: str) -> bool:
        """
        Check if a provider is supported.

        Args:
            provider_name: Name of the provider

        Returns:
            True if supported, False otherwise
        """
        return provider_name in self._adapters

    def list_supported_providers(self) -> List[str]:
        """
        Get list of supported providers.

        Returns:
            List of provider names
        """
        return list(self._adapters.keys())


# Global normalizer instance
_normalizer: Optional[ResponseNormalizer] = None


def get_normalizer() -> ResponseNormalizer:
    """
    Get the global normalizer instance.

    Returns:
        Global ResponseNormalizer instance
    """
    global _normalizer

    if _normalizer is None:
        _normalizer = ResponseNormalizer()

    return _normalizer
