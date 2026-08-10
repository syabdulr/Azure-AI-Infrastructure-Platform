"""Response normalization for multi-provider AI gateway."""

from .models import (
    NormalizationError,
    ToolCall,
    LogProb,
    UsageStatistics,
    NormalizedResponse,
    NormalizationResult
)
from .adapter import ResponseAdapter
from .azure_openai_adapter import AzureOpenAIAdapter
from .openai_adapter import OpenAIAdapter
from .normalizer import ResponseNormalizer, get_normalizer

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
    "get_normalizer"
]