"""Models for observability and monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Type of metric."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricTag:
    """A tag/label for a metric."""

    key: str
    value: str


@dataclass
class MetricSample:
    """A single metric sample."""

    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HealthSnapshot:
    """Health snapshot for a provider."""

    provider_name: str
    healthy: bool
    latency_ms: float
    success_rate: float
    error_rate: float
    last_check: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class GatewayMetrics:
    """Aggregated metrics for the entire gateway."""

    def __init__(self) -> None:
        """Initialize gateway metrics."""
        self.total_requests: int = 0
        self.total_errors: int = 0
        self.total_cost: float = 0.0
        self.total_tokens: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self._latencies: List[float] = []
        self._provider_data: Dict[str, Dict[str, Any]] = {}
        self._model_data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def record_request(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        cost_usd: float,
        tokens: int,
        success: bool,
    ) -> None:
        """Record a single request."""
        self.total_requests += 1
        self.total_cost += cost_usd
        self.total_tokens += tokens
        self._latencies.append(latency_ms)

        if not success:
            self.total_errors += 1

        # Track per-provider
        if provider not in self._provider_data:
            self._provider_data[provider] = {
                "requests": 0,
                "errors": 0,
                "cost": 0.0,
                "tokens": 0,
                "latencies": [],
            }
        self._provider_data[provider]["requests"] += 1
        self._provider_data[provider]["cost"] += cost_usd
        self._provider_data[provider]["tokens"] += tokens
        self._provider_data[provider]["latencies"].append(latency_ms)
        if not success:
            self._provider_data[provider]["errors"] += 1

        # Track per-model
        if provider not in self._model_data:
            self._model_data[provider] = {}
        if model not in self._model_data[provider]:
            self._model_data[provider][model] = {
                "requests": 0,
                "errors": 0,
                "cost": 0.0,
                "tokens": 0,
                "latencies": [],
            }
        self._model_data[provider][model]["requests"] += 1
        self._model_data[provider][model]["cost"] += cost_usd
        self._model_data[provider][model]["tokens"] += tokens
        self._model_data[provider][model]["latencies"].append(latency_ms)
        if not success:
            self._model_data[provider][model]["errors"] += 1

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def get_provider_metrics(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific provider."""
        data = self._provider_data.get(provider)
        if data is None:
            return None
        latencies = data.get("latencies", [])
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        return {
            "requests": data["requests"],
            "errors": data["errors"],
            "cost": data["cost"],
            "tokens": data["tokens"],
            "avg_latency_ms": avg_lat,
        }

    def get_model_metrics(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific model under a provider."""
        data = self._model_data.get(provider, {}).get(model)
        if data is None:
            return None
        latencies = data.get("latencies", [])
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        return {
            "requests": data["requests"],
            "errors": data["errors"],
            "cost": data["cost"],
            "tokens": data["tokens"],
            "avg_latency_ms": avg_lat,
        }

    def snapshot(self) -> Dict[str, Any]:
        """Take a snapshot of current metrics."""
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.error_rate,
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": self.avg_latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
        }
