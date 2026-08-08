"""Data models for multi-provider AI gateway."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RoutingStrategy(str, Enum):
    """Routing strategies for provider selection."""
    ROUND_ROBIN = "round_robin"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_BASED = "performance_based"
    HEALTH_BASED = "health_based"
    CAPABILITY_BASED = "capability_based"
    CUSTOM_RULES = "custom_rules"


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    REASONING = "reasoning"
    CODE = "code"
    ANALYSIS = "analysis"
    MULTIMODAL = "multimodal"
    SIMPLE_REASONING = "simple_reasoning"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    cost_per_1k_tokens: float
    max_tokens: int
    capabilities: Set[ModelCapability]
    context_window: int = 8192
    supports_function_calling: bool = False
    supports_streaming: bool = True


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    provider_type: str  # "azure_openai", "openai", "anthropic", etc.
    api_key: str
    endpoint: Optional[str] = None
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    health_check_enabled: bool = True
    rate_limit: int = 100  # requests per minute
    budget: Optional[float] = None  # monthly budget in USD
    timeout: int = 30  # request timeout in seconds
    max_retries: int = 3
    retry_backoff_multiplier: float = 2.0


@dataclass
class HealthCheckResult:
    """Result of a provider health check."""
    provider_name: str
    status: ProviderStatus
    timestamp: datetime
    latency_ms: float
    error: Optional[str] = None
    success_rate: Optional[float] = None  # rolling success rate


@dataclass
class ProviderMetrics:
    """Metrics collected for a provider."""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    rate_limit_hits: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None


class GatewayRequest(BaseModel):
    """Request to the AI gateway."""
    prompt: str = Field(..., description="The prompt to send to the LLM")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Sampling temperature")
    model_requirements: Optional[Set[ModelCapability]] = Field(
        default=None,
        description="Required model capabilities"
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID for budget tracking")
    user_id: Optional[str] = Field(None, description="User ID for audit trail")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    routing_strategy: Optional[RoutingStrategy] = Field(
        default=RoutingStrategy.COST_OPTIMIZED,
        description="Routing strategy to use"
    )
    allow_degraded_providers: bool = Field(
        False,
        description="Whether to route to degraded providers"
    )
    preferred_provider: Optional[str] = Field(
        None,
        description="Preferred provider (if available and healthy)"
    )


class GatewayResponse(BaseModel):
    """Response from the AI gateway."""
    content: str = Field(..., description="The generated content")
    model: str = Field(..., description="Model that generated the response")
    provider: str = Field(..., description="Provider that handled the request")
    routing_strategy: RoutingStrategy = Field(..., description="Strategy used for routing")
    routing_reason: str = Field(..., description="Why this provider was chosen")
    tokens_used: int = Field(..., description="Tokens consumed")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    cost: float = Field(..., description="Cost of the request")
    request_id: str = Field(..., description="Request ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    quality_score: Optional[float] = Field(None, description="LLM-as-a-judge quality score")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    cached: bool = Field(False, description="Whether response was from cache")


@dataclass
class RoutingDecision:
    """Decision made by the routing engine."""
    provider_name: str
    model_name: str
    strategy: RoutingStrategy
    reason: str
    confidence: float  # 0-1, how confident we are in this decision
    alternate_providers: List[str] = field(default_factory=list)