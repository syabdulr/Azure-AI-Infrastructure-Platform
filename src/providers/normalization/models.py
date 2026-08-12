"""Response normalization models for multi-provider AI gateway."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NormalizationError(str, Enum):
    """Types of normalization errors."""

    INVALID_FORMAT = "invalid_format"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    TYPE_MISMATCH = "type_mismatch"
    EMPTY_RESPONSE = "empty_response"
    TOOL_CALL_FORMAT_ERROR = "tool_call_format_error"
    STREAMING_UNSUPPORTED = "streaming_unsupported"


class ToolCall(BaseModel):
    """Normalized tool/function call representation."""

    id: str = Field(..., description="Unique identifier for this tool call")
    name: str = Field(..., description="Function name")
    arguments: str = Field(..., description="Serialized function arguments")
    type: str = Field(default="function", description="Tool call type")


class LogProb(BaseModel):
    """Log probability for a token."""

    token: str = Field(..., description="The token")
    logprob: float = Field(..., description="Log probability")
    top_logprobs: List[Dict[str, float]] = Field(
        default_factory=list, description="Top alternative tokens and their logprobs"
    )


class UsageStatistics(BaseModel):
    """Unified token usage statistics."""

    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens")
    prompt_cost: float = Field(0.0, description="Cost of prompt tokens")
    completion_cost: float = Field(0.0, description="Cost of completion tokens")
    total_cost: float = Field(0.0, description="Total cost")


class NormalizedResponse(BaseModel):
    """
    Unified response format normalized from any provider.

    This abstracts away provider-specific response formats (Azure OpenAI,
    OpenAI, Anthropic, etc.) into a consistent structure.
    """

    # Core content
    content: str = Field(..., description="The generated text content")
    model: str = Field(..., description="Model that generated the response")
    provider: str = Field(..., description="Provider name")

    # Usage statistics
    usage: UsageStatistics = Field(..., description="Token usage and cost")

    # Timing
    latency_ms: float = Field(..., description="Total request latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    # Quality and metadata
    finish_reason: Optional[str] = Field(
        None, description="Why generation stopped (stop, length, content_filter, etc.)"
    )
    quality_score: Optional[float] = Field(
        None, description="LLM-as-a-judge quality score (0-1)", ge=0.0, le=1.0
    )

    # Advanced features
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Tool/function calls in the response"
    )
    logprobs: Optional[List[LogProb]] = Field(None, description="Log probabilities for tokens")

    # Error handling
    error: Optional[str] = Field(None, description="Error message if response failed")
    normalization_warnings: List[str] = Field(
        default_factory=list, description="Warnings from normalization process"
    )

    # Provider-specific metadata (preserved for debugging)
    raw_response: Dict[str, Any] = Field(
        default_factory=dict, description="Raw provider response for debugging"
    )

    # Metadata
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    cached: bool = Field(False, description="Whether response was from cache")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


@dataclass
class NormalizationResult:
    """Result of response normalization."""

    success: bool
    response: Optional[NormalizedResponse]
    warnings: List[str]
    errors: List[str]
    original_provider: str
    normalization_duration_ms: float
