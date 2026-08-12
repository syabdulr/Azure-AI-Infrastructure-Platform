"""Models for A/B testing framework."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ExperimentStatus(Enum):
    """Status of an experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ExperimentVariant:
    """A variant in an A/B test experiment."""

    name: str
    provider: str
    model: str
    traffic_weight: int  # percentage 0-100
    is_control: bool = False
    description: str = ""


class ABExperiment:
    """An A/B testing experiment with multiple variants."""

    def __init__(
        self,
        name: str,
        description: str,
        variants: List[ExperimentVariant],
    ) -> None:
        """Initialize experiment."""
        self.name = name
        self.description = description
        self.variants = variants
        self.status = ExperimentStatus.DRAFT
        self.created_at: datetime = field(default_factory=datetime.now) if False else datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def total_traffic_weight(self) -> int:
        """Get sum of all variant traffic weights."""
        return sum(v.traffic_weight for v in self.variants)

    def validate_traffic(self) -> bool:
        """Check if traffic weights sum to 100."""
        return self.total_traffic_weight() == 100

    def get_variant(self, name: str) -> Optional[ExperimentVariant]:
        """Get a variant by name."""
        for v in self.variants:
            if v.name == name:
                return v
        return None

    def get_control_variant(self) -> Optional[ExperimentVariant]:
        """Get the control variant."""
        for v in self.variants:
            if v.is_control:
                return v
        return None

    def start(self) -> None:
        """Start the experiment."""
        if not self.validate_traffic():
            raise ValueError("Traffic weights must sum to 100")
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now()

    def pause(self) -> None:
        """Pause the experiment."""
        if self.status == ExperimentStatus.RUNNING:
            self.status = ExperimentStatus.PAUSED

    def resume(self) -> None:
        """Resume a paused experiment."""
        if self.status == ExperimentStatus.PAUSED:
            self.status = ExperimentStatus.RUNNING

    def complete(self) -> None:
        """Complete the experiment."""
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now()


@dataclass
class VariantMetrics:
    """Metrics tracked per variant."""

    variant_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    total_latency_ms: float = 0.0

    def record_request(
        self, success: bool, latency_ms: float, cost_usd: float, tokens: int
    ) -> None:
        """Record a request outcome."""
        self.total_requests += 1
        self.total_cost += cost_usd
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def avg_cost_per_request(self) -> float:
        """Calculate average cost per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_cost / self.total_requests

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "variant_name": self.variant_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost_per_request": self.avg_cost_per_request,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
        }


@dataclass
class ExperimentAssignment:
    """Result of assigning a request to a variant."""

    experiment_name: str
    variant_name: str
    request_id: str
    provider: str
    model: str
    timestamp: datetime = field(default_factory=datetime.now)
