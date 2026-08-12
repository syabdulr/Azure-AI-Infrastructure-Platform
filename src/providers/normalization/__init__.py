"""Response normalization for multi-provider AI gateway."""

from .adapter import ResponseAdapter
from .azure_openai_adapter import AzureOpenAIAdapter
from .models import (
    LogProb,
    NormalizationError,
    NormalizationResult,
    NormalizedResponse,
    ToolCall,
    UsageStatistics,
)
from .normalizer import ResponseNormalizer, get_normalizer
from .openai_adapter import OpenAIAdapter

__all__ = [
    # Enums
    "NormalizationError",
    # Models
    "ToolCall",
    "LogProb",
    "UsageStatistics",
    "NormalizedResponse",
    "NormalizationResult",
    # Adapters
    "ResponseAdapter",
    "AzureOpenAIAdapter",
    "OpenAIAdapter",
    # Normalizer
    "ResponseNormalizer",
    "get_normalizer",
]
